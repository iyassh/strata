"""Phase 6 — the joint (union) false-alarm budget and the STRATA detector definition.

Usage: uv run python scripts/union_fpr.py <sdahu|pfpu|sfpu>

Closes gap S1/S2 (MASTER_PLAN): no artifact stored the healthy-year false-alarm
rate of all channels COMBINED — the number a deployed operator actually lives
with. This script

  1. mirrors scripts/benchmark.py's training/calibration exactly, scores the
     HEALTHY year with every channel, and reports per-channel and UNION flag
     rates on the shared calendar holdout (last `holdout_days_per_month` days
     of each month — the only healthy days no threshold was min/max-fit on);
  2. verifies, from the committed v12 benchmark artifact, that demoting the
     seasonal RATE channel to diagnostic-only costs nothing:
       (a) no scenario's significant-channel set is {rate} alone, and
       (b) no TTD is set by rate (rolling 30-day windows cannot flag before
           ~day 30; all measured TTDs are 1-2 days) —
     both checked as hard assertions, not narrated;
  3. writes outputs/union_fpr_<system>.json with counts, day lists, and the
     demotion verification, so the paper's joint-FPR table is a recomputable
     artifact.

Standing caveat (D2, carried into the artifact): these healthy "negatives" are
the calibration year's holdout — train-only min/max thresholds have still seen
the same building and weather year. No independent healthy negative exists on
any LBNL system.
"""

import json
import os
import sys
import warnings

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")

from pathlib import Path

import pandas as pd
import yaml

from processheal.core.detection import build_detector, classify_days, holdout_mask
from processheal.core.devices import (
    absence_days,
    build_device_detector,
    classify_device_days,
)
from processheal.core.frequency import (
    _flag_matrix,
    build_frequency_detector,
    build_rate_detector_monthly,
    classify_frequency_days,
    classify_rate_days_monthly,
    device_day_counts,
    unit_day_counts,
)
from processheal.core.oscillation import build_oscillation_detector, daily_direction_changes
from processheal.core.residuals import calibrate_band, daily_residual_scores, flag_days
from processheal.hvac.events import abstract_events, event_alphabet_map
from processheal.io.config import load_config

SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "sdahu"
CONFIG_DIR = f"configs/lbnl_{SYSTEM}"
DATA = Path(f"data/processed/{SYSTEM}")
RESIDUAL_RULE = "supply_air_residual"

cfg = load_config(CONFIG_DIR)
manifest = yaml.safe_load(Path(f"{CONFIG_DIR}/scenarios.yaml").read_text())
HEALTHY_FILE = manifest["healthy_file"]
SIGNATURE_EVENTS = {
    e for e, a in event_alphabet_map(cfg).items() if a == "signature"
} - {RESIDUAL_RULE}

# ---- train/calibrate exactly as benchmark.py does -------------------------
df = pd.read_parquet(DATA / f"{HEALTHY_FILE}.parquet")
log = abstract_events(df, cfg)
det = build_detector(cfg, log)

w = df.rename(columns={v: k for k, v in cfg.sensors.items()})
day = w["Datetime"].dt.date.astype(str)
occ = w["OCCUPIED"] > 0
diffs = w["Datetime"].diff().dropna().dt.total_seconds() / 60.0
interval = float(diffs.median()) if len(diffs) else 1.0
uni = (
    pd.DataFrame({"case_id": day, "occ": occ}).groupby("case_id")["occ"].sum() * interval
).rename("occupied_min").to_frame()
days = uni.index
sched = [d for d in days if uni.loc[d, "occupied_min"] > 0]

dev_det = build_device_detector(cfg, log, sched)
HOLD_N = cfg.rules["detection"]["holdout_days_per_month"]
freq_unit = build_frequency_detector(unit_day_counts(log), HOLD_N)
freq_dev = build_frequency_detector(device_day_counts(log, cfg), HOLD_N)
rate_det = build_rate_detector_monthly(unit_day_counts(log), HOLD_N, window=30)

RES_CHANNELS = cfg.rules["detection"].get("residual_channels", [RESIDUAL_RULE])
RES = {}
for rname in RES_CHANNELS:
    rh = daily_residual_scores(df, cfg, rule_name=rname)
    if rh.empty:
        continue
    hmask = holdout_mask(rh["case_id"], HOLD_N)
    RES[rname] = calibrate_band(
        rh, ~hmask, min_width=cfg.rules["detection"].get("residual_min_band_width", 0.0)
    )
osc_det = build_oscillation_detector(df, cfg)

# ---- score the healthy year with every channel -----------------------------
has_events = pd.Series([d in set(log["case_id"]) for d in days], index=days)

sig = log[log["activity"].isin(SIGNATURE_EVENTS)]
rules = pd.Series([d in set(sig["case_id"]) for d in days], index=days)

per_day = classify_days(det, log)
model = per_day.set_index("case_id")["flagged"].reindex(days).fillna(False)
model = model | (~has_events & (uni["occupied_min"] > 0))

res_flag = pd.Series(False, index=days)
for rname, band_r in RES.items():
    rs = daily_residual_scores(df, cfg, rule_name=rname)
    if rs.empty:
        continue
    rf = flag_days(
        rs, band_r, min_margin=cfg.rules["detection"].get("residual_min_exceedance", 0.0)
    ).set_index("case_id")
    res_flag = res_flag | rf["flagged"].reindex(days).fillna(False)

osc_flag = pd.Series(False, index=days)
if osc_det is not None:
    oc = daily_direction_changes(df, cfg)
    if not oc.empty:
        om = _flag_matrix(oc, osc_det.bands).any(axis=1)
        om.index = oc.index.astype(str)
        osc_flag = osc_flag | om.reindex(days).fillna(False)

dev_flag = pd.Series(False, index=days)
abs_flag = pd.Series(False, index=days)
if dev_det is not None:
    per_dev = classify_device_days(dev_det, log, cfg)
    if len(per_dev):
        fl = per_dev[per_dev["flagged"]]
        dev_flag = dev_flag | pd.Series(days.isin(set(fl["day"])), index=days)
    ab = absence_days(dev_det, log, cfg, sched)
    rare = ab[(ab["silent"]) & (ab["healthy_rate"] <= 0.05)]
    abs_flag = abs_flag | pd.Series(days.isin(set(rare["day"])), index=days)

freq_flag = pd.Series(False, index=days)
if freq_unit is not None:
    fu = classify_frequency_days(freq_unit, unit_day_counts(log)).set_index("day")
    freq_flag = freq_flag | fu["flagged"].reindex(days).fillna(False)
if freq_dev is not None:
    fd = classify_frequency_days(freq_dev, device_day_counts(log, cfg)).set_index("day")
    freq_flag = freq_flag | fd["flagged"].reindex(days).fillna(False)

rate_flag = pd.Series(False, index=days)
if rate_det is not None:
    rr = classify_rate_days_monthly(rate_det, unit_day_counts(log))
    if len(rr):
        rr = rr.set_index("day")
        rate_flag = rate_flag | rr["flagged"].reindex(days).fillna(False)

# ---- the joint budget on the shared calendar holdout ------------------------
hold = holdout_mask(pd.Series(days, index=days), HOLD_N)
hd = days[hold.values]
chans = {
    "rules": rules, "resid": res_flag, "model": model, "device": dev_flag,
    "absence": abs_flag, "freq": freq_flag, "rate": rate_flag, "osc": osc_flag,
}

print(f"== {SYSTEM} == healthy year, shared calendar holdout: {len(hd)} of {len(days)} days")
union = pd.Series(False, index=days)
union_norate = pd.Series(False, index=days)
out_channels = {}
for name, fl in chans.items():
    on_hold = fl.reindex(hd).fillna(False)
    k = int(on_hold.sum())
    out_channels[name] = {
        "holdout_fp_days": k,
        "holdout_days": len(hd),
        "full_year_days": int(fl.sum()),
        "holdout_fp_dates": sorted(on_hold[on_hold].index.tolist()),
    }
    print(f"  {name:8s} holdout FP {k:3d}/{len(hd)}  ({k / len(hd):.1%})   full-year {int(fl.sum())}")
    union = union | fl
    if name != "rate":
        union_norate = union_norate | fl
ku = int(union.reindex(hd).fillna(False).sum())
kn = int(union_norate.reindex(hd).fillna(False).sum())
print(f"  UNION (all 8)        {ku:3d}/{len(hd)}  ({ku / len(hd):.1%})")
print(f"  UNION minus rate     {kn:3d}/{len(hd)}  ({kn / len(hd):.1%})   <- the STRATA detector")

# ---- rate-demotion verification against the committed v12 artifact ----------
# The deployed detector = significance-gated union of all channels EXCEPT the
# seasonal rate channel (diagnostic-only). Assert the demotion is free.
bench = json.loads(Path(f"outputs/benchmark_v6_{SYSTEM}.json").read_text())
demotion = {"scenarios_with_rate_significant": [], "violations": []}
for s in bench["scenarios"]:
    mc = (s.get("meaningful_channels") or "").split("+")
    if "rate" not in mc:
        continue
    fd_ = s.get("flag_days", {})
    rate_days = set(fd_.get("rate", []))
    entry = {
        "label": s["label"],
        "channels": s["meaningful_channels"],
        "ttd_days": s["ttd_days"],
        "first_rate_day": min(rate_days) if rate_days else None,
        "rate_only_alarm_days": len(
            [x for x in fd_.get("sig_union", [])
             if x in rate_days
             and not any(x in set(fd_.get(ch, []))
                         for ch in ("rules", "residual", "model", "device", "freq", "osc"))]
        ),
    }
    demotion["scenarios_with_rate_significant"].append(entry)
    # (a) rate must never be the only significant channel
    if mc == ["rate"]:
        demotion["violations"].append(f"{s['label']}: carried SOLELY by rate")
    # (b) rate must never set the TTD: the first significant-union day must be
    # covered by at least one non-rate channel's day list. (Structurally, the
    # 30-day rolling rate windows cannot flag before ~day 30 anyway; this
    # checks the decisive fact directly instead of relying on that argument.)
    su = fd_.get("sig_union", [])
    if s["ttd_days"] is not None and su:
        first = min(su)
        covered = any(
            first in set(fd_.get(ch, []))
            for ch in ("rules", "residual", "model", "device", "freq", "osc")
        )
        if not covered:
            demotion["violations"].append(
                f"{s['label']}: first alarm day {first} is rate-only — demotion would delay TTD"
            )

n_rate_sig = len(demotion["scenarios_with_rate_significant"])
print(f"\nrate-demotion check: {n_rate_sig} scenarios have rate significant; "
      f"violations: {len(demotion['violations'])}")
for v in demotion["violations"]:
    print(f"  VIOLATION: {v}")
assert not demotion["violations"], "rate demotion is NOT free — do not ship it"

out = {
    "system": SYSTEM,
    "healthy_file": HEALTHY_FILE,
    "holdout_days": len(hd),
    "total_days": len(days),
    "channels": out_channels,
    "union_all8": {"holdout_fp_days": ku, "rate": ku / len(hd)},
    "union_minus_rate": {"holdout_fp_days": kn, "rate": kn / len(hd)},
    "detector_definition": (
        "The STRATA detector = OR of the significance-gated channels "
        "{rules, residual, model, device, absence, freq, osc}; the seasonal "
        "rate channel is diagnostic-only (corroboration and explanation, "
        "never a lone alarm)."
    ),
    "rate_demotion": demotion,
    "caveat": (
        "Healthy negatives are the calibration year's shared calendar holdout; "
        "no independent healthy negative exists on any LBNL system (D2). "
        "Per-day autocorrelation makes any binomial p on these counts optimistic."
    ),
}
Path(f"outputs/union_fpr_{SYSTEM}.json").write_text(json.dumps(out, indent=1))
print(f"\nwrote outputs/union_fpr_{SYSTEM}.json")
