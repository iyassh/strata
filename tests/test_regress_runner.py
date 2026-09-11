"""tests/test_regress_runner.py — regress.py diff-verdict logic."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from regress import artifact_verdict  # noqa: E402


def test_identical_verdict(tmp_path):
    a = tmp_path / "a.json"; b = tmp_path / "b.json"
    a.write_text(json.dumps({"x": 1})); b.write_text(json.dumps({"x": 1}))
    assert artifact_verdict(a, b) == "IDENTICAL"


def test_changed_verdict_names_paths(tmp_path):
    a = tmp_path / "a.json"; b = tmp_path / "b.json"
    a.write_text(json.dumps({"x": 1, "y": {"z": 2}}))
    b.write_text(json.dumps({"x": 1, "y": {"z": 3}}))
    v = artifact_verdict(a, b)
    assert v.startswith("CHANGED") and "y.z" in v
