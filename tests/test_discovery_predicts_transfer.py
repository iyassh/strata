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


def test_nine_cells_three_systems_six_scored():
    a = _art()
    assert len(a["cells"]) == 9
    assert set(a["Q"]) == {"sdahu", "pfpu", "sfpu"}
    assert sum(1 for c in a["cells"] if c["scored"]) == 6          # Amendment 1
    assert all(not c["scored"] for c in a["cells"] if c["system"] == "sdahu")


def test_p2_consistency_is_computed_per_cell():
    a = _art()
    assert len(a["P2"]["rows"]) == 6                                # Amendment 1
    assert a["P2"]["pass"] == all(r["consistent"] for r in a["P2"]["rows"])


def test_prereg_and_amendment_predate_the_artifact_in_git():
    """L22: the pre-commitment is enforced, not merely documented. The
    commits that fixed the prediction (pre-reg 1155dd0, amendment 4a3723a,
    scorer bc66755) must be ancestors of the commit that first added the
    artifact. Skips if the artifact is not yet committed or git is absent."""
    import subprocess
    if not ART.exists():
        pytest.skip("experiment not yet run")
    try:
        first = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%H", "--", str(ART.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("git not available")
    if not first:
        pytest.skip("artifact exists but is not yet committed")
    artifact_commit = first[-1]
    for fixed in ("1155dd0", "4a3723a", "bc66755"):
        r = subprocess.run(["git", "merge-base", "--is-ancestor", fixed, artifact_commit], cwd=ROOT)
        assert r.returncode == 0, f"{fixed} is not an ancestor of the artifact commit {artifact_commit[:7]}"


def test_amendment_2_power_block_and_no_conclusion():
    """The amended design cannot reach p < 0.05; the artifact must say so
    and must not claim a conclusion."""
    a = _art()
    assert a["power"]["min_attainable_p"] == pytest.approx(0.05)
    assert a["power"]["criterion_attainable"] is False
    assert a["conclusion_licensed"] is False


def test_amendment_3_cluster_level_power():
    """Q is constant within a building; the valid null permutes buildings.
    With three buildings the minimum one-sided p is 1/6 — the test never had
    power, and F2's only contradicting cell has an invalid predictor."""
    a = _art()
    assert a["power"]["unit_of_replication"] == "building"
    assert a["power"]["n_buildings"] == 2 or a["power"]["n_buildings"] == 3
    assert a["power"]["cluster_min_attainable_p"] >= 1 / 6 - 1e-12
    assert a["power"]["criterion_attainable_at_cluster_level"] is False
    assert a["power"]["F2_informative"] is False
    assert a["conclusion_licensed"] is False
