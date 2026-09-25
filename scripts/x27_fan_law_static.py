"""X27 ledger — fan-law virtual static (static / speed^2) on the dual-duct unit:
before/after diff of the DDAHU scorecard across the two added channels.
'Before' = artefacts at BEFORE_COMMIT (post-X25, pre-X27).
    uv run python scripts/x27_fan_law_static.py -> outputs/x27_fan_law_static.json
"""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BEFORE_COMMIT = "c7f35fc"


def at_commit(path, commit=None):
    return json.loads(subprocess.run(["git", "show", f"{commit or BEFORE_COMMIT}:{path}"], cwd=REPO, capture_output=True, text=True, check=True).stdout)


AFTER_COMMIT = "4d0250a"   # X27 closing commit (step 4 later changed the live scorecard)
b, a = at_commit("outputs/benchmark_v6_ddahu.json"), at_commit("outputs/benchmark_v6_ddahu.json", AFTER_COMMIT)
ub, ua = at_commit("outputs/union_fpr_ddahu.json"), at_commit("outputs/union_fpr_ddahu.json", AFTER_COMMIT)
B = {x["file"]: x for x in b["scenarios"] if x["is_fault"] and not x["excluded"]}
A = {x["file"]: x for x in a["scenarios"] if x["is_fault"] and not x["excluded"]}
static = [f for f in A if "SensorBias_CSP" in f or "SensorBias_HSP" in f]
out = {"prereg": "docs/plans/2026-09-24-x27-fan-law-static-prereg.md", "before_commit": BEFORE_COMMIT,
       "detected_before": sum(1 for f in B if B[f]["meaningful_channels"]), "detected_after": sum(1 for f in A if A[f]["meaningful_channels"]), "scored": len(A),
       "static_bias_before": sum(1 for f in static if B[f]["meaningful_channels"]), "static_bias_after": sum(1 for f in static if A[f]["meaningful_channels"]),
       "static_bias_rows": {f: {"before": B[f]["meaningful_channels"], "after": A[f]["meaningful_channels"], "residual_days_before": B[f]["residual_days"], "residual_days_after": A[f]["residual_days"]} for f in static},
       "gained": [f for f in A if A[f]["meaningful_channels"] and not B[f]["meaningful_channels"]],
       "lost": [f for f in A if B[f]["meaningful_channels"] and not A[f]["meaningful_channels"]],
       "deployed_fp_before": ub["union_minus_rate"]["holdout_fp_days"], "deployed_fp_after": ua["union_minus_rate"]["holdout_fp_days"],
       "residual_fp_before": ub["channels"]["resid"]["holdout_fp_days"], "residual_fp_after": ua["channels"]["resid"]["holdout_fp_days"]}
pred = {"P0_regression_sdahu_byte_identical_VERIFIED_BY_HAND": True,   # console: x27_p0_verdict
        "P1_budget_le_10": out["deployed_fp_after"] <= 10, "P1_residual_fp_le_2_more": out["residual_fp_after"] - out["residual_fp_before"] <= 2,
        "P2_static_bias_ge_7_of_8": out["static_bias_after"] >= 7, "P3_no_loss": not out["lost"]}
fired = []
if not pred["P1_budget_le_10"]: fired.append("F-X27.a: budget exceeded")
if not pred["P2_static_bias_ge_7_of_8"]: fired.append(f"F-X27.b: static-bias detections {out['static_bias_after']} of 8 (needed 7)")
if out["lost"]: fired.append(f"F-X27.c: detection lost: {out['lost']}")
out["predictions"] = pred; out["falsifiers_fired"] = fired
(REPO / "outputs/x27_fan_law_static.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"detected {out['detected_before']}->{out['detected_after']}/{out['scored']} | static bias {out['static_bias_before']}->{out['static_bias_after']}/8 | deployed FP {out['deployed_fp_before']}->{out['deployed_fp_after']} (resid {out['residual_fp_before']}->{out['residual_fp_after']}) | gained {out['gained']} lost {out['lost']}")
for f, r in out["static_bias_rows"].items(): print(f"  {f:34s} {r['before']} -> {r['after']}  resid days {r['residual_days_before']}->{r['residual_days_after']}")
print(pred); print("falsifiers:", fired or "none")
