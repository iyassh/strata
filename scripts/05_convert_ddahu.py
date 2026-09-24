"""One-time conversion of LBNL DDAHU CSVs to Parquet (X17 onboarding).

Usage: uv run python scripts/05_convert_ddahu.py [src_dir]
src_dir defaults to $STRATA_DDAHU_RAW/LBNL_FDD_Dataset_DDAHU. Same shape as
scripts/00_convert_to_parquet.py; the only differences are the folder and
the timestamp format (MM/DD/YYYY HH:MM).
"""
import os
import sys
from pathlib import Path

import pandas as pd

SRC = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else Path(os.environ.get("STRATA_DDAHU_RAW",
                             "data/raw/LBNL_FDD_Data_Sets_DDAHU_all_3"))
    / "LBNL_FDD_Dataset_DDAHU"
)
DST = Path("data/processed/ddahu")
DST.mkdir(parents=True, exist_ok=True)


def main() -> None:
    csvs = sorted(SRC.glob("*.csv"))
    if not csvs:
        sys.exit(f"ERROR: no CSVs found under {SRC} — set STRATA_DDAHU_RAW or pass the source directory")
    print(f"Converting {len(csvs)} CSV files from {SRC}", flush=True)
    for csv in csvs:
        out = DST / (csv.stem.rstrip("_") + ".parquet")
        if out.exists():
            print(f"skip  {csv.name}", flush=True)
            continue
        df = pd.read_csv(csv)
        df["Datetime"] = pd.to_datetime(df["Datetime"], format="%m/%d/%Y %H:%M")
        df.to_parquet(out, compression="snappy")
        print(f"wrote {out.name:48s} {df.shape[0]:>7,} rows x {df.shape[1]} cols", flush=True)
    print("done")


if __name__ == "__main__":
    main()
