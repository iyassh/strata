"""Conformance checking: replay an event log against a Petri net and score the fit.

One alignment pass per log (the audit found fitness and diagnostics were each
re-aligning the whole log). Both directions of deviation are counted:

- ``unexpected`` — log-only moves: events that happened but the model did not
  expect (e.g. a mismatch event absent from healthy behaviour).
- ``missing`` — model-only moves on labelled transitions: behaviour the model
  expected that never happened (e.g. cooling never activating). The audit
  showed dropping these made suppression faults report "no deviations" under a
  failing fitness.

Fitness is reported per trace (one trace = one day), which is what the
temporal-split benchmark evaluates on.
"""

from __future__ import annotations

import pandas as pd
import pm4py

SKIP = ">>"


def check_conformance(event_log: pd.DataFrame, net, im, fm) -> dict:
    """Align a log against a Petri net; return per-day fitness and deviations."""
    log = pm4py.format_dataframe(
        event_log,
        case_id="case_id",
        activity_key="activity",
        timestamp_key="timestamp",
    )
    diagnostics = pm4py.conformance_diagnostics_alignments(log, net, im, fm)

    case_ids = sorted(event_log["case_id"].unique())
    if len(case_ids) != len(diagnostics):  # defensive: mapping must be 1:1
        raise RuntimeError(
            f"alignment count {len(diagnostics)} != case count {len(case_ids)}"
        )

    unexpected: dict[str, int] = {}
    missing: dict[str, int] = {}
    rows = []
    for case_id, diag in zip(case_ids, diagnostics):
        n_unexpected = n_missing = 0
        for log_move, model_move in diag["alignment"]:
            if model_move == SKIP and log_move != SKIP:  # log-only move
                unexpected[log_move] = unexpected.get(log_move, 0) + 1
                n_unexpected += 1
            elif log_move == SKIP and model_move not in (SKIP, None):  # model-only
                missing[model_move] = missing.get(model_move, 0) + 1
                n_missing += 1
        rows.append((case_id, diag["fitness"], n_unexpected, n_missing))

    per_day = pd.DataFrame(rows, columns=["case_id", "fitness", "n_unexpected", "n_missing"])
    return {
        "average_trace_fitness": float(per_day["fitness"].mean()),
        "percentage_fitting_traces": float((per_day["fitness"] == 1.0).mean() * 100),
        "per_day": per_day,
        "unexpected_by_activity": dict(sorted(unexpected.items(), key=lambda kv: -kv[1])),
        "missing_by_activity": dict(sorted(missing.items(), key=lambda kv: -kv[1])),
    }
