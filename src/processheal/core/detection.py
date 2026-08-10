"""Temporal-split fault detector.

Fixes the audit's central benchmark flaws:

- The model is discovered ONLY from training days; the detection threshold is
  CALIBRATED on held-out healthy days the model never saw (no hand-picked
  margin, no train=test tautology).
- The unit of evaluation is the day (one trace), not the year-file, so metrics
  come with real statistical power.

The split is calendar-stratified: the last ``holdout_days_per_month`` days of
each month are held out, keeping every season represented on both sides.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from processheal.core.conformance import check_conformance
from processheal.core.discovery import discover_model
from processheal.hvac.events import state_only
from processheal.io.config import Config


def holdout_mask(case_ids: pd.Series, holdout_days_per_month: int) -> pd.Series:
    """True for day-cases in the last N days of their month."""
    dates = pd.to_datetime(case_ids)
    return dates.dt.day > (dates.dt.days_in_month - holdout_days_per_month)


@dataclass
class Detector:
    net: object
    im: object
    fm: object
    threshold: float
    n_train_days: int
    holdout_per_day: pd.DataFrame  # held-out healthy per-day fitness

    @property
    def holdout_fpr(self) -> float:
        return float((self.holdout_per_day["fitness"] < self.threshold).mean())


def build_detector(cfg: Config, healthy_log: pd.DataFrame) -> Detector:
    """Discover on train days; calibrate the per-day threshold on held-out days.

    Alphabet split (STRATA v2): the model channel is state-events-only, end to
    end. Discovery, calibration and classification all run on the state slice,
    so the discovered model can never re-encode the signature rules.
    """
    healthy_log = state_only(healthy_log)
    d = cfg.rules["detection"]
    hold = holdout_mask(healthy_log["case_id"], d["holdout_days_per_month"])

    train_log = healthy_log[~hold].reset_index(drop=True)
    hold_log = healthy_log[hold].reset_index(drop=True)

    net, im, fm = discover_model(train_log)
    hold_conf = check_conformance(hold_log, net, im, fm)
    threshold = float(hold_conf["per_day"]["fitness"].quantile(d["fpr_quantile"]))

    return Detector(
        net=net,
        im=im,
        fm=fm,
        threshold=threshold,
        n_train_days=train_log["case_id"].nunique(),
        holdout_per_day=hold_conf["per_day"],
    )


def classify_days(detector: Detector, event_log: pd.DataFrame) -> pd.DataFrame:
    """Per-day fitness + flagged verdict for an event log (the ONE detection rule).

    Scores the state-alphabet slice only: signature events belong to the rules
    channel and must not influence model fitness.
    """
    conf = check_conformance(state_only(event_log), detector.net, detector.im, detector.fm)
    per_day = conf["per_day"].copy()
    per_day["flagged"] = per_day["fitness"] < detector.threshold
    per_day.attrs["unexpected_by_activity"] = conf["unexpected_by_activity"]
    per_day.attrs["missing_by_activity"] = conf["missing_by_activity"]
    return per_day
