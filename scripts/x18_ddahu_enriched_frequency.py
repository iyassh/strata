"""X18 — X15's protocol on the fourth system: enriched alphabet, frequency
channel only, two holdout splits, DDAHU.

Pre-registered: docs/plans/2026-09-24-x18-ddahu-enriched-frequency-prereg.md.
Enrichment as in X14 (positions = `_POS` in the canonical name, flows =
ZONE_FLOW_* minus setpoints, healthy occupied train 10th/90th percentiles,
15-minute dwell); only build_frequency_detector / classify_frequency_days;
the frequency channel's own gate.

    uv run python scripts/x18_ddahu_enriched_frequency.py -> outputs/x18_ddahu_enriched_frequency.json
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

import strata.core.frequency as _freq
import strata.core.splits as _splits
from strata.core.frequency import (build_frequency_detector, classify_frequency_days,
                                   device_day_counts, unit_day_counts)
from strata.core.significance import frequency_significant
from strata.core.splits import holdout_mask as _last_n
from strata.hvac.events import abstract_events
from strata.io.config import load_config

SYSTEM = "ddahu"
ZONES = ("W", "SB", "SA", "E")
DWELL = {"min_dwell_min": 15}


def enrich(cfg, hdf, hold_n, split_fn):
    w = hdf.rename(columns={v: k for k, v in cfg.sensors.items()})
    day = w["Datetime"].dt.date.astype(str)
    train = ~split_fn(day, hold_n).values
    occ = (w["OCCUPIED"] > 0.5).values & train
    sigs = [k for k in cfg.sensors if ("_POS" in k or k.startswith("ZONE_FLOW_")) and "_SP" not in k and k in w.columns]
    added = {}
    for s in sigs:
        v = w.loc[occ, s].dropna()
        if v.empty:
            continue
        q10, q90 = float(v.quantile(0.10)), float(v.quantile(0.90))
        if not (q90 - q10 > 1e-6):
            continue
        tag = {}
        z = s.rsplit("_", 1)[-1]
        if z in ZONES and s.startswith("ZONE_"):
            tag = {"stratum": "device", "device": f"TU_{z}"}
        cfg.rules["events"][f"x18_{s}_high"] = {"kind": "mode", "alphabet": "state", "signal": s, "on_above": q90,
                                               "on_event": f"{s}_high_entered", "off_event": f"{s}_high_exited", **tag, **DWELL}
        cfg.rules["events"][f"x18_{s}_low"] = {"kind": "window", "alphabet": "state", "signal": s, "low": -1e9, "high": q10,
                                              "enter_event": f"{s}_low_entered", "exit_event": f"{s}_low_exited", **tag, **DWELL}
        added[s] = {"q10": round(q10, 4), "q90": round(q90, 4)}
    return added


def first_n(case_ids: pd.Series, n: int) -> pd.Series:
    d = pd.to_datetime(case_ids.str.split("__").str[0])
    return d.dt.day <= n


def run_split(split_name, split_fn):
    _splits.holdout_mask = split_fn; _freq.holdout_mask = split_fn
    try:
        cfg = load_config(f"configs/lbnl_{SYSTEM}")
        man = yaml.safe_load(Path(f"configs/lbnl_{SYSTEM}/scenarios.yaml").read_text())
        hold_n = cfg.rules["detection"]["holdout_days_per_month"]
        card = {s["file"]: s for s in json.loads(Path(f"outputs/benchmark_v6_{SYSTEM}.json").read_text())["scenarios"]}
        toks = {t for s in card.values() for t in str(s["meaningful_channels"]).split("+")}
        assert toks <= {"rules", "resid", "model", "device", "absence", "freq", "rate", "osc", "None", ""}, toks
        hdf = pd.read_parquet(f"data/processed/{SYSTEM}/{man['healthy_file']}.parquet")
        added = enrich(cfg, hdf, hold_n, split_fn)
        hlog = abstract_events(hdf, cfg)
        fu = build_frequency_detector(unit_day_counts(hlog), hold_n)
        fd = build_frequency_detector(device_day_counts(hlog, cfg), hold_n)
        days = pd.Series(sorted(set(hlog["case_id"])))
        hold = set(days[split_fn(days, hold_n).values])
        hfl = set()
        for det, counts in ((fu, unit_day_counts(hlog)), (fd, device_day_counts(hlog, cfg))):
            if det is None or counts.empty:
                continue
            c = classify_frequency_days(det, counts); hfl |= set(c.loc[c["flagged"], "day"])
        out = {"split": split_name, "n_added_signals": len(added), "added": added, "holdout_days": len(hold),
               "holdout_fp_days": len(hfl & hold), "unit_fp": (fu.holdout_fp_days if fu else None),
               "dev_fp": (fd.holdout_fp_days if fd else None), "scenarios": []}
        for s in man["scenarios"]:
            if not s["is_fault"] or s.get("exclude"):
                continue
            log = abstract_events(pd.read_parquet(f"data/processed/{SYSTEM}/{s['file']}.parquet"), cfg)
            flagged = set()
            for det, counts in ((fu, unit_day_counts(log)), (fd, device_day_counts(log, cfg))):
                if det is None or counts.empty:
                    continue
                c = classify_frequency_days(det, counts); flagged |= set(c.loc[c["flagged"], "day"])
            n_eval = int(log["case_id"].nunique())
            sig = frequency_significant(len(flagged), n_eval, fu.holdout_fp_days if fu else 0, fu.holdout_days if fu else 0,
                                        fd.holdout_fp_days if fd else 0, fd.holdout_days if fd else 0)
            c0 = card[s["file"]]
            out["scenarios"].append({"file": s["file"], "family": s["family"], "flag_days": len(flagged), "n_eval": n_eval,
                                     "significant": bool(sig), "deployed_detected": bool(c0["meaningful_channels"]),
                                     "deployed_frequency_sig": "freq" in str(c0["meaningful_channels"])})
        print(f"{SYSTEM} {split_name}: +{len(added)} signals | holdout FP {out['holdout_fp_days']}/{len(hold)} | "
              f"sig {sum(r['significant'] for r in out['scenarios'])}/{len(out['scenarios'])} | newly "
              f"{[r['file'] for r in out['scenarios'] if r['significant'] and not r['deployed_detected']]}", flush=True)
        return out
    finally:
        _splits.holdout_mask = _last_n; _freq.holdout_mask = _last_n


res = {"pre_registration": "docs/plans/2026-09-24-x18-ddahu-enriched-frequency-prereg.md", "system": SYSTEM,
       "last8": run_split("last8", _last_n), "first8": run_split("first8", first_n)}
def sig(split, f): return next(r["significant"] for r in res[split]["scenarios"] if r["file"] == f)
newly_both = sorted(r["file"] for r in res["last8"]["scenarios"] if r["significant"] and not r["deployed_detected"] and sig("first8", r["file"]))
fam = {r["file"]: r["family"] for r in res["last8"]["scenarios"]}
p1 = res["last8"]["holdout_fp_days"] <= 10 and res["first8"]["holdout_fp_days"] <= 10
p2 = any(fam[f] == "coil_fouling" for f in newly_both)
p3 = not any(fam[f] == "static_sensor_bias" for f in newly_both)
enr = sum(1 for r in res["last8"]["scenarios"] if r["deployed_detected"] and r["significant"])
dep = sum(1 for r in res["last8"]["scenarios"] if r["deployed_detected"] and r["deployed_frequency_sig"])
fired = []
if not p1:
    fired.append("F-X18.a: enriched frequency channel exceeds the budget under a split")
if not p2:
    fired.append("F-X18.b: no missed fouling scenario significant under both splits — the X15 gain does not replicate")
res.update({"predictions": {"P1_budget_both_splits": p1, "P2_fouling_newly_both_splits": p2, "P3_no_static_bias_new": p3,
                            "newly_significant_both_splits": newly_both, "P4_enriched_ge_deployed_on_detected": enr >= dep,
                            "enriched_sig_on_detected": enr, "deployed_frequency_sig_on_detected": dep},
            "falsifiers_fired": fired})
Path("outputs/x18_ddahu_enriched_frequency.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res["predictions"], indent=1)); print("falsifiers fired:", fired or "none"); print("wrote outputs/x18_ddahu_enriched_frequency.json")
