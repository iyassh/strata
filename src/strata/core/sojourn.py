"""The time perspective of the discovered state model (X12).

A time-infused state model: for every on/off pair in the STATE alphabet the
model carries, per healthy train day, the day's median on-duration, median
off-gap and first-on minute-of-day. Bands are train min/max widened by a
5-minute floor; the holdout gives the channel's false-alarm rate. The
signature alphabet is never read (the wall holds). Pre-registered in
docs/plans/2026-09-23-x12-time-perspective-prereg.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from strata.core.splits import holdout_mask
from strata.io.config import Config

FLOOR_MIN = 5.0      # minutes, each side
SEEN_FRAC = 0.05     # a pair is monitored only if present on >= 5% of train days


def state_pairs(cfg: Config) -> list[tuple[str, str, str]]:
    """(name, on_event, off_event) for every state-alphabet on/off pair."""
    out = []
    for name, spec in cfg.rules["events"].items():
        if spec.get("alphabet", "state") != "state":
            continue
        on = spec.get("on_event") or spec.get("enter_event")
        off = spec.get("off_event") or spec.get("exit_event")
        if on and off:
            out.append((name, on, off))
    return out


def daily_sojourn_stats(log: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Per day x pair: on_med, off_med (minutes) and first_on (minute of day)."""
    rows: dict[str, dict[str, float]] = {}
    for name, on, off in state_pairs(cfg):
        sub = log[log["activity"].isin([on, off])].sort_values("timestamp", kind="stable")
        for day, g in sub.groupby("case_id", sort=False):
            ts = g["timestamp"].to_numpy(); act = g["activity"].to_numpy()
            ons, offs = [], []
            cur_on = None; last_off = None
            for t, a in zip(ts, act):
                if a == on:
                    if last_off is not None:
                        offs.append((t - last_off) / np.timedelta64(1, "m"))
                    cur_on = t
                elif a == off and cur_on is not None:
                    ons.append((t - cur_on) / np.timedelta64(1, "m"))
                    last_off = t; cur_on = None
            first = g[g["activity"] == on]["timestamp"]
            r = rows.setdefault(str(day), {})
            if ons:
                r[f"{name}:on_med"] = float(np.median(ons))
            if offs:
                r[f"{name}:off_med"] = float(np.median(offs))
            if len(first):
                f0 = first.iloc[0]
                r[f"{name}:first_on"] = float(f0.hour * 60 + f0.minute)
    return pd.DataFrame.from_dict(rows, orient="index").sort_index()


@dataclass
class SojournDetector:
    bands: dict[str, tuple[float, float]]
    holdout_fp_days: int
    holdout_days: int
    n_train_days: int


def _flag_matrix(stats: pd.DataFrame, bands: dict[str, tuple[float, float]]) -> pd.DataFrame:
    cols = {}
    for k, (lo, hi) in bands.items():
        if k in stats.columns:
            v = stats[k]
            cols[k] = ((v < lo) | (v > hi)).fillna(False)
    return pd.DataFrame(cols, index=stats.index) if cols else pd.DataFrame(index=stats.index)


def build_sojourn_detector(healthy_stats: pd.DataFrame, holdout_days_per_month: int,
                           floor: float = FLOOR_MIN, seen_frac: float = SEEN_FRAC) -> SojournDetector | None:
    """Bands from TRAIN days only; holdout days give the day-level false-alarm rate."""
    if healthy_stats.empty:
        return None
    days = pd.Series(healthy_stats.index.astype(str), index=healthy_stats.index)
    hold = holdout_mask(days, holdout_days_per_month)
    train, hold_s = healthy_stats[~hold.values], healthy_stats[hold.values]
    keys = [k for k in train.columns if train[k].notna().mean() >= seen_frac]
    if not keys:
        return None
    bands = {k: (float(train[k].min()) - floor, float(train[k].max()) + floor) for k in keys}
    fm = _flag_matrix(hold_s, bands)
    fp = int(fm.any(axis=1).sum()) if len(fm.columns) else 0
    return SojournDetector(bands=bands, holdout_fp_days=fp, holdout_days=len(hold_s),
                           n_train_days=len(train))


def classify_sojourn_days(det: SojournDetector, stats: pd.DataFrame) -> pd.DataFrame:
    """Per day: flagged + which statistic(s) violated."""
    if det is None or stats.empty:
        return pd.DataFrame(columns=["day", "flagged", "violations"])
    fm = _flag_matrix(stats, det.bands)
    flagged = fm.any(axis=1) if len(fm.columns) else pd.Series(False, index=stats.index)
    viol = fm.apply(lambda row: [k for k, v in row.items() if v], axis=1) if len(fm.columns) \
        else pd.Series([[]] * len(stats), index=stats.index)
    return pd.DataFrame({"day": stats.index.astype(str), "flagged": flagged.values,
                         "violations": viol.values})
