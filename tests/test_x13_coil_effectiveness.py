"""Guard: X13 (coil-effectiveness residual, fault-informed design disclosed)
— the falsifier fired: one of the fouling scenarios is significant, not the
six predicted; nothing newly detected; the false-alarm budget held."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x13_coil_effectiveness.json"


def test_x13_falsifier_fired_and_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert "fault-informed" in a["design_disclosure"]
    p = a["predictions"]
    assert p["P1_fouling_sig_ge_6"] is False
    assert p["P1_fouling_sig"] == ["SFPU_ReheatCoilFouling_Waterside_Severe"]
    assert p["newly_detected_scenarios"] == []
    assert p["P2_own_fp_le_3"] is True and p["P3_joint_fp_le_8_of_96"] is True
    assert a["falsifiers_fired"] == ["F-X13.b: fewer than 4 of 9 fouling scenarios significant"]
