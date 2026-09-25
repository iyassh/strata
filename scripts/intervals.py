"""Confidence intervals and the paired test quoted in the manuscript, regenerated from
the committed artefacts so that they sit under the regression gate like every other number.

    uv run python scripts/intervals.py -> outputs/intervals.json

Wilson 95 % intervals for the deployed and naive false-alarm rates (union_fpr_*.json), the PCA
baseline's strict false-alarm rates (baselines_*.json), the three-system detection counts
(benchmark_v6_*.json, adjudicated 56/73 per x11_branch.json, naive 57/73, baseline 61/73), and the
exact McNemar test on the discordant scenarios between STRATA (adjudicated) and the strict PCA baseline.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from scipy.stats import binom

REPO = Path(__file__).resolve().parents[1]
THREE = ["sdahu", "pfpu", "sfpu"]
ALL = ["sdahu", "pfpu", "sfpu", "ddahu", "fcu", "rtu_sim", "rtu_field"]
ADJUDICATED_OUT = {"oa_bias_4_annual"}   # X11 branch adjudication (ERRATA E5)


def wilson(k: int, n: int, z: float = 1.959964) -> list[float]:
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [abs(round(100 * (c - h), 1)), round(100 * (c + h), 1)]


def load(name):
    return json.loads((REPO / "outputs" / name).read_text())


def main() -> int:
    out = {"method": "Wilson score interval, 95 %, z = 1.959964; McNemar exact two-sided binomial on discordant pairs", "false_alarm_rates": {}, "detection": {}, "mcnemar": {}}
    for s in ALL:
        p = REPO / f"outputs/union_fpr_{s}.json"
        if not p.exists():
            continue
        u = json.loads(p.read_text())
        n = u["holdout_days"]
        out["false_alarm_rates"][s] = {"deployed": [u["union_minus_rate"]["holdout_fp_days"], n, wilson(u["union_minus_rate"]["holdout_fp_days"], n)],
                                       "naive": [u["union_all8"]["holdout_fp_days"], n, wilson(u["union_all8"]["holdout_fp_days"], n)]}
    for s in THREE:
        b = load(f"baselines_{s}.json")
        k, n = b["pca_holdout_fp_strict"]
        out["false_alarm_rates"][s]["pca_strict"] = [k, n, wilson(k, n)]
    strata, base, so, bo = {}, {}, [], []
    for s in THREE:
        card = load(f"benchmark_v6_{s}.json")["scenarios"]
        bl = {v["file"]: bool(v["pca_sig_strict"]) for v in load(f"baselines_{s}.json")["scenarios"]}
        for x in card:
            if not x["is_fault"] or x["excluded"]:
                continue
            strata[x["file"]] = bool(x["meaningful_channels"]) and x["file"] not in ADJUDICATED_OUT
            base[x["file"]] = bl[x["file"]]
    n = len(strata); ks = sum(strata.values()); kb = sum(base.values())
    naive = ks + sum(1 for f in ADJUDICATED_OUT if f in strata)
    out["detection"] = {"n_scenarios": n, "strata_adjudicated": [ks, n, wilson(ks, n)], "strata_naive": [naive, n, wilson(naive, n)], "pca_strict": [kb, n, wilson(kb, n)]}
    so = sorted(f for f in strata if strata[f] and not base[f]); bo = sorted(f for f in strata if base[f] and not strata[f])
    d = len(so) + len(bo)
    p = min(1.0, 2 * binom.cdf(min(len(so), len(bo)), d, 0.5)) if d else None
    out["mcnemar"] = {"strata_only": so, "baseline_only": bo, "discordant": d, "exact_p_two_sided": round(p, 4) if p is not None else None,
                      "both_miss": sorted(f for f in strata if not strata[f] and not base[f])}
    (REPO / "outputs/intervals.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "method"}, indent=1)[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
