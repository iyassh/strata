"""Guard: ERRATA E5's schedule leg is a measurement — same occupied-day
universe on every full-year SDAHU file, one-hour phase shift on the healthy
branch (05:01/05:02 on 200 of 303 days) against 06:01 on every fault file."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "e5_schedule.json"


def test_schedule_phase_shift_is_measured():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["occupancy_signal"].startswith("SYS_CTL")
    assert a["healthy_occupied_days"] == 303
    assert a["healthy_days_starting_0501_0502"] == 200
    assert a["fault_files_all_start_0601"] is True
    days = a["fault_occupied_days"]
    assert len(days) == 20
    assert all(v == 303 for k, v in days.items() if k != "damper_stuck_100_annual_short")
    assert days["damper_stuck_100_annual_short"] == 179
