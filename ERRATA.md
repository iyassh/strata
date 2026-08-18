# LBNL FDD Dataset Errata — SDAHU / PFPU / SFPU

Documented dataset-quality findings in the LBNL fault-detection datasets
(Granderson et al., DOI 10.25984/1881324, CC BY 4.0), discovered during the
STRATA project's week-0 audits and phase audits. Each erratum states the
affected files, the evidence with a recompute command, the consequence, and
who it bites. Machine-readable evidence: `outputs/week0_audit.json`
(gates 1–6; gate 5 = `sdahu_errata_evidence`, gate 6 =
`sfpu_rotation_evidence`).

These findings do not diminish the datasets — they remain the largest
labeled HVAC fault corpus available — but any benchmark built on them
inherits these properties silently unless they are handled.

**Numbering note (this file is canonical):** earlier project documents used
an evolving numbering. Mapping: this file's E1 = GAP_ANALYSIS F1 /
RESEARCH_LOG D2 ("erratum #1"); E2 (coi_leakage duplication) was previously
unnumbered (noted in GAP_ANALYSIS G5); E3 = RESEARCH_LOG D7's "erratum #4"
and the vault v2 revision's coi_leakage_050 note ("#3" — same phenomenon,
first sighting); E4 = RESEARCH_LOG L10's rotated file ("erratum #2" in some
lists); E5 is new (Phase-7 hostile audit, no historical number). Cite this
file, not the historical numbers. (Experiments from the v2 revision use the
X-namespace — X1–X11 — to avoid collision with these E-tags.)

---

## Erratum E1 — SDAHU `oa_bias_*`: one run shipped four times, and the bias is controller-side

**Files:** `oa_bias_-4/-2/2/4_annual.csv` (and their parquets).

**Evidence** (`uv run python scripts/02_week0_audit.py sdahu`):
- All four files are **byte-identical** (raw CSV MD5 `89b13704…`, parquet
  `63b857d7…`): one simulation run shipped under four severity labels. The
  ±2/±4 severity labels carry no information.
- **The labeled sensor-side bias is absent from the recorded stream**: the
  recorded `OA_TEMP` tracks the healthy file's weather to within 0.33 °F
  (mean 0.02 °F, signed mean ≈ 0, 38% exact zeros; the sub-degree residual
  is intake-node flow feedback) — nowhere near ±2–4 °F — and the OA_TEMP
  column is bit-identical across ALL fault files, so it carries no
  fault-specific signal at all. Yet the run misbehaves: relative to other
  fault families, oa_bias holds the cooling valve closed until ~2 °F
  warmer outdoor conditions, leaving SA_TEMP ≈ 2.8 °F above setpoint on
  ~2,000 occupied rows, while the 60 °F economizer lockout shows **no**
  shift. (Caution on the degree-scale MA/SA divergence vs the healthy
  file: most of it is the configuration-branch offset shared by every
  fault file — see E5 — not this fault; the fault-specific signal is the
  cooling-interlock shift above.)
- **Mechanism, honestly bounded:** the evidence is consistent with a −2 °F
  bias injected only into the cooling interlock's outdoor-air input
  ("controller-side"), but is observationally indistinguishable from a
  mislabeled cooling-lockout-setpoint fault. What is proven: the labeled
  sensor bias is not in the data, the run is faulty, and the ±2/±4
  labels are fiction.

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

**Evidence** (same gate): healthy `SA_SP` ≈ 402 Pa-scale (varying over a
~9 Pa range), `SA_SPSPT` exactly constant 1.607460; **every one of the 20
fault files** has `SA_SP` on the inH₂O scale (means 0.84–0.97) and
`SA_SPSPT` exactly constant −400.252530. Zero overlap — either column
alone separates healthy from fault by provenance. First noticed on
`coi_leakage_050` (vault v2 revision note); verified healthy-vs-ALL-faults.

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

**Evidence:** the raw file is a pure rotation by exactly 2,880 rows
(2 days): identical timestamp SET to FaultFree, non-monotonic with exactly
one wrap point, first row 2018-01-03 00:00. Machine evidence:
`uv run python scripts/02_week0_audit.py rotation` (gate 6 — reads the RAW
csv; the parquet gates cannot exhibit the defect because conversion sorts,
see `scripts/01_convert_fpu.py`). `RESEARCH_LOG.md` L10.

**Consequence:** naive positional (row-index) comparison against the
healthy file misaligns every timestamp. We sort on conversion, enforce
calendar identity, and **exclude the scenario from scoring** (marked
`exclude: true` in `configs/lbnl_sfpu/scenarios.yaml`), leaving SFPU with
29 scored fault scenarios.

**Who it bites:** any pipeline that aligns files positionally rather than
by timestamp; any SFPU scenario count of 30.

## Erratum E5 — SDAHU healthy file simulated on a different configuration branch than every fault file

*(Found by the Phase-7 hostile audit, 2026-08-18, while attacking E1's
evidence.)*

**Files:** `AHU_annual` (healthy) vs all 20 fault files.

**Evidence** (`uv run python scripts/02_week0_audit.py sdahu`,
`config_branch` block; integration-review corrections 2026-08-18):
- **Damper floor:** during fan-on hours (SF_CS > 0.5) the healthy file's
  OA damper minimum is **0.000**; every fault file floors at exactly
  **0.100** (the three damper_stuck files at 0.25/0.75/1.0 sit at their
  stuck value above the floor).
- **Schedule:** on the pipeline's own occupancy signal (SYS_CTL) the day
  universe and daily occupied minutes are IDENTICAL between branches
  (same 303 occupied days, ±2 min/day) — the branch difference is a
  **one-hour phase shift** (healthy starts 05:01–05:02 on ~200 days;
  every fault file starts 06:01) plus ~74 min/day more fan runtime
  (SF_CS) in healthy. *(An earlier version of this erratum quoted
  "occupied rows 163,186–351,441" — that range conflated a short 215-day
  file, plausible fault-driven night cycling, and the branch effect, and
  was measured on SF_CS, a sensor the pipeline does not read. Corrected
  per L26/L27.)*
- **Simulation-physics offset (audit-measured, gate ownership queued in
  X11):** the residual channel's no-fault baseline differs by
  **−1.06 °F** between branches — fault-branch fault-free level +0.008 °F
  (five concordant measurements: all four coi_bias files after
  subtracting their nominal bias, plus oa_bias) vs healthy branch
  +1.071 °F (band [0.526, 1.372]). The offset is uniform across occupied
  hours and survives restricting healthy to the fault schedule — it lives
  in the simulated temperatures, not in any harmonizable input column.

**Consequence:** healthy-vs-fault comparisons on SDAHU carry a
**configuration-branch offset on top of the fault**. Most of the
degree-scale MA/SA divergence quoted against the healthy file (E1) is this
branch offset — fault-vs-fault cross-family divergence is ~0.05–0.14 °F.
Any healthy-trained detector on SDAHU (ours included) may partially detect
branch provenance rather than fault physics. Concretely, for THIS project
(integration review, 2026-08-18): the **oa_bias residual detection sits
exactly on the fault-branch no-fault baseline (+0.007 vs +0.008) — it is
likely branch provenance, and SDAHU's scorecard is expected to become
13/14 under branch correction**; the coi_bias detections survive by an
order of magnitude (±3.6/±7.2 °F vs the 1.06 °F offset); the nine
rules-carried scenarios are branch-immune (signature rules compare a
device's position to its own command within the same file — verified: the
command floors wherever the position does); the seasonal rate channel is
branch-confounded on SDAHU and stays diagnostic-only. FPU systems are
single-branch on the schedule axis (verified) — cross-checks live there.
**Adjudication is X11 in MASTER_PLAN Phase 8 (fault-vs-fault branch-offset
estimation + branch-corrected re-scoring — column harmonization alone is
provably insufficient).**

**Who it bites:** every method — classical, ML, or ours — trained on
`AHU_annual` and scored on the fault files. This erratum bites our own
benchmark and we say so.

---

## Handling summary (what this repo does)

| Erratum | Mitigation in this repo |
|---|---|
| E1 | oa_bias = ONE fault scenario, relabeled as a fault; never a negative |
| E2 | coi_leakage = ONE scenario in `scenarios.yaml` |
| E3 | `ERRATUM_COLS` dropped in baselines; STRATA configs never mapped them |
| E4 | sort-on-convert + calendar gate + `exclude: true` |
| E5 | disclosed; branch-sensitivity check queued (X11); FPU systems unaffected |

Week-0 gate battery (MD5, zone ground truth, monotonicity/calendar, TTL
coverage, errata evidence): `scripts/02_week0_audit.py` — reusable on any
new dataset before any design decision touches it.
