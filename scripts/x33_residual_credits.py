"""X33 diagnostic — which residual rule carries which scenario on one system: per fault file,
flagged days per residual rule under the facade's own bands (alignment off).

    uv run python scripts/x33_residual_credits.py --system pfpu [--scenarios a,b] -> outputs/x33_residual_credits_<system>.json
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
HEALTHY = {"sdahu": "AHU_annual", "pfpu": "PFPU_FaultFree", "sfpu": "SFPU_FaultFree", "ddahu": "DualDuct_FaultFree", "fcu": "FCU_FaultFree"}


def main() -> int:
    import strata.core.detection as detmod
    from strata.core.pipeline import fit
    from strata.core.residuals import daily_residual_scores, flag_days, residual_floor
    from strata.io.config import load_config

    def _off(*_a, **_k):
        raise ImportError("alignment off")
    detmod.build_detector = _off
    system = sys.argv[sys.argv.index("--system") + 1]
    only = sys.argv[sys.argv.index("--scenarios") + 1].split(",") if "--scenarios" in sys.argv else None
    cfg = load_config(str(REPO / f"configs/lbnl_{system}"))
    man = yaml.safe_load((REPO / f"configs/lbnl_{system}/scenarios.yaml").read_text())
    det = fit(cfg, pd.read_parquet(REPO / f"data/processed/{system}/{HEALTHY[system]}.parquet"))
    out = {"system": system, "bands": {k: [float(v[0]), float(v[1])] for k, v in det.residual_bands.items()}, "scenarios": {}}
    for s in man["scenarios"]:
        if not s["is_fault"] or s.get("exclude") or (only and s["file"] not in only):
            continue
        df = pd.read_parquet(REPO / f"data/processed/{system}/{s['file']}.parquet")
        row = {"family": s["family"], "per_rule_flagged_days": {}, "per_rule_evaluable_days": {}}
        for rname, band in det.residual_bands.items():
            rs = daily_residual_scores(df, cfg, rule_name=rname)
            if rs.empty:
                row["per_rule_flagged_days"][rname] = 0; row["per_rule_evaluable_days"][rname] = 0; continue
            rf = flag_days(rs, band, min_margin=residual_floor(cfg, rname, "residual_min_exceedance"))
            row["per_rule_flagged_days"][rname] = int(rf["flagged"].sum()); row["per_rule_evaluable_days"][rname] = int(rf["evaluable"].sum())
        out["scenarios"][s["file"]] = row
        top = sorted(row["per_rule_flagged_days"].items(), key=lambda kv: -kv[1])[:4]
        print(f"{s['file']:44s} {top}", flush=True)
    path = REPO / f"outputs/x33_residual_credits_{system}.json"
    if only and path.exists():   # merge into an existing artefact
        old = json.loads(path.read_text()); old["scenarios"].update(out["scenarios"]); out = old
    path.write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
