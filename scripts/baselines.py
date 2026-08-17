"""Phase 4 external baselines: IsolationForest + PCA-SPE on identical splits.

The "why not just use generic ML?" answer, in numbers. Conventions per the
guidance sweep: daily aggregate features (mean/std/min/max per sensor over
scheduled-operation minutes), fit on healthy TRAIN days only, decision
threshold = 99th percentile of TRAIN scores (healthy-only calibration —
sklearn's contamination-on-test idiom is deliberately avoided), holdout
days validate. Citations: Liu et al. 2008 (iForest); Wang & Xiao 2004
(PCA/SPE for AHU FDD). No published iForest/PCA numbers exist on LBNL at
daily granularity — these baselines set the anchor, so the protocol
mirrors ours exactly: same splits, same day-level labels, same noise-gate
logic (a scenario is 'detected' only above the holdout floor).

Honest framing, pre-registered: these detectors get the RAW SENSORS (more
information than our event channels) but produce an anomaly score with no
diagnosis. The comparison axes are detection AND explainability.

    uv run python scripts/baselines.py <system>
"""

import json
import sys
import warnings
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

warnings.filterwarnings("ignore")

from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest

sys.path.insert(0, "src")
from processheal.core.detection import holdout_mask
from processheal.io.config import load_config

SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "sdahu"
DATA = Path(f"data/processed/{SYSTEM}")
cfg = load_config(f"configs/lbnl_{SYSTEM}")
manifest = yaml.safe_load(Path(f"configs/lbnl_{SYSTEM}/scenarios.yaml").read_text())


def binom_sf(k, n, p):
    if n <= 0:
        return 1.0
    return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(min(k, n), n + 1))


# Dataset erratum #4 (Phase-4 audit D1): SDAHU's healthy file logs SA_SP /
# SA_SPSPT in different units/roles than every fault file; a baseline fed
# these columns detects FILE PROVENANCE, not faults (SPE ~1e37). Dropped.
ERRATUM_COLS = {"SA_SP", "SA_SPSPT"}


def daily_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=[c for c in ERRATUM_COLS if c in df.columns])
    w = df.rename(columns={v: k for k, v in cfg.sensors.items()})
    active = w[w["OCCUPIED"] > 0]
    num = active.select_dtypes("number").drop(columns=["OCCUPIED"], errors="ignore")
    day = active["Datetime"].dt.date.astype(str)
    g = num.groupby(day.values)
    feats = pd.concat([g.mean().add_suffix("_mean"), g.std().add_suffix("_std"),
                       g.min().add_suffix("_min"), g.max().add_suffix("_max")], axis=1)
    return feats.fillna(0.0)


healthy = daily_features(pd.read_parquet(DATA / f"{manifest['healthy_file']}.parquet"))
days = pd.Series(healthy.index.astype(str), index=healthy.index)
hold = holdout_mask(days, cfg.rules["detection"]["holdout_days_per_month"])
train, holdout = healthy[~hold.values], healthy[hold.values]

mu, sd = train.mean(), train.std().replace(0, 1.0)
z = lambda X: (X - mu) / sd

results = {}
# --- IsolationForest ---
iforest = IsolationForest(n_estimators=200, random_state=7).fit(z(train))
if_scores_train = -iforest.score_samples(z(train))
if_thr = np.quantile(if_scores_train, 0.99)
if_thr_strict = float(if_scores_train.max())  # zero train FP — matches our extreme calibration
if_hold = -iforest.score_samples(z(holdout))
if_hold_fp = int((if_hold > if_thr).sum())
if_hold_fp_strict = int((if_hold > if_thr_strict).sum())
# --- PCA-SPE (Wang & Xiao style: components to 95% variance, SPE limit) ---
pca = PCA(n_components=0.95, random_state=7).fit(z(train))
spe = lambda X: ((z(X).values - pca.inverse_transform(pca.transform(z(X)))) ** 2).sum(axis=1)
spe_train = spe(train)
pca_thr = np.quantile(spe_train, 0.99)
pca_thr_strict = float(spe_train.max())
spe_hold = spe(holdout)
pca_hold_fp = int((spe_hold > pca_thr).sum())
pca_hold_fp_strict = int((spe_hold > pca_thr_strict).sum())

print(f"[{SYSTEM}] features {train.shape[1]} | train {len(train)}d holdout {len(holdout)}d")
print(f"iforest holdout FP {if_hold_fp}/{len(holdout)} | pca-spe holdout FP {pca_hold_fp}/{len(holdout)}")

rows = []
for sc in manifest["scenarios"]:
    f = daily_features(pd.read_parquet(DATA / f"{sc['file']}.parquet"))
    n = len(f)
    if_s = -iforest.score_samples(z(f))
    pca_s = spe(f)
    k_if = int((if_s > if_thr).sum())
    k_pca = int((pca_s > pca_thr).sum())
    k_if_strict = int((if_s > if_thr_strict).sum())
    k_pca_strict = int((pca_s > pca_thr_strict).sum())
    days_idx = f.index.astype(str)
    pca_strict_days = sorted(days_idx[pca_s > pca_thr_strict].tolist())
    scored_days = sorted(days_idx.tolist())  # PCA's day universe (audit D2)
    p_ifs = max(if_hold_fp_strict, 1) / max(len(holdout), 1)
    p_pcs = max(pca_hold_fp_strict, 1) / max(len(holdout), 1)
    sig_if_strict = binom_sf(k_if_strict, n, min(p_ifs, 1.0)) < 1e-3
    sig_pca_strict = binom_sf(k_pca_strict, n, min(p_pcs, 1.0)) < 1e-3
    p_if = max(if_hold_fp, 1) / max(len(holdout), 1)
    p_pca = max(pca_hold_fp, 1) / max(len(holdout), 1)
    sig_if = binom_sf(k_if, n, min(p_if, 1.0)) < 1e-3
    sig_pca = binom_sf(k_pca, n, min(p_pca, 1.0)) < 1e-3
    rows.append({"file": sc["file"], "family": sc["family"], "label": sc["label"],
                 "days": n, "iforest_days": k_if, "iforest_sig": sig_if,
                 "pca_days": k_pca, "pca_sig": sig_pca,
                 "iforest_days_strict": k_if_strict, "iforest_sig_strict": sig_if_strict,
                 "pca_days_strict": k_pca_strict, "pca_sig_strict": sig_pca_strict,
                 "pca_strict_flag_days": pca_strict_days,
                 "scored_days": scored_days})
    print(f"  {sc['label']:36s} iforest {k_if:>3}{'*' if sig_if else ' '} "
          f"pca {k_pca:>3}{'*' if sig_pca else ' '}")

det_if = sum(1 for r in rows if r["iforest_sig"])
det_pca = sum(1 for r in rows if r["pca_sig"])
print(f"\nmeaningfully detected: iforest {det_if}/{len(rows)} | pca {det_pca}/{len(rows)}")
Path("outputs").mkdir(exist_ok=True)
Path(f"outputs/baselines_{SYSTEM}.json").write_text(json.dumps({
    "system": SYSTEM, "iforest_holdout_fp": [if_hold_fp, len(holdout)],
    "pca_holdout_fp": [pca_hold_fp, len(holdout)],
    "iforest_holdout_fp_strict": [if_hold_fp_strict, len(holdout)],
    "pca_holdout_fp_strict": [pca_hold_fp_strict, len(holdout)],
    "train_days": len(train), "n_features": int(train.shape[1]),
    "scenarios": rows}, indent=2))
print(f"wrote outputs/baselines_{SYSTEM}.json")
