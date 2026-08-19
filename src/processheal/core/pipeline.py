"""The STRATA detector facade (Phase 9 / T3): fit on fault-free data, score
anything — the deployable pipeline lifted out of scripts/benchmark.py.

    from processheal.core.pipeline import fit, day_universe
    det = fit(cfg, healthy_df)          # trains + calibrates every channel
    day = det.score(new_df)             # per-day flags per channel
    rep = det.evaluate(new_df)          # + significance gates, deployed union,
                                        #   TTD, channel report

Design rules carried from the audits:
- The DEPLOYED union excludes the seasonal rate channel (diagnostic-only,
  Phase 6 / L23); rate results are reported separately as corroboration.
- Day universe comes from the raw calendar, never the event log (L6/L22).
- The model/device thresholds are quantile-fit on the calibration holdout;
  their healthy-holdout FP is a CALIBRATION TARGET, not an out-of-sample
  measurement (L24) — carried in `provenance` until the three-way
  discover/calibrate/test split lands.
- pm4py (AGPL) is imported LAZILY: without it, the model and device
  conformance strata are disabled with a warning and every other channel
  works — the MIT-clean core path (LICENSING-NOTES.md).

Regression contract: on the LBNL healthy years, score() must reproduce the
per-channel healthy-holdout FP counts committed in outputs/union_fpr_*.json
(guarded by tests/test_pipeline_facade.py).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from processheal.core.splits import holdout_mask
from processheal.core.frequency import (
    _flag_matrix,
    build_frequency_detector,
    build_rate_detector_monthly,
    classify_frequency_days,
    classify_rate_days_monthly,
    device_day_counts,
    unit_day_counts,
)
from processheal.core.oscillation import build_oscillation_detector, daily_direction_changes
from processheal.core.residuals import calibrate_band, daily_residual_scores, flag_days
from processheal.hvac.events import abstract_events, event_alphabet_map, event_device_map
from processheal.io.config import Config

DEFAULT_RESIDUAL_RULE = "supply_air_residual"
DEPLOYED_CHANNELS = ("rules", "residual", "model", "device", "absence",
                     "frequency", "oscillation")  # rate is diagnostic-only


def day_universe(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Raw-calendar day universe with occupied minutes (L6: never from the
    event log). Mirrors scripts/benchmark.py day_universe exactly."""
    w = df.rename(columns={v: k for k, v in cfg.sensors.items()})
    day = w["Datetime"].dt.date.astype(str)
    occ = w["OCCUPIED"] > 0
    diffs = w["Datetime"].diff().dropna().dt.total_seconds() / 60.0
    interval = float(diffs.median()) if len(diffs) else 1.0
    uni = (pd.DataFrame({"case_id": day, "occ": occ})
           .groupby("case_id")["occ"].sum() * interval)
    return uni.rename("occupied_min").to_frame()


@dataclass
class StrataDetector:
    """Everything fit() calibrated, plus the noise floors evaluate() needs."""

    cfg: Config
    signature_events: set[str]
    residual_bands: dict[str, tuple[float, float]]
    residual_holdout: tuple[int, int]            # (fp, evaluable holdout days)
    freq_unit: Any
    freq_dev: Any
    rate_det: dict | None
    osc_det: Any
    unit_model: Any = None                       # None when pm4py absent
    device_model: Any = None
    model_holdout: tuple[int, int] = (0, 0)      # (fp, holdout days)
    device_case_stats: tuple[int, int, int] = (0, 0, 0)  # (case fp, cases, n devices)
    healthy_sched: list[str] = field(default_factory=list)
    provenance: dict[str, str] = field(default_factory=dict)

    # ---- scoring -----------------------------------------------------------

    def score(self, df: pd.DataFrame) -> dict[str, Any]:
        """Per-day channel flags on arbitrary data. Returns dict with the day
        universe, one boolean Series per channel, and diagnosis maps."""
        cfg = self.cfg
        uni = day_universe(df, cfg)
        days = uni.index
        log = abstract_events(df, cfg)
        has_events = pd.Series([d in set(log["case_id"]) for d in days], index=days)
        uni["evaluable"] = has_events | (uni["occupied_min"] > 0)

        sig = log[log["activity"].isin(self.signature_events)]
        rules = pd.Series([d in set(sig["case_id"]) for d in days], index=days)

        res_flag = pd.Series(False, index=days)
        res_eval = pd.Series(False, index=days)
        margin = cfg.rules["detection"].get("residual_min_exceedance", 0.0)
        for rname, band in self.residual_bands.items():
            rs = daily_residual_scores(df, cfg, rule_name=rname)
            if rs.empty:
                continue
            rf = flag_days(rs, band, min_margin=margin).set_index("case_id")
            res_flag = res_flag | rf["flagged"].reindex(days).fillna(False)
            res_eval = res_eval | rf["evaluable"].reindex(days).fillna(False)

        osc_flag = pd.Series(False, index=days)
        if self.osc_det is not None:
            oc = daily_direction_changes(df, cfg)
            if not oc.empty:
                om = _flag_matrix(oc, self.osc_det.bands).any(axis=1)
                om.index = oc.index.astype(str)
                osc_flag = osc_flag | om.reindex(days).fillna(False)

        model = pd.Series(False, index=days)
        dev_flag = pd.Series(False, index=days)
        abs_flag = pd.Series(False, index=days)
        dev_by_device: dict[str, int] = {}
        dev_days_map: dict[str, list] = {}
        abs_by_device: dict[str, tuple[int, int, float]] = {}
        if self.unit_model is not None:
            from processheal.core.detection import classify_days

            per_day = classify_days(self.unit_model, log)
            model = per_day.set_index("case_id")["flagged"].reindex(days).fillna(False)
        model = model | (~has_events & (uni["occupied_min"] > 0))
        if self.device_model is not None:
            from processheal.core.devices import absence_days, classify_device_days

            per_dev = classify_device_days(self.device_model, log, cfg)
            if len(per_dev):
                fl = per_dev[per_dev["flagged"]]
                dev_flag = dev_flag | pd.Series(days.isin(set(fl["day"])), index=days)
                dev_by_device = {d: int(n) for d, n in
                                 fl.groupby("device")["day"].nunique().items()}
                dev_days_map = {d: sorted(set(g["day"])) for d, g in fl.groupby("device")}
            sched = [d for d in days if uni.loc[d, "occupied_min"] > 0]
            ab = absence_days(self.device_model, log, cfg, sched)
            rare = ab[(ab["silent"]) & (ab["healthy_rate"] <= 0.05)]
            abs_flag = abs_flag | pd.Series(days.isin(set(rare["day"])), index=days)
            abs_by_device = {dev: (int(g["silent"].sum()), len(g),
                                   float(g["healthy_rate"].iloc[0]))
                             for dev, g in ab.groupby("device")}

        freq_flag = pd.Series(False, index=days)
        if self.freq_unit is not None:
            fu = classify_frequency_days(self.freq_unit, unit_day_counts(log)).set_index("day")
            freq_flag = freq_flag | fu["flagged"].reindex(days).fillna(False)
        if self.freq_dev is not None:
            fd = classify_frequency_days(self.freq_dev,
                                         device_day_counts(log, cfg)).set_index("day")
            freq_flag = freq_flag | fd["flagged"].reindex(days).fillna(False)

        rate_flag = pd.Series(False, index=days)
        if self.rate_det is not None:
            rr = classify_rate_days_monthly(self.rate_det, unit_day_counts(log))
            if len(rr):
                rr = rr.set_index("day")
                rate_flag = rate_flag | rr["flagged"].reindex(days).fillna(False)

        # X3 localization: top-firing device among signature events
        top_device = None
        if len(sig):
            dev_map = event_device_map(cfg)
            dd = sig.assign(dev=sig["activity"].map(dev_map)).dropna(subset=["dev"])
            if len(dd):
                counts = dd.groupby("dev")["case_id"].nunique()
                top_device = str(counts.idxmax())

        channels = {"rules": rules, "residual": res_flag, "model": model,
                    "device": dev_flag, "absence": abs_flag, "frequency": freq_flag,
                    "oscillation": osc_flag}
        deployed = pd.Series(False, index=days)
        for name in DEPLOYED_CHANNELS:
            deployed = deployed | channels[name]
        return {"universe": uni, "channels": channels,
                "rate_diagnostic": rate_flag, "deployed_union": deployed,
                "residual_evaluable": res_eval,
                "device_days_by_device": dev_by_device,
                "device_days_map": dev_days_map,
                "absence_by_device": abs_by_device,
                "top_device": top_device,
                "signature_log": sig}

    # ---- significance-gated evaluation --------------------------------------

    def evaluate(self, df: pd.DataFrame) -> dict[str, Any]:
        """score() + the per-channel significance gates + deployed verdict."""
        from processheal.core import significance as S

        s = self.score(df)
        uni = s["universe"]
        n_eval = int(uni["evaluable"].sum())
        c = {k: int(v.sum()) for k, v in s["channels"].items()}
        n_win = int(s["residual_evaluable"].sum())

        sig: dict[str, bool] = {
            "rules": S.rules_significant(c["rules"], n_eval),
            "residual": S.residual_significant(c["residual"], n_win,
                                               *self.residual_holdout),
            "frequency": (self.freq_unit is not None
                          and S.frequency_significant(
                              c["frequency"], n_eval,
                              self.freq_unit.holdout_fp_days, self.freq_unit.holdout_days,
                              getattr(self.freq_dev, "holdout_fp_days", 0),
                              getattr(self.freq_dev, "holdout_days", 0))),
            "oscillation": (self.osc_det is not None
                            and S.oscillation_significant(
                                c["oscillation"], n_eval,
                                self.osc_det.holdout_fp_days, self.osc_det.holdout_days)),
        }
        sig["model"] = (self.unit_model is not None
                        and S.model_significant(c["model"], n_eval, *self.model_holdout))
        sig_dev, sig_devices = (False, [])
        if self.device_model is not None and s["device_days_by_device"]:
            case_fp, case_n, n_dev = self.device_case_stats
            sig_dev, sig_devices = S.device_significant(
                s["device_days_by_device"], n_eval, case_fp, case_n, n_dev)
        sig["device"] = sig_dev
        sig["absence"] = S.absence_significant(s["absence_by_device"])

        meaningful = [k for k in DEPLOYED_CHANNELS if sig.get(k)]
        # TTD from significant channels only (audit G) — and for the device
        # channel, only the SIGNIFICANT devices' days (benchmark.py:380-384:
        # a noise day from an insignificant sibling must not set TTD)
        sig_union = pd.Series(False, index=uni.index)
        for name in meaningful:
            if name == "device":
                sig_days = [d for dv in sig_devices
                            for d in s["device_days_map"].get(dv, [])]
                sig_union = sig_union | pd.Series(uni.index.isin(sig_days),
                                                  index=uni.index)
            else:
                sig_union = sig_union | s["channels"][name]
        ttd = None
        for i, d in enumerate(uni.index, start=1):
            if bool(sig_union.get(d, False)):
                ttd = i
                break

        # rate: diagnostic corroboration only
        decision_days = [d for i, d in enumerate(uni.index) if i % 30 == 29]
        k_rate = int(sum(bool(s["rate_diagnostic"].get(d, False)) for d in decision_days))
        rate_corroborates = (self.rate_det is not None
                             and S.rate_significant(
                                 k_rate, len(decision_days),
                                 self.rate_det["holdout_fp_days"],
                                 self.rate_det["holdout_days"]))

        return {**s, "counts": c, "significant": sig,
                "meaningful_channels": meaningful, "detected": bool(meaningful),
                "ttd_days": ttd, "significant_devices": sig_devices,
                "rate_corroborates": rate_corroborates,
                "provenance": self.provenance}


def fit(cfg: Config, healthy_df: pd.DataFrame,
        residual_rule: str = DEFAULT_RESIDUAL_RULE) -> StrataDetector:
    """Train and calibrate every channel on a fault-free year. Mirrors the
    audited scripts/benchmark.py setup exactly (regression-guarded)."""
    log = abstract_events(healthy_df, cfg)
    uni = day_universe(healthy_df, cfg)
    sched = [d for d in uni.index if uni.loc[d, "occupied_min"] > 0]
    hold_n = cfg.rules["detection"]["holdout_days_per_month"]

    signature = {e for e, a in event_alphabet_map(cfg).items()
                 if a == "signature"} - {residual_rule}

    # residual channels: train-only bands + holdout noise floor
    res_channels = cfg.rules["detection"].get("residual_channels", [residual_rule])
    bands: dict[str, tuple[float, float]] = {}
    min_w = cfg.rules["detection"].get("residual_min_band_width", 0.0)
    margin = cfg.rules["detection"].get("residual_min_exceedance", 0.0)
    res_fp = res_hold = 0
    for rname in res_channels:
        rh = daily_residual_scores(healthy_df, cfg, rule_name=rname)
        if rh.empty:
            continue
        hmask = holdout_mask(rh["case_id"], hold_n)
        bands[rname] = calibrate_band(rh, ~hmask, min_width=min_w)
        hf = flag_days(rh[hmask.values], bands[rname], min_margin=margin)
        res_fp += int(hf["flagged"].sum())
        res_hold += int(hf["evaluable"].sum())

    freq_unit = build_frequency_detector(unit_day_counts(log), hold_n)
    freq_dev = build_frequency_detector(device_day_counts(log, cfg), hold_n)
    rate_det = build_rate_detector_monthly(unit_day_counts(log), hold_n, window=30)
    osc_det = build_oscillation_detector(healthy_df, cfg)

    unit_model = device_model = None
    model_holdout = (0, 0)
    device_case_stats = (0, 0, 0)
    provenance = {ch: "train-only thresholds; holdout out-of-sample"
                  for ch in ("rules", "residual", "frequency", "oscillation", "rate",
                             "absence")}
    try:
        from processheal.core.detection import build_detector
        from processheal.core.devices import build_device_detector

        unit_model = build_detector(cfg, log)
        model_holdout = (int((unit_model.holdout_per_day["fitness"]
                              < unit_model.threshold).sum()),
                         len(unit_model.holdout_per_day))
        device_model = build_device_detector(cfg, log, sched)
        if device_model is not None:
            device_case_stats = (
                int((device_model.holdout_per_case["fitness"]
                     < device_model.threshold).sum()),
                len(device_model.holdout_per_case),
                max(len(device_model.healthy_absence), 1))
        provenance["model"] = provenance["device"] = (
            "holdout-quantile threshold: healthy-holdout FP is the calibration "
            "target, not out-of-sample (L24; three-way split pending)")
    except ImportError:
        warnings.warn(
            "pm4py not installed: model and device conformance strata are "
            "DISABLED; rules/residual/frequency/oscillation/absence channels "
            "run normally. Install extras for discovery (LICENSING-NOTES.md: "
            "pm4py is AGPL-3.0).", stacklevel=2)
        provenance["model"] = provenance["device"] = "disabled (pm4py not installed)"

    return StrataDetector(
        cfg=cfg, signature_events=signature, residual_bands=bands,
        residual_holdout=(res_fp, res_hold), freq_unit=freq_unit,
        freq_dev=freq_dev, rate_det=rate_det, osc_det=osc_det,
        unit_model=unit_model, device_model=device_model,
        model_holdout=model_holdout, device_case_stats=device_case_stats,
        healthy_sched=sched, provenance=provenance)


__all__ = ["StrataDetector", "fit", "day_universe", "DEPLOYED_CHANNELS"]
