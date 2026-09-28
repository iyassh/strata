"""X37 — diagnosis layer: signed rule patterns + redundant-pair consensus, scored leave-one-out.
Pre-registration: docs/plans/2026-09-27-x37-diagnosis-layer-prereg.md

    uv run python scripts/x37_diagnosis.py -> outputs/x37_diagnosis.json
"""
from __future__ import annotations

import json
import os
import re
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
from component_attribution import rule_component, seeded_component  # noqa: E402

SYSTEMS = ["sdahu", "pfpu", "sfpu", "ddahu", "fcu"]
HEALTHY = {"sdahu": "AHU_annual", "pfpu": "PFPU_FaultFree", "sfpu": "SFPU_FaultFree", "ddahu": "DualDuct_FaultFree", "fcu": "FCU_FaultFree"}
ZONE_RE = re.compile(r"_(I|W|S|E|SB|SA)$")
GROUPS = {"pfpu": {"ra_minus_zone": ("return-air sensor", "zone_temp_sensor")}, "sfpu": {"ra_minus_zone": ("return-air sensor", "zone_temp_sensor")},
          "ddahu": {"box_static_C": ("cold deck", "static_sensor"), "box_static_H": ("hot deck", "static_sensor"), "box_eat_C": ("cold deck", "sat_sensor"), "box_eat_H": ("hot deck", "sat_sensor")}}


def family(system, f):
    man = {m["file"]: m["family"] for m in yaml.safe_load((REPO / f"configs/lbnl_{system}/scenarios.yaml").read_text())["scenarios"]}
    fam = man.get(f, "?")
    for w in ("Airside", "Waterside"):
        if w in f: fam += "_" + w.lower()
    for w in ("Cooling", "Heating", "_Cold", "_Hot", "_CSA", "_HSA", "_CSP", "_HSP", "Cool", "Heat"):
        if w in f: fam += "_" + w.strip("_").lower(); break
    return fam


def signed_pattern(system, cfg, det, x, cred, log_days):
    """set of (rule stem, sign); sign from the scenario's median residual vs the healthy band."""
    from strata.core.residuals import daily_residual_scores
    chans = set(str(x["meaningful_channels"]).split("+")); pat = set(); per_rule = {}
    df = None
    if "resid" in chans and x["file"] in cred:
        for r, d in cred[x["file"]]["per_rule_flagged_days"].items():
            if d < 0.1 * max(cred[x["file"]]["per_rule_evaluable_days"].get(r, 1), 1):
                continue
            if df is None:
                df = pd.read_parquet(REPO / f"data/processed/{system}/{x['file']}.parquet")
            rs = daily_residual_scores(df, cfg, rule_name=r)["score"].dropna()
            lo, hi = det.residual_bands[r]; med = float(rs.median()) if len(rs) else float("nan")
            sign = "above" if med > hi else "below" if med < lo else "inside"
            per_rule[r] = {"days": d, "median": med, "band": [lo, hi], "sign": sign}
            if sign != "inside":
                pat.add((ZONE_RE.sub("", r), sign))
    if "rules" in chans:
        for r, d in log_days.items():
            if d >= 5 and r not in per_rule:
                # run 2 (after the run-1 defect): a residual-kind rule that fires its fixed band is a moving copy too;
                # its direction is computed the same way as for the residual channel
                if r in det.residual_bands:
                    if df is None:
                        df = pd.read_parquet(REPO / f"data/processed/{system}/{x['file']}.parquet")
                    rs = daily_residual_scores(df, cfg, rule_name=r)["score"].dropna()
                    lo, hi = det.residual_bands[r]; med = float(rs.median()) if len(rs) else float("nan")
                    sign = "above" if med > hi else "below" if med < lo else "fires"
                    per_rule[r] = {"days": d, "median": med, "band": [lo, hi], "sign": sign}; pat.add((ZONE_RE.sub("", r), sign))
                else:
                    per_rule[r] = {"days": d, "sign": "fires"}; pat.add((ZONE_RE.sub("", r), "fires"))
    return frozenset(pat), per_rule


def consensus_component(system, per_rule):
    """redundant groups, as pre-registered: every copy moving in the SAME direction -> shared end;
    exactly one copy moving -> that zone; anything else (copies moving in opposite directions, two or
    three copies) -> no consensus. Run 2 counted three or more copies moving in any direction as
    consensus, which blamed the shared return-air sensor when one zone's copy moved the opposite way
    to the other three (kept as outputs/x37_diagnosis_run2.json)."""
    n_copies = 4
    for stem, shared in GROUPS.get(system, {}).items():
        moving = {r: v["sign"] for r, v in per_rule.items() if r.startswith(stem + "_") and v.get("sign") in ("above", "below")}
        if not moving:
            continue
        zones = {ZONE_RE.search(r).group(1) for r in moving if ZONE_RE.search(r)}
        if len(zones) == n_copies and len(set(moving.values())) == 1:
            return shared, f"consensus: all {n_copies} copies move {next(iter(moving.values()))}"
        if len(zones) == 1:
            z = next(iter(zones)); comp = "zone_damper" if stem.startswith("box_static") else "zone_temp_sensor"
            return (f"zone {z}", comp), "single copy moves"
        return None, f"no consensus: {len(zones)} copies move, directions {sorted(set(moving.values()))}"
    return None, None


def main() -> int:
    import strata.core.detection as detmod
    from strata.core.pipeline import fit
    from strata.hvac.events import abstract_events
    from strata.io.config import load_config

    def _off(*_a, **_k):
        raise ImportError("alignment off")
    detmod.build_detector = _off
    rows = []
    for s in SYSTEMS:
        cfg = load_config(str(REPO / f"configs/lbnl_{s}"))
        det = fit(cfg, pd.read_parquet(REPO / f"data/processed/{s}/{HEALTHY[s]}.parquet"))
        card = json.loads((REPO / f"outputs/benchmark_v6_{s}.json").read_text())["scenarios"]
        cred = json.loads((REPO / f"outputs/x33_residual_credits_{s}.json").read_text())["scenarios"]
        attr = {r["file"]: r for r in json.loads((REPO / "outputs/component_attribution.json").read_text())["rows"] if r["system"] == s}
        for x in card:
            if not (x["is_fault"] and not x["excluded"] and x["meaningful_channels"]):
                continue
            log_days = {}
            if "rules" in str(x["meaningful_channels"]):
                log = abstract_events(pd.read_parquet(REPO / f"data/processed/{s}/{x['file']}.parquet"), cfg)
                sig = log[log["alphabet"] == "signature"]; log_days = {r: int(n) for r, n in sig.groupby("activity")["case_id"].nunique().items()}
            pat, per_rule = signed_pattern(s, cfg, det, x, cred, log_days)
            cons, why = consensus_component(s, per_rule)
            rows.append({"system": s, "file": x["file"], "family": family(s, x["file"]), "pattern": sorted(f"{a}:{b}" for a, b in pat), "per_rule": per_rule,
                         "consensus_component": list(cons) if cons else None, "consensus_reason": why, "x34_verdict": attr[x["file"]]["verdict"], "seeded_component": list(seeded_component(s, x["file"]) or ())})
            print(f"{s:6s} {x['file']:44s} pattern {rows[-1]['pattern'][:4]} consensus {cons}", flush=True)
    # leave-one-out family diagnosis
    def jacc(a, b):
        a, b = set(a), set(b); return len(a & b) / len(a | b) if a | b else 0.0
    n_res = fam_ok = 0; unresolved = 0
    for r in rows:
        others = [o for o in rows if o["system"] == r["system"] and o is not r]
        exact = [o for o in others if o["pattern"] == r["pattern"] and r["pattern"]]
        pool = exact or [o for o in others if jacc(o["pattern"], r["pattern"]) > 0.5]
        if not pool:
            r["diagnosed_family"] = None; unresolved += 1; continue
        pred = Counter(o["family"] for o in pool).most_common(1)[0][0]
        r["diagnosed_family"] = pred; n_res += 1; fam_ok += (pred == r["family"])
    # component with consensus override
    def comp_verdict(r):
        seeded = tuple(r["seeded_component"]) if r["seeded_component"] else None
        c = tuple(r["consensus_component"]) if r["consensus_component"] else None
        if c and seeded:
            same_sub = c[0] == seeded[0] or (seeded[0] == "zone (unspecified)" and c[0].startswith("zone "))
            if same_sub and (c[1] == seeded[1] or seeded[1] in c[1].split("/")):
                return "exact"
            if same_sub:
                return "subsystem"
            if c[0].startswith("zone ") and seeded[0] == "zone (unspecified)":
                return "exact"
            return "wrong"
        return r["x34_verdict"]
    for r in rows:
        r["component_verdict_x37"] = comp_verdict(r)
    n = len(rows); cv = Counter(r["component_verdict_x37"] for r in rows)
    out = {"prereg": "docs/plans/2026-09-27-x37-diagnosis-layer-prereg.md", "rows": rows,
           "family": {"resolved": n_res, "unresolved": unresolved, "correct": fam_ok, "accuracy_resolved": round(fam_ok / max(n_res, 1), 3), "unresolved_rate": round(unresolved / n, 3)},
           "component": {v: cv.get(v, 0) for v in ("exact", "subsystem", "wrong", "unnamed")}, "n": n}
    out["component"]["exact_rate"] = round(cv.get("exact", 0) / n, 3); out["component"]["wrong_rate"] = round(cv.get("wrong", 0) / n, 3)
    dd = [r for r in rows if r["system"] == "ddahu" and "DMPRStuck_" in r["file"] and "OA" not in r["file"] and r["x34_verdict"] == "wrong"]
    biases = [r for r in rows if r["system"] == "ddahu" and ("SensorBias_HSP" in r["file"] or "SensorBias_CSP" in r["file"] or "SensorBias_HSA" in r["file"] or "SensorBias_CSA" in r["file"])]
    out["predictions"] = {"P1_family_ge_80pct": out["family"]["accuracy_resolved"] >= 0.80 and out["family"]["unresolved_rate"] <= 0.15,
                          "P2_component_exact_ge_78pct_and_wrong_lt_10pct": out["component"]["exact_rate"] >= 0.78 and out["component"]["wrong_rate"] < 0.10,
                          "P3_ddahu_damper_single_copy": all(r["consensus_reason"] == "single copy moves" for r in dd) and bool(dd),
                          "P3_ddahu_bias_consensus": sum(1 for r in biases if str(r["consensus_reason"]).startswith("consensus: all")), "P3_ddahu_bias_n": len(biases),
                          "P4_fcu_unresolved_component": Counter(r["component_verdict_x37"] for r in rows if r["system"] == "fcu")}
    fired = []
    if not out["predictions"]["P1_family_ge_80pct"]: fired.append("F-X37.a: family accuracy below 80 % or unresolved above 15 %")
    if out["component"]["wrong_rate"] >= 0.10: fired.append("F-X37.b: wrong-subsystem rate not below 10 %")
    out["falsifiers_fired"] = fired
    out["run"] = 3; out["run1_defect"] = "consensus ignored copies that moved through the rules channel (signature firings); run-1 artefact kept as outputs/x37_diagnosis_run1.json"
    out["run2_defect"] = "consensus counted three or more copies moving in any direction as 'all copies move' where the pre-registration says every copy in the same direction; run-2 artefact kept as outputs/x37_diagnosis_run2.json"
    (REPO / "outputs/x37_diagnosis.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(json.dumps({k: out[k] for k in ("family", "component", "predictions", "falsifiers_fired")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
