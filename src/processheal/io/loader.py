"""Loading and verification of LBNL SDAHU sensor data."""

from __future__ import annotations

import pandas as pd


def operating_summary(df: pd.DataFrame) -> dict:
    """Compute the operating-mode breakdown and the key diagnostic discrepancies.

    The two ``*_cmd_pos_meanabs`` figures are near zero for healthy operation and
    jump sharply when an actuator is stuck, so they are the simplest fault check.
    """
    return {
        "rows": len(df),
        "occupied_frac": (df["SYS_CTL"] == 1).mean(),
        "cooling_active_frac": (df["CHWC_VLV"] > 0.05).mean(),
        "economizer_open_frac": (df["OA_DMPR"] > 0.5).mean(),
        "mean_OA_TEMP": df["OA_TEMP"].mean(),
        "mean_SA_TEMP": df["SA_TEMP"].mean(),
        "valve_cmd_pos_meanabs": (df["CHWC_VLV"] - df["CHWC_VLV_DM"]).abs().mean(),
        "damper_cmd_pos_meanabs": (df["OA_DMPR"] - df["OA_DMPR_DM"]).abs().mean(),
    }
