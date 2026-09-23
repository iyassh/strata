"""Guard: X12 (time perspective of the discovered state model) — pins the
pre-registered outcome. P1, P2, P4 held; P3 (a scenario no deployed channel
detects) did not; no falsifier fired; the channel costs five holdout
false-alarm days on each fan-powered system."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x12_time_perspective.json"


def test_x12_outcome_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["n_scored"] == 73
    p = a["predictions"]
    assert p["P1_sig_ge_5"] is True and p["P1_count"] == 11
    assert p["P2_no_fouling_sig"] is True and p["P2_fouling_sig"] == []
    assert p["P3_reduces_misses"] is False and p["P3_newly_detected"] == []
    assert p["P4_unique_vs_frequency_ge_3"] is True
    assert a["falsifiers_fired"] == []
    j = {s: v["joint_fpr"] for s, v in a["systems"].items()}
    assert (j["sdahu"]["deployed_union_minus_rate_fp_days"], j["sdahu"]["with_time_channel_fp_days"]) == (1, 1)
    assert (j["pfpu"]["deployed_union_minus_rate_fp_days"], j["pfpu"]["with_time_channel_fp_days"]) == (5, 10)
    assert (j["sfpu"]["deployed_union_minus_rate_fp_days"], j["sfpu"]["with_time_channel_fp_days"]) == (4, 9)
    sig = [r for v in a["systems"].values() for r in v["scenarios"] if r["significant"]]
    # never earlier than the deployed detector
    assert all(r["ttd_time_days"] >= r["ttd_deployed_days"] for r in sig)
    big = {r["file"]: r["unique_days_vs_deployed"] for r in sig}
    assert big["SFPU_RMTEMPUnstable"] == 120 and big["coi_bias_-4_annual"] == 82
