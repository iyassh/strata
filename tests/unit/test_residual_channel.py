"""Gap-fix tests: blind-calibrated residual channel (G1) and fail-closed gates (G8)."""

import pandas as pd

from processheal.core.residuals import calibrate_band, daily_residual_scores, flag_days
from processheal.hvac.events import abstract_events
from processheal.io.config import load_config

CFG = load_config("configs/lbnl_sdahu")


def _two_day_frame(sa_day2: float) -> pd.DataFrame:
    """Two occupied coil-off days; day 1 healthy (SA = MA + 1), day 2 varies."""
    idx = pd.date_range("2018-06-01 00:00", periods=2880, freq="1min")
    sa = [61.0] * 1440 + [sa_day2] * 1440
    return pd.DataFrame({
        "SYS_CTL": 1, "CHWC_VLV": 0.0, "CHWC_VLV_DM": 0.0,
        "OA_DMPR": 0.1, "OA_DMPR_DM": 0.1,
        "OA_TEMP": 50.0, "RA_TEMP": 72.0, "MA_TEMP": 60.0,
        "SA_TEMP": sa, "SA_TEMPSPT": 55.0, "Datetime": idx,
    })


def test_daily_scores_are_medians():
    s = daily_residual_scores(_two_day_frame(68.2), CFG).set_index("case_id")
    assert abs(s.loc["2018-06-01", "score"] - 1.0) < 1e-9
    assert abs(s.loc["2018-06-02", "score"] - 8.2) < 1e-9


def test_day_without_window_abstains():
    df = _two_day_frame(68.2)
    df.loc[df["Datetime"].dt.date.astype(str) == "2018-06-02", "CHWC_VLV"] = 0.5
    s = daily_residual_scores(df, CFG).set_index("case_id")
    assert pd.isna(s.loc["2018-06-02", "score"])  # coil on all day: no window
    f = flag_days(s.reset_index(), (-1.0, 3.0)).set_index("case_id")
    assert not bool(f.loc["2018-06-02", "flagged"])  # abstain, never flag
    assert not bool(f.loc["2018-06-02", "evaluable"])


def test_band_from_train_only_flags_bias_day():
    healthy = daily_residual_scores(_two_day_frame(61.0), CFG)
    band = calibrate_band(healthy, pd.Series([True, True]))
    biased = daily_residual_scores(_two_day_frame(68.2), CFG)
    f = flag_days(biased, band).set_index("case_id")
    assert not bool(f.loc["2018-06-01", "flagged"])  # healthy day inside band
    assert bool(f.loc["2018-06-02", "flagged"])      # +4C bias day outside


def test_gates_fail_closed_when_gate_sensor_unmapped():
    # Remove the coil signal entirely: supply_air_residual and
    # setpoint_deviation both declare gates on it -> both rules must be
    # SKIPPED (fail closed), not run ungated (G8).
    df = _two_day_frame(68.2).drop(columns=["CHWC_VLV"])
    df.loc[df.index[:360], "SYS_CTL"] = 0  # an occupancy edge -> a state event
    log = abstract_events(df, CFG)
    assert (log["activity"] == "supply_air_residual").sum() == 0
    assert (log["activity"] == "setpoint_deviation").sum() == 0
    # state events still emitted: the building is degraded, not dead
    assert (log["alphabet"] == "state").any()


def test_residual_scores_empty_when_sensors_missing():
    df = _two_day_frame(68.2).drop(columns=["MA_TEMP"])
    s = daily_residual_scores(df, CFG)
    assert s.empty


def test_multi_gate_residual_requires_all_gates_idle():
    """FPU-style: SA-MA residual gated on cooling AND heating coils (gates list)."""
    from processheal.io.config import Config
    rules = {
        "detection": CFG.rules["detection"],
        "events": {
            "supply_air_residual": {
                "kind": "paired_residual", "a": "SA_TEMP", "b": "MA_TEMP",
                "low": -2.6, "high": 3.3,
                "gates": [
                    {"signal": "CHWC_VLV_POS", "below": 0.02},
                    {"signal": "HWC_VLV_POS", "below": 0.02},
                ],
                "occ_signal": "OCCUPIED", "sustained_min": 120,
            },
        },
    }
    cfg2 = Config(sensors={**CFG.sensors, "HWC_VLV_POS": "HWC_VLV"}, rules=rules)
    df = _two_day_frame(68.2)
    df["HWC_VLV"] = 0.0
    log = abstract_events(df, cfg2)
    assert (log["activity"] == "supply_air_residual").sum() >= 1  # both coils off: fires
    df2 = _two_day_frame(68.2)
    df2["HWC_VLV"] = 0.5  # heating coil ACTIVE: residual hidden -> silent
    log2 = abstract_events(df2, cfg2)
    assert (log2["activity"] == "supply_air_residual").sum() == 0
    df3 = _two_day_frame(68.2).drop(columns=["SA_TEMPSPT"])  # unrelated col fine
    df3 = df3.drop(columns=[])  # no-op
    df3 = df3.drop(columns=["OA_DMPR"])  # still fine: not needed by this rule
    df3["HWC_VLV"] = 0.0
    log3 = abstract_events(df3, cfg2)
    assert (log3["activity"] == "supply_air_residual").sum() >= 1
    # gates list fail-closed: drop a gate sensor -> rule skipped
    df4 = _two_day_frame(68.2).drop(columns=["CHWC_VLV"])
    df4["HWC_VLV"] = 0.0
    log4 = abstract_events(df4, cfg2)
    assert (log4["activity"] == "supply_air_residual").sum() == 0


def test_stratum_routing_excludes_device_events_from_unit_slice():
    from processheal.hvac.events import device_state_only, state_only
    from processheal.io.config import Config
    rules = {
        "detection": CFG.rules["detection"],
        "events": {
            "occupancy": {"kind": "occupancy", "signal": "OCCUPIED",
                          "on_event": "system_started", "off_event": "system_stopped"},
            "zone_fan": {"kind": "mode", "signal": "OA_DMPR_POS", "on_above": 0.5,
                         "on_event": "fan_started", "off_event": "fan_stopped",
                         "stratum": "device"},
        },
    }
    cfg2 = Config(sensors=CFG.sensors, rules=rules)
    df = _two_day_frame(61.0)
    df.loc[df.index[:360], "SYS_CTL"] = 0
    df.loc[df.index[720:1080], "OA_DMPR"] = 0.9  # fan cycles
    log = abstract_events(df, cfg2)
    unit = state_only(log)
    dev = device_state_only(log)
    assert set(unit["activity"]) == {"system_started"}
    assert set(dev["activity"]) <= {"fan_started", "fan_stopped"} and len(dev) > 0


def test_occ_above_gate_includes_night_cycle_state():
    from processheal.io.config import Config
    rules = {
        "detection": CFG.rules["detection"],
        "events": {
            "supply_air_residual": {
                "kind": "paired_residual", "a": "SA_TEMP", "b": "MA_TEMP",
                "low": -2.6, "high": 3.3,
                "gate_signal": "CHWC_VLV_POS", "gate_below": 0.02,
                "occ_signal": "OCCUPIED", "occ_above": 0.5,
                "sustained_min": 120,
            },
        },
    }
    cfg2 = Config(sensors=CFG.sensors, rules=rules)
    df = _two_day_frame(68.2)
    df["SYS_CTL"] = 2  # night-cycle state, biased residual
    log = abstract_events(df, cfg2)
    assert (log["activity"] == "supply_air_residual").sum() == 1
    # default ==1 semantics would have been silent on state 2
    del rules["events"]["supply_air_residual"]["occ_above"]
    log2 = abstract_events(df, Config(sensors=CFG.sensors, rules=rules))
    assert (log2["activity"] == "supply_air_residual").sum() == 0
