"""X19 diagnostic (after scoring; no threshold touched): why waterside fouling
is missed on the fan coil unit. Quantities, with their exact definitions:
  dT_daily_median : median over days of the chwc_waterside_dT residual channel's
                    daily score (EWT - LWT, gated as the channel is gated:
                    CHWC_VLV_POS > 0.10, CHWC_FLOW > 0.05, OCCUPIED > 0.5)
  valve_open_min  : minutes with FCU_CTRL == 1 and CHWC_VLV_POS > 0.10
  flow_gpm_open   : mean CHWC_FLOW over those minutes
    uv run python scripts/x19_waterside_diagnostic.py -> outputs/x19_waterside_diagnostic.json
"""
import json
from pathlib import Path

import pandas as pd

from strata.core.residuals import daily_residual_scores
from strata.io.config import load_config

cfg = load_config("configs/lbnl_fcu")
FILES = ["FCU_FaultFree", "FCU_Fouling_Cooling_Waterside_Minor", "FCU_Fouling_Cooling_Waterside_Moderate",
         "FCU_Fouling_Cooling_Waterside_Severe", "FCU_Fouling_Heating_Waterside_Minor",
         "FCU_Fouling_Heating_Waterside_Moderate", "FCU_Fouling_Heating_Waterside_Severe"]
out = {}
for f in FILES:
    df = pd.read_parquet(f"data/processed/fcu/{f}.parquet")
    coil = "hwc" if "Heating" in f else "chwc"
    pos, flow = ("FCU_HVLV", "FCU_HTG_GPM") if coil == "hwc" else ("FCU_CVLV", "FCU_CLG_GPM")
    s = daily_residual_scores(df, cfg, f"{coil}_waterside_dT")["score"].dropna()
    m = (df["FCU_CTRL"] == 1) & (df[pos] > 0.10)
    out[f] = {"channel": f"{coil}_waterside_dT", "evaluable_days": int(len(s)),
              "dT_daily_median_F": round(float(s.median()), 2),
              "valve_open_min": int(m.sum()), "flow_gpm_open": round(float(df.loc[m, flow].mean()), 3)}
    print(f"{f:42s} {out[f]}")
h = out["FCU_FaultFree"]
for coil in ("chwc", "hwc"):
    hh = {"chwc": None, "hwc": None}
# healthy reference for each coil
ref = {}
for coil, pos, flow in (("chwc", "FCU_CVLV", "FCU_CLG_GPM"), ("hwc", "FCU_HVLV", "FCU_HTG_GPM")):
    df = pd.read_parquet("data/processed/fcu/FCU_FaultFree.parquet")
    s = daily_residual_scores(df, cfg, f"{coil}_waterside_dT")["score"].dropna()
    m = (df["FCU_CTRL"] == 1) & (df[pos] > 0.10)
    ref[coil] = {"dT_daily_median_F": round(float(s.median()), 2), "valve_open_min": int(m.sum()),
                 "flow_gpm_open": round(float(df.loc[m, flow].mean()), 3)}
out["healthy_reference_by_coil"] = ref
for f in FILES[1:]:
    r = ref[out[f]["channel"].split("_")[0]]
    out[f]["flow_rel_diff_pct"] = round(100 * (out[f]["flow_gpm_open"] - r["flow_gpm_open"]) / r["flow_gpm_open"], 1)
    out[f]["valve_open_rel_diff_pct"] = round(100 * (out[f]["valve_open_min"] - r["valve_open_min"]) / r["valve_open_min"], 2)
Path("outputs/x19_waterside_diagnostic.json").write_text(json.dumps(out, indent=2) + "\n")
print("wrote outputs/x19_waterside_diagnostic.json")
