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


def test_verdict_from_text_matches_path_version(tmp_path):
    from regress import verdict_from_text
    assert verdict_from_text('{"x": 1}', '{"x": 1}') == "IDENTICAL"
    v = verdict_from_text('{"y": {"z": 2}}', '{"y": {"z": 3}}')
    assert v.startswith("CHANGED") and "y.z" in v


def test_gate_does_not_depend_on_temp_files():
    """The baseline is held in memory. A tempfile.mkdtemp() stash was emptied
    by the OS mid-run and killed the sweep on artifact 2 of 12."""
    import regress
    src = Path(regress.__file__).read_text()
    assert "tempfile" not in src
    assert "mkdtemp" not in src


def test_verdicts_are_flushed_for_live_progress():
    """A multi-hour sweep must report per-artifact, not buffer to the end."""
    import regress
    src = Path(regress.__file__).read_text()
    assert src.count("flush=True") >= 4
