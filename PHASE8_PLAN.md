# Phase 8 Pre-Registration — X11 branch adjudication, X8 contamination, X5 severity

Committed BEFORE any Phase-8 computation runs (project law). Honesty note
on X11: its expectations are informed by the 2026-08-18 integration
review's audit measurements (fault-branch residual baseline +0.008 °F vs
healthy +1.071 °F). What is pre-registered here is therefore not the
estimate but the ADJUDICATION PROCEDURE, its falsifiers, and the decision
rule — committed before the adjudication itself is computed by our own
instrument.

## X11 — branch-offset adjudication (ERRATA E5)

**Procedure (script `scripts/x11_branch.py`, artifact `outputs/x11_branch.json`):**
1. Recompute the healthy residual band [0.526, 1.372] and healthy
   median-of-daily-medians from data (owning the audit's numbers).
2. Estimate the fault-branch no-fault baseline: median of the five
   concordant estimators {coi_bias_-4 +7.2, coi_bias_-2 +3.6,
   coi_bias_+2 −3.6, coi_bias_+4 −7.2 (each debiased by its nominal
   bias, ±2 °C = 3.6 °F, ±4 °C = 7.2 °F), oa_bias_4 as-is}.
3. Branch offset δ = healthy_median − fault_branch_baseline.
   Corrected band = [lo − δ, hi − δ]; same 0.5 °F exceedance floor.
4. Re-score every SDAHU scenario's residual window days against the
   corrected band; recompute significance against the channel's own
   noise floor exactly as benchmark.py does (p_resid = max(fp,1)/n_hold,
   binomial p < 1e-3).
5. Adjudicated scorecard: a scenario stays detected iff its corrected
   meaningful channels (deployed set — rate stays diagnostic-only)
   remain non-empty.
6. FPU homogeneity battery: for PFPU and SFPU, (a) occupied-minutes/day
   healthy-vs-fault identity on the pipeline's occupancy signal, (b)
   occupied-hours floor check on the primary damper columns, (c)
   supply-air residual medians of fault families with no supply-air-path
   mechanism (rmtemp_bias) must sit inside the healthy band.

**Pre-registered expectations:**
- H-X11.1: five estimator values concordant within 0.1 °F; δ ≈ 1.06 °F.
- H-X11.2: oa_bias corrected flags fall below significance → adjudicated
  scorecard SDAHU 13/14. PCA comparison becomes 60 v 61
  ("near-tie, complementary misses").
- H-X11.3: all four coi_bias scenarios remain significant under the
  corrected band (margins ≥ 2.5 °F).
- H-X11.4: FPU battery clean (no branch markers) on all three legs.

**Falsifiers (fire = report, do not adjudicate):**
- F-X11.a: estimator spread > 0.25 °F (no single branch baseline exists).
- F-X11.b: corrected band still flags oa_bias above the noise floor
  (branch story incomplete — something else moves the residual).
- F-X11.c: any coi_bias scenario loses significance (correction too
  aggressive; procedure wrong).
- F-X11.d: any FPU battery leg fails (FPU results need the same
  treatment; "FPU unaffected" retracted).

**Decision rule:** all four H hold and no F fires → the paper quotes
"14/14 naive; 13/14 after branch correction (ERRATA E5)" and the D2/E1
narratives are reframed. Any F fires → the finding is reported as
unresolved with both numbers carried.

## X8 — training contamination (S3)

**Procedure (script `scripts/x8_contamination.py`, artifact
`outputs/x8_contamination.json`):** for k ∈ {2, 5, 10}% of SDAHU TRAIN
days (deterministic every-Nth-train-day selection, no RNG), replace the
day's rows with the same calendar day from a fault file (same weather
year — the contamination is realistic: "the building was quietly faulty
on those days"). Two contamination sources, run separately:
- WORST CASE: coi_bias_-4 (residual-extreme, −7.2 °F);
- MILD CASE: damper_stuck_010 (rules-visible, residual-quiet).
For each (source, k): recompute the train-only calibrations — residual
band, frequency count-bands, monthly rate bands — and report (a)
threshold/band drift, (b) consequence: window-day coverage of
coi_bias_±2/±4 and healthy-holdout FP under the drifted bands.
No model/device re-discovery (cost; scoped out and stated).

**Pre-registered expectations:**
- H-X8.1: min/max (extreme-value) calibration is maximally
  contamination-sensitive: ONE extreme contaminated day widens the
  residual band to include it. Expect severe band widening in the worst
  case even at k = 2%, with measurable recall loss on coi_bias_±2.
- H-X8.2: the mild case drifts bands little (damper faults barely move
  the supply-air residual).
- H-X8.3: healthy-holdout FP does not increase (bands only widen).

**Falsifiers:**
- F-X8.a: worst-case k = 10% leaves bands unchanged → instrument broken
  (contamination not actually reaching calibration).
- F-X8.b: FP increases under contamination → accounting bug (widened
  bands cannot flag more healthy days).

**Framing rule:** X8 measures a KNOWN property of extreme-value
calibration honestly; the paper's mitigation sentence is the exceedance
floor + the significance gates + (future work) robust quantile
calibration. No spin.

## X5 — severity monotonicity (S6)

**Procedure (script `scripts/x5_severity.py`, artifact
`outputs/x5_severity.json`):** Spearman ρ between severity rank and
deployed alarm-day count (sig_union minus rate-only days), from committed
artifacts only. Ladders (≥3 rungs, FPU only per the integration review —
SDAHU stuck ladders saturate 365/365, coi_leakage is E2-vacuous):
PFPU/SFPU reheat_stuck {0,10,25,50,75,100 as available}, damper_stuck
ladder, coil fouling {minor, moderate, severe} × (airside, waterside),
airflow_bias {±200, ±400} and rmtemp_bias {±2, ±4} as |severity| pairs.
Report ρ per ladder with n, plus the saturation caveat where alarm days
hit the ceiling; per-day autocorrelation caveat standard.

**Pre-registered expectations:**
- H-X5.1: ρ ≥ 0 on every ladder (no ladder should be significantly
  ANTI-monotone).
- H-X5.2: fouling ladders (the graded physics) show ρ > 0.5.

**Falsifier F-X5.a:** any ladder significantly anti-monotone → report as
a finding against the dose-response narrative.

## X7 — 15-min downsample (pre-registration appended 2026-08-18, before running)

Capacity permits; running after X5. **Procedure** (`scripts/x7_downsample.py`
→ `outputs/x7_downsample.json`): take every 15th row (data is 1-min) of
each healthy year and one fault file per family; recompute rules
(signature-event days), residual (band recalibrated ON the 15-min data,
train-only, same floors), and frequency (bands rebuilt) — no model/device
re-discovery (scoped out, stated). Compare per-scenario day-coverage
against the 1-min artifacts.

**Pre-registered expectations:**
- H-X7.1: healthy silence preserved at 15-min (0 signature days on all
  three healthy years).
- H-X7.2: rules fault coverage within 10% of the 1-min day counts
  (sustained_min thresholds are minute-denominated and interval-aware).
- H-X7.3: residual coverage of the bias families ≈ unchanged (daily
  medians are robust to 15× thinning); band position within 0.2 °F.

**Falsifiers:**
- F-X7.a: any healthy year gains signature days at 15-min (rules channel
  not sampling-robust → transfer claim scoped to 1-min data).
- F-X7.b: any family's coverage drops > 25% → that channel's portability
  claim carries a sampling-rate caveat.

## Order and audit

X11 → X8 → X5 → single hostile audit of the whole phase → doc reframes
(D2/E1/F1/Part V/ERRATA E5) land only after the audit passes.
