"""Guard: X15 (enriched alphabet, frequency channel only, two holdout splits)
— all four predictions held, no falsifier fired: the one X14 gain survives
inside the budget under the mirrored split. A candidate deployable addition,
not an adopted one."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x15_enriched_frequency.json"
TARGET = "SFPU_ReheatCoilFouling_Airside_Moderate"


def test_x15_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    p = a["predictions"]
    assert p["P1_budget_both_splits"] and p["P2_target_sig_both_splits"] and p["P3_no_other_new"] and p["P4_enriched_ge_deployed_on_detected"]
    assert p["newly_significant_both_splits"] == [TARGET]
    assert (p["enriched_sig_on_detected"], p["deployed_frequency_sig_on_detected"]) == (41, 12)
    assert a["falsifiers_fired"] == []
    fp = {(s, sp): a["systems"][s][sp]["holdout_fp_days"] for s in a["systems"] for sp in ("last8", "first8")}
    assert fp == {("sdahu", "last8"): 2, ("sdahu", "first8"): 0, ("pfpu", "last8"): 4, ("pfpu", "first8"): 8,
                  ("sfpu", "last8"): 3, ("sfpu", "first8"): 5}
    for sp in ("last8", "first8"):
        r = next(x for x in a["systems"]["sfpu"][sp]["scenarios"] if x["file"] == TARGET)
        assert r["significant"] and r["flag_days"] >= 364 and not r["deployed_detected"]
