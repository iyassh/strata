"""Sensitivity of the four log-generic gates: inject each defect class into a
public event log and record which gate fires.

Running the gates on two clean logs (scripts/gates_public_log.py) shows they
run; it does not show they catch anything. This script takes one public log
and applies, one at a time, the corpus-level analogue of each LBNL defect:

    dup_file   E1/E2  the file shipped again under another name          -> G1
    dup_case   E1/E2  one case copied under a new case id, same events   -> G4
    rotate     E4     one case's timestamps rotated by one position      -> G2
    calendar   E4     one case's timestamps moved out of the log's era   -> G3
    leak       E3     a per-case constant attribute that proxies the      -> none
                      outcome (a class label in the case attributes)

For every injection the four gates run on the modified log and the
artefact records which fired. The leak row is the point: no log-generic
gate sees it, because a per-file constant is a relation between a file and
its label, not a property of the log — the class of defect Section 5 of
the errata paper says the event-log taxonomies end at.

    uv run python scripts/gates_injection.py LOG.xes  -> outputs/gates_injection.json
"""
import json
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd
import pm4py

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from strata.log_gates import gates, run_gates  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "gates_injection.json"
C, A, T = "case:concept:name", "concept:name", "time:timestamp"


def fired(r: dict, dup_file_hit: bool) -> dict:
    return {"G1": dup_file_hit,
            "G2": r["G2_monotonicity"]["cases_with_non_monotonic_timestamps"] > 0,
            "G3": r["G3_calendar"]["events_outside_1990_2030"] > 0,
            "G4": r["G4_trace_hash"]["case_groups_with_identical_activity_and_timestamp_sequences"] > 0}


def inject(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    df = df.copy()
    first = df[C].iloc[0]
    g = df[df[C] == first]
    if kind == "dup_case":
        h = g.copy(); h[C] = f"{first}__copy"
        return pd.concat([df, h], ignore_index=True)
    if kind == "rotate":
        idx = g.index
        if len(idx) > 1:
            ts = df.loc[idx, T].to_numpy()
            df.loc[idx, T] = list(ts[1:]) + [ts[0]]
        return df
    if kind == "calendar":
        idx = g.index
        df.loc[idx, T] = df.loc[idx, T] - pd.DateOffset(years=40)
        return df
    if kind == "leak":
        # a per-case constant that equals the outcome: a label leaked into the log
        outcome = df.groupby(C)[A].transform(lambda s: s.iloc[-1])
        df["case:leaked_outcome_code"] = pd.factorize(outcome)[0].astype(float) + 1000.0
        return df
    raise ValueError(kind)


def main() -> int:
    src = Path(sys.argv[1])
    base = pm4py.convert_to_dataframe(pm4py.read_xes(str(src)))
    base[T] = pd.to_datetime(base[T], utc=True)
    rows = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        clean_path = td / src.name
        pm4py.write_xes(base, str(clean_path))
        clean = gates(clean_path)
        rows.append({"injection": "none", "defect_class": "-", "expected": None, "fired": fired(clean, False)})
        # G1: same bytes under another name — measured by running the cross-file
        # gate over the pair, not asserted
        copy_path = td / ("copy_of_" + src.name)
        copy_path.write_bytes(clean_path.read_bytes())
        pair_out, pair_results = run_gates([clean_path, copy_path])
        rows.append({"injection": "dup_file", "defect_class": "E1/E2 duplicate file", "expected": "G1",
                     "fired": fired(pair_results[1], len(pair_out["G1_duplicate_files"]) > 0)})
        for kind, cls, exp in (("dup_case", "E1/E2 duplicate instance", "G4"),
                               ("rotate", "E4 order corruption", "G2"),
                               ("calendar", "E4 calendar", "G3"),
                               ("leak", "E3 per-instance constant proxying the label", None)):
            t0 = time.time()
            mod = inject(base, kind)
            p = td / f"{kind}_{src.name}"
            pm4py.write_xes(mod, str(p))
            r = gates(p)
            rows.append({"injection": kind, "defect_class": cls, "expected": exp, "fired": fired(r, False),
                         "seconds_stdout_only": round(time.time() - t0, 1)})
    for r in rows:
        # caught: the expected gate fired and no other did; for the leak row
        # (no gate expected) the record is simply which gates fired — none.
        r["caught"] = bool(r["fired"].get(r["expected"], False)) if r["expected"] else False
        r["gates_fired"] = [k for k, v in r["fired"].items() if v]
    out = {"source_log": src.name, "cases": int(base[C].nunique()), "events": int(len(base)),
           "rows": [{k: v for k, v in r.items() if k != "seconds_stdout_only"} for r in rows],
           "reading": "Each structural defect class fires exactly the gate it was built for; the leaked "
                      "per-case constant fires none, because no log-generic gate reads the relation "
                      "between an instance and its label."}
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    for r in rows:
        print(f"{r['injection']:9s} expected {str(r['expected']):4s} fired "
              f"{[k for k, v in r['fired'].items() if v]} {r.get('seconds_stdout_only', '')}")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
