"""Guard: the four log-generic gates each fire on exactly the injected defect
class they were built for, and none of them sees a leaked per-case constant."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "gates_injection.json"
EXPECTED = {"none": [], "dup_file": ["G1"], "dup_case": ["G4"], "rotate": ["G2"], "calendar": ["G3"], "leak": []}


def test_each_injection_fires_only_its_gate():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    rows = {r["injection"]: r for r in a["rows"]}
    assert set(rows) == set(EXPECTED)
    for k, exp in EXPECTED.items():
        assert rows[k]["gates_fired"] == exp, (k, rows[k]["gates_fired"])
        assert rows[k]["caught"] == bool(exp)
    assert "seconds" not in json.dumps(a)          # runtime is machine-dependent: stdout only
