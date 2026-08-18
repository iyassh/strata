"""Phase 6 regression guards: the joint false-alarm budget artifacts.

Data-free — reads the committed outputs/union_fpr_*.json and
outputs/benchmark_v6_*.json artifacts; skips if they are absent
(fresh clone without outputs). Guards the invariants the paper quotes:

  1. the union is consistent (>= every channel, minus-rate <= all-8);
  2. the rate demotion is free (no scenario carried solely by rate,
     no first alarm day covered only by rate);
  3. the deployed-detector FPR stays at or below the quoted ceilings.
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
def test_union_consistency(system):
    art = _load(system)
    n = art["holdout_days"]
    per_channel = {k: v["holdout_fp_days"] for k, v in art["channels"].items()}
    union = art["union_all8"]["holdout_fp_days"]
    norate = art["union_minus_rate"]["holdout_fp_days"]
    assert union >= max(per_channel.values())
    assert union <= sum(per_channel.values())
    assert norate <= union
    assert norate >= max(v for k, v in per_channel.items() if k != "rate")
    assert 0 < n <= art["total_days"]


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
