"""X25 ledger — before/after diff of every system's scorecard and false-alarm
artefact across the statistical repair (calibration slice + rule-of-three floor).
'Before' = the artefacts as committed at BEFORE_COMMIT (the last pre-X25 state).
    uv run python scripts/x25_statistical_repair.py -> outputs/x25_statistical_repair.json
"""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
import sys
BEFORE_COMMIT = sys.argv[sys.argv.index("--before") + 1] if "--before" in sys.argv else "5bd7c5e"
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "outputs/x25_statistical_repair.json"
SYSTEMS = ("sdahu", "pfpu", "sfpu", "ddahu", "fcu")


def at_commit(path):
    return json.loads(subprocess.run(["git", "show", f"{BEFORE_COMMIT}:{path}"], cwd=REPO, capture_output=True, text=True, check=True).stdout)


out = {"prereg": "docs/plans/2026-09-24-x25-statistical-repair-prereg.md", "before_commit": BEFORE_COMMIT, "systems": {}}
total_flips = 0
for s in SYSTEMS:
    b, a = at_commit(f"outputs/benchmark_v6_{s}.json"), json.loads((REPO / f"outputs/benchmark_v6_{s}.json").read_text())
    ub, ua = at_commit(f"outputs/union_fpr_{s}.json"), json.loads((REPO / f"outputs/union_fpr_{s}.json").read_text())
    B = {x["file"]: x for x in b["scenarios"] if x["is_fault"] and not x["excluded"]}
    A = {x["file"]: x for x in a["scenarios"] if x["is_fault"] and not x["excluded"]}
    det_b = sum(1 for f in B if B[f]["meaningful_channels"]); det_a = sum(1 for f in A if A[f]["meaningful_channels"])
    gained = [f for f in A if A[f]["meaningful_channels"] and not B[f]["meaningful_channels"]]
    lost = [f for f in A if B[f]["meaningful_channels"] and not A[f]["meaningful_channels"]]
    changed = {f: [B[f]["meaningful_channels"], A[f]["meaningful_channels"]] for f in A if B[f]["meaningful_channels"] != A[f]["meaningful_channels"]}
    conf_only = [f for f in A if A[f]["meaningful_channels"] and set(str(A[f]["meaningful_channels"]).split("+")) <= {"model", "device"}]
    total_flips += len(gained) + len(lost)
    out["systems"][s] = {
        "detected_before": det_b, "detected_after": det_a, "scored": len(A), "gained": gained, "lost": lost, "status_changed": changed,
        "conformance_only_after": conf_only,
        "model_threshold_before": b["model_threshold"], "model_threshold_after": a["model_threshold"],
        "model_holdout_fp_before": b["model_holdout_fp"], "model_holdout_fp_after": a["model_holdout_fp"],
        "model_fp_provenance_after": ua["channels"]["model"]["threshold_provenance"],
        "device_fp_provenance_after": ua["channels"].get("device", {}).get("threshold_provenance"),
        "deployed_fp_before": ub["union_minus_rate"]["holdout_fp_days"], "deployed_fp_after": ua["union_minus_rate"]["holdout_fp_days"],
        "per_channel_fp_after": {k: v["holdout_fp_days"] for k, v in ua["channels"].items()},
        "per_channel_fp_before": {k: v["holdout_fp_days"] for k, v in ub["channels"].items()},
        "model_credits_before": sum(1 for f in B if "model" in str(B[f]["meaningful_channels"]).split("+")),
        "model_credits_after": sum(1 for f in A if "model" in str(A[f]["meaningful_channels"]).split("+")),
    }
S = out["systems"]
pred = {"P0_step1_sdahu_byte_identical_VERIFIED_BY_HAND": True,   # console: x25_p0_verdict IDENTICAL at 5bd7c5e (key absent)
        "P1_out_of_sample": all("out-of-sample" in v["model_fp_provenance_after"] and (("out-of-sample" in (v["device_fp_provenance_after"] or "")) or ("channel absent" in (v["device_fp_provenance_after"] or ""))) for v in S.values()),
        "P2_budget_le_10": all(v["deployed_fp_after"] <= 10 for v in S.values()),
        "P3_counts_within_2": all(abs(v["detected_after"] - v["detected_before"]) <= 2 for v in S.values()),
        "P3_no_conformance_only": all(not v["conformance_only_after"] for v in S.values()),
        "P4_status_flips_total": total_flips, "P4_le_3": total_flips <= 3}
fired = []
for s, v in S.items():
    if v["deployed_fp_after"] > 10: fired.append(f"F-X25.a: budget exceeded on {s} ({v['deployed_fp_after']}/96)")
    if v["conformance_only_after"]: fired.append(f"F-X25.b: conformance-only detection on {s}: {v['conformance_only_after']}")
    if v["detected_before"] - v["detected_after"] > 2: fired.append(f"F-X25.c: {s} lost more than 2 detections: {v['lost']}")
out["predictions"] = pred; out["falsifiers_fired"] = fired
(REPO / OUT).write_text(json.dumps(out, indent=2) + "\n")
for s, v in S.items():
    print(f"{s:6s} detected {v['detected_before']}->{v['detected_after']}/{v['scored']} | deployed FP {v['deployed_fp_before']}->{v['deployed_fp_after']} | model thr {v['model_threshold_before']:.3f}->{v['model_threshold_after']:.3f} FP {v['model_holdout_fp_before']}->{v['model_holdout_fp_after']} | model credits {v['model_credits_before']}->{v['model_credits_after']} | gained {v['gained']} lost {v['lost']}")
print(pred); print("falsifiers:", fired or "none")
