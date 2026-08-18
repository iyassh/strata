"""One-time conversion of LBNL PFPU/SFPU CSVs to Parquet.

FPU datetime format differs from SDAHU (MM/DD/YYYY HH:MM vs ISO) — parsed
explicitly so no row is silently misread (dataset-audit quirk #8).

Usage: uv run python scripts/01_convert_fpu.py [root_dir]
root_dir defaults to $STRATA_FPU_RAW (must contain
LBNL_FDD_Data_Sets_PFPU/ and LBNL_FDD_Data_Sets_SFPU/; see REPRODUCING.md).
"""

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("STRATA_FPU_RAW",
                        "/Users/yassh/Downloads/Ureap/LBNL_FDD_Data_Sets_FPU_all_3")
)
SYSTEMS = {
    "pfpu": ROOT / "LBNL_FDD_Data_Sets_PFPU",
    "sfpu": ROOT / "LBNL_FDD_Data_Sets_SFPU",
}


def main() -> None:
    for system, src in SYSTEMS.items():
        dst = Path(f"data/processed/{system}")
        dst.mkdir(parents=True, exist_ok=True)
        csvs = sorted(src.glob("*.csv"))
        if not csvs:
            sys.exit(f"ERROR: no CSVs found under {src} — set STRATA_FPU_RAW or "
                     f"pass the root directory as the first argument (REPRODUCING.md §3)")
        print(f"[{system}] converting {len(csvs)} CSVs from {src}")
        for csv in csvs:
            out = dst / (csv.stem + ".parquet")
            if out.exists():
                print(f"  skip  {csv.name}")
                continue
            df = pd.read_csv(csv)
            df["Datetime"] = pd.to_datetime(df["Datetime"], format="%m/%d/%Y %H:%M")
            # one raw file ships date-rotated (SFPU_SensorBias_RMTEMP_-2C
            # starts at Jan 3 and wraps) — sort so downstream positional
            # comparisons are never misaligned
            df = df.sort_values("Datetime").reset_index(drop=True)
            assert df["Datetime"].is_monotonic_increasing
            df.to_parquet(out, compression="snappy")
            print(f"  wrote {out.name:52s} {df.shape[0]:>7,} rows x {df.shape[1]} cols")
    print("done")


if __name__ == "__main__":
    main()
