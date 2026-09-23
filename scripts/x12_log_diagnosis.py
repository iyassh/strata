"""The log-level diagnosis behind X12, as an artefact: what the state-event
log carries under each scenario the deployed detector misses.

For every system: per-day state-activity counts and per-pair on-duration
medians on the fault-free year and on every scored scenario; for each
scenario the largest relative change in any activity's daily count and in
any pair's on-duration median against healthy. A scenario whose largest
changes are both below 5 % has a state log indistinguishable from healthy
at day level — nothing that reads that log can detect it.

    uv run python scripts/x12_log_diagnosis.py -> outputs/x12_log_diagnosis.json
"""
import json
import os
import sys
import warnings

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from strata.core.sojourn import daily_sojourn_stats
from strata.hvac.events import abstract_events, event_alphabet_map
from strata.io.config import load_config

TOL = 0.05


def profile(df, cfg, state):
    log = abstract_events(df, cfg)
    log = log[log["activity"].isin(state)]
    counts = (log.groupby("activity").size() / log["case_id"].nunique()).to_dict()
    st = daily_sojourn_stats(log, cfg)
    on = {c: float(st[c].median()) for c in st.columns if c.endswith(":on_med") and st[c].notna().sum() >= 30}
    return {"events_per_day": round(len(log) / max(log["case_id"].nunique(), 1), 2),
            "activity_per_day": {k: round(v, 3) for k, v in counts.items()},
            "on_median_min": {k: round(v, 1) for k, v in on.items()}}


def max_rel_change(h: dict, f: dict) -> tuple[float, str]:
    best, key = 0.0, ""
    for k, hv in h.items():
        fv = f.get(k, 0.0)
        if hv <= 0:
            continue
        r = abs(fv - hv) / hv
        if r > best:
            best, key = r, k
    return round(best, 4), key


out = {"tolerance": TOL, "systems": {}}
for system in ("sdahu", "pfpu", "sfpu"):
    cfg = load_config(f"configs/lbnl_{system}")
    man = yaml.safe_load(Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())
    card = {s["file"]: s for s in json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]}
    state = [k for k, v in event_alphabet_map(cfg).items() if v == "state"]
    hp = profile(pd.read_parquet(f"data/processed/{system}/{man['healthy_file']}.parquet"), cfg, state)
    sysout = {"healthy": hp, "scenarios": []}
    for s in man["scenarios"]:
        if not s["is_fault"] or s.get("exclude"):
            continue
        fp = profile(pd.read_parquet(f"data/processed/{system}/{s['file']}.parquet"), cfg, state)
        dc, kc = max_rel_change(hp["activity_per_day"], fp["activity_per_day"])
        dd, kd = max_rel_change(hp["on_median_min"], fp["on_median_min"])
        row = {"file": s["file"], "deployed_detected": bool(card[s["file"]]["meaningful_channels"]),
               "events_per_day": fp["events_per_day"],
               "max_count_change": dc, "max_count_change_activity": kc,
               "max_on_duration_change": dd, "max_on_duration_change_pair": kd,
               "log_indistinguishable_at_5pct": bool(dc < TOL and dd < TOL)}
        sysout["scenarios"].append(row)
        print(f"{system} {s['file'][:38]:38s} {'DET ' if row['deployed_detected'] else 'miss'} count Δ {dc:6.3f} ({kc[:28]}) "
              f"dur Δ {dd:6.3f} ({kd[:26]}) {'IDENTICAL@5%' if row['log_indistinguishable_at_5pct'] else ''}", flush=True)
    out["systems"][system] = sysout

rows = [r for v in out["systems"].values() for r in v["scenarios"]]
missed = [r for r in rows if not r["deployed_detected"]]
out["summary"] = {"n_scored": len(rows), "n_missed": len(missed),
                  "missed_with_indistinguishable_log": [r["file"] for r in missed if r["log_indistinguishable_at_5pct"]],
                  "detected_with_indistinguishable_log": [r["file"] for r in rows if r["deployed_detected"] and r["log_indistinguishable_at_5pct"]]}
Path("outputs/x12_log_diagnosis.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out["summary"], indent=1)); print("wrote outputs/x12_log_diagnosis.json")
