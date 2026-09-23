"""Guard for the pre-registered discovery-predicts-transfer test.

Written and committed BEFORE the sealed quantities or the six unknown
firing counts were seen. Whatever the verdict, it is pinned here so a
later regeneration cannot quietly change it.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "outputs" / "discovery_predicts_transfer.json"


def _art():
    if not ART.exists():
        pytest.skip("experiment not yet run")
    return json.loads(ART.read_text())


def test_verdict_follows_prereg_rule():
    a = _art()
    p1 = a["P1"]["pass"]
    assert p1 == (a["P1"]["rho"] < 0 and a["P1"]["perm_p"] < 0.05)
    if not p1:
        assert a["verdict"] == "F1_FIRED" and "F1" in a["falsifiers_fired"]
    elif not a["P3"]["pass"]:
        assert a["verdict"] == "P1_PASS_P3_FAIL" and "F3" in a["falsifiers_fired"]
    else:
        assert a["verdict"] == "P1_PASS"


def test_nine_cells_three_systems():
    a = _art()
    assert len(a["cells"]) == 9
    assert set(a["Q"]) == {"sdahu", "pfpu", "sfpu"}


def test_p2_consistency_is_computed_per_cell():
    a = _art()
    assert len(a["P2"]["rows"]) == 9
    assert a["P2"]["pass"] == all(r["consistent"] for r in a["P2"]["rows"])
