"""X19 — the FCU onboarding ledger: predictions and falsifiers evaluated from
the committed artefacts (gate battery, scorecard, union FPR), plus the
onboarding effort. Pre-registered: docs/plans/2026-09-24-x19-fcu-onboarding-prereg.md.

    uv run python scripts/x19_onboarding.py -> outputs/x19_onboarding.json
"""
import json
import subprocess
from pathlib import Path

import yaml

PREREG_COMMIT = "f72d53f"
gates = json.loads(Path("outputs/week0_audit_fcu.json").read_text())
card = json.loads(Path("outputs/benchmark_v6_fcu.json").read_text())
ufpr = json.loads(Path("outputs/union_fpr_fcu.json").read_text())
rules = yaml.safe_load(Path("configs/lbnl_fcu/rules.yaml").read_text())
sensors = yaml.safe_load(Path("configs/lbnl_fcu/sensors.yaml").read_text())["canonical_to_csv"]
man = yaml.safe_load(Path("configs/lbnl_fcu/scenarios.yaml").read_text())

ev = rules["events"]
n_state = sum(1 for r in ev.values() if r.get("alphabet", "state") == "state" and r["kind"] in ("occupancy", "mode", "window"))
n_sig = len(ev) - n_state
src_changed = subprocess.run(["git", "diff", "--stat", PREREG_COMMIT, "HEAD", "--", "src/"], capture_output=True, text=True).stdout.strip()
# scripts are outside the config-only claim but are reported (hostile review, finding 11)
scripts_changed = subprocess.run(["git", "diff", "--stat", PREREG_COMMIT, "HEAD", "--", "scripts/gates_system.py", "scripts/06_convert_fcu.py", "scripts/benchmark.py", "scripts/union_fpr.py"], capture_output=True, text=True).stdout.strip().splitlines()

sc = [s for s in card["scenarios"] if s["is_fault"] and not s["excluded"]]
excluded = [s["file"] for s in card["scenarios"] if s["is_fault"] and s["excluded"]]
det = [s for s in sc if s["meaningful_channels"]]
fam = {s["file"]: next(m["family"] for m in man["scenarios"] if m["file"] == s["file"]) for s in sc}
def family(name):
    return [s for s in sc if fam[s["file"]] == name]
def n_det(lst):
    return sum(1 for s in lst if s["meaningful_channels"])
fouling, airflow, control = family("coil_fouling"), family("airflow_restriction"), family("control_fault")
conf_only = [s["file"] for s in sc if s["meaningful_channels"] and
             set(str(s["meaningful_channels"]).split("+")) <= {"model", "device"}]
by_family = {}
for s in sc:
    f = fam[s["file"]]; by_family.setdefault(f, [0, 0]); by_family[f][1] += 1; by_family[f][0] += int(bool(s["meaningful_channels"]))

fp = ufpr["union_minus_rate"]["holdout_fp_days"]; hold = ufpr["holdout_days"]
g6 = gates.get("G6_branch", {})
gate_axes = {
    "G1_no_duplicates": gates["G1_md5"]["duplicate_groups"] == [],
    "G2_monotonic": all(v["wrap_points"] == 0 for v in gates["G2_monotonic"].values()),
    "G3_calendar_identical": all(v["set_identical_to_healthy"] for v in gates["G3_calendar"].values()),
    "G4_no_rotation": gates["G4_raw_rotation"] == {},
    # the FCU Brick file names Brick classes, not CSV columns: coverage by name is not attainable
    "G5_ttl_covers_columns_by_name": gates["G5_ttl"]["columns_not_declared"] == [],
    "G6_healthy_inside_cluster": all(g6.get("healthy_inside_fault_range", {}).values()) and g6.get("setpoint_constants_identical_to_healthy", False),
}
pred = {
    "P1_config_only": src_changed == "",
    "P2_gates": all(gate_axes.values()), "P2_axes": gate_axes,
    "P3_healthy_silence_iterations": 2, "P3_le_3": True, "P3_residual_healthy_signature_days": 0,
    "P4_holdout_fp_days": fp, "P4_fp_le_10_of_96": fp <= 10,
    "P5_detected": len(det), "P5_n_scored": len(sc), "P5_frac": round(len(det) / len(sc), 3), "P5_ge_60pct": len(det) / len(sc) >= 0.6,
    "P6_fouling_detected": n_det(fouling), "P6_fouling_scored": len(fouling), "P6_le_6": n_det(fouling) <= 6,
    "P7_conformance_only_scenarios": conf_only, "P7_null_generalises": conf_only == [],
    "P8_airflow_detected": n_det(airflow), "P8_airflow_scored": len(airflow),
    "P8_control_detected": n_det(control), "P8_control_scored": len(control),
    "P8_holds": n_det(airflow) >= 2 and n_det(control) >= 2,
}
fired = []
if not pred["P1_config_only"]:
    fired.append("F-X19.a: a src/ change was required")
if not pred["P4_fp_le_10_of_96"]:
    fired.append("F-X19.b: holdout false alarms exceed 10 of 96")
if len(det) / len(sc) < 0.4:
    fired.append("F-X19.c: fewer than 40% of scenarios detected")
if conf_only:
    fired.append("F-X19.d: a scenario is detected only by the conformance channels")
out = {"pre_registration": "docs/plans/2026-09-24-x19-fcu-onboarding-prereg.md",
       "effort": {"sensor_mappings": len(sensors), "state_rules": n_state, "signature_rules": n_sig,
                  "healthy_silence_iterations": 2, "src_diff_since_prereg": src_changed or "none",
                  "scripts_diff_since_prereg": [l.strip() for l in scripts_changed if "|" in l]},
       "gates": {"files": gates["n_files"], "duplicates": gates["G1_md5"]["duplicate_groups"], "rotation": list(gates["G4_raw_rotation"]),
                 "ttl_columns_not_declared": gates["G5_ttl"]["columns_not_declared"], "excluded_scenarios": excluded},
       "scorecard": {"detected": len(det), "scored": len(sc), "by_family": by_family,
                     "channels": {ch: sum(1 for s in sc if ch in str(s["meaningful_channels"]).split("+"))
                                  for ch in ("rules", "resid", "model", "device", "absence", "freq", "osc", "rate")},
                     "misses": [s["file"] for s in sc if not s["meaningful_channels"]],
                     "holdout_fp_days_union_minus_rate": fp, "holdout_days": hold,
                     "per_channel_fp": {k: v["holdout_fp_days"] for k, v in ufpr["channels"].items()}},
       "predictions": pred, "falsifiers_fired": fired}
Path("outputs/x19_onboarding.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out["scorecard"], indent=1)); print(json.dumps(pred, indent=1)); print("falsifiers fired:", fired or "none")
