"""Benchmark v6 — cross-system, per-scenario, blind-calibrated (Phase 3b).

All v5 protocol fixes retained (G1-G7; see GAP_ANALYSIS_AUG2026.md), now
parameterized over buildings: config + data + scenario manifest per system,
zero code difference between systems.

    uv run python scripts/benchmark.py sdahu
    uv run python scripts/benchmark.py pfpu
    uv run python scripts/benchmark.py sfpu

New in v6: zone localization scoring (X3). For systems with a week-0 zone
ground truth, each detected scenario's rules-channel events are grouped by
their device tag; localization is correct when the top-firing device matches
the audited injection zone. INDETERMINATE scenarios are excluded from
localization scoring (never force-labeled).

Negative-evidence honesty: within-system independent negatives do NOT exist
for any LBNL system (SDAHU's oa_bias relabel is overturned; each FPU system
has exactly one FaultFree year, which is the calibration file). False-alarm
evidence = held-out healthy days only, stated on every output.
"""

import os
import sys

os.environ["TQDM_DISABLE"] = "1"

import hashlib
import json
import warnings
from pathlib import Path

import pandas as pd
import yaml

warnings.filterwarnings("ignore")

from processheal.core import significance as S
from processheal.core.detection import build_detector, classify_days, holdout_mask
from processheal.core.devices import (absence_days, build_device_detector,
                                       classify_device_days, pooling_homogeneity)
from processheal.core.oscillation import build_oscillation_detector, daily_direction_changes
from processheal.core.frequency import _flag_matrix
from processheal.core.frequency import (build_frequency_detector, build_rate_detector_monthly,
                                        classify_frequency_days, classify_rate_days_monthly,
                                        device_day_counts, unit_day_counts)
from processheal.core.residuals import calibrate_band, daily_residual_scores, flag_days
from processheal.hvac.events import abstract_events, event_alphabet_map, event_device_map
from processheal.io.config import load_config

SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "sdahu"
CONFIG_DIR = f"configs/lbnl_{SYSTEM}"
DATA = Path(f"data/processed/{SYSTEM}")
RESIDUAL_RULE = "supply_air_residual"

cfg = load_config(CONFIG_DIR)
manifest = yaml.safe_load(Path(f"{CONFIG_DIR}/scenarios.yaml").read_text())
HEALTHY_FILE = manifest["healthy_file"]
SCENARIOS = manifest["scenarios"]
SIGNATURE_EVENTS = {
    e for e, a in event_alphabet_map(cfg).items() if a == "signature"
} - {RESIDUAL_RULE}
DEVICE_OF = event_device_map(cfg)

# zone ground truth (X3), if the week-0 audit covered this system
_gt_path = Path("outputs/week0_audit.json")
GROUND_TRUTH = {}
if _gt_path.exists():
    GROUND_TRUTH = json.loads(_gt_path.read_text()).get("zone_ground_truth", {})


def day_universe(df: pd.DataFrame) -> pd.DataFrame:
    w = df.rename(columns={v: k for k, v in cfg.sensors.items()})
    day = w["Datetime"].dt.date.astype(str)
    occ = w["OCCUPIED"] > 0  # any scheduled operation (incl. night-cycle)
    diffs = w["Datetime"].diff().dropna().dt.total_seconds() / 60.0
    interval = float(diffs.median()) if len(diffs) else 1.0
    uni = pd.DataFrame({"case_id": day, "occ": occ}).groupby("case_id")["occ"].sum() * interval
    return uni.rename("occupied_min").reset_index()


def evaluate(fname: str):
    df = pd.read_parquet(DATA / f"{fname}.parquet")
    uni = day_universe(df).set_index("case_id")
    log = abstract_events(df, cfg)
    log_hash = hashlib.md5(
        log[["case_id", "activity"]].to_csv(index=False).encode()
    ).hexdigest()[:8]

    days = uni.index
    has_events = pd.Series([d in set(log["case_id"]) for d in days], index=days)
    uni["evaluable"] = has_events | (uni["occupied_min"] > 0)

    sig = log[log["activity"].isin(SIGNATURE_EVENTS)]
    sig_days = set(sig["case_id"])
    rules = pd.Series([d in sig_days for d in days], index=days)

    per_day = classify_days(det, log)
    model = per_day.set_index("case_id")["flagged"].reindex(days).fillna(False)
    model = model | (~has_events & (uni["occupied_min"] > 0))
    # min-robust model count: days STRICTLY worse than the worst healthy
    # holdout day (immune to the interpolated-threshold artifact, audit 1b)
    strict = float(det.holdout_per_day["fitness"].min())
    minrob = per_day[per_day["fitness"] < strict]["case_id"]
    model_minrobust = int(len(set(minrob)))

    res_flag = pd.Series(False, index=days)
    res_eval = pd.Series(False, index=days)
    for rname, band_r in RES.items():
        rs = daily_residual_scores(df, cfg, rule_name=rname)
        if rs.empty:
            continue
        rf = flag_days(rs, band_r,
                       min_margin=cfg.rules["detection"].get("residual_min_exceedance", 0.0)
                       ).set_index("case_id")
        res_flag = res_flag | rf["flagged"].reindex(days).fillna(False)
        res_eval = res_eval | rf["evaluable"].reindex(days).fillna(False)
    osc_flag = pd.Series(False, index=days)
    if osc_det is not None:
        oc = daily_direction_changes(df, cfg)
        if not oc.empty:
            om = _flag_matrix(oc, osc_det.bands).any(axis=1)
            om.index = oc.index.astype(str)
            osc_flag = osc_flag | om.reindex(days).fillna(False)

    # device stratum: pooled-model conformance per instance + absence channel
    dev_flag = pd.Series(False, index=days)
    abs_flag = pd.Series(False, index=days)
    top_dev_channel, dev_case_days, abs_days_sig = None, 0, {}
    dev_by_device: dict[str, int] = {}
    dev_days_map: dict[str, list] = {}
    if dev_det is not None:
        per_dev = classify_device_days(dev_det, log, cfg)
        if len(per_dev):
            fl = per_dev[per_dev["flagged"]]
            dev_case_days = int(len(fl))
            dev_flag = dev_flag | pd.Series(days.isin(set(fl["day"])), index=days)
            if len(fl):
                dev_by_device = {d_: int(n) for d_, n in
                                 fl.groupby("device")["day"].nunique().items()}
                dev_days_map = {d_: sorted(set(g["day"])) for d_, g in fl.groupby("device")}
                top_dev_channel = max(dev_by_device, key=dev_by_device.get)
        sched = [d for d in days if uni.loc[d, "occupied_min"] > 0]
        ab = absence_days(dev_det, log, cfg, sched)
        # a silent day flags only for devices whose healthy silence is rare
        rare = ab[(ab["silent"]) & (ab["healthy_rate"] <= 0.05)]
        abs_flag = abs_flag | pd.Series(days.isin(set(rare["day"])), index=days)
        abs_days_sig = {dev: [int(g["silent"].sum()), len(g), float(g["healthy_rate"].iloc[0])]
                        for dev, g in ab.groupby("device")}

    # frequency channels (Phase 4): per-day count-bands + seasonal rate
    freq_flag = pd.Series(False, index=days)
    freq_viol: dict[str, int] = {}
    if freq_unit is not None:
        fu = classify_frequency_days(freq_unit, unit_day_counts(log)).set_index("day")
        freq_flag = freq_flag | fu["flagged"].reindex(days).fillna(False)
        for v in fu.loc[fu["flagged"], "violations"]:
            for k in v:
                freq_viol[k] = freq_viol.get(k, 0) + 1
    if freq_dev is not None:
        fd = classify_frequency_days(freq_dev, device_day_counts(log, cfg)).set_index("day")
        freq_flag = freq_flag | fd["flagged"].reindex(days).fillna(False)
        for v in fd.loc[fd["flagged"], "violations"]:
            for k in v:
                freq_viol[k] = freq_viol.get(k, 0) + 1
    rate_flag = pd.Series(False, index=days)
    if rate_det is not None:
        rr = classify_rate_days_monthly(rate_det, unit_day_counts(log))
        if len(rr):
            rr = rr.set_index("day")
            rate_flag = rate_flag | rr["flagged"].reindex(days).fillna(False)

    combined = rules | model | res_flag | dev_flag | abs_flag | freq_flag | rate_flag | osc_flag

    # X3: top-firing device among signature events (fire-days per device)
    top_device, loc_days = None, 0
    if len(sig):
        dev_days = sig.assign(dev=sig["activity"].map(DEVICE_OF)).dropna(subset=["dev"])
        if len(dev_days):
            counts = dev_days.groupby("dev")["case_id"].nunique().sort_values(ascending=False)
            top_device, loc_days = counts.index[0], int(counts.iloc[0])

    return {
        "uni": uni, "rules": rules, "model": model, "res_flag": res_flag,
        "res_eval": res_eval, "combined": combined, "log_hash": log_hash,
        "n_model_unique": int((model & ~rules & ~res_flag).sum()),
        "top_device": top_device, "top_device_days": loc_days,
        "model_minrobust": model_minrobust,
        "dev_flag": dev_flag, "abs_flag": abs_flag,
        "top_dev_channel": top_dev_channel, "dev_case_days": dev_case_days,
        "abs_days_sig": abs_days_sig, "dev_by_device": dev_by_device,
        "dev_days_map": dev_days_map,
        "freq_flag": freq_flag, "rate_flag": rate_flag, "freq_viol": freq_viol,
        "osc_flag": osc_flag,
    }


def ttd(flags: pd.Series, uni: pd.DataFrame) -> int | None:
    for i, d in enumerate(uni.index, start=1):
        if bool(flags.get(d, False)):
            return i
    return None


print("=" * 106)
print(f"STRATA benchmark v6 — system: {SYSTEM} — blind-calibrated channels, per-scenario reporting")
print("=" * 106)

healthy_df = pd.read_parquet(DATA / f"{HEALTHY_FILE}.parquet")
healthy_log = abstract_events(healthy_df, cfg)
det = build_detector(cfg, healthy_log)

h_uni_early = day_universe(healthy_df).set_index("case_id")
HEALTHY_SCHED = [d for d in h_uni_early.index if h_uni_early.loc[d, "occupied_min"] > 0]
dev_det = build_device_detector(cfg, healthy_log, HEALTHY_SCHED)

HOLD_N = cfg.rules["detection"]["holdout_days_per_month"]
freq_unit = build_frequency_detector(unit_day_counts(healthy_log), HOLD_N)
freq_dev = build_frequency_detector(device_day_counts(healthy_log, cfg), HOLD_N)
rate_det = build_rate_detector_monthly(unit_day_counts(healthy_log), HOLD_N, window=30)
if freq_unit:
    dev_part = (f"device bands {len(freq_dev.bands)} "
                f"(FP {freq_dev.holdout_fp_days}/{freq_dev.holdout_days})"
                if freq_dev else "device bands n/a")
    print(f"frequency channel: unit bands {len(freq_unit.bands)} "
          f"(holdout FP {freq_unit.holdout_fp_days}/{freq_unit.holdout_days}), " + dev_part)
else:
    print("frequency channel: n/a")
if rate_det:
    print(f"rate channel (30d, seasonal): holdout FP {rate_det['holdout_fp_days']}"
          f"/{rate_det['holdout_days']}")

RES_CHANNELS = cfg.rules["detection"].get("residual_channels", [RESIDUAL_RULE])
RES = {}
hold_fp, hold_n = 0, 0
for rname in RES_CHANNELS:
    rh = daily_residual_scores(healthy_df, cfg, rule_name=rname)
    if rh.empty:
        continue
    hmask = holdout_mask(rh["case_id"], cfg.rules["detection"]["holdout_days_per_month"])
    band_r = calibrate_band(rh, ~hmask,
                            min_width=cfg.rules["detection"].get("residual_min_band_width", 0.0))
    rhold = flag_days(rh[hmask], band_r,
                      min_margin=cfg.rules["detection"].get("residual_min_exceedance", 0.0))
    RES[rname] = band_r
    hold_fp += int(rhold["flagged"].sum())
    hold_n += int(rhold["evaluable"].sum())
BAND = RES.get(RESIDUAL_RULE, (0.0, 0.0))
osc_det = build_oscillation_detector(healthy_df, cfg)
if osc_det:
    print(f"oscillation channel: {len(osc_det.bands)} signals, holdout FP "
          f"{osc_det.holdout_fp_days}/{osc_det.holdout_days}")

h_uni = day_universe(healthy_df).set_index("case_id")
h_sig = set(healthy_log.loc[healthy_log["activity"].isin(SIGNATURE_EVENTS), "case_id"])
model_hold_fp = int((det.holdout_per_day["fitness"] < det.threshold).sum())

print(f"\nresidual band (TRAIN-only): [{BAND[0]:+.2f}, {BAND[1]:+.2f}] F | "
      f"holdout: {hold_fp}/{hold_n} window-days outside")
print(f"model threshold: {det.threshold:.4f} (min-calibration on {len(det.holdout_per_day)} holdout days; "
      f"holdout FP {model_hold_fp})")
print(f"rules on FULL healthy year: {len(h_sig)} signature days (computed)")
DEV_META = None
if dev_det is not None:
    homog = pooling_homogeneity(dev_det)
    DEV_META = {
        "threshold": dev_det.threshold,
        "n_train_cases": dev_det.n_train_cases,
        "holdout_cases": len(dev_det.holdout_per_case),
        "holdout_case_fp": int((dev_det.holdout_per_case["fitness"] < dev_det.threshold).sum()),
        "holdout_fitness_min": float(dev_det.holdout_per_case["fitness"].min()),
        "healthy_absence_rates": dev_det.healthy_absence,
        "absence_holdout_fp": getattr(dev_det, "absence_holdout_fp", {}),
        "pooling_homogeneity": homog,
    }
    print(f"device stratum: pooled model from {dev_det.n_train_cases} train cases; "
          f"threshold {dev_det.threshold:.4f}; holdout case FP "
          f"{DEV_META['holdout_case_fp']}/{DEV_META['holdout_cases']}; "
          f"absence rates (train-only) "
          f"{ {k: round(v, 3) for k, v in dev_det.healthy_absence.items()} }")
    print(f"  pooling homogeneity: KW H={homog['kruskal_wallis_h']} "
          f"vs crit(p=.01)={homog['critical_value_p01']} -> "
          f"{'HOMOGENEOUS' if homog['homogeneous'] else 'HETEROGENEOUS (pooling caveat applies)'}")
else:
    print("device stratum: no device-tagged rules in this config (n/a)")
print("false-alarm evidence = held-out healthy days ONLY (no independent negative exists; stated).")

rows = []
print(f"\n{'scenario':34s} {'eval':>4} "
      f"{'rules':>5} {'resid':>5} {'model':>5} {'dev':>5} {'freq':>5} {'rate':>5} "
      f"{'comb':>5} {'TTD':>4} {'locz':>10}")
print("-" * 106)

for sc in SCENARIOS:
    fname, family, label, is_fault = sc["file"], sc["family"], sc["label"], sc["is_fault"]
    excluded = bool(sc.get("exclude"))
    e = evaluate(fname)
    uni = e["uni"]
    n_days, n_eval = len(uni), int(uni["evaluable"].sum())
    n_win = int(e["res_eval"].sum())
    c = {ch: int(e[ch].sum()) for ch in ("rules", "res_flag", "model", "combined",
                                          "dev_flag", "abs_flag", "freq_flag",
                                          "rate_flag", "osc_flag")}

    # significance vs each channel's own holdout noise floor — the gate
    # math now lives in core.significance (T3 facade extraction; identical
    # formulas, regression-guarded by the byte-identical SDAHU rerun)
    sig_rules = S.rules_significant(c["rules"], n_eval)
    sig_resid = S.residual_significant(c["res_flag"], n_win, hold_fp, hold_n)
    sig_model = S.model_significant(c["model"], n_eval,
                                    model_hold_fp, len(det.holdout_per_day))
    sig_dev, sig_devices = False, []
    if dev_det is not None and e["dev_by_device"]:
        sig_dev, sig_devices = S.device_significant(
            e["dev_by_device"], n_eval,
            int((dev_det.holdout_per_case["fitness"] < dev_det.threshold).sum()),
            len(dev_det.holdout_per_case),
            len(dev_det.healthy_absence))
    sig_abs = S.absence_significant(
        {d: (k, n_, r) for d, (k, n_, r) in e["abs_days_sig"].items()})
    sig_freq = freq_unit is not None and S.frequency_significant(
        c["freq_flag"], n_eval,
        freq_unit.holdout_fp_days, freq_unit.holdout_days,
        getattr(freq_dev, "holdout_fp_days", 0),
        getattr(freq_dev, "holdout_days", 0) if freq_dev is not None else 0)
    sig_osc = osc_det is not None and S.oscillation_significant(
        c["osc_flag"], n_eval, osc_det.holdout_fp_days, osc_det.holdout_days)
    sig_rate = False
    if rate_det is not None:
        decision_days = [d for i, d in enumerate(e["uni"].index) if i % 30 == 29]
        k_rate = int(sum(bool(e["rate_flag"].get(d, False)) for d in decision_days))
        sig_rate = S.rate_significant(k_rate, len(decision_days),
                                      rate_det["holdout_fp_days"],
                                      rate_det["holdout_days"])
    meaningful = "+".join(x for x, s_ in
                          (("rules", sig_rules), ("resid", sig_resid), ("model", sig_model),
                           ("device", sig_dev), ("absence", sig_abs),
                           ("freq", sig_freq), ("rate", sig_rate),
                           ("osc", sig_osc)) if s_)

    # TTD only from channels that PASSED their gates (audit G: a noise-day
    # from an insignificant channel must not set time-to-detection)
    sig_union = pd.Series(False, index=e["uni"].index)
    if sig_rules:
        sig_union = sig_union | e["rules"]
    if sig_resid:
        sig_union = sig_union | e["res_flag"]
    if sig_model:
        sig_union = sig_union | e["model"]
    if sig_dev:
        # only the SIGNIFICANT devices' days set TTD (residual audit-G nit:
        # a noise day from an insignificant sibling must not lead)
        sig_days = [d for dv in sig_devices for d in e["dev_days_map"].get(dv, [])]
        sig_union = sig_union | pd.Series(e["uni"].index.isin(sig_days),
                                          index=e["uni"].index)
    if sig_abs:
        sig_union = sig_union | e["abs_flag"]
    if sig_freq:
        sig_union = sig_union | e["freq_flag"]
    if sig_rate:
        sig_union = sig_union | e["rate_flag"]
    if sig_osc:
        sig_union = sig_union | e["osc_flag"]
    t = ttd(sig_union, uni) if meaningful else None

    if excluded:
        meaningful = ""  # calendar-misaligned source: never counted (audit F2)
    gt = GROUND_TRUTH.get(fname, {}).get("injected_zone")
    loc = "-"
    if gt == "INDETERMINATE":
        loc = "excl(GT?)"
    elif gt and e["top_device"]:
        loc = "OK" if e["top_device"] == f"TU_{gt}" else f"MISS({e['top_device']})"
    print(f"{label:34s} {n_eval:>4} "
          f"{c['rules']:>5} {c['res_flag']:>5} {c['model']:>5} {c['dev_flag']:>5} "
          f"{c['freq_flag']:>5} {c['rate_flag']:>5} {c['combined']:>5} "
          f"{str(t) if t else '-':>4} {loc:>10}")
    rows.append({
        "file": fname, "family": family, "label": label, "is_fault": is_fault,
        "days": n_days, "evaluable_days": n_eval, "window_days": n_win,
        "rules_days": c["rules"], "residual_days": c["res_flag"],
        "model_days": c["model"], "combined_days": c["combined"],
        "model_unique_days": e["n_model_unique"], "ttd_days": t,
        "log_hash": e["log_hash"], "top_device": e["top_device"],
        "ground_truth_zone": gt, "localization": loc,
        "meaningful_channels": (meaningful or None) if not excluded else None,
        "excluded": excluded,
        "meaningful_channels_raw": meaningful or None,
        "model_days_minrobust": e["model_minrobust"],
        "device_days": c["dev_flag"], "absence_days": c["abs_flag"],
        "frequency_days": c["freq_flag"], "rate_days": c["rate_flag"],
        "oscillation_days": c["osc_flag"],
        "flag_days": {
            "rules": sorted(e["rules"][e["rules"]].index.tolist()),
            "residual": sorted(e["res_flag"][e["res_flag"]].index.tolist()),
            "model": sorted(e["model"][e["model"]].index.tolist()),
            "device": sorted(e["dev_flag"][e["dev_flag"]].index.tolist()),
            "freq": sorted(e["freq_flag"][e["freq_flag"]].index.tolist()),
            "osc": sorted(e["osc_flag"][e["osc_flag"]].index.tolist()),
            "rate": sorted(e["rate_flag"][e["rate_flag"]].index.tolist()),
            "sig_union": sorted(sig_union[sig_union].index.tolist()),
        },
        "frequency_violations": dict(sorted(e["freq_viol"].items(),
                                            key=lambda kv: -kv[1])[:6]),
        "top_device_channel": e["top_dev_channel"],
        "device_case_days": e["dev_case_days"],
        "device_days_by_device": e["dev_by_device"],
        "absence_by_device": e["abs_days_sig"],
    })

by_hash: dict[str, list[str]] = {}
for r in rows:
    by_hash.setdefault(r["log_hash"], []).append(r["label"])
dupes = {h: ls for h, ls in by_hash.items() if len(ls) > 1}
print("-" * 106)
if dupes:
    print("event-identical scenario groups: " +
          " | ".join(" = ".join(ls) for ls in dupes.values()))

fam: dict[str, list[dict]] = {}
for r in rows:
    if r["is_fault"]:
        fam.setdefault(r["family"], []).append(r)
print(f"\n{'family':14s} {'scen':>4} {'detected':>8} {'medTTD':>7} {'med alarm%':>10} {'locz OK/scored':>14}")
for f, rs in sorted(fam.items()):
    det_n = sum(1 for r in rs if r["ttd_days"] is not None)
    ttds = sorted(r["ttd_days"] for r in rs if r["ttd_days"] is not None)
    fracs = sorted(len(r.get("flag_days", {}).get("sig_union", []))
                   / max(r["evaluable_days"], 1) for r in rs)
    scored = [r for r in rs if r["localization"] in ("OK",) or r["localization"].startswith("MISS")]
    ok = sum(1 for r in scored if r["localization"] == "OK")
    print(f"{f:14s} {len(rs):>4} {det_n:>8} {str(ttds[len(ttds)//2]) if ttds else '-':>7} "
          f"{fracs[len(fracs)//2]:>9.0%} {f'{ok}/{len(scored)}' if scored else '-':>14}")

out = Path("outputs")
out.mkdir(exist_ok=True)
(out / f"benchmark_v6_{SYSTEM}.json").write_text(json.dumps({
    "system": SYSTEM, "device_stratum": DEV_META, "residual_band": BAND,
    "frequency": {
        "unit_bands": len(freq_unit.bands) if freq_unit else 0,
        "unit_holdout_fp": [freq_unit.holdout_fp_days, freq_unit.holdout_days] if freq_unit else None,
        "device_bands": len(freq_dev.bands) if freq_dev else 0,
        "device_holdout_fp": [freq_dev.holdout_fp_days, freq_dev.holdout_days] if freq_dev else None,
        "rate_holdout_fp": [rate_det["holdout_fp_days"], rate_det["holdout_days"]] if rate_det else None,
    },
    "residual_holdout_fp": [hold_fp, hold_n],
    "model_threshold": det.threshold, "model_holdout_fp": model_hold_fp,
    "train_days": det.n_train_days, "healthy_sig_days": len(h_sig),
    "scenarios": rows, "event_identical_groups": dupes,
}, indent=2, default=str))
print(f"\nwrote outputs/benchmark_v6_{SYSTEM}.json")
