"""Guard: the confidence intervals and the paired test quoted in the manuscript regenerate from
the committed artefacts (scripts/intervals.py -> outputs/intervals.json)."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "intervals.json"


def test_intervals_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    f = a["false_alarm_rates"]
    assert f["sdahu"]["deployed"] == [1, 96, [0.2, 5.7]] and f["pfpu"]["deployed"] == [7, 96, [3.6, 14.3]] and f["sfpu"]["deployed"] == [6, 96, [2.9, 13.0]]
    assert f["sdahu"]["pca_strict"] == [1, 79, [0.2, 6.8]] and f["pfpu"]["pca_strict"] == [1, 96, [0.2, 5.7]] and f["sfpu"]["pca_strict"] == [1, 96, [0.2, 5.7]]
    d = a["detection"]
    assert d["strata_adjudicated"] == [56, 73, [65.8, 84.9]] and d["pca_strict"] == [61, 73, [73.4, 90.3]] and d["strata_naive"][0] == 57
    m = a["mcnemar"]
    assert m["discordant"] == 7 and m["exact_p_two_sided"] == 0.125 and m["strata_only"] == ["PFPU_VAVDMPRUnstable"] and len(m["baseline_only"]) == 6 and len(m["both_miss"]) == 11
