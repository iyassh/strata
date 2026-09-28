"""X38: the traditional-rules baseline — ASHRAE Guideline 36 via open-fdd, REPAIRED (2026-09-27).

Grades current commercial practice on STRATA's exam. Pre-registration (repair, scoring, predictions):
  docs/plans/2026-09-27-x38-guideline36-repaired-prereg.md
The 2026-09-11 artefacts (docs/plans/2026-09-11-openfdd-prereg.md) are VOID and live in outputs/void/.

Usage:
  uv run python scripts/openfdd_baseline.py sdahu|pfpu|sfpu       -> outputs/openfdd_baseline_<system>.json
  uv run python scripts/openfdd_baseline.py --ledger               -> outputs/x38_guideline36.json

No open-fdd rule parameter is altered: the installed defaults are the as-deployed condition.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

AHU_RULES = [f"FC{i}" for i in range(1, 16)]                                   # Guideline 36 air-handler battery
TU_RULES = ["VAV-1", "VAV-2", "VAV-3", "VAV-4", "VAV-5", "VAV-6", "VAV-7", "VAV-REHEAT", "VAV-AHU-LEAVE", "SCHED-247", "PID-HUNT-1"]
ZONES = ["I", "W", "S", "E"]
E3_CONSTANT = 401.85999   # ERRATA E3: healthy SA_SP carries it added; every fault file's SA_SPSPT carries it subtracted
CONFIG_DIR = {"sdahu": "lbnl_sdahu", "pfpu": "lbnl_pfpu", "sfpu": "lbnl_sfpu"}
TIME_COL = "Datetime"

_SHARED = {"outside-air-temp": "OA_TEMP", "discharge-air-temp": "SA_TEMP", "discharge-air-temp-sp": "SA_TEMPSPT", "mixed-air-temp": "MA_TEMP",
           "return-air-temp": "RA_TEMP", "cooling-valve": "CHWC_VLV", "outside-air-damper": "OA_DMPR", "duct-static-pressure": "SA_SP",
           "duct-static-pressure-sp": "SA_SPSPT", "vav-total-airflow": "SA_CFM"}
AHU_ROLE_MAP = {
    # SDAHU: constant-speed fan (SF_SPD one value); no heating coil, no coil air temperatures -> FC5/FC7/FC14/FC15 not applicable
    "sdahu": {**_SHARED, "fan-cmd": "SF_SPD", "fan-status": "SF_SPD_DM"},
    # FPU air handler: SF_SPD is the speed command, SF_CS binary status; coil AIR-side temperatures (repair 2):
    "pfpu": {**_SHARED, "fan-cmd": "SF_SPD", "fan-status": "SF_CS", "heating-valve": "HWC_VLV",
             "cooling-coil-entering-temp": "HWC_DAT", "cooling-coil-leaving-temp": "CHWC_DAT",
             "heating-coil-entering-temp": "MA_TEMP", "heating-coil-leaving-temp": "HWC_DAT"},
}
AHU_ROLE_MAP["sfpu"] = dict(AHU_ROLE_MAP["pfpu"])


def tu_role_map(z: str) -> dict:
    return {"zone-air-temp": f"RM_TEMP_{z}", "reheat-valve": f"RH_VLV_{z}", "damper": f"VAV_DMPR_{z}", "zone-airflow": f"VAV_PM_CFM_{z}",
            "vav-discharge-air-temp": f"VAV_DAT_{z}", "vav-inlet-air-temp": "SA_TEMP", "ahu-discharge-air-temp": "SA_TEMP",
            "outside-air-temp": "OA_TEMP", "occupied": "SYS_CTL", "fan-status": f"VAV_FAN_CS_{z}", "fan-cmd": f"VAV_FAN_CS_{z}"}


def time_index(df: pd.DataFrame) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(df[TIME_COL]))


def day_key(index) -> pd.Index:
    return pd.Index(pd.DatetimeIndex(index).strftime("%Y-%m-%d"))


def to_frame(df: pd.DataFrame, role_map: dict, system: str, healthy: bool) -> pd.DataFrame:
    out = df.copy(); out.index = time_index(df)
    if system == "sdahu":   # repair 3: additive E3 correction by file branch
        if healthy:
            out["SA_SP"] = out["SA_SP"] - E3_CONSTANT
        else:
            out["SA_SPSPT"] = out["SA_SPSPT"] + E3_CONSTANT
    for role, col in role_map.items():
        if col in out.columns:
            out[role] = pd.to_numeric(out[col], errors="coerce")
    if "occupied" in out.columns:
        out["occupied"] = (out["occupied"] > 0).astype(int)
    return out


def poll_seconds_of(df: pd.DataFrame) -> float:
    med = float(pd.Series(time_index(df)).diff().dt.total_seconds().median())
    return med if med and med > 0 else 60.0


def run_battery(frame: pd.DataFrame, poll: float, rule_ids: list[str]) -> dict:
    """{rule: {'status', 'flag_dates': [...]}}"""
    from open_fdd.rules import run_rule
    days = day_key(frame.index); out = {}
    for rid in rule_ids:
        try:
            res = run_rule(rid, frame, poll_seconds=poll)
        except Exception as exc:
            out[rid] = {"status": "not_applicable", "reason": f"error: {exc}"[:160], "flag_dates": []}; continue
        missing = list(getattr(res, "missing_roles", []) or [])
        if not getattr(res, "applicable", True) or missing:
            out[rid] = {"status": "not_applicable", "reason": ", ".join(missing) or "not applicable", "flag_dates": []}; continue
        fault = getattr(res, "confirmed_fault", None)
        if fault is None:
            out[rid] = {"status": "not_applicable", "reason": "no fault series", "flag_dates": []}; continue
        mask = pd.Series(fault).fillna(False).astype(bool).to_numpy()
        hit = sorted(set(pd.Index(days)[: len(mask)][mask]))
        out[rid] = {"status": "fired" if hit else "not_fired", "reason": "", "flag_dates": hit}
    return out


def score_file(df: pd.DataFrame, system: str, healthy: bool) -> dict:
    """per-rule flag dates for the AHU battery and, on the FPUs, the terminal battery per zone."""
    poll = poll_seconds_of(df)
    res = {"ahu": run_battery(to_frame(df, AHU_ROLE_MAP[system], system, healthy), poll, AHU_RULES)}
    if system in ("pfpu", "sfpu"):
        res["tu"] = {z: run_battery(to_frame(df, tu_role_map(z), system, healthy), poll, TU_RULES) for z in ZONES}
    return res


def union_dates(res: dict, exclude: set[str] = frozenset()) -> set[str]:
    s = set()
    for rid, v in res["ahu"].items():
        if rid not in exclude: s |= set(v["flag_dates"])
    for z, rr in res.get("tu", {}).items():
        for rid, v in rr.items():
            if rid not in exclude: s |= set(v["flag_dates"])
    return s


def rule_dates(res: dict) -> dict:
    """rule -> set of dates, terminal rules pooled over zones"""
    d = {}
    for rid, v in res["ahu"].items(): d.setdefault(rid, set()).update(v["flag_dates"])
    for z, rr in res.get("tu", {}).items():
        for rid, v in rr.items(): d.setdefault(rid, set()).update(v["flag_dates"])
    return d


def run_system(system: str) -> dict:
    from strata.core.significance import model_significant
    from strata.core.splits import holdout_mask
    cfg = yaml.safe_load((ROOT / "configs" / CONFIG_DIR[system] / "scenarios.yaml").read_text())
    data = ROOT / "data" / "processed" / system
    healthy = pd.read_parquet(data / f"{cfg['healthy_file']}.parquet")
    hres = score_file(healthy, system, healthy=True)
    all_days = sorted(set(day_key(time_index(healthy))))
    s = pd.Series(all_days); hold = set(s[holdout_mask(s, 8).to_numpy()])
    hrules = rule_dates(hres)
    per_rule_holdout = {rid: sorted(d & hold) for rid, d in hrules.items()}
    noisiest = max(per_rule_holdout, key=lambda r: len(per_rule_holdout[r])) if any(per_rule_holdout.values()) else None
    fp_all = union_dates(hres) & hold; fp_dem = union_dates(hres, {noisiest} if noisiest else set()) & hold
    clean = {"healthy_file": cfg["healthy_file"], "holdout_days": len(hold), "holdout_fp_days_all_rules": len(fp_all), "holdout_fp_days_minus_noisiest": len(fp_dem),
             "noisiest_rule": noisiest, "per_rule_holdout_fp_days": {r: len(v) for r, v in per_rule_holdout.items()},
             "full_year_fp_days_all_rules": len(union_dates(hres)), "full_year_days": len(all_days),
             "rule_status": {r: v["status"] + ("" if v["status"] != "not_applicable" else f" ({v['reason'][:60]})") for r, v in hres["ahu"].items()}}
    if "tu" in hres:
        clean["tu_rule_status_zone_S"] = {r: v["status"] + ("" if v["status"] != "not_applicable" else f" ({v['reason'][:60]})") for r, v in hres["tu"]["S"].items()}
    rows = []
    for sc in cfg["scenarios"]:
        if sc.get("exclude") or sc.get("excluded") or not sc.get("is_fault", True):
            continue
        df = pd.read_parquet(data / f"{sc['file']}.parquet"); res = score_file(df, system, healthy=False)
        n_days = len(set(day_key(time_index(df)))); k_all = len(union_dates(res)); k_dem = len(union_dates(res, {noisiest} if noisiest else set()))
        rd = rule_dates(res); top = sorted(rd, key=lambda r: -len(rd[r]))[:3]
        rows.append({"file": sc["file"], "family": sc.get("family"), "total_days": n_days,
                     "flag_days_all_rules": k_all, "flag_days_minus_noisiest": k_dem,
                     "detected_raw": k_all > 0,
                     "detected_gated_all_rules": model_significant(k_all, n_days, len(fp_all), len(hold)),
                     "detected_gated_minus_noisiest": model_significant(k_dem, n_days, len(fp_dem), len(hold)),
                     "top_rules": {r: len(rd[r]) for r in top}})
        print(f"  {sc['file']:44s} raw {k_all:3d}/{n_days} gated {'Y' if rows[-1]['detected_gated_all_rules'] else '-'} top {rows[-1]['top_rules']}", flush=True)
    bench = json.loads((ROOT / "outputs" / f"benchmark_v6_{system}.json").read_text())
    union = json.loads((ROOT / "outputs" / f"union_fpr_{system}.json").read_text())
    strata_det = {x["file"]: bool(x["meaningful_channels"]) for x in bench["scenarios"] if x["is_fault"] and not x["excluded"]}
    from importlib.metadata import version
    return {"system": system, "openfdd_version": version("open-fdd"), "prereg": "docs/plans/2026-09-27-x38-guideline36-repaired-prereg.md",
            "ahu_rules": AHU_RULES, "tu_rules": TU_RULES if system != "sdahu" else [], "ahu_role_map": AHU_ROLE_MAP[system], "tu_role_map_zone_S": tu_role_map("S") if system != "sdahu" else {},
            "params_overridden": {}, "e3_static_repair": system == "sdahu",
            "clean_year": clean, "scenarios": rows,
            "battery": {"detected_raw": sum(r["detected_raw"] for r in rows), "detected_gated_all_rules": sum(r["detected_gated_all_rules"] for r in rows),
                        "detected_gated_minus_noisiest": sum(r["detected_gated_minus_noisiest"] for r in rows), "scored": len(rows)},
            "strata": {"detected": sum(strata_det.values()), "scored": len(strata_det), "holdout_fp_all8": union["union_all8"]["holdout_fp_days"],
                       "holdout_fp_minus_rate": union["union_minus_rate"]["holdout_fp_days"], "holdout_days": union["holdout_days"],
                       "detected_files": sorted(f for f, d in strata_det.items() if d)},
            "battery_gated_detected_files": sorted(r["file"] for r in rows if r["detected_gated_all_rules"])}


def ledger() -> dict:
    out = {"prereg": "docs/plans/2026-09-27-x38-guideline36-repaired-prereg.md", "systems": {}}
    for s in CONFIG_DIR:
        a = json.loads((ROOT / "outputs" / f"openfdd_baseline_{s}.json").read_text())
        b, st, c = a["battery"], a["strata"], a["clean_year"]
        out["systems"][s] = {"scored": b["scored"], "battery_raw": b["detected_raw"], "battery_gated": b["detected_gated_all_rules"], "battery_gated_demoted": b["detected_gated_minus_noisiest"],
                             "battery_fp_all": c["holdout_fp_days_all_rules"], "battery_fp_demoted": c["holdout_fp_days_minus_noisiest"], "noisiest_rule": c["noisiest_rule"],
                             "strata_detected": st["detected"], "strata_fp_all8": st["holdout_fp_all8"], "strata_fp_minus_rate": st["holdout_fp_minus_rate"], "holdout_days": c["holdout_days"],
                             "battery_only_gated": sorted(set(a["battery_gated_detected_files"]) - set(st["detected_files"])),
                             "strata_only_gated": sorted(set(st["detected_files"]) - set(a["battery_gated_detected_files"]))}
    S = out["systems"]; h = S["sdahu"]
    p1 = h["battery_fp_all"] / h["holdout_days"] > 0.30 and h["battery_gated"] < 13
    p2 = all(S[s]["battery_raw"] >= S[s]["scored"] / 2 and S[s]["battery_fp_all"] / S[s]["holdout_days"] > 0.10 for s in ("pfpu", "sfpu"))
    p3 = all(S[s]["strata_detected"] >= S[s]["battery_gated"] and S[s]["strata_fp_all8"] < S[s]["battery_fp_all"] and S[s]["strata_fp_minus_rate"] < S[s]["battery_fp_demoted"] for s in S)
    p4 = all(len(S[s]["battery_only_gated"]) <= 2 for s in ("pfpu", "sfpu"))
    out["predictions"] = {"P1_sdahu_battery_fp_gt_30pct_and_gated_lt_13": p1, "P2_tu_battery_raw_ge_half_at_fp_gt_10pct": p2, "P3_strata_ge_battery_gated_and_lower_fp_both_framings": p3, "P4_battery_only_le_2": p4}
    out["falsifiers_fired"] = [] if p3 else [f"F-X38.a: current practice matches or beats STRATA under the same gate on {[s for s in S if not (S[s]['strata_detected'] >= S[s]['battery_gated'] and S[s]['strata_fp_all8'] < S[s]['battery_fp_all'] and S[s]['strata_fp_minus_rate'] < S[s]['battery_fp_demoted'])]}"]
    (ROOT / "outputs" / "x38_guideline36.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1)[:3000]); return out


def main() -> int:
    if "--ledger" in sys.argv:
        ledger(); return 0
    system = sys.argv[1]
    result = run_system(system)
    (ROOT / "outputs" / f"openfdd_baseline_{system}.json").write_text(json.dumps(result, indent=2) + "\n")
    b, s, c = result["battery"], result["strata"], result["clean_year"]
    print(f"\n[{system}] battery raw {b['detected_raw']} gated {b['detected_gated_all_rules']} (demoted {b['detected_gated_minus_noisiest']}) of {b['scored']} | battery holdout FP all {c['holdout_fp_days_all_rules']} minus {c['noisiest_rule']} {c['holdout_fp_days_minus_noisiest']} of {c['holdout_days']} | STRATA {s['detected']}/{s['scored']} FP all8 {s['holdout_fp_all8']} minus-rate {s['holdout_fp_minus_rate']}")
    print("  AHU rule status:", c["rule_status"])
    if "tu_rule_status_zone_S" in c: print("  TU rule status (zone S):", c["tu_rule_status_zone_S"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
