"""tests/test_openfdd_baseline.py — the 2026-09-11 open-fdd artifacts are VOID and live in outputs/void/;
the live outputs/openfdd_baseline_<system>.json are the X38 repaired run
(docs/plans/2026-09-27-x38-guideline36-repaired-prereg.md).

The first execution of the Guideline 36 comparison failed its own audit
(docs/plans/NEXT-openfdd-baseline-repair.md). The void files must keep saying so in-file, so
no reader of the public repo takes them for results; the live files must name the X38
pre-registration and the open-fdd version they ran under. X38's numbers are pinned in
tests/test_x38_guideline36.py.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("system", ("sdahu", "pfpu", "sfpu"))
def test_void_artifacts_declare_themselves_void(system):
    p = ROOT / "outputs" / "void" / f"openfdd_baseline_{system}.json"
    if not p.exists():
        pytest.skip("void artifact absent")
    s = json.loads(p.read_text())["status"]
    assert s["verdict"] == "VOID"
    assert s["do_not_quote"] is True
    assert (ROOT / s["repair_plan"]).exists(), "repair plan must exist while the void artifacts are kept"


@pytest.mark.parametrize("system", ("sdahu", "pfpu", "sfpu"))
def test_live_artifacts_are_the_x38_run(system):
    p = ROOT / "outputs" / f"openfdd_baseline_{system}.json"
    if not p.exists():
        pytest.skip("artifact absent")
    a = json.loads(p.read_text())
    assert "status" not in a, "a void artifact is sitting at the live path"
    assert a["prereg"] == "docs/plans/2026-09-27-x38-guideline36-repaired-prereg.md"
    assert a["openfdd_version"] == "4.4.1"
    assert a["params_overridden"] in ({}, [], None)
