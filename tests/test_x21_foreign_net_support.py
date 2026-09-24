"""Guard: X21 — a net's reading of a FOREIGN building's year. Fan-powered nets
synchronise heating exactly at the foreign log's count (PFPU/SFPU nets on
every log); the DDAHU net on a fraction; the FCU net on none. F-X21.a fired
(6 of 12 pairs differ by > 0.05). The foreign predictor orders the buildings
differently from the raw count and predicts MR1 firings worse (rho -0.6,
p 0.21 vs the count's -1, 1/24)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "outputs" / "x21_foreign_net_support.json"


def test_x21_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["P1_bound"] is True
    assert a["P2_within_tolerance"]["pass"] is False and len(a["P2_within_tolerance"]["violations"]) == 6
    pr = a["pairs"]
    for k in ("pfpu->sfpu", "pfpu->fcu", "sfpu->pfpu", "sfpu->ddahu", "sfpu->fcu"):
        assert pr[k]["sync_days"] == pr[k]["raw_days_with_anchor"], k
    assert pr["pfpu->ddahu"]["sync_days"] == 204 and pr["pfpu->ddahu"]["raw_days_with_anchor"] == 208
    assert all(pr[f"fcu->{b}"]["sync_days"] == 0 for b in ("pfpu", "sfpu", "ddahu"))
    assert (pr["ddahu->pfpu"]["sync_days"], pr["ddahu->sfpu"]["sync_days"], pr["ddahu->fcu"]["sync_days"]) == (24, 147, 55)
    p3 = a["P3_ordering"]
    assert p3["same_ordering_as_raw"] is False
    assert abs(p3["rho_foreign_vs_mr1"] + 0.6) < 1e-9 and abs(p3["exact_one_sided_p_foreign"] - 5 / 24) < 1e-9
    assert abs(p3["rho_control_vs_mr1"] + 1.0) < 1e-9
    assert [f.split(":")[0] for f in a["falsifiers_fired"]] == ["F-X21.a"]
    assert "heating_inactive" not in a["nets"]["fcu"]["labels"] and "heating_inactive" not in a["nets"]["pfpu"]["labels"]
