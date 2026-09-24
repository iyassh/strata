"""Guard: X17 — the dual-duct AHU onboarded config-only. Gates clean, healthy
silence in one iteration, 45 of 55 detected, deployed false alarms 3 of 96,
no scenario detected by the conformance channels alone; P6 (fouling <= 4)
was the one prediction that failed, in the good direction; no falsifier."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "outputs" / "x17_onboarding.json"


def test_x17_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    p = a["predictions"]
    assert a["falsifiers_fired"] == []
    assert p["P1_config_only"] and p["P2_gates"] and p["P4_fp_le_10_of_96"] and p["P5_ge_60pct"] and p["P7_null_generalises"] and p["P8_holds"]
    assert p["P6_le_4_of_12"] is False and p["P6_fouling_detected"] == 5
    assert (p["P5_detected"], p["P5_n_scored"]) == (45, 55) and p["P4_holdout_fp_days"] == 3
    assert p["P7_conformance_only_scenarios"] == []
    assert a["effort"]["src_diff_since_prereg"] == "none"
    assert a["gates"]["duplicates"] == [] and a["gates"]["rotation"] == [] and a["gates"]["ttl_columns_not_declared"] == []
    s = a["scorecard"]
    assert s["by_family"] == {"unstable_control": [2, 2], "zone_damper_stuck": [10, 10], "oa_damper_stuck": [5, 5],
                              "coil_fouling": [5, 12], "sat_sensor_bias": [8, 8], "static_sensor_bias": [5, 8], "valve_stuck": [10, 10]}
    assert s["channels"]["model"] == 0 and s["per_channel_fp"]["absence"] == 3
    u = json.loads((ROOT / "outputs" / "union_fpr_ddahu.json").read_text())
    assert u["union_minus_rate"]["holdout_fp_days"] == 3 and u["union_all8"]["holdout_fp_days"] == 8
    assert len(u["rate_demotion"]["violations"]) == 1      # the TTD cost, recorded not hidden
