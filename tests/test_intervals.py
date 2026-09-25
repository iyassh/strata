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
    assert f["sdahu"]["deployed"] == [1, 96, [0.2, 5.7]] and f["pfpu"]["deployed"] == [8, 96, [4.3, 15.6]] and f["sfpu"]["deployed"] == [9, 96, [5.0, 16.9]]
    assert f["sdahu"]["pca_strict"] == [1, 79, [0.2, 6.8]] and f["pfpu"]["pca_strict"] == [1, 96, [0.2, 5.7]] and f["sfpu"]["pca_strict"] == [1, 96, [0.2, 5.7]]
    d = a["detection"]
    # X33 coverage series (2026-09-25): 56 -> 64 adjudicated; was 56/73 [65.8, 84.9], discordant 7, p 0.125, baseline-only 6
    assert d["strata_adjudicated"] == [64, 73, [78.2, 93.4]] and d["pca_strict"] == [61, 73, [73.4, 90.3]] and d["strata_naive"][0] == 65
    m = a["mcnemar"]
    assert m["discordant"] == 3 and m["exact_p_two_sided"] == 0.25 and m["baseline_only"] == [] and len(m["strata_only"]) == 3 and len(m["both_miss"]) == 9
