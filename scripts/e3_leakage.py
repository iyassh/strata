"""ERRATA E3 as a measurement, not an assertion.

On SDAHU, SA_SP and SA_SPSPT are encoded differently in the healthy file
than in every fault file (ERRATA.md E3). This script asks the leakage
question directly: does a one-feature rule, chosen on the HEALTHY file
alone, separate healthy days from fault-file days by provenance?

    uv run python scripts/e3_leakage.py   -> outputs/e3_leakage.json
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "processed" / "sdahu"
healthy = "AHU_annual"

def day_medians(f):
    df = pd.read_parquet(D / f"{f}.parquet", columns=["Datetime", "SA_SP", "SA_SPSPT"])
    df["day"] = pd.to_datetime(df["Datetime"]).dt.date
    return df.groupby("day")[["SA_SP", "SA_SPSPT"]].median()

h = day_medians(healthy)
# thresholds chosen from the healthy file ONLY: the midpoint between its
# minimum and zero, i.e. no fault file is consulted when choosing them
thr = {c: float(h[c].min()) / 2.0 for c in ("SA_SP", "SA_SPSPT")}
rule = {c: f"{c} day-median > {thr[c]:.4f}  => classified as healthy-file day" for c in thr}

files = sorted(p.stem for p in D.glob("*.parquet") if p.stem != healthy)
res = {"healthy_file": healthy, "n_fault_files": len(files), "rule_chosen_on": "healthy file only",
       "thresholds": thr, "rule": rule, "per_feature": {}}
for c in thr:
    tp = int((h[c] > thr[c]).sum()); hn = int(len(h))
    per_file = {}; fp_total = 0; n_total = 0
    for f in files:
        m = day_medians(f)[c]
        fp = int((m > thr[c]).sum()); per_file[f] = {"days": int(len(m)), "misclassified_as_healthy": fp,
                                                    "range": [float(m.min()), float(m.max())],
                                                    "mean_of_day_medians": float(m.mean())}
        fp_total += fp; n_total += int(len(m))
    res["per_feature"][c] = {
        "healthy_days": hn, "healthy_days_classified_healthy": tp,
        "fault_days": n_total, "fault_days_misclassified_as_healthy": fp_total,
        "accuracy": (tp + (n_total - fp_total)) / (hn + n_total),
        "healthy_range": [float(h[c].min()), float(h[c].max())],
        "per_file": per_file}
res["verdict"] = ("A single threshold on either column, chosen from the healthy file alone, "
                  "separates every healthy day from every fault-file day. Any model given these "
                  "columns can classify file provenance perfectly without reference to any fault.")
(ROOT / "outputs" / "e3_leakage.json").write_text(json.dumps(res, indent=2) + "\n")
for c, r in res["per_feature"].items():
    print(f"{c:9s} healthy {r['healthy_days_classified_healthy']}/{r['healthy_days']} | fault misclassified "
          f"{r['fault_days_misclassified_as_healthy']}/{r['fault_days']} | accuracy {r['accuracy']:.4f} | "
          f"healthy range {r['healthy_range']}")
