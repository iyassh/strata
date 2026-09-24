"""X17 — the DDAHU onboarding ledger: predictions and falsifiers evaluated from
the committed artefacts (gate battery, scorecard, union FPR), plus the
onboarding effort. Pre-registered: docs/plans/2026-09-24-x17-ddahu-onboarding-prereg.md.

    uv run python scripts/x17_onboarding.py -> outputs/x17_onboarding.json
"""
import json
import subprocess
from pathlib import Path

import yaml


def _at(path: str, commit: str) -> dict:
    """The artefact as committed when this experiment closed. X24 (2026-09-24)
    later changed the live scorecards; this ledger records its own experiment."""
    import subprocess
    return json.loads(subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, text=True, check=True).stdout)

gates = json.loads(Path("outputs/week0_audit_ddahu.json").read_text())
card = _at("outputs/benchmark_v6_ddahu.json", "327ee7e")   # X17 closing scorecard
ufpr = _at("outputs/union_fpr_ddahu.json", "4f19f49")
CLOSE_COMMIT = "4f19f49"   # the experiment's closing commit: every diff and config count is taken there, not at HEAD
rules = yaml.safe_load(subprocess.run(["git", "show", f"{CLOSE_COMMIT}:configs/lbnl_ddahu/rules.yaml"], capture_output=True, text=True, check=True).stdout)
sensors = yaml.safe_load(subprocess.run(["git", "show", f"{CLOSE_COMMIT}:configs/lbnl_ddahu/sensors.yaml"], capture_output=True, text=True, check=True).stdout)["canonical_to_csv"]
man = yaml.safe_load(Path("configs/lbnl_ddahu/scenarios.yaml").read_text())

ev = rules["events"]
n_state = sum(1 for r in ev.values() if r.get("alphabet", "state") == "state" and r["kind"] in ("occupancy", "mode", "window"))
n_sig = len(ev) - n_state
src_changed = subprocess.run(["git", "diff", "--stat", "b8fadc8", CLOSE_COMMIT, "--", "src/"], capture_output=True, text=True).stdout.strip()

sc = [s for s in card["scenarios"] if s["is_fault"] and not s["excluded"]]
det = [s for s in sc if s["meaningful_channels"]]
fam = {s["file"]: next(m["family"] for m in man["scenarios"] if m["file"] == s["file"]) for s in sc}
fouling = [s for s in sc if fam[s["file"]] == "coil_fouling"]
static = [s for s in sc if fam[s["file"]] == "static_sensor_bias"]
unstable = [s for s in sc if fam[s["file"]] == "unstable_control"]
conf_only = [s["file"] for s in sc if s["meaningful_channels"] and
             set(str(s["meaningful_channels"]).split("+")) <= {"model", "device"}]
by_family = {}
for s in sc:
    f = fam[s["file"]]; by_family.setdefault(f, [0, 0]); by_family[f][1] += 1; by_family[f][0] += int(bool(s["meaningful_channels"]))

fp = ufpr["union_minus_rate"]["holdout_fp_days"]; hold = ufpr["holdout_days"]
pred = {
    "P1_config_only": src_changed == "",
    "P2_gates": (not gates["G1_md5"]["duplicate_groups"] and not gates["G4_raw_rotation"]
                 and all(v["wrap_points"] == 0 for v in gates["G2_monotonic"].values())
                 and all(v["set_identical_to_healthy"] for v in gates["G3_calendar"].values())
                 and gates["G5_ttl"]["columns_not_declared"] == []
                 and all(gates.get("G6_branch", {}).get("healthy_inside_fault_range", {}).values())
                 and gates.get("G6_branch", {}).get("setpoint_constants_identical_to_healthy", False)),
    "P3_healthy_silence_iterations": 1, "P3_residual_healthy_signature_days": 1,
    "P4_holdout_fp_days": fp, "P4_fp_le_10_of_96": fp <= 10,
    "P5_detected": len(det), "P5_n_scored": len(sc), "P5_frac": round(len(det) / len(sc), 3), "P5_ge_60pct": len(det) / len(sc) >= 0.6,
    "P6_fouling_detected": sum(1 for s in fouling if s["meaningful_channels"]), "P6_le_4_of_12": sum(1 for s in fouling if s["meaningful_channels"]) <= 4,
    "P7_conformance_only_scenarios": conf_only, "P7_null_generalises": conf_only == [],
    "P8_static_bias_detected": sum(1 for s in static if s["meaningful_channels"]),
    "P8_unstable_detected": sum(1 for s in unstable if s["meaningful_channels"]),
    "P8_holds": sum(1 for s in static if s["meaningful_channels"]) >= 4 and sum(1 for s in unstable if s["meaningful_channels"]) == 2,
}
fired = []
if not pred["P1_config_only"]:
    fired.append("F-X17.a: a src/ change was required")
if not pred["P4_fp_le_10_of_96"]:
    fired.append("F-X17.b: holdout false alarms exceed 10 of 96")
if len(det) / len(sc) < 0.4:
    fired.append("F-X17.c: fewer than 40% of scenarios detected")
if conf_only:
    fired.append("F-X17.d: a scenario is detected only by the conformance channels")
out = {"pre_registration": "docs/plans/2026-09-24-x17-ddahu-onboarding-prereg.md",
       "effort": {"sensor_mappings": len(sensors), "state_rules": n_state, "signature_rules": n_sig,
                  "healthy_silence_iterations": 1, "src_diff_since_prereg": src_changed or "none"},
       "gates": {"files": gates["n_files"], "duplicates": gates["G1_md5"]["duplicate_groups"], "rotation": list(gates["G4_raw_rotation"]),
                 "ttl_columns_not_declared": gates["G5_ttl"]["columns_not_declared"]},
       "scorecard": {"detected": len(det), "scored": len(sc), "by_family": by_family,
                     "channels": {ch: sum(1 for s in sc if ch in str(s["meaningful_channels"]).split("+"))
                                  for ch in ("rules", "resid", "model", "device", "absence", "freq", "osc", "rate")},
                     "holdout_fp_days_union_minus_rate": fp, "holdout_days": hold,
                     "per_channel_fp": {k: v["holdout_fp_days"] for k, v in ufpr["channels"].items()}},
       "predictions": pred, "falsifiers_fired": fired}
Path("outputs/x17_onboarding.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out["scorecard"], indent=1)); print(json.dumps(pred, indent=1)); print("falsifiers fired:", fired or "none")
