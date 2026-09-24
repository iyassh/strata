"""X29 ledger — refrigerant-side observability on the simulated RTU.
    uv run python scripts/x29_refrigerant_observability.py -> outputs/x29_refrigerant_observability.json
"""
import json
import subprocess
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
b = json.loads((REPO / "outputs/benchmark_v6_rtu_sim.json").read_text())
u = json.loads((REPO / "outputs/union_fpr_rtu_sim.json").read_text())
g = json.loads((REPO / "outputs/week0_audit_rtu_sim.json").read_text())
man = yaml.safe_load((REPO / "configs/lbnl_rtu_sim/scenarios.yaml").read_text())
fam = {m["file"]: m["family"] for m in man["scenarios"]}
sc = [s for s in b["scenarios"] if s["is_fault"] and not s["excluded"]]
by = {}
for s in sc:
    f = fam[s["file"]]; by.setdefault(f, []).append((s["file"], s["meaningful_channels"]))
def sev(name):
    import re; m = re.search(r"(\d+)", name.split("_")[-1]); return int(m.group(1)) if m else 0
def monotone(rows):
    rows = sorted(rows, key=lambda r: sev(r[0])); det = [bool(r[1]) for r in rows]
    first = next((i for i, d in enumerate(det) if d), None)
    return first is None or all(det[first:])
cond = by.get("condenser_fouling", []); evap = by.get("evaporator_fouling", [])
cond_det = sum(1 for _, m in cond if m); evap_det = sum(1 for _, m in evap if m)
cond_channels = {ch for _, m in cond if m for ch in str(m).split("+")}
other = [r for f, rows in by.items() if f not in ("condenser_fouling", "evaporator_fouling") for r in rows]
conf_only = [f for f, m in [(s["file"], s["meaningful_channels"]) for s in sc] if m and set(str(m).split("+")) <= {"model", "device"}]
src_changed = subprocess.run(["git", "diff", "--stat", "df064db", "HEAD", "--", "src/"], capture_output=True, text=True).stdout.strip()
fp, hd = u["union_minus_rate"]["holdout_fp_days"], u["holdout_days"]
pred = {"P1_gates_clean": g["G1_md5"]["duplicate_groups"] == [] and all(v["set_identical_to_healthy"] for v in g["G3_calendar"].values()) and g["G5_ttl"]["columns_not_declared"] == [],
        "P1_silence_iterations": 1,
        "P2_budget_le_10pct": fp / hd <= 0.10, "P2_fp": [fp, hd],
        "P3_cond_ge_3_of_5": cond_det >= 3, "P3_cond_channel_ok": bool(cond_channels & {"resid", "rules"}), "P3_cond_monotone": monotone(cond),
        "P4_evap_ge_3_of_5": evap_det >= 3, "P4_evap_monotone": monotone(evap),
        "P5_other_ge_6_of_14": sum(1 for _, m in other if m) >= 6,
        "P6_none_conformance_only": conf_only == [], "config_only": src_changed == ""}
fired = []
if not pred["P3_cond_ge_3_of_5"] and not pred["P4_evap_ge_3_of_5"]: fired.append("F-X29.a: fouling not seen even with refrigerant-side points")
if not pred["P2_budget_le_10pct"]: fired.append("F-X29.b: budget exceeded")
if src_changed: fired.append("F-X29.c: src/ change required")
out = {"prereg": "docs/plans/2026-09-24-x29-refrigerant-observability-prereg.md", "scored": len(sc), "detected": sum(1 for s in sc if s["meaningful_channels"]),
       "by_family": {f: [(n, m) for n, m in rows] for f, rows in by.items()},
       "family_counts": {f: [sum(1 for _, m in rows if m), len(rows)] for f, rows in by.items()},
       "per_channel_fp": {k: v["holdout_fp_days"] for k, v in u["channels"].items()}, "deployed_fp": [fp, hd], "naive_fp": u["union_all8"]["holdout_fp_days"],
       "channel_credits": {ch: sum(1 for s in sc if ch in str(s["meaningful_channels"]).split("+")) for ch in ("rules", "resid", "model", "device", "absence", "freq", "osc", "rate")},
       "predictions": pred, "falsifiers_fired": fired}
(REPO / "outputs/x29_refrigerant_observability.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"detected {out['detected']}/{out['scored']} | FP {fp}/{hd} naive {out['naive_fp']} | families {out['family_counts']}")
for f, rows in by.items():
    print(" ", f, [(n.replace('RTU_sim_', ''), m) for n, m in sorted(rows, key=lambda r: sev(r[0]))])
print(pred); print("falsifiers:", fired or "none")
