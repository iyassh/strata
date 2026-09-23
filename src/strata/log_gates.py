"""The four log-generic week-0 gates, packaged.

Four of the project's six pre-analysis gates make no reference to HVAC and
apply to any event log: (G1) file integrity and duplicate-file detection by
MD5; (G2) timestamp monotonicity within each case, in recorded order; (G3)
calendar sanity — the span the log covers and timestamps outside a
plausible window; (G4) trace hashing — cases whose (activity, timestamp)
sequence is identical to another case's, i.e. duplicates shipped as
distinct cases, reported separately from ordinary activity-sequence
variants. The two HVAC-specific gates (Brick coverage; raw-CSV calendar
rotation) need a declared point list or calendar and are not here.

Used by `strata gates LOG.xes [...]`, scripts/gates_public_log.py and
scripts/gates_injection.py.
"""
from __future__ import annotations

import hashlib
import time
from collections import Counter
from pathlib import Path

import pandas as pd

GATES = ["G1 md5 integrity + duplicate files", "G2 within-case timestamp monotonicity",
         "G3 calendar sanity", "G4 trace hashing (variants vs true duplicates)"]
NOT_APPLICABLE = ["Brick/TTL semantic coverage", "raw-CSV calendar rotation (needs a declared calendar)"]
C, A, T = "case:concept:name", "concept:name", "time:timestamp"


def gates(path: Path) -> dict:
    """Run G2–G4 on one XES file (G1 is a cross-file check, see run_gates)."""
    import pm4py  # local import: heavy, and the CLI must stay importable without it

    t0 = time.time()
    raw = path.read_bytes()
    log = pm4py.read_xes(str(path))
    df = pm4py.convert_to_dataframe(log) if not isinstance(log, pd.DataFrame) else log
    # recorded order is kept on purpose: G2 asks whether the file is monotonic
    res = {"file": path.name, "md5": hashlib.md5(raw).hexdigest(), "bytes": len(raw),
           "cases": int(df[C].nunique()), "events": int(len(df))}
    viol = []
    for cid, g in df.groupby(C, sort=False):
        ts = g[T].to_numpy()
        if (ts[1:] < ts[:-1]).any():
            viol.append(str(cid))
    res["G2_monotonicity"] = {"cases_with_non_monotonic_timestamps": len(viol), "examples": viol[:5]}
    ts = pd.to_datetime(df[T], utc=True)
    lo, hi = ts.min(), ts.max()
    outside = df[(ts.dt.year < 1990) | (ts.dt.year > 2030)]
    res["G3_calendar"] = {"span": [str(lo), str(hi)], "days": int((hi - lo).days),
                          "events_outside_1990_2030": int(len(outside)),
                          "events_at_exact_midnight": int((ts.dt.hour.eq(0) & ts.dt.minute.eq(0) & ts.dt.second.eq(0)).sum())}
    act_h, full_h = {}, {}
    for cid, g in df.groupby(C, sort=False):
        a = tuple(g[A].astype(str)); f = tuple(zip(a, g[T].astype(str)))
        act_h.setdefault(hashlib.md5(repr(a).encode()).hexdigest(), []).append(str(cid))
        full_h.setdefault(hashlib.md5(repr(f).encode()).hexdigest(), []).append(str(cid))
    dup_full = [v for v in full_h.values() if len(v) > 1]
    res["G4_trace_hash"] = {"distinct_activity_variants": len(act_h),
                            "cases_sharing_an_activity_variant": int(sum(len(v) for v in act_h.values() if len(v) > 1)),
                            "case_groups_with_identical_activity_and_timestamp_sequences": len(dup_full),
                            "cases_in_such_groups": int(sum(len(v) for v in dup_full)),
                            "examples": dup_full[:3]}
    res["runtime_seconds_stdout_only"] = round(time.time() - t0, 1)
    return res


def run_gates(paths: list[Path]) -> tuple[dict, list[dict]]:
    """All four gates over a set of logs. Returns (artefact, per-log results
    incl. the machine-dependent runtime that the artefact deliberately omits)."""
    results = [gates(p) for p in paths]
    md5s = Counter(r["md5"] for r in results)
    out = {"gates": GATES, "not_applicable": NOT_APPLICABLE,
           "G1_duplicate_files": [m for m, c in md5s.items() if c > 1],
           "logs": [{k: v for k, v in r.items() if k != "runtime_seconds_stdout_only"} for r in results]}
    return out, results


def summary_line(r: dict) -> str:
    return (f"{r['file']}: {r['cases']} cases, {r['events']} events, {r['runtime_seconds_stdout_only']}s | "
            f"non-monotonic cases {r['G2_monotonicity']['cases_with_non_monotonic_timestamps']} | "
            f"span {r['G3_calendar']['days']} d | variants {r['G4_trace_hash']['distinct_activity_variants']} | "
            f"true-duplicate groups {r['G4_trace_hash']['case_groups_with_identical_activity_and_timestamp_sequences']}")
