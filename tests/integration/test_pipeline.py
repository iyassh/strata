"""Integration tests on the real SDAHU data. Marked 'integration' (need Parquet)."""

from pathlib import Path

import pandas as pd
import pytest

from processheal.core.conformance import check_conformance
from processheal.core.discovery import discover_model
from processheal.hvac.events import abstract_events
from processheal.io.config import load_config

DATA = Path("data/processed/sdahu")

pytestmark = pytest.mark.skipif(
    not (DATA / "AHU_annual.parquet").exists(),
    reason="LBNL Parquet data not present (run scripts/00_convert_to_parquet.py)",
)

CFG = load_config("configs/lbnl_sdahu")


@pytest.mark.integration
def test_discovers_sound_net_from_healthy_data():
    df = pd.read_parquet(DATA / "AHU_annual.parquet")
    net, im, fm = discover_model(abstract_events(df, CFG))
    assert len(net.transitions) >= 1
    assert im is not None and fm is not None


@pytest.mark.integration
def test_faulty_file_has_lower_fitness_and_localised_deviation():
    healthy_log = abstract_events(pd.read_parquet(DATA / "AHU_annual.parquet"), CFG)
    net, im, fm = discover_model(healthy_log)

    healthy = check_conformance(healthy_log, net, im, fm)
    faulty = check_conformance(
        abstract_events(pd.read_parquet(DATA / "damper_stuck_075_annual.parquet"), CFG),
        net, im, fm,
    )

    assert faulty["average_trace_fitness"] < healthy["average_trace_fitness"]
    assert "damper_command_mismatch" in faulty["unexpected_by_activity"]
    # per-day output covers every day of the year
    assert len(faulty["per_day"]) == 365
