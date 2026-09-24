"""Guard (X19 Amendment 1): the scorecard's model-channel false-alarm baseline
must be the same count the deployed false-alarm artefact reports. On the FCU
run 1 they disagreed (1 of 72 event days vs 25 of 96 holdout days) because
the scorecard's gate ignored the silent-while-scheduled days that the
deployed count included; six "detections" followed from that gap."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "outputs"
SYSTEMS = ["sdahu", "pfpu", "sfpu", "ddahu", "fcu"]


@pytest.mark.parametrize("system", SYSTEMS)
def test_model_channel_baseline_matches_deployed_count(system):
    card, ufpr = ROOT / f"benchmark_v6_{system}.json", ROOT / f"union_fpr_{system}.json"
    if not (card.exists() and ufpr.exists()):
        pytest.skip("artefacts absent")
    c, u = json.loads(card.read_text()), json.loads(ufpr.read_text())
    assert c["model_holdout_fp"] == u["channels"]["model"]["holdout_fp_days"], (
        f"{system}: scorecard gate baseline {c['model_holdout_fp']} != deployed model FP "
        f"{u['channels']['model']['holdout_fp_days']}")
