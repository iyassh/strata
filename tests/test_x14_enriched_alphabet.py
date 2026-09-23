"""Guard: X14 (enriched state alphabet, Amendments 1-2) — P1 held on exactly
one missed scenario, P3 held (SDAHU model channel 14 vs 5), P2 failed and
F-X14.a fired: the enriched channels exceed the false-alarm budget."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x14_enriched_alphabet.json"


def test_x14_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    p = a["predictions"]
    assert a["n_scored"] == 73 and p["n_missed"] == 12
    assert p["P1_newly_detected"] == ["PFPU_SensorBias_RMTEMP_+2C"]
    assert p["P2_fp_within_budget"] is False
    assert p["P3_model_sig_ge_deployed"] is True and (p["model_sig_enriched"], p["model_sig_deployed"]) == (14, 5)
    assert a["falsifiers_fired"] == ["F-X14.a: enriched state channels exceed the false-alarm budget"]
    s = a["systems"]
    assert s["sdahu"]["alignment_channels_evaluated"] is True
    assert s["pfpu"]["alignment_channels_evaluated"] is False and s["sfpu"]["alignment_channels_evaluated"] is False
    assert (s["sdahu"]["state_channels_holdout_fp_days"], s["pfpu"]["state_channels_holdout_fp_days"],
            s["sfpu"]["state_channels_holdout_fp_days"]) == (7, 14, 18)
    # the amendment: alignment channels are null, not False, where not evaluated
    r = next(x for x in s["pfpu"]["scenarios"] if x["file"] == "PFPU_SensorBias_RMTEMP_+2C")
    assert r["enriched_sig"]["model"] is None and r["enriched_sig"]["time"] is True
    assert "fit_seconds" not in json.dumps(a).replace("fit_seconds_stdout_only_note", "")
