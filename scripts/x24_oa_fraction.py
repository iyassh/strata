"""X24 ledger — the outdoor-air-fraction residual: scenario-level diff of the
scorecards before (git a4b57cb^, i.e. the committed artefacts before X24 scoring)
and after, plus the pre-registered predictions.
    uv run python scripts/x24_oa_fraction.py -> outputs/x24_oa_fraction.json
"""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BEFORE_COMMIT = "a4b57cb"      # configs committed before scoring; artefacts at this commit are pre-X24
AFTER_COMMIT = "944e477"       # X24 closing commit (X25 later changed the live scorecards)
SYSTEMS = ("fcu", "sdahu", "ddahu")


def at_commit(path: str, commit: str = BEFORE_COMMIT) -> dict:
    txt = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    return json.loads(txt)


out = {"prereg": "docs/plans/2026-09-24-x24-oa-fraction-prereg.md", "before_commit": BEFORE_COMMIT, "systems": {}}
for s in SYSTEMS:
    b = at_commit(f"outputs/benchmark_v6_{s}.json"); a = at_commit(f"outputs/benchmark_v6_{s}.json", AFTER_COMMIT)
    ub = at_commit(f"outputs/union_fpr_{s}.json"); ua = at_commit(f"outputs/union_fpr_{s}.json", AFTER_COMMIT)
    B = {x["file"]: x for x in b["scenarios"] if x["is_fault"] and not x["excluded"]}
    A = {x["file"]: x for x in a["scenarios"] if x["is_fault"] and not x["excluded"]}
    gained = [f for f in A if A[f]["meaningful_channels"] and not B[f]["meaningful_channels"]]
    lost = [f for f in A if B[f]["meaningful_channels"] and not A[f]["meaningful_channels"]]
    changed = {f: (B[f]["meaningful_channels"], A[f]["meaningful_channels"]) for f in A if B[f]["meaningful_channels"] != A[f]["meaningful_channels"]}
    resid_days_delta = {f: int(A[f]["residual_days"]) - int(B[f]["residual_days"]) for f in A if A[f]["residual_days"] != B[f]["residual_days"]}
    out["systems"][s] = {
        "detected_before": sum(1 for f in B if B[f]["meaningful_channels"]), "detected_after": sum(1 for f in A if A[f]["meaningful_channels"]),
        "scored": len(A), "gained": gained, "lost": lost, "status_changed": changed, "residual_days_delta": resid_days_delta,
        "deployed_fp_before": ub["union_minus_rate"]["holdout_fp_days"], "deployed_fp_after": ua["union_minus_rate"]["holdout_fp_days"],
        "residual_fp_before": ub["channels"]["resid"]["holdout_fp_days"], "residual_fp_after": ua["channels"]["resid"]["holdout_fp_days"],
        "residual_band_after": a.get("residual_band"),
    }
fcu = out["systems"]["fcu"]
pred = {"P1_regression_sdahu_byte_identical_before_configs_VERIFIED_BY_HAND": True,   # console only (x24_reg_verdict IDENTICAL, 2026-09-24); not recomputed here
        "P2_healthy_silence_unchanged_VERIFIED_BY_HAND": True,                            # console only (03_healthy_silence 0 / 0 / 1 pre-existing)
        "P3_fcu_leak20_detected": "FCU_OADMPRLeak_20" in fcu["gained"] or bool(json.loads((REPO / "outputs/benchmark_v6_fcu.json").read_text())),
        "P4_budget_le_10": all(v["deployed_fp_after"] <= 10 for v in out["systems"].values()),
        "P5_no_loss": all(not v["lost"] for v in out["systems"].values())}
pred["P3_fcu_leak20_detected"] = "FCU_OADMPRLeak_20" in fcu["gained"]
fired = []
if not pred["P3_fcu_leak20_detected"]:
    fired.append("F-X24.b: the 20% leak stays undetected")
for s, v in out["systems"].items():
    if v["deployed_fp_after"] > 10:
        fired.append(f"F-X24.c: budget exceeded on {s}")
    if v["lost"]:
        fired.append(f"F-X24.d: detection lost on {s}: {v['lost']}")
out["predictions"] = pred; out["falsifiers_fired"] = fired
(REPO / "outputs/x24_oa_fraction.json").write_text(json.dumps(out, indent=2) + "\n")
for s, v in out["systems"].items():
    print(f"{s:6s} detected {v['detected_before']}->{v['detected_after']} of {v['scored']} | FP {v['deployed_fp_before']}->{v['deployed_fp_after']} (resid {v['residual_fp_before']}->{v['residual_fp_after']}) | gained {v['gained']} lost {v['lost']} | status changes {len(v['status_changed'])} | resid-day deltas {len(v['residual_days_delta'])}")
print(pred); print("falsifiers:", fired or "none")
