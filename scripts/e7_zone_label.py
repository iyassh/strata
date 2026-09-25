"""ERRATA E7 evidence — which zone's columns move in each PFPU/SFPU fault file (documentation says west, _W).
    uv run python scripts/e7_zone_label.py -> outputs/e7_zone_label.json
"""
import json
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
out = {"documentation": "LBNL_FDD_Data_Sets_FPU.pdf p.12: fault imposed in the west zone, identifier _W", "systems": {}}
for system, healthy in [("pfpu", "PFPU_FaultFree"), ("sfpu", "SFPU_FaultFree")]:
    h = pd.read_parquet(REPO / f"data/processed/{system}/{healthy}.parquet"); occ = h["SYS_CTL"] == 1
    man = yaml.safe_load((REPO / f"configs/lbnl_{system}/scenarios.yaml").read_text())
    rows = {}
    for s in man["scenarios"]:
        if not s["is_fault"]:
            continue
        d = pd.read_parquet(REPO / f"data/processed/{system}/{s['file']}.parquet")
        score = {z: float((d.loc[occ, f"RM_TEMP_{z}"] - h.loc[occ, f"RM_TEMP_{z}"]).abs().mean() + (d.loc[occ, f"VAV_DMPR_{z}"] - h.loc[occ, f"VAV_DMPR_{z}"]).abs().mean() * 10
                          + abs(d.loc[occ, f"RH_GPM_{z}"].mean() - h.loc[occ, f"RH_GPM_{z}"].mean())) for z in "IWSE"}
        top = max(score, key=score.get)
        rows[s["file"]] = {"zone_movement_score": {z: round(v, 3) for z, v in score.items()}, "moving_zone": top if score[top] > 2 * sorted(score.values())[-2] + 1e-9 else "indeterminate"}
    zones = [r["moving_zone"] for r in rows.values()]
    out["systems"][system] = {"files": rows, "count": {z: zones.count(z) for z in set(zones)}}
    print(system, out["systems"][system]["count"])
(REPO / "outputs/e7_zone_label.json").write_text(json.dumps(out, indent=2) + "\n")
