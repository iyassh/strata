"""Guard: the log-level diagnosis behind X12 — 8 of the 12 scenarios the
deployed detector misses have a state log indistinguishable from healthy at
5 % (all reheat-coil fouling); the four others change a count by >= 7 %."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x12_log_diagnosis.json"
IDENTICAL = {"PFPU_ReheatCoilFouling_Airside_Minor", "PFPU_ReheatCoilFouling_Waterside_Minor",
             "PFPU_ReheatCoilFouling_Waterside_Moderate", "PFPU_ReheatCoilFouling_Waterside_Severe",
             "SFPU_ReheatCoilFouling_Airside_Minor", "SFPU_ReheatCoilFouling_Airside_Moderate",
             "SFPU_ReheatCoilFouling_Waterside_Minor", "SFPU_ReheatCoilFouling_Waterside_Moderate"}


def test_diagnosis_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    s = a["summary"]
    assert s["n_scored"] == 73 and s["n_missed"] == 12
    assert set(s["missed_with_indistinguishable_log"]) == IDENTICAL
    assert all("ReheatCoilFouling" in f for f in s["missed_with_indistinguishable_log"])
    rows = [r for v in a["systems"].values() for r in v["scenarios"] if not r["deployed_detected"]]
    others = [r for r in rows if r["file"] not in IDENTICAL]
    assert len(others) == 4 and all(r["max_count_change"] >= 0.07 for r in others)
