"""Phase 5 grammar machinery tests."""

import pandas as pd

from processheal.core.grammar import (CANONICAL, band_violation_days, canonical_log,
                                      count_bands, log_profile_distance,
                                      shuffle_within_traces)


def _log():
    return pd.DataFrame({
        "case_id": ["d1"] * 4 + ["d2"] * 2,
        "activity": ["system_started", "cooling_active", "cooling_inactive",
                     "system_stopped", "system_started", "system_stopped"],
        "timestamp": pd.date_range("2018-06-01 06:00", periods=6, freq="1h"),
        "alphabet": ["state"] * 6,
        "stratum": ["unit"] * 6,
        "device": [None] * 6,
    })


def test_canonical_filter_drops_noncanonical():
    log = _log()
    log.loc[len(log)] = ["d1", "zone_fan_S_started",
                         pd.Timestamp("2018-06-01 12:00"), "state", "device", "TU_S"]
    c = canonical_log(log)
    assert "zone_fan_S_started" not in set(c["activity"])
    assert set(c["activity"]) <= set(CANONICAL)


def test_shuffle_preserves_per_day_counts():
    log = _log()
    sh = shuffle_within_traces(log, seed=1)
    a = log.groupby(["case_id", "activity"]).size().sort_index()
    b = sh.groupby(["case_id", "activity"]).size().sort_index()
    assert (a == b).all()  # configuration-model invariant


def test_union_band_violations_two_sided():
    counts = pd.DataFrame({"heating_active": [2, 0, 9]},
                          index=["d1", "d2", "d3"])
    bands = {"heating_active": (1.0, 5.0)}
    v = band_violation_days(counts, bands)
    assert list(v) == [False, True, True]  # removal AND addition flagged


def test_profile_distance_zero_for_identical():
    c = pd.DataFrame({"cooling_active": [3, 4, 5], "system_started": [1, 1, 1]})
    assert log_profile_distance(c, c) == 0.0
    far = pd.DataFrame({"cooling_active": [30, 40, 50], "system_started": [1, 1, 1]})
    assert log_profile_distance(c, far) > 5
