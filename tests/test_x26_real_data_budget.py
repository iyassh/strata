"""Guard: X26 — the false-alarm budget on a real building (LBNL field RTU,
Site 2, 182 measured clean days): deployed union 3 of 49 holdout days (6.1 %),
every channel inside budget, no abstention (P3 failed as a prediction). The
40 % undercharge on circuit B is a CASE REPORT: with circuit-1 residuals only
(run 1) and with both circuits (Amendment 1, run 2) it flags 1 residual day
of 30; the recorded circuit-2 pressures and temperatures sit within a few
per cent of the healthy June. No falsifier fired."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x26_real_data_budget.json"


def test_x26_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["falsifiers_fired"] == []
    r2 = a["run2_amendment1_both_circuits"]
    assert (r2["deployed_fp"], r2["holdout_days"], r2["naive_fp"]) == (3, 49, 4)
    assert r2["per_channel_fp"] == {"rules": 0, "resid": 1, "model": 0, "device": 0, "absence": 0, "freq": 2, "rate": 1, "osc": 1}
    assert "out-of-sample" in r2["model_fp_provenance"]
    assert r2["case_undercharge"]["meaningful_channels"] is None and r2["case_undercharge"]["residual_days"] == 1
    p = a["predictions"]
    assert p["P2_budget_le_10pct"] and p["A1_P1_budget_holds_with_circuit2"]
    assert p["P3_some_residual_abstains_ge_20pct"] is False and p["A1_P2_case_ge_50pct_days_flagged_run2"] is False
    assert "case report" in a["claim"]
