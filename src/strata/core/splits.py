"""Calendar train/holdout splitting — pm4py-free (T3 facade extraction).

Moved out of core.detection so the MIT-clean pipeline path (rules,
residual, frequency, oscillation channels) never imports the AGPL
discovery stack. core.detection re-exports for back-compat.
"""

from __future__ import annotations

import pandas as pd


def holdout_mask(case_ids: pd.Series, holdout_days_per_month: int) -> pd.Series:
    """True for cases whose DAY falls in the last N days of its month.

    Case ids are either plain days ("2018-06-01") or composite
    day-x-device cases ("2018-06-01__TU_S", the device stratum). The split
    is always calendar-based: every case of the same day lands on the same
    side, so pooled device cases can never leak a day across the split.
    """
    dates = pd.to_datetime(case_ids.str.split("__").str[0])
    return dates.dt.day > (dates.dt.days_in_month - holdout_days_per_month)
