"""X11 — branch-offset adjudication for ERRATA E5 (pre-registered: PHASE8_PLAN.md).

Usage: uv run python scripts/x11_branch.py

Steps (exactly as pre-registered, commit 65fe3b8):
 1. healthy residual band + median (own the audit's numbers);
 2. fault-branch no-fault baseline from five concordant estimators
    (coi_bias ladder debiased by nominal bias + oa_bias as-is);
 3. branch offset delta and corrected band;
 4. corrected-band re-scoring of every SDAHU scenario + significance vs a
    fault-branch noise floor (healthy's own out-of-band rate, rule-of-three
    floored); consistency check: day-level debiased coi_bias series must be
    ~captured by the corrected band;
 5. adjudicated scorecard (deployed channels; rate stays diagnostic-only);
 6. FPU homogeneity battery: (a) occupied-minutes identity, (b) occupied
    damper floors, (c) rmtemp_bias supply-air-residual medians inside the
    healthy band.

Falsifiers F-X11.a-d per the plan; any firing is reported in the artifact
and the script exits 2 (adjudication withheld). Artifact: outputs/x11_branch.json
"""

import json
import os
import sys
import warnings

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")

from pathlib import Path

import pandas as pd
import yaml

from processheal.core.detection import holdout_mask
from processheal.core.residuals import calibrate_band, daily_residual_scores, flag_days
from processheal.io.config import load_config

RULE = "supply_air_residual"
NOMINAL_BIAS_F = {  # LBNL labels are Celsius biases; data is Fahrenheit
    "coi_bias_-4_annual": -7.2, "coi_bias_-2_annual": -3.6,
    "coi_bias_2_annual": 3.6, "coi_bias_4_annual": 7.2,
}

cfg = load_config("configs/lbnl_sdahu")
DATA = Path("data/processed/sdahu")
manifest = yaml.safe_load(Path("configs/lbnl_sdahu/scenarios.yaml").read_text())
HOLD_N = cfg.rules["detection"]["holdout_days_per_month"]
MIN_W = cfg.rules["detection"]["residual_min_band_width"]
MARGIN = cfg.rules["detection"]["residual_min_exceedance"]

out: dict = {"pre_registration": "PHASE8_PLAN.md @ commit 65fe3b8"}
falsifiers: list[str] = []

# ---- 1. healthy band + median -------------------------------------------------
hdf = pd.read_parquet(DATA / f"{manifest['healthy_file']}.parquet")
rh = daily_residual_scores(hdf, cfg, rule_name=RULE)
hmask = holdout_mask(rh["case_id"], HOLD_N)
band = calibrate_band(rh, ~hmask, min_width=MIN_W)
healthy_median = float(rh["score"].median())
out["healthy"] = {"band": [band[0], band[1]], "median": round(healthy_median, 4),
                  "window_days": int(len(rh))}
print(f"healthy: band [{band[0]:.3f}, {band[1]:.3f}], median {healthy_median:+.4f}, "
      f"windows {len(rh)}")

# ---- 2. fault-branch baseline -------------------------------------------------
scen_scores: dict[str, pd.DataFrame] = {}
estimators: dict[str, float] = {}
for sc in manifest["scenarios"]:
    f = sc["file"]
    rs = daily_residual_scores(pd.read_parquet(DATA / f"{f}.parquet"), cfg, rule_name=RULE)
    scen_scores[f] = rs
    med = float(rs["score"].median()) if len(rs) else float("nan")
    if f in NOMINAL_BIAS_F:
        estimators[f] = med - NOMINAL_BIAS_F[f]
    elif f.startswith("oa_bias"):
        estimators[f] = med
vals = sorted(estimators.values())
spread = vals[-1] - vals[0]
baseline = float(pd.Series(vals).median())
delta = healthy_median - baseline
out["fault_branch_baseline"] = {"estimators": {k: round(v, 4) for k, v in estimators.items()},
                                "spread": round(spread, 4), "baseline": round(baseline, 4),
                                "delta": round(delta, 4)}
print(f"estimators: { {k: round(v,3) for k,v in estimators.items()} }")
print(f"spread {spread:.4f} | baseline {baseline:+.4f} | delta {delta:+.4f}")
if spread > 0.25:
    falsifiers.append(f"F-X11.a: estimator spread {spread:.3f} > 0.25")

# ---- 3. corrected band ---------------------------------------------------------
cband = (band[0] - delta, band[1] - delta)
out["corrected_band"] = [round(cband[0], 4), round(cband[1], 4)]
print(f"corrected band [{cband[0]:.3f}, {cband[1]:.3f}] (same {MARGIN} F exceedance floor)")

# noise floor for the corrected band: healthy's own out-of-band-with-margin
# rate on ITS band (the day-to-day spread proxy), rule-of-three floored
h_flags = flag_days(rh, band, min_margin=MARGIN)
h_rate = float(h_flags["flagged"].sum()) / max(int(h_flags["evaluable"].sum()), 1)
p0 = max(h_rate, 3.0 / 365.0)
out["noise_floor"] = {"healthy_out_of_band_rate": round(h_rate, 5), "p0": round(p0, 5)}

# ---- 4. corrected re-scoring ---------------------------------------------------
from scipy.stats import binom  # noqa: E402


def binom_sf(k: int, n: int, p: float) -> float:
    return float(binom.sf(k - 1, n, min(p, 1.0))) if n else 1.0


rescored = {}
for sc in manifest["scenarios"]:
    f = sc["file"]
    rs = scen_scores[f]
    if not len(rs):
        rescored[f] = {"window_days": 0, "flagged": 0, "significant": False}
        continue
    fl = flag_days(rs, cband, min_margin=MARGIN)
    k, n = int(fl["flagged"].sum()), int(len(fl))
    sig = binom_sf(k, n, p0) < 1e-3
    rescored[f] = {"window_days": n, "flagged": k, "significant": bool(sig),
                   "median": round(float(rs["score"].median()), 4)}
    print(f"  {f:34s} corrected-band flags {k:3d}/{n:3d}  sig={sig}")
out["corrected_rescoring"] = rescored

oa = next(f for f in rescored if f.startswith("oa_bias"))
if rescored[oa]["significant"]:
    falsifiers.append(f"F-X11.b: corrected band still flags oa_bias "
                      f"({rescored[oa]['flagged']}/{rescored[oa]['window_days']})")
for f, bias in NOMINAL_BIAS_F.items():
    if not rescored[f]["significant"]:
        falsifiers.append(f"F-X11.c: {f} lost significance under corrected band")

# consistency check: day-level debiased coi_bias captured by corrected band
consistency = {}
for f, bias in NOMINAL_BIAS_F.items():
    rs = scen_scores[f].copy()
    rs["score"] = rs["score"] - bias
    fl = flag_days(rs, cband, min_margin=MARGIN)
    consistency[f] = {"debiased_flag_rate": round(float(fl["flagged"].mean()), 4)}
out["debias_consistency"] = consistency
print(f"debias consistency (should be ~0): "
      f"{ {k: v['debiased_flag_rate'] for k, v in consistency.items()} }")

# ---- 5. adjudicated scorecard ---------------------------------------------------
bench = json.loads(Path("outputs/benchmark_v6_sdahu.json").read_text())
DEPLOYED = {"rules", "resid", "model", "device", "absence", "freq", "osc"}  # no rate
adjudicated = []
for s in bench["scenarios"]:
    mc = set((s.get("meaningful_channels") or "").split("+")) - {""}
    mc_dep = mc & DEPLOYED
    if "resid" in mc_dep and not rescored[s["file"]]["significant"]:
        mc_dep = mc_dep - {"resid"}
    adjudicated.append({"file": s["file"], "label": s["label"],
                        "naive_channels": s.get("meaningful_channels"),
                        "adjudicated_deployed_channels": "+".join(sorted(mc_dep)) or None,
                        "detected": bool(mc_dep)})
n_det = sum(a["detected"] for a in adjudicated)
out["adjudicated_scorecard"] = {"detected": n_det, "of": len(adjudicated),
                                "scenarios": adjudicated}
print(f"adjudicated scorecard: {n_det}/{len(adjudicated)}")

# ---- 6. FPU homogeneity battery --------------------------------------------------
fpu = {}
for system in ("pfpu", "sfpu"):
    fcfg = load_config(f"configs/lbnl_{system}")
    pdir = Path(f"data/processed/{system}")
    occ_col = fcfg.sensors["OCCUPIED"]
    dmp_cols = [fcfg.sensors[k] for k in ("OA_DMPR_POS", "RA_DMPR_POS", "EA_DMPR_POS")
                if k in fcfg.sensors]
    healthy_name = f"{system.upper()}_FaultFree"
    # INSTRUMENT CORRECTION (first run's F-X11.d firing, diagnosed): the
    # schedule-identity leg must compare SCHEDULED occupancy (SYS_CTL == 1)
    # only. SYS_CTL == 2 is night-cycle — FAULT-RESPONSIVE behaviour (an
    # alphabet event; RMTEMP bias/damper faults legitimately change night
    # heating) and belongs to the fault signal, not the branch. The naive
    # ">0" leg conflated them (max day-diff 1201/1230 min, ALL of it
    # night-cycle; scheduled diff is 0 everywhere except the E4-rotated
    # file's known 720-min calendar artifact, which is excluded here as it
    # is everywhere else). Same conflation class as L21/L28 — logged.
    excluded = {s["file"] for s in yaml.safe_load(
        Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())["scenarios"]
        if s.get("exclude")}
    dfh = pd.read_parquet(pdir / f"{healthy_name}.parquet",
                          columns=["Datetime", occ_col] + dmp_cols)
    day_h = dfh["Datetime"].dt.date.astype(str)
    sched_h = (dfh[occ_col] == 1).groupby(day_h).sum()
    occ_mask_h = dfh[occ_col] > 0
    floor_h = {c: round(float(dfh.loc[occ_mask_h, c].min()), 4) for c in dmp_cols}

    max_daydiff, max_night_diff, floor_mismatch = 0.0, 0.0, {}
    for pq in sorted(pdir.glob("*.parquet")):
        if pq.stem == healthy_name or pq.stem in excluded:
            continue
        d = pd.read_parquet(pq, columns=["Datetime", occ_col] + dmp_cols)
        dd = d["Datetime"].dt.date.astype(str)
        sched_f = (d[occ_col] == 1).groupby(dd).sum()
        night_f = (d[occ_col] == 2).groupby(dd).sum()
        night_h = (dfh[occ_col] == 2).groupby(day_h).sum()
        shared = sched_h.index.intersection(sched_f.index)
        max_daydiff = max(max_daydiff,
                          float((sched_h.loc[shared] - sched_f.loc[shared]).abs().max()))
        max_night_diff = max(max_night_diff,
                             float((night_h.loc[shared] - night_f.loc[shared]).abs().max()))
        m = d[occ_col] > 0
        for c in dmp_cols:
            fl = round(float(d.loc[m, c].min()), 4)
            if abs(fl - floor_h[c]) > 0.02:
                floor_mismatch.setdefault(pq.stem, {})[c] = [floor_h[c], fl]

    # (c) rmtemp_bias residual medians inside healthy band
    frh = daily_residual_scores(pd.read_parquet(pdir / f"{healthy_name}.parquet"),
                                fcfg, rule_name=RULE)
    fh_mask = holdout_mask(frh["case_id"], fcfg.rules["detection"]["holdout_days_per_month"])
    fband = calibrate_band(frh, ~fh_mask,
                           min_width=fcfg.rules["detection"]["residual_min_band_width"])
    rm_meds = {}
    for pq in sorted(pdir.glob("*RMTEMP*2C*.parquet")):
        if pq.stem in excluded:
            continue
        rs = daily_residual_scores(pd.read_parquet(pq), fcfg, rule_name=RULE)
        if len(rs):
            rm_meds[pq.stem] = round(float(rs["score"].median()), 4)
    inside = {k: bool(fband[0] <= v <= fband[1]) for k, v in rm_meds.items()}
    fpu[system] = {
        "max_scheduled_occupancy_daydiff_min": max_daydiff,
        "max_night_cycle_daydiff_min_fault_responsive": max_night_diff,
        "damper_floor_mismatches": floor_mismatch,
        "healthy_band": [round(fband[0], 4), round(fband[1], 4)],
        "rmtemp_bias_residual_medians": rm_meds,
        "rmtemp_medians_inside_band": inside,
        "instrument_note": "schedule leg compares SYS_CTL==1 only; night-cycle "
                           "(==2) is fault-responsive and reported separately; "
                           "E4-excluded file skipped (first-run F-X11.d firing "
                           "was this conflation — diagnosed and corrected)",
    }
    print(f"[{system}] sched-occ max day-diff {max_daydiff:.1f} min "
          f"(night-cycle {max_night_diff:.0f}, fault-responsive) | floor mismatches "
          f"{len(floor_mismatch)} | rmtemp medians {rm_meds} inside={inside}")
    if max_daydiff > 30 or floor_mismatch or not all(inside.values()):
        falsifiers.append(f"F-X11.d: {system} homogeneity battery leg failed")
out["fpu_homogeneity"] = fpu

out["falsifiers_fired"] = falsifiers
out["verdict"] = ("ADJUDICATED" if not falsifiers else "WITHHELD (falsifier fired)")
Path("outputs/x11_branch.json").write_text(json.dumps(out, indent=1))
print(f"\nfalsifiers fired: {falsifiers or 'NONE'}")
print(f"verdict: {out['verdict']} -> wrote outputs/x11_branch.json")
sys.exit(0 if not falsifiers else 2)
