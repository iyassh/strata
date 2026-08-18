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
    n_fault_days = sum(s["evaluable_days"] for s in b["scenarios"]
                       if s["is_fault"] and not s.get("excluded")
                       and s.get("meaningful_channels"))
    ratio = fp / (fp + tp) if (fp + tp) else 0.0
    out[system] = {"fp_days_healthy_holdout": fp,
                   "healthy_holdout_days": u["holdout_days"],
                   "tp_alarm_days_fault_scenarios": tp,
                   "fault_scenario_days_observed": n_fault_days,
                   "cry_wolf_ratio": round(ratio, 5)}
    print(f"[{system}] FP {fp}/{u['holdout_days']} healthy-holdout days | "
          f"TP {tp} over {n_fault_days} fault-scenario days | cry-wolf {ratio:.4%}")

out["definition"] = ("FP_days/(FP_days+TP_days) for the deployed detector "
                     "(significance-gated union, rate diagnostic-only); FP on the "
                     "96-day healthy holdout, TP across non-excluded detected "
                     "fault scenarios' significant-union days minus rate-only days. "
                     "ALWAYS quote with both denominators: exposure is 96 healthy "
                     "days vs thousands of fault-scenario days from 14-24 "
                     "simultaneous year-long single-fault runs no real operator "
                     "experiences at once — an operator-experience summary, not a "
                     "symmetric error rate.")
Path("outputs/crywolf.json").write_text(json.dumps(out, indent=1))
print("wrote outputs/crywolf.json")
