"""One-time conversion of LBNL SDAHU CSVs to Parquet for fast downstream loading.

Usage: uv run python scripts/00_convert_to_parquet.py [src_dir]
src_dir defaults to $STRATA_SDAHU_RAW/LBNL_FDD_Dataset_SDAHU (see
REPRODUCING.md for the dataset download source).
"""

import os
import sys
from pathlib import Path

import pandas as pd

SRC = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else Path(os.environ.get("STRATA_SDAHU_RAW",
                             "/Users/yassh/Downloads/LBNL_FDD_Data_Sets_SDAHU_all_3"))
    / "LBNL_FDD_Dataset_SDAHU"
)
DST = Path("data/processed/sdahu")
DST.mkdir(parents=True, exist_ok=True)


def main() -> None:
    csvs = sorted(SRC.glob("*.csv"))
    print(f"Converting {len(csvs)} CSV files from {SRC}")
    for csv in csvs:
        out = DST / (csv.stem + ".parquet")
        if out.exists():
            print(f"skip  {csv.name}")
            continue
        df = pd.read_csv(csv, parse_dates=["Datetime"])
        df.to_parquet(out, compression="snappy")
        print(f"wrote {out.name:42s} {df.shape[0]:>7,} rows x {df.shape[1]} cols")
    print("done")


if __name__ == "__main__":
    main()
