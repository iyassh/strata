"""Guard: the alarm-attribution counts, and their internal consistency."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "outputs" / "alarm_attribution.json"


def _a():
    if not ART.exists():
        pytest.skip("artifact absent")
    return json.loads(ART.read_text())


def test_counts_sum_to_detected_and_are_pinned():
    a = _a(); c = a["counts"]
    # X25 step 4 (2026-09-24): the per-day residual null removed four fan-powered detections
    # (three of them attributed 'none', one with indeterminate ground truth); was 61 / 36-10-0-14-1
    # X33b (2026-09-25): PFPU 22 -> 26 detections; the four gains are residual-only and name no device (none 7 -> 10), one has
    # indeterminate zone ground truth; was 57 / 36-7-0-14-0 after X25
    assert sum(c.values()) == a["n_detected"] == 61
    assert c == {"correct": 36, "none": 10, "wrong": 0, "no_device_stratum": 14, "indeterminate_gt": 1}


def test_no_wrong_attribution_and_sdahu_names_no_device():
    a = _a()
    assert all(r["attribution"] != "wrong" for r in a["rows"])
    assert all(r["alarm_device"] is None for r in a["rows"] if r["system"] == "sdahu")


def test_rows_recompute_from_scorecards():
    """Not just internal arithmetic: recount from benchmark_v6_*.json."""
    a = _a(); n = 0
    for s in ("sdahu", "pfpu", "sfpu"):
        d = json.loads((ROOT / "outputs" / f"benchmark_v6_{s}.json").read_text())
        n += sum(1 for x in d["scenarios"] if not x.get("excluded") and x.get("ttd_days") is not None)
    assert n == a["n_detected"]
