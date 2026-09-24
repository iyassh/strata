"""X28 ledger — coil UA channel: before/after diff of the DDAHU and FCU scorecards.
'Before' = artefacts at BEFORE_COMMIT (X25 step 4 final gate, pre-X28).
    uv run python scripts/x28_coil_ua.py -> outputs/x28_coil_ua.json
"""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BEFORE_COMMIT = "295dfe3"


def at_commit(path):
    return json.loads(subprocess.run(["git", "show", f"{BEFORE_COMMIT}:{path}"], cwd=REPO, capture_output=True, text=True, check=True).stdout)


out = {"prereg": "docs/plans/2026-09-24-x28-coil-ua-prereg.md", "before_commit": BEFORE_COMMIT, "systems": {}}
for s in ("ddahu", "fcu"):
    b, a = at_commit(f"outputs/benchmark_v6_{s}.json"), json.loads((REPO / f"outputs/benchmark_v6_{s}.json").read_text())
    ub, ua = at_commit(f"outputs/union_fpr_{s}.json"), json.loads((REPO / f"outputs/union_fpr_{s}.json").read_text())
    B = {x["file"]: x for x in b["scenarios"] if x["is_fault"] and not x["excluded"]}
    A = {x["file"]: x for x in a["scenarios"] if x["is_fault"] and not x["excluded"]}
    foul = [f for f in A if "Fouling" in f]
    out["systems"][s] = {
        "detected_before": sum(1 for f in B if B[f]["meaningful_channels"]), "detected_after": sum(1 for f in A if A[f]["meaningful_channels"]), "scored": len(A),
        "fouling_before": sum(1 for f in foul if B[f]["meaningful_channels"]), "fouling_after": sum(1 for f in foul if A[f]["meaningful_channels"]), "fouling_scored": len(foul),
        "fouling_rows": {f: {"before": B[f]["meaningful_channels"], "after": A[f]["meaningful_channels"], "resid_days": [B[f]["residual_days"], A[f]["residual_days"]]} for f in foul},
        "gained": [f for f in A if A[f]["meaningful_channels"] and not B[f]["meaningful_channels"]],
        "lost": [f for f in A if B[f]["meaningful_channels"] and not A[f]["meaningful_channels"]],
        "deployed_fp_before": ub["union_minus_rate"]["holdout_fp_days"], "deployed_fp_after": ua["union_minus_rate"]["holdout_fp_days"],
        "residual_fp_before": ub["channels"]["resid"]["holdout_fp_days"], "residual_fp_after": ua["channels"]["resid"]["holdout_fp_days"]}
S = out["systems"]
pred = {"P0_VERIFIED_BY_HAND": True,   # console: x28_p0_verdict IDENTICAL (bc2dc4e, no config)
        "P1_budget": all(v["deployed_fp_after"] <= 10 and v["residual_fp_after"] - v["residual_fp_before"] <= 1 for v in S.values()),
        "P2_ddahu_ge_3_fouling_gained": len([f for f in S["ddahu"]["gained"] if "Fouling" in f]) >= 3,
        "P3_fcu_ge_2_fouling_gained": len([f for f in S["fcu"]["gained"] if "Fouling" in f]) >= 2,
        "P4_no_loss": all(not v["lost"] for v in S.values())}
fired = []
for s, v in S.items():
    if v["deployed_fp_after"] > 10: fired.append(f"F-X28.a: budget exceeded on {s}")
if not pred["P2_ddahu_ge_3_fouling_gained"] and not pred["P3_fcu_ge_2_fouling_gained"]:
    fired.append("F-X28.b: UA from these points does not see the simulated fouling on either system")
for s, v in S.items():
    if v["lost"]: fired.append(f"F-X28.c: detection lost on {s}: {v['lost']}")
out["predictions"] = pred; out["falsifiers_fired"] = fired
(REPO / "outputs/x28_coil_ua.json").write_text(json.dumps(out, indent=2) + "\n")
for s, v in S.items():
    print(f"{s:6s} detected {v['detected_before']}->{v['detected_after']}/{v['scored']} | fouling {v['fouling_before']}->{v['fouling_after']}/{v['fouling_scored']} | FP {v['deployed_fp_before']}->{v['deployed_fp_after']} (resid {v['residual_fp_before']}->{v['residual_fp_after']}) | gained {v['gained']} lost {v['lost']}")
    for f, r in v["fouling_rows"].items():
        if r["before"] != r["after"] or r["resid_days"][0] != r["resid_days"][1]: print(f"    {f:44s} {r['before']} -> {r['after']} resid {r['resid_days']}")
print(pred); print("falsifiers:", fired or "none")
