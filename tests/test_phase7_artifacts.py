"""Phase 7 stasis guards: errata evidence, sensor coverage, cry-wolf.

Artifact-reading consistency checks (skip on fresh clones without outputs/).
Same philosophy as test_union_fpr.py: these catch stale or hand-edited
artifacts and internal inconsistencies, not a wrong-but-consistent script.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    p = ROOT / "outputs" / name
    if not p.exists():
        pytest.skip(f"artifact missing: {p}")
    return json.loads(p.read_text())


def test_sdahu_errata_evidence_present():
    w = _load("week0_audit.json")
    ev = w.get("sdahu_errata_evidence")
    assert ev, "gate 5 (sdahu) has not been run"
    # E1/E2: exactly two byte-identical groups of four, in raw and parquet
    for layer in ("raw_csv", "parquet"):
        if "skipped" in ev[layer]:
            continue
        dupes = ev[layer]["duplicates"]
        groups = sorted(sorted(v) for v in dupes.values())
        assert len(groups) == 2
        assert all(len(g) == 4 for g in groups)
        joined = [" ".join(g) for g in groups]
        assert any("coi_leakage" in j for j in joined)
        assert any("oa_bias" in j for j in joined)
    # E3: healthy/fault SA_SP scales differ by ~2-3 orders of magnitude
    mm = ev["sa_sp_mismatch"]
    assert mm["healthy"]["SA_SP"]["mean"] > 100
    assert mm["fault_example_damper_stuck_010"]["SA_SP"]["mean"] < 10
    assert mm["fault_example_damper_stuck_010"]["SA_SPSPT"]["mean"] < -100
    # E1 controller-side: recorded OA_TEMP residual far below the labeled bias
    ob = ev["oa_bias_controller_side"]
    assert ob["OA_TEMP_abs_diff"]["max"] < 0.5 < ob["labeled_bias_magnitude_F"]
    assert ob["behaviour_mean_abs_divergence"]["MA_TEMP"] > 1.0


def test_sensor_coverage_consistent():
    cov = _load("sensor_coverage.json")
    assert set(cov) == {"sdahu", "pfpu", "sfpu"}
    for system, c in cov.items():
        assert c["mapped"] + len(c["unmapped"]) == c["data_columns"], system
        assert c["mapped_but_absent_in_data"] == [], f"{system}: ghost mappings"
    # the honesty anchor: the sensor PCA used to beat us on SFPU airside
    # fouling must appear in the unmapped list, or the claim is stale
    assert any(c.startswith("VAV_FAN_DP") for c in cov["sfpu"]["unmapped"])


def test_crywolf_consistent_with_union():
    cw = _load("crywolf.json")
    for system in ("sdahu", "pfpu", "sfpu"):
        u = _load(f"union_fpr_{system}.json")
        e = cw[system]
        assert e["fp_days_healthy_holdout"] == u["union_minus_rate"]["holdout_fp_days"]
        fp, tp = e["fp_days_healthy_holdout"], e["tp_alarm_days_fault_scenarios"]
        # artifact rounds to 5 decimals -> tolerance is the rounding half-step
        assert abs(e["cry_wolf_ratio"] - fp / (fp + tp)) <= 5e-6
        assert e["cry_wolf_ratio"] < 0.001  # the quoted "<0.1%" claim


def test_errata_doc_exists_and_canonical():
    text = (ROOT / "ERRATA.md").read_text()
    for tag in ("E1", "E2", "E3", "E4", "10.25984/1881324", "week0_audit.json"):
        assert tag in text
