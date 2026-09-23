"""Guard: X14 (enriched state alphabet, Amendments 1-3) — P1 held by the
letter on exactly one missed scenario (a threshold coincidence on the zone-S
damper band), P3 held (SDAHU model channel 14 of 14 vs 0 of 14 deployed; the
artefact's global 5 is the series unit's), P2 failed and F-X14.a fired: the
enriched channels exceed the false-alarm budget (7 / 18 / 21 of 96)."""
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
    assert p["P1_newly_detected"] == ["SFPU_ReheatCoilFouling_Airside_Moderate"]
    assert p["P2_fp_within_budget"] is False
    assert p["P3_model_sig_ge_deployed"] is True and (p["model_sig_enriched"], p["model_sig_deployed"]) == (14, 5)
    assert a["falsifiers_fired"] == ["F-X14.a: enriched state channels exceed the false-alarm budget"]
    s = a["systems"]
    assert (len(s["sdahu"]["added_signals"]), len(s["pfpu"]["added_signals"]), len(s["sfpu"]["added_signals"])) == (3, 20, 18)
    assert s["sdahu"]["alignment_channels_evaluated"] is True
    assert s["pfpu"]["alignment_channels_evaluated"] is False and s["sfpu"]["alignment_channels_evaluated"] is False
    assert (s["sdahu"]["state_channels_holdout_fp_days"], s["pfpu"]["state_channels_holdout_fp_days"],
            s["sfpu"]["state_channels_holdout_fp_days"]) == (7, 18, 21)
    assert s["pfpu"]["time_channel_holdout"]["fp_days"] == 15 and s["sfpu"]["time_channel_holdout"]["fp_days"] == 19
    sd = s["sdahu"]["scenarios"]
    assert sum(1 for r in sd if r["enriched_sig"]["model"]) == 14 == len(sd)
    # the amendment: alignment channels are null, not False, where not evaluated
    r = next(x for x in s["sfpu"]["scenarios"] if x["file"] == "SFPU_ReheatCoilFouling_Airside_Moderate")
    assert r["enriched_sig"]["model"] is None and r["enriched_sig"]["frequency"] is True and r["enriched_sig"]["time"] is True
    assert "fit_seconds" not in json.dumps(a).replace("fit_seconds_stdout_only_note", "")
