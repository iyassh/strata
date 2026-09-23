"""Guard: the fault-versus-fault control behind X14's one new detection —
the zone-S damper low band is a dose-monotone signature of airside reheat-coil
fouling on the series unit (moderate and severe both fire on the same
statistic; minor sits at the healthy rate), not a threshold coincidence."""
import json
import re
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x14_control.json"


def test_control_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    raw = ART.read_text()
    assert not re.search(r"\b(NaN|Infinity)\b", raw)          # valid JSON, no bare non-finite tokens
    a = json.loads(raw)
    f = {r["file"]: r for r in a["files"]}
    share = [f[k]["occupied_share_at_or_below_edge"] for k in
             ("SFPU_FaultFree", "SFPU_ReheatCoilFouling_Airside_Minor",
              "SFPU_ReheatCoilFouling_Airside_Moderate", "SFPU_ReheatCoilFouling_Airside_Severe")]
    assert share == sorted(share, reverse=True) and share[0] > 0.6 and share[-1] < 0.05   # monotone ladder
    assert f["SFPU_ReheatCoilFouling_Airside_Minor"]["sustained_low_entries_per_day"] == f["SFPU_FaultFree"]["sustained_low_entries_per_day"]
    assert f["SFPU_ReheatCoilFouling_Airside_Moderate"]["sustained_low_entries_per_day"] > 8
    assert f["SFPU_ReheatCoilFouling_Airside_Severe"]["sustained_low_entries_per_day"] > 8
    assert f["SFPU_ReheatCoilFouling_Airside_Moderate"]["off_gap_median_min"] == 30.0
    assert f["SFPU_ReheatCoilFouling_Airside_Severe"]["damper_min"] == f["SFPU_FaultFree"]["damper_min"]   # the "never below 0.34" reading was wrong
    lad = a["airside_ladder"]
    assert lad["SFPU_ReheatCoilFouling_Airside_Moderate"]["log10_p_time"] < -250
    assert lad["SFPU_ReheatCoilFouling_Airside_Severe"]["enriched_sig"]["time"] is True
    assert lad["SFPU_ReheatCoilFouling_Airside_Minor"]["p_time"] > 0.5
