"""X20 — the transfer test with four scorable buildings, decided by whether the
model-derived predictor is the log's own count.
Pre-registration: docs/plans/2026-09-24-x20-transfer-four-buildings-prereg.md

Inputs
  outputs/discovery_predicts_transfer_q.json        (sdahu, pfpu, sfpu — sealed, unchanged)
  outputs/discovery_predicts_transfer_q_four.json   (ddahu, fcu — same code, --systems)
  outputs/matched_rules_{pfpu,sfpu,ddahu,fcu}.json  (MR1/MR3 healthy-year firings)
  the healthy state logs (raw_heating_frac, computed here from the log alone)

    uv run python scripts/x20_transfer_four.py -> outputs/x20_transfer_four.json
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from strata.core.pipeline import day_universe  # noqa: E402
from strata.hvac.events import abstract_events, state_only  # noqa: E402
from strata.io.config import load_config  # noqa: E402

BUILDINGS = ("pfpu", "sfpu", "ddahu", "fcu")   # the scorable pool: each has a heating coil
HEALTHY = {"pfpu": "data/processed/pfpu/PFPU_FaultFree.parquet",
           "sfpu": "data/processed/sfpu/SFPU_FaultFree.parquet",
           "ddahu": "data/processed/ddahu/DualDuct_FaultFree.parquet",
           "fcu": "data/processed/fcu/FCU_FaultFree.parquet"}
ANCHOR = "heating_active"


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


def raw_heating(system: str) -> dict:
    """From the state log alone: occupied days, days whose log contains the
    anchor, and whether EVERY occupied day contains it."""
    cfg = load_config(str(REPO / f"configs/lbnl_{system}"))
    df = pd.read_parquet(REPO / HEALTHY[system])
    slog = state_only(abstract_events(df, cfg))
    uni = day_universe(df, cfg)
    occ = [d for d in uni.index if uni.loc[d, "occupied_min"] > 0]
    heat_days = set(slog.loc[slog["activity"] == ANCHOR, "case_id"])
    traced = set(slog["case_id"])
    raw = sum(1 for d in occ if d in heat_days)
    n_traced = sum(1 for d in occ if d in traced)
    return {"occupied_days": len(occ), "raw_days_with_anchor": raw,
            "raw_heating_frac": raw / len(occ) if occ else float("nan"),
            "every_occupied_day_has_anchor": raw == len(occ),
            # observation only (not the pre-registered P3 criterion): an occupied day
            # with no state event contributes no trace, so it cannot bear on obligatoriness
            "occupied_days_with_trace": n_traced,
            "every_traced_occupied_day_has_anchor": raw == n_traced}


def main() -> int:
    q = json.loads((REPO / "outputs/discovery_predicts_transfer_q.json").read_text())
    q.update(json.loads((REPO / "outputs/discovery_predicts_transfer_q_four.json").read_text()))
    fp = {b: json.loads((REPO / f"outputs/matched_rules_{b}.json").read_text())["healthy_fp"] for b in BUILDINGS}
    raw = {b: raw_heating(b) for b in BUILDINGS}

    rows = []
    for b in BUILDINGS:
        rows.append({"building": b, "Q_support": float(q[b]["Q_support"]), "sync_days": int(q[b]["sync_days"]),
                     "Q_obligatory": int(q[b]["Q_obligatory"]), **raw[b],
                     "mr1_healthy_firings": int(fp[b]["mr1"]), "mr3_healthy_firings": int(fp[b]["mr3"])})
    # P1 identity: sync_days == raw count (and Q_support == raw frac) on the two new buildings
    p1 = {b: {"sync_days": r["sync_days"], "raw_days_with_anchor": r["raw_days_with_anchor"],
              "identical": r["sync_days"] == r["raw_days_with_anchor"],
              "abs_diff_days": abs(r["sync_days"] - r["raw_days_with_anchor"])}
          for r in rows for b in [r["building"]]}
    p1_new = all(p1[b]["identical"] for b in ("ddahu", "fcu"))
    p1_all = all(p1[b]["identical"] for b in BUILDINGS)
    # P3 obligatory form is a log property
    p3 = {r["building"]: {"Q_obligatory": r["Q_obligatory"], "every_occupied_day_has_anchor": r["every_occupied_day_has_anchor"],
                          "consistent": bool(r["Q_obligatory"]) == r["every_occupied_day_has_anchor"],
                          "every_traced_occupied_day_has_anchor": r["every_traced_occupied_day_has_anchor"],
                          "consistent_with_traced_form": bool(r["Q_obligatory"]) == r["every_traced_occupied_day_has_anchor"]} for r in rows}
    p3_pass = all(v["consistent"] for v in p3.values())
    # P2 the four-building correlation with an exact building-level permutation null
    xs = [r["Q_support"] for r in rows]; ys = [r["mr1_healthy_firings"] for r in rows]
    rho = spearman(xs, ys)
    perms = list(itertools.permutations(ys))
    null = [spearman(xs, list(p)) for p in perms]
    p_one = sum(1 for v in null if v <= rho + 1e-12) / len(perms)
    attainable = min(null); floor_p = sum(1 for v in null if v <= attainable + 1e-12) / len(perms)
    distinct = len(set(ys)) == len(ys)
    p2 = {"rho": rho, "exact_one_sided_p": p_one, "n_perm": len(perms),
          "mr1_counts_distinct": distinct, "attainable_min_rho": attainable, "attainable_floor_p": floor_p,
          "would_pass_criterion": p_one < 0.05}
    # Control (implied by the pre-registration's disclosure): the same test with the
    # log's own heating-day fraction as predictor — no discovery in it at all.
    xr = [r["raw_heating_frac"] for r in rows]
    rho_c = spearman(xr, ys)
    p_c = sum(1 for v in [spearman(xr, list(pp)) for pp in perms] if v <= rho_c + 1e-12) / len(perms)
    control = {"predictor": "raw_heating_frac (occupied days whose log contains heating_active / occupied days)",
               "rho": rho_c, "exact_one_sided_p": p_c, "same_ordering_as_Q_support": _ranks(xr) == _ranks(xs),
               "reading": "if the control orders the buildings identically, the pass of P2 is carried by the count of "
                          "heating days, which MR1 is defined as the workday complement of; discovery adds nothing testable at n = 4"}
    fired = []
    if not p1_new:
        fired.append("F-X20.a: Q_support differs from the log's own count on a new building; the alignment carries information")
    if not p3_pass:
        fired.append("F-X20.b: the obligatory form is not a log property on some building")
    verdict = ("WITHDRAWN_UNINFORMATIVE: the predictor is the log's own heating-day count on every building; "
               "the four-building correlation is reported as a demonstration, not as evidence"
               if p1_new else "INFORMATIVE: score P2 as the pre-registered four-building test")
    out = {"prereg": "docs/plans/2026-09-24-x20-transfer-four-buildings-prereg.md",
           "buildings": rows, "P1_identity": {"per_building": p1, "holds_on_new_buildings": p1_new, "holds_on_all_four": p1_all},
           "P2_four_building_correlation": p2, "P2_control_raw_count": control,
           "P3_obligatory_is_log_property": {"per_building": p3, "pass": p3_pass},
           "falsifiers_fired": fired, "verdict": verdict,
           "conclusion_licensed_about_discovery_predicting_transfer": not p1_new and p2["would_pass_criterion"],
           "note": "MR2 is device-stratum and was voided by the original test's Amendment 3; MR3 is reported, not scored."}
    (REPO / "outputs/x20_transfer_four.json").write_text(json.dumps(out, indent=2) + "\n")
    for r in rows:
        print(f"{r['building']:6s} Q_support={r['Q_support']:.4f} sync={r['sync_days']:3d} raw={r['raw_days_with_anchor']:3d}/{r['occupied_days']:3d} "
              f"traced={r['occupied_days_with_trace']:3d} Q_obl={r['Q_obligatory']} all_days={r['every_occupied_day_has_anchor']} "
              f"all_traced={r['every_traced_occupied_day_has_anchor']} MR1={r['mr1_healthy_firings']:3d} MR3={r['mr3_healthy_firings']}")
    print("P1 identity new buildings:", p1_new, "| all four:", p1_all)
    print(f"P2 rho={rho:.3f} exact one-sided p={p_one:.4f} (floor {floor_p:.4f}, distinct MR1 counts={distinct})")
    print(f"control raw_heating_frac: rho={rho_c:.3f} p={p_c:.4f} same ordering as Q_support={control['same_ordering_as_Q_support']}")
    print("P3:", p3_pass, "| falsifiers:", fired or "none"); print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
