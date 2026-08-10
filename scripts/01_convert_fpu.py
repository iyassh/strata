"""One-time conversion of LBNL PFPU/SFPU CSVs to Parquet.

FPU datetime format differs from SDAHU (MM/DD/YYYY HH:MM vs ISO) — parsed
explicitly so no row is silently misread (dataset-audit quirk #8).
"""

from pathlib import Path

import pandas as pd

ROOT = Path("/Users/yassh/Downloads/Ureap/LBNL_FDD_Data_Sets_FPU_all_3")
SYSTEMS = {
    "pfpu": ROOT / "LBNL_FDD_Data_Sets_PFPU",
    "sfpu": ROOT / "LBNL_FDD_Data_Sets_SFPU",
}


def main() -> None:
    for system, src in SYSTEMS.items():
        dst = Path(f"data/processed/{system}")
        dst.mkdir(parents=True, exist_ok=True)
        csvs = sorted(src.glob("*.csv"))
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
