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
from strata.core.devices import device_log, device_templates  # noqa: E402
from pm4py.objects.log.obj import EventLog, Trace, Event  # noqa: E402
from pm4py.algo.conformance.alignments.petri_net import algorithm as ali  # noqa: E402

ROOT = str(REPO) + "/"
ANCHOR = "heating_active"
SPEC = {"sdahu": ("configs/lbnl_sdahu", "data/processed/sdahu/AHU_annual.parquet"),
        "pfpu": ("configs/lbnl_pfpu", "data/processed/pfpu/PFPU_FaultFree.parquet"),
        "sfpu": ("configs/lbnl_sfpu", "data/processed/sfpu/SFPU_FaultFree.parquet"),
        # X20 (2026-09-24): the two buildings onboarded after the test was sealed
        "ddahu": ("configs/lbnl_ddahu", "data/processed/ddahu/DualDuct_FaultFree.parquet"),
        "fcu": ("configs/lbnl_fcu", "data/processed/fcu/FCU_FaultFree.parquet")}
# --systems a,b restricts the run (default: the three original systems, so the
# committed artefact regenerates unchanged)
_DEFAULT_SYSTEMS = ("sdahu", "pfpu", "sfpu")
SYSTEMS = tuple(sys.argv[sys.argv.index("--systems") + 1].split(",")) if "--systems" in sys.argv else _DEFAULT_SYSTEMS


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


def compute_device(SYS: str) -> dict:
    """Device-stratum Q (Amendment 1, addition 1): one pooled device net per
    system; anchor is the pooled activity (no @device suffix)."""
    if SYS == "sdahu":
        return {"device_model": None}
    CFG, HEA = SPEC[SYS]
    t0 = time.time()
    cfg = load_config(ROOT + CFG)
    df = pd.read_parquet(ROOT + HEA)

    det = fit(cfg, df)
    dm = det.device_model
    if dm is None:
        return {"device_model": None}
    net, im, fm, ndev_train = dm.net, dm.im, dm.fm, dm.n_train_cases
    print(f"[{SYS}] device net {len(net.places)}p/{len(net.transitions)}t "
          f"({sum(1 for t in net.transitions if t.label is None)} silent); "
          f"labels={sorted({t.label for t in net.transitions if t.label})}", flush=True)

    tpl = device_templates(cfg)
    heat_tpl = sorted({v[0] for k, v in tpl.items() if "heating" in k and k.endswith("_active")})
    print(f"[{SYS}] device templates for zone heating 'on' events: {heat_tpl}", flush=True)
    ANCHOR = heat_tpl[0] if heat_tpl else None

    log = abstract_events(df, cfg)
    dlog = device_log(log, cfg).sort_values(["case_id", "timestamp"])
    uni = day_universe(df, cfg)
    occ_days = [d for d in uni.index if uni.loc[d, "occupied_min"] > 0]
    devices = sorted(dlog["device"].unique())

    case_var = {c: tuple(g["activity"]) for c, g in dlog.groupby("case_id", sort=True)}
    variants = sorted(set(case_var.values()))
    print(f"[{SYS}] {len(devices)} devices {devices}, {len(case_var)} day-device cases, "
          f"{len(variants)} device variants, {len(occ_days)} occupied days", flush=True)

    def align(traces):
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

    vd = align(variants)
    vi = {v: i for i, v in enumerate(variants)}
    sync = {v: any(lm == ANCHOR and mm == ANCHOR for lm, mm in vd[vi[v]]["alignment"])
            for v in variants}
    cost0_orig = {v: float(vd[vi[v]]["fitness"]) >= 1 - 1e-12 for v in variants}

    per_dev = {}
    for dev in devices:
        n_sync = n_raw = n_present = 0
        for d in occ_days:
            v = case_var.get(f"{d}__{dev}")
            if v is None:
                continue
            n_present += 1
            if ANCHOR in v:
                n_raw += 1
            if sync[v]:
                n_sync += 1
        per_dev[dev] = {"sync_days": n_sync, "occupied_days": len(occ_days),
                        "days_with_trace": n_present,
                        "raw_log_days_with_anchor": n_raw,
                        "frac": n_sync / len(occ_days)}
        print(f"[{SYS}] {dev}: sync {n_sync}/{len(occ_days)} raw {n_raw} "
              f"traces {n_present}", flush=True)

    q_sup_dev = sum(v["frac"] for v in per_dev.values()) / len(per_dev)

    # Q_obligatory_device: pooled over all device variants, and per device
    short = [tuple(a for a in v if a != ANCHOR) for v in variants]
    sd = align(short)
    short_c0 = {variants[i]: float(sd[i]["fitness"]) >= 1 - 1e-12 for i in range(len(variants))}
    pooled_c0 = sum(short_c0.values())
    q_obl_dev_pooled = 0 if pooled_c0 > 0 else 1

    per_dev_obl = {}
    for dev in devices:
        dvars = sorted({case_var[c] for c in case_var if c.endswith("__" + dev)})
        c0 = sum(1 for v in dvars if short_c0[v])
        base_c0 = sum(1 for v in dvars if cost0_orig[v])
        per_dev_obl[dev] = {"variants": len(dvars), "cost0_without_anchor": c0,
                            "baseline_cost0_unmodified": base_c0,
                            "Q_obligatory_device": 0 if c0 > 0 else 1}
        print(f"[{SYS}] {dev}: variants={len(dvars)} cost0_noanchor={c0} "
              f"baseline_cost0={base_c0}", flush=True)

    res = {
      "anchor_activity_in_device_net": ANCHOR,
      "device_net_is_pooled_across_devices": True,
      "devices": devices,
      "Q_support_device": q_sup_dev,
      "Q_obligatory_device": q_obl_dev_pooled,
      "per_device": per_dev,
      "per_device_obligatory": per_dev_obl,
      "device_variants_tested": len(variants),
      "device_variants_cost0_without_anchor": pooled_c0,
      "baseline_device_variants_cost0_unmodified": sum(cost0_orig.values()),
      "device_net": {"places": len(net.places), "transitions": len(net.transitions),
                     "silent": sum(1 for t in net.transitions if t.label is None),
                     "labels": sorted({t.label for t in net.transitions if t.label})},
      "n_train_cases": ndev_train,
    }

    return res


def main() -> int:
    out_path = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv \
        else REPO / "outputs" / "discovery_predicts_transfer_q.json"
    result = {s: compute(s) for s in SYSTEMS}
    for s in SYSTEMS:
        result[s]["device"] = compute_device(s)
    # Gated artifact: never write wall-clock or host-specific values into it,
    # or the L2 regression gate reports CHANGED on every run (repo audit
    # 2026-09-23). Timings go to stdout only.
    VOLATILE = ("fit_seconds", "seconds", "elapsed", "timestamp", "hostname")
    def _strip(o):
        if isinstance(o, dict):
            return {k: _strip(v) for k, v in o.items() if not any(w in k.lower() for w in VOLATILE)}
        if isinstance(o, list):
            return [_strip(v) for v in o]
        return o
    result = _strip(result)
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
