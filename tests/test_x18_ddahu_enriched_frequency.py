"""Guard: X18 — X15's enriched-frequency protocol on the fourth system. Inside
the budget under both splits (P1), triples coverage on detected scenarios
(P4), but no missed scenario becomes significant: F-X18.b fired — the X15
gain does not replicate on the dual-duct AHU."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x18_ddahu_enriched_frequency.json"


def test_x18_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    p = a["predictions"]
    assert p["P1_budget_both_splits"] and p["P3_no_static_bias_new"] and p["P4_enriched_ge_deployed_on_detected"]
    assert p["P2_fouling_newly_both_splits"] is False and p["newly_significant_both_splits"] == []
    assert (p["enriched_sig_on_detected"], p["deployed_frequency_sig_on_detected"]) == (22, 8)
    assert a["falsifiers_fired"] == ["F-X18.b: no missed fouling scenario significant under both splits — the X15 gain does not replicate"]
    for sp in ("last8", "first8"):
        assert a[sp]["holdout_fp_days"] == 2 and a[sp]["n_added_signals"] == 17
        assert not any(r["significant"] for r in a[sp]["scenarios"] if not r["deployed_detected"])
