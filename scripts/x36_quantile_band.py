"""X36 — quantile bands (p2/p98 of training-day scores) as an alternative residual calibration, evaluated
through the facade against the deployed extreme-band calibration on every system. Not an adoption.
Pre-registration: docs/plans/2026-09-27-x36-quantile-band-prereg.md

    uv run python scripts/x36_quantile_band.py [--systems a,b] -> outputs/x36_quantile_band.json
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
HEALTHY = {"sdahu": "AHU_annual", "pfpu": "PFPU_FaultFree", "sfpu": "SFPU_FaultFree", "ddahu": "DualDuct_FaultFree", "fcu": "FCU_FaultFree"}
DEPLOYED = ["rules", "residual", "absence", "frequency", "oscillation"]
EDGE = ["PFPU_ReheatCoilFouling_Airside_Moderate", "PFPU_ReheatCoilFouling_Airside_Severe", "PFPU_SensorBias_RMTEMP_+2C", "SFPU_ReheatCoilFouling_Airside_Moderate", "DualDuct_Fouling_Heating_Waterside_Minor"]
Q = 0.02


def quantile_band(healthy_scores, train_mask, min_width=0.0):
    train = healthy_scores.loc[train_mask, "score"].dropna()
    lo, hi = float(train.quantile(Q)), float(train.quantile(1 - Q))
    if hi - lo < min_width:
        mid = (lo + hi) / 2; lo, hi = mid - min_width / 2, mid + min_width / 2
    return lo, hi


def run(system, arm):
    import strata.core.detection as detmod
    import strata.core.pipeline as pipemod
    import strata.core.residuals as resmod
    from strata.core.splits import holdout_mask
    from strata.io.config import load_config

    def _off(*_a, **_k):
        raise ImportError("alignment off (X36)")
    detmod.build_detector = _off
    orig = resmod.calibrate_band
    if arm == "quantile":
        pipemod.calibrate_band = quantile_band
    else:
        pipemod.calibrate_band = orig
    cfg = load_config(str(REPO / f"configs/lbnl_{system}")); man = yaml.safe_load((REPO / f"configs/lbnl_{system}/scenarios.yaml").read_text())
    hdf = pd.read_parquet(REPO / f"data/processed/{system}/{man['healthy_file']}.parquet")
    det = pipemod.fit(cfg, hdf); det.unit_model = None; det.device_model = None
    sc = det.score(hdf); days = sc["universe"].index
    hold = holdout_mask(pd.Series(days.astype(str), index=days), cfg.rules["detection"]["holdout_days_per_month"]).values
    union = pd.Series(False, index=days); per_ch = {}
    for ch in DEPLOYED:
        s = sc["channels"][ch].reindex(days).fillna(False); union = union | s; per_ch[ch] = int(s.values[hold].sum())
    per = {}
    for s in man["scenarios"]:
        if not s["is_fault"] or s.get("exclude"):
            continue
        r = det.evaluate(pd.read_parquet(REPO / f"data/processed/{system}/{s['file']}.parquet")); per[s["file"]] = bool(r["detected"])
    return {"detected": sum(per.values()), "n_scored": len(per), "holdout_fp_days": int(union.values[hold].sum()), "holdout_days": int(hold.sum()), "per_channel_fp": per_ch,
            "per_scenario": per, "bands": {k: [float(v[0]), float(v[1])] for k, v in det.residual_bands.items()}}


def main() -> int:
    systems = sys.argv[sys.argv.index("--systems") + 1].split(",") if "--systems" in sys.argv else list(HEALTHY)
    out = {"prereg": "docs/plans/2026-09-27-x36-quantile-band-prereg.md", "quantile": Q, "systems": {}}
    p1 = p2 = p4 = True; gained_all = []
    for s in systems:
        ext = run(s, "extreme"); qua = run(s, "quantile")
        gained = sorted(f for f in qua["per_scenario"] if qua["per_scenario"][f] and not ext["per_scenario"][f])
        lost = sorted(f for f in qua["per_scenario"] if ext["per_scenario"][f] and not qua["per_scenario"][f])
        row = {"extreme": {k: v for k, v in ext.items() if k not in ("per_scenario", "bands")}, "quantile": {k: v for k, v in qua.items() if k not in ("per_scenario", "bands")},
               "gained": gained, "lost": lost, "edge_recoveries_kept": [f for f in EDGE if f in qua["per_scenario"] and qua["per_scenario"][f]],
               "edge_recoveries_lost": [f for f in EDGE if f in qua["per_scenario"] and not qua["per_scenario"][f]],
               "band_width_ratio_median": float(pd.Series([(qua["bands"][k][1] - qua["bands"][k][0]) / max(ext["bands"][k][1] - ext["bands"][k][0], 1e-12) for k in ext["bands"]]).median())}
        out["systems"][s] = row; gained_all += gained
        dfp = qua["holdout_fp_days"] - ext["holdout_fp_days"]
        p1 &= (dfp <= 3 and qua["holdout_fp_days"] <= 10); p2 &= not row["edge_recoveries_lost"]; p4 &= not lost
        print(f"[{s}] extreme {ext['detected']}/{ext['n_scored']} fp {ext['holdout_fp_days']} | quantile {qua['detected']}/{qua['n_scored']} fp {qua['holdout_fp_days']} | gained {gained} lost {lost} | edge lost {row['edge_recoveries_lost']} | width ratio {row['band_width_ratio_median']:.2f}", flush=True)
    out["predictions"] = {"P1_fp_rise_le_3_and_le_10": p1, "P2_edge_recoveries_kept": p2, "P3_ge_2_new_detections": len(gained_all) >= 2, "P3_gained": gained_all, "P4_no_loss": p4}
    fired = []
    if not p1: fired.append("F-X36.a: false alarms rose beyond the bar")
    if not p4: fired.append("F-X36.b: a detection was lost under narrower bands")
    out["falsifiers_fired"] = fired
    (REPO / "outputs/x36_quantile_band.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["predictions"], indent=1)); print("falsifiers:", fired or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
