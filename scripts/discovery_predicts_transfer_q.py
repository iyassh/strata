"""Regenerate the sealed Q values for the discovery-predicts-transfer test.

Adopted verbatim (paths made repo-relative, scratch cache removed) from the
computation the sealed agent ran on 2026-09-23 without access to the rule-
firing artifacts. Definitions: docs/plans/2026-09-23-discovery-predicts-transfer-prereg.md.
Writes outputs/discovery_predicts_transfer_q.json (or --out PATH).

    caffeinate -i uv run python scripts/discovery_predicts_transfer_q.py
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from strata.io.config import load_config          # noqa: E402
from strata.core.pipeline import fit, day_universe  # noqa: E402
from strata.hvac.events import abstract_events, state_only  # noqa: E402

ROOT = str(REPO) + "/"
ANCHOR = "heating_active"
SPEC = {"sdahu": ("configs/lbnl_sdahu", "data/processed/sdahu/AHU_annual.parquet"),
        "pfpu": ("configs/lbnl_pfpu", "data/processed/pfpu/PFPU_FaultFree.parquet"),
        "sfpu": ("configs/lbnl_sfpu", "data/processed/sfpu/SFPU_FaultFree.parquet")}


def compute(SYS: str) -> dict:
    CFG_DIR, HEALTHY = SPEC[SYS]
    t0 = time.time()
    cfg = load_config(ROOT + CFG_DIR)
    df = pd.read_parquet(ROOT + HEALTHY)
    print(f"[{SYS}] loaded {df.shape}", flush=True)

    det = fit(cfg, df)
    print(f"[{SYS}] fit done in {time.time()-t0:.0f}s", flush=True)
    unit = det.unit_model
    assert unit is not None, "pm4py missing -> no unit model"
    net, im, fm, n_train_days = unit.net, unit.im, unit.fm, unit.n_train_days

    silent = sum(1 for t in net.transitions if t.label is None)
    net_stats = {"places": len(net.places), "transitions": len(net.transitions),
                 "silent": silent,
                 "labels": sorted({t.label for t in net.transitions if t.label})}
    print(f"[{SYS}] net {net_stats['places']}p/{net_stats['transitions']}t "
          f"({silent} silent); labels={net_stats['labels']}", flush=True)

    # ---- healthy unit-stratum state log + occupied days ----------------------
    log = abstract_events(df, cfg)
    slog = state_only(log).sort_values(["case_id", "timestamp"]).reset_index(drop=True)
    uni = day_universe(df, cfg)
    occupied_days = [d for d in uni.index if uni.loc[d, "occupied_min"] > 0]
    occ_set = set(occupied_days)

    heating_in_log = bool((slog["activity"] == ANCHOR).any())
    zone_heating_in_net = sorted(l for l in net_stats["labels"] if "zone_heating" in l)

    day_variant = {d: tuple(g["activity"]) for d, g in slog.groupby("case_id", sort=True)}
    variants = sorted(set(day_variant.values()))
    print(f"[{SYS}] {len(day_variant)} days with state events, "
          f"{len(variants)} variants, {len(occupied_days)} occupied days, "
          f"heating_in_log={heating_in_log}", flush=True)

    # ---- alignment helper -----------------------------------------------------
    import pm4py

    from pm4py.objects.log.obj import EventLog, Trace, Event
    from pm4py.algo.conformance.alignments.petri_net import algorithm as ali_algo

    ALIGN_VARIANT = ali_algo.Variants.VERSION_STATE_EQUATION_A_STAR

    def align_traces(traces):
        """traces: list of tuples of activity names -> list of pm4py alignment
        diagnostics, IN THE SAME ORDER (low-level API preserves log order, so no
        case-id sorting assumption; empty traces are supported natively)."""
        base = pd.Timestamp("2000-01-01")
        elog = EventLog()
        for t in traces:
            tr = Trace()
            for j, a in enumerate(t):
                tr.append(Event({"concept:name": a,
                                 "time:timestamp": base + pd.Timedelta(seconds=j)}))
            elog.append(tr)
        diags = ali_algo.apply(elog, net, im, fm, variant=ALIGN_VARIANT)
        assert len(diags) == len(traces), (len(diags), len(traces))
        for t, dg in zip(traces, diags):
            proj = tuple(lm for lm, mm in dg["alignment"] if lm != ">>")
            assert proj == t, (proj, t)     # order/identity sanity check
        return diags

    # ---- Q_support ------------------------------------------------------------
    var_diags = align_traces(variants)
    var_index = {v: i for i, v in enumerate(variants)}

    def has_sync_heating(dg):
        return any(lm == ANCHOR and mm == ANCHOR for lm, mm in dg["alignment"])

    var_sync = {v: has_sync_heating(var_diags[var_index[v]]) for v in variants}

    sync_days = 0
    occ_no_events = 0
    for d in occupied_days:
        v = day_variant.get(d)
        if v is None:
            occ_no_events += 1
            continue
        if var_sync[v]:
            sync_days += 1

    q_support = sync_days / len(occupied_days) if occupied_days else 0.0
    print(f"[{SYS}] Q_support = {sync_days}/{len(occupied_days)} = {q_support:.6f} "
          f"(occupied days with no state events: {occ_no_events})", flush=True)

    # ---- Q_obligatory ---------------------------------------------------------
    shortened = [tuple(a for a in v if a != ANCHOR) for v in variants]
    short_diags = align_traces(shortened)
    cost0 = 0
    cost0_examples = []
    empty_short = 0
    for i, dg in enumerate(short_diags):
        if len(shortened[i]) == 0:
            empty_short += 1
        if float(dg["fitness"]) >= 1.0 - 1e-12:
            cost0 += 1
            if len(cost0_examples) < 3:
                cost0_examples.append(list(shortened[i])[:20])

    q_obligatory = 0 if (cost0 > 0 or not heating_in_log) else 1
    print(f"[{SYS}] variants_tested={len(variants)} cost0_without_heating={cost0} "
          f"(empty shortened traces skipped: {empty_short}) -> "
          f"Q_obligatory={q_obligatory}", flush=True)

    res = {
        "Q_support": q_support,
        "sync_days": sync_days,
        "occupied_days": len(occupied_days),
        "Q_obligatory": q_obligatory,
        "variants_tested": len(variants),
        "variants_cost0_without_heating": cost0,
        "heating_in_log": heating_in_log,
        "zone_heating_activities": zone_heating_in_net,
        "net": {"places": net_stats["places"], "transitions": net_stats["transitions"],
                "silent": net_stats["silent"]},
        "_aux": {
            "net_labels": net_stats["labels"],
            "heating_in_net": ANCHOR in net_stats["labels"],
            "n_days_with_state_events": len(day_variant),
            "occupied_days_with_no_state_events": occ_no_events,
            "variants_with_empty_shortened_trace": empty_short,
            "variants_containing_heating": sum(1 for v in variants if ANCHOR in v),
            "occupied_days_whose_log_contains_heating":
                sum(1 for d in occupied_days if ANCHOR in day_variant.get(d, ())),
            "cost0_shortened_examples": cost0_examples,
            "n_train_days": n_train_days,
            "fit_seconds": round(time.time() - t0, 1),
        },
    }

    return res


def main() -> int:
    out_path = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv \
        else REPO / "outputs" / "discovery_predicts_transfer_q.json"
    result = {s: compute(s) for s in SPEC}
    result["_method"] = ("Unit-stratum net from fit().unit_model (inductive miner, noise 0.2, state "
                         "alphabet, train days only); pm4py alignments VERSION_STATE_EQUATION_A_STAR via "
                         "the low-level API in log order, one alignment per distinct variant mapped back "
                         "to days; Q_support = occupied days whose alignment has a sync move on "
                         "heating_active; Q_obligatory = 1 iff no variant with heating_active deleted "
                         "aligns at cost 0. Adopted from the sealed computation of 2026-09-23.")
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
