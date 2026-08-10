"""STRATA v2 Phase 1: the state/signature alphabet split.

The invariant these tests protect: the model channel (discovery, calibration,
classification) sees ONLY state events. Signature events — the hand-written
fault detectors — must never influence model fitness, or conformance is just
re-scoring the rules (the circularity behind the +0.4pp v1 result).
"""

import pandas as pd

from processheal.core.detection import build_detector, classify_days
from processheal.hvac.events import (
    abstract_events,
    event_alphabet_map,
    rule_alphabet,
    state_only,
)
from processheal.io.config import load_config

CFG = load_config("configs/lbnl_sdahu")


def _two_day_frame(stuck_damper: bool = False) -> pd.DataFrame:
    """Two occupied days; optionally the damper is stuck (mismatch fires)."""
    idx = pd.date_range("2018-06-01 00:00", periods=2880, freq="1min")
    occ = [1 if 6 <= t.hour < 22 else 0 for t in idx]
    return pd.DataFrame({
        "SYS_CTL": occ,
        "OA_DMPR": 0.75 if stuck_damper else 0.10,
        "OA_DMPR_DM": 0.10,
        "CHWC_VLV": 0.0,
        "CHWC_VLV_DM": 0.0,
        "OA_TEMP": 70.0,  # outside economizer window: no window events
        "SA_TEMP": 55.0,
        "SA_TEMPSPT": 55.0,
        "MA_TEMP": 60.0,
        "Datetime": idx,
    })


def test_log_carries_alphabet_column():
    log = abstract_events(_two_day_frame(stuck_damper=True), CFG)
    assert "alphabet" in log.columns
    assert set(log["alphabet"].unique()) <= {"state", "signature"}


def test_alphabet_assignment_matches_kinds():
    amap = event_alphabet_map(CFG)
    assert amap["system_started"] == "state"
    assert amap["cooling_active"] == "state"
    assert amap["economizer_window_entered"] == "state"
    assert amap["damper_command_mismatch"] == "signature"
    assert amap["valve_leak"] == "signature"
    assert amap["setpoint_deviation"] == "signature"


def test_untagged_rule_falls_back_by_kind():
    assert rule_alphabet({"kind": "mismatch"}) == "signature"
    assert rule_alphabet({"kind": "occupancy"}) == "state"
    # explicit tag wins over the kind default
    assert rule_alphabet({"kind": "mode", "alphabet": "signature"}) == "signature"


def test_state_only_strips_signature_events():
    log = abstract_events(_two_day_frame(stuck_damper=True), CFG)
    assert (log["activity"] == "damper_command_mismatch").any()
    state = state_only(log)
    assert not (state["activity"] == "damper_command_mismatch").any()
    assert (state["activity"] == "system_started").any()


def test_state_only_passes_through_legacy_logs():
    legacy = pd.DataFrame({
        "case_id": ["2018-06-01"], "activity": ["system_started"],
        "timestamp": [pd.Timestamp("2018-06-01 06:00")],
    })
    out = state_only(legacy)
    assert len(out) == 1


def test_model_channel_is_blind_to_signature_events():
    """THE Phase 1 invariant: injecting signature events into a day must not
    change its model fitness — the rules channel owns those events."""
    healthy = abstract_events(_two_day_frame(stuck_damper=False), CFG)
    det = build_detector(CFG, healthy)

    clean = abstract_events(_two_day_frame(stuck_damper=False), CFG)
    faulty = abstract_events(_two_day_frame(stuck_damper=True), CFG)
    assert (faulty["activity"] == "damper_command_mismatch").any()

    fit_clean = classify_days(det, clean).set_index("case_id")["fitness"]
    fit_faulty = classify_days(det, faulty).set_index("case_id")["fitness"]
    # same state behaviour, signature events differ -> identical fitness
    pd.testing.assert_series_equal(fit_clean, fit_faulty)


def test_detector_trains_on_state_slice_only():
    healthy = abstract_events(_two_day_frame(stuck_damper=False), CFG)
    det = build_detector(CFG, healthy)
    model_activities = {t.label for t in det.net.transitions if t.label}
    sig_names = {n for n, a in event_alphabet_map(CFG).items() if a == "signature"}
    assert not (model_activities & sig_names)
