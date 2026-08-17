"""Phase 4 frequency channel: two-sided count-bands, train-only calibration."""

import pandas as pd

from processheal.core.frequency import (
    build_frequency_detector,
    classify_frequency_days,
    unit_day_counts,
)


def _healthy_counts(days=60):
    """Healthy month(s): cooling cycles 3-6/day, heating 1-2/day."""
    idx = [f"2018-06-{d:02d}" if d <= 30 else f"2018-07-{d-30:02d}" for d in range(1, days + 1)]
    import random
    rnd = random.Random(7)
    return pd.DataFrame({
        "cooling_active": [rnd.randint(3, 6) for _ in idx],
        "heating_active": [rnd.randint(1, 2) for _ in idx],
    }, index=idx)


def test_bands_come_from_train_days_only():
    hc = _healthy_counts()
    det = build_frequency_detector(hc, holdout_days_per_month=8)
    days = pd.Series(hc.index)
    from processheal.core.detection import holdout_mask
    train = hc[~holdout_mask(days, 8).values]
    assert det.bands["cooling_active"] == (train["cooling_active"].min(),
                                           train["cooling_active"].max())
    assert det.holdout_days > 0  # holdout validated, not used for bands


def test_two_sided_catches_addition_and_removal():
    det = build_frequency_detector(_healthy_counts(), holdout_days_per_month=8)
    test = pd.DataFrame({
        "cooling_active": [40, 4, 0],     # hunting / healthy / silenced
        "heating_active": [1, 1, 1],
    }, index=["d1", "d2", "d3"])
    out = classify_frequency_days(det, test).set_index("day")
    assert bool(out.loc["d1", "flagged"])       # addition (oscillation)
    assert not bool(out.loc["d2", "flagged"])   # healthy day passes
    assert bool(out.loc["d3", "flagged"])       # removal (count below band)
    assert out.loc["d1", "violations"] == ["cooling_active"]


def test_zero_count_day_visible_when_activity_always_occurs():
    # a monitored activity absent from the counts table entirely (day had
    # none) must still register as a 0-count violation if train_min > 0
    det = build_frequency_detector(_healthy_counts(), holdout_days_per_month=8)
    test = pd.DataFrame({"cooling_active": [4]}, index=["d1"])  # no heating col
    out = classify_frequency_days(det, test).set_index("day")
    assert bool(out.loc["d1", "flagged"])
    assert "heating_active" in out.loc["d1", "violations"]


def test_rare_activities_are_not_monitored():
    hc = _healthy_counts()
    hc["economizer_rare"] = 0
    hc.loc[hc.index[0], "economizer_rare"] = 1  # occurs on ~2% of days
    det = build_frequency_detector(hc, holdout_days_per_month=8)
    assert "economizer_rare" not in det.bands  # no stable healthy band


def test_unit_day_counts_uses_state_slice_only():
    log = pd.DataFrame({
        "case_id": ["2018-06-01"] * 3,
        "activity": ["cooling_active", "cooling_active", "mismatch"],
        "timestamp": pd.date_range("2018-06-01 08:00", periods=3, freq="1h"),
        "alphabet": ["state", "state", "signature"],
        "stratum": ["unit", "unit", "unit"],
        "device": [None, None, None],
    })
    c = unit_day_counts(log)
    assert c.loc["2018-06-01", "cooling_active"] == 2
    assert "mismatch" not in c.columns  # signature events never counted
