"""Guard (X31 Amendment 1): the library facade's residual null is the per-day null of
X25 step 4 — the same numbers scripts/benchmark.py and union_fpr.py report — not the
pooled channel-day count that let the facade detect five DDAHU scenarios the
scorecard does not."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


@pytest.mark.parametrize("system,healthy", [("sdahu", "AHU_annual"), ("ddahu", "DualDuct_FaultFree")])
def test_facade_residual_null_matches_scorecard(system, healthy):
    card = REPO / f"outputs/benchmark_v6_{system}.json"
    data = REPO / f"data/processed/{system}/{healthy}.parquet"
    if not card.exists() or not data.exists():
        pytest.skip("artefact or data absent")
    import strata.core.detection as detmod
    from strata.core.pipeline import fit
    from strata.io.config import load_config

    def _off(*_a, **_k):
        raise ImportError("alignment strata off for this guard")
    detmod.build_detector = _off
    det = fit(load_config(str(REPO / f"configs/lbnl_{system}")), pd.read_parquet(data))
    assert list(det.residual_holdout) == json.loads(card.read_text())["residual_holdout_fp"]
