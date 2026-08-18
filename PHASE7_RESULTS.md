# Phase 7 Results — Make the Record True

Closes MASTER_PLAN gaps S5 (staleness), S7 (cry-wolf), S9 (errata),
S10 (reproducibility), S11 (sensor coverage). No detection numbers changed
in this phase — it makes the existing numbers quotable, recomputable, and
internally consistent. New artifacts: `outputs/crywolf.json`,
`outputs/sensor_coverage.json`, `outputs/benchmark_v2_processheal_v1.json`,
`week0_audit.json` gate 5. New docs: `ERRATA.md`, `REPRODUCING.md`.
Guards: `tests/test_phase7_artifacts.py` (94 tests total passing after the audit fixes below).

## 1. ERRATA.md — the dataset-quality contribution, now citable (S9)

All four then-known LBNL dataset errata consolidated in one canonical file (E1–E4; the hostile audit below added a fifth, E5)
with per-erratum evidence, recompute command, consequence, and who-it-bites,
backed by a new machine-readable evidence gate
(`scripts/02_week0_audit.py sdahu` → `week0_audit.json.sdahu_errata_evidence`):
raw + parquet MD5 duplicate tables, SA_SP/SA_SPSPT healthy-vs-fault stats,
and the controller-side proof for oa_bias.

**A falsifier fired while building the evidence** — and improved the claim:
the long-standing prose "OA_TEMP bit-identical to healthy" is FALSE. The
recorded OA_TEMP differs by up to 0.33 °F (mean 0.02 °F) from intake-node
flow feedback; OA_CFM is bit-identical. The controller-side conclusion
SURVIVES on the corrected evidence — the recorded stream contains nothing
resembling the labeled ±2–4 °F bias while behaviour diverges by degrees —
but the precise statement is now the one in ERRATA.md E1, and
GAP_ANALYSIS F1 was amended. (Ledger L26.)

## 2. Staleness sweep (S5) — every known stale number corrected at source

- **RESEARCH_LOG Part V addendum (2026-08-18)**: the canonical
  quote-from-here block — v12 scorecards, honest TTD distribution
  ("median 1 day" + tails, never bare "1–2 days"), joint FPR + demotion,
  50/10 zone ground truth, MR2=freq on BOTH FPUs (141=141, 206=206),
  MR1 231/124, the PCA dead heat 61=61, window-conditional recall 100%,
  residual denominator semantics, onboarding recount.
- GAP_ANALYSIS G5 rescoped ("event-log-identical" was v1-alphabet-only;
  byte-level duplicates stand); F1 weather-identity phrasing corrected.
- ONBOARDING_LOG: 48→**45** mappings at commit aa92970 (miscount),
  today's 57+39 noted with timestamps.
- PHASE1: "18 unique model days" → 23 in v12 (same ≈-noise conclusion).
- PHASE2: SUPERSEDED banner (never quote; three reasons listed).
- DAYLOG 08-10: 51/9 → 50/10 correction footnote (artifact wins).
- `union_fpr.py` docstring TTD claim scoped to rate-significant scenarios.

## 3. REPRODUCING.md (S10) — clone-to-artifacts path

Dataset DOI (10.25984/1881324) + download layout; `uv sync`; converter
paths now overridable (`STRATA_SDAHU_RAW`, `STRATA_FPU_RAW`, or argv —
hardcoded personal paths removed from behaviour); the full ordered
runbook (week-0 gates → benchmark/baselines/matched-rules/stats/union per
system → grammar → coverage → cry-wolf); provenance notes; a
claim→artifact table. The v1 circularity artifact
(`benchmark_v2_processheal_v1.json`, structure recall 0.0524) is now
in-repo, so the 5.2%→1.8% claim no longer depends on a second repository.
Dead `make_figures.py` (read a nonexistent v2 artifact) deleted; the v12
figure pipeline is paper-phase work. README now points here and marks the
v1 quick-start demo as legacy.

## 4. Sensor coverage (S11) and cry-wolf (S7) — as artifacts, not prose

- `sensor_coverage.json`: SDAHU **12/30** columns mapped (18 unmapped,
  incl. ZONE_TEMP_1..5, SA/RA/OA_CFM); PFPU/SFPU **56/109** (53 unmapped,
  incl. VAV_FAN_DP_* — the sensor PCA used on SFPU airside fouling). Zero
  ghost mappings (every configured sensor exists in the data). This is the
  honesty section's ammunition and the headroom estimate.
- `crywolf.json`: deployed-detector cry-wolf ratio **0.026% / 0.083% /
  0.066%** (SDAHU/PFPU/SFPU) — of all alarm-days raised, fewer than 1 in
  1000 are false, with the exposure asymmetry stated in the artifact.

## Hostile-audit fixes (2026-08-18, applied post-fb80099)

The audit verdict was "NOT paper-citable as committed" — arithmetic all
sound (every number reproduced, several byte-identically), but eight
required fixes. All applied:

1. **E1 mechanism reworded**: "bias injected into the controller's
   reading" demoted to "consistent with a controller-side injection
   confined to the cooling interlock; a mislabeled cooling-lockout fault
   cannot be excluded." The vacuous OA_CFM leg (a constant column) is
   descoped; the degree-scale MA/SA divergence is re-attributed to E5.
2. **NEW ERRATUM E5** (found by the audit attacking E1): the healthy SDAHU
   file was simulated on a different configuration branch than every fault
   file (occupied OA-damper floor 0.000 vs exactly 0.100; different fan
   schedules). Verified across all 20 fault files; evidence in gate 5's
   `config_branch` block. It bites every healthy-trained SDAHU evaluation
   including ours — branch-sensitivity check queued as X11 (Phase 8).
   Fault-vs-fault cross-family divergence is ~0.05–0.14 °F vs degrees
   against healthy: most healthy-vs-fault "behaviour divergence" was
   branch, not fault.
3. **Gate 6 added** (E4 raw-rotation evidence: set-identical timestamps,
   1 wrap, starts Jan 3) — E4 now has machine evidence; the previously
   cited `mono` gate could never exhibit the defect (conversion sorts).
4. **8 missed stale locations fixed**: gate-5 docstring (still asserted
   the falsified "bit-identical" claim!), PHASE4 median TTD row + tail
   row, PHASE3B banner, PHASE3C marker, RESEARCH_LOG D2/D3 in-place
   corrections, GAP_ANALYSIS G6 + F1 scope notes, DAYLOG top banner.
   MASTER_PLAN statuses updated (S1–S2/S5/S7–S11 done).
5. **Experiment tags renamed E→X** (X1–X11) repo-wide, ending the
   collision with ERRATA E-tags; stats.py's third "audit E1" namespace
   removed.
6. **Guards de-tautologized**: crywolf TP and coverage `mapped` are now
   RECOMPUTED from upstream sources in the tests; E5 + gate-6 guards
   added (94 tests passing).
7. **Converters fail loudly** on an empty source glob (was a silent no-op
   printing "Converting 0 CSV files").
8. **Cry-wolf denominators** ship in the artifact and print
   (FP 1/96 healthy days vs TP 3886/4891 fault-scenario days, etc.);
   definition text forbids quoting the ratio without them.

## Ledger

- **L26**: evidence packaging is itself an audit — turning the narrated
  oa_bias claim into a computed artifact falsified its strongest wording
  ("bit-identical") while strengthening the conclusion (the labeled bias
  is absent from the recorded stream). Every claim promoted into a citable
  document must be recomputed on promotion, not copied.
- **L27** (from the hostile audit): a "make the record true" pass is
  itself a record that can be stale — the sweep missed 8 locations, one
  INSIDE the function computing the correction, and left the master plan
  stale about itself. Staleness sweeps need a grep-list of the retired
  numbers ("17/30", "38–45%", "51/60", "bit-identical", …) run over the
  WHOLE repo, docs and code comments alike, not a curated file list.
- **L28**: healthy-vs-fault divergence is only fault evidence after a
  fault-vs-fault control — E5 hid for six phases because every comparison
  ran against the healthy file; one cross-family diff (0.05 °F vs
  degrees) exposed the branch offset immediately. The control is now part
  of the week-0 battery's logic.
