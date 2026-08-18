"""Phase 7 (gap S11) — definitive sensor-coverage table as an artifact.

Usage: uv run python scripts/sensor_coverage.py

For each system: which raw columns the configs map (and therefore which
physics STRATA can see) vs which columns exist in the data and were never
used. This list is honesty ammunition, not embarrassment: it is what makes
"PCA detected SFPU airside fouling via a zone-fan pressure sensor we never
mapped" a documented measurement instead of an excuse, and it prices the
headroom left in each dataset. Writes outputs/sensor_coverage.json.
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from processheal.io.config import load_config  # noqa: E402

HEALTHY = {"sdahu": "AHU_annual", "pfpu": "PFPU_FaultFree", "sfpu": "SFPU_FaultFree"}

out = {}
for system, healthy in HEALTHY.items():
    cfg = load_config(f"configs/lbnl_{system}")
    pq = Path(f"data/processed/{system}/{healthy}.parquet")
    cols = set(pd.read_parquet(pq).columns) - {"Datetime"}
    mapped_raw = set(cfg.sensors.values()) - {"Datetime"}
    unmapped = sorted(cols - mapped_raw)
    ghost = sorted(mapped_raw - cols)  # mapped in config but absent in data
    out[system] = {
        "data_columns": len(cols),
        "mapped": len(mapped_raw & cols),
        "unmapped": unmapped,
        "mapped_but_absent_in_data": ghost,
    }
    print(f"[{system}] columns {len(cols)} | mapped {len(mapped_raw & cols)} | "
          f"unmapped {len(unmapped)} | ghost-mappings {len(ghost)}")
    if ghost:
        print(f"  GHOST (config maps a column the data lacks): {ghost}")

Path("outputs/sensor_coverage.json").write_text(json.dumps(out, indent=1))
print("wrote outputs/sensor_coverage.json")
