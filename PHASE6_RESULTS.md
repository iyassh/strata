# Phase 6 Results — The Joint False-Alarm Budget and the STRATA Detector

Closes MASTER_PLAN gaps S1 (no union FPR anywhere), S2 (no single detector
definition), S8 (margin-policy uniformity). Pre-registered expectations were
the cross-phase auditor's independently computed numbers; falsifier: any
disagreement, or any scenario carried solely by the rate channel, stops the
demotion. Artifacts: `outputs/union_fpr_{sdahu,pfpu,sfpu}.json`
(script: `scripts/union_fpr.py`; guards: `tests/test_union_fpr.py`).

## The problem this phase fixes

Every channel was individually calibrated with its own noise floor, but no
artifact measured what a deployed operator actually lives with: the OR of
all channels on healthy data. The scorecard footnote "healthy false-alarm
days: 0" is the RULES channel only. Computed honestly, the naive 8-channel
union false-alarms on the healthy year's calendar holdout at:

| channel | SDAHU | PFPU | SFPU |
|---|---|---|---|
| rules | 0/96 | 0/96 | 0/96 |
| residual | 0 | 2 | 0 |
| model | 0 | 1 | 1 |
| device | 0 | 0 | 3 |
| absence | 0 | 0 | 0 |
| frequency | 1 | 1 | 1 |
| **seasonal rate** | **14** | **7** | **0** |
| oscillation | 0 | 2 | 0 |
| **UNION (all 8)** | **15/96 = 15.6%** | **12/96 = 12.5%** | **4/96 = 4.2%** |
| **UNION minus rate** | **1/96 = 1.0%** | **5/96 = 5.2%** | **4/96 = 4.2%** |

One false alarm every ~6 days on SDAHU — a cry-wolf rate that would sink
the trust narrative. The seasonal rate channel is the entire problem
(14 of SDAHU's 15 days; 7 of PFPU's 12).

## The STRATA detector (single definition, first stated here)

> **The STRATA detector** = OR of the significance-gated channels
> {rules, residual, model conformance, device conformance, absence,
> frequency, oscillation}. The **seasonal rate channel is diagnostic-only**:
> it corroborates and explains an alarm another channel raised; it never
> raises one alone.

Deployed joint false-alarm budget: **1.0% (SDAHU), 5.2% (PFPU), 4.2%
(SFPU)** of healthy holdout days.

## Why the demotion is free (verified, not argued)

From the committed v12 artifacts, checked as hard assertions in
`scripts/union_fpr.py` (violations found: **0**):

1. **No scenario is carried solely by rate.** Rate is significant on 13
   scenarios (6 SDAHU, 1 PFPU, 6 SFPU); in every one, at least one other
   channel is independently significant. Detection scorecards are
   unchanged: **14/14, 23/30, 24/29.**
2. **No TTD is set by rate.** The first significant alarm day of every
   rate-significant scenario is covered by a non-rate channel (checked
   directly per scenario). Structurally, the 30-day rolling rate windows
   cannot flag before ~day 30; all measured TTDs are 1–2 days.
3. **What demotion costs — reported, not hidden:** rate contributes unique
   mid-year *alarm days* on some scenarios (e.g. 116 rate-only days on
   SA bias −4C, 80 on VAV airflow −200CFM). Those days remain available
   as corroboration/diagnosis; they simply no longer page anyone.

This table is the G9 deliverable: to our knowledge the first jointly
FPR-budgeted multi-channel detector reported for building FDD (claim to
be tempered in the paper as "we found no prior joint alarm budget in the
building-FDD literature").

## Margin-policy uniformity (gap S8)

SDAHU's config lacked the two floor lines the FPU configs carry. Both
added (`residual_min_band_width: 0.5`, `residual_min_exceedance: 0.5`);
pre-registered expectation: numeric no-op (SDAHU's calibrated band is
0.846 °F wide; bias-fault margins ≫ 0.5 °F). Verified by full SDAHU
benchmark re-run: the regenerated artifact is **byte-identical** to the
committed v12 artifact. Falsifier did not fire. "ONE margin policy across
all systems" is now literally true in the configs, not just in prose.

## Standing caveats (embedded in the artifacts)

- The healthy negatives are the calibration year's own calendar holdout
  (last 8 days/month). Train-only min/max thresholds never saw those days,
  but they share the building, year, and weather with training. **No
  independent healthy negative exists on any LBNL system** (D2).
- Per-day autocorrelation makes any binomial p-value on these counts
  optimistic; the table reports raw proportions, not significance stars.
- SFPU's device channel (3/96) is the largest non-rate contributor and is
  already per-device Bonferroni-gated at scenario level; at deployment,
  the per-scenario significance gates (not raw day-flags) decide pages.

## Ledger

- **L23**: a system of individually calibrated detectors has no collective
  guarantee until the union is measured. "Every channel has an FP floor"
  does not compose into "the detector has an FP floor" — the union must be
  a first-class, tested artifact (here: union_fpr.json + regression guards
  that fail if a future change raises the deployed FPR above the quoted
  ceilings or makes a scenario rate-only).
