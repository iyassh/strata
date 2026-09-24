"""X21 — a discovered net's reading of a FOREIGN building's fault-free year:
does Q_AB (support for heating_active when B's log is aligned to A's net)
escape being B's own heating-day count?
Pre-registration: docs/plans/2026-09-24-x21-foreign-net-support-prereg.md

    uv run python scripts/x21_foreign_net_support.py -> outputs/x21_foreign_net_support.json
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from strata.core.pipeline import day_universe, fit  # noqa: E402
from strata.hvac.events import abstract_events, state_only  # noqa: E402
from strata.io.config import load_config  # noqa: E402
from pm4py.objects.log.obj import Event, EventLog, Trace  # noqa: E402
from pm4py.algo.conformance.alignments.petri_net import algorithm as ali  # noqa: E402

BUILDINGS = ("pfpu", "sfpu", "ddahu", "fcu")
SPEC = {"pfpu": ("configs/lbnl_pfpu", "data/processed/pfpu/PFPU_FaultFree.parquet"),
        "sfpu": ("configs/lbnl_sfpu", "data/processed/sfpu/SFPU_FaultFree.parquet"),
        "ddahu": ("configs/lbnl_ddahu", "data/processed/ddahu/DualDuct_FaultFree.parquet"),
        "fcu": ("configs/lbnl_fcu", "data/processed/fcu/FCU_FaultFree.parquet")}
ANCHOR = "heating_active"
TOL = 0.05


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = _ranks(x), _ranks(y); n = len(x); mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5; vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else 0.0


def load(system):
    cfg_dir, hp = SPEC[system]
    cfg = load_config(str(REPO / cfg_dir)); df = pd.read_parquet(REPO / hp)
    det = fit(cfg, df); um = det.unit_model
    slog = state_only(abstract_events(df, cfg)).sort_values(["case_id", "timestamp"])
    uni = day_universe(df, cfg)
    occ = [d for d in uni.index if uni.loc[d, "occupied_min"] > 0]
    day_variant = {d: tuple(g["activity"]) for d, g in slog.groupby("case_id", sort=True)}
    heat_days = set(slog.loc[slog["activity"] == ANCHOR, "case_id"])
    return {"net": (um.net, um.im, um.fm), "n_train_days": um.n_train_days,
            "labels": sorted({t.label for t in um.net.transitions if t.label}),
            "occ": occ, "day_variant": day_variant,
            "raw_days": sum(1 for d in occ if d in heat_days)}


def align(traces, net, im, fm):
    base = pd.Timestamp("2000-01-01"); el = EventLog()
    for t in traces:
        tr = Trace()
        for j, a in enumerate(t):
            tr.append(Event({"concept:name": a, "time:timestamp": base + pd.Timedelta(seconds=j)}))
        el.append(tr)
    dg = ali.apply(el, net, im, fm, variant=ali.Variants.VERSION_STATE_EQUATION_A_STAR)
    assert len(dg) == len(traces)
    for t, d in zip(traces, dg):
        assert tuple(lm for lm, mm in d["alignment"] if lm != ">>") == t
    return dg


def main() -> int:
    B = {s: load(s) for s in BUILDINGS}
    fp = {b: json.loads((REPO / f"outputs/matched_rules_{b}.json").read_text())["healthy_fp"]["mr1"] for b in BUILDINGS}
    pairs = {}
    for a, b in itertools.permutations(BUILDINGS, 2):
        net, im, fm = B[a]["net"]
        variants = sorted(set(B[b]["day_variant"].values()))
        dg = align(variants, net, im, fm)
        sync = {v: any(lm == ANCHOR and mm == ANCHOR for lm, mm in d["alignment"]) for v, d in zip(variants, dg)}
        sync_days = sum(1 for d in B[b]["occ"] if d in B[b]["day_variant"] and sync[B[b]["day_variant"][d]])
        n_occ = len(B[b]["occ"]); raw = B[b]["raw_days"]
        pairs[f"{a}->{b}"] = {"net_from": a, "log_of": b, "variants_aligned": len(variants),
                              "sync_days": sync_days, "raw_days_with_anchor": raw, "occupied_days": n_occ,
                              "Q_AB": sync_days / n_occ, "raw_B": raw / n_occ,
                              "diff": sync_days / n_occ - raw / n_occ,
                              "anchor_in_net": ANCHOR in B[a]["labels"]}
        print(f"{a:5s} net -> {b:5s} log: sync {sync_days:3d} raw {raw:3d} / {n_occ}  Q_AB={sync_days / n_occ:.3f} raw_B={raw / n_occ:.3f}", flush=True)
    p1 = all(p["Q_AB"] <= p["raw_B"] + 1e-12 for p in pairs.values())
    p2_viol = {k: p["diff"] for k, p in pairs.items() if abs(p["diff"]) > TOL}
    p2 = not p2_viol
    q_foreign = {b: sum(p["Q_AB"] for p in pairs.values() if p["log_of"] == b) / 3 for b in BUILDINGS}
    raw_b = {b: B[b]["raw_days"] / len(B[b]["occ"]) for b in BUILDINGS}
    xs = [q_foreign[b] for b in BUILDINGS]; xr = [raw_b[b] for b in BUILDINGS]; ys = [fp[b] for b in BUILDINGS]
    same_order = _ranks(xs) == _ranks(xr)
    rho_f, rho_c = spearman(xs, ys), spearman(xr, ys)
    perms = list(itertools.permutations(ys))
    p_f = sum(1 for pp in perms if spearman(xs, list(pp)) <= rho_f + 1e-12) / len(perms)
    p3 = same_order
    fired = []
    if not p1:
        fired.append("F-X21.b: Q_AB > raw_B on some pair — alignment or alphabet error")
    if not p2:
        fired.append(f"F-X21.a: a foreign net reads a year differently from its count on {len(p2_viol)} pair(s)")
    out = {"prereg": "docs/plans/2026-09-24-x21-foreign-net-support-prereg.md",
           "nets": {s: {"labels": B[s]["labels"], "n_train_days": B[s]["n_train_days"]} for s in BUILDINGS},
           "pairs": pairs,
           "P1_bound": p1, "P2_within_tolerance": {"pass": p2, "tolerance": TOL, "violations": p2_viol,
                                                   "max_abs_diff": max(abs(p["diff"]) for p in pairs.values())},
           "Q_foreign": q_foreign, "raw_B": raw_b, "mr1_healthy_firings": fp,
           "P3_ordering": {"same_ordering_as_raw": same_order, "rho_foreign_vs_mr1": rho_f, "exact_one_sided_p_foreign": p_f,
                           "rho_control_vs_mr1": rho_c},
           "falsifiers_fired": fired}
    (REPO / "outputs/x21_foreign_net_support.json").write_text(json.dumps(out, indent=2) + "\n")
    print("P1", p1, "| P2", p2, "max |diff|", round(out["P2_within_tolerance"]["max_abs_diff"], 4), "| P3 same ordering", same_order,
          f"rho_foreign={rho_f:.3f} p={p_f:.4f} rho_control={rho_c:.3f}")
    print("Q_foreign", {b: round(v, 3) for b, v in q_foreign.items()}, "raw_B", {b: round(v, 3) for b, v in raw_b.items()})
    print("falsifiers:", fired or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
