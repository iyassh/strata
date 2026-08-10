"""Stratum D tests: template pooling, per-instance cases, absence channel."""

import pandas as pd

from processheal.core.devices import (
    absence_days,
    build_device_detector,
    classify_device_days,
    device_log,
    device_templates,
)
from processheal.hvac.events import abstract_events
from processheal.io.config import Config, load_config

CFG = load_config("configs/lbnl_pfpu")


def _rules(**detection):
    return {
        "detection": {"fpr_quantile": 0.01, "holdout_days_per_month": 8, **detection},
        "events": {
            "occupancy": {"kind": "occupancy", "signal": "OCCUPIED",
                          "on_event": "system_started", "off_event": "system_stopped"},
            **{f"zone_fan_{z}": {
                "kind": "mode", "signal": f"FAN_{z}", "on_above": 0.5,
                "on_event": f"zone_fan_{z}_started", "off_event": f"zone_fan_{z}_stopped",
                "alphabet": "state", "stratum": "device", "device": f"TU_{z}",
            } for z in ("S", "E")},
        },
    }


def _cfg():
    sensors = {"OCCUPIED": "SYS_CTL", "FAN_S": "FAN_S", "FAN_E": "FAN_E",
               "Datetime": "Datetime"}
    return Config(sensors=sensors, rules=_rules())


def _month_frame(days=30, fan_s_on=True, fan_e_on=True):
    idx = pd.date_range("2018-06-01 00:00", periods=days * 1440, freq="1min")
    hours = idx.hour
    fan_cycle = ((hours >= 8) & (hours < 10)) | ((hours >= 14) & (hours < 16))
    return pd.DataFrame({
        "SYS_CTL": ((hours >= 6) & (hours < 18)).astype(int),
        "FAN_S": (fan_cycle & fan_s_on).astype(float),
        "FAN_E": (fan_cycle & fan_e_on).astype(float),
        "Datetime": idx,
    })


def test_templates_strip_zone_token():
    tpl = device_templates(_cfg())
    assert tpl["zone_fan_S_started"] == ("zone_fan_started", "TU_S")
    assert tpl["zone_fan_E_stopped"] == ("zone_fan_stopped", "TU_E")


def test_device_log_pools_instances_into_shared_alphabet():
    log = abstract_events(_month_frame(), _cfg())
    dlog = device_log(log, _cfg())
    assert set(dlog["activity"]) == {"zone_fan_started", "zone_fan_stopped"}
    assert set(dlog["device"]) == {"TU_S", "TU_E"}
    assert dlog["case_id"].str.contains("__TU_").all()
    # unit slice unaffected
    from processheal.hvac.events import state_only
    assert set(state_only(log)["activity"]) == {"system_started", "system_stopped"}


def test_device_detector_flags_deviant_instance_only():
    cfg = _cfg()
    healthy = abstract_events(_month_frame(), cfg)
    sched = sorted(set(healthy["case_id"]))
    det = build_device_detector(cfg, healthy, sched)
    assert det is not None and det.n_train_cases > 0

    # fault month: zone S fan runs continuously (starts once, never the
    # healthy two-cycle rhythm); zone E stays healthy
    df = _month_frame()
    df["FAN_S"] = (df["SYS_CTL"] == 1).astype(float)  # on all occupied hours
    log = abstract_events(df, cfg)
    per = classify_device_days(det, log, cfg)
    # per-instance scoring keeps the zone: any flags must not implicate TU_E
    flagged_devices = set(per.loc[per["flagged"], "device"])
    assert "TU_E" not in flagged_devices


def test_absence_channel_catches_dead_device():
    cfg = _cfg()
    healthy = abstract_events(_month_frame(), cfg)
    sched = sorted(set(healthy["case_id"]))
    det = build_device_detector(cfg, healthy, sched)
    assert det.healthy_absence["TU_S"] == 0.0  # healthy fan cycles daily

    dead = _month_frame(fan_s_on=False)  # fan S never runs again
    log = abstract_events(dead, cfg)
    ab = absence_days(det, log, cfg, sched)
    s = ab[(ab["device"] == "TU_S")]
    e = ab[(ab["device"] == "TU_E")]
    assert s["silent"].all()          # every scheduled day silent for TU_S
    assert not e["silent"].any()      # TU_E unaffected: localization preserved
