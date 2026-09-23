"""ERRATA E5, schedule leg, as a measurement, not an assertion.

ERRATA E5 states that on the pipeline's own occupancy signal (SYS_CTL,
configs/lbnl_sdahu/sensors.yaml OCCUPIED) the healthy SDAHU file and every
fault file share the same 303 occupied days, and that the branch difference
is a one-hour phase shift: the healthy file's first occupied minute is
05:01-05:02 on 200 of those days, every fault file's is 06:01. Until this
script existed that sentence lived only in prose. It now records, per file,
the occupied-day count and the distribution of the first occupied minute.

    uv run python scripts/e5_schedule.py   -> outputs/e5_schedule.json
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "processed" / "sdahu"
healthy = "AHU_annual"

per_file = {}
for p in sorted(D.glob("*.parquet")):
    df = pd.read_parquet(p, columns=["Datetime", "SYS_CTL"])
    occ = df[df["SYS_CTL"] > 0.5]
    ts = pd.to_datetime(occ["Datetime"])
    first = ts.groupby(ts.dt.date).min().dt.strftime("%H:%M")
    counts = first.value_counts().sort_index()
    per_file[p.stem] = {"occupied_days": int(len(first)),
                        "first_occupied_minute": {k: int(v) for k, v in counts.items()}}

h = per_file[healthy]["first_occupied_minute"]
early = sum(v for k, v in h.items() if k in ("05:01", "05:02"))
faults = {k: v for k, v in per_file.items() if k != healthy}
all_0601 = all(set(v["first_occupied_minute"]) == {"06:01"} for v in faults.values())
res = {
    "occupancy_signal": "SYS_CTL > 0.5 (configs/lbnl_sdahu/sensors.yaml OCCUPIED)",
    "healthy_file": healthy,
    "healthy_occupied_days": per_file[healthy]["occupied_days"],
    "healthy_days_starting_0501_0502": early,
    "fault_files_all_start_0601": all_0601,
    "fault_occupied_days": {k: v["occupied_days"] for k, v in faults.items()},
    "per_file": per_file,
    "note": "Occupied-day universe is 303 on every full-year file; the one short "
            "file (damper_stuck_100_annual_short) has 179. The branch difference is "
            "the first occupied minute: 05:01/05:02 on the healthy file for "
            f"{early} of {per_file[healthy]['occupied_days']} days (06:02 otherwise), 06:01 on "
            "every day of every fault file.",
}
(ROOT / "outputs" / "e5_schedule.json").write_text(json.dumps(res, indent=2) + "\n")
print(f"healthy: {res['healthy_occupied_days']} occupied days, {early} start 05:01/05:02, "
      f"dist {h}; faults all 06:01: {all_0601}; fault day counts "
      f"{sorted(set(res['fault_occupied_days'].values()))}")
