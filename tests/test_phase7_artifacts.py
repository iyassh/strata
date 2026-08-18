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
    """Not just internal arithmetic: `mapped` is RECOMPUTED from the configs
    (hostile-audit fix — the arithmetic-only guard passed consistent
    forgeries). Config reading needs no data files."""
    import yaml

    cov = _load("sensor_coverage.json")
    assert set(cov) == {"sdahu", "pfpu", "sfpu"}
    for system, c in cov.items():
        assert c["mapped"] + len(c["unmapped"]) == c["data_columns"], system
        assert c["mapped_but_absent_in_data"] == [], f"{system}: ghost mappings"
        raw = yaml.safe_load((ROOT / f"configs/lbnl_{system}/sensors.yaml").read_text())
        sensors = raw[next(iter(raw))]  # single top-level mapping key
        n_cfg = len(set(sensors.values()) - {"Datetime"})
        # every configured sensor exists in the data (0 ghosts), so
        # artifact `mapped` must equal the config's mapping count
        assert c["mapped"] == n_cfg, f"{system}: artifact mapped {c['mapped']} != config {n_cfg}"
    # the honesty anchor: the sensor PCA used to beat us on SFPU airside
    # fouling must appear in the unmapped list, or the claim is stale
    assert any(c.startswith("VAV_FAN_DP") for c in cov["sfpu"]["unmapped"])


def test_crywolf_consistent_with_union():
    """TP is RECOMPUTED from benchmark_v6 + union artifacts (hostile-audit
    fix — the arithmetic-only guard accepted a consistently-halved TP)."""
    cw = _load("crywolf.json")
    for system in ("sdahu", "pfpu", "sfpu"):
        u = _load(f"union_fpr_{system}.json")
        b = _load(f"benchmark_v6_{system}.json")
        e = cw[system]
        assert e["fp_days_healthy_holdout"] == u["union_minus_rate"]["holdout_fp_days"]
        rate_only = {s["label"]: s["rate_only_alarm_days"]
                     for s in u["rate_demotion"]["scenarios_with_rate_significant"]}
        tp_expected = sum(
            len(s["flag_days"]["sig_union"]) - rate_only.get(s["label"], 0)
            for s in b["scenarios"]
            if s["is_fault"] and not s.get("excluded") and s.get("meaningful_channels")
        )
        assert e["tp_alarm_days_fault_scenarios"] == tp_expected, system
        fp, tp = e["fp_days_healthy_holdout"], e["tp_alarm_days_fault_scenarios"]
        # artifact rounds to 5 decimals -> tolerance is the rounding half-step
        assert abs(e["cry_wolf_ratio"] - fp / (fp + tp)) <= 5e-6
        assert e["cry_wolf_ratio"] < 0.001  # the quoted "<0.1%" claim
        # denominators must ship with the ratio (post-audit requirement)
        assert e["healthy_holdout_days"] == u["holdout_days"]
        assert e["fault_scenario_days_observed"] > 0


def test_config_branch_erratum_evidence():
    """ERRATA.md E5: healthy occupied damper floor 0.0 vs 0.1 in every fault
    file (damper_stuck files sit at their stuck value above the floor)."""
    w = _load("week0_audit.json")
    cb = w["sdahu_errata_evidence"].get("config_branch")
    assert cb, "gate 5 config_branch block missing"
    assert cb["healthy_floor"] == 0.0
    floors = cb["occupied_oa_dmpr_min"]
    for name, v in floors.items():
        if name == "AHU_annual":
            continue
        assert v >= 0.1 - 1e-9, f"{name}: fault floor {v} below 0.1"


def test_sfpu_rotation_evidence():
    """ERRATA.md E4: raw rotation evidence (gate 6) — skip if raw absent."""
    w = _load("week0_audit.json")
    ev = w.get("sfpu_rotation_evidence")
    if not ev or "skipped" in ev:
        pytest.skip("raw SFPU files not present")
    assert ev["timestamp_set_identical_to_faultfree"]
    assert not ev["monotonic"]
    assert ev["wrap_points"] == 1


def test_errata_doc_exists_and_canonical():
    text = (ROOT / "ERRATA.md").read_text()
    for tag in ("E1", "E2", "E3", "E4", "10.25984/1881324", "week0_audit.json"):
        assert tag in text
