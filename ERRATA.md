# LBNL FDD Dataset Errata — SDAHU / PFPU / SFPU

Documented dataset-quality findings in the LBNL fault-detection datasets
(Granderson et al., DOI 10.25984/1881324, CC BY 4.0), discovered during the
STRATA project's week-0 audits and phase audits. Each erratum states the
affected files, the evidence with a recompute command, the consequence, and
who it bites. Machine-readable evidence: `outputs/week0_audit.json`
(gates 1–5; gate 5 = `sdahu_errata_evidence`).

These findings do not diminish the datasets — they remain the largest
labeled HVAC fault corpus available — but any benchmark built on them
inherits these properties silently unless they are handled.

**Numbering note (this file is canonical):** earlier project documents used
an evolving numbering. Mapping: this file's E1 = GAP_ANALYSIS F1 /
RESEARCH_LOG D2 ("erratum #1"); E2 (coi_leakage duplication) was previously
unnumbered (noted in GAP_ANALYSIS G5); E3 = RESEARCH_LOG D7's "erratum #4"
and the vault v2 revision's coi_leakage_050 note ("#3" — same phenomenon,
first sighting); E4 = RESEARCH_LOG L10's rotated file ("erratum #2" in some
lists). Cite this file, not the historical numbers.

---

## Erratum E1 — SDAHU `oa_bias_*`: one run shipped four times, and the bias is controller-side

**Files:** `oa_bias_-4/-2/2/4_annual.csv` (and their parquets).

**Evidence** (`uv run python scripts/02_week0_audit.py sdahu`):
- All four files are **byte-identical** (raw CSV MD5 `89b13704…`, parquet
  `63b857d7…`): one simulation run shipped under four severity labels. The
  ±2/±4 severity labels carry no information.
- The recorded `OA_TEMP` tracks the healthy file's weather to within
  0.33 °F (mean 0.02 °F) — nowhere near the labeled ±2–4 °F bias — while
  behaviour diverges by degrees (MA_TEMP mean |Δ| 1.72 °F, SA_TEMP
  2.10 °F). `OA_CFM` is bit-identical to healthy. A sensor-side bias would
  appear in the recorded stream; it does not. **The bias was injected into
  the controller's reading**, so the run behaves faulty while its sensor
  data looks healthy.

**Consequence:** the oa_bias runs are **fault runs, not healthy negatives**.
Early in this project one oa_bias file was provisionally treated as an
independent healthy year; a "48.8% false-positive rate" against it turned
out to be genuine detection of the controller-side fault (relabel history in
`GAP_ANALYSIS_AUG2026.md` F1, `RESEARCH_LOG.md` D2). After the relabel,
**SDAHU has no independent healthy negative run at all** — a limitation
every SDAHU study inherits.

**Who it bites:** any evaluation using oa_bias as a negative/healthy class;
any method comparison treating the four severities as four scenarios; any
sensor-space method expecting the labeled bias in the data (e.g. AFDD
sensor-bias detectors evaluated on these files test nothing).

## Erratum E2 — SDAHU `coi_leakage_*`: one run shipped four times

**Files:** `coi_leakage_010/025/040/050_annual.csv` (and parquets).

**Evidence:** all four byte-identical (raw MD5 `a9fdfc50…`, parquet
`5133132d…`) — same gate as above.

**Consequence:** the 010/025/040/050 severity ladder is vacuous; SDAHU has
**one** valve-leakage scenario, not four. Together with erratum 1, the
21-file SDAHU set contains **15 distinct files = healthy + 14 distinct
fault scenarios**. Severity–response analysis (dose-response, Spearman ρ)
is impossible for this family on SDAHU.

**Who it bites:** any per-scenario accounting that counts 20 fault
scenarios; any severity-monotonicity analysis including this family.

## Erratum E3 — SDAHU `SA_SP`/`SA_SPSPT`: units and roles swapped between the healthy file and every fault file

**Files:** `AHU_annual` (healthy) vs all fault files.

**Evidence** (same gate): healthy `SA_SP` ≈ 402 (Pa-scale constant),
`SA_SPSPT` ≈ 1.607; every fault file `SA_SP` ≈ 0.86 (inH₂O-scale),
`SA_SPSPT` ≈ −400.25. First noticed on `coi_leakage_050` (vault v2
revision note); the week-0-style recheck shows it holds healthy-vs-ALL-faults.

**Consequence:** any data-driven model fed these columns separates healthy
from fault **by file provenance**, not by fault physics. Our own PCA-SPE
baseline initially scored SPE ≈ 1e37 from exactly this (found by auditing
our own baseline — `RESEARCH_LOG.md` D7, ledger L18); the columns are
dropped from all baselines (`scripts/baselines.py: ERRATUM_COLS`).

**Who it bites:** every ML baseline trained on healthy and scored on fault
files with these columns included — its SDAHU numbers are provenance
detection. Published SDAHU ML results that used the full column set should
be read with this in mind.

## Erratum E4 — SFPU `SensorBias_RMTEMP_-2C`: date-rotated calendar

**Files:** `SFPU_SensorBias_RMTEMP_-2C.csv`.

**Evidence:** the raw file's rows are date-rotated relative to every other
SFPU file (found by the week-0 monotonicity/calendar-identity gate:
`uv run python scripts/02_week0_audit.py mono`; conversion sorts and
asserts — see `scripts/01_convert_fpu.py`). `RESEARCH_LOG.md` L10.

**Consequence:** naive positional (row-index) comparison against the
healthy file misaligns every timestamp. We sort on conversion, enforce
calendar identity, and **exclude the scenario from scoring** (marked
`exclude: true` in `configs/lbnl_sfpu/scenarios.yaml`), leaving SFPU with
29 scored fault scenarios.

**Who it bites:** any pipeline that aligns files positionally rather than
by timestamp; any SFPU scenario count of 30.

---

## Handling summary (what this repo does)

| Erratum | Mitigation in this repo |
|---|---|
| E1 | oa_bias = ONE fault scenario, relabeled controller-side; never a negative |
| E2 | coi_leakage = ONE scenario in `scenarios.yaml` |
| E3 | `ERRATUM_COLS` dropped in baselines; STRATA configs never mapped them |
| E4 | sort-on-convert + calendar gate + `exclude: true` |

Week-0 gate battery (MD5, zone ground truth, monotonicity/calendar, TTL
coverage, errata evidence): `scripts/02_week0_audit.py` — reusable on any
new dataset before any design decision touches it.
