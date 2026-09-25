"""Guard: X33 coverage series ledgers (one per audited system)."""
import json
from pathlib import Path

import pytest

OUT = Path(__file__).resolve().parents[1] / "outputs"


def test_x33a_sdahu():
    art = OUT / "x33_coverage_sdahu.json"
    if not art.exists():
        pytest.skip("artifact absent")
    a = json.loads(art.read_text())
    assert a["columns_mapped"] == [12, 26] and a["columns_excluded"] == ["OA_CFM", "SA_SP", "SA_SPSPT", "SF_SPD"]
    assert (a["detected_before"], a["detected_after"], a["scored"]) == (14, 14, 14) and a["lost"] == [] and a["gained"] == []
    assert a["deployed_fp"] == [1, 1] and a["model_rows_identical"] and a["ttd_later"] == []
    assert {r: v["holdout_fp"] for r, v in a["new_rule_holdout_fp"].items()} == {"rf_specific_power": 0, "sf_flow_per_speed": 0, "sf_specific_power": 0}
    assert a["residual_days_rose_and_credited"] == ["coi_stuck_010_annual", "coi_stuck_025_annual"]
    assert all(a["predictions"].values()) and a["falsifiers_fired"] == []
