"""X33 ledger — coverage audit of one system: before/after diff of the scorecard and the
false-alarm artefact across the configuration change, per-channel credits, and each new
residual rule's own holdout false alarms (facade fit on the fault-free year, alignment off).
Pre-registration: docs/plans/2026-09-25-x33-coverage-series-prereg.md

    uv run python scripts/x33_coverage.py --system sdahu --before <commit> [--after <commit>]
        -> outputs/x33_coverage_<system>.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
HEALTHY = {"sdahu": "AHU_annual", "pfpu": "PFPU_FaultFree", "sfpu": "SFPU_FaultFree", "ddahu": "DualDuct_FaultFree", "fcu": "FCU_FaultFree"}


def at(path, commit):
    if commit is None:
        return json.loads((REPO / path).read_text())
    return json.loads(subprocess.run(["git", "show", f"{commit}:{path}"], cwd=REPO, capture_output=True, text=True, check=True).stdout)


def per_rule_holdout_fp(system: str) -> dict:
    import strata.core.detection as detmod
    from strata.core.pipeline import fit
    from strata.core.residuals import daily_residual_scores, flag_days, residual_floor
    from strata.core.splits import holdout_mask
    from strata.io.config import load_config

    def _off(*_a, **_k):
        raise ImportError("alignment off for the per-rule null")
    detmod.build_detector = _off
    cfg = load_config(str(REPO / f"configs/lbnl_{system}"))
    df = pd.read_parquet(REPO / f"data/processed/{system}/{HEALTHY[system]}.parquet")
    det = fit(cfg, df)
    out = {}
    for rname, band in det.residual_bands.items():
        rs = daily_residual_scores(df, cfg, rule_name=rname)
        hmask = holdout_mask(rs["case_id"], cfg.rules["detection"]["holdout_days_per_month"])
        hf = flag_days(rs[hmask.values], band, min_margin=residual_floor(cfg, rname, "residual_min_exceedance"))
        out[rname] = {"holdout_fp": int(hf["flagged"].sum()), "holdout_evaluable": int(hf["evaluable"].sum()), "band": [float(band[0]), float(band[1])]}
    return out


def main() -> int:
    system = sys.argv[sys.argv.index("--system") + 1]
    before = sys.argv[sys.argv.index("--before") + 1]
    after = sys.argv[sys.argv.index("--after") + 1] if "--after" in sys.argv else None
    b, a = at(f"outputs/benchmark_v6_{system}.json", before), at(f"outputs/benchmark_v6_{system}.json", after)
    ub, ua = at(f"outputs/union_fpr_{system}.json", before), at(f"outputs/union_fpr_{system}.json", after)
    B = {x["file"]: x for x in b["scenarios"] if x["is_fault"] and not x["excluded"]}
    A = {x["file"]: x for x in a["scenarios"] if x["is_fault"] and not x["excluded"]}
    chan = lambda x: set(str(x["meaningful_channels"]).split("+")) if x["meaningful_channels"] else set()
    rules_b = yaml.safe_load(subprocess.run(["git", "show", f"{before}:configs/lbnl_{system}/rules.yaml"], cwd=REPO, capture_output=True, text=True, check=True).stdout)
    rules_a = yaml.safe_load((REPO / f"configs/lbnl_{system}/rules.yaml").read_text())
    new_rules = sorted(set(rules_a["events"]) - set(rules_b["events"]))
    sens_b = yaml.safe_load(subprocess.run(["git", "show", f"{before}:configs/lbnl_{system}/sensors.yaml"], cwd=REPO, capture_output=True, text=True, check=True).stdout)
    sens_a = yaml.safe_load((REPO / f"configs/lbnl_{system}/sensors.yaml").read_text())
    rows = {f: {"before": B[f]["meaningful_channels"], "after": A[f]["meaningful_channels"], "ttd_before": B[f].get("ttd_days"), "ttd_after": A[f].get("ttd_days"),
                "residual_days": [B[f].get("residual_days"), A[f].get("residual_days")]} for f in A}
    out = {"prereg": "docs/plans/2026-09-25-x33-coverage-series-prereg.md", "system": system, "before_commit": before, "after_commit": after or "working tree",
           "columns_mapped": [len(sens_b["canonical_to_csv"]) - 1, len(sens_a["canonical_to_csv"]) - 1], "columns_excluded": sorted((sens_a.get("unmapped") or {}).keys()),
           "new_rules": new_rules, "scored": len(A),
           "detected_before": sum(1 for f in B if B[f]["meaningful_channels"]), "detected_after": sum(1 for f in A if A[f]["meaningful_channels"]),
           "gained": sorted(f for f in A if A[f]["meaningful_channels"] and not B[f]["meaningful_channels"]),
           "lost": sorted(f for f in A if B[f]["meaningful_channels"] and not A[f]["meaningful_channels"]),
           "channel_changes": {f: r for f, r in rows.items() if r["before"] != r["after"]},
           "ttd_later": sorted(f for f in A if (A[f].get("ttd_days") or 0) > (B[f].get("ttd_days") or 0) and B[f]["meaningful_channels"]),
           "deployed_fp": [ub["union_minus_rate"]["holdout_fp_days"], ua["union_minus_rate"]["holdout_fp_days"]],
           "per_channel_fp": {k: [ub["channels"].get(k, {}).get("holdout_fp_days"), ua["channels"].get(k, {}).get("holdout_fp_days")] for k in ua["channels"]},
           "model_rows_identical": all((B[f].get("model_days"), B[f].get("device_days")) == (A[f].get("model_days"), A[f].get("device_days")) for f in A),
           "new_rule_holdout_fp": {}, "new_rule_credited_scenarios": {}}
    prf = per_rule_holdout_fp(system)
    for r in new_rules:
        if r in prf:
            out["new_rule_holdout_fp"][r] = prf[r]
    # credits: a new residual rule is 'credited' if the residual channel is credited on a scenario whose residual days rose vs before
    resid_credit = sorted(f for f in A if "resid" in chan(A[f]) and (A[f].get("residual_days") or 0) > (B[f].get("residual_days") or 0))
    out["residual_days_rose_and_credited"] = resid_credit
    out["adoption"] = {r: ("keep" if (v["holdout_fp"] <= 1 or resid_credit) else "remove (credited nowhere, >1 holdout day)") for r, v in out["new_rule_holdout_fp"].items()}
    dep_b, dep_a = out["deployed_fp"]
    pred = {"P1_no_loss": not out["lost"], "P2_budget": dep_a <= 10 and dep_a <= dep_b + 3, "P2_new_rule_fp_le_3": all(v["holdout_fp"] <= 3 for v in out["new_rule_holdout_fp"].values()),
            "P3_some_new_channel_credited": bool(resid_credit) or any("osc" in chan(A[f]) and "osc" not in chan(B[f]) for f in A) or any(r in str(A[f]["meaningful_channels"]) for f in A for r in new_rules),
            "P4_ttd_not_later": not out["ttd_later"], "P5_model_rows_identical": out["model_rows_identical"]}
    fired = []
    if out["lost"]: fired.append(f"F-{system}.a: detection lost {out['lost']}")
    if not pred["P2_budget"] or not pred["P2_new_rule_fp_le_3"]: fired.append(f"F-{system}.b: budget or per-rule false alarms exceeded {out['new_rule_holdout_fp']}")
    if not pred["P5_model_rows_identical"]: fired.append(f"F-{system}.c: model/device rows changed")
    out["predictions"] = pred; out["falsifiers_fired"] = fired
    (REPO / f"outputs/x33_coverage_{system}.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"[{system}] columns {out['columns_mapped'][0]}->{out['columns_mapped'][1]} mapped, excluded {out['columns_excluded']} | detected {out['detected_before']}->{out['detected_after']}/{out['scored']} gained {out['gained']} lost {out['lost']} | deployed FP {dep_b}->{dep_a} | per-channel {out['per_channel_fp']}")
    for r, v in out["new_rule_holdout_fp"].items(): print(f"   new rule {r:22s} holdout FP {v['holdout_fp']}/{v['holdout_evaluable']} band {v['band']} -> {out['adoption'][r]}")
    print("   channel changes:", out["channel_changes"] or "none"); print("  ", pred); print("   falsifiers:", fired or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
