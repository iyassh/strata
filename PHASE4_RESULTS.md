# Phase 4 Results — Frequency, Oscillation, Baselines, Statistics (final, post-audit)

Phase 4 built the channels every earlier audit pointed at, faced them with
external ML baselines on identical splits, subjected everything to the
hostile audit, applied all six of its fixes, and re-ran the full pipeline.
These are the final numbers; every one is reproducible from the committed
artifacts.

## Final scorecards (v12 — all audit fixes, noise-gated, exclusions honored)

| | SDAHU | PFPU | SFPU |
|---|---|---|---|
| meaningfully detected | **14/14** | **23/30** | **24/29** * |
| median TTD (significant channels only) | 1 d | 1 d | 1 d |
| TTD tail (full distribution in Part V addendum) | max 2 d | max 21 d | max 108 d |
| healthy-year false-alarm days (rules) | 0 | 0 | 0 |

† *Naive scorecard. X11 (Phase 8) adjudicated SDAHU to **13/14** — the oa_bias residual detection is ERRATA E5 branch provenance. Quote "14/14 naive; 13/14 adjudicated"; see PHASE8_RESULTS.md.*

\* SFPU denominator excludes SensorBias_RMTEMP_−2C (source file calendar-
rotated; weather-mismatched vs calibration year — counted nowhere).

Per-family (FPU): airflow bias 4/4 · damper stuck 5/5 · reheat leak 3/3 ·
reheat stuck 5/5 · fan restrict 1/1 · **instability 2/2 (both systems)** ·
rmtemp bias 3/4 (PFPU), 2/3 (SFPU) · fouling **0/6 (PFPU), 2/6 (SFPU)**.

## What Phase 4 added, channel by channel (honest attribution)

- **Frequency channel** (per-day two-sided count-bands; log-skeleton
  lineage, stochastic-conformance context): delivered RMTEMPUnstable on
  both systems (206/141 days, correctly zone-localized) — prediction P3,
  pre-registered in the v2 spec, CONFIRMED with the clean discovery→channel
  chain. Also carried PFPU RMTEMP−4C (27d), replicating cross-system what
  SFPU's device stratum found — the same invariant, two instruments.
- **Oscillation channel** (Hägglund-style daily direction-change counts,
  per-signal-class deadbands): VAVDMPRUnstable 264/349 days — the fault
  family nothing else could see, because the damper (command-less) has no
  event vocabulary; its hunting lives only in the position signal.
  Post-audit, temperature-signal reversal counting below sensor precision
  is disabled (the secondary stuck/leak firings died with it, correctly).
- **Waterside ΔT residuals**: fouling moved off zero where physics permits:
  SFPU airside severe (7d) + waterside severe (15d) survive the 0.5 °F
  exceedance-margin floor; moderates fall below it; PFPU shows NO
  distributional shift at all under this statistic (Mann-Whitney p=0.68) —
  an instrument-conditional null, reported as such.
- **Seasonal rate channel**: P1 (PFPU damper via heating-day-rate collapse)
  is **partially confirmed with the mechanism corrected**: the collapse is
  real in raw data (166→25 heating days) and the scenario is detected — but
  by the per-day frequency channel via cooling-count side-effects; the rate
  instrument built for the prediction does not clear its own significance
  gate on non-overlapping windows. The 4-iteration instrument chain and
  this outcome are reported in full. P2 remains half-confirmed (faulted
  zone visible via removal; series coupling makes attribution system-wide).

## The baselines (identical splits, healthy-only fit, strict = train-max threshold)

- **IsolationForest: weak everywhere** (2–8 scenarios/system).
- **PCA-SPE: strong and honestly credited.** Post-erratum-fix (see below):
  SDAHU 13/14 at 1/79 holdout FP; FPU systems comparable-to-better on raw
  day counts for saturating families, and it legitimately detects SFPU
  airside fouling better than our channels (via a zone-fan pressure sensor
  our configs never mapped — recorded as a sensor-coverage gap, not method
  superiority). Its SPE contribution decomposition gives coarse
  localization credit we now acknowledge rather than deny.
- **Dataset erratum #4 (found by auditing our own baseline):** SDAHU's
  healthy file logs SA_SP/SA_SPSPT in different units/roles than every
  fault file; a baseline fed those columns detects FILE PROVENANCE, not
  faults (SPE ≈ 1e37). Columns dropped; baseline regenerated; a cross-file
  column-consistency gate joins the week-0 battery.
- The honest comparison sentence: **on saturated year-long single-fault
  simulations, a well-built PCA detects broadly; what it cannot do is name
  a valve, explain a flag, or run at our false-alarm discipline — and the
  three families it beat us on are now either closed (instability via
  oscillation), matched (fouling severe), or named sensor-coverage gaps.**

## The matched-rule arm (finally built; the falsifier discipline, mechanized)

`scripts/matched_rules.py` — MR1 (heating-absence workday), MR2 (per-zone
heating-episode bands), MR3 (seasonal heating-day rate), all train-only.
Verdicts:
- MR2 covers RMTEMPUnstable exactly as well as the frequency channel
  (141 = 141 days, 0 healthy FP) → the freq claim is DISCOVERY-AUTOMATION,
  not detection supremacy: the strata located the invariant; the calibrated
  channel generalizes it to every activity without hand-picking.
- MR1 on PFPU fires 124 healthy days — the rule is INVALID where the rhythm
  doesn't exist. One number that proves the point: the models tell you
  WHERE each invariant holds; rules transplanted without that knowledge
  false-alarm catastrophically.
- No matched rule touches VAVDMPRUnstable (0/2/0 vs oscillation's 349) —
  the oscillation channel IS the classical rule (Hägglund), calibrated;
  nothing simpler replaces it.

## Statistics battery (post-audit constructions)

Exact-binomial tests against each channel's own holdout noise floor
(the invalid c=0 "McNemar" is retracted — it awarded stars to noise; 13
PFPU rows lost them), BH correction across scenarios, day universes
intersected for every STRATA-vs-PCA comparison, day-level autocorrelation
stated as a limitation. Per-scenario day lists ship in the artifacts so
every test is recomputable.

## Audit corrections ledger (this phase)

1. SDAHU baseline poisoned by erratum columns → CRITICAL, fixed, erratum #4.
2. Q1 statistic invalid → replaced with channel-noise null.
3. Rotated file back in the scorecard → excluded; SFPU is n/29; PFPU
   manifest's copy-paste note fixed.
4. Waterside margins sub-precision → exceedance floor; fouling 5/12 → 2/12
   (severe only) — dose-response coherent.
5. Oscillation temperature deadbands → secondary firings retracted.
6. Rate significance rebuilt (non-overlapping windows, uniform policy);
   P1 mechanism honestly re-attributed.

## Where this leaves the thesis

The stratified framework's honest claim, now triple-tested: **discovered
models locate the invariants of healthy operation (which counts matter,
where rhythms exist, which zones own them); calibrated interpretable
channels hold those invariants; and every detection ships with a name, an
explanation, and a false-alarm guarantee.** Detection breadth now equals
or approaches a strong raw-sensor baseline while keeping the axes the
field actually lacks. Remaining honest opens: PFPU fouling (instrument-
conditional null), moderate fouling grades, RMTEMP +2C, and discrimination
-grade localization (needs faults outside Zone S — TRU's job).

Next: Phase 5 — the cross-replay grammar (null model + engineering-truth
validation pre-registered), then the ICPM paper (abstract Sept 4, paper
Sept 11).
