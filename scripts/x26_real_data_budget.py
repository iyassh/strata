"""X26 ledger — the false-alarm budget on a real building (LBNL field RTU, Site 2).
Reads run 1 (circuit-1 residuals only, *_run1.json) and run 2 (after Amendment 1,
the live artefacts). The undercharge scenario is a CASE REPORT (n = 1), never a rate.
    uv run python scripts/x26_real_data_budget.py -> outputs/x26_real_data_budget.json
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(tag):
    b = json.loads((REPO / f"outputs/benchmark_v6_rtu_field{tag}.json").read_text())
    u = json.loads((REPO / f"outputs/union_fpr_rtu_field{tag}.json").read_text())
    case = next(s for s in b["scenarios"] if s["file"] == "Site2_Undercharged40")
    site1 = {s["file"]: {"days": s["days"], "model_days": s["model_days"], "residual_days": s["residual_days"]} for s in b["scenarios"] if s["file"].startswith("Site1")}
    return {"holdout_days": u["holdout_days"], "deployed_fp": u["union_minus_rate"]["holdout_fp_days"],
            "naive_fp": u["union_all8"]["holdout_fp_days"],
            "per_channel_fp": {k: v["holdout_fp_days"] for k, v in u["channels"].items()},
            "exposure": u["exposure"], "residual_band": b.get("residual_band"), "model_threshold": b["model_threshold"],
            "model_fp_provenance": u["channels"]["model"]["threshold_provenance"],
            "case_undercharge": {"days": case["days"], "evaluable": case["evaluable_days"], "rules_days": case["rules_days"],
                                 "residual_days": case["residual_days"], "model_days": case["model_days"],
                                 "frequency_days": case["frequency_days"], "oscillation_days": case["oscillation_days"],
                                 "meaningful_channels": case["meaningful_channels"]},
            "site1_other_unit_excluded": site1}


run1, run2 = load("_run1"), load("")
out = {"prereg": "docs/plans/2026-09-24-x26-real-data-budget-prereg.md", "run1_circuit1_only": run1, "run2_amendment1_both_circuits": run2}
hd = run2["holdout_days"]
pred = {"P1_healthy_silence_iterations": 2, "P1_le_3": True,
        "P2_budget_le_10pct": run2["deployed_fp"] / hd <= 0.10, "P2_deployed_fp_pct": round(100 * run2["deployed_fp"] / hd, 1),
        "P3_some_residual_abstains_ge_20pct": run2["exposure"]["residual_evaluable_holdout_days"] <= 0.8 * hd,
        "P4_case_ge_50pct_days_flagged_run1": run1["case_undercharge"]["residual_days"] >= 0.5 * run1["case_undercharge"]["days"],
        "A1_P1_budget_holds_with_circuit2": run2["deployed_fp"] / hd <= 0.10,
        "A1_P2_case_ge_50pct_days_flagged_run2": run2["case_undercharge"]["residual_days"] >= 0.5 * run2["case_undercharge"]["days"]}
fired = []
if not pred["P2_budget_le_10pct"]:
    fired.append("F-X26.a: the budget does not survive real data")
out["predictions"] = pred; out["falsifiers_fired"] = fired
out["claim"] = ("A measured false-alarm budget on one real building; the undercharge scenario is a case report, "
                "not a detection rate (n = 1 fault of one kind on one unit).")
(REPO / "outputs/x26_real_data_budget.json").write_text(json.dumps(out, indent=2) + "\n")
for tag, r in (("run1", run1), ("run2", run2)):
    print(f"{tag}: deployed FP {r['deployed_fp']}/{r['holdout_days']} naive {r['naive_fp']} | per channel {r['per_channel_fp']} | case: resid {r['case_undercharge']['residual_days']} model {r['case_undercharge']['model_days']} of {r['case_undercharge']['days']} -> {r['case_undercharge']['meaningful_channels']}")
print(pred); print("falsifiers:", fired or "none")
