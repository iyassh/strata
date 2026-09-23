"""X9 (sensor noise at 1x/2x/4x) and X10 (first-8-days holdout) — robustness
of the deployed detector. Pre-registered: docs/plans/2026-09-23-x9-x10-robustness-prereg.md.

The detector is re-fitted per condition on the (noisy) healthy year; every
scored scenario is evaluated with strata.core.pipeline (the deployed path).
Committed scorecards give the clean reference. Machine time printed only.

    uv run python scripts/x9_x10_robustness.py [--only sdahu] -> outputs/x9_x10_robustness.json
"""
import json
import os
import sys
import time
import warnings
import zlib

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import strata.core.detection as _det
import strata.core.devices as _dev
import strata.core.frequency as _freq
import strata.core.oscillation as _osc
import strata.core.pipeline as _pipe
import strata.core.splits as _splits
from strata.core.pipeline import fit
from strata.core.splits import holdout_mask as _last_n
from strata.io.config import load_config

DEPLOYED = ["rules", "residual", "model", "device", "absence", "frequency", "oscillation"]
# Amendment 3: without the alignment-based channels (model, device, and absence, which reads the
# device model). On clean data their removal changes no detection count (ablation: conformance
# sole = 0; absence is meaningful on no scenario) and lowers SFPU's holdout FP from 4 to 1.
DEPLOYED_NO_ALIGN = ["rules", "residual", "frequency", "oscillation"]
NO_ALIGN = "--no-alignment" in sys.argv
NOISE = {"temp": 0.5, "flow_rel": 0.02, "pos": 0.01, "sp_rel": 0.02}


def family(canonical: str) -> str | None:
    c = canonical.upper()
    if any(k in c for k in ("_CMD", "STATUS", "OCCUPIED", "_SP")) and not c == "SA_SP":
        return None
    if "TEMP" in c or "_EWT_" in c or "_LWT_" in c or c.endswith("_EWT") or c.endswith("_LWT"):
        return "temp"
    if "FLOW" in c or "CFM" in c:
        return "flow"
    if "_POS" in c:
        return "pos"
    if c == "SA_SP":
        return "sp"
    return None


def add_noise(df: pd.DataFrame, cfg, dose: float, fname: str) -> pd.DataFrame:
    if dose == 0:
        return df
    rng = np.random.default_rng(zlib.crc32(fname.encode()))
    out = df.copy()
    for canonical, col in cfg.sensors.items():
        fam = family(canonical)
        if fam is None or col not in out.columns:
            continue
        v = out[col].to_numpy(dtype=float)
        if fam == "temp":
            v = v + rng.normal(0, NOISE["temp"] * dose, len(v))
        elif fam == "flow":
            v = v * (1 + rng.normal(0, NOISE["flow_rel"] * dose, len(v)))
        elif fam == "pos":
            v = np.clip(v + rng.normal(0, NOISE["pos"] * dose, len(v)), 0, 1)
        elif fam == "sp":
            v = v * (1 + rng.normal(0, NOISE["sp_rel"] * dose, len(v)))
        out[col] = v
    return out


def first_n_mask(case_ids: pd.Series, n: int) -> pd.Series:
    dates = pd.to_datetime(case_ids.str.split("__").str[0])
    return dates.dt.day <= n


def set_split(fn):
    for m in (_splits, _det, _dev, _freq, _osc, _pipe):
        m.holdout_mask = fn


def run_condition(system: str, cfg, man, dose: float, split_fn) -> dict:
    set_split(split_fn)
    try:
        return _run_condition(system, cfg, man, dose, split_fn)
    finally:
        set_split(_last_n)      # restored even if fit/evaluate raises (review item E)


def _run_condition(system: str, cfg, man, dose: float, split_fn) -> dict:
    hold_n = cfg.rules["detection"]["holdout_days_per_month"]
    hdf = add_noise(pd.read_parquet(f"data/processed/{system}/{man['healthy_file']}.parquet"), cfg, dose, man["healthy_file"])
    det = fit(cfg, hdf)
    if NO_ALIGN:     # Amendment 3: alignment-based channels dropped (their removal changes no clean scorecard)
        det.unit_model = None
        det.device_model = None
    sc = det.score(hdf)
    days = sc["universe"].index
    hold = split_fn(pd.Series(days.astype(str), index=days), hold_n).values
    union = pd.Series(False, index=days)
    for ch in (DEPLOYED_NO_ALIGN if NO_ALIGN else DEPLOYED):
        union = union | sc["channels"][ch].reindex(days).fillna(False)
    fp = int(union.values[hold].sum()); nh = int(hold.sum())
    detected, per = 0, {}
    for s in man["scenarios"]:
        if not s["is_fault"] or s.get("exclude"):
            continue
        df = add_noise(pd.read_parquet(f"data/processed/{system}/{s['file']}.parquet"), cfg, dose, s["file"])
        r = det.evaluate(df)
        per[s["file"]] = bool(r["detected"]); detected += int(r["detected"])
    return {"detected": detected, "n_scored": len(per), "holdout_fp_days": fp, "holdout_days": nh,
            "holdout_fp_rate": round(fp / max(nh, 1), 4), "per_scenario": per}


only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
from_artefact = "--from-artefact" in sys.argv     # recompute predictions/falsifiers from the committed systems block
out = {"pre_registration": "docs/plans/2026-09-23-x9-x10-robustness-prereg.md", "noise_1x": NOISE,
       "notes": ["noise is i.i.d. per-sample jitter (Amendment 1), not bias or drift",
                 "seeds are per file and shared across doses: common random numbers, doses perfectly rank-correlated",
                 "SA_SP is mapped on no system, so static pressure was never perturbed",
                 "clean_detected is the naive scorecard count (SDAHU 14, not the adjudicated 13)"],
       "systems": {}}
if from_artefact:
    out["systems"] = json.loads(Path("outputs/x9_x10_robustness.json").read_text())["systems"]
for system in ("sdahu", "pfpu", "sfpu"):
    if from_artefact or (only and system != only):
        continue
    cfg = load_config(f"configs/lbnl_{system}")
    man = yaml.safe_load(Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())
    card = json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]
    if NO_ALIGN:
        clean_det = sum(1 for c in card if c["is_fault"] and not c["excluded"]
                        and set(str(c["meaningful_channels"]).split("+")) & {"rules", "resid", "freq", "osc"})
        uch = json.loads(Path(f"outputs/union_fpr_{system}.json").read_text())["channels"]
        fp_dates = set()
        for ch, v in uch.items():
            if ch not in ("rate", "model", "device"):
                fp_dates |= set(v["holdout_fp_dates"])
        ufpr = {"holdout_fp_days": len(fp_dates)}
    else:
        clean_det = sum(1 for c in card if c["is_fault"] and not c["excluded"] and c["meaningful_channels"])
        ufpr = json.loads(Path(f"outputs/union_fpr_{system}.json").read_text())["union_minus_rate"]
    sysout = {"clean_detected": clean_det, "clean_holdout_fp_days": ufpr["holdout_fp_days"],
              "alignment_channels": not NO_ALIGN, "conditions": {}}
    arms = sys.argv[sys.argv.index("--arms") + 1].split(",") if "--arms" in sys.argv else None
    for name, dose, split in (("noise_1x", 1, _last_n), ("noise_2x", 2, _last_n), ("noise_4x", 4, _last_n),
                              ("split_first8", 0, first_n_mask)):
        if arms and name not in arms:      # Amendment 2: fan-powered stress arms dropped for compute
            continue
        t0 = time.time()
        sysout["conditions"][name] = run_condition(system, cfg, man, dose, split)
        r = sysout["conditions"][name]
        print(f"{system} {name:13s} detected {r['detected']}/{r['n_scored']} (clean {clean_det}) | holdout FP "
              f"{r['holdout_fp_days']}/{r['holdout_days']} (clean {ufpr['holdout_fp_days']}) | {time.time()-t0:.0f}s", flush=True)
    out["systems"][system] = sysout

pred, fired = {}, []
for s, v in out["systems"].items():
    c = v["conditions"]; n1 = c["noise_1x"]; sp = c["split_first8"]
    d1 = v["clean_detected"] - n1["detected"]
    stress = "noise_2x" in c and "noise_4x" in c
    pred[s] = {"P-X9.1_det_change_le_3": abs(d1) <= 3, "det_drop_1x": d1,     # two-sided, as pre-registered
               "P-X9.1_fpr_le_10pct": n1["holdout_fp_rate"] <= 0.10,
               "P-X9.2_monotone": (c["noise_4x"]["detected"] <= c["noise_2x"]["detected"] <= n1["detected"]) if stress else None,
               "stress_arms_run": stress,
               "P-X10.1_det_within_3": abs(v["clean_detected"] - sp["detected"]) <= 3,
               "P-X10.2_fpr_le_10pct": sp["holdout_fp_rate"] <= 0.10}
    if d1 > 3:
        fired.append(f"F-X9.a ({s}): detections fall by {d1} at 1x noise")
    if n1["holdout_fp_rate"] > 0.10:
        fired.append(f"F-X9.b ({s}): holdout FP {n1['holdout_fp_rate']:.3f} at 1x noise")
    if not (pred[s]["P-X10.1_det_within_3"] and pred[s]["P-X10.2_fpr_le_10pct"]):
        fired.append(f"F-X10.a ({s}): split-dependent (det {sp['detected']} vs {v['clean_detected']}, fp {sp['holdout_fp_rate']:.3f})")
out["predictions"] = pred
out["falsifiers_fired"] = fired
path = Path("outputs/x9_x10_robustness.json")
if only and path.exists() and not from_artefact:   # merge a partial run: this system's rows and falsifiers replace its old ones
    prev = json.loads(path.read_text()); prev["systems"].update(out["systems"]); prev["predictions"].update(pred)
    kept = [f for f in prev.get("falsifiers_fired", []) if f"({only})" not in f]
    prev["falsifiers_fired"] = sorted(set(kept) | set(fired)); prev["notes"] = out["notes"]; out = prev
path.write_text(json.dumps(out, indent=2) + "\n")
print("predictions:", json.dumps(pred, indent=1)); print("falsifiers fired:", fired or "none"); print("wrote", path)
