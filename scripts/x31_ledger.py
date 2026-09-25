"""X31 — combine the per-system field-condition artefacts into the pre-registered
ledger. Pre-registration: docs/plans/2026-09-24-x31-field-conditions-prereg.md

    uv run python scripts/x31_ledger.py -> outputs/x31_field_conditions.json

Reads outputs/x31_field_conditions_<system>.json (written by x31_field_conditions.py)
and the clean scorecards; tests P1-P4 exactly as pre-registered and names the
scenarios gained or lost under every condition.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SYSTEMS = ["sdahu", "ddahu", "fcu"]
ARMS = ["field_noise", "cov_gaps", "schedule", "combined"]
DEPLOYED = {"rules", "resid", "freq", "osc", "absence"}


def clean_detected(system: str) -> set[str]:
    card = json.loads((REPO / f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]
    return {c["file"] for c in card if c["is_fault"] and not c["excluded"] and set(str(c["meaningful_channels"]).split("+")) & DEPLOYED}


def main() -> int:
    out = {"prereg": "docs/plans/2026-09-24-x31-field-conditions-prereg.md", "systems": {}, "predictions": {}, "falsifiers_fired": []}
    p1_fail, p2_fail, p3_fail, p4_fail, not_eval = [], [], [], [], []
    for s in SYSTEMS:
        path = REPO / f"outputs/x31_field_conditions_{s}.json"
        if not path.exists():
            not_eval += [(s, a) for a in ARMS]; out["systems"][s] = {"error": "artefact absent"}; continue
        a = json.loads(path.read_text())
        clean_det, clean_fp = a["clean_detected_no_alignment"], a["clean_holdout_fp_no_alignment"]
        clean_set = clean_detected(s)
        assert len(clean_set) == clean_det, (s, len(clean_set), clean_det)
        sysrow = {"clean_detected": clean_det, "clean_holdout_fp": clean_fp, "calendar": a["calendar"], "conditions": {}}
        for arm in ARMS:
            r = a["conditions"].get(arm)
            if r is None or "error" in r:
                not_eval.append((s, arm)); sysrow["conditions"][arm] = {"error": (r or {}).get("error", "not run")}; continue
            det_set = {k for k, v in r["per_scenario"].items() if v}
            row = {"detected": r["detected"], "n_scored": r["n_scored"], "holdout_fp_days": r["holdout_fp_days"], "holdout_days": r["holdout_days"],
                   "per_channel_fp": r["per_channel_fp"], "gained": sorted(det_set - clean_set), "lost": sorted(clean_set - det_set), "seconds": r.get("seconds")}
            fp, det = r["holdout_fp_days"], r["detected"]
            row["P1_budget"] = fp <= 10 and fp <= 2 * clean_fp + 2
            if not row["P1_budget"]:
                p1_fail.append((s, arm, fp))
            if arm in ("field_noise", "cov_gaps"):
                row["P2_within_minus_3"] = det >= clean_det - 3
                if not row["P2_within_minus_3"]:
                    p2_fail.append((s, arm, det, clean_det))
            if arm == "schedule":
                row["P3_within_pm_1_and_fp_le_clean_plus_2"] = abs(det - clean_det) <= 1 and fp <= clean_fp + 2
                if not row["P3_within_pm_1_and_fp_le_clean_plus_2"]:
                    p3_fail.append((s, arm, det, clean_det, fp, clean_fp))
            if arm == "combined":
                row["P4_within_minus_4"] = det >= clean_det - 4
                if not row["P4_within_minus_4"]:
                    p4_fail.append((s, arm, det, clean_det))
            sysrow["conditions"][arm] = row
        out["systems"][s] = sysrow
    out["predictions"] = {"P1_budget_all": not p1_fail, "P1_failures": p1_fail, "P2_noise_cov_within_minus_3": not p2_fail, "P2_failures": p2_fail,
                          "P3_schedule_within_pm_1": not p3_fail, "P3_failures": p3_fail, "P4_combined_within_minus_4": not p4_fail, "P4_failures": p4_fail,
                          "not_evaluated": not_eval}
    if p1_fail:
        out["falsifiers_fired"].append(f"F-X31.a: budget failed on {p1_fail}")
    if p2_fail or p4_fail:
        out["falsifiers_fired"].append(f"F-X31.b: detections lost beyond the bar on {p2_fail + p4_fail}")
    if not_eval:
        out["falsifiers_fired"].append(f"F-X31.c: not evaluated {not_eval}")
    (REPO / "outputs/x31_field_conditions.json").write_text(json.dumps(out, indent=2) + "\n")
    for s, v in out["systems"].items():
        if "error" in v:
            print(f"[{s}] {v['error']}"); continue
        for arm, r in v["conditions"].items():
            if "error" in r:
                print(f"[{s}] {arm:12s} NOT EVALUATED {r['error']}"); continue
            print(f"[{s}] {arm:12s} {r['detected']}/{r['n_scored']} (clean {v['clean_detected']}) fp {r['holdout_fp_days']}/{r['holdout_days']} (clean {v['clean_holdout_fp']}) gained {r['gained']} lost {r['lost']}")
    print(json.dumps(out["predictions"], indent=1)); print("falsifiers fired:", out["falsifiers_fired"] or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
