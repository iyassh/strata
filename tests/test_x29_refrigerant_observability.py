"""Guard: X29 — refrigerant-side observability on the simulated RTU. With the
condenser/discharge/suction pressures and temperatures recorded, all five
condenser-fouling and all five evaporator-fouling severities (10-50 %) are
detected, monotone in severity, plus 8/8 line restrictions and the 20 %
charge faults: 20 of 24 at 0 false-alarm days in 28 (Amendment 1: the one-row boundary date is
dropped at conversion; 1/29 at close). Condenser fouling is carried by cond_approach, evaporator
fouling by supply_dT (air side). No falsifier."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x29_refrigerant_observability.json"


def test_x29_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["falsifiers_fired"] == [] and all(v for k, v in a["predictions"].items() if isinstance(v, bool))
    assert (a["detected"], a["scored"]) == (20, 24) and a["deployed_fp"] == [0, 28]
    assert a["family_counts"] == {"condenser_fouling": [5, 5], "evaporator_fouling": [5, 5], "liquid_line_restriction": [4, 4],
                                  "suction_line_restriction": [4, 4], "refrigerant_overcharge": [1, 3], "refrigerant_undercharge": [1, 3]}
    assert a["channel_credits"]["resid"] == 20 and a["channel_credits"]["model"] == 0 and a["channel_credits"]["device"] == 0
    assert a["predictions"]["P3_cond_approach_flagged_on_every_condenser_file"] and a["predictions"]["amendment1_src_unchanged"]


def test_x29_residual_credits_split_by_coil():
    art = ART.with_name("x29_residual_credits.json")
    if not art.exists():
        pytest.skip("artifact absent")
    c = json.loads(art.read_text())["scenarios"]
    for k in (10, 20, 30, 40, 50):
        assert c[f"RTU_sim_condfouling{k}"]["per_rule_flagged_days"]["cond_approach"] >= 91
        assert c[f"RTU_sim_evapfouling{k}"]["per_rule_flagged_days"]["supply_dT"] == 100
    assert c["RTU_sim_evapfouling10"]["per_rule_flagged_days"]["pressure_ratio"] <= 3   # refrigerant side blind to 10 % evaporator fouling

