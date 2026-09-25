"""X34 — component attribution: does the rule carrying each detection point at the seeded component?
Pre-registration: docs/plans/2026-09-25-x34-component-attribution-prereg.md

    uv run python scripts/component_attribution.py -> outputs/component_attribution.json
"""
from __future__ import annotations

import json
import os
import re
import sys
import warnings
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from strata.hvac.events import abstract_events  # noqa: E402
from strata.io.config import load_config  # noqa: E402

SYSTEMS = ["sdahu", "pfpu", "sfpu", "ddahu", "fcu"]
ZONES = {"pfpu": "IWSE", "sfpu": "IWSE", "ddahu": ["W", "SB", "SA", "E"]}


def rule_component(system: str, rule: str):
    """(subsystem, component) a rule points at, from its inputs. None = no component (unit-level)."""
    r = rule
    if system == "sdahu":
        if r in ("damper_command_mismatch", "oa_fraction_residual", "mixed_air_envelope"): return ("outdoor-air section", "oa_damper")
        if r == "ra_damper_command_mismatch": return ("outdoor-air section", "ra_damper")
        if r in ("valve_command_mismatch", "valve_leak"): return ("cooling coil", "valve")
        if r in ("supply_air_residual", "setpoint_deviation"): return ("cooling coil", "coil/sat_sensor")
        if r in ("sf_specific_power", "sf_flow_per_speed"): return ("supply fan", "fan")
        if r in ("rf_specific_power", "rf_speed_mismatch"): return ("return fan", "fan")
    if system in ("pfpu", "sfpu"):
        m = re.match(r"(.*)_([IWSE])$", r)
        if m:
            base, z = m.groups(); sub = f"zone {z}"
            if base in ("rh_valve_mismatch", "rh_water_leak"): return (sub, "reheat_valve")
            if base == "rh_waterside_dT": return (sub, "reheat_coil")
            if base == "zone_flow_tracking": return (sub, "zone_damper")
            if base == "ra_minus_zone": return (sub, "zone_temp_sensor")
            if base == "dat_minus_sa": return (sub, "reheat_valve")
            if base == "da_minus_pm": return (sub, "zone_airflow_path")
            if base in ("zone_fan_spf", "zone_fan_dp_per_cfm2"): return (sub, "zone_fan")
        if r in ("oa_damper_mismatch", "mixed_air_envelope"): return ("ahu outdoor-air section", "oa_damper")
        if r == "ra_damper_mismatch": return ("ahu outdoor-air section", "ra_damper")
        if r == "ea_damper_mismatch": return ("ahu outdoor-air section", "ea_damper")
        if r in ("chwc_valve_mismatch", "chwc_valve_leak"): return ("ahu cooling coil", "valve")
        if r in ("hwc_valve_mismatch", "hwc_valve_leak"): return ("ahu heating coil", "valve")
        if r in ("chwc_waterside_dT",): return ("ahu cooling coil", "coil")
        if r in ("hwc_waterside_dT",): return ("ahu heating coil", "coil")
        if r in ("supply_air_residual", "sat_setpoint_deviation"): return ("ahu cooling coil", "coil/sat_sensor")
        if r in ("sf_specific_power", "sf_flow_per_speed", "static_per_speed2", "static_setpoint_deviation"): return ("ahu supply fan", "fan")
        if r == "rf_specific_power": return ("ahu return fan", "fan")
    if system == "ddahu":
        m = re.match(r"(box_static|box_eat|zone_flow_tracking)_([CH])_(W|SB|SA|E)$", r)
        if m:
            kind, deck, z = m.groups(); d = "cold deck" if deck == "C" else "hot deck"
            if kind == "box_static": return (d, "static_sensor")
            if kind == "box_eat": return (d, "sat_sensor")
            return (f"zone {z}", "zone_damper")
        cold = r.startswith(("cold_", "chwc_", "csf_", "chwp_")); hot = r.startswith(("hot_", "hwc_", "hsf_", "hwp_"))
        d = "cold deck" if cold else "hot deck" if hot else None
        if r in ("cold_static_setpoint_deviation", "hot_static_setpoint_deviation", "cold_static_per_speed", "hot_static_per_speed", "cold_static_per_speed2", "hot_static_per_speed2"): return (d, "static_sensor/fan")
        if r in ("cold_sat_setpoint_deviation", "hot_sat_setpoint_deviation", "supply_air_residual", "hot_deck_residual"): return (d or "cold deck", "sat_sensor/coil")
        if r in ("chwc_valve_mismatch", "chwc_valve_leak", "hwc_valve_mismatch", "hwc_valve_leak"): return (d, "valve")
        if r in ("chwc_waterside_dT", "hwc_waterside_dT", "chwc_ua", "hwc_ua", "chwp_bypass_flow", "hwp_bypass_flow"): return (d, "coil")
        if r in ("csf_specific_power", "csf_flow_per_speed", "csf_dp_per_speed2", "hsf_specific_power", "hsf_flow_per_speed", "hsf_dp_per_speed2"): return (d, "fan")
        if r == "rf_specific_power": return ("return fan", "fan")
        if r in ("oa_damper_mismatch", "oa_fraction_residual", "mixed_air_envelope"): return ("outdoor-air section", "oa_damper")
        if r == "ra_damper_mismatch": return ("outdoor-air section", "ra_damper")
        if r == "ea_damper_mismatch": return ("outdoor-air section", "ea_damper")
    if system == "fcu":
        if r in ("oa_damper_mismatch", "oa_fraction_residual", "oa_flow_ratio_min_pos", "mixed_air_envelope"): return ("outdoor-air section", "oa_damper")
        if r in ("chwc_valve_mismatch", "chwc_valve_leak", "chwc_flow_when_closed"): return ("cooling coil", "valve")
        if r in ("hwc_valve_mismatch", "hwc_valve_leak", "hwc_flow_when_closed"): return ("heating coil", "valve")
        if r in ("chwc_waterside_dT", "cooling_only_residual"): return ("cooling coil", "coil")
        if r in ("hwc_waterside_dT", "heating_only_residual"): return ("heating coil", "coil")
        if r == "supply_air_residual": return ("coils", "coil")
        if r in ("zone_cooling_tracking", "zone_heating_tracking"): return ("zone control", "control/zone_temp_sensor")
        if r in ("flow_per_speed", "fan_specific_power"): return ("airflow path", "fan/filter")
    return None


def seeded_component(system: str, f: str):
    if system == "sdahu":
        if f.startswith("damper_stuck"): return ("outdoor-air section", "oa_damper")
        if f.startswith("oa_bias"): return ("outdoor-air section", "oa_temp_sensor")
        if f.startswith("coi_bias"): return ("cooling coil", "coil/sat_sensor")
        if f.startswith(("coi_stuck", "coi_leakage")): return ("cooling coil", "valve")
    if system in ("pfpu", "sfpu"):
        s = "zone S"
        if "ReheatVLV" in f: return (s, "reheat_valve")
        if "ReheatCoilFouling" in f: return (s, "reheat_coil")
        if "SensorBias_RMTEMP" in f: return (s, "zone_temp_sensor")
        if "SensorBias_VAVAirflow" in f: return (s, "zone_flow_sensor")
        if "VAVDMPR" in f: return (s, "zone_damper")
        if "RMTEMPUnstable" in f: return (s, "control")
        if "VAVFanRestrictFlow" in f: return (s, "zone_fan")
    if system == "ddahu":
        if "DMPRStuck_OA" in f: return ("outdoor-air section", "oa_damper")
        if "DMPRStuck_Cold" in f or "DMPRStuck_Hot" in f: return ("zone (unspecified)", "zone_damper")
        d = "cold deck" if ("Cooling" in f or "_CSA" in f or "_CSP" in f or "CoolSeq" in f) else "hot deck"
        if "VLVStuck" in f: return (d, "valve")
        if "Fouling" in f: return (d, "coil")
        if "SensorBias_CSA" in f or "SensorBias_HSA" in f: return (d, "sat_sensor")
        if "SensorBias_CSP" in f or "SensorBias_HSP" in f: return (d, "static_sensor")
        if "Unstable" in f: return (d, "control")
    if system == "fcu":
        if "OADMPR" in f or "OABlockage" in f: return ("outdoor-air section", "oa_damper")
        if "FilterRestriction" in f or "FanOutletBlockage" in f: return ("airflow path", "fan/filter")
        d = "cooling coil" if "Cooling" in f else "heating coil"
        if "VLVLeak" in f or "VLVStuck" in f: return (d, "valve")
        if "Fouling" in f: return (d, "coil")
        if "SensorBias_RMTemp" in f: return ("zone control", "control/zone_temp_sensor")
        if "Control_" in f: return ("zone control", "control/zone_temp_sensor")
    return None


def score(system, rules_top, seeded):
    comps = [rule_component(system, r) for r in rules_top]
    comps = [c for c in comps if c]
    if not comps or seeded is None:
        return "unnamed"
    def same_sub(a, b):
        return a[0] == b[0] or (b[0] == "zone (unspecified)" and a[0].startswith("zone ")) or (a[0] in ("coils",) and b[0].endswith("coil"))
    def same_comp(a, b):
        return same_sub(a, b) and (a[1] == b[1] or (b[1] in a[1].split("/")) or (a[1] in b[1].split("/")))
    if any(same_comp(c, seeded) for c in comps): return "exact"
    if any(same_sub(c, seeded) for c in comps): return "subsystem"
    return "wrong"


def main() -> int:
    out = {"prereg": "docs/plans/2026-09-25-x34-component-attribution-prereg.md", "systems": {}, "rows": []}
    for s in SYSTEMS:
        cfg = load_config(str(REPO / f"configs/lbnl_{s}"))
        card = json.loads((REPO / f"outputs/benchmark_v6_{s}.json").read_text())["scenarios"]
        cred = json.loads((REPO / f"outputs/x33_residual_credits_{s}.json").read_text())["scenarios"]
        det = [x for x in card if x["is_fault"] and not x["excluded"] and x["meaningful_channels"]]
        for x in det:
            f = x["file"]; chans = set(str(x["meaningful_channels"]).split("+"))
            days = {}
            if "resid" in chans and f in cred:
                days.update({r: d for r, d in cred[f]["per_rule_flagged_days"].items() if d})
            if "rules" in chans:
                log = abstract_events(pd.read_parquet(REPO / f"data/processed/{s}/{f}.parquet"), cfg)
                sig = log[log["alphabet"] == "signature"]
                for r, n in sig.groupby("activity")["case_id"].nunique().items():
                    days[r] = max(days.get(r, 0), int(n))
            if not days:
                verdict, top = "unnamed", []
            else:
                mx = max(days.values()); top = sorted(r for r, d in days.items() if d == mx)
                verdict = score(s, top, seeded_component(s, f))
            out["rows"].append({"system": s, "file": f, "channels": x["meaningful_channels"], "carrying_rules": top, "carrying_days": days.get(top[0]) if top else 0,
                                "rule_component": [rule_component(s, r) for r in top], "seeded_component": seeded_component(s, f), "verdict": verdict})
            print(f"{s:6s} {f:44s} {verdict:9s} {top[:2]} -> {seeded_component(s, f)}", flush=True)
        rows = [r for r in out["rows"] if r["system"] == s]
        out["systems"][s] = {"detected": len(rows), **{v: sum(1 for r in rows if r["verdict"] == v) for v in ("exact", "subsystem", "wrong", "unnamed")}}
    n = len(out["rows"]); c = {v: sum(1 for r in out["rows"] if r["verdict"] == v) for v in ("exact", "subsystem", "wrong", "unnamed")}
    out["totals"] = {"detected": n, **c, "exact_rate": round(c["exact"] / n, 3), "exact_or_subsystem_rate": round((c["exact"] + c["subsystem"]) / n, 3), "wrong_rate": round(c["wrong"] / n, 3)}
    bias = [r for r in out["rows"] if "SensorBias" in r["file"] or "_bias" in r["file"]]
    bias_resid = [r for r in bias if any(k in " ".join(r["carrying_rules"]) for k in ("box_", "ra_minus_zone"))]
    out["predictions"] = {"P1_exact_ge_60pct": out["totals"]["exact_rate"] >= 0.60, "P2_exact_or_subsystem_ge_85pct": out["totals"]["exact_or_subsystem_rate"] >= 0.85,
                          "P3_wrong_le_10pct": out["totals"]["wrong_rate"] <= 0.10,
                          "P4_bias_via_redundancy_all_exact": all(r["verdict"] == "exact" for r in bias_resid), "P4_n": len(bias_resid)}
    out["falsifiers_fired"] = [] if out["predictions"]["P3_wrong_le_10pct"] else ["F-X34.a: wrong-subsystem rate above 10 %"]
    (REPO / "outputs/component_attribution.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"systems": out["systems"], "totals": out["totals"], "predictions": out["predictions"], "falsifiers": out["falsifiers_fired"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
