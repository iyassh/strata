"""X8 — training-set contamination (pre-registered: PHASE8_PLAN.md @ 65fe3b8).

Usage: uv run python scripts/x8_contamination.py

For k in {2, 5, 10}% of SDAHU TRAIN days (deterministic every-Nth
selection over the sorted train-day list, no RNG), replace the day's
DAILY AGGREGATES with the same calendar day's aggregates from a fault
file (equivalent to row-level replacement for the day-aggregate channels;
same weather year, so the contamination is realistic). Two sources:

  WORST: coi_bias_-4  (residual-extreme -7.2 F; fires NO signature rules
         -> silent to the rules channel: the dangerous contamination)
  MILD:  damper_stuck_010 (rules-visible 365 d/yr; residual-quiet)

For each (source, k), recompute the train-only calibrations and report:
  (a) residual band drift; frequency count-band drift; monthly rate drift;
  (b) consequences under drifted bands: coi_bias +/-2/+/-4 window-day
      coverage and healthy-holdout residual FP;
  (c) DETECTABILITY of the contamination itself: signature-event days
      among the contaminated train days (would an operator have noticed?).

Artifact: outputs/x8_contamination.json
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
from processheal.core.frequency import build_frequency_detector, unit_day_counts
from processheal.core.residuals import calibrate_band, daily_residual_scores, flag_days
from processheal.hvac.events import abstract_events, event_alphabet_map
from processheal.io.config import load_config

RULE = "supply_air_residual"
KS = (0.02, 0.05, 0.10)
SOURCES = {"worst_coi_bias_-4": "coi_bias_-4_annual",
           "mild_damper_stuck_010": "damper_stuck_010_annual"}

cfg = load_config("configs/lbnl_sdahu")
DATA = Path("data/processed/sdahu")
manifest = yaml.safe_load(Path("configs/lbnl_sdahu/scenarios.yaml").read_text())
HOLD_N = cfg.rules["detection"]["holdout_days_per_month"]
MIN_W = cfg.rules["detection"]["residual_min_band_width"]
MARGIN = cfg.rules["detection"]["residual_min_exceedance"]
SIGNATURE = {e for e, a in event_alphabet_map(cfg).items() if a == "signature"} - {RULE}

# healthy pieces (computed once)
hdf = pd.read_parquet(DATA / f"{manifest['healthy_file']}.parquet")
rh = daily_residual_scores(hdf, cfg, rule_name=RULE)
hmask = holdout_mask(rh["case_id"], HOLD_N)
band0 = calibrate_band(rh, ~hmask, min_width=MIN_W)
train_days = sorted(rh.loc[~hmask.values, "case_id"].tolist())
hlog = abstract_events(hdf, cfg)
hcounts = unit_day_counts(hlog)
freq0 = build_frequency_detector(hcounts, HOLD_N)

# fault-side pieces per scenario for consequences
bias_scores = {f: daily_residual_scores(pd.read_parquet(DATA / f"{f}.parquet"),
                                        cfg, rule_name=RULE)
               for f in ("coi_bias_-4_annual", "coi_bias_-2_annual",
                         "coi_bias_2_annual", "coi_bias_4_annual")}
hold_scores = rh[hmask.values]


def coverage(band):
    cov = {}
    for f, rs in bias_scores.items():
        fl = flag_days(rs, band, min_margin=MARGIN)
        cov[f] = f"{int(fl['flagged'].sum())}/{int(fl['evaluable'].sum())}"
    fp = int(flag_days(hold_scores, band, min_margin=MARGIN)["flagged"].sum())
    return cov, fp


cov0, fp0 = coverage(band0)
print(f"baseline band [{band0[0]:.3f}, {band0[1]:.3f}] cov={cov0} holdout FP={fp0}")

out = {"pre_registration": "PHASE8_PLAN.md @ 65fe3b8",
       "baseline": {"band": [round(band0[0], 4), round(band0[1], 4)],
                    "coverage": cov0, "holdout_fp": fp0},
       "runs": []}

for src_label, src_file in SOURCES.items():
    fdf = pd.read_parquet(DATA / f"{src_file}.parquet")
    frs = daily_residual_scores(fdf, cfg, rule_name=RULE).set_index("case_id")
    flog = abstract_events(fdf, cfg)
    fcounts = unit_day_counts(flog)
    fsig_days = set(flog.loc[flog["activity"].isin(SIGNATURE), "case_id"])
    for k in KS:
        step = max(int(round(1.0 / k)), 1)
        chosen = train_days[::step][: int(round(k * len(train_days)))]
        # ---- residual band under contamination ----
        rc = rh.set_index("case_id").copy()
        replaced = [d for d in chosen if d in frs.index]
        rc.loc[replaced, "score"] = frs.loc[replaced, "score"]
        rc = rc.reset_index()
        mask_c = holdout_mask(rc["case_id"], HOLD_N)
        band_c = calibrate_band(rc, ~mask_c, min_width=MIN_W)
        cov_c, fp_c = coverage(band_c)
        # ---- frequency bands under contamination ----
        cc = hcounts.copy()
        common = [d for d in chosen if d in fcounts.index and d in cc.index]
        cc.loc[common, :] = fcounts.reindex(cc.columns, axis=1).loc[common, :].fillna(0).values
        freq_c = build_frequency_detector(cc, HOLD_N)
        widened = 0
        if freq_c is not None and freq0 is not None:
            for key, (lo, hi) in freq_c.bands.items():
                lo0, hi0 = freq0.bands.get(key, (lo, hi))
                if lo < lo0 or hi > hi0:
                    widened += 1
        # ---- detectability of the contamination itself ----
        sig_hit = len([d for d in chosen if d in fsig_days])
        run = {"source": src_label, "k": k, "n_contaminated": len(chosen),
               "band": [round(band_c[0], 4), round(band_c[1], 4)],
               "band_width": round(band_c[1] - band_c[0], 4),
               "band_width_baseline": round(band0[1] - band0[0], 4),
               "coverage": cov_c, "holdout_fp": fp_c,
               "freq_keys_widened": widened,
               "contaminated_days_with_signature_events": sig_hit}
        out["runs"].append(run)
        print(f"[{src_label} k={k:.0%}] n={len(chosen)} band [{band_c[0]:.2f},{band_c[1]:.2f}] "
              f"width {band_c[1]-band_c[0]:.2f} | cov {cov_c} | FP {fp_c} | "
              f"freq widened {widened} | sig-visible days {sig_hit}/{len(chosen)}")

# falsifier checks (pre-registered)
falsifiers = []
worst10 = next(r for r in out["runs"] if r["source"] == "worst_coi_bias_-4" and r["k"] == 0.10)
if worst10["band_width"] <= worst10["band_width_baseline"] + 1e-9:
    falsifiers.append("F-X8.a: worst-case k=10% left bands unchanged — instrument broken")
if any(r["holdout_fp"] > fp0 for r in out["runs"]):
    falsifiers.append("F-X8.b: FP increased under contamination — accounting bug")
out["falsifiers_fired"] = falsifiers
Path("outputs/x8_contamination.json").write_text(json.dumps(out, indent=1))
print(f"\nfalsifiers fired: {falsifiers or 'NONE'}")
print("wrote outputs/x8_contamination.json")
sys.exit(0 if not falsifiers else 2)
