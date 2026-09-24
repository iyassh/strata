"""Guard: X22 — positive control for the conformance channel. Injected order
violations into healthy holdout traces, scored with the deployed net,
threshold and gate. Reversal is significant on the FCU only (55/72 flagged);
on SDAHU and DDAHU it cuts fitness sharply (AUC 0.91, 0.96) but the healthy
holdout's worst days fit worse than a reversed day, so the hit rate at zero
false alarms is 0.00; on PFPU and SFPU fitness does not move (AUC 0.49/0.50).
Skips of 2-4 events are significant on SDAHU. No falsifier fired; P1, P2, P3
failed as predictions."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x22_positive_control.json"


def test_x22_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text()); s = a["systems"]
    assert a["falsifiers_fired"] == []
    assert s["fcu"]["arms"]["reverse"]["significant"] and s["fcu"]["arms"]["reverse"]["flagged_days"] == 55
    for sys_ in ("sdahu", "ddahu", "pfpu", "sfpu"):
        assert not s[sys_]["arms"]["reverse"]["significant"]
    assert s["sdahu"]["arms"]["reverse"]["auc_perturbed_below_healthy"] > 0.9 and s["sdahu"]["arms"]["reverse"]["oracle_tpr_at_zero_fp"] == 0.0
    assert s["ddahu"]["arms"]["reverse"]["auc_perturbed_below_healthy"] > 0.95 and s["ddahu"]["arms"]["reverse"]["oracle_tpr_at_zero_fp"] == 0.0
    assert abs(s["pfpu"]["arms"]["reverse"]["auc_perturbed_below_healthy"] - 0.5) < 0.05 and abs(s["sfpu"]["arms"]["reverse"]["auc_perturbed_below_healthy"] - 0.5) < 0.05
    assert s["sdahu"]["arms"]["skip_2"]["significant"] and s["sdahu"]["arms"]["skip_4"]["significant"]
    p = a["predictions"]
    assert p["P1_pass"] is False and p["P2_pass"] is False and p["P3_pass"] is False and p["P5_pass"] is True
