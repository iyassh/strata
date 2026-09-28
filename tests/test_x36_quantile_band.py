"""Guard: X36 quantile bands (p2/p98 of training-day scores) as an alternative residual calibration —
no detection gained or lost on any system, every edge recovery kept, false alarms rose 4 days on PFPU and
SFPU (bar 3) → F-X36.a fired; the deployed [min, max] calibration is unchanged. Pins the artefact."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x36_quantile_band.json"


def test_x36_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    p = a["predictions"]
    assert not p["P1_fp_rise_le_3_and_le_10"] and p["P2_edge_recoveries_kept"] and not p["P3_ge_2_new_detections"] and p["P4_no_loss"]
    assert p["P3_gained"] == [] and a["falsifiers_fired"] == ["F-X36.a: false alarms rose beyond the bar"]
    S = a["systems"]
    det = {s: (S[s]["extreme"]["detected"], S[s]["quantile"]["detected"]) for s in S}
    assert det == {"sdahu": (14, 14), "pfpu": (26, 26), "sfpu": (25, 25), "ddahu": (50, 50), "fcu": (43, 43)}
    fp = {s: (S[s]["extreme"]["holdout_fp_days"], S[s]["quantile"]["holdout_fp_days"]) for s in S}
    assert fp == {"sdahu": (1, 1), "pfpu": (6, 10), "sfpu": (4, 8), "ddahu": (0, 3), "fcu": (4, 6)}
    assert all(S[s]["gained"] == [] and S[s]["lost"] == [] and S[s]["edge_recoveries_lost"] == [] for s in S)
    assert all(0.85 <= S[s]["band_width_ratio_median"] <= 0.96 for s in S)
