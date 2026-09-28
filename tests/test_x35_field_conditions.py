"""Guard: X35 — field conditions (sensor error and quantisation, COV logging with gaps, schedule
shifts, all three) on the post-coverage configurations of all five simulated systems, through the
X31 facade against a clean arm of the same facade. No falsifier fired: budget worst 7/96, losses at
most one per system and condition (named), clean arm equals the scorecard everywhere; P3 (two or
more edge recoveries lost under noise) was a wrong prediction — one was lost."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x35_field_conditions.json"
CLEAN = {"sdahu": 14, "pfpu": 26, "sfpu": 25, "ddahu": 50, "fcu": 43}


def test_x35_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    x = a["x35"]
    p = x["predictions"]
    assert p["P1_budget_le_10_and_le_clean_plus_3"] and p["P2_noise_cov_within_minus_4"] and p["P4_schedule_within_pm_3"]
    assert p["P5_combined_within_minus_6"] and p["P6_clean_arm_matches_scorecard"]
    assert not p["P3_ge_2_edge_recoveries_lost_under_noise"] and p["P3_edge_lost_under_noise"] == ["PFPU_ReheatCoilFouling_Airside_Moderate"]
    assert x["falsifiers_fired"] == [] and x["predictions_failed_without_falsifier"] == ["P3_ge_2_edge_recoveries_lost_under_noise"]
    assert a["predictions"]["not_evaluated"] == [] and a["predictions"]["clean_arm_matches_scorecard"]
    S = a["systems"]
    assert {s: S[s]["clean_detected"] for s in S} == CLEAN
    det = {s: {arm: S[s]["conditions"][arm]["detected"] for arm in S[s]["conditions"]} for s in S}
    assert det["sdahu"] == {"field_noise": 14, "cov_gaps": 13, "schedule": 14, "combined": 14}
    assert det["pfpu"] == {"field_noise": 25, "cov_gaps": 25, "schedule": 26, "combined": 25}
    assert det["sfpu"] == {"field_noise": 25, "cov_gaps": 25, "schedule": 25, "combined": 25}
    assert det["ddahu"] == {"field_noise": 50, "cov_gaps": 50, "schedule": 50, "combined": 49}
    assert det["fcu"] == {"field_noise": 43, "cov_gaps": 43, "schedule": 43, "combined": 43}
    fp = [S[s]["conditions"][arm]["holdout_fp_days"] for s in S for arm in S[s]["conditions"]]
    assert max(fp) == 7
    assert S["sdahu"]["conditions"]["cov_gaps"]["lost"] == ["oa_bias_4_annual"]
    assert S["ddahu"]["conditions"]["combined"]["lost"] == ["DualDuct_Fouling_Cooling_Waterside_Moderate"]
    for arm in ("field_noise", "cov_gaps", "combined"):
        assert S["pfpu"]["conditions"][arm]["lost"] == ["PFPU_ReheatCoilFouling_Airside_Moderate"]
    assert all(S[s]["conditions"][arm]["gained"] == [] for s in S for arm in S[s]["conditions"])
