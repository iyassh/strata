"""Guard: X29 — refrigerant-side observability on the simulated RTU. With the
condenser/discharge/suction pressures and temperatures recorded, all five
condenser-fouling and all five evaporator-fouling severities (10-50 %) are
detected, monotone in severity, plus 8/8 line restrictions and the 20 %
charge faults: 20 of 24 at 1 false-alarm day in 29 (3.4 %). No falsifier."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x29_refrigerant_observability.json"


def test_x29_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["falsifiers_fired"] == [] and all(v for k, v in a["predictions"].items() if isinstance(v, bool))
    assert (a["detected"], a["scored"]) == (20, 24) and a["deployed_fp"] == [1, 29]
    assert a["family_counts"] == {"condenser_fouling": [5, 5], "evaporator_fouling": [5, 5], "liquid_line_restriction": [4, 4],
                                  "suction_line_restriction": [4, 4], "refrigerant_overcharge": [1, 3], "refrigerant_undercharge": [1, 3]}
    assert a["channel_credits"]["resid"] == 20 and a["channel_credits"]["model"] == 0 and a["channel_credits"]["device"] == 0
