"""X22 — positive control for the conformance channel: inject genuine order
violations into the healthy HOLDOUT traces and ask whether the deployed
model channel (same net, same threshold, same significance gate) fires.
Pre-registration: docs/plans/2026-09-24-x22-conformance-positive-control-prereg.md

    uv run python scripts/x22_positive_control.py [--systems a,b] -> outputs/x22_positive_control.json
"""
from __future__ import annotations

import json
import os
import random
import sys
import warnings
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from strata.core.detection import build_detector, classify_days, holdout_mask  # noqa: E402
from strata.core.significance import model_significant  # noqa: E402
from strata.hvac.events import abstract_events, state_only  # noqa: E402
from strata.io.config import load_config  # noqa: E402

SPEC = {"sdahu": ("configs/lbnl_sdahu", "data/processed/sdahu/AHU_annual.parquet"),
        "pfpu": ("configs/lbnl_pfpu", "data/processed/pfpu/PFPU_FaultFree.parquet"),
        "sfpu": ("configs/lbnl_sfpu", "data/processed/sfpu/SFPU_FaultFree.parquet"),
        "ddahu": ("configs/lbnl_ddahu", "data/processed/ddahu/DualDuct_FaultFree.parquet"),
        "fcu": ("configs/lbnl_fcu", "data/processed/fcu/FCU_FaultFree.parquet")}
SEED = 7
START_CANDIDATES = ("system_started", "night_cycle_ended")


def perturb(trace: list[str], op: str, k: int, rng: random.Random, start_act: str | None) -> tuple[list[str], bool]:
    """Return (new_trace, changed)."""
    t = list(trace)
    if len(t) < 2:
        return t, False
    if op == "reverse":
        return t[::-1], t[::-1] != t
    if op == "swap":
        cand = [i for i in range(len(t) - 1) if t[i] != t[i + 1]]
        if not cand:
            return t, False
        for i in rng.sample(cand, min(k, len(cand))):
            t[i], t[i + 1] = t[i + 1], t[i]
        return t, t != list(trace)
    if op == "skip":
        idx = sorted(rng.sample(range(len(t)), min(k, len(t) - 1)), reverse=True)
        for i in idx:
            del t[i]
        return t, True
    if op == "skip_start":
        if start_act is None or start_act not in t:
            return t, False
        return [a for a in t if a != start_act], True
    if op == "dup_block":
        if len(t) < 3:
            return t, False
        i = rng.randrange(0, len(t) - 2)
        return t[:i + 3] + t[i:i + 3] + t[i + 3:], True
    raise ValueError(op)


def rebuild_log(day_traces: dict[str, list[str]]) -> pd.DataFrame:
    rows = []
    base = pd.Timestamp("2000-01-01")
    for d, tr in day_traces.items():
        for j, a in enumerate(tr):
            rows.append((d, a, base + pd.Timedelta(days=0, seconds=j)))
    log = pd.DataFrame(rows, columns=["case_id", "activity", "timestamp"])
    log["alphabet"] = "state"
    return log


def run_system(system: str) -> dict:
    cfg_dir, hp = SPEC[system]
    cfg = load_config(str(REPO / cfg_dir))
    df = pd.read_parquet(REPO / hp)
    log = abstract_events(df, cfg)
    det = build_detector(cfg, log)
    slog = state_only(log).sort_values(["case_id", "timestamp"])
    hold = holdout_mask(slog["case_id"], cfg.rules["detection"]["holdout_days_per_month"])
    hold_log = slog[hold]
    traces = {d: list(g["activity"]) for d, g in hold_log.groupby("case_id", sort=True)}
    n_days = len(traces)
    labels = sorted({t.label for t in det.net.transitions if t.label})
    start_act = next((a for a in START_CANDIDATES if any(a in tr for tr in traces.values())), None)
    # unperturbed baseline on the same days
    base = classify_days(det, rebuild_log(traces))
    fp0 = int(base["flagged"].sum())
    base_fit = base.set_index("case_id")["fitness"]
    healthy_min = float(base_fit.min())
    out = {"threshold": det.threshold, "n_holdout_days": n_days, "holdout_fp_unperturbed": fp0,
           "net_labels": labels, "start_activity": start_act,
           "mean_trace_len": sum(len(t) for t in traces.values()) / max(n_days, 1), "arms": {}}
    print(f"[{system}] threshold {det.threshold:.4f}, holdout days {n_days}, unperturbed flagged {fp0}, "
          f"mean trace len {out['mean_trace_len']:.1f}, start={start_act}", flush=True)
    arms = [("reverse", 0), ("swap", 1), ("swap", 2), ("swap", 4), ("swap", 8),
            ("skip", 1), ("skip", 2), ("skip", 4), ("skip_start", 0), ("dup_block", 0)]
    for op, k in arms:
        rng = random.Random(SEED)
        pert, changed = {}, 0
        for d, tr in traces.items():
            nt, ch = perturb(tr, op, k, rng, start_act)
            pert[d] = nt; changed += int(ch)
        per_day = classify_days(det, rebuild_log(pert))
        flagged = int(per_day["flagged"].sum())
        sig = model_significant(flagged, n_days, fp0, n_days)
        key = f"{op}_{k}" if k else op
        pf = per_day.set_index("case_id")["fitness"].reindex(base_fit.index)
        # separability of perturbed vs unperturbed per-day fitness, independent of the threshold:
        # AUC (P[perturbed < healthy]) and the oracle TPR at ZERO healthy false alarms
        # (threshold = the healthy holdout minimum), plus the TPR the deployed threshold gives
        pairs = [(a, b) for a in pf.dropna() for b in base_fit.dropna()]
        auc = sum(1.0 if a < b else 0.5 if a == b else 0.0 for a, b in pairs) / max(len(pairs), 1)
        oracle_tpr = float((pf < healthy_min).mean())
        out["arms"][key] = {"op": op, "k": k, "traces_changed": changed, "flagged_days": flagged,
                            "flagged_frac": flagged / n_days, "mean_fitness": float(per_day["fitness"].mean()),
                            "significant": bool(sig),
                            "auc_perturbed_below_healthy": auc, "oracle_tpr_at_zero_fp": oracle_tpr,
                            "healthy_min_fitness": healthy_min, "perturbed_median_fitness": float(pf.median())}
        print(f"[{system}] {key:12s} changed {changed:3d}/{n_days}  flagged {flagged:3d}  "
              f"mean fitness {per_day['fitness'].mean():.3f}  significant={sig}  AUC {auc:.2f}  oracleTPR {oracle_tpr:.2f}", flush=True)
    return out


def main() -> int:
    systems = sys.argv[sys.argv.index("--systems") + 1].split(",") if "--systems" in sys.argv else list(SPEC)
    res = {s: run_system(s) for s in systems}
    # predictions
    def sig(s, arm):
        return res[s]["arms"][arm]["significant"] if s in res else None
    p1 = {s: sig(s, "reverse") for s in res}
    p1_pass = all(p1.get(s) for s in ("sdahu", "ddahu", "fcu") if s in res) and not any(p1.get(s) for s in ("pfpu", "sfpu") if s in res)
    p2 = {s: sig(s, "skip_start") for s in res}
    p2_pass = all(p2.get(s) for s in ("ddahu", "sfpu") if s in res) and not any(p2.get(s) for s in ("sdahu", "pfpu", "fcu") if s in res)
    def mono(s):
        f = [res[s]["arms"][f"swap_{k}"]["flagged_frac"] for k in (1, 2, 4, 8)]
        return all(b >= a for a, b in zip(f, f[1:]))
    p3_mono = {s: mono(s) for s in res}
    p3_sig8 = sum(1 for s in res if sig(s, "swap_8"))
    p3_pass = all(p3_mono.values()) and p3_sig8 >= 3
    def skip_rise(s):
        f = [res[s]["arms"][f"skip_{k}"]["flagged_frac"] for k in (1, 2, 4)]
        return all(b >= a for a, b in zip(f, f[1:]))
    p4_rise = {s: skip_rise(s) for s in res}
    p4_absorbed = {s: not sig(s, "skip_1") for s in ("pfpu", "sfpu") if s in res}
    p4_pass = all(p4_rise.values()) and all(p4_absorbed.values())
    p5 = {s: sig(s, "dup_block") for s in res}
    p5_pass = not any(p5.values())
    fired = []
    if not any(sig(s, "reverse") or sig(s, "skip_start") for s in res):
        fired.append("F-X22.a: reverse and skip-start non-significant on every system — the instrument is blind to order at the deployed gate")
    if any(p1.get(s) for s in ("pfpu", "sfpu") if s in res):
        fired.append("F-X22.b: a fan-powered unit's net fires under reversal — the order-permissive reading is wrong")
    if sum(1 for s in res if not p3_mono[s]) >= 2:
        fired.append("F-X22.c: no monotone rise in swaps on two or more systems")
    out = {"prereg": "docs/plans/2026-09-24-x22-conformance-positive-control-prereg.md", "seed": SEED, "systems": res,
           "predictions": {"P1_reverse": p1, "P1_pass": p1_pass, "P2_skip_start": p2, "P2_pass": p2_pass,
                           "P3_swap_monotone": p3_mono, "P3_systems_significant_at_8": p3_sig8, "P3_pass": p3_pass,
                           "P4_skip_rise": p4_rise, "P4_single_skip_absorbed_fpu": p4_absorbed, "P4_pass": p4_pass,
                           "P5_dup_block": p5, "P5_pass": p5_pass},
           "falsifiers_fired": fired}
    (REPO / "outputs/x22_positive_control.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["predictions"], indent=1)); print("falsifiers fired:", fired or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
