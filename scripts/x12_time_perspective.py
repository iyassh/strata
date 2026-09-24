"""X12 — the time perspective of the discovered state model.

Pre-registered: docs/plans/2026-09-23-x12-time-perspective-prereg.md
(predictions P1-P4, falsifiers F-X12.a/b/c, all fixed before this ran).

For each system: build the time-infused state model on the healthy year
(train days), classify every scored scenario's days, gate at the same
exact-binomial p < 1e-3 against the holdout false-alarm rate, and compare
against the committed scorecards' per-channel flag days (never re-run).

    uv run python scripts/x12_time_perspective.py  -> outputs/x12_time_perspective.json
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

from strata.core.significance import P_SIG, binom_sf
from strata.core.sojourn import (build_sojourn_detector, classify_sojourn_days,
                                 daily_sojourn_stats)
from strata.core.splits import holdout_mask
from strata.hvac.events import abstract_events
from strata.io.config import load_config

# the scorecards export six channels' day lists (absence is not exported by
# scripts/benchmark.py) plus `sig_union`, the union of the gated channels;
# both comparisons are reported. (A first run used non-existent keys for
# three channels — caught in review, corrected before anything was adopted.)
DEPLOYED = ["rules", "residual", "model", "device", "freq", "osc"]
FOULING = "ReheatCoilFouling"
out = {"pre_registration": "docs/plans/2026-09-23-x12-time-perspective-prereg.md",
       "channel": "time-infused state model: per state pair, day-median on-duration, off-gap, "
                  "first-on minute; train min/max bands +/- 5 min; holdout FP rate; binomial p<1e-3",
       "systems": {}}

for system in ("sdahu", "pfpu", "sfpu"):
    cfg = load_config(f"configs/lbnl_{system}")
    man = yaml.safe_load(Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())
    hold_n = cfg.rules["detection"]["holdout_days_per_month"]
    card = {s["file"]: s for s in json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]}
    hdf = pd.read_parquet(f"data/processed/{system}/{man['healthy_file']}.parquet")
    hstats = daily_sojourn_stats(abstract_events(hdf, cfg), cfg)
    det = build_sojourn_detector(hstats, hold_n)
    sysout = {"healthy_file": man["healthy_file"], "n_train_days": det.n_train_days,
              "holdout_days": det.holdout_days, "holdout_fp_days": det.holdout_fp_days,
              "holdout_days_definition": "days of the last-8-per-month holdout on which the channel has any statistic "
                                        "(87 on SDAHU); joint_fpr below uses the 96 calendar holdout days",
              "holdout_fp_rate": round(det.holdout_fp_days / max(det.holdout_days, 1), 4),
              "monitored_statistics": len(det.bands),
              "bands": {k: [round(v[0], 1), round(v[1], 1)] for k, v in det.bands.items()},
              "scenarios": []}
    p0 = max(det.holdout_fp_days, 1) / max(det.holdout_days, 1)
    # joint false-alarm budget: the deployed union's holdout FP dates (committed
    # union_fpr artefact, rate excluded) plus this channel's own holdout FP dates
    hcl = classify_sojourn_days(det, hstats)
    hold_days = holdout_mask(pd.Series(hstats.index.astype(str), index=hstats.index), hold_n)
    time_fp_dates = sorted(set(hcl.loc[hcl["flagged"].values & hold_days.values, "day"]))
    ufpr = json.loads(Path(f"outputs/union_fpr_{system}.json").read_text())
    deployed_fp = set()
    for ch, v in ufpr["channels"].items():
        if ch != "rate":
            deployed_fp |= set(v.get("holdout_fp_dates", []))
    joint = deployed_fp | set(time_fp_dates)
    sysout["holdout_fp_dates"] = time_fp_dates
    sysout["joint_fpr"] = {"deployed_union_minus_rate_fp_days": len(deployed_fp),
                           "with_time_channel_fp_days": len(joint),
                           "holdout_days": ufpr["holdout_days"],
                           "with_time_channel_rate": round(len(joint) / ufpr["holdout_days"], 4)}
    print(f"== {system}: {len(det.bands)} statistics monitored; holdout FP {det.holdout_fp_days}/{det.holdout_days}; "
          f"joint FP {len(deployed_fp)} -> {len(joint)} of {ufpr['holdout_days']}")
    for sc in man["scenarios"]:
        if not sc["is_fault"] or sc.get("exclude"):
            continue
        df = pd.read_parquet(f"data/processed/{system}/{sc['file']}.parquet")
        st = daily_sojourn_stats(abstract_events(df, cfg), cfg)
        cl = classify_sojourn_days(det, st)
        flagged = set(cl.loc[cl["flagged"], "day"])
        n_eval = int(len(cl))
        p = float(binom_sf(len(flagged), n_eval, p0)) if n_eval else 1.0
        # the suite carries two floors: max(fp,1)/n (residual, model) and a
        # rule-of-three floor (rules, frequency, oscillation); both are reported
        p0_r3 = max(det.holdout_fp_days, 3) / max(det.holdout_days, 1)
        p_r3 = float(binom_sf(len(flagged), n_eval, p0_r3)) if n_eval else 1.0
        c = card[sc["file"]]
        missing = [k for k in DEPLOYED + ["freq", "sig_union"] if k not in c.get("flag_days", {})]
        assert not missing, f"scorecard flag_days lacks {missing} (L36: assert the keys you compare against)"
        union = set()
        for ch in DEPLOYED:
            union |= set(c.get("flag_days", {}).get(ch, []))
        freq = set(c.get("flag_days", {}).get("freq", []))
        sig_union = set(c.get("flag_days", {}).get("sig_union", []))
        viol = pd.Series([v for vs in cl.loc[cl["flagged"], "violations"] for v in vs]).value_counts()
        # time-to-detect: days from the file's first day to the first flagged day
        # (scorecard ttd_days uses the same origin); None when never flagged
        day0 = pd.to_datetime(df["Datetime"]).min().normalize()
        ttd_time = (int((pd.to_datetime(min(flagged)) - day0).days) + 1) if flagged else None
        row = {"file": sc["file"], "family": sc.get("family"),
               "n_days": n_eval,                       # days with any sojourn statistic (the channel abstains otherwise)
               "scorecard_evaluable_days": c.get("evaluable_days"),
               "ttd_time_days": ttd_time if p < P_SIG else None,   # gated meaning only when significant
               "ttd_deployed_days": c.get("ttd_days"),
               "time_flag_days": len(flagged), "p": p, "significant": p < P_SIG,
               "p_rule_of_three_floor": p_r3, "significant_rule_of_three_floor": p_r3 < P_SIG,
               "deployed_detected": bool(c["meaningful_channels"]),
               "deployed_union_days": len(union),
               "unique_days_vs_deployed": len(flagged - union),
               "unique_days_vs_sig_union": len(flagged - sig_union),
               "unique_days_vs_frequency": len(flagged - freq),
               "top_violations": {k: int(v) for k, v in viol.head(4).items()}}
        sysout["scenarios"].append(row)
        print(f"  {sc['file'][:38]:38s} time {len(flagged):3d}/{n_eval} p={p:.1e} {'SIG' if p < P_SIG else '   '} "
              f"| deployed {'DET' if row['deployed_detected'] else 'miss'} union {len(union):3d} "
              f"| unique {row['unique_days_vs_deployed']:3d} (vs freq {row['unique_days_vs_frequency']:3d}) "
              f"| {list(viol.head(2).index)}")
    out["systems"][system] = sysout

rows = [r for s in out["systems"].values() for r in s["scenarios"]]
sig = [r for r in rows if r["significant"]]
sig_missed = [r["file"] for r in sig if not r["deployed_detected"]]
sig_fouling = [r["file"] for r in sig if FOULING in r["file"]]
uniq_vs_freq = [r["file"] for r in sig if r["unique_days_vs_frequency"] > 0]
worst_fp = max(s["holdout_fp_rate"] for s in out["systems"].values())
sig_r3 = [r for r in rows if r["significant_rule_of_three_floor"]]
pred = {"P1_sig_ge_5": len(sig) >= 5, "P1_count": len(sig),
        "P1_count_rule_of_three_floor": len(sig_r3),
        "floor_dependent_scenarios": [r["file"] for r in sig if not r["significant_rule_of_three_floor"]],
        "P2_no_fouling_sig": len(sig_fouling) == 0, "P2_fouling_sig": sig_fouling,
        "P3_reduces_misses": len(sig_missed) >= 1, "P3_newly_detected": sig_missed,
        "P4_unique_vs_frequency_ge_3": len(uniq_vs_freq) >= 3, "P4_scenarios": uniq_vs_freq}
fired = []
if worst_fp > 0.10:
    fired.append("F-X12.a: holdout false-alarm rate > 10% on a system")
if not pred["P3_reduces_misses"] and not pred["P4_unique_vs_frequency_ge_3"]:
    fired.append("F-X12.b: no new scenario and no unique days beyond frequency — time perspective redundant")
if not pred["P2_no_fouling_sig"]:
    fired.append("F-X12.c: a fouling scenario is significant — the 'identical log' diagnosis is wrong somewhere")
out["notes"] = [
    "P4 as pre-registered is a low bar: unique days against one channel (frequency), not against the deployed union; it cannot rescue P3.",
    "A first run compared against scorecard keys that do not exist (absence, frequency, oscillation) and left P4 uncomputed; corrected to the exported keys before anything was adopted (pre-registration erratum).",
    "ttd_time_days is the channel's first raw flag; the scorecard's ttd_days comes from significance-gated channels, so the comparison is asymmetric in kind and only reported where the time channel is significant.",
    "The suite carries two significance floors; p is given under both. n_days counts days on which the channel has any statistic (its abstention rule), beside the scorecard's evaluable days.",
]
out["n_scored"] = len(rows)
out["predictions"] = pred
out["falsifiers_fired"] = fired
out["worst_holdout_fp_rate"] = worst_fp
Path("outputs/x12_time_perspective.json").write_text(json.dumps(out, indent=2) + "\n")
print("\npredictions:", json.dumps(pred, indent=1))
print("falsifiers fired:", fired or "none")
print("wrote outputs/x12_time_perspective.json")
