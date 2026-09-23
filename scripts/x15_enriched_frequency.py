"""X15 — enriched alphabet, frequency channel only, under two holdout splits.

Pre-registered: docs/plans/2026-09-23-x15-enriched-frequency-prereg.md
(motivated by a post-hoc read of X14; the holdout is what changes).

X14's enriched alphabet exactly; only the frequency channel (unit + device
strata, deployed code) is built and gated; last-8-days and first-8-days
splits; the frequency channel's own significance gate.

    uv run python scripts/x15_enriched_frequency.py -> outputs/x15_enriched_frequency.json
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

src = Path("scripts/x14_enriched_alphabet.py").read_text()
ns = {}
exec("import pandas as pd\nfrom strata.core.splits import holdout_mask\nZONES='IWSE'\n"
     + src[src.index("def enrich"):src.index("\nout = {")], ns)
enrich = ns["enrich"]


def first_n(case_ids: pd.Series, n: int) -> pd.Series:
    d = pd.to_datetime(case_ids.str.split("__").str[0])
    return d.dt.day <= n


def run_split(system: str, split_name: str, split_fn) -> dict:
    _splits.holdout_mask = split_fn; _freq.holdout_mask = split_fn; ns["holdout_mask"] = split_fn
    try:
        cfg = load_config(f"configs/lbnl_{system}")
        man = yaml.safe_load(Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())
        hold_n = cfg.rules["detection"]["holdout_days_per_month"]
        card = {s["file"]: s for s in json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]}
        hdf = pd.read_parquet(f"data/processed/{system}/{man['healthy_file']}.parquet")
        added = enrich(cfg, hdf, hold_n)
        hlog = abstract_events(hdf, cfg)
        fu = build_frequency_detector(unit_day_counts(hlog), hold_n)
        fd = build_frequency_detector(device_day_counts(hlog, cfg), hold_n)
        # healthy holdout false alarms of the union of the two strata
        days = pd.Series(sorted(set(hlog["case_id"])))
        hold = set(days[split_fn(days, hold_n).values])
        hfl = set()
        for det, counts in ((fu, unit_day_counts(hlog)), (fd, device_day_counts(hlog, cfg))):
            if det is None or counts.empty:
                continue
            c = classify_frequency_days(det, counts)
            hfl |= set(c.loc[c["flagged"], "day"])
        hold_fp = len(hfl & hold)
        out = {"split": split_name, "n_added_signals": len(added), "holdout_days": len(hold), "holdout_fp_days": hold_fp,
               "unit_fp": (fu.holdout_fp_days if fu else None), "dev_fp": (fd.holdout_fp_days if fd else None),
               "scenarios": []}
        for s in man["scenarios"]:
            if not s["is_fault"] or s.get("exclude"):
                continue
            log = abstract_events(pd.read_parquet(f"data/processed/{system}/{s['file']}.parquet"), cfg)
            flagged = set()
            for det, counts in ((fu, unit_day_counts(log)), (fd, device_day_counts(log, cfg))):
                if det is None or counts.empty:
                    continue
                c = classify_frequency_days(det, counts)
                flagged |= set(c.loc[c["flagged"], "day"])
            n_eval = int(log["case_id"].nunique())
            sig = frequency_significant(len(flagged), n_eval, fu.holdout_fp_days if fu else 0, fu.holdout_days if fu else 0,
                                        fd.holdout_fp_days if fd else 0, fd.holdout_days if fd else 0)
            c0 = card[s["file"]]
            out["scenarios"].append({"file": s["file"], "flag_days": len(flagged), "n_eval": n_eval, "significant": bool(sig),
                                     "deployed_detected": bool(c0["meaningful_channels"]),
                                     "deployed_frequency_sig": "freq" in str(c0["meaningful_channels"])})   # scorecard vocabulary: "freq"
        print(f"{system} {split_name}: +{len(added)} signals | holdout FP {hold_fp}/{len(hold)} | "
              f"sig {sum(r['significant'] for r in out['scenarios'])}/{len(out['scenarios'])} | newly "
              f"{[r['file'] for r in out['scenarios'] if r['significant'] and not r['deployed_detected']]}", flush=True)
        return out
    finally:
        _splits.holdout_mask = _last_n; _freq.holdout_mask = _last_n; ns["holdout_mask"] = _last_n


res = {"pre_registration": "docs/plans/2026-09-23-x15-enriched-frequency-prereg.md", "systems": {}}
for system in ("sdahu", "pfpu", "sfpu"):
    res["systems"][system] = {"last8": run_split(system, "last8", _last_n), "first8": run_split(system, "first8", first_n)}

TARGET = "SFPU_ReheatCoilFouling_Airside_Moderate"
budget = {"sdahu": 9, "pfpu": 10, "sfpu": 10}
p1 = all(v[sp]["holdout_fp_days"] <= budget[s] for s, v in res["systems"].items() for sp in ("last8", "first8"))
def sig_of(system, split, f):
    return next(r["significant"] for r in res["systems"][system][split]["scenarios"] if r["file"] == f)
p2 = sig_of("sfpu", "last8", TARGET) and sig_of("sfpu", "first8", TARGET)
newly_both = sorted({r["file"] for s, v in res["systems"].items() for r in v["last8"]["scenarios"]
                     if r["significant"] and not r["deployed_detected"] and sig_of(s, "first8", r["file"])})
p3 = [f for f in newly_both if f != TARGET] == []
enr = sum(1 for v in res["systems"].values() for r in v["last8"]["scenarios"] if r["deployed_detected"] and r["significant"])
dep = sum(1 for v in res["systems"].values() for r in v["last8"]["scenarios"] if r["deployed_detected"] and r["deployed_frequency_sig"])
p4 = enr >= dep
fired = []
if not p1:
    fired.append("F-X15.a: enriched frequency channel exceeds the budget under a split")
if not p2:
    fired.append("F-X15.b: the detection is split-dependent")
res.update({"predictions": {"P1_budget_both_splits": p1, "P2_target_sig_both_splits": p2, "P3_no_other_new": p3,
                            "newly_significant_both_splits": newly_both, "P4_enriched_ge_deployed_on_detected": p4,
                            "enriched_sig_on_detected": enr, "deployed_frequency_sig_on_detected": dep},
            "falsifiers_fired": fired})
Path("outputs/x15_enriched_frequency.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res["predictions"], indent=1)); print("falsifiers fired:", fired or "none"); print("wrote outputs/x15_enriched_frequency.json")
