"""X31 — field conditions injected into the simulated files: sensor error and
feedback quantisation, change-of-value logging with gaps, schedule shifts, and
all three. Pre-registration: docs/plans/2026-09-24-x31-field-conditions-prereg.md
    uv run python scripts/x31_field_conditions.py --system sdahu -> outputs/x31_field_conditions_<system>.json
Detector: deployed facade re-fitted on the perturbed fault-free year, alignment channels off
(X9/X10 Amendment 3), X25 gate, last-8 holdout.
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
import strata.core.detection as _detmod
from strata.core.pipeline import fit
from strata.core.splits import holdout_mask
from strata.io.config import load_config


def _no_alignment(*_a, **_k):
    raise ImportError("alignment-based strata disabled (X31; X9/X10 Amendment 3)")
_detmod.build_detector = _no_alignment
DEPLOYED = ["rules", "residual", "absence", "frequency", "oscillation"]


def family(canonical: str):
    c = canonical.upper()
    if c in ("OCCUPIED", "Datetime") or "STATUS" in c or c.endswith("_CMD") or "_SP" in c:
        return None
    if "TEMP" in c or c.endswith("_EWT") or c.endswith("_LWT") or "_EWT_" in c or "_LWT_" in c:
        return "temp"
    if "FLOW" in c or "GPM" in c or "CFM" in c:
        return "flow"
    if c.endswith("_POS") or "DMPR" in c and "POS" in c:
        return "pos"
    return None


def field_noise(df, cfg, rng):
    out = df.copy()
    for canonical, col in cfg.sensors.items():
        fam = family(canonical)
        if fam is None or col not in out.columns:
            continue
        v = out[col].to_numpy(dtype=float)
        if fam == "temp":
            v = v + rng.normal(0, 0.9, len(v))
        elif fam == "flow":
            v = v * (1 + rng.normal(0, 0.02, len(v)))
        elif fam == "pos":
            v = np.clip(np.round(v / 0.05) * 0.05 + rng.normal(0, 0.01, len(v)), 0, 1)
        out[col] = v
    return out


def cov_gaps(df, cfg, rng):
    out = df.copy()
    dead = {"temp": 0.5, "pos": 0.02, "flow": None}
    for canonical, col in cfg.sensors.items():
        fam = family(canonical)
        if fam is None or col not in out.columns:
            continue
        v = out[col].to_numpy(dtype=float); kept = v.copy(); last = v[0]
        for i in range(1, len(v)):
            thr = dead[fam] if fam != "flow" else 0.02 * max(abs(last), 1e-9)
            if abs(v[i] - last) > thr:
                last = v[i]
            kept[i] = last
        out[col] = kept
    n = len(out); n_gap_blocks = int(0.02 * n / 30)
    starts = rng.integers(0, max(n - 30, 1), size=n_gap_blocks)
    drop = np.zeros(n, dtype=bool)
    for s in starts:
        drop[s:s + 30] = True
    return out.loc[~drop].reset_index(drop=True)


def schedule(df, cfg, seed_calendar):
    occ = cfg.sensors.get("OCCUPIED")
    if occ is None or occ not in df.columns:
        return df
    out = df.copy(); dt = out["Datetime"]; day = dt.dt.date
    early_days, holidays = seed_calendar
    o = out[occ].to_numpy(dtype=float, copy=True)   # pandas copy-on-write returns a read-only view otherwise
    for d in holidays:
        o[(day == d).to_numpy()] = 0.0
    # optimum start: shift the day's occupied block 30 minutes earlier
    for d in early_days:
        m = (day == d).to_numpy()
        idx = np.where(m)[0]
        if len(idx) < 60:
            continue
        seg = o[idx]; shifted = np.concatenate([seg[30:], np.repeat(seg[-1], 30)])
        o[idx] = shifted
    out[occ] = o
    return out


def calendar(df, seed):
    rng = np.random.default_rng(seed)
    days = sorted(set(df["Datetime"].dt.date)); wk = [d for d in days if d.weekday() < 5]
    early = set(rng.choice(wk, size=int(0.2 * len(wk)), replace=False).tolist())
    hol = set(rng.choice([d for d in wk if d not in early], size=6, replace=False).tolist())
    return early, hol


def perturb(df, cfg, arm, fname, cal):
    rng = np.random.default_rng(zlib.crc32(fname.encode()))
    if arm in ("field_noise", "combined"):
        df = field_noise(df, cfg, rng)
    if arm in ("cov_gaps", "combined"):
        df = cov_gaps(df, cfg, rng)
    if arm in ("schedule", "combined"):
        df = schedule(df, cfg, cal)
    return df


def run(system):
    cfg = load_config(f"configs/lbnl_{system}"); man = yaml.safe_load(Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())
    hold_n = cfg.rules["detection"]["holdout_days_per_month"]
    card = json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]
    clean_det = sum(1 for c in card if c["is_fault"] and not c["excluded"] and set(str(c["meaningful_channels"]).split("+")) & {"rules", "resid", "freq", "osc", "absence"})
    uch = json.loads(Path(f"outputs/union_fpr_{system}.json").read_text())["channels"]
    clean_fp = len(set().union(*[set(v["holdout_fp_dates"]) for k, v in uch.items() if k not in ("rate", "model", "device")]))
    hdf0 = pd.read_parquet(f"data/processed/{system}/{man['healthy_file']}.parquet")
    cal = calendar(hdf0, zlib.crc32(system.encode()))
    out_path = Path(f"outputs/x31_field_conditions_{system}.json")
    arms = sys.argv[sys.argv.index("--arms") + 1].split(",") if "--arms" in sys.argv else ["field_noise", "cov_gaps", "schedule", "combined"]
    out = json.loads(out_path.read_text()) if out_path.exists() and "--arms" in sys.argv else {"clean_detected_no_alignment": clean_det, "clean_holdout_fp_no_alignment": clean_fp, "calendar": {"optimum_start_days": len(cal[0]), "holidays": [str(d) for d in sorted(cal[1])]}, "conditions": {}}
    for arm in arms:
        t0 = time.time()
        try:
            hdf = perturb(hdf0, cfg, arm, man["healthy_file"], cal)
            det = fit(cfg, hdf); det.unit_model = None; det.device_model = None
            sc = det.score(hdf); days = sc["universe"].index
            hold = holdout_mask(pd.Series(days.astype(str), index=days), hold_n).values
            union = pd.Series(False, index=days); per_ch = {}
            for ch in DEPLOYED:
                s = sc["channels"][ch].reindex(days).fillna(False); union = union | s; per_ch[ch] = int(s.values[hold].sum())
            fp, nh = int(union.values[hold].sum()), int(hold.sum())
            per, detected = {}, 0
            for s in man["scenarios"]:
                if not s["is_fault"] or s.get("exclude"):
                    continue
                df = perturb(pd.read_parquet(f"data/processed/{system}/{s['file']}.parquet"), cfg, arm, s["file"], cal)
                r = det.evaluate(df); per[s["file"]] = bool(r["detected"]); detected += int(r["detected"])
            res = {"detected": detected, "n_scored": len(per), "holdout_fp_days": fp, "holdout_days": nh, "per_channel_fp": per_ch, "per_scenario": per, "seconds": round(time.time() - t0)}
            print(f"[{system}] {arm:12s} detected {detected}/{len(per)} (clean {clean_det}) | holdout FP {fp}/{nh} (clean {clean_fp}) per-channel {per_ch} | {res['seconds']}s", flush=True)
        except Exception as exc:
            res = {"error": f"{type(exc).__name__}: {exc}"}; print(f"[{system}] {arm:12s} NOT EVALUATED {exc}", flush=True)
        out["conditions"][arm] = res
        out_path.write_text(json.dumps(out, indent=2) + "\n")   # written after every arm


if __name__ == "__main__":
    run(sys.argv[sys.argv.index("--system") + 1])
