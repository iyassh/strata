"""Week-0 FPU data audit (pre-registered in the implementation plan).

Three gates, all BEFORE any design decision touches FPU data:
1. MD5 every raw CSV — the SDAHU lesson (byte-identical fault files shipped
   under different names; oa_bias relabel saga) makes this non-negotiable.
2. Per-scenario zone-column diff vs FaultFree -> WHICH zones each fault
   actually touches = the localization ground truth for E3. (Fault file
   names do not carry the zone; the data must say.)
3. TTL-vs-CSV point-name coverage — every Brick point must exist as a CSV
   column and vice versa, or localization silently breaks.

Run AFTER 01_convert_fpu.py (parts 2-3 read parquet). Part 1 reads raw CSVs.
Usage: uv run python scripts/02_week0_audit.py [md5|zones|ttl|all]
"""

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/yassh/Downloads/Ureap/LBNL_FDD_Data_Sets_FPU_all_3")
RAW = {
    "pfpu": ROOT / "LBNL_FDD_Data_Sets_PFPU",
    "sfpu": ROOT / "LBNL_FDD_Data_Sets_SFPU",
}
TTL = {
    "pfpu": ROOT / "LBNL_FDD_Data_Sets_PFPU_ttl.ttl",
    "sfpu": ROOT / "LBNL_FDD_Data_Sets_SFPU_ttl.ttl",
}
PROCESSED = {s: Path(f"data/processed/{s}") for s in RAW}
ZONES = ["I", "W", "S", "E"]
OUT = Path("outputs/week0_audit.json")


def md5_gate() -> dict:
    print("== Gate 1: MD5 all raw CSVs ==")
    hashes: dict[str, str] = {}
    by_hash = defaultdict(list)
    for system, src in RAW.items():
        for csv in sorted(src.glob("*.csv")):
            h = hashlib.md5(csv.read_bytes()).hexdigest()
            hashes[csv.name] = h
            by_hash[h].append(csv.name)
    dupes = {h: names for h, names in by_hash.items() if len(names) > 1}
    print(f"  files: {len(hashes)} | distinct contents: {len(by_hash)}")
    if dupes:
        for h, names in dupes.items():
            print(f"  DUPLICATE [{h[:8]}]: {', '.join(names)}")
    else:
        print("  no byte-identical duplicates — all 62 scenarios are distinct data")
    return {"hashes": hashes, "duplicates": dupes}


def zone_ground_truth() -> dict:
    """Which zone columns differ from FaultFree, per scenario (E3 ground truth).

    A column 'differs' if >0.5% of its samples deviate by more than a tiny
    absolute tolerance — loose enough to ignore solver noise, strict enough
    to catch any real behavioural change.
    """
    print("\n== Gate 2: per-scenario zone-diff ground truth ==")
    truth: dict[str, dict] = {}
    for system, pdir in PROCESSED.items():
        base = pd.read_parquet(pdir / f"{system.upper()}_FaultFree.parquet")
        zone_cols = {z: [c for c in base.columns if c.endswith(f"_{z}")] for z in ZONES}
        ahu_cols = [c for c in base.columns
                    if c != "Datetime" and not any(c.endswith(f"_{z}") for z in ZONES)]
        for pq in sorted(pdir.glob("*.parquet")):
            if pq.stem == f"{system.upper()}_FaultFree":
                continue
            df = pd.read_parquet(pq)
            n = min(len(df), len(base))
            rec = {}
            for z, cols in zone_cols.items():
                frac = max(
                    float(((df[c].iloc[:n].values - base[c].iloc[:n].values) ** 2 > 1e-6).mean())
                    for c in cols
                )
                rec[z] = round(frac, 4)
            ahu_frac = max(
                float(((df[c].iloc[:n].values - base[c].iloc[:n].values) ** 2 > 1e-6).mean())
                for c in ahu_cols
            )
            affected = [z for z, f in rec.items() if f > 0.005]
            truth[pq.stem] = {"zone_diff_frac": rec, "ahu_diff_frac": round(ahu_frac, 4),
                              "affected_zones": affected}
            print(f"  {pq.stem:52s} zones {affected or ['-none-']} ahu {ahu_frac:.3f}")
    return truth


def ttl_coverage() -> dict:
    print("\n== Gate 3: TTL-vs-CSV point coverage ==")
    import rdflib
    report = {}
    for system, ttl_path in TTL.items():
        g = rdflib.Graph()
        g.parse(ttl_path, format="turtle")
        points = {str(o).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
                  for _, p, o in g if str(p).endswith("hasPoint")}
        cols = set(pd.read_parquet(
            PROCESSED[system] / f"{system.upper()}_FaultFree.parquet"
        ).columns) - {"Datetime"}
        ttl_not_csv = sorted(points - cols)
        csv_not_ttl = sorted(cols - points)
        print(f"  [{system}] TTL points: {len(points)} | CSV cols: {len(cols)} | "
          f"TTL-not-in-CSV: {len(ttl_not_csv)} | CSV-not-in-TTL: {len(csv_not_ttl)}")
        if ttl_not_csv:
            print(f"    TTL-only: {ttl_not_csv[:8]}{' ...' if len(ttl_not_csv) > 8 else ''}")
        if csv_not_ttl:
            print(f"    CSV-only: {csv_not_ttl[:8]}{' ...' if len(csv_not_ttl) > 8 else ''}")
        report[system] = {"ttl_points": len(points), "csv_cols": len(cols),
                          "ttl_not_csv": ttl_not_csv, "csv_not_ttl": csv_not_ttl}
    return report


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    result = {}
    if which in ("md5", "all"):
        result["md5"] = md5_gate()
    if which in ("zones", "all"):
        result["zone_ground_truth"] = zone_ground_truth()
    if which in ("ttl", "all"):
        result["ttl_coverage"] = ttl_coverage()
    OUT.parent.mkdir(exist_ok=True)
    existing = json.loads(OUT.read_text()) if OUT.exists() else {}
    existing.update(result)
    OUT.write_text(json.dumps(existing, indent=2))
    print(f"\nwrote {OUT}")
