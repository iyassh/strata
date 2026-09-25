"""X29 follow-up (review finding): which residual channel carries each detection on
the simulated RTU. The scorecard records channel families only ("resid"); this
re-scores every fault file per residual rule with the bands the deployed facade
fits on the baseline (alignment channels off) and records the flagged days.

    uv run python scripts/x29_residual_credits.py -> outputs/x29_residual_credits.json
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
import strata.core.detection as _detmod  # noqa: E402
from strata.core.pipeline import fit  # noqa: E402
from strata.core.residuals import daily_residual_scores, flag_days, residual_floor  # noqa: E402
from strata.io.config import load_config  # noqa: E402


def _no_alignment(*_a, **_k):
    raise ImportError("alignment strata off: residual credits only")


def main() -> int:
    _detmod.build_detector = _no_alignment
    cfg = load_config(str(REPO / "configs/lbnl_rtu_sim"))
    man = yaml.safe_load((REPO / "configs/lbnl_rtu_sim/scenarios.yaml").read_text())
    base = pd.read_parquet(REPO / f"data/processed/rtu_sim/{man['healthy_file']}.parquet")
    det = fit(cfg, base)
    out = {"bands": {k: list(v) for k, v in det.residual_bands.items()}, "scenarios": {}}
    for s in man["scenarios"]:
        if not s["is_fault"] or s.get("exclude"):
            continue
        df = pd.read_parquet(REPO / f"data/processed/rtu_sim/{s['file']}.parquet")
        row = {"family": s["family"], "per_rule_flagged_days": {}, "evaluable_days": None}
        for rname, band in det.residual_bands.items():
            rs = daily_residual_scores(df, cfg, rule_name=rname)
            if rs.empty:
                row["per_rule_flagged_days"][rname] = 0
                continue
            rf = flag_days(rs, band, min_margin=residual_floor(cfg, rname, "residual_min_exceedance"))
            row["per_rule_flagged_days"][rname] = int(rf["flagged"].sum())
            row["evaluable_days"] = int(rf["evaluable"].sum())
        out["scenarios"][s["file"]] = row
        print(f"{s['file']:28s} {row['per_rule_flagged_days']}", flush=True)
    (REPO / "outputs/x29_residual_credits.json").write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
