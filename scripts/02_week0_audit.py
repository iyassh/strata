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
    """Which zone each fault was injected in (E3 ground truth), v2.

    Pre-registered method (replaces the vacuous v1 whole-column binary diff):
    per zone, divergence = mean over that zone's own columns of
    mean(|fault - healthy|) / healthy column std (timestamp-ALIGNED, never
    positional — one raw file shipped date-rotated). The injected zone must
    lead the runner-up by >= MARGIN x; otherwise the scenario is recorded
    INDETERMINATE (scored as such in E3, never force-labeled).
    """
    MARGIN = 2.0
    print("\n== Gate 2 (v2): per-scenario zone ground truth ==")
    truth: dict[str, dict] = {}
    for system, pdir in PROCESSED.items():
        base = pd.read_parquet(pdir / f"{system.upper()}_FaultFree.parquet").set_index("Datetime")
        zone_cols = {z: [c for c in base.columns if c.endswith(f"_{z}")] for z in ZONES}
        col_std = base.std()
        for pq in sorted(pdir.glob("*.parquet")):
            if pq.stem == f"{system.upper()}_FaultFree":
                continue
            df = pd.read_parquet(pq).set_index("Datetime")
            idx = base.index.intersection(df.index)
            b, f = base.loc[idx], df.loc[idx]
            div = {}
            for z, cols in zone_cols.items():
                vals = []
                for c in cols:
                    sd = col_std[c]
                    if sd > 1e-9:
                        vals.append(float((f[c] - b[c]).abs().mean()) / float(sd))
                div[z] = round(sum(vals) / len(vals), 4)
            ranked = sorted(div.items(), key=lambda kv: -kv[1])
            (top_z, top_v), (_, second_v) = ranked[0], ranked[1]
            zone = top_z if (second_v == 0 or top_v / max(second_v, 1e-9) >= MARGIN) else "INDETERMINATE"
            truth[pq.stem] = {"zone_divergence": div, "injected_zone": zone,
                              "top_ratio": round(top_v / max(second_v, 1e-9), 2)}
            print(f"  {pq.stem:52s} -> {zone:13s} (ratio {truth[pq.stem]['top_ratio']:.1f}) {div}")
    return truth


def monotonic_gate() -> dict:
    """Every parquet must be strictly time-ordered with the FaultFree date index."""
    print("\n== Gate 4: timestamp monotonicity / calendar identity ==")
    report = {}
    for system, pdir in PROCESSED.items():
        base_idx = pd.read_parquet(pdir / f"{system.upper()}_FaultFree.parquet", columns=["Datetime"])["Datetime"]
        bad = []
        for pq in sorted(pdir.glob("*.parquet")):
            dt = pd.read_parquet(pq, columns=["Datetime"])["Datetime"]
            if not dt.is_monotonic_increasing or len(dt) != len(base_idx) or not (dt.values == base_idx.values).all():
                bad.append(pq.stem)
        print(f"  [{system}] {'ALL OK' if not bad else 'BAD: ' + ', '.join(bad)}")
        report[system] = bad
    return report


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
    if which in ("mono", "all"):
        result["monotonic"] = monotonic_gate()
    if which in ("ttl", "all"):
        result["ttl_coverage"] = ttl_coverage()
    OUT.parent.mkdir(exist_ok=True)
    existing = json.loads(OUT.read_text()) if OUT.exists() else {}
    existing.update(result)
    OUT.write_text(json.dumps(existing, indent=2))
    print(f"\nwrote {OUT}")
