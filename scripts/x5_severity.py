"""X5 — severity monotonicity (pre-registered: PHASE8_PLAN.md @ 65fe3b8).

Usage: uv run python scripts/x5_severity.py

Spearman rho between severity rank and DEPLOYED alarm-day count
(significant-union days minus rate-only days), from committed artifacts
only. FPU ladders only (SDAHU stuck families saturate 365/365 -> rho
degenerate; coi_leakage is ERRATA E2-vacuous). Excluded scenarios skipped.
Caveats carried in the artifact: per-day autocorrelation; ceiling effects
reported per ladder. Artifact: outputs/x5_severity.json
"""

import json
import re
import sys
from pathlib import Path

from scipy.stats import spearmanr

SEVERITY_ORDER = {"Minor": 1, "Moderate": 2, "Severe": 3}

LADDERS = {  # ladder name -> (system, regex with severity group, parser)
    "pfpu_reheat_stuck": ("pfpu", r"ReheatVLVStuck_(\d+)%", int),
    "sfpu_reheat_stuck": ("sfpu", r"ReheatVLVStuck_(\d+)%", int),
    "pfpu_damper_stuck": ("pfpu", r"VAVDMPRStuck_(\d+)%", int),
    "sfpu_damper_stuck": ("sfpu", r"VAVDMPRStuck_(\d+)%", int),
    "pfpu_fouling_air": ("pfpu", r"Fouling_Airside_(\w+)", lambda s: SEVERITY_ORDER[s]),
    "sfpu_fouling_air": ("sfpu", r"Fouling_Airside_(\w+)", lambda s: SEVERITY_ORDER[s]),
    "pfpu_fouling_water": ("pfpu", r"Fouling_Waterside_(\w+)", lambda s: SEVERITY_ORDER[s]),
    "sfpu_fouling_water": ("sfpu", r"Fouling_Waterside_(\w+)", lambda s: SEVERITY_ORDER[s]),
    "pfpu_airflow_bias_abs": ("pfpu", r"VAVAirflow_[+-](\d+)CFM", int),
    "sfpu_airflow_bias_abs": ("sfpu", r"VAVAirflow_[+-](\d+)CFM", int),
    "pfpu_rmtemp_bias_abs": ("pfpu", r"RMTEMP_[+-](\d)C", int),
    "sfpu_rmtemp_bias_abs": ("sfpu", r"RMTEMP_[+-](\d)C", int),
}

bench = {s: json.loads(Path(f"outputs/benchmark_v6_{s}.json").read_text())
         for s in ("pfpu", "sfpu")}
union = {s: json.loads(Path(f"outputs/union_fpr_{s}.json").read_text())
         for s in ("pfpu", "sfpu")}
rate_only = {s: {x["label"]: x["rate_only_alarm_days"]
                 for x in union[s]["rate_demotion"]["scenarios_with_rate_significant"]}
             for s in ("pfpu", "sfpu")}

out = {"pre_registration": "PHASE8_PLAN.md @ 65fe3b8", "ladders": {}}
falsifiers = []
for name, (system, pattern, parse) in LADDERS.items():
    rungs = []
    for s in bench[system]["scenarios"]:
        if s.get("excluded"):
            continue
        m = re.search(pattern, s["file"])
        if not m:
            continue
        alarm = len(s["flag_days"]["sig_union"]) - rate_only[system].get(s["label"], 0)
        rungs.append((parse(m.group(1)), alarm, s["file"], s["evaluable_days"]))
    if len(rungs) < 3:
        continue
    rungs.sort()
    sev = [r[0] for r in rungs]
    alarms = [r[1] for r in rungs]
    rho, p = spearmanr(sev, alarms)
    at_ceiling = sum(1 for r in rungs if r[1] >= r[3])
    out["ladders"][name] = {
        "rungs": [{"severity": r[0], "deployed_alarm_days": r[1], "file": r[2]}
                  for r in rungs],
        "spearman_rho": None if rho != rho else round(float(rho), 3),
        "p_value_naive": None if p != p else round(float(p), 4),
        "n": len(rungs), "rungs_at_ceiling": at_ceiling,
    }
    print(f"{name:24s} n={len(rungs)} rho={rho if rho==rho else float('nan'):+.3f} "
          f"alarms={alarms} ceiling={at_ceiling}")
    if rho == rho and rho < 0 and p == p and p < 0.05:
        falsifiers.append(f"F-X5.a: {name} significantly anti-monotone (rho={rho:.3f})")

out["caveats"] = [
    "p-values are naive (per-day autocorrelation; tiny n) — report rho, not stars",
    "deployed alarm days = sig_union minus rate-only days",
    "ceiling effects reported per ladder; a saturated ladder cannot show monotonicity",
]
out["falsifiers_fired"] = falsifiers
Path("outputs/x5_severity.json").write_text(json.dumps(out, indent=1))
print(f"\nfalsifiers fired: {falsifiers or 'NONE'}")
print("wrote outputs/x5_severity.json")
sys.exit(0 if not falsifiers else 2)
