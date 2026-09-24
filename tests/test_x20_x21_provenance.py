"""L22 discipline for X20 and X21: the pre-registration commit must be an
ancestor of the commit that first added each artefact."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = {"outputs/x20_transfer_four.json": "fd95da3", "outputs/x21_foreign_net_support.json": "7f75efc"}


@pytest.mark.parametrize("artefact,prereg", CASES.items())
def test_prereg_predates_artefact(artefact, prereg):
    if not (ROOT / artefact).exists():
        pytest.skip("artefact absent")
    try:
        first = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", artefact],
                               cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        if not first:
            pytest.skip("artefact not yet committed")
        rc = subprocess.run(["git", "merge-base", "--is-ancestor", prereg, first[-1]], cwd=ROOT).returncode
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("git unavailable")
    assert rc == 0, f"{prereg} is not an ancestor of the commit that added {artefact}"
