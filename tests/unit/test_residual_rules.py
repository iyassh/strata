"""Phase 2 analytic-redundancy kinds: paired_residual and envelope_residual.

The physics: with the cooling coil off, supply air = mixed air + fan heat, so
a biased SA sensor appears verbatim in the SA-MA residual; and mixed air is a
blend of outdoor and return air, so MA must lie between them.
"""

import pandas as pd

from processheal.hvac.events import abstract_events, event_alphabet_map
from processheal.io.config import load_config

CFG = load_config("configs/lbnl_sdahu")


def _frame(**overrides) -> pd.DataFrame:
    """An occupied, coil-off frame whose residuals are healthy by default."""
    n = overrides.pop("n", 180)
    idx = pd.date_range("2018-06-01 06:00", periods=n, freq="1min")
    base = {
        "SYS_CTL": 1,
        "OA_DMPR": 0.10,
        "OA_DMPR_DM": 0.10,
        "RA_DMPR": 0.90,
        "RA_DMPR_DM": 0.90,
        "CHWC_VLV": 0.0,
        "CHWC_VLV_DM": 0.0,
        "OA_TEMP": 50.0,
        "RA_TEMP": 72.0,
        "MA_TEMP": 60.0,
        "SA_TEMP": 61.0,  # MA + 1F fan heat: inside the healthy band
        "SA_TEMPSPT": 55.0,
        "Datetime": idx,
    }
    base.update(overrides)
    return pd.DataFrame(base)


# ---- paired_residual (supply_air_residual) --------------------------------

def test_healthy_residual_is_silent():
    log = abstract_events(_frame(), CFG)
    assert (log["activity"] == "supply_air_residual").sum() == 0


def test_positive_bias_fires_once():
    # +4C bias: SA reads MA + 1 + 7.2 -> residual 8.2, sustained 3 hours
    log = abstract_events(_frame(SA_TEMP=68.2), CFG)
    assert (log["activity"] == "supply_air_residual").sum() == 1


def test_negative_bias_fires_once():
    # -2C bias: residual = 1 - 3.6 = -2.6-ish -> use -3.6 (below the -2.6 band)
    log = abstract_events(_frame(SA_TEMP=57.4), CFG)
    assert (log["activity"] == "supply_air_residual").sum() == 1


def test_residual_gated_off_while_coil_controls():
    # Same biased residual, but the coil is actively controlling: the control
    # loop hides the residual, so the rule must NOT fire.
    log = abstract_events(_frame(SA_TEMP=68.2, CHWC_VLV=0.4), CFG)
    assert (log["activity"] == "supply_air_residual").sum() == 0


def test_residual_transient_does_not_fire():
    # 90 violating minutes < sustained_min 120 -> silent
    sa = [68.2] * 90 + [61.0] * 90
    log = abstract_events(_frame(SA_TEMP=sa), CFG)
    assert (log["activity"] == "supply_air_residual").sum() == 0


def test_residual_unoccupied_does_not_fire():
    log = abstract_events(_frame(SA_TEMP=68.2, SYS_CTL=0), CFG)
    assert (log["activity"] == "supply_air_residual").sum() == 0


# ---- envelope_residual (mixed_air_envelope) --------------------------------

def test_healthy_envelope_is_silent():
    log = abstract_events(_frame(), CFG)  # 60 between 50 and 72
    assert (log["activity"] == "mixed_air_envelope").sum() == 0


def test_ma_above_envelope_fires_once():
    # MA 80 > max(OA 50, RA 72) + 2F tolerance -> violation
    log = abstract_events(_frame(MA_TEMP=80.0, SA_TEMP=81.0), CFG)
    assert (log["activity"] == "mixed_air_envelope").sum() == 1


def test_ma_below_envelope_fires_once():
    log = abstract_events(_frame(MA_TEMP=45.0, SA_TEMP=46.0), CFG)
    assert (log["activity"] == "mixed_air_envelope").sum() == 1


def test_envelope_within_tolerance_is_silent():
    # MA 73.5 is above RA 72 but within the 2F tolerance
    log = abstract_events(_frame(MA_TEMP=73.5, SA_TEMP=74.5), CFG)
    assert (log["activity"] == "mixed_air_envelope").sum() == 0


# ---- integration with the alphabet split -----------------------------------

def test_residual_rules_are_signature_alphabet():
    amap = event_alphabet_map(CFG)
    assert amap["supply_air_residual"] == "signature"
    assert amap["mixed_air_envelope"] == "signature"
    assert amap["ra_damper_command_mismatch"] == "signature"


def test_ra_mismatch_reuses_mismatch_kind():
    log = abstract_events(_frame(RA_DMPR=0.30), CFG)  # cmd 0.90, pos 0.30
    assert (log["activity"] == "ra_damper_command_mismatch").sum() == 1
