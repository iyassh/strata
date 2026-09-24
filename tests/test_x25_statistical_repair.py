"""Guard: X25 — statistical repair, final state (step 4). Conformance thresholds
calibrated on a slice before each month's holdout (out-of-sample rows: model
1->4, 1->5 on the fan-powered units; budgets 5->7, 4->6 of 96) and a per-day
residual null floored at three days, which removed seven residual-only
detections (14/22/21/45/40); F-X25.c fired on SFPU and the change is reported
as a detector change. No conformance-only detection."""
import json
from pathlib import Path

import pytest

ART = Path(__file__).resolve().parents[1] / "outputs" / "x25_statistical_repair.json"


def test_x25_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text()); s = a["systems"]
    # step 4 (per-day residual null): F-X25.c fired on SFPU; reported as a detector change
    assert [f.split(":")[0] for f in a["falsifiers_fired"]] == ["F-X25.c"]
    assert a["predictions"]["P1_out_of_sample"] and a["predictions"]["P2_budget_le_10"] and a["predictions"]["P3_no_conformance_only"]
    assert {k: (v["detected_before"], v["detected_after"]) for k, v in s.items()} == {"sdahu": (14, 14), "pfpu": (23, 22), "sfpu": (24, 21), "ddahu": (45, 45), "fcu": (42, 40)}
    assert {k: (v["deployed_fp_before"], v["deployed_fp_after"]) for k, v in s.items()} == {"sdahu": (1, 1), "pfpu": (5, 7), "sfpu": (4, 6), "ddahu": (3, 3), "fcu": (4, 4)}
    assert {k: (v["model_holdout_fp_before"], v["model_holdout_fp_after"]) for k, v in s.items()} == {"sdahu": (0, 0), "pfpu": (1, 4), "sfpu": (1, 5), "ddahu": (0, 0), "fcu": (1, 1)}
    assert all(not v["conformance_only_after"] for v in s.values())
    assert sorted(s["sfpu"]["lost"]) == ["SFPU_ReheatCoilFouling_Airside_Severe", "SFPU_ReheatCoilFouling_Waterside_Severe", "SFPU_VAVFanRestrictFlow"]
    assert sorted(s["fcu"]["lost"]) == ["FCU_OADMPRLeak_20", "FCU_OADMPRLeak_50"] and s["pfpu"]["lost"] == ["PFPU_SensorBias_RMTEMP_+4C"]
    assert s["ddahu"]["gained"] == ["DualDuct_SensorBias_CSP_+2inwg"] and s["ddahu"]["lost"] == ["DualDuct_SensorBias_HSA_+2C"]
    assert all("out-of-sample" in v["model_fp_provenance_after"] for v in s.values())
    assert a["predictions"]["P4_status_flips_total"] == 8
    step4 = json.loads((ART.parent / "x25_step4_perday.json").read_text())
    assert [f.split(":")[0] for f in step4["falsifiers_fired"]] == ["F-X25.c"]
    assert a["predictions"]["P0_step1_sdahu_byte_identical_VERIFIED_BY_HAND"] is True
