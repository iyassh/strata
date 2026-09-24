"""Guard: X27 — fan-law virtual static (static / speed^2) on the dual-duct unit.
Static-bias detections 5 -> 6 of 8 (cold +0.2 in.wg gained; hot -0.2/-0.4 still
missed) so F-X27.b fired (bar was 7); unpredicted gain: cooling-coil airside
moderate fouling (airflow resistance shows in static per speed^2). DDAHU
45 -> 47 of 55 at 3/96, nothing lost."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x27_fan_law_static.json"


def test_x27_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert [f.split(":")[0] for f in a["falsifiers_fired"]] == ["F-X27.b"]
    assert (a["detected_before"], a["detected_after"], a["scored"]) == (45, 47, 55)
    assert (a["static_bias_before"], a["static_bias_after"]) == (5, 6)
    assert sorted(a["gained"]) == ["DualDuct_Fouling_Cooling_Airside_Moderate", "DualDuct_SensorBias_CSP_+2inwg"] and a["lost"] == []
    assert (a["deployed_fp_before"], a["deployed_fp_after"]) == (3, 3)
    assert a["static_bias_rows"]["DualDuct_SensorBias_HSP_-2inwg"]["after"] is None
    assert a["predictions"]["P2_static_bias_ge_7_of_8"] is False and a["predictions"]["P3_no_loss"] is True
