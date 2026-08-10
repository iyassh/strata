"""Rigorous per-day benchmark of ProcessHeal on the LBNL SDAHU scenarios.

Design (fixes the audited flaws of the first benchmark):
- Temporal split: model discovered from healthy TRAIN days only; the detection
  threshold is calibrated on HELD-OUT healthy days at the configured
  false-positive quantile. No hand-picked margin; the training file is never
  scored as a negative.
- Unit of evaluation: the DAY (one trace). ~5,300 scored trace-days instead of
  15 file-level calls, reported as precision/recall/F1 with Wilson CIs.
- ALPHABET SPLIT (STRATA v2, Phase 1): the model channel is state-events-only
  END TO END — discovery, calibration and scoring all run on the state slice
  (enforced inside build_detector/classify_days), so the discovered model can
  no longer re-encode the signature rules. The ablation is therefore honest:
    rules-only  — a day is flagged iff an actuator-signature event
                  (mismatch/leak kinds) occurred that day; no model at all.
    model-only  — a day is flagged only by state-alphabet conformance fitness
                  (missing/ordering behaviour) against the healthy model.
    combined    — signature event OR state-fitness below the calibrated
                  threshold; each channel FPR-controlled on held-out days.
  Also reported: the model channel's UNIQUE contribution — fault days flagged
  by the model that the rules missed. That number is what Phase 1 exists to
  measure.

Scenario notes: the four coi_leakage_* files are byte-identical (one shown);
the four oa_bias_* files are byte-identical to EACH OTHER and contain no
injected bias, but are a DISTINCT healthy-like simulation run — scored here as
an out-of-sample negative. damper_stuck_100 covers Apr-Nov only (215 days).
"""

import os

os.environ["TQDM_DISABLE"] = "1"

import json
import math
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

from processheal.core.detection import build_detector, classify_days
from processheal.hvac.events import abstract_events, emitted_event_names
from processheal.io.config import load_config

DATA = Path("data/processed/sdahu")
cfg = load_config("configs/lbnl_sdahu")

# (file, category, is_fault_ground_truth)
SCENARIOS = [
    ("damper_stuck_010_annual", "damper stuck 10%", True),
    ("damper_stuck_025_annual", "damper stuck 25%", True),
    ("damper_stuck_075_annual", "damper stuck 75%", True),
    ("damper_stuck_100_annual_short", "damper stuck 100%", True),
    ("coi_stuck_010_annual", "valve stuck 10%", True),
    ("coi_stuck_025_annual", "valve stuck 25%", True),
    ("coi_stuck_050_annual", "valve stuck 50%", True),
    ("coi_stuck_075_annual", "valve stuck 75%", True),
    ("coi_leakage_010_annual", "valve leaking", True),
    ("coi_bias_-4_annual", "SA sensor bias -4C", True),
    ("coi_bias_-2_annual", "SA sensor bias -2C", True),
    ("coi_bias_2_annual", "SA sensor bias +2C", True),
    ("coi_bias_4_annual", "SA sensor bias +4C", True),
    ("oa_bias_4_annual", "independent healthy-like run", False),
]

SIGNATURE_EVENTS = emitted_event_names(cfg, kinds=("mismatch", "leak"))


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def rules_only_flags(log: pd.DataFrame) -> pd.Series:
    """day -> flagged iff any actuator-signature event occurred (no model)."""
    days = pd.Index(sorted(log["case_id"].unique()))
    sig_days = set(log.loc[log["activity"].isin(SIGNATURE_EVENTS), "case_id"])
    return pd.Series([d in sig_days for d in days], index=days)


print("=" * 78)
print("ProcessHeal rigorous benchmark — temporal split, per-day evaluation")
print("=" * 78)

healthy_log = abstract_events(pd.read_parquet(DATA / "AHU_annual.parquet"), cfg)
det = build_detector(cfg, healthy_log)
n_hold = len(det.holdout_per_day)
print(f"\nmodel: discovered from {det.n_train_days} healthy train days")
print(f"threshold: {det.threshold:.4f} = q{cfg.rules['detection']['fpr_quantile']:.2f} "
      f"of {n_hold} HELD-OUT healthy days (learned, not hand-picked)")
print(f"held-out healthy false-positive rate: {det.holdout_fpr:.1%}")

rows = []
# out-of-sample negatives: held-out healthy days + the independent healthy-like run
neg = {
    "combined": [int((det.holdout_per_day["fitness"] < det.threshold).sum()), n_hold],
    "rules": [0, n_hold],  # healthy holdout has no signature events by validation
    "structure": [int((det.holdout_per_day["fitness"] < det.threshold).sum()), n_hold],
}
pos = {"combined": [0, 0], "rules": [0, 0], "structure": [0, 0]}

print(f"\n{'scenario':30s} {'days':>5} {'rules-only':>11} {'structure':>10} {'combined':>9}")
print("-" * 78)

unique_model_days = 0  # fault days the model flags that the rules missed

for fname, category, is_fault in SCENARIOS:
    log = abstract_events(pd.read_parquet(DATA / f"{fname}.parquet"), cfg)
    n_days = log["case_id"].nunique()

    # model channel: classify_days scores the STATE slice only (split enforced)
    per_day = classify_days(det, log)
    fit_by_day = per_day.set_index("case_id")["flagged"]

    rule_flags = rules_only_flags(log)
    rules_flagged = int(rule_flags.sum())

    model_flags = fit_by_day.reindex(rule_flags.index, fill_value=False)
    structure_flagged = int(model_flags.sum())

    combined_flagged = int((rule_flags | model_flags).sum())
    unique_model = int((model_flags & ~rule_flags).sum())
    if is_fault:
        unique_model_days += unique_model

    for name, k in (("combined", combined_flagged), ("rules", rules_flagged),
                    ("structure", structure_flagged)):
        bucket = pos if is_fault else neg
        bucket[name][0] += k
        bucket[name][1] += n_days

    top_unexpected = next(iter(per_day.attrs["unexpected_by_activity"]), "-")
    print(f"{category:30s} {n_days:>5} {rules_flagged / n_days:>10.0%} "
          f"{structure_flagged / n_days:>9.0%} {combined_flagged / n_days:>8.0%}"
          f"   model-unique: {unique_model:>3}   top: {top_unexpected}")
    rows.append({
        "file": fname, "category": category, "is_fault": is_fault, "days": n_days,
        "rules_only_flagged": rules_flagged, "model_only_flagged": structure_flagged,
        "model_unique_days": unique_model, "combined_flagged": combined_flagged,
        "per_day_fitness": [round(float(f), 4) for f in per_day["fitness"]],
        "top_unexpected": per_day.attrs["unexpected_by_activity"],
        "top_missing": per_day.attrs["missing_by_activity"],
    })

print("-" * 78)
print(f"\n{'metric (per-day, out-of-sample)':38s} {'rules-only':>11} {'structure':>10} {'combined':>9}")
summary = {}
for name in ("rules", "structure", "combined"):
    tp, p_n = pos[name]
    fp, n_n = neg[name]
    recall = tp / p_n if p_n else 0.0
    fpr = fp / n_n if n_n else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    rlo, rhi = wilson_ci(tp, p_n)
    summary[name] = {"recall": recall, "fpr": fpr, "precision": precision, "f1": f1,
                     "recall_ci": [rlo, rhi], "tp": tp, "pos_days": p_n,
                     "fp": fp, "neg_days": n_n}
print(f"{'recall (fault days flagged)':38s} "
      f"{summary['rules']['recall']:>10.1%} {summary['structure']['recall']:>9.1%} "
      f"{summary['combined']['recall']:>8.1%}")
print(f"{'false-positive rate (healthy days)':38s} "
      f"{summary['rules']['fpr']:>10.1%} {summary['structure']['fpr']:>9.1%} "
      f"{summary['combined']['fpr']:>8.1%}")
print(f"{'precision':38s} "
      f"{summary['rules']['precision']:>10.1%} {summary['structure']['precision']:>9.1%} "
      f"{summary['combined']['precision']:>8.1%}")
print(f"{'F1':38s} "
      f"{summary['rules']['f1']:>10.3f} {summary['structure']['f1']:>9.3f} "
      f"{summary['combined']['f1']:>8.3f}")
r = summary["combined"]
print(f"\ncombined recall 95% CI: [{r['recall_ci'][0]:.1%}, {r['recall_ci'][1]:.1%}] "
      f"over {r['pos_days']:,} fault days; negatives = {r['neg_days']:,} out-of-sample "
      f"healthy days")
print(f"model channel UNIQUE contribution: {unique_model_days} fault days flagged "
      f"by state-alphabet conformance that the rules missed")

out = Path("outputs")
out.mkdir(exist_ok=True)
(out / "benchmark_v3.json").write_text(json.dumps({
    "alphabet_split": True,
    "threshold": det.threshold, "train_days": det.n_train_days,
    "holdout_days": n_hold, "holdout_fpr": det.holdout_fpr,
    "unique_model_fault_days": unique_model_days,
    "holdout_fitness": [round(float(f), 4) for f in det.holdout_per_day["fitness"]],
    "scenarios": rows, "summary": summary,
}, indent=2, default=str))
print("\nwrote outputs/benchmark_v3.json")
