"""Guard: ERRATA E3 leakage is a measurement — a healthy-only threshold on
either static-pressure column separates provenance perfectly."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "e3_leakage.json"


def test_provenance_separates_perfectly_on_both_columns():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text())
    assert a["rule_chosen_on"] == "healthy file only" and a["n_fault_files"] == 20
    for c in ("SA_SP", "SA_SPSPT"):
        r = a["per_feature"][c]
        assert r["fault_days_misclassified_as_healthy"] == 0
        assert r["healthy_days_classified_healthy"] == r["healthy_days"]
        assert r["accuracy"] == 1.0
