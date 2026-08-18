"""Phase 7 (gap S7) — the cry-wolf ratio of the deployed STRATA detector.

Usage: uv run python scripts/crywolf.py

Definition (v2 revision reporting addition): of every alarm-day the DEPLOYED
detector raises across the healthy holdout and all non-excluded fault
scenarios, what fraction is false?

    cry_wolf = FP_days / (FP_days + TP_days)

- FP_days: healthy-year deployed false alarms = union-minus-rate holdout FP
  (from outputs/union_fpr_<system>.json).
- TP_days: per detected scenario, the significant-union day count MINUS the
  rate-only days (the deployed detector does not page on rate), from
  outputs/benchmark_v6_<system>.json + the union artifact's rate-only counts.

Exposure asymmetry stated up front: FP is measured on 96 healthy holdout
days, TP on full fault years — the ratio is an operator-experience summary
("when it pages, how often is it wrong"), not a symmetric error rate.
Reads artifacts only (no data needed). Writes outputs/crywolf.json.
"""

import json
from pathlib import Path

out = {}
for system in ("sdahu", "pfpu", "sfpu"):
    u = json.loads(Path(f"outputs/union_fpr_{system}.json").read_text())
    b = json.loads(Path(f"outputs/benchmark_v6_{system}.json").read_text())
    fp = u["union_minus_rate"]["holdout_fp_days"]
    rate_only = {s["label"]: s["rate_only_alarm_days"]
                 for s in u["rate_demotion"]["scenarios_with_rate_significant"]}
    tp = 0
    for s in b["scenarios"]:
        if not s["is_fault"] or s.get("excluded") or not s.get("meaningful_channels"):
            continue
        tp += len(s["flag_days"]["sig_union"]) - rate_only.get(s["label"], 0)
    ratio = fp / (fp + tp) if (fp + tp) else 0.0
    out[system] = {"fp_days_healthy_holdout": fp, "tp_alarm_days_fault_scenarios": tp,
                   "cry_wolf_ratio": round(ratio, 5)}
    print(f"[{system}] FP {fp} | TP {tp} | cry-wolf {ratio:.4%}")

out["definition"] = ("FP_days/(FP_days+TP_days) for the deployed detector "
                     "(significance-gated union, rate diagnostic-only); FP on the "
                     "96-day healthy holdout, TP across non-excluded detected "
                     "fault scenarios' significant-union days minus rate-only days")
Path("outputs/crywolf.json").write_text(json.dumps(out, indent=1))
print("wrote outputs/crywolf.json")
