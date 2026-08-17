"""The matched-rule ablation arm (G1 — the control the protocol requires).

Every discovered/calibrated channel claim faces its one-line rule twin,
train-calibrated, zero fault-side knowledge. Coverage parity or better by
the rule = the channel's claim must be discovery-automation, not detection
superiority. This arm exists so no Phase-4+ number ships uncontrolled.

Rules implemented (each named for the finding it controls):
  MR1 unit heating-absence  (3b finding): occupied workday AND AHU heating
      never active that day.
  MR2 device heat-episode count (3c finding): zone heating episodes/day
      outside the train min/max for that zone.
  MR3 heating-day rate (P1): trailing-30d count of AHU heating-active days
      outside the seasonal train band (evaluated on non-overlapping
      decision days).

    uv run python scripts/matched_rules.py <system>
"""

import json
import sys
import warnings
from pathlib import Path

import pandas as pd
import yaml

warnings.filterwarnings("ignore")
sys.path.insert(0, "src")

from processheal.core.detection import holdout_mask
from processheal.core.frequency import unit_day_counts, device_day_counts, rolling_active_rate
from processheal.hvac.events import abstract_events
from processheal.io.config import load_config

SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "sfpu"
DATA = Path(f"data/processed/{SYSTEM}")
cfg = load_config(f"configs/lbnl_{SYSTEM}")
manifest = yaml.safe_load(Path(f"configs/lbnl_{SYSTEM}/scenarios.yaml").read_text())
HOLD_N = cfg.rules["detection"]["holdout_days_per_month"]

SEASON = {"12": "DJF", "01": "DJF", "02": "DJF", "03": "MAM", "04": "MAM", "05": "MAM",
          "06": "JJA", "07": "JJA", "08": "JJA", "09": "SON", "10": "SON", "11": "SON"}


def calibrate(healthy_log):
    uc = unit_day_counts(healthy_log)
    dc = device_day_counts(healthy_log, cfg)
    days = pd.Series(uc.index.astype(str), index=uc.index)
    hold = holdout_mask(days, HOLD_N)
    uc_t = uc[~hold.values]
    bands = {}
    # MR2 per-zone heating episode bands
    for col in dc.columns:
        if col.startswith("zone_heating_active@"):
            tr = dc.reindex(uc.index).fillna(0)[~hold.values][col]
            bands[col] = (float(tr.min()), float(tr.max()))
    # MR3 seasonal 30d heating-day-rate bands
    heat = "heating_active"
    rate = rolling_active_rate(uc[[heat]], 30) if heat in uc.columns else pd.DataFrame()
    rbands = {}
    if not rate.empty:
        rdays = pd.Series(rate.index.astype(str), index=rate.index)
        rhold = holdout_mask(rdays, HOLD_N)
        seas = rdays.str[5:7].map(SEASON)
        for sn in ("DJF", "MAM", "JJA", "SON"):
            tr = rate[(seas == sn).values & (~rhold.values)]
            if len(tr):
                rbands[sn] = (float(tr[heat].min()), float(tr[heat].max()))
    return bands, rbands


def score(log, bands, rbands):
    uc = unit_day_counts(log)
    dc = device_day_counts(log, cfg)
    days = sorted(set(uc.index.astype(str)) | set(dc.index.astype(str)))
    # MR1: occupied workday & heating never active
    heat_days = set(uc.index[uc.get("heating_active", pd.Series(0, index=uc.index)) > 0].astype(str))
    workdays = [d for d in days if pd.Timestamp(d).dayofweek < 5]
    mr1 = set(d for d in workdays if d not in heat_days)
    # MR2
    mr2 = set()
    dcr = dc.reindex(pd.Index(days)).fillna(0)
    for col, (lo, hi) in bands.items():
        if col in dcr.columns:
            v = dcr[col]
            mr2 |= set(v.index[(v < lo) | (v > hi)].astype(str))
    # MR3 on non-overlapping decision days
    mr3 = set()
    if rbands and "heating_active" in uc.columns:
        rate = rolling_active_rate(uc[["heating_active"]], 30)
        rd = rate.index.astype(str)
        for i, d in enumerate(rd):
            if i % 30 != 29:
                continue
            sn = SEASON[d[5:7]]
            lo, hi = rbands.get(sn, (0, 30))
            v = float(rate.iloc[i]["heating_active"])
            if v < lo or v > hi:
                mr3.add(d)
    return mr1, mr2, mr3


healthy_log = abstract_events(pd.read_parquet(DATA / f"{manifest['healthy_file']}.parquet"), cfg)
bands, rbands = calibrate(healthy_log)
h1, h2, h3 = score(healthy_log, bands, rbands)
print(f"[{SYSTEM}] matched rules healthy-year firings: MR1={len(h1)} MR2={len(h2)} MR3={len(h3)}")

bench = json.loads(Path(f"outputs/benchmark_v6_{SYSTEM}.json").read_text())
rows = []
print(f"{'scenario':38s} {'MR1':>4} {'MR2':>4} {'MR3':>4} | {'freq':>4} {'rate':>4} {'model':>5} {'dev':>4}")
for sc in manifest["scenarios"]:
    log = abstract_events(pd.read_parquet(DATA / f"{sc['file']}.parquet"), cfg)
    m1, m2, m3 = score(log, bands, rbands)
    br = next(r for r in bench["scenarios"] if r["file"] == sc["file"])
    print(f"{sc['label']:38s} {len(m1):>4} {len(m2):>4} {len(m3):>4} | "
          f"{br['frequency_days']:>4} {br['rate_days']:>4} {br['model_days']:>5} {br['device_days']:>4}")
    rows.append({"file": sc["file"], "mr1": len(m1), "mr2": len(m2), "mr3": len(m3),
                 "freq": br["frequency_days"], "rate": br["rate_days"],
                 "model": br["model_days"], "device": br["device_days"]})
Path(f"outputs/matched_rules_{SYSTEM}.json").write_text(json.dumps(
    {"system": SYSTEM, "healthy_fp": {"mr1": len(h1), "mr2": len(h2), "mr3": len(h3)},
     "scenarios": rows}, indent=2))
print(f"wrote outputs/matched_rules_{SYSTEM}.json")
