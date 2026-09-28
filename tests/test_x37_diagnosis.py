"""Guard: X37 diagnosis layer (signed patterns, redundant-pair consensus, leave-one-out family vote) —
both pre-registered falsifiers fired on run 3 (the design as written): family accuracy 74.6 % with
27.8 % unresolved (bar 80 % / 15 %); component wrong-subsystem rate 10.1 % (bar < 10 %). The
consensus rule resolved the five dual-duct damper cases X34 scored wrong. Pins the artefact."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x37_diagnosis.json"


def test_x37_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["run"] == 3 and "run1_defect" in a and "run2_defect" in a
    f, c = a["family"], a["component"]
    assert (f["resolved"], f["unresolved"], f["correct"]) == (114, 44, 85)
    assert f["accuracy_resolved"] == 0.746 and f["unresolved_rate"] == 0.278
    assert (c["exact"], c["subsystem"], c["wrong"], c["unnamed"]) == (112, 23, 16, 7)
    assert c["exact_rate"] == 0.709 and c["wrong_rate"] == 0.101
    p = a["predictions"]
    assert not p["P1_family_ge_80pct"] and not p["P2_component_exact_ge_78pct_and_wrong_lt_10pct"]
    assert p["P3_ddahu_damper_single_copy"] and p["P3_ddahu_bias_consensus"] == 14 and p["P3_ddahu_bias_n"] == 16
    assert p["P4_fcu_unresolved_component"] == {"exact": 29, "wrong": 14}
    assert a["falsifiers_fired"] == ["F-X37.a: family accuracy below 80 % or unresolved above 15 %", "F-X37.b: wrong-subsystem rate not below 10 %"]
    rows = a["rows"]
    assert len(rows) == 158
    dd_wrong = [r for r in rows if r["system"] == "ddahu" and r["component_verdict_x37"] == "wrong"]
    assert dd_wrong == []
    sfpu = [r for r in rows if r["system"] == "sfpu"]
    assert sum(1 for r in sfpu if str(r["consensus_reason"]).startswith("no consensus")) == 14
    assert all(r["component_verdict_x37"] == r["x34_verdict"] for r in sfpu)
