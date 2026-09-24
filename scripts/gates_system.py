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
ttl = Path(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else None
ONLY_G6 = "--only-g6" in sys.argv          # recompute the branch block on top of the committed G1-G5
csvs = sorted(raw_dir.glob("*.csv"))
out = json.loads(Path(f"outputs/week0_audit_{system}.json").read_text()) if ONLY_G6 else {"system": system, "raw_dir": str(raw_dir), "n_files": len(csvs)}

# G1 md5
by_hash = defaultdict(list); hashes = {}
if ONLY_G6:
    csvs_g1 = []
else:
    csvs_g1 = csvs
for c in csvs_g1:
    h = hashlib.md5(c.read_bytes()).hexdigest(); hashes[c.name] = h; by_hash[h].append(c.name)
if not ONLY_G6:
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
# G6 configuration-branch comparison (the E5 class): per file, the occupied-day
# universe, the modal first-occupied minute, the outdoor-air damper floor while
# the supply fan runs, and every setpoint column's constant value. The healthy
# file must sit inside the fault files' cluster on every axis.
import yaml
sens = yaml.safe_load(Path(f"configs/lbnl_{system}/sensors.yaml").read_text())["canonical_to_csv"]
occ_col = sens.get("OCCUPIED"); dmpr = sens.get("OA_DMPR_POS")
fan_cols = [v for k, v in sens.items() if "STATUS" in k or k in ("SF_CS",)]
def branch_profile(c: Path) -> dict:
    hdr = pd.read_csv(c, nrows=1).columns
    sp_cols = [x for x in hdr if "SPT" in x.upper() or x.upper().endswith("_SP")]
    cols = ["Datetime"] + [x for x in [occ_col, dmpr] + fan_cols + sp_cols if x in hdr]
    d = pd.read_csv(c, usecols=cols); ts = pd.to_datetime(d["Datetime"])
    prof = {}
    if occ_col in d:
        occ = d[occ_col] == 1
        first = ts[occ].groupby(ts[occ].dt.date).min()
        prof["occupied_days"] = int(occ.groupby(ts.dt.date).any().sum())
        prof["first_occupied_minute_mode"] = (first.dt.hour * 60 + first.dt.minute).mode().iloc[0].item() if len(first) else None
    if dmpr in d and fan_cols and fan_cols[0] in d:
        on = d[fan_cols[0]] > 0.5
        prof["oa_damper_floor_fan_on"] = round(float(d.loc[on, dmpr].min()), 4) if on.any() else None
    # only true setpoint columns (name contains SPT); measured statics like CSA_SP are not setpoints
    prof["setpoint_constants"] = {x: (round(float(d[x].iloc[0]), 3) if d[x].nunique() == 1 else f"varies({d[x].nunique()})")
                                  for x in sp_cols if x in d and "SPT" in x.upper()}
    return prof
profiles = {c.name: branch_profile(c) for c in csvs}
ref_name = next(c.name for c in csvs if c.stem.rstrip("_") == healthy)
hp = profiles[ref_name]; faults = {k: v for k, v in profiles.items() if k != ref_name}
def inside(key):
    vals = [v[key] for v in faults.values() if v.get(key) is not None]
    return (min(vals) <= hp[key] <= max(vals)) if vals and hp.get(key) is not None else None
g6 = {"healthy": hp, "healthy_inside_fault_range": {k: inside(k) for k in ("occupied_days", "first_occupied_minute_mode", "oa_damper_floor_fan_on")},
      # compare only the setpoints that are CONSTANT on the healthy file (a per-branch constant is the E5 signature)
      "healthy_constant_setpoints": {k: v for k, v in hp["setpoint_constants"].items() if not str(v).startswith("varies")},
      "setpoint_constants_identical_to_healthy": all(v["setpoint_constants"].get(k) == hv for k, hv in hp["setpoint_constants"].items()
                                                     if not str(hv).startswith("varies") for v in faults.values()),
      "files_with_different_setpoint_constants": sorted(k for k, v in faults.items() if any(v["setpoint_constants"].get(c) != hv for c, hv in hp["setpoint_constants"].items() if not str(hv).startswith("varies"))),
      "per_file": profiles}
out["G6_branch"] = g6
print(f"G6 branch: healthy {hp} | inside fault range {g6['healthy_inside_fault_range']} | setpoint constants identical {g6['setpoint_constants_identical_to_healthy']}", flush=True)
Path(f"outputs/week0_audit_{system}.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"wrote outputs/week0_audit_{system}.json")
