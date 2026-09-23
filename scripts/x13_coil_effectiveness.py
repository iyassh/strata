"""X13 — coil-effectiveness residual, (EWT - LWT) / GPM per terminal unit.

Pre-registered (with the fault-informed-design disclosure) in
docs/plans/2026-09-23-x13-coil-effectiveness-prereg.md. Bands from the
fault-free train days only; holdout gives the false-alarm rate; the
residual channel's own calibrate_band / flag_days / significance gate.
Nothing here touches the deployed configs or the committed scorecards.

    uv run python scripts/x13_coil_effectiveness.py -> outputs/x13_coil_effectiveness.json
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

from strata.core.residuals import calibrate_band, flag_days
from strata.core.significance import residual_significant
from strata.core.splits import holdout_mask
from strata.io.config import load_config

MIN_WIDTH, MARGIN, SUSTAINED = 2.0, 1.0, 120     # pre-registered
# scorecards export these six channels' day lists (absence is not exported);
# a first run used non-existent keys for three channels — corrected in review.
# The pre-registration says "9 fouling scenarios"; the scored universe holds
# 12 (six per fan-powered system), of which 10 are deployed misses. The
# falsifier threshold (< 4 significant) fires under either count.
DEPLOYED = ["rules", "residual", "model", "device", "freq", "osc"]
ZONES = "IWSE"
FOULING = "ReheatCoilFouling"


def daily_scores(df: pd.DataFrame, cfg, z: str) -> pd.DataFrame:
    w = df.rename(columns={v: k for k, v in cfg.sensors.items()}).sort_values("Datetime")
    need = [f"RH_EWT_{z}", f"RH_LWT_{z}", f"RH_FLOW_{z}", f"RH_VLV_POS_{z}", "OCCUPIED"]
    if any(c not in w.columns for c in need):
        return pd.DataFrame(columns=["case_id", "score", "window_min"])
    gated = (w["OCCUPIED"] > 0.5) & (w[f"RH_VLV_POS_{z}"] > 0.10) & (w[f"RH_FLOW_{z}"] > 0.10)
    stat = ((w[f"RH_EWT_{z}"] - w[f"RH_LWT_{z}"]) / w[f"RH_FLOW_{z}"]).where(gated)
    diffs = w["Datetime"].diff().dropna().dt.total_seconds() / 60.0
    interval = float(diffs.median()) if len(diffs) else 1.0
    g = pd.DataFrame({"case_id": w["Datetime"].dt.date.astype(str), "r": stat}).groupby("case_id")["r"]
    out = pd.DataFrame({"score": g.median(), "window_min": g.count() * interval}).reset_index()
    out.loc[out["window_min"] < SUSTAINED, "score"] = float("nan")
    return out


out = {"pre_registration": "docs/plans/2026-09-23-x13-coil-effectiveness-prereg.md",
       "design_disclosure": "fault-informed statistic (chosen after inspecting three fouling files); "
                            "thresholds from fault-free train days only",
       "statistic": "(RH_EWT - RH_LWT) / RH_FLOW per terminal unit, daily median over gated minutes",
       "band": {"min_width": MIN_WIDTH, "min_exceedance": MARGIN, "sustained_min": SUSTAINED},
       "systems": {}}
for system in ("pfpu", "sfpu"):
    cfg = load_config(f"configs/lbnl_{system}")
    man = yaml.safe_load(Path(f"configs/lbnl_{system}/scenarios.yaml").read_text())
    hold_n = cfg.rules["detection"]["holdout_days_per_month"]
    card = {s["file"]: s for s in json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())["scenarios"]}
    hdf = pd.read_parquet(f"data/processed/{system}/{man['healthy_file']}.parquet")
    # deployed residual convention (scripts/benchmark.py): rule-days summed over
    # zones on both sides of the gate; the union-of-days view is kept beside it
    bands, hold_fp, hold_n_days, hold_fp_dates, disabled = {}, 0, 0, set(), []
    for z in ZONES:
        hs = daily_scores(hdf, cfg, z)
        hm = holdout_mask(hs["case_id"], hold_n)
        b = calibrate_band(hs, ~hm, min_width=MIN_WIDTH)
        if not (b[0] == b[0] and b[1] == b[1]):      # NaN band: no evaluable healthy day
            disabled.append(z); bands[z] = None; continue
        bands[z] = b
        hf = flag_days(hs[hm.values], b, min_margin=MARGIN)
        hold_fp_dates |= set(hf.loc[hf["flagged"], "case_id"])
        hold_fp += int(hf["flagged"].sum()); hold_n_days += int(hf["evaluable"].sum())
    ufpr = json.loads(Path(f"outputs/union_fpr_{system}.json").read_text())
    deployed_fp = set()
    for ch, v in ufpr["channels"].items():
        if ch != "rate":
            deployed_fp |= set(v.get("holdout_fp_dates", []))
    joint = deployed_fp | hold_fp_dates
    sysout = {"bands_F_per_gpm": {z: ([round(b[0], 2), round(b[1], 2)] if b else None) for z, b in bands.items()},
              "zones_disabled_no_evaluable_healthy_day": disabled,
              "denominator_convention": "rule-days summed over zones (deployed residual convention); "
                                        "unique-day counts use the union of days",
              "holdout_fp_rule_days": hold_fp, "holdout_evaluable_rule_days": hold_n_days,
              "holdout_fp_days": len(hold_fp_dates),
              "holdout_fp_dates": sorted(hold_fp_dates),
              "joint_fpr": {"deployed_union_minus_rate_fp_days": len(deployed_fp),
                            "with_x13_fp_days": len(joint), "holdout_days": ufpr["holdout_days"],
                            "with_x13_rate": round(len(joint) / ufpr["holdout_days"], 4)},
              "scenarios": []}
    print(f"== {system}: bands {sysout['bands_F_per_gpm']} | holdout FP {hold_fp}/{hold_n_days} | "
          f"joint FP {len(deployed_fp)} -> {len(joint)} of {ufpr['holdout_days']}")
    for sc in man["scenarios"]:
        if not sc["is_fault"] or sc.get("exclude"):
            continue
        df = pd.read_parquet(f"data/processed/{system}/{sc['file']}.parquet")
        flagged, flag_rd, n_win, by_zone = set(), 0, 0, {}
        for z in ZONES:
            if bands[z] is None:
                continue
            s = daily_scores(df, cfg, z)
            f = flag_days(s, bands[z], min_margin=MARGIN)
            zf = set(f.loc[f["flagged"], "case_id"]); flagged |= zf
            by_zone[z] = len(zf); flag_rd += len(zf); n_win += int(f["evaluable"].sum())
        sig = residual_significant(flag_rd, n_win, hold_fp, hold_n_days)
        c = card[sc["file"]]
        missing = [k for k in DEPLOYED if k not in c.get("flag_days", {})]
        assert not missing, f"scorecard flag_days lacks {missing} (L36: assert the keys you compare against)"
        union = set()
        for ch in DEPLOYED:
            union |= set(c.get("flag_days", {}).get(ch, []))
        row = {"file": sc["file"], "fouling": FOULING in sc["file"], "x13_flag_days": len(flagged),
               "x13_flag_rule_days": flag_rd, "n_evaluable_rule_days": n_win,
               "significant": bool(sig), "by_zone": by_zone,
               "deployed_detected": bool(c["meaningful_channels"]),
               "unique_days_vs_deployed": len(flagged - union)}
        sysout["scenarios"].append(row)
        print(f"  {sc['file'][:38]:38s} x13 {len(flagged):3d}/{n_win} {'SIG' if sig else '   '} "
              f"| deployed {'DET' if row['deployed_detected'] else 'miss'} | unique {row['unique_days_vs_deployed']:3d} | {by_zone}")
    out["systems"][system] = sysout

rows = [r for s in out["systems"].values() for r in s["scenarios"]]
foul = [r for r in rows if r["fouling"]]
foul_sig = [r["file"] for r in foul if r["significant"]]
newly = [r["file"] for r in rows if r["significant"] and not r["deployed_detected"]]
worst_joint = max(s["joint_fpr"]["with_x13_rate"] for s in out["systems"].values())
worst_own = max(s["holdout_fp_days"] for s in out["systems"].values())
pred = {"P1_fouling_sig_ge_6": len(foul_sig) >= 6, "P1_fouling_sig": foul_sig, "n_fouling": len(foul),
        "P2_own_fp_le_3": worst_own <= 3, "P3_joint_fp_le_8_of_96": all(
            s["joint_fpr"]["with_x13_fp_days"] <= 8 for s in out["systems"].values()),
        "newly_detected_scenarios": newly, "other_significant": [r["file"] for r in rows if r["significant"] and not r["fouling"]]}
fired = []
if worst_joint > 0.10:
    fired.append("F-X13.a: joint false-alarm rate > 10%")
if len(foul_sig) < 4:
    fired.append("F-X13.b: fewer than 4 of 9 fouling scenarios significant")
out["predictions"] = pred
out["falsifiers_fired"] = fired
Path("outputs/x13_coil_effectiveness.json").write_text(json.dumps(out, indent=2) + "\n")
print("\npredictions:", json.dumps(pred, indent=1))
print("falsifiers fired:", fired or "none")
print("wrote outputs/x13_coil_effectiveness.json")
