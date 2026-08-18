"""Phase 5 runner — the pre-registered cross-system grammar experiment.

    caffeinate -i uv run python scripts/grammar.py

Produces outputs/grammar_results.json: M1/M2/M3 matrices, the order-shuffle
null, engineering-truth table, and the leave-one-out cold-start — exactly
the deliverables in PHASE5_PLAN.md.
"""

import json
import os
import warnings
from math import comb
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")

import pandas as pd
import yaml

import sys
sys.path.insert(0, "src")

from processheal.core.grammar import (CANONICAL, band_violation_days, canonical_day_counts,
                                      canonical_log, count_bands, fitness_distribution,
                                      log_profile_distance, shuffle_within_traces,
                                      split_train_holdout)
from processheal.core.discovery import discover_model
from processheal.core.conformance import check_conformance
from processheal.hvac.events import abstract_events
from processheal.io.config import load_config

SYSTEMS = ["sdahu", "pfpu", "sfpu"]
HEALTHY = {"sdahu": "AHU_annual", "pfpu": "PFPU_FaultFree", "sfpu": "SFPU_FaultFree"}
NULL_SEEDS = [11, 22, 33, 44, 55]


def binom_sf(k, n, p):
    if n <= 0:
        return 1.0
    return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(min(k, n), n + 1))


print("=" * 90)
print("Phase 5 — cross-system grammar (pre-registered: PHASE5_PLAN.md)")
print("=" * 90)

# ---- load, project, split ----
data = {}
for s in SYSTEMS:
    cfg = load_config(f"configs/lbnl_{s}")
    df = pd.read_parquet(f"data/processed/{s}/{HEALTHY[s]}.parquet")
    log = canonical_log(abstract_events(df, cfg))
    hn = cfg.rules["detection"]["holdout_days_per_month"]
    train, hold = split_train_holdout(log, hn)
    counts = canonical_day_counts(log)
    tmask = ~counts.index.astype(str).isin(set(hold["case_id"]))
    data[s] = {
        "cfg": cfg, "train": train, "hold": hold,
        "counts_train": counts[tmask], "counts_hold": counts[~tmask],
        "alphabet": sorted(log["activity"].unique()),
    }
    print(f"[{s}] canonical activities present: {len(data[s]['alphabet'])}/10 "
          f"| train days {train['case_id'].nunique()} hold {hold['case_id'].nunique()}")

# ---- discover canonical models + count bands per system ----
for s in SYSTEMS:
    net, im, fm = discover_model(data[s]["train"][["case_id", "activity", "timestamp"]])
    data[s]["model"] = (net, im, fm)
    data[s]["bands"] = count_bands(data[s]["counts_train"])

# ---- M1: alignment cross-fitness (holdout days of j on model of i) ----
M1, M1_null = {}, {}
for i in SYSTEMS:
    net, im, fm = data[i]["model"]
    for j in SYSTEMS:
        cell = f"{j}_on_{i}"
        conf = check_conformance(data[j]["hold"][["case_id", "activity", "timestamp"]], net, im, fm)
        M1[cell] = fitness_distribution(conf["per_day"])
        # order-shuffle null (counts preserved)
        null_means = []
        for seed in NULL_SEEDS:
            sh = shuffle_within_traces(data[j]["hold"], seed)
            nc = check_conformance(sh[["case_id", "activity", "timestamp"]], net, im, fm)
            null_means.append(float(nc["per_day"]["fitness"].mean()))
        M1_null[cell] = {"null_mean_of_means": round(sum(null_means) / len(null_means), 4),
                         "observed_mean": M1[cell]["mean"],
                         "order_signal": round(M1[cell]["mean"] - sum(null_means) / len(null_means), 4)}
        print(f"M1 {cell:16s} mean {M1[cell]['mean']:.3f} (null {M1_null[cell]['null_mean_of_means']:.3f}, "
              f"order-signal {M1_null[cell]['order_signal']:+.3f})")

# ---- M2: count-band cross-violation rates (holdout of j vs bands of i) ----
M2 = {}
for i in SYSTEMS:
    for j in SYSTEMS:
        v = band_violation_days(data[j]["counts_hold"], data[i]["bands"])
        M2[f"{j}_on_{i}"] = {"violation_rate": round(float(v.mean()), 4) if len(v) else None,
                             "n_days": int(len(v))}
print("\nM2 violation rates:")
for i in SYSTEMS:
    print("  " + " ".join(f"{M2[f'{j}_on_{i}']['violation_rate']:.2f}({j})" for j in SYSTEMS) + f"  <- bands of {i}")

# ---- M3: model-free log profile distances ----
M3 = {}
for i in SYSTEMS:
    for j in SYSTEMS:
        M3[f"{i}_vs_{j}"] = log_profile_distance(
            canonical_day_counts_full := data[i]["counts_train"], data[j]["counts_train"])
print("\nM3 profile distances (train days):")
for i in SYSTEMS:
    print("  " + " ".join(f"{M3[f'{i}_vs_{j}']:.2f}" for j in SYSTEMS) + f"  <- {i}")

# ---- engineering-truth table (from discovered bands/alphabets alone) ----
truth = {}
for s in SYSTEMS:
    b = data[s]["bands"]
    ct = data[s]["counts_train"]
    heat_frac = float((ct["heating_active"] > 0).mean()) if "heating_active" in ct.columns else 0.0
    truth[s] = {
        "has_night_cycle": "night_cycle_started" in data[s]["alphabet"],
        "has_heating": "heating_active" in data[s]["alphabet"],
        # rhythm = active on >=95% of train days (train-min was the wrong
        # instrument: one zero-heating day in 269 destroys it — instrument
        # bug caught in the Phase-5 self-analysis, fixed before audit)
        "heating_active_day_fraction": round(heat_frac, 3),
        "heating_daily_rhythm": bool(heat_frac >= 0.95),
        "has_economizer": "economizer_window_entered" in data[s]["alphabet"],
    }
print("\nengineering truth (discovered, not told):")
for s, t in truth.items():
    print(f"  {s}: {t}")

# ---- cold-start: leave-one-out count-band transfer ----
coldstart = {}
for target in SYSTEMS:
    sources = [s for s in SYSTEMS if s != target]
    # union bands over source-shared activities, intersected with the
    # target's CONFIGURED alphabet (config exists day one; data does not)
    shared = set(data[sources[0]]["bands"]) & set(data[sources[1]]["bands"])
    shared &= set(data[target]["alphabet"])
    bands = {a: (min(data[sources[0]]["bands"][a][0], data[sources[1]]["bands"][a][0]),
                 max(data[sources[0]]["bands"][a][1], data[sources[1]]["bands"][a][1]))
             for a in shared}
    # zero-shot FP estimate on the target's holdout (validation only)
    fp = band_violation_days(data[target]["counts_hold"], bands)
    fp_rate = float(fp.mean()) if len(fp) else 1.0
    p0 = max(fp_rate, 3.0 / 365.0)
    # score the target's full scenario suite
    manifest = yaml.safe_load(Path(f"configs/lbnl_{target}/scenarios.yaml").read_text())
    det, tot = 0, 0
    per_family = {}
    for sc in manifest["scenarios"]:
        if sc.get("exclude"):
            continue
        df = pd.read_parquet(f"data/processed/{target}/{sc['file']}.parquet")
        counts = canonical_day_counts(abstract_events(df, data[target]["cfg"]))
        v = band_violation_days(counts, bands)
        k, n = int(v.sum()), int(len(v))
        sig = binom_sf(k, n, min(p0, 1.0)) < 1e-3
        tot += 1
        det += int(sig)
        fam = per_family.setdefault(sc["family"], [0, 0])
        fam[1] += 1
        fam[0] += int(sig)
    coldstart[target] = {
        "sources": sources, "shared_activities": sorted(shared),
        "zero_shot_fp_rate_on_target_holdout": round(fp_rate, 4),
        "detected": det, "of": tot,
        "per_family": {k: f"{a}/{b}" for k, (a, b) in sorted(per_family.items())},
    }
    print(f"\ncold-start -> {target}: {det}/{tot} zero-shot "
          f"(fp on target holdout {fp_rate:.3f}; shared activities {len(shared)})")
    print(f"   {coldstart[target]['per_family']}")

Path("outputs").mkdir(exist_ok=True)
Path("outputs/grammar_results.json").write_text(json.dumps({
    "canonical_alphabet": CANONICAL,
    "alphabets": {s: data[s]["alphabet"] for s in SYSTEMS},
    "bands": {s: data[s]["bands"] for s in SYSTEMS},
    "M1": M1, "M1_null": M1_null, "M2": M2, "M3": M3,
    "engineering_truth": truth, "coldstart": coldstart,
}, indent=2))
print("\nwrote outputs/grammar_results.json")
