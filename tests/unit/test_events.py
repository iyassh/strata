import pandas as pd
import pytest

from processheal.hvac.events import abstract_events, event_sensor_map
from processheal.io.config import Config, load_config

CFG = load_config("configs/lbnl_sdahu")


def _frame(**overrides) -> pd.DataFrame:
    """A one-hour occupied frame with healthy defaults; override any column."""
    n = overrides.pop("n", 60)
    freq = overrides.pop("freq", "1min")
    idx = pd.date_range("2018-06-01 06:00", periods=n, freq=freq)
    base = {
        "SYS_CTL": 1,
        "OA_DMPR": 0.10,
        "OA_DMPR_DM": 0.10,
        "CHWC_VLV": 0.0,
        "CHWC_VLV_DM": 0.0,
        "OA_TEMP": 50.0,
        "SA_TEMP": 55.0,
        "SA_TEMPSPT": 55.0,
        "MA_TEMP": 60.0,
        "Datetime": idx,
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_one_system_started_per_occupied_day():
    idx = pd.date_range("2018-06-01 00:00", periods=2880, freq="1min")  # 2 days
    occ = [1 if 6 <= t.hour < 22 else 0 for t in idx]
    df = _frame(n=2880, SYS_CTL=occ, Datetime=idx)
    log = abstract_events(df, CFG)
    assert (log["activity"] == "system_started").sum() == 2


def test_damper_mismatch_fires_once_when_stuck():
    df = _frame(OA_DMPR=0.75, OA_DMPR_DM=0.10)  # 60 consecutive mismatched minutes
    log = abstract_events(df, CFG)
    assert (log["activity"] == "damper_command_mismatch").sum() == 1


def test_no_damper_mismatch_when_healthy():
    df = _frame(OA_DMPR=0.10, OA_DMPR_DM=0.10)
    log = abstract_events(df, CFG)
    assert (log["activity"] == "damper_command_mismatch").sum() == 0


def test_scattered_mismatch_minutes_do_not_fire():
    # 120 minutes alternating mismatch/no-mismatch: 60 flagged minutes total,
    # but the longest CONSECUTIVE run is 1 -> must NOT fire (audit finding).
    pos = [0.75 if i % 2 == 0 else 0.10 for i in range(120)]
    df = _frame(n=120, OA_DMPR=pos, OA_DMPR_DM=0.10)
    log = abstract_events(df, CFG)
    assert (log["activity"] == "damper_command_mismatch").sum() == 0


def test_sustained_min_is_interval_aware():
    # On 5-minute data, 60 sustained minutes = 12 samples (audit finding:
    # previously interpreted as 60 SAMPLES = 5 hours).
    df = _frame(n=12, freq="5min", OA_DMPR=0.75, OA_DMPR_DM=0.10)
    log = abstract_events(df, CFG)
    assert (log["activity"] == "damper_command_mismatch").sum() == 1
    df_short = _frame(n=6, freq="5min", OA_DMPR=0.75, OA_DMPR_DM=0.10)
    log_short = abstract_events(df_short, CFG)
    assert (log_short["activity"] == "damper_command_mismatch").sum() == 0


def test_valve_mismatch_fires_when_stuck():
    df = _frame(CHWC_VLV=0.50, CHWC_VLV_DM=0.0)
    log = abstract_events(df, CFG)
    assert (log["activity"] == "valve_command_mismatch").sum() == 1


def test_cooling_and_economizer_edges():
    idx = pd.date_range("2018-05-01 06:00", periods=6, freq="1min")
    df = _frame(
        n=6,
        CHWC_VLV=[0, 0, 0.2, 0.2, 0, 0],
        CHWC_VLV_DM=[0, 0, 0.2, 0.2, 0, 0],
        OA_TEMP=[30, 30, 45, 45, 65, 65],
        Datetime=idx,
    )
    acts = set(abstract_events(df, CFG)["activity"])
    assert "cooling_active" in acts
    assert "economizer_window_entered" in acts
    assert "economizer_window_exited" in acts


def test_first_row_state_is_not_a_transition():
    # Condition already True on row 0 must not fabricate an "entered" event
    # (audit finding: shift fill_value=False created day-start artifacts).
    df = _frame(OA_TEMP=45.0)  # inside the economizer window from row 0
    log = abstract_events(df, CFG)
    assert (log["activity"] == "economizer_window_entered").sum() == 0


def test_valve_leak_with_small_idle_command():
    # cmd=0.01 (not exactly zero) with pos above leak_above must STILL count
    # as a leak (audit finding: cmd <= 0.0 exact-float dead zone).
    df = _frame(CHWC_VLV=0.10, CHWC_VLV_DM=0.01, OA_TEMP=70.0)
    log = abstract_events(df, CFG)
    assert (log["activity"] == "valve_leak").sum() == 1


def test_setpoint_deviation_fires_only_when_cooling_gated():
    # Deviation while mechanically cooling -> fires.
    hot = _frame(SA_TEMP=62.0, SA_TEMPSPT=55.0, CHWC_VLV=0.30, CHWC_VLV_DM=0.30)
    assert (abstract_events(hot, CFG)["activity"] == "setpoint_deviation").sum() == 1
    # Same deviation with the coil closed (winter drift) -> must NOT fire.
    winter = _frame(SA_TEMP=62.0, SA_TEMPSPT=55.0, CHWC_VLV=0.0, CHWC_VLV_DM=0.0)
    assert (abstract_events(winter, CFG)["activity"] == "setpoint_deviation").sum() == 0


def test_rules_are_config_driven_not_hardcoded():
    # A brand-new mismatch rule added to the config must be emitted with no
    # code change (audit finding: rule names were hardcoded).
    rules = {
        "events": {
            "ra_damper_command_mismatch": {
                "kind": "mismatch",
                "pos": "RA_DMPR_POS",
                "cmd": "RA_DMPR_CMD",
                "threshold": 0.05,
                "sustained_min": 10,
            }
        }
    }
    sensors = {"RA_DMPR_POS": "RA_DMPR", "RA_DMPR_CMD": "RA_DMPR_DM", "Datetime": "Datetime"}
    cfg = Config(sensors=sensors, rules=rules)
    idx = pd.date_range("2018-06-01 06:00", periods=20, freq="1min")
    df = pd.DataFrame({"RA_DMPR": 0.9, "RA_DMPR_DM": 0.1, "Datetime": idx})
    log = abstract_events(df, cfg)
    assert (log["activity"] == "ra_damper_command_mismatch").sum() == 1


def test_rule_with_missing_sensor_is_skipped():
    df = _frame().drop(columns=["SA_TEMPSPT"])  # setpoint rule loses its sensor
    log = abstract_events(df, CFG)  # must not raise
    assert (log["activity"] == "setpoint_deviation").sum() == 0


def test_unknown_kind_fails_loudly():
    cfg = Config(sensors={"Datetime": "Datetime"}, rules={"events": {"x": {"kind": "bogus"}}})
    df = pd.DataFrame({"Datetime": pd.date_range("2018-06-01", periods=2, freq="1min")})
    with pytest.raises(ValueError, match="unknown kind"):
        abstract_events(df, cfg)


def test_event_sensor_map_derived_from_config():
    m = event_sensor_map(CFG)
    assert m["damper_command_mismatch"] == "OA_DMPR"
    assert m["valve_leak"] == "CHWC_VLV"
    assert m["system_started"] == "SYS_CTL"
    assert m["cooling_active"] == "CHWC_VLV"
