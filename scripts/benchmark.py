"""Benchmark v6 — cross-system, per-scenario, blind-calibrated (Phase 3b).

All v5 protocol fixes retained (G1-G7; see GAP_ANALYSIS_AUG2026.md), now
parameterized over buildings: config + data + scenario manifest per system,
zero code difference between systems.

    uv run python scripts/benchmark.py sdahu
    uv run python scripts/benchmark.py pfpu
    uv run python scripts/benchmark.py sfpu

New in v6: zone localization scoring (E3). For systems with a week-0 zone
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
from math import comb


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k), X ~ Binom(n, p) — is an alarm count above a channel's
    healthy noise floor, or just the floor itself? (G4 at scenario level:
    'detected' must mean 'significantly above what noise produces'.)"""
    if n <= 0:
        return 1.0
    return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(min(k, n), n + 1))

warnings.filterwarnings("ignore")

from processheal.core.detection import build_detector, classify_days, holdout_mask
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

# zone ground truth (E3), if the week-0 audit covered this system
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

    res = flag_days(daily_residual_scores(df, cfg), BAND).set_index("case_id")
    res_flag = res["flagged"].reindex(days).fillna(False)
    res_eval = res["evaluable"].reindex(days).fillna(False)

    combined = rules | model | res_flag

    # E3: top-firing device among signature events (fire-days per device)
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

res_healthy = daily_residual_scores(healthy_df, cfg)
hold = holdout_mask(res_healthy["case_id"], cfg.rules["detection"]["holdout_days_per_month"])
BAND = calibrate_band(res_healthy, ~hold,
                      min_width=cfg.rules["detection"].get("residual_min_band_width", 0.0))
res_hold = flag_days(res_healthy[hold], BAND)
hold_fp, hold_n = int(res_hold["flagged"].sum()), int(res_hold["evaluable"].sum())

h_uni = day_universe(healthy_df).set_index("case_id")
h_sig = set(healthy_log.loc[healthy_log["activity"].isin(SIGNATURE_EVENTS), "case_id"])
model_hold_fp = int((det.holdout_per_day["fitness"] < det.threshold).sum())

print(f"\nresidual band (TRAIN-only): [{BAND[0]:+.2f}, {BAND[1]:+.2f}] F | "
      f"holdout: {hold_fp}/{hold_n} window-days outside")
print(f"model threshold: {det.threshold:.4f} (min-calibration on {len(det.holdout_per_day)} holdout days; "
      f"holdout FP {model_hold_fp})")
print(f"rules on FULL healthy year: {len(h_sig)} signature days (computed)")
print("false-alarm evidence = held-out healthy days ONLY (no independent negative exists; stated).")

rows = []
print(f"\n{'scenario':34s} {'days':>4} {'eval':>4} {'win':>4} "
      f"{'rules':>5} {'resid':>5} {'model':>5} {'comb':>5} {'TTD':>4} {'locz':>10}")
print("-" * 106)

for sc in SCENARIOS:
    fname, family, label, is_fault = sc["file"], sc["family"], sc["label"], sc["is_fault"]
    e = evaluate(fname)
    uni = e["uni"]
    n_days, n_eval = len(uni), int(uni["evaluable"].sum())
    n_win = int(e["res_eval"].sum())
    c = {ch: int(e[ch].sum()) for ch in ("rules", "res_flag", "model", "combined")}

    # significance vs each channel's own holdout noise floor
    p_model = max(model_hold_fp, 1) / max(len(det.holdout_per_day), 1)
    p_resid = max(hold_fp, 1) / max(hold_n, 1)
    # rules floor: 0 observed FP on the healthy year still only bounds the
    # rate at ~3/365 (rule of three) — 1-3 fire-days are NOT detection
    sig_rules = binom_sf(c["rules"], n_eval, 3.0 / 365.0) < 1e-3
    sig_resid = bool(n_win) and binom_sf(c["res_flag"], n_win, p_resid) < 1e-3
    sig_model = binom_sf(c["model"], n_eval, p_model) < 1e-3
    meaningful = "+".join(x for x, s_ in
                          (("rules", sig_rules), ("resid", sig_resid), ("model", sig_model)) if s_)

    # TTD only means something when detection beats noise (audit 5)
    t = ttd(e["combined"], uni) if meaningful else None

    gt = GROUND_TRUTH.get(fname, {}).get("injected_zone")
    loc = "-"
    if gt == "INDETERMINATE":
        loc = "excl(GT?)"
    elif gt and e["top_device"]:
        loc = "OK" if e["top_device"] == f"TU_{gt}" else f"MISS({e['top_device']})"
    print(f"{label:34s} {n_days:>4} {n_eval:>4} {n_win:>4} "
          f"{c['rules']:>5} {c['res_flag']:>5} {c['model']:>5} {c['combined']:>5} "
          f"{str(t) if t else '-':>4} {loc:>10}")
    rows.append({
        "file": fname, "family": family, "label": label, "is_fault": is_fault,
        "days": n_days, "evaluable_days": n_eval, "window_days": n_win,
        "rules_days": c["rules"], "residual_days": c["res_flag"],
        "model_days": c["model"], "combined_days": c["combined"],
        "model_unique_days": e["n_model_unique"], "ttd_days": t,
        "log_hash": e["log_hash"], "top_device": e["top_device"],
        "ground_truth_zone": gt, "localization": loc,
        "meaningful_channels": meaningful or None,
        "model_days_minrobust": e["model_minrobust"],
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
    fracs = sorted(r["combined_days"] / r["evaluable_days"] for r in rs)
    scored = [r for r in rs if r["localization"] in ("OK",) or r["localization"].startswith("MISS")]
    ok = sum(1 for r in scored if r["localization"] == "OK")
    print(f"{f:14s} {len(rs):>4} {det_n:>8} {str(ttds[len(ttds)//2]) if ttds else '-':>7} "
          f"{fracs[len(fracs)//2]:>9.0%} {f'{ok}/{len(scored)}' if scored else '-':>14}")

out = Path("outputs")
out.mkdir(exist_ok=True)
(out / f"benchmark_v6_{SYSTEM}.json").write_text(json.dumps({
    "system": SYSTEM, "residual_band": BAND,
    "residual_holdout_fp": [hold_fp, hold_n],
    "model_threshold": det.threshold, "model_holdout_fp": model_hold_fp,
    "train_days": det.n_train_days, "healthy_sig_days": len(h_sig),
    "scenarios": rows, "event_identical_groups": dupes,
}, indent=2, default=str))
print(f"\nwrote outputs/benchmark_v6_{SYSTEM}.json")
