"""Integration tests for the temporal-split detector (need Parquet data)."""

from pathlib import Path

import pandas as pd
import pytest

from processheal.core.detection import build_detector, classify_days
from processheal.hvac.events import abstract_events, emitted_event_names
from processheal.io.config import load_config

DATA = Path("data/processed/sdahu")

pytestmark = pytest.mark.skipif(
    not (DATA / "AHU_annual.parquet").exists(),
    reason="LBNL Parquet data not present (run scripts/00_convert_to_parquet.py)",
)

CFG = load_config("configs/lbnl_sdahu")


@pytest.mark.integration
def test_detector_calibrates_out_of_sample_with_low_fpr():
    healthy_log = abstract_events(pd.read_parquet(DATA / "AHU_annual.parquet"), CFG)
    det = build_detector(CFG, healthy_log)
    # every event-bearing day lands in exactly one side of the split
    # (days with zero events — e.g. Sundays with the system off — have no trace)
    assert det.n_train_days + len(det.holdout_per_day) == healthy_log["case_id"].nunique()
    assert det.holdout_fpr <= 0.05


@pytest.mark.integration
def test_unified_rule_flags_stuck_damper_days():
    healthy_log = abstract_events(pd.read_parquet(DATA / "AHU_annual.parquet"), CFG)
    det = build_detector(CFG, healthy_log)
    log = abstract_events(pd.read_parquet(DATA / "damper_stuck_075_annual.parquet"), CFG)

    signature = emitted_event_names(CFG, kinds=("mismatch", "leak"))
    per_day = classify_days(det, log)
    sig_days = set(log.loc[log["activity"].isin(signature), "case_id"])
    flagged = per_day["flagged"] | per_day["case_id"].isin(sig_days)
    assert flagged.mean() >= 0.95
