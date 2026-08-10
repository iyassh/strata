from processheal.core.report import build_report
from processheal.io.brick import point_to_equipment
from processheal.io.config import load_config

CFG = load_config("configs/lbnl_sdahu")


def test_brick_maps_points_to_equipment():
    m = point_to_equipment("configs/lbnl_sdahu/equipment.ttl")
    assert m["OA_DMPR"] == "Outdoor_Air_Damper"
    assert m["CHWC_VLV"] == "Cooling_Coil"
    assert m["SYS_CTL"] == "AHU"


def _conf(unexpected=None, missing=None):
    return {
        "average_trace_fitness": 0.62,
        "percentage_fitting_traces": 30.0,
        "unexpected_by_activity": unexpected or {},
        "missing_by_activity": missing or {},
    }


def test_report_localises_via_config_not_hardcoded_table():
    p2e = point_to_equipment("configs/lbnl_sdahu/equipment.ttl")
    md = build_report(_conf(unexpected={"damper_command_mismatch": 47}), CFG, p2e, "x")
    assert "Outdoor Air Damper" in md
    assert "0.62" in md


def test_report_localises_occupancy_events_to_ahu():
    # audit finding: system_started used to print "unknown equipment"
    p2e = point_to_equipment("configs/lbnl_sdahu/equipment.ttl")
    md = build_report(_conf(unexpected={"system_started": 3}), CFG, p2e, "x")
    assert "AHU" in md
    assert "unknown equipment" not in md


def test_report_shows_missing_behaviour():
    # audit finding: suppression faults used to print "No deviations detected"
    p2e = point_to_equipment("configs/lbnl_sdahu/equipment.ttl")
    md = build_report(_conf(missing={"cooling_active": 200}), CFG, p2e, "x")
    assert "Missing behaviour" in md
    assert "cooling_active" in md
    assert "expected but did not occur" in md
