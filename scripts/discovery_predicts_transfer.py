"""Score the pre-registered test: does discovery predict where a rule transfers?

Pre-registration (committed BEFORE this script was written or run):
  docs/plans/2026-09-23-discovery-predicts-transfer-prereg.md

Inputs
  --q   JSON from the sealed computation: per system Q_support, Q_obligatory
  outputs/matched_rules_{sdahu,pfpu,sfpu}.json : healthy_fp for mr1/mr2/mr3

Output
  outputs/discovery_predicts_transfer.json with P1/P2/P3 and the verdicts.

The scoring rule below is fixed by the pre-registration; nothing here is a
free parameter. Spearman rho and a permutation p are implemented by hand so
the result does not depend on an optional dependency.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("sdahu", "pfpu", "sfpu")
# Amendment 1: SDAHU has no heating signal; its cells are reported, not scored.
SCORED = ("pfpu", "sfpu")
RULES = ("mr1", "mr2", "mr3")
N_PERM = 10_000
SEED = 7


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = _ranks(x), _ranks(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else 0.0


def main() -> int:
    if "--q" not in sys.argv:
        print("usage: discovery_predicts_transfer.py --q /path/q_values.json")
        return 2
    q = json.loads(Path(sys.argv[sys.argv.index("--q") + 1]).read_text())
    fp = {s: json.loads((ROOT / "outputs" / f"matched_rules_{s}.json").read_text())["healthy_fp"]
          for s in SYSTEMS}

    all_cells = [(r, s) for r in RULES for s in SYSTEMS]
    cells = [(r, s) for r in RULES for s in SCORED]          # Amendment 1
    qs = [float(q[s]["Q_support"]) for _, s in cells]
    ys = [int(fp[s][r]) for r, s in cells]

    # P1: firings decrease in Q_support -> rho < 0, permutation p < 0.05
    rho = spearman(qs, ys)
    rng = random.Random(SEED)
    hits = 0
    for _ in range(N_PERM):
        perm = ys[:]
        rng.shuffle(perm)
        if spearman(qs, perm) <= rho:
            hits += 1
    p1_p = hits / N_PERM
    p1_pass = rho < 0 and p1_p < 0.05

    # P2: obligatory <-> zero firings, every cell
    p2_rows = []
    p2_pass = True
    for r, s in cells:
        ob = int(q[s]["Q_obligatory"])
        y = int(fp[s][r])
        ok = (ob == 1 and y == 0) or (ob == 0 and y > 0)
        p2_pass &= ok
        p2_rows.append({"rule": r, "system": s, "Q_obligatory": ob, "healthy_firings": y, "consistent": ok})

    # P3: secondary, disclosed-as-known: Q_support orders SFPU > PFPU > SDAHU
    # Amendment 1: SDAHU's Q is 0 by configuration; P3 reduces to SFPU > PFPU,
    # a consistency check on disclosed values, not a blind prediction.
    p3_pass = (q["sfpu"]["Q_support"] > q["pfpu"]["Q_support"])

    if not p1_pass:
        verdict, fired = "F1_FIRED", ["F1"]
    elif not p3_pass:
        verdict, fired = "P1_PASS_P3_FAIL", ["F3"]
    else:
        verdict, fired = "P1_PASS", []
    if not p2_pass:
        fired.append("F2")

    out = {
        "prereg": "docs/plans/2026-09-23-discovery-predicts-transfer-prereg.md",
        "Q": {s: q[s] for s in SYSTEMS},
        "cells": [{"rule": r, "system": s, "Q_support": float(q[s]["Q_support"]),
                   "healthy_firings": int(fp[s][r]), "scored": s in SCORED}
                  for (r, s) in all_cells],
        "amendment_1": "SDAHU excluded from P1/P2: no heating signal in its configuration; "
                       "P1 scored on six PFPU/SFPU cells; seal holds for MR2/MR3 only",
        "P1": {"rho": rho, "perm_p": p1_p, "n_perm": N_PERM, "seed": SEED, "pass": p1_pass},
        "P2": {"rows": p2_rows, "pass": p2_pass},
        "P3": {"pass": p3_pass, "note": "secondary; MR1 firing order was known to the drafter"},
        "falsifiers_fired": fired,
        "verdict": verdict,
    }
    (ROOT / "outputs" / "discovery_predicts_transfer.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("P1", "verdict", "falsifiers_fired")}, indent=2))
    for row in out["cells"]:
        tag = "" if row["scored"] else "  (reported, not scored — Amendment 1)"
        print(f"  {row['rule']} {row['system']:6s} Q_support={row['Q_support']:.3f}  firings={row['healthy_firings']}{tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
