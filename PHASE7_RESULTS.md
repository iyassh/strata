# Phase 7 Results — Make the Record True

Closes MASTER_PLAN gaps S5 (staleness), S7 (cry-wolf), S9 (errata),
S10 (reproducibility), S11 (sensor coverage). No detection numbers changed
in this phase — it makes the existing numbers quotable, recomputable, and
internally consistent. New artifacts: `outputs/crywolf.json`,
`outputs/sensor_coverage.json`, `outputs/benchmark_v2_processheal_v1.json`,
`week0_audit.json` gate 5. New docs: `ERRATA.md`, `REPRODUCING.md`.
Guards: `tests/test_phase7_artifacts.py` (92 tests total passing).

## 1. ERRATA.md — the dataset-quality contribution, now citable (S9)

All four LBNL dataset errata consolidated in one canonical file (E1–E4)
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

## Ledger

- **L26**: evidence packaging is itself an audit — turning the narrated
  oa_bias claim into a computed artifact falsified its strongest wording
  ("bit-identical") while strengthening the conclusion (the labeled bias
  is absent from the recorded stream). Every claim promoted into a citable
  document must be recomputed on promotion, not copied.
