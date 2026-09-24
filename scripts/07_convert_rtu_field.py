"""One-time conversion of the LBNL field RTU CSVs (Site 1, Site 2) to Parquet (X26).

Usage: uv run python scripts/07_convert_rtu_field.py [src_dir]
src_dir defaults to $STRATA_RTU_RAW/"Field RTU". The ONLY preprocessing beyond
type parsing is a derived column FAN_ON = (RTU_SA_FAN_WATT > 100), because the
unit has no schedule point; it is mapped to OCCUPIED in sensors.yaml and
documented in the X26 pre-registration.
"""
import os
import sys
from pathlib import Path

import pandas as pd

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else Path(os.environ.get("STRATA_RTU_RAW", "data/raw/LBNL_FDD_Data_Sets_RTU_all_3")) / "Field RTU")
DST = Path("data/processed/rtu_field")
DST.mkdir(parents=True, exist_ok=True)
FAN_ON_W = 100.0


def main() -> None:
    csvs = sorted(SRC.glob("*.csv"))
    if not csvs:
        sys.exit(f"ERROR: no CSVs under {SRC}")
    for csv in csvs:
        out = DST / (csv.stem + ".parquet")
        if out.exists():
            print(f"skip  {csv.name}", flush=True); continue
        df = pd.read_csv(csv)
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        df = df.sort_values("Datetime").drop_duplicates("Datetime").reset_index(drop=True)
        df["FAN_ON"] = (df["RTU_SA_FAN_WATT"] > FAN_ON_W).astype(int)
        df.to_parquet(out, compression="snappy")
        print(f"wrote {out.name:36s} {df.shape[0]:>7,} rows x {df.shape[1]} cols  fan-on {df['FAN_ON'].mean():.3f}", flush=True)
    print("done")


if __name__ == "__main__":
    main()
