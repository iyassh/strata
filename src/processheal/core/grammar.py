"""Stratum S — the cross-system grammar experiment (Phase 5).

Implements the pre-registered design in PHASE5_PLAN.md, and nothing not in
it: canonical projection (identity over a FIXED unit-level list), three 3x3
matrices, the order-shuffle null (configuration-model style: preserves
per-day counts, destroys order), and the leave-one-out cold-start.

Honesty invariants carried from the plan:
- M1 cells are PER-TRACE FITNESS DISTRIBUTIONS (never bare means).
- Diagonals use HOLDOUT days only (a model never judges its own train days).
- The null decides what counts as grammar; below-null structure is artifact.
- Cold-start bands never touch the target system's data; the target's
  holdout is used ONLY to estimate the zero-shot false-alarm rate.
"""

from __future__ import annotations

import random

import pandas as pd

from processheal.core.detection import holdout_mask
from processheal.core.discovery import discover_model
from processheal.core.conformance import check_conformance
from processheal.hvac.events import state_only

# Pre-registered canonical alphabet (PHASE5_PLAN.md) — identity projection;
# activities a system lacks simply do not occur in its log.
CANONICAL = [
    "system_started", "system_stopped",
    "night_cycle_started", "night_cycle_ended",
    "heating_active", "heating_inactive",
    "cooling_active", "cooling_inactive",
    "economizer_window_entered", "economizer_window_exited",
]


def canonical_log(log: pd.DataFrame) -> pd.DataFrame:
    """Unit-stratum state events restricted to the canonical alphabet."""
    u = state_only(log)
    return u[u["activity"].isin(CANONICAL)].reset_index(drop=True)


def canonical_day_counts(log: pd.DataFrame,
                         all_days: list[str] | None = None) -> pd.DataFrame:
    """Per-day canonical counts. ``all_days`` = the RAW calendar (rule L6:
    the day universe must never derive from the event log — a scheduled day
    with zero canonical events is a row of zeros, which min-bands then
    judge; the audit found 9 SDAHU holdout days silently vanishing)."""
    c = canonical_log(log)
    if c.empty and not all_days:
        return pd.DataFrame()
    m = (c.groupby(["case_id", "activity"]).size().unstack(fill_value=0)
         if not c.empty else pd.DataFrame())
    m = m.reindex(columns=CANONICAL, fill_value=0)
    if all_days:
        m = m.reindex(pd.Index(sorted(all_days)), fill_value=0)
    return m


def split_train_holdout(log: pd.DataFrame, holdout_days_per_month: int):
    hold = holdout_mask(log["case_id"], holdout_days_per_month)
    return log[~hold].reset_index(drop=True), log[hold].reset_index(drop=True)


def fitness_distribution(per_day: pd.DataFrame) -> dict:
    f = per_day["fitness"]
    return {
        "n": int(len(f)),
        "mean": round(float(f.mean()), 4),
        "median": round(float(f.median()), 4),
        "p10": round(float(f.quantile(0.10)), 4),
        "frac_perfect": round(float((f >= 0.9999).mean()), 4),
    }


def shuffle_within_traces(log: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Configuration-model null: permute activity labels WITHIN each trace —
    per-day counts identical, order destroyed."""
    rng = random.Random(seed)
    out = log.copy().reset_index(drop=True)
    for _, idx in out.groupby("case_id").groups.items():
        acts = out.loc[idx, "activity"].tolist()
        rng.shuffle(acts)
        out.loc[idx, "activity"] = acts
    return out


def count_bands(train_counts: pd.DataFrame, min_seen_frac: float = 0.05) -> dict:
    """Two-sided per-activity daily count bands from TRAIN days (Phase-4
    machinery, canonical alphabet)."""
    seen = (train_counts > 0).mean()
    return {a: (float(train_counts[a].min()), float(train_counts[a].max()))
            for a in train_counts.columns if seen.get(a, 0) >= min_seen_frac}


def band_violation_days(counts: pd.DataFrame, bands: dict) -> pd.Series:
    """Bool per day: any monitored activity outside the band (missing
    activity = 0 count, judged against the band two-sidedly)."""
    if counts.empty or not bands:
        return pd.Series(dtype=bool)
    m = counts.reindex(columns=list(bands), fill_value=0)
    lo = pd.Series({k: v[0] for k, v in bands.items()})
    hi = pd.Series({k: v[1] for k, v in bands.items()})
    return (m.lt(lo, axis=1) | m.gt(hi, axis=1)).any(axis=1)


def wasserstein1(a: pd.Series, b: pd.Series) -> float:
    """Exact 1-Wasserstein distance (scipy; the 99-quantile approximation
    underestimated by up to 3.9% — audit M3 finding)."""
    from scipy.stats import wasserstein_distance
    return float(wasserstein_distance(a.values, b.values))


def log_profile_distance(counts_a: pd.DataFrame, counts_b: pd.DataFrame,
                         activities: list[str] | None = None) -> float:
    """M3: mean per-activity W1 distance between daily-count distributions.
    ``activities`` restricts the comparison (audit: the all-10 version mixes
    alphabet PRESENCE with behaviour; report shared-alphabet alongside)."""
    acts = activities or [a for a in CANONICAL
                          if a in counts_a.columns and a in counts_b.columns]
    if not acts:
        return float("nan")
    return round(sum(wasserstein1(counts_a[a], counts_b[a]) for a in acts) / len(acts), 4)
