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


def test_x33d_ddahu():
    art = OUT / "x33_coverage_ddahu.json"
    if not art.exists():
        pytest.skip("artifact absent")
    a = json.loads(art.read_text())
    assert a["columns_mapped"] == [79, 114] and a["columns_excluded"] == []
    assert (a["detected_before"], a["detected_after"], a["scored"]) == (45, 50, 55) and a["lost"] == []
    assert a["gained"] == ["DualDuct_Fouling_Cooling_Airside_Moderate", "DualDuct_Fouling_Heating_Waterside_Minor", "DualDuct_SensorBias_HSA_+2C", "DualDuct_SensorBias_HSP_-2inwg", "DualDuct_SensorBias_HSP_-4inwg"]
    assert a["deployed_fp"] == [3, 3] and a["model_rows_identical"] and a["ttd_later"] == []
    assert len(a["new_rule_holdout_fp"]) == 25 and all(v["holdout_fp"] == 0 for v in a["new_rule_holdout_fp"].values())
    assert a["predictions"]["P1_no_loss"] and a["predictions"]["P2_budget"] and a["falsifiers_fired"] == []
    c = json.loads((OUT / "x33_residual_credits_ddahu.json").read_text())["scenarios"]
    assert c["DualDuct_SensorBias_HSP_-4inwg"]["per_rule_flagged_days"]["box_static_H_SA"] == 282
    assert c["DualDuct_Fouling_Heating_Waterside_Minor"]["per_rule_flagged_days"]["hwp_bypass_flow"] == 282


def test_x33e_fcu():
    art = OUT / "x33_coverage_fcu.json"
    if not art.exists():
        pytest.skip("artifact absent")
    a = json.loads(art.read_text())
    assert a["columns_mapped"] == [29, 29] and a["columns_excluded"] == []
    assert (a["detected_before"], a["detected_after"], a["scored"]) == (40, 43, 47) and a["lost"] == []
    assert a["gained"] == ["FCU_Fouling_Heating_Waterside_Moderate", "FCU_OADMPRLeak_20", "FCU_OADMPRLeak_50"]
    assert a["deployed_fp"] == [4, 5] and a["model_rows_identical"] and a["ttd_later"] == []
    assert {r: v["holdout_fp"] for r, v in a["new_rule_holdout_fp"].items()} == {"fan_specific_power": 1, "oa_flow_ratio_min_pos": 1}
    assert a["falsifiers_fired"] == []
    c = json.loads((OUT / "x33_residual_credits_fcu.json").read_text())["scenarios"]
    assert c["FCU_OADMPRLeak_20"]["per_rule_flagged_days"]["oa_flow_ratio_min_pos"] == 261


def test_x33_series_totals():
    tot_b = tot_a = fp_b = fp_a = 0
    for s in ("sdahu", "pfpu", "sfpu", "ddahu", "fcu"):
        art = OUT / f"x33_coverage_{s}.json"
        if not art.exists():
            pytest.skip("artifact absent")
        a = json.loads(art.read_text())
        tot_b += a["detected_before"]; tot_a += a["detected_after"]; fp_b += a["deployed_fp"][0]; fp_a += a["deployed_fp"][1]
        assert a["lost"] == [] and a["model_rows_identical"]
    assert (tot_b, tot_a) == (142, 158) and (fp_b, fp_a) == (21, 26)

