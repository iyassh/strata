"""ERRATA E8 evidence — the recorded shift under the dual-duct hot-deck sensor-bias labels.
    uv run python scripts/e8_bias_magnitude.py -> outputs/e8_bias_magnitude.json
"""
import json
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
m = yaml.safe_load((REPO / "configs/lbnl_ddahu/sensors.yaml").read_text())["canonical_to_csv"]
h = pd.read_parquet(REPO / "data/processed/ddahu/DualDuct_FaultFree.parquet")
on = (h[m["OCCUPIED"]] > 0.5) & (h[m["HSF_STATUS"]] > 0.5)
out = {}
for f, label, deck, boxes in [("DualDuct_SensorBias_HSP_-2inwg", "-2 in.wg", "HSA_SP", ["VAV_SP_H_W", "VAV_SP_H_SB", "VAV_SP_H_SA", "VAV_SP_H_E"]),
                              ("DualDuct_SensorBias_HSP_-4inwg", "-4 in.wg", "HSA_SP", ["VAV_SP_H_W", "VAV_SP_H_SB", "VAV_SP_H_SA", "VAV_SP_H_E"]),
                              ("DualDuct_SensorBias_HSA_+2C", "+2 C (3.6 F)", "HSA_TEMP", ["VAV_EAT_H_W", "VAV_EAT_H_SB", "VAV_EAT_H_SA", "VAV_EAT_H_E"]),
                              ("DualDuct_SensorBias_CSP_-2inwg", "-2 in.wg", "CSA_SP", ["VAV_SP_C_W", "VAV_SP_C_SB", "VAV_SP_C_SA", "VAV_SP_C_E"])]:
    d = pd.read_parquet(REPO / f"data/processed/ddahu/{f}.parquet")
    out[f] = {"label": label, "deck_column_median_shift": round(float((d.loc[on, deck] - h.loc[on, deck]).median()), 4),
              "box_columns_median_shift": {b: round(float((d.loc[on, b] - h.loc[on, b]).median()), 4) for b in boxes},
              "minutes": int(on.sum())}
    print(f, out[f]["deck_column_median_shift"], out[f]["box_columns_median_shift"])
(REPO / "outputs/e8_bias_magnitude.json").write_text(json.dumps(out, indent=2) + "\n")
