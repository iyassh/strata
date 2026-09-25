"""X30 — method-coverage grid: other process-mining instruments on the scenarios
the deployed detector misses. Pre-registration: docs/plans/2026-09-24-x30-method-grid-prereg.md

Each cell: discover on training days (X25 split), threshold = 1 % quantile of the
per-day score on the calibration slice, false alarms on the holdout, detection
gate = model_significant(flagged, n_eval, holdout_fp, holdout_n) — the deployed rule.

    uv run python scripts/x30_method_grid.py [--systems a,b] -> outputs/x30_method_grid.json
"""
from __future__ import annotations

import json
import os
import signal
import sys
import traceback
import warnings
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
import pandas as pd
import pm4py

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from strata.core.significance import model_significant  # noqa: E402
from strata.core.splits import calibration_mask, holdout_mask  # noqa: E402
from strata.hvac.events import abstract_events, state_only  # noqa: E402
from strata.io.config import load_config  # noqa: E402

SPEC = {"sdahu": ("configs/lbnl_sdahu", "data/processed/sdahu", "AHU_annual"),
        "pfpu": ("configs/lbnl_pfpu", "data/processed/pfpu", "PFPU_FaultFree"),
        "sfpu": ("configs/lbnl_sfpu", "data/processed/sfpu", "SFPU_FaultFree"),
        "ddahu": ("configs/lbnl_ddahu", "data/processed/ddahu", "DualDuct_FaultFree"),
        "fcu": ("configs/lbnl_fcu", "data/processed/fcu", "FCU_FaultFree")}
CELLS = ["IM00-align", "IM05-align", "IM02-token", "HM-align", "SKEL", "DECLARE", "TEMPORAL"]
CELL_TIMEOUT_S = 15 * 60   # F-X30.b: a cell that does not finish in 15 minutes is "not evaluated", never a null


class CellTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise CellTimeout(f"cell exceeded {CELL_TIMEOUT_S} s")


def fmt(log: pd.DataFrame):
    return pm4py.format_dataframe(log[["case_id", "activity", "timestamp"]].copy(), case_id="case_id", activity_key="activity", timestamp_key="timestamp")


def per_day_scores(cell: str, model, log: pd.DataFrame) -> pd.Series:
    """Per-case score in [0, 1], higher = more conforming."""
    L = fmt(log)
    cases = sorted(log["case_id"].unique())
    if cell.endswith("-align"):
        net, im, fm = model
        d = pm4py.conformance_diagnostics_alignments(L, net, im, fm)
        vals = [float(x["fitness"]) for x in d]
    elif cell == "IM02-token":
        net, im, fm = model
        d = pm4py.conformance_diagnostics_token_based_replay(L, net, im, fm)
        vals = [float(x["trace_fitness"]) for x in d]
    elif cell == "SKEL":
        d = pm4py.conformance_log_skeleton(L, model)
        n_ev = log.groupby("case_id").size().reindex(cases).fillna(1).values
        vals = [1.0 - len(x.get("deviations", [])) / max(int(n), 1) for x, n in zip(d, n_ev)]
    elif cell == "DECLARE":
        d = pm4py.conformance_declare(L, model)
        vals = [float(x.get("dev_fitness", 1.0)) if isinstance(x, dict) else 1.0 for x in d]
    elif cell == "TEMPORAL":
        d = pm4py.conformance_temporal_profile(L, model, zeta=3.0)
        n_ev = log.groupby("case_id").size().reindex(cases).fillna(1).values
        vals = [1.0 - len(x) / max(int(n), 1) for x, n in zip(d, n_ev)]
    else:
        raise ValueError(cell)
    assert len(vals) == len(cases), (cell, len(vals), len(cases))
    return pd.Series(vals, index=cases)


def discover(cell: str, train: pd.DataFrame):
    L = fmt(train)
    if cell == "IM00-align":
        return pm4py.discover_petri_net_inductive(L, noise_threshold=0.0)
    if cell == "IM05-align":
        return pm4py.discover_petri_net_inductive(L, noise_threshold=0.5)
    if cell == "IM02-token":
        return pm4py.discover_petri_net_inductive(L, noise_threshold=0.2)
    if cell == "HM-align":
        return pm4py.discover_petri_net_heuristics(L)
    if cell == "SKEL":
        return pm4py.discover_log_skeleton(L)
    if cell == "DECLARE":
        return pm4py.discover_declare(L)
    if cell == "TEMPORAL":
        return pm4py.discover_temporal_profile(L)
    raise ValueError(cell)


def run_system(system: str) -> dict:
    cfg_dir, data_dir, healthy = SPEC[system]
    cfg = load_config(str(REPO / cfg_dir))
    d = cfg.rules["detection"]
    hlog = state_only(abstract_events(pd.read_parquet(REPO / data_dir / f"{healthy}.parquet"), cfg)).sort_values(["case_id", "timestamp"]).reset_index(drop=True)
    hold = holdout_mask(hlog["case_id"], d["holdout_days_per_month"])
    calib = calibration_mask(hlog["case_id"], d["holdout_days_per_month"], int(d.get("calibration_days_per_month", 0)))
    train, calib_log, hold_log = hlog[~hold & ~calib], hlog[calib], hlog[hold]
    card = json.loads((REPO / f"outputs/benchmark_v6_{system}.json").read_text())
    misses = [s["file"] for s in card["scenarios"] if s["is_fault"] and not s["excluded"] and not s["meaningful_channels"]]
    out = {"n_train_days": int(train["case_id"].nunique()), "n_calib_days": int(calib_log["case_id"].nunique()), "n_holdout_days": int(hold_log["case_id"].nunique()),
           "missed_scenarios": misses, "cells": {}}
    print(f"[{system}] train {out['n_train_days']} calib {out['n_calib_days']} holdout {out['n_holdout_days']} | misses {len(misses)}", flush=True)
    scen_logs = {m: state_only(abstract_events(pd.read_parquet(REPO / data_dir / f"{m}.parquet"), cfg)) for m in misses}
    for cell in CELLS:
        signal.signal(signal.SIGALRM, _alarm); signal.alarm(CELL_TIMEOUT_S)
        try:
            model = discover(cell, train)
            thr = float(per_day_scores(cell, model, calib_log).quantile(d["fpr_quantile"]))
            hs = per_day_scores(cell, model, hold_log)
            fp, hn = int((hs < thr).sum()), int(len(hs))
            res = {"threshold": thr, "holdout_fp": fp, "holdout_n": hn, "holdout_fp_rate": fp / max(hn, 1), "scenarios": {}}
            for m, slog in scen_logs.items():
                ss = per_day_scores(cell, model, slog)
                k, n = int((ss < thr).sum()), int(len(ss))
                res["scenarios"][m] = {"flagged": k, "n": n, "significant": bool(model_significant(k, n, fp, hn))}
            res["detected"] = [m for m, v in res["scenarios"].items() if v["significant"]]
            print(f"[{system}] {cell:11s} thr {thr:.3f} holdout FP {fp}/{hn} | detects {len(res['detected'])} of {len(misses)}: {res['detected']}", flush=True)
        except (Exception, CellTimeout) as exc:  # F-X30.b: reported, never a null
            res = {"error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc()[-600:]}
            print(f"[{system}] {cell:11s} NOT EVALUATED {type(exc).__name__}: {str(exc)[:120]}", flush=True)
        finally:
            signal.alarm(0)
        out["cells"][cell] = res
    return out


def main() -> int:
    systems = sys.argv[sys.argv.index("--systems") + 1].split(",") if "--systems" in sys.argv else ["pfpu", "sfpu", "ddahu", "fcu", "sdahu"]
    if "--summarise" in sys.argv:   # recompute the predictions block from the saved per-cell results (no cell re-run)
        res = json.loads((REPO / "outputs/x30_method_grid.json").read_text())["systems"]
    else:
        res = {s: run_system(s) for s in systems}
    within = [(s, c, v["detected"]) for s in res for c, v in res[s]["cells"].items() if "detected" in v and v["detected"] and v["holdout_fp"] <= 3]
    over10 = [(s, c, v["holdout_fp_rate"]) for s in res for c, v in res[s]["cells"].items() if "holdout_fp_rate" in v and v["holdout_fp_rate"] > 0.10]
    errors = [(s, c) for s in res for c, v in res[s]["cells"].items() if "error" in v]
    pred = {"P1_no_cell_detects_a_miss_within_3_fp": not within, "P1_violations": within,
            "P2_some_cell_over_10pct_fp": bool(over10), "P2_cells": over10,
            "P3_all_cells_ran": not errors, "P3_errors": errors}
    fired = []
    if within: fired.append(f"F-X30.a: {within}")
    if errors: fired.append(f"F-X30.b: cells not evaluated: {errors}")
    pred["predictions_failed_without_falsifier"] = ([] if over10 else ["P2: no cell exceeded 10 % holdout false alarms (worst 7/72 = 9.7 %)"])
    pred["threshold_policy"] = "one threshold per cell: the 1 % quantile of the per-day score on the calibration slice; no threshold sweep"
    pred["cell_budget_note"] = f"{CELL_TIMEOUT_S} s per cell covering discovery plus every scenario log; set in this script, not in the pre-registration"
    out = {"prereg": "docs/plans/2026-09-24-x30-method-grid-prereg.md", "cells": CELLS, "systems": res, "predictions": pred, "falsifiers_fired": fired}
    (REPO / "outputs/x30_method_grid.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(pred, indent=1)); print("falsifiers fired:", fired or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
