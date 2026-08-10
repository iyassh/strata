"""Per-day analytic-redundancy residual channel, blind-calibrated (gap G1 fix).

The Phase-2 *event* rule proved the physics but its band was placed with
knowledge of the fault scenarios (data snooping). This channel replaces it
for detection scoring: each day gets a CONTINUOUS score — the median of the
coil-off, occupied SA-MA residual — and the healthy band is calibrated on
TRAINING days only, before any fault file is opened. The daily median washes
out shutdown transients, so no hand-placed margin is needed.

A day ABSTAINS (score = NaN) unless it offers at least ``min_window_min``
gated minutes: no physics window, no verdict — reported as such, never
silently counted either way.
"""

from __future__ import annotations

import pandas as pd

from processheal.io.config import Config


def daily_residual_scores(
    df: pd.DataFrame, cfg: Config, rule_name: str = "supply_air_residual"
) -> pd.DataFrame:
    """Per-day residual scores for one paired_residual rule.

    Returns a DataFrame with columns ``case_id``, ``score`` (median gated
    residual; NaN when the day has no adequate window) and ``window_min``.
    """
    from processheal.hvac.events import residual_gates

    r = cfg.rules["events"][rule_name]
    w = df.rename(columns={v: k for k, v in cfg.sensors.items()}).sort_values("Datetime")
    gates = residual_gates(r)
    needed = [r["a"], r["b"], r["occ_signal"]] + [g["signal"] for g in gates]
    if any(c not in w.columns for c in needed):
        return pd.DataFrame(columns=["case_id", "score", "window_min"])

    diffs = w["Datetime"].diff().dropna().dt.total_seconds() / 60.0
    interval = float(diffs.median()) if len(diffs) else 1.0

    occ_col = w[r["occ_signal"]]
    gated = (occ_col > r["occ_above"]) if "occ_above" in r else (occ_col == 1)
    for g in gates:
        if "below" in g:
            gated = gated & (w[g["signal"]] <= g["below"])
        if "above" in g:
            gated = gated & (w[g["signal"]] > g["above"])
    day = w["Datetime"].dt.date.astype(str)
    resid = (w[r["a"]] - w[r["b"]]).where(gated)

    g = pd.DataFrame({"case_id": day, "resid": resid}).groupby("case_id")["resid"]
    out = pd.DataFrame({
        "score": g.median(),
        "window_min": g.count() * interval,
    }).reset_index()

    min_window = float(r.get("sustained_min", 120))
    out.loc[out["window_min"] < min_window, "score"] = float("nan")
    return out


def calibrate_band(
    healthy_scores: pd.DataFrame, train_mask: pd.Series, min_width: float = 0.0
) -> tuple[float, float]:
    """Healthy band = [min, max] of TRAIN-day scores (blind: no fault data,
    no holdout data), expanded symmetrically to at least ``min_width`` —
    the sensor-precision floor. Without it, an ultra-stable simulated train
    year yields a razor band (SFPU: 0.22 F) and "detections" that exceed the
    edge by 0.02-0.03 F: physically meaningless on real hardware. Reported
    honestly as extreme-calibrated: the achievable per-side false-alarm rate
    is a discrete ladder, not a smooth quantile."""
    train = healthy_scores.loc[train_mask, "score"].dropna()
    lo, hi = float(train.min()), float(train.max())
    if hi - lo < min_width:
        pad = (min_width - (hi - lo)) / 2.0
        lo, hi = lo - pad, hi + pad
    return lo, hi


def flag_days(scores: pd.DataFrame, band: tuple[float, float]) -> pd.DataFrame:
    """Flag = score strictly outside the healthy band. NaN score = abstain."""
    lo, hi = band
    out = scores.copy()
    out["flagged"] = (out["score"] < lo) | (out["score"] > hi)
    out.loc[out["score"].isna(), "flagged"] = False
    out["evaluable"] = out["score"].notna()
    return out
