"""tests/test_openfdd_baseline.py — the open-fdd artifacts are VOID.

The first execution of the Guideline 36 comparison failed its own audit
(docs/plans/NEXT-openfdd-baseline-repair.md). Until the repair lands and is
re-audited, the only property worth guarding is that the artifacts SAY so
in-file, so no reader of the public repo takes them for results. The
adapter tests that once lived here pinned refuted behaviour and were cut.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("system", ("sdahu", "pfpu", "sfpu"))
def test_void_artifacts_declare_themselves_void(system):
    p = ROOT / "outputs" / f"openfdd_baseline_{system}.json"
    if not p.exists():
        pytest.skip("artifact absent")
    s = json.loads(p.read_text())["status"]
    assert s["verdict"] == "VOID"
    assert s["do_not_quote"] is True
    assert (ROOT / s["repair_plan"]).exists(), "repair plan must exist while artifacts are void"
