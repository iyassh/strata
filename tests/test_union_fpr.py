"""Phase 6 regression guards: the joint false-alarm budget artifacts.

These are STASIS guards, not recomputation: they read the committed
outputs/union_fpr_*.json and outputs/benchmark_v6_*.json artifacts (skipping
if absent, e.g. on a fresh clone) and fail if a regeneration or edit changes
the invariants the paper quotes. They do not detect a script that produces
internally-consistent-but-wrong numbers — that is what the hostile-audit
recompute (independent route) is for.

Guarded invariants:
  1. the union counts reconstruct exactly from the per-channel date lists;
  2. the rate demotion is free (no scenario carried solely by rate, no first
     alarm day covered only by rate, under the significance-gated check);
  3. the deployed-detector FPR stays at or below the quoted ceilings;
  4. the demotion verification covers every rate-significant scenario in the
     CURRENT benchmark artifact (staleness guard);
  5. the model/device threshold-provenance disclosure is present (those two
     channels' FP rows are calibration targets, not out-of-sample).
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("sdahu", "pfpu", "sfpu")

# quoted in PHASE6_RESULTS.md — a regression above these ceilings must be
# a deliberate, documented decision, never an accident
DEPLOYED_FPR_CEILING = {"sdahu": 1 / 96, "pfpu": 5 / 96, "sfpu": 4 / 96}


def _load(system):
    p = ROOT / "outputs" / f"union_fpr_{system}.json"
    if not p.exists():
        pytest.skip(f"artifact missing: {p}")
    return json.loads(p.read_text())


@pytest.mark.parametrize("system", SYSTEMS)
def test_union_reconstructs_from_channel_dates(system):
    """The stored union counts must equal the union of the stored per-channel
    holdout FP date lists — the one non-tautological consistency check the
    artifact affords (hostile-audit prescription)."""
    art = _load(system)
    all_dates, norate_dates = set(), set()
    for name, ch in art["channels"].items():
        dates = set(ch["holdout_fp_dates"])
        assert len(dates) == ch["holdout_fp_days"], f"{name}: dates/count mismatch"
        all_dates |= dates
        if name != "rate":
            norate_dates |= dates
    assert art["union_all8"]["holdout_fp_days"] == len(all_dates)
    assert art["union_minus_rate"]["holdout_fp_days"] == len(norate_dates)


@pytest.mark.parametrize("system", SYSTEMS)
def test_rate_demotion_is_free(system):
    art = _load(system)
    assert art["rate_demotion"]["violations"] == []
    # every rate-significant scenario has at least one other significant channel
    for s in art["rate_demotion"]["scenarios_with_rate_significant"]:
        chans = set(s["channels"].split("+"))
        assert chans != {"rate"}, s["label"]


@pytest.mark.parametrize("system", SYSTEMS)
def test_deployed_fpr_ceiling(system):
    art = _load(system)
    assert art["union_minus_rate"]["rate"] <= DEPLOYED_FPR_CEILING[system] + 1e-9


@pytest.mark.parametrize("system", SYSTEMS)
def test_demotion_check_ran_against_current_benchmark(system):
    """The demotion verification must cover every rate-significant scenario
    in the CURRENT benchmark artifact (stale union artifact -> fail)."""
    bench_p = ROOT / "outputs" / f"benchmark_v6_{system}.json"
    if not bench_p.exists():
        pytest.skip("benchmark artifact missing")
    art = _load(system)
    bench = json.loads(bench_p.read_text())
    rate_sig = {
        s["label"]
        for s in bench["scenarios"]
        if "rate" in (s.get("meaningful_channels") or "").split("+")
    }
    checked = {s["label"] for s in art["rate_demotion"]["scenarios_with_rate_significant"]}
    assert rate_sig == checked


@pytest.mark.parametrize("system", SYSTEMS)
def test_calibration_target_channels_disclosed(system):
    """model/device thresholds are quantile-fit on the holdout itself; the
    artifact must carry that disclosure (hostile-audit finding #1)."""
    art = _load(system)
    for ch in ("model", "device"):
        assert "calibration target" in art["channels"][ch]["threshold_provenance"]
    assert any("calibration target" in c for c in art["caveats"])


@pytest.mark.parametrize("system", SYSTEMS)
def test_split_half_probe_present(system):
    """The post-selection defense must ship with the artifact: both halves
    present, and on systems where rate has holdout FPs at all, the demotion
    decision must reproduce on both decision halves."""
    art = _load(system)
    sh = art["split_half_demotion_robustness"]
    assert set(sh) == {"even_months", "odd_months"}
    if art["channels"]["rate"]["holdout_fp_days"] > 0:
        for half in sh.values():
            assert half["rate_is_worst_or_tied"], "demotion decision not split-half stable"
