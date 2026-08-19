# Reproducing every number in this repository

Every figure quoted in the PHASE*_RESULTS documents and the paper is
recomputable from the committed code plus the public LBNL datasets. This
file is the complete path from a fresh clone to regenerated artifacts.
(The committed `outputs/*.json` already contain every number — steps 3–5
regenerate them; byte-identical output is the expectation and the
regression standard for SDAHU.)

## 1. Get the data (public, CC BY 4.0)

The LBNL fault-detection datasets: Granderson, Lin et al.,
**DOI 10.25984/1881324** — "LBNL Fault Detection and Diagnostics Datasets",
hosted on OpenEI: <https://data.openei.org/submissions/5763>
(also indexed at <https://faultdetection.lbl.gov/data/>).

Download the three system archives:

| System | Archive folder expected | Contents used |
|---|---|---|
| SDAHU (single-duct AHU) | `LBNL_FDD_Data_Sets_SDAHU_all_3/LBNL_FDD_Dataset_SDAHU/` | 21 annual CSVs (1-min) |
| PFPU (parallel fan-powered unit) | `LBNL_FDD_Data_Sets_FPU_all_3/LBNL_FDD_Data_Sets_PFPU/` | 31 annual CSVs + Brick .ttl |
| SFPU (series fan-powered unit) | `LBNL_FDD_Data_Sets_FPU_all_3/LBNL_FDD_Data_Sets_SFPU/` | 31 annual CSVs + Brick .ttl |

Known dataset defects and their handling: **ERRATA.md** (E1–E5:
byte-duplicate fault files, the oa_bias mislabel, SA_SP unit swap, one
rotated calendar, and the healthy file's configuration-branch offset).
The pipeline handles or discloses all five.

## 2. Environment

```sh
uv sync          # exact pins from uv.lock; Python >= 3.12
uv run pytest -q # full suite (98 tests), ~10 s, no data needed
```

System dependency: `pm4py` visualisations need the Graphviz *binary*
(`brew install graphviz` / `apt install graphviz`); detection itself does not.

## 3. Convert raw CSVs to parquet

Point the converters at your download location (env var or first argument):

```sh
export STRATA_SDAHU_RAW=/path/to/LBNL_FDD_Data_Sets_SDAHU_all_3
export STRATA_FPU_RAW=/path/to/LBNL_FDD_Data_Sets_FPU_all_3
uv run python scripts/00_convert_to_parquet.py   # -> data/processed/sdahu/
uv run python scripts/01_convert_fpu.py          # -> data/processed/{pfpu,sfpu}/
```

`data/` is gitignored; any location works if `data/processed/<system>/`
resolves from the repo root (symlink is fine).

## 4. Gates before science (the week-0 battery)

```sh
uv run python scripts/02_week0_audit.py all        # MD5 + errata evidence + zone GT + calendar + TTL
uv run python scripts/03_healthy_silence.py configs/lbnl_pfpu data/processed/pfpu/PFPU_FaultFree.parquet
```

(The healthy-silence gate is per config; run it for any config you touch.)

## 5. The result pipeline (order matters only within a system)

```sh
for s in sdahu pfpu sfpu; do
  caffeinate -i uv run python scripts/benchmark.py $s        # scorecards -> outputs/benchmark_v6_$s.json
  caffeinate -i uv run python scripts/baselines.py $s        # iForest/PCA -> outputs/baselines_$s.json
  caffeinate -i uv run python scripts/matched_rules.py $s    # ablation arm -> outputs/matched_rules_$s.json
  uv run python scripts/stats.py $s                          # significance battery (prints; day lists in artifacts)
  caffeinate -i uv run python scripts/union_fpr.py $s        # joint FPR + demotion checks -> outputs/union_fpr_$s.json
done
caffeinate -i uv run python scripts/grammar.py               # Phase 5 -> outputs/grammar_results.json
uv run python scripts/sensor_coverage.py                     # -> outputs/sensor_coverage.json
uv run python scripts/crywolf.py                             # -> outputs/crywolf.json (artifacts only)
```

Approximate wall-clock on an Apple-silicon laptop: SDAHU minutes; PFPU/SFPU
tens of minutes each (device-stratum discovery dominates); grammar ~15 min.
Use `caffeinate -i` — a sleeping laptop silently stretches runs by hours.

## 6. Provenance notes

- `outputs/benchmark_v2_processheal_v1.json` is copied from the v1
  prototype repo (`processheal`, pre-alphabet-split). It is the **5.2%**
  side of the measured-circularity claim (v1 `summary.structure.recall` =
  0.0524 vs post-split 1.8% in `outputs/benchmark_v3.json`); kept here so
  the claim is recomputable without the other repository.
- Seeds are fixed where randomness exists (`baselines.py` random_state=7;
  `grammar.py` NULL_SEEDS). Everything else is deterministic.
- SDAHU is the bit-repro regression standard: re-running
  `scripts/benchmark.py sdahu` must reproduce
  `outputs/benchmark_v6_sdahu.json` byte-identically.

## 7. Which artifact backs which claim

| Claim | Artifact |
|---|---|
| Scorecards 14/14 naive / **13/14 adjudicated (E5, X11)**, 23/30, 24/29; TTD; localization | `benchmark_v6_*.json` + `x11_branch.json` |
| Joint FPR 15.6/12.5/4.2% naive; 1.0/5.2/4.2% deployed | `union_fpr_*.json` |
| PCA/iForest baselines (13/14 @ 1/79 etc.) | `baselines_*.json` |
| Discovery-automation (MR2=freq 141=141, 206=206; MR1 231/124 healthy-day fires) | `matched_rules_*.json` |
| Grammar, reversal probe, cold-start FAIL | `grammar_results.json` |
| Zone ground truth (50 S / 10 indeterminate), dataset errata evidence | `week0_audit.json` |
| Circularity 5.2% → 1.8% | `benchmark_v2_processheal_v1.json` + `benchmark_v3.json` |
| Sensor coverage (12/30, 56/109 mapped) | `sensor_coverage.json` |
| Cry-wolf ratios (<0.1%) | `crywolf.json` |
| X11 branch adjudication (13/14); X8 contamination breakdown; X5 severity; X7 sampling | `x11_branch.json`, `x8_contamination.json`, `x5_severity.json`, `x7_downsample.json` |
