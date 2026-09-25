"""Guard: X31 — field conditions (sensor error and feedback quantisation, change-of-value
logging with gaps, schedule shifts, all three) injected into SDAHU, DDAHU and FCU and
scored through the repaired library facade (Amendment 1) against a clean arm of the same
facade. Budget holds everywhere (P1); noise and COV cost at most three detections (P2);
combined at most one (P4); the schedule shift GAINS three DDAHU sensor-bias detections
(P3 failed upward). The absence channel was not exercised (device stratum off)."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x31_field_conditions.json"


def test_x31_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    p = a["predictions"]
    assert p["P1_budget_all"] and p["P2_noise_cov_within_minus_3"] and p["P4_combined_within_minus_4"]
    assert not p["P3_schedule_within_pm_1"] and p["P3_failures"] == [["ddahu", "schedule", 48, 45, 0, 0]]
    assert p["clean_arm_matches_scorecard"] and p["absence_channel_evaluated"] is False and p["not_evaluated"] == []
    S = a["systems"]
    assert {s: S[s]["clean_detected"] for s in S} == {"sdahu": 14, "ddahu": 45, "fcu": 40}
    det = {s: {arm: S[s]["conditions"][arm]["detected"] for arm in S[s]["conditions"]} for s in S}
    assert det["sdahu"] == {"field_noise": 14, "cov_gaps": 13, "schedule": 14, "combined": 14}
    assert det["ddahu"] == {"field_noise": 44, "cov_gaps": 42, "schedule": 48, "combined": 45}
    assert det["fcu"] == {"field_noise": 39, "cov_gaps": 40, "schedule": 40, "combined": 39}
    fp = {s: {arm: S[s]["conditions"][arm]["holdout_fp_days"] for arm in S[s]["conditions"]} for s in S}
    assert max(v for d in fp.values() for v in d.values()) <= 3
    assert S["sdahu"]["conditions"]["cov_gaps"]["lost"] == ["oa_bias_4_annual"]
    assert S["fcu"]["conditions"]["field_noise"]["lost"] == ["FCU_OADMPRLeak_80"]
    assert a["falsifiers_fired"] == []
