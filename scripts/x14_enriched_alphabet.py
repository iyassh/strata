"""X14 — enriched state alphabet: was the discovered model starved of vocabulary?

Pre-registered: docs/plans/2026-09-23-x14-enriched-alphabet-prereg.md.
Adds healthy-derived band states (<signal>_high above the occupied train
90th percentile; <signal>_low at or below the 10th) for every actuator
position and flow signal, keeps the alphabet wall, rebuilds every state
channel with strata.core.pipeline.fit/evaluate, and asks whether any of
the 13 missed scenarios becomes significant. Rules/residual channels are
untouched by construction.

    uv run python scripts/x14_enriched_alphabet.py -> outputs/x14_enriched_alphabet.json
"""
import json
import os
import sys
import time
import warnings

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")

from pathlib import Path

import pandas as pd
import yaml

from strata.core.pipeline import fit
from strata.core.significance import P_SIG, binom_sf
from strata.core.sojourn import (build_sojourn_detector, classify_sojourn_days,
                                 daily_sojourn_stats)
from strata.core.splits import holdout_mask
from strata.hvac.events import abstract_events
from strata.io.config import load_config

STATE_CH = ["model", "device", "absence", "frequency"]
ZONES = "IWSE"


def enrich(cfg, hdf: pd.DataFrame, hold_n: int) -> dict:
    w = hdf.rename(columns={v: k for k, v in cfg.sensors.items()})
    day = w["Datetime"].dt.date.astype(str)
    train = ~holdout_mask(day, hold_n).values
    occ = (w["OCCUPIED"] > 0.5).values & train
    # Amendment 1: setpoints excluded (never flows), 15-minute dwell on every added band
    sigs = [k for k in cfg.sensors if (k.endswith("_POS") or k.startswith("RH_FLOW_") or k.startswith("ZONE_FLOW_"))
            and "_SP" not in k and k in w.columns]
    DWELL = {"min_dwell_min": 15}
    added = {}
    for s in sigs:
        v = w.loc[occ, s].dropna()
        if v.empty:
            continue
        q10, q90 = float(v.quantile(0.10)), float(v.quantile(0.90))
        if not (q90 - q10 > 1e-6):
            continue
        tag = {}
        if s[-2] == "_" and s[-1] in ZONES:
            tag = {"stratum": "device", "device": f"TU_{s[-1]}"}
        cfg.rules["events"][f"x14_{s}_high"] = {"kind": "mode", "alphabet": "state", "signal": s, "on_above": q90,
                                               "on_event": f"{s}_high_entered", "off_event": f"{s}_high_exited", **tag, **DWELL}
        cfg.rules["events"][f"x14_{s}_low"] = {"kind": "window", "alphabet": "state", "signal": s, "low": -1e9, "high": q10,
                                              "enter_event": f"{s}_low_entered", "exit_event": f"{s}_low_exited", **tag, **DWELL}
        added[s] = {"q10": round(q10, 4), "q90": round(q90, 4)}
    return added


out = {"pre_registration": "docs/plans/2026-09-23-x14-enriched-alphabet-prereg.md", "systems": {}}
t_all = time.time()
for system in ("sdahu", "pfpu", "sfpu"):
    t0 = time.time()
    cfg = load_config(f"configs/lbnl_{system}")
    man = yaml.safe_load(Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())
    hold_n = cfg.rules["detection"]["holdout_days_per_month"]
    card = {s["file"]: s for s in json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]}
    hdf = pd.read_parquet(f"data/processed/{system}/{man['healthy_file']}.parquet")
    added = enrich(cfg, hdf, hold_n)
    n_state = sum(1 for r in cfg.rules["events"].values() if r.get("alphabet", "state") == "state"
                  and r.get("kind") in ("mode", "window", "occupancy"))
    det = fit(cfg, hdf)
    # Amendment 2: on the fan-powered units the alignment-based channels
    # (model, device, absence) are infeasible on the enriched alphabet (fit
    # 1061 s; the first PFPU scenario had not finished after 47 min). They
    # are dropped there and marked not evaluated; SDAHU keeps its model channel.
    alignment_channels_evaluated = system == "sdahu"
    if not alignment_channels_evaluated:
        det.unit_model = None
        det.device_model = None
    hlog = abstract_events(hdf, cfg)
    tdet = build_sojourn_detector(daily_sojourn_stats(hlog, cfg), hold_n)
    # healthy-holdout false alarms of the enriched state channels
    sc = det.score(hdf)
    days = sc["universe"].index
    hold = holdout_mask(pd.Series(days.astype(str), index=days), hold_n).values
    state_union = pd.Series(False, index=days)
    for ch in STATE_CH:
        state_union = state_union | sc["channels"][ch].reindex(days).fillna(False)
    hs = daily_sojourn_stats(hlog, cfg)
    hcl = classify_sojourn_days(tdet, hs).set_index("day")["flagged"] if tdet else pd.Series(dtype=bool)
    time_fp = set(hcl[hcl].index) & set(days[hold].astype(str))
    fp_days = set(days[hold & state_union.values].astype(str)) | time_fp
    sysout = {"added_signals": added, "n_added_events": 2 * len(added), "n_state_pairs_total": n_state,
              "alignment_channels_evaluated": alignment_channels_evaluated,
              "fit_seconds_stdout_only_note": "fit time printed, not committed (machine-dependent)",
              "holdout_days": int(hold.sum()), "state_channels_holdout_fp_days": len(fp_days),
              "time_holdout_fp_days": len(time_fp), "scenarios": []}
    print(f"== {system}: +{2*len(added)} state events ({len(added)} signals); fit {time.time()-t0:.0f}s; "
          f"holdout FP state∪time {len(fp_days)}/{int(hold.sum())}", flush=True)
    p0 = max(tdet.holdout_fp_days, 1) / max(tdet.holdout_days, 1) if tdet else 1.0
    for s in man["scenarios"]:
        if not s["is_fault"] or s.get("exclude"):
            continue
        t1 = time.time()
        df = pd.read_parquet(f"data/processed/{system}/{s['file']}.parquet")
        r = det.evaluate(df)
        sig = {ch: (bool(r["significant"].get(ch, False)) if (alignment_channels_evaluated or ch == "frequency") else None)
               for ch in STATE_CH}
        log = abstract_events(df, cfg)
        st = daily_sojourn_stats(log, cfg)
        cl = classify_sojourn_days(tdet, st) if tdet else None
        tf = int(cl["flagged"].sum()) if cl is not None else 0
        sig["time"] = bool(cl is not None and binom_sf(tf, len(cl), p0) < P_SIG)
        c = card[s["file"]]
        row = {"file": s["file"], "deployed_detected": bool(c["meaningful_channels"]),
               "deployed_model_sig": "model" in str(c["meaningful_channels"]),
               "enriched_sig": sig, "enriched_any_state": any(sig.values()),
               "counts": {ch: int(r["counts"].get(ch, 0)) for ch in STATE_CH}, "time_flag_days": tf}
        sysout["scenarios"].append(row)
        print(f"  {s['file'][:38]:38s} deployed {'DET' if row['deployed_detected'] else 'miss'} | enriched "
              f"{[k for k, v in sig.items() if v]} | counts {row['counts']} time {tf} | {time.time()-t1:.0f}s", flush=True)
    out["systems"][system] = sysout

rows = [(s, r) for s, v in out["systems"].items() for r in v["scenarios"]]
missed = [(s, r) for s, r in rows if not r["deployed_detected"]]
newly = [r["file"] for s, r in missed if r["enriched_any_state"]]
model_now = sum(1 for s, r in rows if r["enriched_sig"]["model"]); model_was = sum(1 for s, r in rows if r["deployed_model_sig"])
fp_ok = all((v["state_channels_holdout_fp_days"] <= (9 if s == "sdahu" else 10)) for s, v in out["systems"].items())
pred = {"P1_newly_detected_ge_1": len(newly) >= 1, "P1_newly_detected": newly, "n_missed": len(missed),
        "P2_fp_within_budget": fp_ok, "P3_model_sig_ge_deployed": model_now >= model_was,
        "model_sig_enriched": model_now, "model_sig_deployed": model_was}
fired = []
if not fp_ok:
    fired.append("F-X14.a: enriched state channels exceed the false-alarm budget")
if not pred["P1_newly_detected_ge_1"]:
    fired.append("F-X14.b: no missed scenario becomes significant — vocabulary was not the limit")
out.update({"n_scored": len(rows), "predictions": pred, "falsifiers_fired": fired})
Path("outputs/x14_enriched_alphabet.json").write_text(json.dumps(out, indent=2) + "\n")
print("\npredictions:", json.dumps(pred, indent=1))
print("falsifiers fired:", fired or "none")
print(f"wrote outputs/x14_enriched_alphabet.json ({time.time()-t_all:.0f}s)")
