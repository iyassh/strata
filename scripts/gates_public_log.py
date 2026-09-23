"""The generalisable week-0 gates, run on public process-mining event logs.

Four of the project's six pre-analysis gates make no reference to HVAC and
apply to any event log: (1) file integrity and duplicate-file detection by
MD5; (2) timestamp monotonicity within each case; (3) calendar sanity —
the span the log covers and timestamps outside a plausible window;
(4) trace hashing — cases whose (activity, timestamp) sequence is identical
to another case's, i.e. duplicates shipped as distinct cases, reported
separately from ordinary activity-sequence variants. The two HVAC-specific
gates (Brick coverage; raw-CSV calendar rotation) do not apply.

    uv run python scripts/gates_public_log.py LOG.xes [LOG2.xes ...]
    -> outputs/gates_public_log.json
"""
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import pm4py

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "gates_public_log.json"


def gates(path: Path) -> dict:
    t0 = time.time()
    raw = path.read_bytes()
    log = pm4py.read_xes(str(path))
    df = pm4py.convert_to_dataframe(log) if not isinstance(log, pd.DataFrame) else log
    C, A, T = "case:concept:name", "concept:name", "time:timestamp"
    df = df.sort_values([C, T], kind="stable") if False else df  # keep LOG order for monotonicity
    res = {"file": path.name, "md5": hashlib.md5(raw).hexdigest(), "bytes": len(raw),
           "cases": int(df[C].nunique()), "events": int(len(df))}
    # G2 monotonicity within case, in recorded order
    viol = []
    for cid, g in df.groupby(C, sort=False):
        ts = g[T].to_numpy()
        if (ts[1:] < ts[:-1]).any():
            viol.append(str(cid))
    res["G2_monotonicity"] = {"cases_with_non_monotonic_timestamps": len(viol), "examples": viol[:5]}
    # G3 calendar sanity
    ts = pd.to_datetime(df[T], utc=True)
    lo, hi = ts.min(), ts.max()
    outside = df[(ts.dt.year < 1990) | (ts.dt.year > 2030)]
    res["G3_calendar"] = {"span": [str(lo), str(hi)], "days": int((hi - lo).days),
                          "events_outside_1990_2030": int(len(outside)),
                          "events_at_exact_midnight": int((ts.dt.hour.eq(0) & ts.dt.minute.eq(0) & ts.dt.second.eq(0)).sum())}
    # G4 trace hashing: activity-only (variants; normal) vs activity+timestamp (true duplicates)
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


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    results = [gates(p) for p in paths]
    # G1 across files: duplicate files by MD5
    md5s = Counter(r["md5"] for r in results)
    out = {"gates": ["G1 md5 integrity + duplicate files", "G2 within-case timestamp monotonicity",
                     "G3 calendar sanity", "G4 trace hashing (variants vs true duplicates)"],
           "not_applicable": ["Brick/TTL semantic coverage", "raw-CSV calendar rotation (needs a declared calendar)"],
           "G1_duplicate_files": [m for m, c in md5s.items() if c > 1],
           "logs": [{k: v for k, v in r.items() if k != "runtime_seconds_stdout_only"} for r in results]}
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    for r in results:
        print(f"{r['file']}: {r['cases']} cases, {r['events']} events, {r['runtime_seconds_stdout_only']}s | "
              f"non-monotonic cases {r['G2_monotonicity']['cases_with_non_monotonic_timestamps']} | "
              f"span {r['G3_calendar']['days']} d | variants {r['G4_trace_hash']['distinct_activity_variants']} | "
              f"true-duplicate groups {r['G4_trace_hash']['case_groups_with_identical_activity_and_timestamp_sequences']}")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
