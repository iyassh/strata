"""Week-0 gate battery for any raw LBNL-style system directory (X17+).

Generic form of the six gates scripts/02_week0_audit.py runs on the three
original systems, for onboarding a new one: (1) MD5 over every raw CSV with
duplicate groups; (2) within-file timestamp monotonicity, counting wrap
points; (3) calendar identity of every file's timestamp set against the
fault-free file; (4) raw-file rotation (set-identical but non-monotonic);
(5) Brick/TTL coverage: declared points vs. the CSV columns, by name;
(6) healthy silence is the separate scripts/03_healthy_silence.py.

    uv run python scripts/gates_system.py <system> <raw_dir> <healthy_stem> [ttl]
        -> outputs/week0_audit_<system>.json
"""
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

system, raw_dir, healthy = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
ttl = Path(sys.argv[4]) if len(sys.argv) > 4 else None
csvs = sorted(raw_dir.glob("*.csv"))
out = {"system": system, "raw_dir": str(raw_dir), "n_files": len(csvs)}

# G1 md5
by_hash = defaultdict(list); hashes = {}
for c in csvs:
    h = hashlib.md5(c.read_bytes()).hexdigest(); hashes[c.name] = h; by_hash[h].append(c.name)
out["G1_md5"] = {"hashes": hashes, "duplicate_groups": [v for v in by_hash.values() if len(v) > 1]}
print(f"G1 md5: {len(csvs)} files, {len(by_hash)} distinct, duplicate groups {out['G1_md5']['duplicate_groups'] or 'none'}", flush=True)

# G2-G4 monotonicity, calendar identity, rotation — on the raw Datetime column
def stamps(c: Path) -> pd.Series:
    return pd.to_datetime(pd.read_csv(c, usecols=["Datetime"])["Datetime"])
ref = stamps(next(c for c in csvs if c.stem.rstrip("_") == healthy))
ref_set = set(ref)
mono, cal, rot = {}, {}, {}
for c in csvs:
    s = stamps(c)
    wraps = int((s.diff().dropna() < pd.Timedelta(0)).sum())
    mono[c.name] = {"wrap_points": wraps, "first": str(s.iloc[0]), "last": str(s.iloc[-1]), "rows": int(len(s))}
    cal[c.name] = {"set_identical_to_healthy": set(s) == ref_set, "n_unique": int(s.nunique())}
    rot[c.name] = bool(cal[c.name]["set_identical_to_healthy"] and wraps > 0)
out["G2_monotonic"] = mono; out["G3_calendar"] = cal; out["G4_raw_rotation"] = {k: v for k, v in rot.items() if v}
print(f"G2 monotonic: non-monotonic files {[k for k, v in mono.items() if v['wrap_points']] or 'none'}", flush=True)
print(f"G3 calendar identity vs {healthy}: mismatches {[k for k, v in cal.items() if not v['set_identical_to_healthy']] or 'none'}", flush=True)
print(f"G4 rotation: {list(out['G4_raw_rotation']) or 'none'}", flush=True)

# G5 TTL coverage
if ttl and ttl.exists():
    cols = set(pd.read_csv(csvs[0], nrows=1).columns) - {"Datetime"}
    txt = ttl.read_text()
    declared = set(re.findall(r"bldg:([A-Za-z0-9_%]+)", txt)) | set(re.findall(r":([A-Z][A-Za-z0-9_]+)\s+a\s+brick:", txt))
    declared = {d for d in declared if d not in {"DDAHU", "AHU"}}
    out["G5_ttl"] = {"columns": len(cols), "declared_points": len(declared),
                     "columns_not_declared": sorted(cols - declared)[:40], "declared_not_in_columns": sorted(declared - cols)[:40]}
    print(f"G5 ttl: {len(cols)} columns, {len(declared)} declared; not declared {len(cols - declared)}; declared-not-column {len(declared - cols)}", flush=True)
Path(f"outputs/week0_audit_{system}.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"wrote outputs/week0_audit_{system}.json")
