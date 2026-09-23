"""Does the alarm name the right equipment? Scored on every detected scenario.

Reads the committed scorecards only (no re-run). For each detected,
non-excluded scenario: the seeded zone, the device the deployed alarm names
(`top_device`), and whether they agree. Because every seeded zone fault in
the LBNL FPU sets is in zone S, agreement is specificity, not discrimination
(RESEARCH_LOG L14): the informative counts are the wrong attributions and
the silent ones. SDAHU has no device stratum, so its alarms carry a rule
name and no device — reported as such, not as a miss.

    uv run python scripts/alarm_attribution.py   -> outputs/alarm_attribution.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows, counts = [], {"correct": 0, "none": 0, "wrong": 0, "no_device_stratum": 0, "indeterminate_gt": 0}
for s in ("sdahu", "pfpu", "sfpu"):
    d = json.loads((ROOT / "outputs" / f"benchmark_v6_{s}.json").read_text())
    for x in d["scenarios"]:
        if x.get("excluded") or x.get("ttd_days") is None:
            continue
        gt, dev = x.get("ground_truth_zone"), x.get("top_device")
        if gt is None:
            cls = "no_device_stratum"
        elif gt == "INDETERMINATE":
            cls = "indeterminate_gt"
        elif dev is None:
            cls = "none"
        elif dev.endswith("_" + gt):
            cls = "correct"
        else:
            cls = "wrong"
        counts[cls] += 1
        rows.append({"system": s, "scenario": x["file"], "family": x.get("family"),
                     "seeded_zone": gt, "alarm_device": dev, "channels": x.get("meaningful_channels"),
                     "attribution": cls})
out = {"source": "benchmark_v6_*.json (committed scorecards; no re-run)", "n_detected": len(rows),
       "counts": counts,
       "note": ("Zone ground truth has no variance on the FPU sets (all zone S), so 'correct' is "
                "specificity; 'wrong' and 'none' are the informative counts. SDAHU has no device "
                "stratum and names no device by construction."),
       "rows": rows}
(ROOT / "outputs" / "alarm_attribution.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({"n_detected": len(rows), **counts}))
