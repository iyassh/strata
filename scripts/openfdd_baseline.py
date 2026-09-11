"""D1: the traditional-rules baseline — ASHRAE Guideline 36 via open-fdd.

Grades the standard industry method on STRATA's exam, so "better than
traditional" becomes a measured claim instead of an assertion.

Contract (decided BEFORE any run):
  docs/plans/2026-09-11-openfdd-prereg.md

Usage:
  uv run python scripts/openfdd_baseline.py sdahu
  uv run python scripts/openfdd_baseline.py --list-roles sdahu

Emits outputs/openfdd_baseline_{system}.json. No rule parameter is ever
altered: open-fdd's installed defaults are the as-deployed condition.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# The headline battery: the published Guideline 36 AHU fault conditions.
# open-fdd 4.4.1 ships 26 further AHU rules of its own invention; those are a
# secondary row, not the standard (pre-reg section 0).
FC_RULES = [f"FC{i}" for i in range(1, 16)]

INH2O_PER_PA = 1.0 / 249.0889

CONFIG_DIR = {"sdahu": "lbnl_sdahu", "pfpu": "lbnl_pfpu", "sfpu": "lbnl_sfpu"}

# open-fdd role -> RAW dataset column. Raw, not STRATA-canonical: mapping the
# canonical subset would starve the battery of the fan signal and silently
# disable six conditions (pre-reg section 0).
_SHARED = {
    "outside-air-temp": "OA_TEMP",
    "discharge-air-temp": "SA_TEMP",
    "discharge-air-temp-sp": "SA_TEMPSPT",
    "mixed-air-temp": "MA_TEMP",
    "return-air-temp": "RA_TEMP",
    "cooling-valve": "CHWC_VLV",
    "outside-air-damper": "OA_DMPR",
    "duct-static-pressure": "SA_SP",
    "duct-static-pressure-sp": "SA_SPSPT",
    "vav-total-airflow": "SA_CFM",
    "occupied": "SYS_CTL",
}

ROLE_MAP = {
    # SDAHU: constant-speed fan (SF_SPD has one unique value); SF_CS is the
    # fan CURRENT sensor, not a command. Cooling-only: no heating valve, no
    # coil water temps -> FC5/FC7/FC14/FC15 unrunnable.
    "sdahu": {**_SHARED, "fan-cmd": "SF_SPD", "fan-status": "SF_SPD_DM"},
    # FPUs: the fan roles are INVERTED vs SDAHU — SF_SPD is the real 67-level
    # speed command, SF_CS is binary status. Heating coil present.
    "pfpu": {
        **_SHARED, "fan-cmd": "SF_SPD", "fan-status": "SF_CS",
        "heating-valve": "HWC_VLV",
        "cooling-coil-entering-temp": "CHWC_EWT",
        "cooling-coil-leaving-temp": "CHWC_LWT",
        "heating-coil-entering-temp": "HWC_EWT",
        "heating-coil-leaving-temp": "HWC_LWT",
    },
}
ROLE_MAP["sfpu"] = dict(ROLE_MAP["pfpu"])

# Duct static is logged in PASCALS on SDAHU against an inH2O setpoint
# (402 Pa vs 1.607 inH2O). Unconverted, FC1 fires on every row and invents a
# ~100% false-alarm rate. This is a unit correction, not a tuned threshold.
PASCAL_DUCT_STATIC = {"sdahu"}
# SYS_CTL is {0,1,2} on the FPUs, {0,1} on SDAHU.
OCCUPANCY_THRESHOLDED = {"pfpu", "sfpu"}


def day_key(index: pd.DatetimeIndex) -> pd.Index:
    """Calendar day of each sample, as 'YYYY-MM-DD' (matches case ids)."""
    return pd.to_datetime(index).strftime("%Y-%m-%d")


def to_openfdd_frame(df: pd.DataFrame, system: str) -> pd.DataFrame:
    """Raw dataset frame -> frame carrying open-fdd role columns.

    Row count is preserved; the raw columns are left in place.
    """
    out = df.copy()
    for role, col in ROLE_MAP[system].items():
        if col in out.columns:
            out[role] = pd.to_numeric(out[col], errors="coerce")
    if "duct-static-pressure" in out.columns and system in PASCAL_DUCT_STATIC:
        out["duct-static-pressure"] = out["duct-static-pressure"] * INH2O_PER_PA
    if "occupied" in out.columns and system in OCCUPANCY_THRESHOLDED:
        out["occupied"] = (out["occupied"] > 0).astype(int)
    return out


def poll_seconds_of(df: pd.DataFrame) -> float:
    """Sampling interval, read from the data (a descriptor, not a knob)."""
    deltas = pd.Series(pd.to_datetime(df.index)).diff().dt.total_seconds()
    med = float(deltas.median())
    return med if med and med > 0 else 60.0


def _flagged_days(frame: pd.DataFrame, poll: float) -> tuple[set[str], dict]:
    """Run the battery; return (days flagged by ANY condition, per-rule info)."""
    from open_fdd.rules import run_rule  # lazy: keeps data-free tests import-light

    days = day_key(frame.index)
    flagged: set[str] = set()
    per_rule: dict[str, dict] = {}
    for rid in FC_RULES:
        try:
            res = run_rule(rid, frame, poll_seconds=poll)
        except Exception as exc:  # unrunnable for a structural reason
            per_rule[rid] = {"status": "unrunnable", "missing_roles": [f"error: {exc}"[:160]],
                             "flag_days": 0}
            continue
        missing = list(getattr(res, "missing_roles", []) or [])
        if not getattr(res, "applicable", True) or missing:
            per_rule[rid] = {"status": "unrunnable", "missing_roles": missing or ["not applicable"],
                             "flag_days": 0}
            continue
        fault = getattr(res, "confirmed_fault", None)
        if fault is None:
            per_rule[rid] = {"status": "unrunnable", "missing_roles": ["no fault series returned"],
                             "flag_days": 0}
            continue
        mask = pd.Series(fault).fillna(False).astype(bool).to_numpy()
        hit = sorted(set(pd.Index(days)[: len(mask)][mask]))
        per_rule[rid] = {"status": "fired" if hit else "not_fired",
                         "missing_roles": [], "flag_days": len(hit)}
        flagged |= set(hit)
    return flagged, per_rule


def _holdout_days(days: list[str], n_per_month: int = 8) -> set[str]:
    """Last N days of each month — the same split STRATA calibrates on."""
    from processheal.core.splits import holdout_mask
    s = pd.Series(sorted(set(days)))
    return set(s[holdout_mask(s, n_per_month).to_numpy()])


def _strata_reference(system: str) -> dict:
    """STRATA's numbers on the same exam, read from committed artifacts."""
    bench = json.loads((ROOT / "outputs" / f"benchmark_v6_{system}.json").read_text())
    union = json.loads((ROOT / "outputs" / f"union_fpr_{system}.json").read_text())
    detected = [s for s in bench["scenarios"] if s.get("ttd_days") is not None]
    return {
        "detected_scenarios": len(detected),
        "detected_definition": "scenario has a non-null ttd_days in benchmark_v6",
        "holdout_fp_days": union["union_minus_rate"]["holdout_fp_days"],
        "holdout_fp_rate": union["union_minus_rate"]["rate"],
        "holdout_days": union["holdout_days"],
        "detector": union["detector_definition"],
    }


def run_system(system: str) -> dict:
    cfg = yaml.safe_load((ROOT / "configs" / CONFIG_DIR[system] / "scenarios.yaml").read_text())
    data = ROOT / "data" / "processed" / system
    scenarios = [s for s in cfg["scenarios"] if not (s.get("exclude") or s.get("excluded"))]

    per_condition: dict[str, dict] = {r: {"status": "unrunnable",
                                          "missing_roles": ["not yet evaluated"],
                                          "scenarios_fired": 0} for r in FC_RULES}
    rows = []
    for sc in scenarios:
        df = pd.read_parquet(data / f"{sc['file']}.parquet")
        frame = to_openfdd_frame(df, system)
        poll = poll_seconds_of(df)
        flagged, per_rule = _flagged_days(frame, poll)
        total = len(set(day_key(df.index)))
        rows.append({"file": sc["file"], "family": sc.get("family"),
                     "label": sc.get("label"), "battery_flag_days": int(len(flagged)),
                     "total_days": int(total), "detected": bool(flagged)})
        for rid, info in per_rule.items():
            cur = per_condition[rid]
            if info["status"] == "unrunnable" and cur["status"] == "unrunnable":
                cur["missing_roles"] = info["missing_roles"]
            elif info["status"] == "fired":
                cur["status"] = "fired"
                cur["missing_roles"] = []
                cur["scenarios_fired"] += 1
            elif info["status"] == "not_fired" and cur["status"] != "fired":
                cur["status"] = "not_fired"
                cur["missing_roles"] = []
        print(f"  {sc['file']:44s} flagged {len(flagged):4d}/{total} days", flush=True)

    healthy = pd.read_parquet(data / f"{cfg['healthy_file']}.parquet")
    hframe = to_openfdd_frame(healthy, system)
    hflagged, _ = _flagged_days(hframe, poll_seconds_of(healthy))
    all_days = sorted(set(day_key(healthy.index)))
    hold = _holdout_days(all_days)
    clean = {
        "healthy_file": cfg["healthy_file"],
        "holdout_fp_days": int(len(hflagged & hold)),
        "holdout_days": int(len(hold)),
        "holdout_fp_rate": (len(hflagged & hold) / len(hold)) if hold else None,
        "full_year_fp_days": int(len(hflagged)),
        "full_year_days": int(len(all_days)),
        "full_year_fp_rate": (len(hflagged) / len(all_days)) if all_days else None,
    }

    ref = _strata_reference(system)
    detected = sum(1 for r in rows if r["detected"])
    fired = (detected >= ref["detected_scenarios"]
             and clean["holdout_fp_rate"] is not None
             and clean["holdout_fp_rate"] <= ref["holdout_fp_rate"])
    from importlib.metadata import version
    return {
        "system": system,
        "openfdd_version": version("open-fdd"),
        "rules": FC_RULES,
        "params_overridden": {},
        "role_map": ROLE_MAP[system],
        "prereg": "docs/plans/2026-09-11-openfdd-prereg.md",
        "scoring": "a day is flagged if ANY condition fires on ANY row of it",
        "scenarios": rows,
        "battery_detected_scenarios": int(detected),
        "clean_year": clean,
        "per_condition": per_condition,
        "strata_reference": ref,
        "falsifier_F1": {
            "statement": ("battery detected-scenario count >= STRATA's at a clean-year "
                          "holdout FP rate <= STRATA's => 'better than traditional' dies "
                          "for this system"),
            "verdict": "FIRED" if fired else "NOT_FIRED",
            "battery_detected": int(detected),
            "strata_detected": ref["detected_scenarios"],
            "battery_holdout_fp_rate": clean["holdout_fp_rate"],
            "strata_holdout_fp_rate": ref["holdout_fp_rate"],
        },
    }


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--list-roles" in sys.argv:
        for role, col in ROLE_MAP[args[0]].items():
            print(f"  {role:30s} <- {col}")
        return 0
    if not args or args[0] not in CONFIG_DIR:
        print(f"usage: openfdd_baseline.py {{{'|'.join(CONFIG_DIR)}}}")
        return 2
    system = args[0]
    print(f"[openfdd_baseline] {system}", flush=True)
    result = run_system(system)
    out = ROOT / "outputs" / f"openfdd_baseline_{system}.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    f1 = result["falsifier_F1"]
    print(f"\n  battery detected {f1['battery_detected']} vs STRATA {f1['strata_detected']}"
          f" | clean-year holdout FP {f1['battery_holdout_fp_rate']} vs {f1['strata_holdout_fp_rate']}")
    print(f"  FALSIFIER F1: {f1['verdict']}")
    print(f"  wrote {out.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
