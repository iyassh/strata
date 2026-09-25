"""Guard: X33 coverage series ledgers (one per audited system)."""
import json
from pathlib import Path

import pytest

OUT = Path(__file__).resolve().parents[1] / "outputs"


def test_x33a_sdahu():
    art = OUT / "x33_coverage_sdahu.json"
    if not art.exists():
        pytest.skip("artifact absent")
    a = json.loads(art.read_text())
    assert a["columns_mapped"] == [12, 26] and a["columns_excluded"] == ["OA_CFM", "SA_SP", "SA_SPSPT", "SF_SPD"]
    assert (a["detected_before"], a["detected_after"], a["scored"]) == (14, 14, 14) and a["lost"] == [] and a["gained"] == []
    assert a["deployed_fp"] == [1, 1] and a["model_rows_identical"] and a["ttd_later"] == []
    assert {r: v["holdout_fp"] for r, v in a["new_rule_holdout_fp"].items()} == {"rf_specific_power": 0, "sf_flow_per_speed": 0, "sf_specific_power": 0}
    assert a["residual_days_rose_and_credited"] == ["coi_stuck_010_annual", "coi_stuck_025_annual"]
    assert all(a["predictions"].values()) and a["falsifiers_fired"] == []


def test_x33b_pfpu():
    art = OUT / "x33_coverage_pfpu.json"
    if not art.exists():
        pytest.skip("artifact absent")
    a = json.loads(art.read_text())
    assert a["columns_mapped"] == [56, 109] and a["columns_excluded"] == []
    assert (a["detected_before"], a["detected_after"], a["scored"]) == (22, 26, 30) and a["lost"] == []
    assert a["gained"] == ["PFPU_ReheatCoilFouling_Airside_Moderate", "PFPU_ReheatCoilFouling_Airside_Severe", "PFPU_SensorBias_RMTEMP_+2C", "PFPU_SensorBias_RMTEMP_+4C"]
    assert a["deployed_fp"] == [7, 8] and a["model_rows_identical"] and a["ttd_later"] == []
    assert all(v["holdout_fp"] <= 1 for v in a["new_rule_holdout_fp"].values()) and len(a["new_rule_holdout_fp"]) == 18
    assert a["predictions"]["P1_no_loss"] and a["predictions"]["P2_budget"] and a["falsifiers_fired"] == []
    c = json.loads((OUT / "x33_residual_credits_pfpu.json").read_text())["scenarios"]
    assert c["PFPU_ReheatCoilFouling_Airside_Severe"]["per_rule_flagged_days"]["da_minus_pm_S"] == 227
    assert c["PFPU_SensorBias_RMTEMP_+4C"]["per_rule_flagged_days"]["ra_minus_zone_S"] == 261


def test_x33c_sfpu():
    art = OUT / "x33_coverage_sfpu.json"
    if not art.exists():
        pytest.skip("artifact absent")
    a = json.loads(art.read_text())
    assert a["columns_mapped"] == [56, 109] and a["columns_excluded"] == []
    assert (a["detected_before"], a["detected_after"], a["scored"]) == (21, 25, 29) and a["lost"] == []
    assert a["gained"] == ["SFPU_ReheatCoilFouling_Airside_Moderate", "SFPU_ReheatCoilFouling_Airside_Severe", "SFPU_SensorBias_RMTEMP_+2C", "SFPU_VAVFanRestrictFlow"]
    assert a["deployed_fp"] == [6, 9] and a["model_rows_identical"] and a["ttd_later"] == []
    fp = {r: v["holdout_fp"] for r, v in a["new_rule_holdout_fp"].items()}
    assert len(fp) == 22 and max(fp.values()) == 2 and fp["static_per_speed2"] == 2
    assert a["predictions"]["P1_no_loss"] and a["predictions"]["P2_budget"] and a["falsifiers_fired"] == []
    c = json.loads((OUT / "x33_residual_credits_sfpu.json").read_text())["scenarios"]
    assert c["SFPU_VAVFanRestrictFlow"]["per_rule_flagged_days"]["zone_fan_spf_S"] == 261
    assert c["SFPU_ReheatCoilFouling_Airside_Severe"]["per_rule_flagged_days"]["zone_fan_spf_S"] == 261
    assert c["SFPU_ReheatCoilFouling_Airside_Moderate"]["per_rule_flagged_days"]["zone_fan_spf_S"] == 145

