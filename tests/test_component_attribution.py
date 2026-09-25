"""Guard: X34 component attribution — the pre-registered component-level claim was NOT met (F-X34.a fired);
the paper reports subsystem-level rates. Pins the artefact."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "component_attribution.json"


def test_x34_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    t = a["totals"]
    assert (t["detected"], t["exact"], t["subsystem"], t["wrong"], t["unnamed"]) == (158, 109, 22, 20, 7)
    assert t["exact_rate"] == 0.69 and t["exact_or_subsystem_rate"] == 0.829 and t["wrong_rate"] == 0.127
    p = a["predictions"]
    assert p["P1_exact_ge_60pct"] and not p["P2_exact_or_subsystem_ge_85pct"] and not p["P3_wrong_le_10pct"] and p["P4_bias_via_redundancy_all_exact"]
    assert a["falsifiers_fired"] == ["F-X34.a: wrong-subsystem rate above 10 %"]
    assert a["systems"]["fcu"]["wrong"] == 14 and a["systems"]["ddahu"]["wrong"] == 5
