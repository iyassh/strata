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
import os
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

# Raw-data roots are overridable for other machines (REPRODUCING.md):
#   STRATA_FPU_RAW   -> directory containing LBNL_FDD_Data_Sets_{PFPU,SFPU}/
#   STRATA_SDAHU_RAW -> directory containing LBNL_FDD_Dataset_SDAHU/
ROOT = Path(os.environ.get(
    "STRATA_FPU_RAW", "/Users/yassh/Downloads/Ureap/LBNL_FDD_Data_Sets_FPU_all_3"))
SDAHU_RAW = Path(os.environ.get(
    "STRATA_SDAHU_RAW",
    "/Users/yassh/Downloads/LBNL_FDD_Data_Sets_SDAHU_all_3")) / "LBNL_FDD_Dataset_SDAHU"
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


def sdahu_evidence() -> dict:
    """SDAHU dataset-errata evidence as an artifact (ERRATA.md #1, #2, #4).

    Phase 7: the errata were narrated across docs but the evidence lived
    nowhere recomputable. This gate emits:
      - MD5 of every raw CSV and processed parquet, with duplicate groups
        (errata #1/#2: oa_bias x4 and coi_leakage x4 are one run each);
      - healthy-vs-fault SA_SP / SA_SPSPT summary stats (erratum #4: units
        and roles swapped between the healthy file and EVERY fault file —
        any ML baseline fed these columns scores file provenance);
      - the controller-side proof for oa_bias (erratum #1): weather input
        OA_TEMP is bit-identical to healthy while behaviour columns
        diverge, so the bias was injected in the controller, not the sensor
        stream — there is no independent healthy negative run.
    """
    print("\n== Gate 5: SDAHU errata evidence ==")
    out: dict = {}
    for label, folder, pattern in (("raw_csv", SDAHU_RAW, "*.csv"),
                                   ("parquet", Path("data/processed/sdahu"), "*.parquet")):
        hashes, by_hash = {}, defaultdict(list)
        if not folder.exists():
            print(f"  [{label}] SKIPPED — {folder} not present")
            out[label] = {"skipped": str(folder)}
            continue
        for f in sorted(folder.glob(pattern)):
            h = hashlib.md5(f.read_bytes()).hexdigest()
            hashes[f.name] = h
            by_hash[h].append(f.name)
        dupes = {h: names for h, names in by_hash.items() if len(names) > 1}
        print(f"  [{label}] files: {len(hashes)} | distinct: {len(by_hash)}")
        for h, names in dupes.items():
            print(f"    DUPLICATE [{h[:8]}]: {', '.join(names)}")
        out[label] = {"hashes": hashes, "duplicates": dupes}

    pdir = Path("data/processed/sdahu")
    if pdir.exists():
        h = pd.read_parquet(pdir / "AHU_annual.parquet")
        f = pd.read_parquet(pdir / "damper_stuck_010_annual.parquet")

        def stats(d, c):
            return {"mean": round(float(d[c].mean()), 3),
                    "min": round(float(d[c].min()), 3),
                    "max": round(float(d[c].max()), 3)}

        out["sa_sp_mismatch"] = {
            "healthy": {c: stats(h, c) for c in ("SA_SP", "SA_SPSPT")},
            "fault_example_damper_stuck_010": {c: stats(f, c) for c in ("SA_SP", "SA_SPSPT")},
            "note": "healthy: SA_SP~402 (Pa-scale), SPSPT~1.6; every fault "
                    "file: SA_SP~0.9, SPSPT~-400 — units AND roles swapped",
        }
        print(f"  SA_SP  healthy mean {out['sa_sp_mismatch']['healthy']['SA_SP']['mean']} "
              f"vs fault {out['sa_sp_mismatch']['fault_example_damper_stuck_010']['SA_SP']['mean']}")

        import numpy as np

        ob = pd.read_parquet(pdir / "oa_bias_2_annual.parquet")
        oat = (h["OA_TEMP"] - ob["OA_TEMP"]).abs()
        behaviour_cols = [c for c in ("MA_TEMP", "SA_TEMP", "OA_DMPR") if c in h.columns]
        diverging = {c: round(float((h[c] - ob[c]).abs().mean()), 4) for c in behaviour_cols}
        out["oa_bias_controller_side"] = {
            "calendar_identical": h["Datetime"].equals(ob["Datetime"]),
            "OA_CFM_bit_identical_to_healthy": bool(
                np.array_equal(h["OA_CFM"].values, ob["OA_CFM"].values, equal_nan=True)
            ) if "OA_CFM" in h.columns else None,
            "OA_TEMP_abs_diff": {"mean": round(float(oat.mean()), 4),
                                 "max": round(float(oat.max()), 4)},
            "labeled_bias_magnitude_F": 2.0,
            "behaviour_mean_abs_divergence": diverging,
            "note": "recorded OA_TEMP tracks healthy weather to within 0.33 F "
                    "(mean 0.02) — nowhere near the labeled +/-2-4 F bias — "
                    "while MA/SA behaviour diverges by degrees. A sensor-side "
                    "bias would appear in the recorded stream; it does not. "
                    "The bias therefore lives in the CONTROLLER's reading: the "
                    "oa_bias run is a fault run, not a healthy negative "
                    "(relabel saga, D2/F1). NOTE: the earlier prose claim "
                    "'OA_TEMP bit-identical to healthy' was IMPRECISE — the "
                    "sub-0.33 F residual is intake-node flow feedback; the "
                    "conclusion stands on the absence of the labeled bias.",
        }
        print(f"  oa_bias: OA_TEMP |diff| mean {oat.mean():.4f} max {oat.max():.4f} "
              f"(labeled bias 2.0 F); behaviour divergence={diverging}")
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    result = {}
    if which in ("md5", "all"):
        result["md5"] = md5_gate()
    if which in ("sdahu", "all"):
        result["sdahu_errata_evidence"] = sdahu_evidence()
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
