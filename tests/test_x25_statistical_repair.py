"""Guard: X25 — statistical repair. Conformance thresholds calibrated on a slice
before each month's holdout (out-of-sample holdout rows) and a uniform
rule-of-three floor. Detection counts unchanged on all five systems, no
scenario changed status, no conformance-only detection; the out-of-sample
model rows rose on the fan-powered units (1->4, 1->5), taking their deployed
budgets from 5 and 4 to 7 and 6 of 96. No falsifier fired."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x25_statistical_repair.json"


def test_x25_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text()); s = a["systems"]
    assert a["falsifiers_fired"] == [] and all(v for k, v in a["predictions"].items() if isinstance(v, bool))
    assert {k: (v["detected_before"], v["detected_after"]) for k, v in s.items()} == {"sdahu": (14, 14), "pfpu": (23, 23), "sfpu": (24, 24), "ddahu": (45, 45), "fcu": (42, 42)}
    assert {k: (v["deployed_fp_before"], v["deployed_fp_after"]) for k, v in s.items()} == {"sdahu": (1, 1), "pfpu": (5, 7), "sfpu": (4, 6), "ddahu": (3, 3), "fcu": (4, 4)}
    assert {k: (v["model_holdout_fp_before"], v["model_holdout_fp_after"]) for k, v in s.items()} == {"sdahu": (0, 0), "pfpu": (1, 4), "sfpu": (1, 5), "ddahu": (0, 0), "fcu": (1, 1)}
    assert all(not v["gained"] and not v["lost"] and not v["conformance_only_after"] for v in s.values())
    assert all("out-of-sample" in v["model_fp_provenance_after"] for v in s.values())
    assert a["predictions"]["P4_status_flips_total"] == 0
    assert a["predictions"]["P0_step1_sdahu_byte_identical_VERIFIED_BY_HAND"] is True
