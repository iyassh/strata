"""Guard: X20 — the transfer test with four scorable buildings. Pre-registered
identity (Q_support = the log's own heating-day count) holds on DDAHU exactly
and fails on FCU (74 sync days vs 118 raw), so F-X20.a fired and P2 was scored:
rho = -1, exact one-sided p = 1/24. The pre-registered control — the raw
heating-day fraction, no discovery in it — orders the four buildings
identically and passes identically. F-X20.b fired: the obligatory form is
not 'every occupied day has heating' on any building."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "outputs" / "x20_transfer_four.json"


def test_x20_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    rows = {r["building"]: r for r in a["buildings"]}
    assert [r["building"] for r in a["buildings"]] == ["pfpu", "sfpu", "ddahu", "fcu"]
    assert (rows["ddahu"]["sync_days"], rows["ddahu"]["raw_days_with_anchor"], rows["ddahu"]["occupied_days"]) == (208, 208, 285)
    assert (rows["fcu"]["sync_days"], rows["fcu"]["raw_days_with_anchor"], rows["fcu"]["occupied_days"]) == (74, 118, 365)
    assert {b: rows[b]["mr1_healthy_firings"] for b in rows} == {"pfpu": 124, "sfpu": 0, "ddahu": 66, "fcu": 149}
    assert all(rows[b]["mr3_healthy_firings"] == 0 for b in ("sfpu", "ddahu", "fcu")) and rows["pfpu"]["mr3_healthy_firings"] == 1
    assert a["P1_identity"]["holds_on_new_buildings"] is False and a["P1_identity"]["per_building"]["ddahu"]["identical"]
    p2 = a["P2_four_building_correlation"]
    assert abs(p2["rho"] + 1.0) < 1e-9 and abs(p2["exact_one_sided_p"] - 1 / 24) < 1e-9 and p2["would_pass_criterion"] and p2["mr1_counts_distinct"]
    c = a["P2_control_raw_count"]
    assert abs(c["rho"] + 1.0) < 1e-9 and abs(c["exact_one_sided_p"] - 1 / 24) < 1e-9 and c["same_ordering_as_Q_support"] is True
    assert a["P3_obligatory_is_log_property"]["pass"] is False
    assert [f.split(":")[0] for f in a["falsifiers_fired"]] == ["F-X20.a", "F-X20.b"]
    assert a["verdict"].startswith("INFORMATIVE")
    assert a["conclusion_licensed_about_discovery_predicting_transfer"] is True   # formally; the control says what it is worth


def test_x20_original_artefact_untouched():
    q = json.loads((ROOT / "outputs" / "discovery_predicts_transfer_q.json").read_text())
    assert set(q) - {"_method"} == {"sdahu", "pfpu", "sfpu"}
    assert q["pfpu"]["sync_days"] == 166 and q["sfpu"]["sync_days"] == 357
