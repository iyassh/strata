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
TU_BATTERY = [r for r in TU_RULES if r not in ("VAV-AHU-LEAVE", "PID-HUNT-1")]   # Amendment 1: A5 (not applicable on a mixing box), A3 (reheat valve only)
NOT_APPLICABLE = {   # Amendment 1: recorded, never a null
    "VAV-AHU-LEAVE": "single-duct rule: a fan-powered box mixes plenum air by design (A5)",
    "FC6@sdahu": "SA_CFM is not in cfm on SDAHU (median 4.96e5, no documented unit) (A6)",
}
ZONES = ["I", "W", "S", "E"]
E3_CONSTANT = 401.85999   # ERRATA E3: healthy SA_SP carries it added; every fault file's SA_SPSPT carries it subtracted
CONFIG_DIR = {"sdahu": "lbnl_sdahu", "pfpu": "lbnl_pfpu", "sfpu": "lbnl_sfpu"}
TIME_COL = "Datetime"

_SHARED = {"outside-air-temp": "OA_TEMP", "discharge-air-temp": "SA_TEMP", "discharge-air-temp-sp": "SA_TEMPSPT", "mixed-air-temp": "MA_TEMP",
           "return-air-temp": "RA_TEMP", "cooling-valve": "CHWC_VLV", "outside-air-damper": "OA_DMPR", "duct-static-pressure": "SA_SP",
           "duct-static-pressure-sp": "SA_SPSPT", "vav-total-airflow": "SA_CFM"}
AHU_ROLE_MAP = {
    # SDAHU: constant-speed fan (SF_SPD one value); no heating coil, no coil air temperatures -> FC5/FC7/FC14/FC15 not applicable
    # Amendment 1 A1: SF_SPD is a dead constant (0.9 on every row); SF_CS is the speed command
    "sdahu": {**_SHARED, "fan-cmd": "SF_CS", "fan-status": "SF_SPD_DM"},
    # FPU air handler: SF_SPD is the speed command, SF_CS binary status; coil AIR-side temperatures (repair 2):
    "pfpu": {**_SHARED, "fan-cmd": "SF_SPD", "fan-status": "SF_CS", "heating-valve": "HWC_VLV",
             "cooling-coil-entering-temp": "HWC_DAT", "cooling-coil-leaving-temp": "CHWC_DAT",
             "heating-coil-entering-temp": "MA_TEMP", "heating-coil-leaving-temp": "HWC_DAT"},
}
AHU_ROLE_MAP["sfpu"] = dict(AHU_ROLE_MAP["pfpu"])


def tu_role_map(z: str) -> dict:
    return {"zone-air-temp": f"RM_TEMP_{z}", "reheat-valve": f"RH_VLV_{z}", "damper": f"VAV_DMPR_{z}", "zone-airflow": f"VAV_PM_CFM_{z}",
            "vav-discharge-air-temp": f"VAV_DAT_{z}", "vav-inlet-air-temp": "SA_TEMP", "ahu-discharge-air-temp": "SA_TEMP",
            "outside-air-temp": "OA_TEMP", "occupied": "SYS_CTL"}   # Amendment 1 A2: no box-fan roles; the library's airflow proxy gates


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
        out["occupied"] = (out["occupied"] == 1).astype(int)   # Amendment 1 A4: SYS_CTL 0=off, 1=occupied, 2=night-cycle
    return out


def poll_seconds_of(df: pd.DataFrame) -> float:
    med = float(pd.Series(time_index(df)).diff().dt.total_seconds().median())
    return med if med and med > 0 else 60.0


def run_battery(frame: pd.DataFrame, poll: float, rule_ids: list[str], params: dict | None = None) -> dict:
    """{rule: {'status', 'flag_dates': [...]}}; params = {rule: {param: value}} (Amendment 1 arm S only)"""
    from open_fdd.rules import run_rule
    days = day_key(frame.index); out = {}
    for rid in rule_ids:
        try:
            res = run_rule(rid, frame, params=(params or {}).get(rid), poll_seconds=poll)
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


def score_file(df: pd.DataFrame, system: str, healthy: bool, site_params: dict | None = None) -> dict:
    """per-rule flag dates for the AHU battery and, on the FPUs, the terminal battery per zone.
    Amendment 1: PID-HUNT-1 on a reheat-valve-only frame (A3); VAV-AHU-LEAVE and FC6@SDAHU recorded not applicable
    (A5, A6); arm S = FC6 re-run with the site datum min_cfm_design (res['ahu_site'])."""
    poll = poll_seconds_of(df)
    ahu_frame = to_frame(df, AHU_ROLE_MAP[system], system, healthy)
    ahu_rules = [r for r in AHU_RULES if not (system == "sdahu" and r == "FC6")]
    res = {"ahu": run_battery(ahu_frame, poll, ahu_rules)}
    if system == "sdahu":
        res["ahu"]["FC6"] = {"status": "not_applicable", "reason": NOT_APPLICABLE["FC6@sdahu"], "flag_dates": []}
    if system in ("pfpu", "sfpu"):
        res["tu"] = {}
        for z in ZONES:
            zf = to_frame(df, tu_role_map(z), system, healthy)
            rr = run_battery(zf, poll, TU_BATTERY)
            rv = zf[[c for c in zf.columns if c in ("reheat-valve", "occupied")]].copy()
            rr.update(run_battery(rv, poll, ["PID-HUNT-1"]))
            # SCHED-247 needs a running witness: the box's primary airflow above 5 % of its own maximum, the same
            # airflow proxy the library's operational gate uses once no fan role is supplied (Amendment 1 A2)
            sf = zf[[c for c in zf.columns if c in ("zone-airflow", "occupied")]].copy()
            sf["fan-status"] = (sf["zone-airflow"] > 0.05 * float(sf["zone-airflow"].max() or 1)).astype(int)
            rr.update(run_battery(sf, poll, ["SCHED-247"]))
            rr["VAV-AHU-LEAVE"] = {"status": "not_applicable", "reason": NOT_APPLICABLE["VAV-AHU-LEAVE"], "flag_dates": []}
            res["tu"][z] = rr
        if site_params:
            res["ahu_site"] = run_battery(ahu_frame, poll, ["FC6"], params=site_params)
    return res


def union_dates(res: dict, exclude: set[str] = frozenset()) -> set[str]:
    s = set()
    for rid, v in res["ahu"].items():
        if rid not in exclude: s |= set(v["flag_dates"])
    for z, rr in res.get("tu", {}).items():
        for rid, v in rr.items():
            if rid not in exclude: s |= set(v["flag_dates"])
    return s


def rule_dates(res: dict, site: bool = False) -> dict:
    """rule -> set of dates, terminal rules pooled over zones; site=True swaps FC6 for the arm-S run"""
    d = {}
    for rid, v in res["ahu"].items(): d.setdefault(rid, set()).update(v["flag_dates"])
    for z, rr in res.get("tu", {}).items():
        for rid, v in rr.items(): d.setdefault(rid, set()).update(v["flag_dates"])
    if site and "ahu_site" in res:
        d["FC6"] = set(res["ahu_site"]["FC6"]["flag_dates"])
    return d


def framings(rd: dict, n_days: int, per_rule_holdout: dict, healthy_full_year: dict, n_hold: int, noisiest: str | None) -> dict:
    """Amendment 1: G1 pooled (as pre-registered, both demotions), G2 per rule against its own holdout FP, G3 rules-channel
    treatment (healthy-year-silent rules only, 3/365 null). Returns verdicts and the rules that carried G2/G3."""
    from strata.core.significance import model_significant, rules_significant
    def pooled(exclude):
        return len(set().union(*[v for r, v in rd.items() if r not in exclude]) if any(r not in exclude for r in rd) else set())
    fp_all = len(set().union(*per_rule_holdout.values())) if per_rule_holdout else 0
    fp_dem = len(set().union(*[v for r, v in per_rule_holdout.items() if r != noisiest])) if any(r != noisiest for r in per_rule_holdout) else 0
    k_all, k_dem = pooled(set()), pooled({noisiest} if noisiest else set())
    g2 = sorted(r for r, v in rd.items() if v and model_significant(len(v), n_days, len(per_rule_holdout.get(r, ())), n_hold))
    silent = {r for r in rd if healthy_full_year.get(r, 0) <= 3}
    g3 = sorted(r for r, v in rd.items() if v and r in silent and rules_significant(len(v), n_days))
    return {"flag_days_all_rules": k_all, "flag_days_minus_noisiest": k_dem,
            "G1_pooled_all_rules": model_significant(k_all, n_days, fp_all, n_hold), "G1_pooled_minus_noisiest": model_significant(k_dem, n_days, fp_dem, n_hold),
            "G2_per_rule": bool(g2), "G2_rules": g2, "G3_rules_channel": bool(g3), "G3_rules": g3}


def run_system(system: str) -> dict:
    from strata.core.significance import model_significant
    from strata.core.splits import holdout_mask
    cfg = yaml.safe_load((ROOT / "configs" / CONFIG_DIR[system] / "scenarios.yaml").read_text())
    data = ROOT / "data" / "processed" / system
    healthy = pd.read_parquet(data / f"{cfg['healthy_file']}.parquet")
    site_params = None
    if system in ("pfpu", "sfpu"):   # Amendment 1 arm S: the unit's design minimum outdoor-air flow, read from the fault-free year
        occ = healthy["SYS_CTL"] == 1
        site_params = {"FC6": {"min_cfm_design": float(healthy.loc[occ, "OA_CFM"].median())}}
    hres = score_file(healthy, system, healthy=True, site_params=site_params)
    all_days = sorted(set(day_key(time_index(healthy))))
    s = pd.Series(all_days); hold = set(s[holdout_mask(s, 8).to_numpy()])
    hrules = rule_dates(hres)
    per_rule_holdout = {rid: set(d & hold) for rid, d in hrules.items()}
    healthy_full_year = {rid: len(d) for rid, d in hrules.items()}
    noisiest = max(per_rule_holdout, key=lambda r: len(per_rule_holdout[r])) if any(per_rule_holdout.values()) else None
    fp_all = union_dates(hres) & hold; fp_dem = union_dates(hres, {noisiest} if noisiest else set()) & hold
    # arm S healthy side
    hrules_s = rule_dates(hres, site=True); per_rule_holdout_s = {rid: set(d & hold) for rid, d in hrules_s.items()}
    healthy_full_year_s = {rid: len(d) for rid, d in hrules_s.items()}
    noisiest_s = max(per_rule_holdout_s, key=lambda r: len(per_rule_holdout_s[r])) if any(per_rule_holdout_s.values()) else None
    fp_all_s = len(set().union(*per_rule_holdout_s.values())) if per_rule_holdout_s else 0
    fp_dem_s = len(set().union(*[v for r, v in per_rule_holdout_s.items() if r != noisiest_s])) if any(r != noisiest_s for r in per_rule_holdout_s) else 0
    clean = {"healthy_file": cfg["healthy_file"], "holdout_days": len(hold), "holdout_fp_days_all_rules": len(fp_all), "holdout_fp_days_minus_noisiest": len(fp_dem),
             "noisiest_rule": noisiest, "per_rule_holdout_fp_days": {r: len(v) for r, v in per_rule_holdout.items()},
             "per_rule_full_year_flag_days": healthy_full_year, "healthy_year_silent_rules": sorted(r for r, n in healthy_full_year.items() if n <= 3 and hres["ahu"].get(r, {}).get("status") != "not_applicable"),
             "site_arm": {"params": site_params, "holdout_fp_days_all_rules": fp_all_s, "holdout_fp_days_minus_noisiest": fp_dem_s, "noisiest_rule": noisiest_s,
                          "per_rule_holdout_fp_days": {r: len(v) for r, v in per_rule_holdout_s.items()}} if site_params else None,
             "full_year_fp_days_all_rules": len(union_dates(hres)), "full_year_days": len(all_days),
             "rule_status": {r: v["status"] + ("" if v["status"] != "not_applicable" else f" ({v['reason'][:60]})") for r, v in hres["ahu"].items()}}
    if "tu" in hres:
        clean["tu_rule_status_zone_S"] = {r: v["status"] + ("" if v["status"] != "not_applicable" else f" ({v['reason'][:60]})") for r, v in hres["tu"]["S"].items()}
    rows = []
    for sc in cfg["scenarios"]:
        if sc.get("exclude") or sc.get("excluded") or not sc.get("is_fault", True):
            continue
        df = pd.read_parquet(data / f"{sc['file']}.parquet"); res = score_file(df, system, healthy=False, site_params=site_params)
        n_days = len(set(day_key(time_index(df))))
        rd = rule_dates(res); top = sorted(rd, key=lambda r: -len(rd[r]))[:3]
        fr = framings(rd, n_days, per_rule_holdout, healthy_full_year, len(hold), noisiest)
        fr_s = framings(rule_dates(res, site=True), n_days, per_rule_holdout_s, healthy_full_year_s, len(hold), noisiest_s) if site_params else None
        rows.append({"file": sc["file"], "family": sc.get("family"), "total_days": n_days,
                     "flag_days_all_rules": fr["flag_days_all_rules"], "flag_days_minus_noisiest": fr["flag_days_minus_noisiest"],
                     "detected_raw": fr["flag_days_all_rules"] > 0,
                     "detected_gated_all_rules": fr["G1_pooled_all_rules"],
                     "detected_gated_minus_noisiest": fr["G1_pooled_minus_noisiest"],
                     "G2_per_rule": fr["G2_per_rule"], "G2_rules": fr["G2_rules"], "G3_rules_channel": fr["G3_rules_channel"], "G3_rules": fr["G3_rules"],
                     "site_arm": fr_s, "top_rules": {r: len(rd[r]) for r in top}})
        r0 = rows[-1]
        print(f"  {sc['file']:44s} raw {r0['flag_days_all_rules']:3d}/{n_days} G1 {'Y' if r0['detected_gated_all_rules'] else '-'}/{'Y' if r0['detected_gated_minus_noisiest'] else '-'} G2 {r0['G2_rules']} G3 {r0['G3_rules']} top {r0['top_rules']}", flush=True)
    bench = json.loads((ROOT / "outputs" / f"benchmark_v6_{system}.json").read_text())
    union = json.loads((ROOT / "outputs" / f"union_fpr_{system}.json").read_text())
    strata_det = {x["file"]: bool(x["meaningful_channels"]) for x in bench["scenarios"] if x["is_fault"] and not x["excluded"]}
    if system == "sdahu":   # Amendment 1 A7: ERRATA E5 adjudicates the outdoor-air-bias detection as branch provenance
        strata_det["oa_bias_4_annual"] = False
    from importlib.metadata import version
    return {"system": system, "openfdd_version": version("open-fdd"), "prereg": "docs/plans/2026-09-27-x38-guideline36-repaired-prereg.md",
            "ahu_rules": AHU_RULES, "tu_rules": TU_RULES if system != "sdahu" else [], "ahu_role_map": AHU_ROLE_MAP[system], "tu_role_map_zone_S": tu_role_map("S") if system != "sdahu" else {},
            "params_overridden": {}, "site_arm_params": site_params, "e3_static_repair": system == "sdahu", "amendment": 1,
            "not_applicable": NOT_APPLICABLE, "strata_sdahu_e5_adjudicated": system == "sdahu",
            "clean_year": clean, "scenarios": rows,
            "battery": {"detected_raw": sum(r["detected_raw"] for r in rows), "detected_gated_all_rules": sum(r["detected_gated_all_rules"] for r in rows),
                        "detected_gated_minus_noisiest": sum(r["detected_gated_minus_noisiest"] for r in rows), "scored": len(rows),
                        "G2_per_rule": sum(r["G2_per_rule"] for r in rows), "G3_rules_channel": sum(r["G3_rules_channel"] for r in rows),
                        "G2_files": sorted(r["file"] for r in rows if r["G2_per_rule"]), "G3_files": sorted(r["file"] for r in rows if r["G3_rules_channel"]),
                        "site_arm": {"G1_all": sum(r["site_arm"]["G1_pooled_all_rules"] for r in rows), "G1_demoted": sum(r["site_arm"]["G1_pooled_minus_noisiest"] for r in rows),
                                     "G2": sum(r["site_arm"]["G2_per_rule"] for r in rows), "G3": sum(r["site_arm"]["G3_rules_channel"] for r in rows),
                                     "G2_files": sorted(r["file"] for r in rows if r["site_arm"]["G2_per_rule"]), "G3_files": sorted(r["file"] for r in rows if r["site_arm"]["G3_rules_channel"])} if site_params else None},
            "strata": {"detected": sum(strata_det.values()), "scored": len(strata_det), "holdout_fp_all8": union["union_all8"]["holdout_fp_days"],
                       "holdout_fp_minus_rate": union["union_minus_rate"]["holdout_fp_days"], "holdout_days": union["holdout_days"],
                       "detected_files": sorted(f for f, d in strata_det.items() if d)},
            "battery_gated_detected_files": sorted(r["file"] for r in rows if r["detected_gated_all_rules"])}


def silent_union_fp(system: str, silent: list[str]) -> dict:
    """G3's false-alarm side: the union of the healthy-year-silent rules' holdout days (the rules G3 keeps),
    recomputed from the healthy file because the artefact stores per-rule counts, not dates."""
    from strata.core.splits import holdout_mask
    cfg = yaml.safe_load((ROOT / "configs" / CONFIG_DIR[system] / "scenarios.yaml").read_text())
    healthy = pd.read_parquet(ROOT / "data" / "processed" / system / f"{cfg['healthy_file']}.parquet")
    all_days = sorted(set(day_key(time_index(healthy)))); s = pd.Series(all_days); hold = set(s[holdout_mask(s, 8).to_numpy()])
    poll = poll_seconds_of(healthy); dates: dict[str, set] = {}
    ahu = [r for r in silent if r in AHU_RULES]
    if ahu:
        for rid, v in run_battery(to_frame(healthy, AHU_ROLE_MAP[system], system, True), poll, ahu).items(): dates.setdefault(rid, set()).update(v["flag_dates"])
    tu = [r for r in silent if r in TU_BATTERY or r == "PID-HUNT-1" or r == "SCHED-247"]
    if tu and system in ("pfpu", "sfpu"):
        res = score_file(healthy, system, True)
        for z, rr in res["tu"].items():
            for rid, v in rr.items():
                if rid in tu: dates.setdefault(rid, set()).update(v["flag_dates"])
    union = set().union(*dates.values()) if dates else set()
    return {"rules": silent, "holdout_fp_days": len(union & hold), "per_rule": {r: len(d & hold) for r, d in dates.items()}}


def ledger() -> dict:
    out = {"prereg": "docs/plans/2026-09-27-x38-guideline36-repaired-prereg.md", "amendment": 1, "run": 2,
           "run1": "outputs/openfdd_baseline_<system>_run1.json, outputs/x38_guideline36_run1.json (adapter defects; not quoted)", "systems": {}}
    for s in CONFIG_DIR:
        a = json.loads((ROOT / "outputs" / f"openfdd_baseline_{s}.json").read_text())
        b, st, c = a["battery"], a["strata"], a["clean_year"]
        sa = c.get("site_arm") or {}
        out["systems"][s] = {"scored": b["scored"], "battery_raw": b["detected_raw"], "battery_gated": b["detected_gated_all_rules"], "battery_gated_demoted": b["detected_gated_minus_noisiest"],
                             "battery_G2": b["G2_per_rule"], "battery_G3": b["G3_rules_channel"], "battery_G2_files": b["G2_files"], "battery_G3_files": b["G3_files"],
                             "battery_fp_all": c["holdout_fp_days_all_rules"], "battery_fp_demoted": c["holdout_fp_days_minus_noisiest"], "noisiest_rule": c["noisiest_rule"],
                             "per_rule_holdout_fp_days": c["per_rule_holdout_fp_days"], "healthy_year_silent_rules": c.get("healthy_year_silent_rules", []),
                             "site_arm": {"params": sa.get("params"), "fp_all": sa.get("holdout_fp_days_all_rules"), "fp_demoted": sa.get("holdout_fp_days_minus_noisiest"), "noisiest_rule": sa.get("noisiest_rule"),
                                          "FC6_holdout_fp": (sa.get("per_rule_holdout_fp_days") or {}).get("FC6"), **(b["site_arm"] or {})} if sa else None,
                             "strata_detected": st["detected"], "strata_fp_all8": st["holdout_fp_all8"], "strata_fp_minus_rate": st["holdout_fp_minus_rate"], "holdout_days": c["holdout_days"],
                             "battery_only_gated": sorted(set(a["battery_gated_detected_files"]) - set(st["detected_files"])),
                             "battery_only_G2": sorted(set(b["G2_files"]) - set(st["detected_files"])), "battery_only_G3": sorted(set(b["G3_files"]) - set(st["detected_files"])),
                             "strata_only_gated": sorted(set(st["detected_files"]) - set(a["battery_gated_detected_files"]))}
        # re-audit item 6: the artefact's silent list filtered not-applicable status for AHU rules only; drop the
        # terminal rules recorded not applicable (VAV-AHU-LEAVE) before they are called "silent"
        na_tu = {r for r, v in (c.get("tu_rule_status_zone_S") or {}).items() if str(v).startswith("not_applicable")}
        silent = [r for r in c.get("healthy_year_silent_rules", []) if r not in na_tu]
        out["systems"][s]["healthy_year_silent_rules"] = silent
        out["systems"][s]["G3_false_alarms"] = silent_union_fp(s, silent)
        print(f"[{s}] G3 false alarms (silent rules' holdout days): {out['systems'][s]['G3_false_alarms']}", flush=True)
    S = out["systems"]; h = S["sdahu"]
    p1 = h["battery_fp_all"] / h["holdout_days"] > 0.30 and h["battery_gated"] < 13
    p2 = all(S[s]["battery_raw"] >= S[s]["scored"] / 2 and S[s]["battery_fp_all"] / S[s]["holdout_days"] > 0.10 for s in ("pfpu", "sfpu"))
    def p3_ok(s, det_key, fp_all_key="battery_fp_all", fp_dem_key="battery_fp_demoted"):
        return S[s]["strata_detected"] >= S[s][det_key] and S[s]["strata_fp_all8"] < S[s][fp_all_key] and S[s]["strata_fp_minus_rate"] < S[s][fp_dem_key]
    p3 = {"G1": all(p3_ok(s, "battery_gated") for s in S), "G2": all(S[s]["strata_detected"] >= S[s]["battery_G2"] for s in S),
          # P3 as worded: at least as many detections AND a lower false-alarm rate; equal false alarms = "matches" = F-X38.a
          "G3": all(S[s]["strata_detected"] >= S[s]["battery_G3"] and S[s]["strata_fp_minus_rate"] < S[s]["G3_false_alarms"]["holdout_fp_days"] for s in S),
          "S": all(S[s]["site_arm"] is None or (S[s]["strata_detected"] >= max(S[s]["site_arm"]["G1_all"], S[s]["site_arm"]["G2"], S[s]["site_arm"]["G3"]) and S[s]["strata_fp_all8"] < S[s]["site_arm"]["fp_all"]) for s in S)}
    p4 = all(len(S[s]["battery_only_gated"]) <= 2 for s in ("pfpu", "sfpu"))
    p5 = h["battery_G2"] >= 1 and p3["G2"]
    p6 = all(len(S[s]["healthy_year_silent_rules"]) <= 3 and not S[s]["battery_only_G3"] for s in S)
    p7 = all((S[s]["site_arm"]["FC6_holdout_fp"] or 0) < 10 and S[s]["site_arm"]["fp_all"] / S[s]["holdout_days"] > 0.30 for s in ("pfpu", "sfpu"))
    out["predictions"] = {"P1_sdahu_battery_fp_gt_30pct_and_gated_lt_13": p1, "P2_tu_battery_raw_ge_half_at_fp_gt_10pct": p2,
                          "P3_strata_ge_battery_and_lower_fp": p3, "P4_battery_only_le_2": p4,
                          "P5_G2_sdahu_ge_1_and_strata_ge": p5, "P6_G3_le_3_silent_rules_and_subset": p6, "P7_site_arm_FC6_lt_10_union_gt_30pct": p7}
    def p3_sys(k):
        if k == "G1": return [s for s in S if not p3_ok(s, "battery_gated")]
        if k == "G2": return [s for s in S if not S[s]["strata_detected"] >= S[s]["battery_G2"]]
        if k == "G3": return [s for s in S if not (S[s]["strata_detected"] >= S[s]["battery_G3"] and S[s]["strata_fp_minus_rate"] < S[s]["G3_false_alarms"]["holdout_fp_days"])]
        return [s for s in S if S[s]["site_arm"] and not (S[s]["strata_detected"] >= max(S[s]["site_arm"]["G1_all"], S[s]["site_arm"]["G2"], S[s]["site_arm"]["G3"]) and S[s]["strata_fp_all8"] < S[s]["site_arm"]["fp_all"])]
    fired = [f"F-X38.a ({k}): current practice matches or beats STRATA under framing {k} on {p3_sys(k)}" for k, v in p3.items() if not v]
    out["falsifiers_fired"] = fired
    out["predictions_failed_without_falsifier"] = [k for k, v in {"P1": p1, "P2": p2, "P4": p4, "P6": p6, "P7": p7}.items() if not v] + (["P5 (its failure is the G2 falsifier)"] if not p5 else [])
    # re-audit item 11 (post hoc, not pre-registered): G2 with the rules that pass the gate on the healthy file's own
    # training days excluded — those rules flag the identical day sets on healthy and fault files (FC9/FC14 on PFPU, FC13 on SFPU)
    out["G2_prime_post_hoc"] = {"note": "G2 excluding self-detecting rules (audit A re-audit item 11); computed from the artefacts' G2_rules",
                                "self_detecting": {"sdahu": [], "pfpu": ["FC9", "FC14"], "sfpu": ["FC13"]}}
    for s in S:
        a = json.loads((ROOT / "outputs" / f"openfdd_baseline_{s}.json").read_text()); sd = set(out["G2_prime_post_hoc"]["self_detecting"][s])
        files = sorted(r["file"] for r in a["scenarios"] if set(r["G2_rules"]) - sd)
        out["G2_prime_post_hoc"][s] = {"detected": len(files), "battery_only": sorted(set(files) - set(a["strata"]["detected_files"]))}
    (ROOT / "outputs" / "x38_guideline36.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "systems"}, indent=1))
    for s, v in S.items():
        print(f"[{s}] battery G1 {v['battery_gated']}/{v['battery_gated_demoted']} G2 {v['battery_G2']} G3 {v['battery_G3']} of {v['scored']} | FP all {v['battery_fp_all']} dem {v['battery_fp_demoted']} ({v['noisiest_rule']}) | site {v['site_arm'] and (v['site_arm']['G1_all'], v['site_arm']['G2'], v['site_arm']['G3'], v['site_arm']['fp_all'])} | STRATA {v['strata_detected']} FP {v['strata_fp_all8']}/{v['strata_fp_minus_rate']}")
    return out


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
