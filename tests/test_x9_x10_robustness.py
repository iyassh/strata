"""Guard: X9 (1x/2x/4x per-sample jitter; stress arms on SDAHU only after
Amendment 2) and X10 (first-8-days holdout) — every binding prediction held,
no falsifier fired. Fan-powered arms ran without the alignment-based channels
(Amendment 3); SDAHU ran with every channel."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x9_x10_robustness.json"


def test_x9_x10_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["falsifiers_fired"] == []
    p = a["predictions"]
    for s in ("sdahu", "pfpu", "sfpu"):
        assert p[s]["P-X9.1_det_change_le_3"] and p[s]["P-X9.1_fpr_le_10pct"]
        assert p[s]["P-X10.1_det_within_3"] and p[s]["P-X10.2_fpr_le_10pct"]
        assert p[s]["det_drop_1x"] == 0
    assert p["sdahu"]["stress_arms_run"] and p["sdahu"]["P-X9.2_monotone"]
    assert not p["pfpu"]["stress_arms_run"] and not p["sfpu"]["stress_arms_run"]
    c = {s: a["systems"][s]["conditions"] for s in a["systems"]}
    assert all(c["sdahu"][k]["detected"] == 14 and c["sdahu"][k]["holdout_fp_days"] == 1
               for k in ("noise_1x", "noise_2x", "noise_4x"))
    assert (c["sdahu"]["split_first8"]["detected"], c["sdahu"]["split_first8"]["holdout_fp_days"]) == (13, 0)
    assert (c["pfpu"]["noise_1x"]["detected"], c["pfpu"]["noise_1x"]["holdout_fp_days"]) == (23, 4)
    assert (c["sfpu"]["noise_1x"]["detected"], c["sfpu"]["noise_1x"]["holdout_fp_days"]) == (24, 2)
    assert (c["pfpu"]["split_first8"]["detected"], c["pfpu"]["split_first8"]["holdout_fp_days"]) == (23, 2)
    assert (c["sfpu"]["split_first8"]["detected"], c["sfpu"]["split_first8"]["holdout_fp_days"]) == (25, 3)
    assert a["systems"]["pfpu"]["alignment_channels"] is False and a["systems"]["sfpu"]["alignment_channels"] is False
    assert any("jitter" in n for n in a["notes"])
    assert "seconds" not in json.dumps(a)
