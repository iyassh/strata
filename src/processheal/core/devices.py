"""Stratum D — device lifecycle models (Phase 3c).

Case = (day x device instance). Lifecycle events are normalized to their
CLASS TEMPLATE (zone_fan_S_started -> zone_fan_started) so healthy traces
POOL across identical instances: one discovered model per device class,
4x the training data, conformance scored PER INSTANCE so diagnosis keeps
the zone.

Two channels come out of this stratum:

1. device conformance — alignment fitness of each (day, device) trace
   against the pooled healthy class model, threshold calibrated on held-out
   healthy cases (same blind protocol as every other channel).
2. absence rate — the fraction of scheduled days a device emits ZERO
   lifecycle events. Order-only conformance cannot see missing-OPTIONAL
   behaviour (the PFPU lesson, RESEARCH_LOG L6/D4); a device that stops
   living its lifecycle entirely is invisible to alignment because its
   empty trace never enters the log. Counting the silence is the honest
   detector for that failure mode — calibrated against the device's own
   healthy silence rate (some devices are legitimately quiet: an interior-
   zone parallel fan barely runs).

Design honesty, pre-registered: pooled lifecycle alphabets are tiny (2-4
activities, loop-heavy), so the discovered class nets are expected to be
permissive; the matched-rules falsifiers from the v2 spec apply to THIS
stratum exactly as they did to the unit stratum, and the Phase-4 frequency
check is the designed upgrade for rate-shaped deviations.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from processheal.core.splits import holdout_mask

# pm4py (AGPL) enters only through discovery/conformance — imported lazily
# inside the functions that need them so the MIT-clean channel path
# (frequency imports device_log from here) never loads it (LICENSING-NOTES).
from processheal.hvac.events import device_state_only
from processheal.io.config import Config


def device_templates(cfg: Config) -> dict[str, str]:
    """Map every device-stratum event name to (template_activity, device).

    The template strips the zone token carried in the rule's ``device:`` tag
    (TU_S -> S): zone_fan_S_started -> zone_fan_started.
    """
    out: dict[str, tuple[str, str]] = {}
    for name, r in cfg.rules["events"].items():
        dev = r.get("device")
        if not dev or r.get("stratum") != "device":
            continue
        zone = dev.split("_")[-1]
        for key in ("on_event", "off_event", "enter_event", "exit_event"):
            if key in r:
                e = r[key]
                tpl = e.replace(f"_{zone}_", "_") if f"_{zone}_" in e else (
                    e[: -len(f"_{zone}")] if e.endswith(f"_{zone}") else e
                )
                out[e] = (tpl, dev)
    return out


def device_log(log: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Device-stratum state events as pooled day-x-device cases."""
    d = device_state_only(log)
    if d.empty:
        return pd.DataFrame(columns=["case_id", "activity", "timestamp", "device"])
    tpl = device_templates(cfg)
    d = d[d["activity"].isin(tpl)].copy()
    mapped = d["activity"].map(tpl)
    d["activity"] = mapped.str[0]
    d["device"] = mapped.str[1]
    d["case_id"] = d["case_id"] + "__" + d["device"]
    return d[["case_id", "activity", "timestamp", "device"]].reset_index(drop=True)


@dataclass
class DeviceDetector:
    net: object
    im: object
    fm: object
    threshold: float
    n_train_cases: int
    holdout_per_case: pd.DataFrame
    healthy_absence: dict[str, float]  # device -> healthy fraction of scheduled days silent

    @property
    def holdout_fpr(self) -> float:
        return float((self.holdout_per_case["fitness"] < self.threshold).mean())


def build_device_detector(
    cfg: Config, healthy_log: pd.DataFrame, healthy_scheduled_days: list[str]
) -> DeviceDetector | None:
    """Pooled discovery on TRAIN day-device cases; threshold from holdout cases;
    healthy absence rate per device from the full healthy year."""
    dlog = device_log(healthy_log, cfg)
    if dlog.empty:
        return None
    d = cfg.rules["detection"]
    hold = holdout_mask(dlog["case_id"], d["holdout_days_per_month"])
    train, hold_log = dlog[~hold].reset_index(drop=True), dlog[hold].reset_index(drop=True)

    from processheal.core.conformance import check_conformance
    from processheal.core.discovery import discover_model

    net, im, fm = discover_model(train[["case_id", "activity", "timestamp"]])
    conf = check_conformance(hold_log[["case_id", "activity", "timestamp"]], net, im, fm)
    threshold = float(conf["per_day"]["fitness"].quantile(d["fpr_quantile"]))

    # absence baselines from TRAIN days only (audit E: calibration must not
    # see holdout); holdout silence kept separately as the validation count
    hold_days = set(pd.Series(healthy_scheduled_days)[
        holdout_mask(pd.Series(healthy_scheduled_days), d["holdout_days_per_month"])])
    train_days = [x for x in healthy_scheduled_days if x not in hold_days]
    devices = sorted(dlog["device"].unique())
    absence, absence_holdout_fp = {}, {}
    for dev in devices:
        active_days = set(dlog.loc[dlog["device"] == dev, "case_id"].str.split("__").str[0])
        absence[dev] = (sum(1 for x in train_days if x not in active_days)
                        / max(len(train_days), 1))
        absence_holdout_fp[dev] = [sum(1 for x in hold_days if x not in active_days),
                                   len(hold_days)]

    det = DeviceDetector(
        net=net, im=im, fm=fm, threshold=threshold,
        n_train_cases=train["case_id"].nunique(),
        holdout_per_case=conf["per_day"],
        healthy_absence=absence,
    )
    det.absence_holdout_fp = absence_holdout_fp
    return det


def classify_device_days(det: DeviceDetector, log: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Per (day, device): conformance flag. Returns day, device, fitness, flagged."""
    dlog = device_log(log, cfg)
    if dlog.empty:
        return pd.DataFrame(columns=["day", "device", "fitness", "flagged"])
    from processheal.core.conformance import check_conformance

    conf = check_conformance(dlog[["case_id", "activity", "timestamp"]], det.net, det.im, det.fm)
    per = conf["per_day"].copy()
    parts = per["case_id"].str.split("__")
    per["day"], per["device"] = parts.str[0], parts.str[1]
    per["flagged"] = per["fitness"] < det.threshold
    return per[["day", "device", "fitness", "flagged"]]


def absence_days(
    det: DeviceDetector, log: pd.DataFrame, cfg: Config, scheduled_days: list[str]
) -> pd.DataFrame:
    """Per device: which scheduled days had ZERO lifecycle events.

    Returns day-device silence flags; significance against the device's own
    healthy silence rate is the benchmark's job (same binomial machinery as
    every other channel).
    """
    dlog = device_log(log, cfg)
    rows = []
    for dev, healthy_rate in det.healthy_absence.items():
        active = set(dlog.loc[dlog["device"] == dev, "case_id"].str.split("__").str[0])
        for day in scheduled_days:
            rows.append((day, dev, day not in active, healthy_rate))
    return pd.DataFrame(rows, columns=["day", "device", "silent", "healthy_rate"])


def pooling_homogeneity(det: DeviceDetector) -> dict:
    """Are the pooled instances behaviourally alike in health? (The design
    justification for pooling: identical units under one control sequence are
    one behavioural population. Trace-clustering literature says pooling
    heterogeneous populations harms discovery — so we verify, per system,
    that each device's held-out healthy fitness is indistinguishable from
    the pool. Descriptive check + a conservative flag; formal paired tests
    arrive with the Phase-4 statistics battery.)"""
    per = det.holdout_per_case.copy()
    per["device"] = per["case_id"].str.split("__").str[1]
    by = per.groupby("device")["fitness"]
    stats = {d: {"n": int(g.count()), "mean": float(g.mean()), "std": float(g.std() or 0)}
             for d, g in by}
    # Kruskal-Wallis H against the chi-square critical value (df = groups-1,
    # p = 0.01). Rank-based, dependency-free; the earlier mean-range heuristic
    # said "homogeneous" for a distribution the KW test rejects at p ~ 4e-20
    # (PFPU) — audit finding F. Ties make H slightly conservative; noted.
    ranked = per["fitness"].rank()
    n_total = len(per)
    h_stat = 0.0
    for _, g in per.assign(_r=ranked).groupby("device"):
        r_mean = float(g["_r"].mean())
        h_stat += len(g) * (r_mean - (n_total + 1) / 2.0) ** 2
    h_stat *= 12.0 / (n_total * (n_total + 1))
    crit = {1: 6.63, 2: 9.21, 3: 11.34, 4: 13.28}.get(len(stats) - 1, 13.28)
    return {"per_device": stats,
            "kruskal_wallis_h": round(h_stat, 2),
            "critical_value_p01": crit,
            "homogeneous": bool(h_stat < crit)}
