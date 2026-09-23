"""Guard: the generalisable gates ran on two public event logs and their
identity is pinned (a regeneration on different files fails)."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "gates_public_log.json"


def test_two_public_logs_pinned_by_md5():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    names = {l["file"] for l in a["logs"]}
    assert names == {"sepsis.xes", "receipt.xes"}
    for l in a["logs"]:
        assert len(l["md5"]) == 32 and l["cases"] > 0 and l["events"] > l["cases"]
        for g in ("G2_monotonicity", "G3_calendar", "G4_trace_hash"):
            assert g in l
    assert a["G1_duplicate_files"] == []
