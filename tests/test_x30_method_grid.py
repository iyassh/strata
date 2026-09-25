"""Guard: X30 — method-coverage grid. Seven process-mining instruments (inductive
0.0/0.5 + alignments, deployed net + token replay, heuristics + alignments, log
skeleton, Declare, temporal profile), discovered on the training days and
thresholded on the calibration slice, detect none of the 33 scenarios the
deployed detector misses on PFPU/SFPU/DDAHU/FCU; no cell exceeds 10 % holdout
false alarms; two heuristics-miner cells timed out (F-X30.b, not evaluated)."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x30_method_grid.json"
CELLS = ["IM00-align", "IM05-align", "IM02-token", "HM-align", "SKEL", "DECLARE", "TEMPORAL"]


def test_x30_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["cells"] == CELLS and set(a["systems"]) == {"pfpu", "sfpu", "ddahu", "fcu", "sdahu"}
    assert {s: len(v["missed_scenarios"]) for s, v in a["systems"].items()} == {"pfpu": 8, "sfpu": 8, "ddahu": 10, "fcu": 7, "sdahu": 0}
    evaluated = [(s, c, r) for s, v in a["systems"].items() for c, r in v["cells"].items() if "error" not in r]
    assert len(evaluated) == 33
    assert all(r["detected"] == [] for _, _, r in evaluated)            # P1, at each cell's pre-registered threshold
    assert all(r["holdout_fp_rate"] <= 0.10 for _, _, r in evaluated)  # P2 did not occur
    assert max(r["holdout_fp"] for _, _, r in evaluated) == 7
    assert a["predictions"]["P3_errors"] == [["sfpu", "HM-align"], ["ddahu", "HM-align"]]
    assert len(a["falsifiers_fired"]) == 1 and a["falsifiers_fired"][0].startswith("F-X30.b")
    assert a["predictions"]["predictions_failed_without_falsifier"] == ["P2: no cell exceeded 10 % holdout false alarms (worst 7/72 = 9.7 %)"]
    assert "no threshold sweep" in a["predictions"]["threshold_policy"]
