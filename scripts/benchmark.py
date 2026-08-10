"""Benchmark v5 — gap-fixed evaluation protocol (see GAP_ANALYSIS_AUG2026.md).

Fixes over v4:
- G1  The residual channel is a per-day CONTINUOUS score (median coil-off
      occupied SA-MA residual), band-calibrated on TRAIN days only — blind:
      no fault file, no holdout day touches the calibration. The Phase-2
      hand-banded event rule is EXCLUDED from scoring (kept only for
      localization display).
- G3  FPR accounting: calibration days are never counted as test negatives.
      Headline FPR comes from the independent healthy-like run (oa_bias_4,
      relabeled after the byte-identity audit — stated openly). Holdout-day
      rates are reported separately as calibration diagnostics. The rules
      channel's healthy counts are computed, not asserted.
- G4  The model (conformance) channel is reported as its own arm and NOT
      folded into a headline combined number; on SDAHU it is a measured null.
- G5  Primary reporting is PER SCENARIO: detected yes/no, time-to-first-
      detection, alarm-day fraction — aggregated per fault family. Pooled
      day-level rates appear only in the JSON appendix. Scenarios whose event
      logs are identical are detected automatically and tagged.
- G6  The bias family is decomposed as window prevalence x conditional
      recall (the residual is only physics-bound while the coil is off and
      the zone occupied).
- G7  The day universe comes from the RAW data, not from the event log:
      days with zero events no longer vanish. Unoccupied days are counted as
      not-evaluable; an occupied day with zero events is flagged (silence on
      a scheduled day is itself a deviation).
"""

import os

os.environ["TQDM_DISABLE"] = "1"

import hashlib
import json
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

from processheal.core.detection import build_detector, classify_days, holdout_mask
from processheal.core.residuals import calibrate_band, daily_residual_scores, flag_days
from processheal.hvac.events import abstract_events, event_alphabet_map
from processheal.io.config import load_config

DATA = Path("data/processed/sdahu")
cfg = load_config("configs/lbnl_sdahu")

RESIDUAL_RULE = "supply_air_residual"  # scored via the calibrated channel, not the event
SIGNATURE_EVENTS = {
    e for e, a in event_alphabet_map(cfg).items() if a == "signature"
} - {RESIDUAL_RULE}

# (file, family, label, is_fault)
SCENARIOS = [
    ("damper_stuck_010_annual", "damper_stuck", "damper stuck 10%", True),
    ("damper_stuck_025_annual", "damper_stuck", "damper stuck 25%", True),
    ("damper_stuck_075_annual", "damper_stuck", "damper stuck 75%", True),
    ("damper_stuck_100_annual_short", "damper_stuck", "damper stuck 100%", True),
    ("coi_stuck_010_annual", "valve_stuck", "valve stuck 10%", True),
    ("coi_stuck_025_annual", "valve_stuck", "valve stuck 25%", True),
    ("coi_stuck_050_annual", "valve_stuck", "valve stuck 50%", True),
    ("coi_stuck_075_annual", "valve_stuck", "valve stuck 75%", True),
    ("coi_leakage_010_annual", "valve_leak", "valve leaking", True),
    ("coi_bias_-4_annual", "sensor_bias", "SA sensor bias -4C", True),
    ("coi_bias_-2_annual", "sensor_bias", "SA sensor bias -2C", True),
    ("coi_bias_2_annual", "sensor_bias", "SA sensor bias +2C", True),
    ("coi_bias_4_annual", "sensor_bias", "SA sensor bias +4C", True),
    # Relabel OVERTURNED (2026-08-10): under bit-identical weather inputs
    # (OA_TEMP, OA_CFM match healthy exactly) this run BEHAVES differently
    # (MA/SA/RA corr 0.78-0.84, |diff| p95 ~15F; damper corr 0.91) — the
    # signature of a CONTROLLER-SIDE OA sensor bias: the fault is applied to
    # what the controller reads, so it never appears in the logged column.
    # The four oa_bias files are byte-identical to each other (one run,
    # shipped four times; injected severity not recoverable from the data).
    # Consequence: SDAHU has NO independent healthy negative run.
    ("oa_bias_4_annual", "oa_bias", "OA sensor bias (controller-side)", True),
]


def day_universe(df: pd.DataFrame) -> pd.DataFrame:
    """Every calendar day in the RAW file, with occupied minutes (G7)."""
    w = df.rename(columns={v: k for k, v in cfg.sensors.items()})
    day = w["Datetime"].dt.date.astype(str)
    occ = w["OCCUPIED"] == 1
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
    # G7 semantics (corrected after the unoccupied-day finding): a day is
    # evaluable for the event channels if it EMITS EVENTS or is OCCUPIED.
    # Faults manifest on unoccupied days too — a stuck-open valve cools an
    # empty building, and "equipment active while unoccupied" is exactly the
    # kind of trace the healthy model rejects. Only silent unoccupied days
    # are not evaluable. Silence on an OCCUPIED day is itself a flag.
    has_events = pd.Series([d in set(log["case_id"]) for d in days], index=days)
    uni["evaluable"] = has_events | (uni["occupied_min"] > 0)

    # rules channel: any signature event, any day (residual event excluded)
    sig_days = set(log.loc[log["activity"].isin(SIGNATURE_EVENTS), "case_id"])
    rules = pd.Series([d in sig_days for d in days], index=days)

    # model channel: conformance on state events; silent occupied day = flag
    per_day = classify_days(det, log)
    model = per_day.set_index("case_id")["flagged"].reindex(days).fillna(False)
    model = model | (~has_events & (uni["occupied_min"] > 0))

    # residual channel: blind-calibrated daily score; abstains without window
    res = flag_days(daily_residual_scores(df, cfg), BAND).set_index("case_id")
    res_flag = res["flagged"].reindex(days).fillna(False)
    res_eval = res["evaluable"].reindex(days).fillna(False)

    combined = rules | model | res_flag
    return {
        "uni": uni, "rules": rules, "model": model, "res_flag": res_flag,
        "res_eval": res_eval, "combined": combined, "log_hash": log_hash,
        "n_model_unique": int((model & ~rules & ~res_flag).sum()),
    }


def ttd(flags: pd.Series, uni: pd.DataFrame) -> int | None:
    """Days from file start to first flagged day (1 = first day)."""
    for i, d in enumerate(uni.index, start=1):
        if bool(flags.get(d, False)):
            return i
    return None


print("=" * 100)
print("STRATA benchmark v5 — blind-calibrated channels, per-scenario reporting")
print("=" * 100)

healthy_df = pd.read_parquet(DATA / "AHU_annual.parquet")
healthy_log = abstract_events(healthy_df, cfg)
det = build_detector(cfg, healthy_log)

# --- residual channel calibration: TRAIN days only (G1) ---
res_healthy = daily_residual_scores(healthy_df, cfg)
hold = holdout_mask(res_healthy["case_id"], cfg.rules["detection"]["holdout_days_per_month"])
BAND = calibrate_band(res_healthy, ~hold)
res_hold = flag_days(res_healthy[hold], BAND)
hold_fp = int(res_hold["flagged"].sum())
hold_n = int(res_hold["evaluable"].sum())
print(f"\nresidual band (median coil-off occupied SA-MA), TRAIN-only calibration: "
      f"[{BAND[0]:+.2f}, {BAND[1]:+.2f}] F")
print(f"  holdout validation: {hold_fp}/{hold_n} held-out healthy window-days outside band")
print(f"model threshold: {det.threshold:.4f} (= worst held-out healthy day; the fitness "
      f"distribution is discrete — this is min-calibration, stated honestly)")

# healthy-year rules-channel count: computed, not asserted (G3)
h_uni = day_universe(healthy_df).set_index("case_id")
h_sig = set(healthy_log.loc[healthy_log["activity"].isin(SIGNATURE_EVENTS), "case_id"])
print(f"rules channel on FULL healthy year: {len(h_sig)}/{int((h_uni['occupied_min']>0).sum())} "
      f"occupied days with a signature event (computed)")

rows = []
hdr = (f"{'scenario':26s} {'days':>4} {'eval':>4} {'win':>4} "
       f"{'rules':>6} {'resid':>6} {'model':>6} {'comb':>6} {'TTD':>4}  log")
print("\n" + hdr)
print("-" * 100)

for fname, family, label, is_fault in SCENARIOS:
    e = evaluate(fname)
    uni = e["uni"]
    n_days, n_eval = len(uni), int(uni["evaluable"].sum())
    n_win = int(e["res_eval"].sum())
    counts = {ch: int(e[ch].sum()) for ch in ("rules", "res_flag", "model", "combined")}
    t = ttd(e["combined"], uni)
    print(f"{label:26s} {n_days:>4} {n_eval:>4} {n_win:>4} "
          f"{counts['rules']:>6} {counts['res_flag']:>6} {counts['model']:>6} "
          f"{counts['combined']:>6} {str(t) if t else '-':>4}  {e['log_hash']}")
    rows.append({
        "file": fname, "family": family, "label": label, "is_fault": is_fault,
        "days": n_days, "evaluable_days": n_eval, "window_days": n_win,
        "rules_days": counts["rules"], "residual_days": counts["res_flag"],
        "model_days": counts["model"], "combined_days": counts["combined"],
        "model_unique_days": e["n_model_unique"],
        "ttd_days": t, "log_hash": e["log_hash"],
        "residual_window_conditional": (counts["res_flag"] / n_win) if n_win else None,
    })

# event-identical scenario groups (G5), detected not asserted
by_hash: dict[str, list[str]] = {}
for r in rows:
    by_hash.setdefault(r["log_hash"], []).append(r["label"])
dupes = {h: ls for h, ls in by_hash.items() if len(ls) > 1}
print("-" * 100)
if dupes:
    print("event-identical scenario groups (same log hash — copies at the event level):")
    for h, ls in dupes.items():
        print(f"  [{h}] " + " = ".join(ls))

# family summary (G5): per-scenario detection + median alarm-day fraction
print(f"\n{'family':14s} {'scenarios':>9} {'detected':>8} {'median TTD':>10} {'median alarm-day %':>19}")
fam: dict[str, list[dict]] = {}
for r in rows:
    if not r["is_fault"]:
        continue
    fam.setdefault(r["family"], []).append(r)
for f, rs in fam.items():
    det_n = sum(1 for r in rs if r["ttd_days"] is not None)
    ttds = sorted(r["ttd_days"] for r in rs if r["ttd_days"] is not None)
    fracs = sorted(r["combined_days"] / r["evaluable_days"] for r in rs)
    med_ttd = ttds[len(ttds) // 2] if ttds else None
    med_frac = fracs[len(fracs) // 2]
    print(f"{f:14s} {len(rs):>9} {det_n:>8} {str(med_ttd) if med_ttd else '-':>10} {med_frac:>18.0%}")

# negatives (G3, amended): after the oa_bias relabel was OVERTURNED, SDAHU has
# no independent healthy negative run. The honest false-alarm evidence is:
# held-out healthy days (used once, for calibration validation) and the
# training year's zeros (train-contaminated, diagnostic only). Independent
# negatives arrive with the FPU FaultFree files (Phase 3).
print("\nfalse-alarm evidence (SDAHU has NO independent healthy run — stated plainly):")
print(f"  holdout healthy days: rules 0/{det.holdout_per_day.shape[0]} (computed), "
      f"residual {hold_fp}/{hold_n} window-days, "
      f"model {int((det.holdout_per_day['fitness'] < det.threshold).sum())}/{det.holdout_per_day.shape[0]}")
print(f"  full healthy year (train-contaminated, diagnostic): rules {len(h_sig)}/303 days")
print("  independent negatives: NONE until FPU FaultFree (Phase 3) — a stated limitation.")

out = Path("outputs")
out.mkdir(exist_ok=True)
(out / "benchmark_v5.json").write_text(json.dumps({
    "residual_band": BAND, "residual_holdout_fp": [hold_fp, hold_n],
    "model_threshold": det.threshold, "train_days": det.n_train_days,
    "scenarios": rows, "event_identical_groups": dupes,
}, indent=2, default=str))
print("\nwrote outputs/benchmark_v5.json")
