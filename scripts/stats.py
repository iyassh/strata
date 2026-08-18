"""Phase 4 statistics battery — exact McNemar + BH + per-family comparison.

Questions answered, per system:
  Q1 What does each STRATA channel MARGINALLY add over the rules channel?
     (exact-binomial McNemar on per-day flags, per scenario, BH-corrected)
  Q2 STRATA sig-union vs PCA-SPE at the FPR-MATCHED strict threshold
     (train-max calibration, mirroring our extreme-calibrated channels).
  Q3 Per-family detection map: STRATA vs PCA-strict — who sees what.

Method notes (guidance-sourced): exact binomial McNemar (Dietterich 1998;
small discordant counts are the norm here); BH (Benjamini-Hochberg 1995)
across scenarios within a system; day-level autocorrelation stated as a
limitation — scenario-level detection remains the primary evidence.

    uv run python scripts/stats.py <system>
"""

import json
import sys
from math import comb
from pathlib import Path

SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "sfpu"


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact binomial McNemar p-value for discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def bh(pvals: list[float], q: float = 0.05) -> list[bool]:
    """Benjamini-Hochberg: which hypotheses survive at FDR q."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    keep = [False] * m
    max_k = 0
    for rank, i in enumerate(order, start=1):
        if pvals[i] <= q * rank / m:
            max_k = rank
    for rank, i in enumerate(order, start=1):
        if rank <= max_k:
            keep[i] = True
    return keep


bench = json.loads(Path(f"outputs/benchmark_v6_{SYSTEM}.json").read_text())
base = json.loads(Path(f"outputs/baselines_{SYSTEM}.json").read_text())
base_by_file = {r["file"]: r for r in base["scenarios"]}

print("=" * 96)
print(f"Phase 4 statistics — {SYSTEM}")
print("=" * 96)
print(f"PCA strict holdout FP: {base['pca_holdout_fp_strict']} "
      f"(vs 99th-pct {base['pca_holdout_fp']}) — strict matches our calibration style")

# Q1: marginal contribution of freq/rate over rules — tested against the
# CHANNELS' OWN holdout noise rate (Phase-4 audit fix: the c=0 "McNemar" was a sign
# test against an impossible 50/50 null; any 11 noise days earned a star).
fq = bench.get("frequency") or {}
u_fp = (fq.get("unit_holdout_fp") or [0, 1])
d_fp = (fq.get("device_holdout_fp") or [0, 1])
r_fp = (fq.get("rate_holdout_fp") or [0, 1])
p_noise = (u_fp[0] / max(u_fp[1], 1) + d_fp[0] / max(d_fp[1], 1)
           + r_fp[0] / max(r_fp[1], 1))
p_noise = max(p_noise, 3.0 / 365.0)
print(f"\nQ1 - marginal freq/rate days over rules, vs channel noise null "
      f"p0={p_noise:.4f} (binomial, BH at q=0.05):")
p1, rows1 = [], []
for r in bench["scenarios"]:
    fd = r.get("flag_days", {})
    rules = set(fd.get("rules", []))
    added = (set(fd.get("freq", [])) | set(fd.get("rate", []))) - rules
    b = len(added)
    n = max(r["evaluable_days"], 1)
    pv = sum(comb(n, i) * p_noise**i * (1 - p_noise)**(n - i)
             for i in range(min(b, n), n + 1)) if b else 1.0
    p1.append(pv)
    rows1.append((r["label"], b, pv))
keep1 = bh(p1)
for (label, b, pv), k in zip(rows1, keep1):
    if b > 0:
        print(f"  {label:38s} +{b:>3} days  p={pv:.2e} {'BH-SIG' if k else 'ns'}")

# Q2: STRATA sig-union vs PCA-strict per scenario
print(f"\nQ2 - STRATA (sig-union) vs PCA-SPE (strict, FPR-matched):")
p2, rows2 = [], []
for r in bench["scenarios"]:
    fd = r.get("flag_days", {})
    # intersect day universes (audit D2): both methods judged only on days
    # both could score
    uni_pca = set(base_by_file[r["file"]].get("scored_days", []))
    strata = set(fd.get("sig_union", [])) & uni_pca if uni_pca else set(fd.get("sig_union", []))
    pca = set(base_by_file[r["file"]].get("pca_strict_flag_days", []))
    b = len(strata - pca)   # days only STRATA flags
    c = len(pca - strata)   # days only PCA flags
    pv = mcnemar_exact(b, c)
    p2.append(pv)
    rows2.append((r["label"], r["family"], len(strata), len(pca), b, c, pv))
keep2 = bh(p2)
print(f"  {'scenario':38s} {'strata':>6} {'pca':>5} {'onlyS':>5} {'onlyP':>5} {'p':>9}")
for (label, fam, ns, np_, b, c, pv), k in zip(rows2, keep2):
    tag = "BH-SIG" if k else "ns"
    lead = "PCA" if c > b else ("STRATA" if b > c else "tie")
    print(f"  {label:38s} {ns:>6} {np_:>5} {b:>5} {c:>5} {pv:>9.2e} {tag} ({lead})")

# Q3: family map
print(f"\nQ3 - family detection map (meaningful scenarios):")
fams = {}
for r in bench["scenarios"]:
    fams.setdefault(r["family"], [0, 0, 0])
    fams[r["family"]][2] += 1
    if r.get("meaningful_channels"):
        fams[r["family"]][0] += 1
    if base_by_file[r["file"]].get("pca_sig_strict"):
        fams[r["family"]][1] += 1
print(f"  {'family':16s} {'STRATA':>7} {'PCA-strict':>10} {'of':>4}")
for f, (a, b_, n) in sorted(fams.items()):
    marker = "  <- PCA-only family" if b_ > 0 and a == 0 else ""
    print(f"  {f:16s} {a:>7} {b_:>10} {n:>4}{marker}")
