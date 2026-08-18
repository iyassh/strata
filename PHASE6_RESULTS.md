# Phase 6 Results — The Joint False-Alarm Budget and the STRATA Detector
## (final, post-hostile-audit)

Closes MASTER_PLAN gaps S1 (no union FPR anywhere), S2 (no single detector
definition), S8 (margin-policy uniformity). Pre-registered expectations were
the cross-phase auditor's independently computed numbers; falsifier: any
disagreement, or any scenario carried solely by the rate channel, stops the
demotion. A hostile audit then attacked the finished phase; all six of its
required fixes are applied below and marked [audit]. Artifacts:
`outputs/union_fpr_{sdahu,pfpu,sfpu}.json` (script: `scripts/union_fpr.py`;
guards: `tests/test_union_fpr.py`).

## The problem this phase fixes

Every channel was individually calibrated with its own noise floor, but no
artifact measured what a deployed operator actually lives with: the OR of
all channels on healthy data. The scorecard footnote "healthy false-alarm
days: 0" is the RULES channel only. Computed honestly, on the healthy
year's shared calendar holdout (last 8 days/month, 96 days):

| channel | SDAHU | PFPU | SFPU | threshold provenance |
|---|---|---|---|---|
| rules | 0/96 | 0/96 | 0/96 | train-only; out-of-sample |
| residual | 0 | 2 | 0 | train-only; out-of-sample |
| model | 0 | 1 | 1 | **holdout-quantile: calibration target** |
| device | 0 | 0 | 3 | **holdout-quantile: calibration target** |
| absence | 0 | 0 | 0 | train-only; out-of-sample |
| frequency | 1 | 1 | 1 | train-only; out-of-sample |
| **seasonal rate** | **14** | **7** | **0** | train-only; out-of-sample |
| oscillation | 0 | 2 | 0 | train-only; out-of-sample |
| **UNION (all 8)** | **15/96 = 15.6%** | **12/96 = 12.5%** | **4/96 = 4.2%** |
| **UNION minus rate** | **1/96 = 1.0%** | **5/96 = 5.2%** | **4/96 = 4.2%** |

One false alarm every ~6 days on SDAHU — a cry-wolf rate that would sink
the trust narrative. The seasonal rate channel is the dominant cause
(14 of SDAHU's 15 days; 7 of PFPU's 12). The 14 SDAHU rate dates were
verified by an independent computation route in the audit.

**[audit] Threshold-provenance disclosure (the audit's most important
finding):** `build_detector` and `build_device_detector` set their
thresholds as a quantile OF THE HOLDOUT itself. The model and device rows
above are therefore the calibration target (~1% by construction), not
out-of-sample measurements — SFPU's device 3/96 is exactly the 1% quantile
of its 384 holdout cases surfacing as days. Honest decomposition of the
deployed numbers: **SDAHU 1/96 genuine** (freq); **PFPU 5/96 = 4 genuine
(resid 2, freq 1, osc 2, one overlap) + 1 by-construction (model)**;
**SFPU 4/96 essentially by-construction (model 1 + device 3), 1
overlapping freq day genuine.** No healthy data unseen by every
calibration step exists on any LBNL system.

**[audit] Per-channel exposure:** the 96-day denominator includes days a
channel structurally cannot alarm on. Residual is evaluable on 36/96
(SDAHU) and 41/96 (PFPU/SFPU) holdout days; rate windows exist on 80/96
(SDAHU) and 90/96 (FPU); SDAHU has only 79/96 occupied holdout days.
"0/96" bounds a channel only over its evaluable days. Exposure counts are
embedded in each artifact.

## The STRATA detector (single definition, first stated here)

> **The STRATA detector** = OR of the significance-gated channels
> {rules, residual, model conformance, device conformance, absence,
> frequency, oscillation}. The **seasonal rate channel is diagnostic-only**:
> it corroborates and explains an alarm another channel raised; it never
> raises one alone.

Deployed joint false-alarm budget: **1.0% (SDAHU), 5.2% (PFPU), 4.2%
(SFPU)** of healthy holdout days — with the decomposition caveat above.

## Why the demotion is free (verified, not argued)

Checked as hard assertions in `scripts/union_fpr.py` against the committed
v12 artifacts — under the **significance-gated, device-pessimistic** check
([audit] C-i/C-ii fix: coverage may only come from channels that passed
their significance gates for that scenario; the device channel is excluded
from coverage entirely because its stored day list merges insignificant
devices; a scenario whose coverage depended on absence/device alone would
be flagged for manual review, not passed). Violations found: **0**.

1. **No scenario is carried solely by rate.** Rate is significant on 13
   scenarios (6 SDAHU, 1 PFPU, 6 SFPU); every one has another
   independently significant channel. Scorecards unchanged:
   **14/14, 23/30, 24/29.**
2. **No TTD is set by rate.** Every rate-significant scenario's first
   significant alarm day is covered by significant rules (12 scenarios)
   or significant residual (SA bias −4C). All TTDs (1–2 days) unchanged.
   Structurally, 30-day rolling rate windows cannot flag before ~day 30.
3. **What demotion costs — reported, not hidden:** rate contributes unique
   mid-year *alarm days* on some scenarios (e.g. 116 rate-only days on
   SA bias −4C). Those remain available as corroboration/diagnosis; they
   simply no longer page anyone.

**[audit] Post-selection defense (split-half probe):** the demotion was
decided after observing this holdout, so the deployed FPR is a
post-selection estimate. The probe splits the holdout by month parity,
re-makes the decision on each half, and quotes deployed FPR on the
opposite half: on SDAHU and PFPU rate is the worst channel on BOTH halves
(deployed 0/48 & 1/48; 3/48 & 2/48) — the decision is split-half stable
and the day-level selection optimism is second-order. On SFPU rate has 0
holdout FPs; demotion is a no-op there (4.2% either way). The all-8 union
is always reported alongside.

## Novelty claim ([audit] reworded — the original was overclaimed)

NOT claimed: "first joint FPR budget in building FDD" — tool-level
false-positive rates for complete multi-rule detectors exist in the AFDD
evaluation literature (Frank et al. 2019; the LBNL/Granderson commercial
FDD evaluations). Claimed instead: **an explicit per-channel decomposition
of the joint alarm budget, with a detector-definition decision (channel
demotion) driven by that budget and verified zero-cost against the fault
scorecards, inside a discovered-process-model FDD stack.**

## Margin-policy uniformity (gap S8) — [audit] corrected account

SDAHU's config lacked ONE of the two floor lines the FPU configs carry:
`residual_min_exceedance: 0.5` was already present (since Phase 4, audit
C1); only `residual_min_band_width: 0.5` was missing and was added. (The
first Phase 6 commit wrongly stated both were added and introduced a
duplicate exceedance key — caught by the audit, both fixed.) Verified
numeric no-op: full SDAHU benchmark re-run is **byte-identical** to the
committed v12 artifact (independently reproduced by the auditor). "ONE
margin policy across all systems" is now literally true in the configs.

## Standing caveats (embedded in the artifacts, quoted in the paper)

1. Healthy negatives are the calibration year's own calendar holdout; no
   independent healthy negative exists on any LBNL system (D2); per-day
   autocorrelation makes binomial p-values on these counts optimistic.
2. Model/device rows are calibration targets, not measurements (above).
3. The deployed FPR is a post-selection estimate; all-8 union and
   split-half probe reported alongside.
4. Exposure per channel differs from the 96-day denominator (above).

## Ledger

- **L23**: a system of individually calibrated detectors has no collective
  guarantee until the union is measured. "Every channel has an FP floor"
  does not compose into "the detector has an FP floor" — the union must be
  a first-class, tested artifact.
- **L24** (from the hostile audit): a threshold quantile-fit ON the holdout
  makes that holdout's FP rate a calibration target, not a measurement —
  the same day-set cannot both set a threshold and certify it. Any table
  mixing calibration-target rows with out-of-sample rows must label them.
  (Structural fix — a three-way discover/calibrate/test split — goes to the
  toolkit facade design, Phase 9.)
- **L25**: a verification check must enforce the property it names, at the
  strictness the property requires — my first demotion check accepted
  coverage from insignificant channels; the audit proved the property held
  anyway, but the GUARD was weaker than the CLAIM. Guards are part of the
  result.
