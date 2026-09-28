"""Guard: X38 (Amendment 1, run 2) — the repaired open-fdd 4.4.1 battery on the same exam as STRATA under
three framings. F-X38.a fired under G2 (PFPU, SFPU), G3 (all three) and S (PFPU, SFPU): on the single-duct
unit the healthy-year-silent battery detects 12/14 at 1 false-alarm day against STRATA's 13/14 at 1; on the
terminal units 8/30 and 9/29 at 0 against 26/30 and 25/29 at 8 and 9. G2 on the fan-powered units is not
detection (identical day sets on healthy and fault files). Pins the ledger; run 1 is kept and not quoted."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "outputs" / "x38_guideline36.json"


def test_x38_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["amendment"] == 1 and a["run"] == 2 and (ROOT / "outputs" / "x38_guideline36_run1.json").exists()
    S = a["systems"]
    g3 = {s: (S[s]["battery_G3"], S[s]["G3_false_alarms"]["holdout_fp_days"]) for s in S}
    assert g3 == {"sdahu": (12, 1), "pfpu": (8, 0), "sfpu": (9, 0)}
    assert {s: S[s]["battery_G2"] for s in S} == {"sdahu": 12, "pfpu": 30, "sfpu": 29}
    assert {s: (S[s]["battery_gated"], S[s]["battery_gated_demoted"]) for s in S} == {"sdahu": (1, 7), "pfpu": (0, 0), "sfpu": (0, 0)}
    assert {s: (S[s]["battery_fp_all"], S[s]["battery_fp_demoted"]) for s in S} == {"sdahu": (49, 33), "pfpu": (96, 96), "sfpu": (96, 95)}
    assert {s: (S[s]["strata_detected"], S[s]["strata_fp_minus_rate"]) for s in S} == {"sdahu": (13, 1), "pfpu": (26, 8), "sfpu": (25, 9)}
    assert S["sdahu"]["noisiest_rule"] == "FC4" and S["pfpu"]["noisiest_rule"] == "FC6"
    assert S["pfpu"]["site_arm"]["FC6_holdout_fp"] == 94 and S["sfpu"]["site_arm"]["FC6_holdout_fp"] == 95
    p = a["predictions"]
    assert p["P3_strata_ge_battery_and_lower_fp"] == {"G1": True, "G2": False, "G3": False, "S": False}
    assert p["P1_sdahu_battery_fp_gt_30pct_and_gated_lt_13"] and p["P4_battery_only_le_2"]
    assert not p["P5_G2_sdahu_ge_1_and_strata_ge"] and not p["P6_G3_le_3_silent_rules_and_subset"] and not p["P7_site_arm_FC6_lt_10_union_gt_30pct"]
    assert [f.split(":")[0] for f in a["falsifiers_fired"]] == ["F-X38.a (G2)", "F-X38.a (G3)", "F-X38.a (S)"]
    assert a["predictions_failed_without_falsifier"] == ["P5", "P6", "P7"]


@pytest.mark.parametrize("system", ("sdahu", "pfpu", "sfpu"))
def test_x38_amendment_repairs_in_artifact(system):
    p = ROOT / "outputs" / f"openfdd_baseline_{system}.json"
    if not p.exists():
        pytest.skip("artifact absent")
    a = json.loads(p.read_text())
    assert a["amendment"] == 1 and a["params_overridden"] == {}
    if system == "sdahu":
        assert a["ahu_role_map"]["fan-cmd"] == "SF_CS" and a["clean_year"]["rule_status"]["FC6"].startswith("not_applicable") and a["strata_sdahu_e5_adjudicated"]
    else:
        assert "fan-status" not in a["tu_role_map_zone_S"] and a["clean_year"]["tu_rule_status_zone_S"]["VAV-AHU-LEAVE"].startswith("not_applicable")
