"""Phase 8 stasis guards (X11/X8/X5/X7 artifacts).

Same philosophy as the other artifact guards: catch stale, hand-edited,
or silently-regenerated-with-different-outcome artifacts. The X7 guard
pins the FIRED falsifiers — a rerun that loses them must fail loudly.
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


def test_x11_adjudicated_13_of_14():
    a = _load("x11_branch.json")
    assert a["verdict"] == "ADJUDICATED"
    assert a["falsifiers_fired"] == []
    assert a["adjudicated_scorecard"]["detected"] == 13
    assert a["adjudicated_scorecard"]["of"] == 14
    # the estimator concordance the adjudication rests on
    assert a["fault_branch_baseline"]["spread"] <= 0.25
    est = a["fault_branch_baseline"]["estimators"]
    assert len(est) == 5
    # oa_bias must be the (only) flipped scenario, and via resid removal
    flipped = [s for s in a["adjudicated_scorecard"]["scenarios"] if not s["detected"]]
    assert len(flipped) == 1 and flipped[0]["file"].startswith("oa_bias")
    # coi_bias all still significant under the corrected band
    for f, r in a["corrected_rescoring"].items():
        if f.startswith("coi_bias"):
            assert r["significant"], f
    # FPU homogeneity: scheduled-occupancy identity and clean floors
    for system, b in a["fpu_homogeneity"].items():
        assert b["max_scheduled_occupancy_daydiff_min"] == 0.0, system
        assert b["damper_floor_mismatches"] == {}, system
        assert all(b["rmtemp_medians_inside_band"].values()), system


def test_x8_breakdown_and_visibility_split():
    a = _load("x8_contamination.json")
    assert a["falsifiers_fired"] == []
    base_cov = a["baseline"]["coverage"]
    assert base_cov["coi_bias_-4_annual"] == "164/164"
    for r in a["runs"]:
        # FP never increases (bands only widen)
        assert r["holdout_fp"] <= a["baseline"]["holdout_fp"]
        if r["source"] == "worst_coi_bias_-4":
            # breakdown at every k, including the smallest
            assert r["coverage"]["coi_bias_-4_annual"].startswith("0/")
            assert r["coverage"]["coi_bias_-2_annual"].startswith("0/")
            # silent to the rules channel
            assert r["contaminated_days_with_signature_events"] == 0
        else:
            # mild case: no recall loss, fully rules-visible
            assert r["coverage"] == base_cov
            assert r["contaminated_days_with_signature_events"] == r["n_contaminated"]


def test_x5_no_antimonotone_ladder():
    a = _load("x5_severity.json")
    assert a["falsifiers_fired"] == []
    for name, lad in a["ladders"].items():
        rho, p = lad["spearman_rho"], lad["p_value_naive"]
        if rho is not None and p is not None:
            assert not (rho < 0 and p < 0.05), name


def test_x7_fired_falsifiers_are_pinned():
    """X7's finding IS the fired falsifiers — a regeneration that loses
    them (e.g. after silently re-tuning thresholds) must fail here and
    force a documented decision."""
    a = _load("x7_downsample.json")
    fired = a["falsifiers_fired"]
    assert any("sdahu healthy gains" in f for f in fired)
    assert any("pfpu healthy gains" in f for f in fired)
    assert any("sfpu healthy gains" in f for f in fired)
    # the sampling-robust channel: residual coverage on the bias families
    sd = a["systems"]["sdahu"]["families"]["sensor_bias"]["coverage_1min_vs_15min"]
    r1, r15 = sd["residual_days"]
    assert r15 >= 0.9 * r1
