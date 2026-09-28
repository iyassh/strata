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
SYSTEMS = ["sdahu", "pfpu", "sfpu", "ddahu", "fcu"]   # X35 (2026-09-27): all five; X31 ran sdahu/ddahu/fcu
ARMS = ["field_noise", "cov_gaps", "schedule", "combined"]   # "clean" is the comparator, reported per system
DEPLOYED = {"rules", "resid", "freq", "osc", "absence"}


def clean_detected(system: str) -> set[str]:
    card = json.loads((REPO / f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]
    return {c["file"] for c in card if c["is_fault"] and not c["excluded"] and set(str(c["meaningful_channels"]).split("+")) & DEPLOYED}


def absence_fp_dates(system: str) -> list[str]:
    u = json.loads((REPO / f"outputs/union_fpr_{system}.json").read_text())["channels"]
    others = set().union(*[set(v["holdout_fp_dates"]) for k, v in u.items() if k in ("rules", "resid", "freq", "osc")])
    return [d for d in u.get("absence", {}).get("holdout_fp_dates", []) if d not in others]


X35_EDGE = ["PFPU_ReheatCoilFouling_Airside_Moderate", "PFPU_ReheatCoilFouling_Airside_Severe", "PFPU_SensorBias_RMTEMP_+2C",
            "SFPU_ReheatCoilFouling_Airside_Moderate", "DualDuct_Fouling_Heating_Waterside_Minor"]
X35_SCORECARD = {"sdahu": 14, "pfpu": 26, "sfpu": 25, "ddahu": 50, "fcu": 43}


def x35_predictions(out: dict) -> dict:
    """X35 (docs/plans/2026-09-27-x35-field-conditions-post-coverage-prereg.md): the six bars as pre-registered,
    evaluated on the same per-arm rows. The rows above keep X31's bars for the record; X35's are these."""
    S = out["systems"]
    p1, p2, p4, p5, edge_lost, p6 = [], [], [], [], [], []
    for s, v in S.items():
        if "error" in v:
            continue
        cd, cf = v["clean_detected"], v["clean_holdout_fp"]
        if cd != X35_SCORECARD[s] or v.get("facade_matches_scorecard_fp_without_absence") is False:
            p6.append((s, cd, X35_SCORECARD[s], cf, v.get("scorecard_holdout_fp_without_absence")))
        for arm, r in v["conditions"].items():
            if "error" in r:
                continue
            if not (r["holdout_fp_days"] <= 10 and r["holdout_fp_days"] <= cf + 3):
                p1.append((s, arm, r["holdout_fp_days"], cf))
            if arm in ("field_noise", "cov_gaps") and r["detected"] < cd - 4:
                p2.append((s, arm, r["detected"], cd))
            if arm == "schedule" and abs(r["detected"] - cd) > 3:
                p4.append((s, arm, r["detected"], cd))
            if arm == "combined" and r["detected"] < cd - 6:
                p5.append((s, arm, r["detected"], cd))
            if arm == "field_noise":
                edge_lost += [f for f in r["lost"] if f in X35_EDGE]
    pred = {"P1_budget_le_10_and_le_clean_plus_3": not p1, "P1_failures": p1,
            "P2_noise_cov_within_minus_4": not p2, "P2_failures": p2,
            "P3_ge_2_edge_recoveries_lost_under_noise": len(edge_lost) >= 2, "P3_edge_lost_under_noise": edge_lost,
            "P4_schedule_within_pm_3": not p4, "P4_failures": p4,
            "P5_combined_within_minus_6": not p5, "P5_failures": p5,
            "P6_clean_arm_matches_scorecard": not p6, "P6_failures": p6}
    fired = []
    if p1: fired.append(f"F-X35.a: budget failed on {p1}")
    if p2 or p5: fired.append(f"F-X35.b: detections lost beyond the bar on {p2 + p5}")
    if p6: fired.append(f"F-X35.c: clean arm differs from the scorecard on {p6}")
    if out["predictions"].get("not_evaluated"): fired.append(f"not evaluated: {out['predictions']['not_evaluated']}")
    wrong = [k for k in ("P3_ge_2_edge_recoveries_lost_under_noise", "P4_schedule_within_pm_3") if not pred[k]]
    return {"prereg": "docs/plans/2026-09-27-x35-field-conditions-post-coverage-prereg.md", "predictions": pred, "falsifiers_fired": fired,
            "predictions_failed_without_falsifier": wrong,
            "note": "X35's bars were added to this ledger after the arms had run (the ledger of 2026-09-27 evaluated X31's bars); the bars are copied from the pre-registration unchanged"}


def main() -> int:
    out = {"prereg": "docs/plans/2026-09-24-x31-field-conditions-prereg.md", "systems": {}, "predictions": {}, "falsifiers_fired": []}
    p1_fail, p2_fail, p3_fail, p4_fail, not_eval = [], [], [], [], []
    for s in SYSTEMS:
        path = REPO / f"outputs/x31_field_conditions_{s}.json"
        if not path.exists():
            not_eval += [(s, a) for a in ARMS]; out["systems"][s] = {"error": "artefact absent"}; continue
        a = json.loads(path.read_text())
        card_det, card_fp = a["clean_detected_no_alignment"], a["clean_holdout_fp_no_alignment"]
        clean_set = clean_detected(s)
        assert len(clean_set) == card_det, (s, len(clean_set), card_det)
        # Amendment 1: the comparator is the facade's own clean arm; the scorecard count is reported beside it
        ca = a["conditions"].get("clean")
        if ca is None or "error" in ca:
            not_eval.append((s, "clean")); clean_det, clean_fp = card_det, card_fp; facade_ok = None
        else:
            clean_set = {k for k, v in ca["per_scenario"].items() if v}
            clean_det, clean_fp = ca["detected"], ca["holdout_fp_days"]
            facade_ok = (clean_det == card_det)
        # The absence channel rides on the device stratum, which the alignment-off setting removes
        # (X9/X10 Amendment 3), so X31 exercises rules, residual, frequency and oscillation only;
        # the scorecard's false alarms are compared without absence days.
        card_fp_no_absence = card_fp - len(set(uabs)) if (uabs := absence_fp_dates(s)) else card_fp
        sysrow = {"clean_detected": clean_det, "clean_holdout_fp": clean_fp, "scorecard_detected": card_det, "scorecard_holdout_fp": card_fp,
                  "scorecard_holdout_fp_without_absence": card_fp_no_absence, "absence_channel_evaluated": False,
                  "facade_matches_scorecard_detections": facade_ok,
                  "facade_matches_scorecard_fp_without_absence": (clean_fp == card_fp_no_absence) if ca and "error" not in ca else None,
                  "calendar": a["calendar"], "conditions": {}}
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
    mism = [s for s, v in out["systems"].items() if v.get("facade_matches_scorecard_detections") is False or v.get("facade_matches_scorecard_fp_without_absence") is False]
    out["predictions"]["clean_arm_matches_scorecard"] = not mism
    out["predictions"]["absence_channel_evaluated"] = False
    # Amendment 1 predicted the clean arm's false alarms at the scorecard's deployed-union-without-alignment count
    # (1, 3, 3); DDAHU came in at 0 because the absence channel (three scorecard days) rides on the device stratum
    # that this experiment never builds. The prediction FAILED as written; the absence-free comparator was chosen
    # after seeing the number and is recorded here as such.
    clean_fp_obs = {s: v.get("clean_holdout_fp") for s, v in out["systems"].items() if "error" not in v}
    clean_fp_pred = {s: v.get("scorecard_holdout_fp") for s, v in out["systems"].items() if "error" not in v}
    out["predictions"]["amendment1_clean_fp_prediction"] = {"predicted": clean_fp_pred, "observed": clean_fp_obs, "held": clean_fp_pred == clean_fp_obs,
                                                             "post_hoc_comparator": "scorecard false alarms without absence days"}
    failed = []
    if p3_fail:
        failed.append(f"P3 (schedule within ±1): {p3_fail}")
    if clean_fp_pred != clean_fp_obs:
        failed.append(f"Amendment 1 clean-arm false alarms: predicted {clean_fp_pred}, observed {clean_fp_obs}")
    out["predictions"]["predictions_failed_without_falsifier"] = failed
    out["deviations"] = ["common random numbers hold for the noise and quantisation draws but not for gap placement: one generator per file, so the combined arm's gap blocks differ from the cov_gaps arm's",
                         "the schedule arm shifts the occupied block 30 minutes earlier (start and end), leaving its length unchanged: a whole-day shift, not the extension the pre-registration's 'optimum start' implies"]
    if mism:
        out["falsifiers_fired"].append(f"Amendment 1: facade differs from the scorecard on {mism}")
    import sys as _s
    if "--x35" in _s.argv:
        out["x35"] = x35_predictions(out)
    _out = "outputs/x35_field_conditions.json" if "--x35" in _s.argv else "outputs/x31_field_conditions.json"
    (REPO / _out).write_text(json.dumps(out, indent=2) + "\n")
    for s, v in out["systems"].items():
        if "error" in v:
            print(f"[{s}] {v['error']}"); continue
        for arm, r in v["conditions"].items():
            if "error" in r:
                print(f"[{s}] {arm:12s} NOT EVALUATED {r['error']}"); continue
            print(f"[{s}] {arm:12s} {r['detected']}/{r['n_scored']} (clean {v['clean_detected']}) fp {r['holdout_fp_days']}/{r['holdout_days']} (clean {v['clean_holdout_fp']}) gained {r['gained']} lost {r['lost']}")
    print(json.dumps(out["predictions"], indent=1)); print("falsifiers fired:", out["falsifiers_fired"] or "none")
    if "x35" in out:
        print("X35:", json.dumps(out["x35"]["predictions"], indent=1)); print("X35 falsifiers fired:", out["x35"]["falsifiers_fired"] or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
