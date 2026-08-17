"""Frequency-aware conformance (Phase 4) — the count channel, done properly.

Every audit of Phases 3b-3c reached the same conclusion: the discovered nets
are order-permissive on loop-heavy alphabets, and every genuine model-channel
detection was a FREQUENCY deviation smuggled through alignment cost (extra
heating episodes, collapsed fan cycles, a vanished daily rhythm). This module
measures those deviations directly and honestly:

  For each activity (unit stratum) and each (activity, device) pair (device
  stratum), the per-day event count must lie inside the healthy count-band
  [train_min, train_max], calibrated on TRAIN days only. TWO-SIDED by
  construction: event-ADDITION (oscillating reheat, hunting dampers) and
  event-REMOVAL (a silenced heating rhythm, a collapsed fan lifecycle) are
  both visible — removal is exactly what order-only alignment proved blind
  to (RESEARCH_LOG D4; audit 3c-C: the faulted zone flagged zero days
  because its deviation was removal).

Pre-registered predictions this channel must adjudicate (stated before any
fault file is scored):
  P1  PFPU damper-stuck faults become visible (healthy AHU heating-day count
      166 -> 90-92 under fault; order-conformance saw nothing).
  P2  SFPU VAVDMPRStuck_0% localizes to the FAULTED zone TU_S (its fan/heat
      counts COLLAPSE; the coupled neighbor TU_I gains counts - both sides
      of a two-sided test, with the faulted zone now visible).
  P3  The instability families (RMTEMPUnstable / VAVDMPRUnstable), count-
      check targets since the v2 spec, move off noise.

Honesty notes, pre-registered: count-bands are extreme-calibrated (discrete
FPR ladder, same as every channel; holdout validates); a per-day count-band
is a deliberately simple instance of stochastic-aware conformance (cite the
Leemans stochastic line; we claim application + calibration, not new theory);
and the matched-rule falsifier applies — a count-band IS a rule family, so
the claim is that DISCOVERY located which counts matter, and this channel is
the calibrated, config-free generalization of those matched rules (every
activity monitored, no hand-picking).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from processheal.core.detection import holdout_mask
from processheal.core.devices import device_log
from processheal.hvac.events import state_only
from processheal.io.config import Config


def _daily_counts(log: pd.DataFrame, key: str) -> pd.DataFrame:
    """Rows = day, columns = key (activity or activity@device), values = counts."""
    if log.empty:
        return pd.DataFrame()
    return (log.groupby(["case_id", key]).size().unstack(fill_value=0))


def unit_day_counts(log: pd.DataFrame) -> pd.DataFrame:
    """Per-day counts of unit-stratum state activities (case_id is the day)."""
    u = state_only(log)
    if u.empty:
        return pd.DataFrame()
    return _daily_counts(u, "activity")


def device_day_counts(log: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Per-day counts keyed activity@device (pooled template names)."""
    d = device_log(log, cfg)
    if d.empty:
        return pd.DataFrame()
    d = d.copy()
    d["day"] = d["case_id"].str.split("__").str[0]
    d["key"] = d["activity"] + "@" + d["device"]
    return _daily_counts(d.assign(case_id=d["day"]), "key")


@dataclass
class FrequencyDetector:
    bands: dict[str, tuple[float, float]]   # key -> [train_min, train_max]
    holdout_fp_days: int
    holdout_days: int

    @property
    def holdout_rate(self) -> float:
        return self.holdout_fp_days / max(self.holdout_days, 1)


def _flag_matrix(counts: pd.DataFrame, bands: dict[str, tuple[float, float]]) -> pd.DataFrame:
    """Per (day, key): outside the healthy band? Missing columns count as 0
    (a day where a monitored activity never fired is a 0-count day — the
    two-sided band catches it when 0 < train_min)."""
    keys = list(bands)
    m = counts.reindex(columns=keys, fill_value=0)
    lo = pd.Series({k: bands[k][0] for k in keys})
    hi = pd.Series({k: bands[k][1] for k in keys})
    return (m.lt(lo, axis=1)) | (m.gt(hi, axis=1))


def build_frequency_detector(
    healthy_counts: pd.DataFrame, holdout_days_per_month: int
) -> FrequencyDetector | None:
    """Bands from TRAIN days only; holdout days validate the day-level rate."""
    if healthy_counts.empty:
        return None
    days = pd.Series(healthy_counts.index.astype(str), index=healthy_counts.index)
    hold = holdout_mask(days, holdout_days_per_month)
    train, hold_c = healthy_counts[~hold.values], healthy_counts[hold.values]
    # only monitor activities that actually occur on a meaningful share of
    # train days: a key seen on <5% of days has no stable healthy band
    seen_frac = (train > 0).mean()
    keys = [k for k in train.columns if seen_frac[k] >= 0.05]
    if not keys:
        return None
    bands = {k: (float(train[k].min()), float(train[k].max())) for k in keys}
    fp = int(_flag_matrix(hold_c, bands).any(axis=1).sum())
    return FrequencyDetector(bands=bands, holdout_fp_days=fp, holdout_days=len(hold_c))


def classify_frequency_days(det: FrequencyDetector, counts: pd.DataFrame) -> pd.DataFrame:
    """Per day: flagged + which key(s) violated (for diagnosis)."""
    if counts.empty or det is None:
        return pd.DataFrame(columns=["day", "flagged", "violations"])
    fm = _flag_matrix(counts, det.bands)
    out = pd.DataFrame({
        "day": counts.index.astype(str),
        "flagged": fm.any(axis=1).values,
    })
    viol = fm.apply(lambda row: [k for k, v in row.items() if v], axis=1)
    out["violations"] = viol.values
    return out


def rolling_active_rate(counts: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Per day: how many of the trailing `window` days each activity was
    ACTIVE (count > 0). The P1 lesson: per-day bands are structurally blind
    to a change in the RATE of active days (a zero-heating day is healthy;
    43 of them in a row is not). This is the multi-day-resolution instrument."""
    if counts.empty:
        return pd.DataFrame()
    active = (counts > 0).astype(int)
    return active.rolling(window, min_periods=window).sum().dropna(how="all")


def build_rate_detector(
    healthy_counts: pd.DataFrame, holdout_days_per_month: int, window: int = 30
) -> FrequencyDetector | None:
    """Bands over train-day-ending windows; holdout-ending windows validate.
    Honesty note (pre-registered): windows overlap, so flagged-day counts are
    serially correlated — significance must use non-overlapping window counts
    (n_eff ~ n/window), and windows ending in holdout still contain train
    days; the split is by window-END day (the decision day)."""
    rates = rolling_active_rate(healthy_counts, window)
    if rates.empty:
        return None
    days = pd.Series(rates.index.astype(str), index=rates.index)
    hold = holdout_mask(days, holdout_days_per_month)
    train, hold_r = rates[~hold.values], rates[hold.values]
    seen_frac = (healthy_counts > 0).mean()
    keys = [k for k in train.columns if seen_frac.get(k, 0) >= 0.05]
    if not keys:
        return None
    bands = {k: (float(train[k].min()), float(train[k].max())) for k in keys}
    fp = int(_flag_matrix(hold_r, bands).any(axis=1).sum())
    return FrequencyDetector(bands=bands, holdout_fp_days=fp, holdout_days=len(hold_r))


def build_rate_detector_monthly(
    healthy_counts: pd.DataFrame, holdout_days_per_month: int, window: int = 30
) -> dict | None:
    """Calendar-month-conditioned rate bands: a window ending in January is
    judged against healthy January windows, not against August ones.
    Justified by a locked dataset fact: every scenario file shares the same
    simulated weather year, so calendar-matched comparison is exact. This is
    the third instrument iteration for prediction P1 — per-day bands were
    blind to active-day-rate changes; season-blind rate bands swallowed the
    signal inside the annual spread (0-29). Both misses documented."""
    rates = rolling_active_rate(healthy_counts, window)
    if rates.empty:
        return None
    days = pd.Series(rates.index.astype(str), index=rates.index)
    # SEASONAL conditioning (4th instrument iteration, P1 chain documented):
    # per-month bands failed their own holdout control (56% FP: ~22 train
    # windows per band are razor-tight and month boundaries drift). Seasons
    # give ~66 train windows per band. DJF/MAM/JJA/SON.
    season_of = {"12": "DJF", "01": "DJF", "02": "DJF", "03": "MAM", "04": "MAM",
                 "05": "MAM", "06": "JJA", "07": "JJA", "08": "JJA",
                 "09": "SON", "10": "SON", "11": "SON"}
    months = days.str[5:7].map(season_of)
    hold = holdout_mask(days, holdout_days_per_month)
    seen_frac = (healthy_counts > 0).mean()
    keys = [k for k in rates.columns if seen_frac.get(k, 0) >= 0.05]
    if not keys:
        return None
    bands: dict[tuple[str, str], tuple[float, float]] = {}
    for m in sorted(months.unique()):
        tr = rates[(months == m).values & (~hold.values)]
        for k in keys:
            if len(tr):
                bands[(k, m)] = (float(tr[k].min()), float(tr[k].max()))
    # holdout validation
    fp = 0
    hold_r = rates[hold.values]
    hold_m = months[hold.values]
    for (idx, row), m in zip(hold_r.iterrows(), hold_m):
        if any((k, m) in bands and not (bands[(k, m)][0] <= row[k] <= bands[(k, m)][1])
               for k in keys):
            fp += 1
    return {"bands": bands, "keys": keys, "window": window,
            "holdout_fp_days": fp, "holdout_days": len(hold_r)}


def classify_rate_days_monthly(det: dict, counts: pd.DataFrame) -> pd.DataFrame:
    """Per day: monthly-banded rolling-rate verdict + violating keys."""
    rates = rolling_active_rate(counts, det["window"])
    if rates.empty:
        return pd.DataFrame(columns=["day", "flagged", "violations"])
    season_of = {"12": "DJF", "01": "DJF", "02": "DJF", "03": "MAM", "04": "MAM",
                 "05": "MAM", "06": "JJA", "07": "JJA", "08": "JJA",
                 "09": "SON", "10": "SON", "11": "SON"}
    rows = []
    for idx, row in rates.iterrows():
        day = str(idx)
        m = season_of[day[5:7]]
        viol = [k for k in det["keys"]
                if (k, m) in det["bands"]
                and not (det["bands"][(k, m)][0] <= row.get(k, 0) <= det["bands"][(k, m)][1])]
        rows.append((day, bool(viol), viol))
    return pd.DataFrame(rows, columns=["day", "flagged", "violations"])
