"""One-time conversion of the LBNL simulated RTU CSVs to Parquet (X29).

Usage: uv run python scripts/08_convert_rtu_sim.py [src_dir]
src_dir defaults to $STRATA_RTU_RAW/"Simulated RTU". The ONLY preprocessing
beyond type parsing is a derived column OPERATE = 1 on every row: the unit has
no schedule and its supply fan runs continuously (documentation S1.2) — and,
since X29 Amendment 1, dropping any calendar date with fewer than 720 rows
(the record ends with one row stamped 2018-10-28 00:00; a one-minute "day").
"""
import os
import sys
from pathlib import Path

import pandas as pd

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else Path(os.environ.get("STRATA_RTU_RAW", "data/raw/LBNL_FDD_Data_Sets_RTU_all_3")) / "Simulated RTU")
DST = Path("data/processed/rtu_sim")
DST.mkdir(parents=True, exist_ok=True)

for csv in sorted(SRC.glob("*.csv")):
    out = DST / (csv.stem + ".parquet")
    if out.exists():
        print(f"skip  {csv.name}", flush=True); continue
    df = pd.read_csv(csv)
    df["Datetime"] = pd.to_datetime(df["Datetime"])
    df = df.sort_values("Datetime").drop_duplicates("Datetime").reset_index(drop=True)
    rows_per_date = df.groupby(df["Datetime"].dt.date)["Datetime"].transform("size")
    dropped = sorted(set(df.loc[rows_per_date < 720, "Datetime"].dt.date))
    df = df[rows_per_date >= 720].reset_index(drop=True)
    if dropped:
        print(f"      {csv.name}: dropped partial date(s) {[str(d) for d in dropped]}", flush=True)
    df["OPERATE"] = 1
    df.to_parquet(out, compression="snappy")
    print(f"wrote {out.name:34s} {df.shape[0]:>7,} rows x {df.shape[1]} cols", flush=True)
print("done")
