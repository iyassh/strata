"""tests/test_openfdd_baseline.py — open-fdd traditional-baseline guards.

Contract under test is the pre-registration:
docs/plans/2026-09-11-openfdd-prereg.md
"""
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from openfdd_baseline import (  # noqa: E402
    FC_RULES,
    ROLE_MAP,
    INH2O_PER_PA,
    to_openfdd_frame,
    day_key,
)

SYSTEMS = ("sdahu", "pfpu", "sfpu")


def _frame(**cols):
    idx = pd.date_range("2018-06-01", periods=5, freq="min")
    return pd.DataFrame(cols, index=idx)


def test_headline_battery_is_the_fifteen_g36_conditions():
    """Pre-reg scope: FC1-FC15, the published Guideline 36 conditions."""
    assert FC_RULES == [f"FC{i}" for i in range(1, 16)]


def test_adapter_renames_to_roles_and_preserves_rows():
    df = _frame(
        OA_TEMP=[50.0] * 5, SA_TEMP=[55.0] * 5, MA_TEMP=[60.0] * 5,
        RA_TEMP=[70.0] * 5, SA_TEMPSPT=[55.0] * 5, CHWC_VLV=[0.5] * 5,
        OA_DMPR=[0.2] * 5, SYS_CTL=[1] * 5, SF_SPD=[0.9] * 5,
        SF_SPD_DM=[1] * 5, SA_SP=[402.0] * 5, SA_SPSPT=[1.607] * 5,
        SA_CFM=[1000.0] * 5,
    )
    out = to_openfdd_frame(df, "sdahu")
    assert len(out) == len(df)
    for role in ("outside-air-temp", "discharge-air-temp", "mixed-air-temp",
                 "return-air-temp", "cooling-valve", "outside-air-damper"):
        assert role in out.columns, role
    assert out["outside-air-temp"].iloc[0] == 50.0
    assert out["cooling-valve"].iloc[0] == 0.5


def test_sdahu_duct_static_converted_pascals_to_inches():
    """The unit trap: raw pascals against an inH2O setpoint would fire FC1
    on every row. Pre-reg requires /249.0889 on SDAHU only."""
    df = _frame(SA_SP=[402.0] * 5, SA_SPSPT=[1.607] * 5)
    out = to_openfdd_frame(df, "sdahu")
    assert out["duct-static-pressure"].iloc[0] == pytest.approx(
        402.0 * INH2O_PER_PA, rel=1e-6)
    assert out["duct-static-pressure"].iloc[0] == pytest.approx(1.614, abs=0.01)


def test_fpu_duct_static_not_converted():
    df = _frame(SA_SP=[1.40] * 5, SA_SPSPT=[1.40] * 5)
    out = to_openfdd_frame(df, "pfpu")
    assert out["duct-static-pressure"].iloc[0] == pytest.approx(1.40)


def test_fan_roles_are_inverted_between_systems():
    """SDAHU SF_SPD is a constant speed and SF_CS a current sensor;
    on the FPUs the meanings swap. Pre-reg section 1."""
    assert ROLE_MAP["sdahu"]["fan-cmd"] == "SF_SPD"
    assert ROLE_MAP["sdahu"]["fan-status"] == "SF_SPD_DM"
    for s in ("pfpu", "sfpu"):
        assert ROLE_MAP[s]["fan-cmd"] == "SF_SPD"
        assert ROLE_MAP[s]["fan-status"] == "SF_CS"


def test_fpu_occupancy_is_thresholded_not_passed_through():
    """SYS_CTL is {0,1,2} on the FPUs: occupied := SYS_CTL > 0."""
    df = _frame(SYS_CTL=[0, 1, 2, 0, 2])
    out = to_openfdd_frame(df, "pfpu")
    assert list(out["occupied"]) == [0, 1, 1, 0, 1]


def test_day_key_is_calendar_day():
    idx = pd.to_datetime(["2018-06-01 00:30", "2018-06-01 23:59", "2018-06-02 00:01"])
    assert list(day_key(idx)) == ["2018-06-01", "2018-06-01", "2018-06-02"]


# ---------------------------------------------------------------- artifacts

def _artifact(system):
    p = ROOT / "outputs" / f"openfdd_baseline_{system}.json"
    if not p.exists():
        pytest.skip(f"artifact not generated yet: {p.name}")
    return json.loads(p.read_text())


@pytest.mark.parametrize("system,n_scen", [("sdahu", 14), ("pfpu", 30), ("sfpu", 29)])
def test_artifact_scenario_count_matches_the_exam(system, n_scen):
    a = _artifact(system)
    assert len(a["scenarios"]) == n_scen


@pytest.mark.parametrize("system", SYSTEMS)
def test_artifact_rows_have_required_integer_fields(system):
    a = _artifact(system)
    for s in a["scenarios"]:
        assert isinstance(s["battery_flag_days"], int)
    assert isinstance(a["clean_year"]["holdout_fp_days"], int)
    assert isinstance(a["clean_year"]["holdout_days"], int)
    assert isinstance(a["clean_year"]["full_year_fp_days"], int)


@pytest.mark.parametrize("system", SYSTEMS)
def test_artifact_records_falsifier_verdict(system):
    """F1 must be evaluated in the artifact, not decided in prose later."""
    a = _artifact(system)
    assert a["falsifier_F1"]["verdict"] in ("FIRED", "NOT_FIRED")


@pytest.mark.parametrize("system", SYSTEMS)
def test_artifact_accounts_for_every_condition(system):
    """Honest accounting: all 15 classified, none silently dropped."""
    a = _artifact(system)
    per = a["per_condition"]
    assert set(per) == set(FC_RULES)
    for rid, rec in per.items():
        assert rec["status"] in ("fired", "not_fired", "unrunnable")
        if rec["status"] == "unrunnable":
            assert rec["missing_roles"], rid


def test_sdahu_heating_conditions_recorded_unrunnable():
    """SDAHU is cooling-only: FC5/FC7/FC14/FC15 cannot run (pre-reg 1)."""
    a = _artifact("sdahu")
    for rid in ("FC5", "FC7", "FC14", "FC15"):
        assert a["per_condition"][rid]["status"] == "unrunnable", rid


@pytest.mark.parametrize("system", SYSTEMS)
def test_defaults_were_not_tuned(system):
    a = _artifact(system)
    assert a["params_overridden"] == {}, "as-deployed defaults are the contract"
