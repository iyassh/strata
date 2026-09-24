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
byte-duplicate fault files, the oa_bias mislabel, a per-branch additive constant on SA_SP/SA_SPSPT, one
rotated calendar, and the healthy file's configuration-branch offset).
The pipeline handles or discloses all five.

## 2. Environment

```sh
uv sync          # exact pins from uv.lock; Python >= 3.12
uv run pytest -q # full suite (over a hundred tests; 5 data-dependent ones skip on a bare clone), ~10 s
```

System dependency: `pm4py` visualisations need the Graphviz *binary*
(`brew install graphviz` / `apt install graphviz`); detection itself does not.

## 3. Convert raw CSVs to parquet

Point the converters at your download location (env var or first argument; the default is `data/raw/<archive folder>` relative to the repo root):

```sh
export STRATA_SDAHU_RAW=/path/to/LBNL_FDD_Data_Sets_SDAHU_all_3
export STRATA_FPU_RAW=/path/to/LBNL_FDD_Data_Sets_FPU_all_3
uv run python scripts/00_convert_to_parquet.py   # -> data/processed/sdahu/
uv run python scripts/01_convert_fpu.py          # -> data/processed/{pfpu,sfpu}/
export STRATA_DDAHU_RAW=/path/to/LBNL_FDD_Data_Sets_DDAHU_all_3   # fourth system (X17)
uv run python scripts/05_convert_ddahu.py        # -> data/processed/ddahu/
export STRATA_FCU_RAW=/path/to/LBNL_FDD_Data_Sets_FCU_all_3       # fifth system (X19)
uv run python scripts/06_convert_fcu.py          # -> data/processed/fcu/
```

`data/` is gitignored; any location works if `data/processed/<system>/`
resolves from the repo root (symlink is fine).

## 4. Gates before science (the week-0 battery)

```sh
uv run python scripts/02_week0_audit.py all        # MD5 + errata evidence + zone GT + calendar + TTL
uv run python scripts/03_healthy_silence.py configs/lbnl_pfpu data/processed/pfpu/PFPU_FaultFree.parquet
```

(The healthy-silence gate is per config; run it for any config you touch.)

For a new system the generic gate battery replaces the audit script:

```sh
uv run python scripts/gates_system.py ddahu $STRATA_DDAHU_RAW/LBNL_FDD_Dataset_DDAHU DualDuct_FaultFree configs/lbnl_ddahu/equipment.ttl
uv run python scripts/03_healthy_silence.py configs/lbnl_ddahu data/processed/ddahu/DualDuct_FaultFree.parquet
uv run python scripts/gates_system.py fcu $STRATA_FCU_RAW/LBNL_FDD_Dataset_FCU FCU_FaultFree configs/lbnl_fcu/equipment.ttl
uv run python scripts/03_healthy_silence.py configs/lbnl_fcu data/processed/fcu/FCU_FaultFree.parquet
```

## 5. The result pipeline (order matters only within a system)

```sh
for s in sdahu pfpu sfpu; do
  caffeinate -i uv run python scripts/benchmark.py $s        # scorecards -> outputs/benchmark_v6_$s.json
  caffeinate -i uv run python scripts/baselines.py $s        # iForest/PCA -> outputs/baselines_$s.json
  caffeinate -i uv run python scripts/matched_rules.py $s    # ablation arm -> outputs/matched_rules_$s.json
  uv run python scripts/stats.py $s                          # significance battery (prints; day lists in artifacts)
  caffeinate -i uv run python scripts/union_fpr.py $s        # joint FPR + demotion checks -> outputs/union_fpr_$s.json
done
caffeinate -i uv run python scripts/benchmark.py ddahu       # fourth system (X17) -> outputs/benchmark_v6_ddahu.json
caffeinate -i uv run python scripts/union_fpr.py ddahu       # absence-channel coverage the check cannot see is recorded as unresolved
uv run python scripts/x17_onboarding.py                      # -> outputs/x17_onboarding.json
caffeinate -i uv run python scripts/benchmark.py fcu         # fifth system (X19) -> outputs/benchmark_v6_fcu.json
caffeinate -i uv run python scripts/union_fpr.py fcu
uv run python scripts/x19_onboarding.py                      # -> outputs/x19_onboarding.json
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
| Discovery-predicts-transfer (sealed, pre-registered): Q .978/.455/0, six-cell rho -0.693, exact p 0.200, F1+F2 fired | `discovery_predicts_transfer_q.json` (regenerated by `scripts/discovery_predicts_transfer_q.py`; reproduced identically 2026-09-23) + `discovery_predicts_transfer.json` (scorer) |
| Alarm attribution on all 61 detected scenarios: 36 correct / 10 none / 0 wrong device; 14 SDAHU (no device stratum); 1 indeterminate GT | `alarm_attribution.json` (from the scorecards; `scripts/alarm_attribution.py`) |
| E3 leakage as a measurement: a healthy-only threshold on SA_SP or SA_SPSPT classifies all 20 fault files' days as non-healthy with zero error | `e3_leakage.json` (`scripts/e3_leakage.py`) |
| E5 schedule leg as a measurement: 303 occupied days on every full-year SDAHU file (179 on the short one); healthy first-occupied minute 05:01/05:02 on 200 of 303 days, 06:01 on every day of every fault file | `e5_schedule.json` (`scripts/e5_schedule.py`) |
| The four log-generic gates run on two public event logs (Sepsis: 1,050 cases / 15,214 events; receipt: 1,434 / 8,577), all pass, under a second each on a laptop (timing printed by the script, not committed: machine-dependent) | `gates_public_log.json` (`scripts/gates_public_log.py`, same code as `strata gates`; logs fetched by DOI/URL, not committed) |
| Log-level diagnosis over 73 scenarios: 8 of the 12 misses (all fouling) have a state log indistinguishable from healthy at 5 % in every count and on-duration; the other 4 change a count by 7–39 % | `x12_log_diagnosis.json` (`scripts/x12_log_diagnosis.py`) |
| X12 time perspective of the discovered state model (pre-registered): significant on 11/73, none of them a scenario the deployed channels miss (P3 false), never earlier, +5 holdout false-alarm days on each fan-powered system (PFPU joint 5→10 of 96); a small coverage supplement (81 unique days on coi_bias_-4, at most 16 on a fan-powered scenario) | `x12_time_perspective.json` (`scripts/x12_time_perspective.py`; `docs/plans/2026-09-23-x12-time-perspective-prereg.md`) |
| X13 coil-effectiveness residual for the fouling misses (fault-informed design, disclosed; healthy-only thresholds): **F-X13.b fired** — 1 of 9 fouling scenarios significant, nothing newly detected | `x13_coil_effectiveness.json` (`scripts/x13_coil_effectiveness.py`; `docs/plans/2026-09-23-x13-coil-effectiveness-prereg.md`) |
| X14 enriched state alphabet (healthy-derived actuator/flow bands, 15-min dwell; Amendments 1–3): one missed scenario becomes significant (SFPU_ReheatCoilFouling_Airside_Moderate, a dose-monotone zone-S damper signature — control in `x14_control.json`, `scripts/x14_control.py`), SDAHU model channel 14 of 14 significant against 0 of 14 deployed, but holdout false alarms 7/18/21 of 96 — **F-X14.a fired**; alignment channels not evaluated on the FPUs (infeasible) | `x14_enriched_alphabet.json` (`scripts/x14_enriched_alphabet.py`; `docs/plans/2026-09-23-x14-enriched-alphabet-prereg.md`) |
| X15 enriched alphabet, frequency channel only, both holdout splits (post-hoc-motivated, stated): inside the budget under both (2/0, 4/8, 3/5), SFPU_ReheatCoilFouling_Airside_Moderate significant under both, nothing else new, 41 vs 12 significant on already-detected scenarios; no falsifier fired | `x15_enriched_frequency.json` (`scripts/x15_enriched_frequency.py`; `docs/plans/2026-09-23-x15-enriched-frequency-prereg.md`) |
| X9/X10 robustness (pre-registered, three amendments): 1× jitter leaves detection counts unchanged (14/23/24) at 1/4/2 false-alarm days in 96; 2×/4× identical on SDAHU; first-8-days holdout 13/23/25 at 0/2/3; no falsifier fired; fan-powered arms without the conformance channels | `x9_x10_robustness.json` (`scripts/x9_x10_robustness.py`; `docs/plans/2026-09-23-x9-x10-robustness-prereg.md`) |
| X17 fourth system, dual-duct AHU onboarded config-only (pre-registered): gates clean (56 distinct, monotonic, calendar-identical, TTL complete); 45/55 detected; deployed FP 3/96 (naive 8/96); no scenario by conformance alone; P6 (fouling ≤ 4) failed upward (5); no falsifier; the demotion check's one 'violation' was its own blind spot (an absence-channel day-1 alarm), recorded as unresolved | `week0_audit_ddahu.json`, `benchmark_v6_ddahu.json`, `union_fpr_ddahu.json`, `x17_onboarding.json` (`scripts/gates_system.py`, `benchmark.py ddahu`, `union_fpr.py ddahu`, `x17_onboarding.py`; `docs/plans/2026-09-24-x17-ddahu-onboarding-prereg.md`) |
| X18 X15's enriched-frequency protocol on DDAHU (pre-registered): budget held under both splits (2/83), coverage 22 vs 8 on detected scenarios, **no missed scenario gained — F-X18.b fired** | `x18_ddahu_enriched_frequency.json` (`scripts/x18_ddahu_enriched_frequency.py`; `docs/plans/2026-09-24-x18-ddahu-enriched-frequency-prereg.md`) |
| Injected-defect sensitivity: duplicate file → G1 only; duplicate case → G4 only; rotated case → G2 only; case moved out of era → G3 only; leaked per-case outcome constant → no gate | `gates_injection.json` (`scripts/gates_injection.py` on the Sepsis log) |
