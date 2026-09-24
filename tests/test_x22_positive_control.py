"""Guard: X22 — positive control for the conformance channel. Injected order
violations into healthy holdout traces, scored with the deployed (post-X25)
net, threshold and gate. Reversal is significant on FCU (55/72) and DDAHU
(59/83); on SDAHU it cuts fitness (AUC 0.91) but the healthy holdout's worst
days fit worse than a reversed day (hit rate at zero FP 0.00); on PFPU and
SFPU fitness does not move (AUC 0.49/0.50). The pre-X25 run is kept as
x22_positive_control_prex25.json. No falsifier fired; P1-P4 failed."""
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
    assert s["ddahu"]["arms"]["reverse"]["significant"] and s["ddahu"]["arms"]["reverse"]["flagged_days"] == 59
    for sys_ in ("sdahu", "pfpu", "sfpu"):
        assert not s[sys_]["arms"]["reverse"]["significant"]
    assert s["sdahu"]["arms"]["reverse"]["auc_perturbed_below_healthy"] > 0.9 and s["sdahu"]["arms"]["reverse"]["oracle_tpr_at_zero_fp"] == 0.0
    assert s["ddahu"]["arms"]["reverse"]["oracle_tpr_at_zero_fp"] > 0.7 and s["ddahu"]["threshold_out_of_sample"] is True
    assert s["ddahu"]["arms"]["swap_8"]["significant"] and s["fcu"]["arms"]["swap_8"]["significant"]
    pre = json.loads((ART.parent / "x22_positive_control_prex25.json").read_text())
    assert not pre["systems"]["ddahu"]["arms"]["reverse"]["significant"] and pre["systems"]["sdahu"]["arms"]["skip_4"]["significant"]
    assert abs(s["pfpu"]["arms"]["reverse"]["auc_perturbed_below_healthy"] - 0.5) < 0.05 and abs(s["sfpu"]["arms"]["reverse"]["auc_perturbed_below_healthy"] - 0.5) < 0.05
    p = a["predictions"]
    assert p["P1_pass"] is False and p["P2_pass"] is False and p["P3_pass"] is False and p["P4_pass"] is False and p["P5_pass"] is True
