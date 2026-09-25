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

## Erratum E3 — SDAHU `SA_SP`/`SA_SPSPT`: a constant offset applied to one column in each branch, a different column each

**Correction 2026-09-23.** This erratum previously read "units and roles
swapped between the healthy file and every fault file". Two independent
recomputations (2026-09-11 and 2026-09-23) show that reading was wrong,
and it is retracted here. The consequence (below) is unchanged.

**Files:** `AHU_annual` (healthy) vs all 20 fault files.

**Evidence.** The two branches differ by a single additive constant, not
by a unit:

- healthy `SA_SPSPT` = 1.60746 (constant); every fault file's `SA_SPSPT`
  = −400.25253 (constant); 1.60746 − (−400.25253) = **401.85999**.
- healthy `SA_SP` with fan off ≈ 401.86; every fault file's `SA_SP` with
  fan off ≈ 0.005; difference **401.86** again. Subtracting that constant
  from the healthy `SA_SP` reproduces the fault files' trace to three
  decimals: 0.004 inH₂O with the fan off, 1.61 inH₂O with it on, against a
  1.607 inH₂O setpoint (the physically sensible pair; a duct at 1.6 inH₂O
  with the fan off is impossible, which is what rules out the old
  pascal reading).

So the healthy branch has the constant **added to `SA_SP`** and the fault
branch has it **subtracted from `SA_SPSPT`**. The uncorrupted signals are
the fault files' `SA_SP` (already inH₂O) and the healthy file's
`SA_SPSPT`. Zero overlap between branches on either column, as before.

**Consequence (measured, 2026-09-23):** a single threshold on either
column, chosen from the healthy file alone, classifies all 365 healthy
days and all 7,150 fault-file days correctly — accuracy 1.0 on both
columns (`outputs/e3_leakage.json`, `scripts/e3_leakage.py`). Any
data-driven model fed these columns separates healthy from fault **by
file provenance**, not by fault physics. Our own PCA-SPE baseline
initially scored SPE ≈ 1e37 from exactly this (found by auditing our own
baseline — `RESEARCH_LOG.md` D7, ledger L18); the columns are dropped
from all baselines (`scripts/baselines.py: ERRATUM_COLS`).

**Probable root cause.** The offset is branch-specific, and E5 documents
that the healthy file was simulated on a different configuration branch
than every fault file. E3 is therefore most likely a symptom of the same
branch divergence, manifesting as a post-processing difference in how
the static-pressure columns were written. It is listed separately because
its consequence — provenance leakage into any model — is distinct from
E5's, but the two should not be counted as independent evidence of
dataset defects.

**Who it bites:** every ML baseline trained on healthy and scored on fault
files with these columns included — its SDAHU numbers are provenance
detection. Published SDAHU ML results that used the full column set
should be read with this in mind.

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
- **Schedule** (`uv run python scripts/e5_schedule.py` → `outputs/e5_schedule.json`,
  added 2026-09-23; until then this bullet was prose only): on the
  pipeline's own occupancy signal (SYS_CTL) the day universe is IDENTICAL
  between branches (303 occupied days on every full-year file; the short
  damper_stuck_100 file has 179), within two minutes per day. The branch
  difference is a one-hour phase shift: the healthy file starts at
  05:01–05:02 on 200 of the 303 occupied days, every fault file starts
  06:01. *(A daily fan-runtime difference once quoted here was measured
  on SF_CS, a sensor the pipeline does not read, and is retracted —
  2026-09-23.)* *(An earlier version of this erratum quoted
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
exactly on the fault-branch no-fault baseline (+0.007 vs +0.008) — it IS
branch provenance, and SDAHU's scorecard is 13/14 under branch correction
(X11, Phase 8; `outputs/x11_branch.json`)**; the coi_bias detections survive by an
order of magnitude (±3.6/±7.2 °F vs the 1.06 °F offset); the nine
rules-carried scenarios are branch-immune (signature rules compare a
device's position to its own command within the same file — verified: the
command floors wherever the position does); the seasonal rate channel is
branch-confounded on SDAHU and stays diagnostic-only. FPU systems are
single-branch on the schedule axis (verified) — cross-checks live there.
**Adjudicated by X11 (Phase 8): 14/14 → 13/14; falsifier-clean under the
pre-registered procedure; FPU homogeneity verified as an artifact.**

**Who it bites:** every method — classical, ML, or ours — trained on
`AHU_annual` and scored on the fault files. This erratum bites our own
benchmark and we say so.

---

## Documentary notes (not errata)

- **`coi_bias` naming (recorded 2026-09-23).** The dataset documentation's
  file table names the supply-air-temperature-sensor-bias family
  `sa_bias_*_annual.csv`; the archive ships `coi_bias_*_annual.csv`. No
  erratum is raised; the family is scored as shipped. Not investigated
  further.

## Handling summary (what this repo does)

| Erratum | Mitigation in this repo |
|---|---|
| E1 | oa_bias = ONE fault scenario, relabeled as a fault; never a negative |
| E2 | coi_leakage = ONE scenario in `scenarios.yaml` |
| E3 | `ERRATUM_COLS` dropped in baselines; STRATA configs never mapped them |
| E4 | sort-on-convert + calendar gate + `exclude: true` |
| E5 | adjudicated by X11: 14/14→13/14; oa_bias resid = branch provenance; FPU homogeneity verified (0-min scheduled-occupancy diff; L29 caveat on the leg-(a) reading) |

Week-0 gate battery (MD5, zone ground truth, monotonicity/calendar, TTL
coverage, errata evidence): `scripts/02_week0_audit.py` — reusable on any
new dataset before any design decision touches it.

## Erratum E6 — FCU `Fouling_Cooling_Airside_Minor` and `Fouling_Heating_Airside_Minor`: one run shipped under two family labels

**Files:** `FCU_Fouling_Cooling_Airside_Minor.csv`, `FCU_Fouling_Heating_Airside_Minor.csv`
(LBNL FDD Data Sets: Fan Coil Unit, DOI 10.25984/1881324).

**Evidence** (`uv run python scripts/gates_system.py fcu … FCU_FaultFree`,
`outputs/week0_audit_fcu.json`, G1): the two raw CSVs are **byte-identical**
(MD5 `a0b885fe…`), the only duplicate group among the 49 files. Unlike the
SDAHU cases (E1, E2) the two labels name different *families* — a cooling
coil and a heating coil — so one of them is simply wrong, and nothing in
the data can say which.

**Treatment:** the content is scored once, under the cooling-file entry,
with a label that records the identity; the heating-file entry is kept in
the manifest with `exclude:` so it appears in the scorecard as excluded and
cannot count as independent evidence. The coil-fouling family is therefore
11 scored scenarios on this system, not the documentation's 12, and the
minor-airside cell is attributable to neither coil.

**Related observation (not a defect):** four fault files have fewer
occupied days than the fault-free year (261): `OADMPRStuck_80` 215,
`OADMPRStuck_50` 242, `OADMPRStuck_100` 249, `Control_Unstable` 250. In the
three damper files the controller enters shutdown (`FCU_CTRL = 0`) — 94
days in the stuck-80 % file, mixed-air temperature down to 2 °F — which is
the documented low-temperature protection (mixed air below 35 °F)
responding to a damper held open in winter; the unstable-control file
trips for a different reason (its damper never leaves the normal 0.30). The fault-free file has no shutdown minute. These are
physical consequences of the seeded faults and the G6 healthy-inside-cluster
check passes; they are noted because they change the occupied-day universe those files are scored on (no channel is credited for them: `absence_days` is 0 on every scenario).

## Erratum E7 — FPU documentation names the west zone; the faults are in the south zone

**Found 2026-09-25 (hostile review of X33b).** `LBNL_FDD_Data_Sets_FPU.pdf` p. 12
states: "the fault was performed in the PFPU and SFPU in the west zone (i.e., one
FPU out of four FPUs was imposed faults and its variables are followed by zone
identifier _W)". In every PFPU and SFPU fault file the columns that move are the
`_S` ones. Evidence (occupied minutes, fault file against the fault-free file):

| file | mean \|ΔRM_TEMP\| I / W / S / E | RH_GPM ratio I / W / S / E | mean \|ΔVAV_DMPR\| I / W / S / E |
|---|---|---|---|
| PFPU_SensorBias_RMTEMP_+4C | 0.05 / 0.02 / **1.77** / 0.02 °F | 1.01 / 1.01 / **0.10** / 1.01 | 0.01 / 0.01 / **0.17** / 0.01 |
| PFPU_VAVDMPRStuck_0% | 0.19 / 0.44 / **13.8** / 0.57 | 1.32 / 1.06 / **0.18** / 1.05 | 0.01 / 0.01 / **0.25** / 0.01 |
| PFPU_ReheatCoilFouling_Waterside_Severe | 0.00 / 0.00 / 0.01 / 0.00 | 1.00 / 1.00 / **0.84** / 1.00 | 0 / 0 / 0 / 0 |

The project's zone ground truth (week-0 audit: 50 scenarios S, 10 indeterminate)
was established from the data and already places every fault in zone S; the
alarm-attribution specificity counts rest on that, not on the documentation.
Consequence for others: a reader who takes the documentation at its word and
scores localisation against zone W will score every correct zone-S alarm as
wrong. Reproduce: `uv run python scripts/e7_zone_label.py` (writes
`outputs/e7_zone_label.json`).

