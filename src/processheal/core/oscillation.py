"""Oscillation channel (the v2 spec's promised kind, built at last).

Target: control-loop hunting (VAVDMPRUnstable and kin) — a damper or
sensor oscillating around its setpoint. Our event alphabet never looks at
the damper position (it has no command wire, so no mismatch rule; its
movement events live at device stratum granularity too coarse for hunting).
The classical instrument is Hagglund's zero-crossing/direction-change
counting (Hagglund 1995; Thornhill & Hagglund 1997) — this is that, daily:

  score(day, signal) = number of direction changes of the (lightly
  debounced) signal during scheduled operation that day; healthy band
  [train_min, train_max] per signal, train-only; two-sided (a frozen
  actuator scores LOW - stuck and hunting are both visible).

Config: detection.oscillation_signals: [canonical sensor names]. Debounce:
ignore reversals smaller than `oscillation_deadband` (default 0.01 of the
signal's units) so sensor jitter does not count as motion.
"""

from __future__ import annotations

import pandas as pd

from processheal.core.frequency import FrequencyDetector, _flag_matrix
from processheal.core.detection import holdout_mask
from processheal.io.config import Config


def daily_direction_changes(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    signals = cfg.rules["detection"].get("oscillation_signals", [])
    if not signals:
        return pd.DataFrame()
    dead_default = float(cfg.rules["detection"].get("oscillation_deadband", 0.01))
    dead_map = cfg.rules["detection"].get("oscillation_deadbands", {})
    w = df.rename(columns={v: k for k, v in cfg.sensors.items()}).sort_values("Datetime")
    sched = w["OCCUPIED"] > 0
    day = w["Datetime"].dt.date.astype(str)
    out = {}
    for sig in signals:
        if sig not in w.columns:
            continue
        x = w[sig].where(sched)
        # per-signal-class deadband (audit B2: temperature signals need a
        # sensor-precision deadband >= 0.5F or reversal counts are
        # quantization noise; actuator signals use %-travel)
        dead = float(dead_map.get(sig, dead_default))
        step = x.diff()
        move = step.where(step.abs() > dead)
        direction = move.apply(lambda v: 0 if pd.isna(v) else (1 if v > 0 else -1))
        direction = direction.replace(0, pd.NA).ffill()
        change = (direction != direction.shift()) & direction.notna() & direction.shift().notna()
        out[sig] = change.groupby(day.values).sum()
    if not out:
        return pd.DataFrame()
    return pd.DataFrame(out).fillna(0).astype(int)


def build_oscillation_detector(
    healthy_df: pd.DataFrame, cfg: Config
) -> FrequencyDetector | None:
    counts = daily_direction_changes(healthy_df, cfg)
    if counts.empty:
        return None
    days = pd.Series(counts.index.astype(str), index=counts.index)
    hold = holdout_mask(days, cfg.rules["detection"]["holdout_days_per_month"])
    train, hold_c = counts[~hold.values], counts[hold.values]
    bands = {k: (float(train[k].min()), float(train[k].max())) for k in train.columns}
    fp = int(_flag_matrix(hold_c, bands).any(axis=1).sum())
    return FrequencyDetector(bands=bands, holdout_fp_days=fp, holdout_days=len(hold_c))
