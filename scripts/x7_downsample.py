"""X7 — 15-min downsample robustness (pre-registered: PHASE8_PLAN.md addendum).

Usage: uv run python scripts/x7_downsample.py

Every 15th row of each healthy year + one fault file per family;
recompute rules / residual (band recalibrated on 15-min train data) /
frequency; compare day coverage vs the 1-min artifacts.
Artifact: outputs/x7_downsample.json
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
from processheal.core.frequency import (
    build_frequency_detector,
    classify_frequency_days,
    unit_day_counts,
)
from processheal.core.residuals import calibrate_band, daily_residual_scores, flag_days
from processheal.hvac.events import abstract_events, event_alphabet_map
from processheal.io.config import load_config

STEP = 15
RULE = "supply_air_residual"

out = {"pre_registration": "PHASE8_PLAN.md X7 addendum", "systems": {}}
falsifiers = []

for system in ("sdahu", "pfpu", "sfpu"):
    cfg = load_config(f"configs/lbnl_{system}")
    DATA = Path(f"data/processed/{system}")
    manifest = yaml.safe_load(Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())
    HOLD_N = cfg.rules["detection"]["holdout_days_per_month"]
    MIN_W = cfg.rules["detection"].get("residual_min_band_width", 0.0)
    MARGIN = cfg.rules["detection"].get("residual_min_exceedance", 0.0)
    SIGNATURE = {e for e, a in event_alphabet_map(cfg).items() if a == "signature"} - {RULE}

    def load15(fname):
        return pd.read_parquet(DATA / f"{fname}.parquet").iloc[::STEP].reset_index(drop=True)

    # healthy at 15-min
    hdf = load15(manifest["healthy_file"])
    hlog = abstract_events(hdf, cfg)
    h_sig_days = sorted(set(hlog.loc[hlog["activity"].isin(SIGNATURE), "case_id"]))
    rh = daily_residual_scores(hdf, cfg, rule_name=RULE)
    band15 = None
    if len(rh):
        hmask = holdout_mask(rh["case_id"], HOLD_N)
        band15 = calibrate_band(rh, ~hmask, min_width=MIN_W)
    freq15 = build_frequency_detector(unit_day_counts(hlog), HOLD_N)

    sysres = {"healthy_signature_days_15min": len(h_sig_days),
              "residual_band_15min": [round(band15[0], 4), round(band15[1], 4)] if band15 else None,
              "residual_windows_15min": int(len(rh)),
              "families": {}}
    print(f"[{system}] healthy 15-min: signature days {len(h_sig_days)}, "
          f"band {sysres['residual_band_15min']}, windows {len(rh)}")
    if h_sig_days:
        falsifiers.append(f"F-X7.a: {system} healthy gains {len(h_sig_days)} signature days at 15-min")

    # one fault per family (first non-excluded of each)
    bench = json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())
    ref = {s["file"]: s for s in bench["scenarios"]}
    seen = set()
    for sc in manifest["scenarios"]:
        fam = sc["family"]
        if fam in seen or sc.get("exclude"):
            continue
        seen.add(fam)
        f = sc["file"]
        fdf = load15(f)
        flog = abstract_events(fdf, cfg)
        sig_days_15 = len(set(flog.loc[flog["activity"].isin(SIGNATURE), "case_id"]))
        rules_1min = ref[f]["rules_days"]
        res_15 = 0
        rs = daily_residual_scores(fdf, cfg, rule_name=RULE)
        if band15 and len(rs):
            res_15 = int(flag_days(rs, band15, min_margin=MARGIN)["flagged"].sum())
        freq_15 = 0
        if freq15 is not None:
            fc = classify_frequency_days(freq15, unit_day_counts(flog))
            freq_15 = int(fc["flagged"].sum()) if len(fc) else 0
        row = {"rules_days": [rules_1min, sig_days_15],
               "residual_days": [ref[f]["residual_days"], res_15],
               "freq_days": [ref[f]["frequency_days"], freq_15]}
        sysres["families"][fam] = {"file": f, "coverage_1min_vs_15min": row}
        print(f"   {fam:16s} rules {rules_1min}->{sig_days_15}  "
              f"resid {ref[f]['residual_days']}->{res_15}  "
              f"freq {ref[f]['frequency_days']}->{freq_15}")
        if rules_1min > 20 and sig_days_15 < 0.75 * rules_1min:
            falsifiers.append(f"F-X7.b: {system}/{fam} rules coverage dropped >25% at 15-min")
        if ref[f]["residual_days"] > 20 and res_15 < 0.75 * ref[f]["residual_days"]:
            falsifiers.append(f"F-X7.b: {system}/{fam} residual coverage dropped >25% at 15-min")
    out["systems"][system] = sysres

out["falsifiers_fired"] = falsifiers
Path("outputs/x7_downsample.json").write_text(json.dumps(out, indent=1))
print(f"\nfalsifiers fired: {falsifiers or 'NONE'}")
print("wrote outputs/x7_downsample.json")
sys.exit(0 if not falsifiers else 2)
