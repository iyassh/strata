# X22 — positive control: does the conformance channel fire on genuine order violations? (pre-registration)

**Written 2026-09-24 after the review round (docs/plans/2026-09-24-review-verdict-and-improvement-plan.md, A1) and before any injected log is scored. Committed before the script is written.**

## Why

The process-mining null (0 of 168 scenarios detected by the conformance
channels alone, five systems) can be read two ways: the domain's faults do
not change event order, or the instrument cannot see order. The existing
reversal probe (grammar.py) reports only mean fitness on three systems.
This test asks the deployed question: under the deployed detector, its
calibrated threshold and its significance gate, does the model channel
flag days whose event ORDER has been genuinely violated?

## Procedure (fixed now)

For each of the five systems (SDAHU, PFPU, SFPU, DDAHU, FCU):
1. Fit the unit-stratum detector exactly as deployed (`build_detector`:
   inductive miner on training days, threshold = 1 % quantile of holdout
   fitness). Take the healthy HOLDOUT days' state traces (the days that
   define the channel's false-alarm floor; 96 per system).
2. Perturb every holdout trace with one of five operations, each at graded
   strength, seed 7:
   - **reverse**: the whole day's trace reversed (strength n/a);
   - **swap-k**: k randomly chosen adjacent pairs of *distinct* activities
     swapped, k ∈ {1, 2, 4, 8};
   - **skip-k**: k randomly chosen state events deleted, k ∈ {1, 2, 4};
   - **skip-start**: every occurrence of the system/occupancy start event
     (`system_started`, or `night_cycle_ended` where the alphabet has no
     `system_started`) deleted;
   - **dup-block**: a random contiguous block of 3 events duplicated in
     place.
   A trace shorter than 2 events is left as is and counted.
3. Score with `classify_days` (fitness < threshold ⇒ flagged) and gate with
   `model_significant(flagged, n_days, holdout_fp, holdout_n)` — the
   deployed rule, where `holdout_fp` is the unperturbed holdout's flag count
   (0/1/1/0/1 on the five systems).

## Predictions

- **P1 (reverse).** Significant on SDAHU, DDAHU and FCU (nets whose
  start/stop structure encodes order); NOT significant on PFPU and SFPU
  (nets known from the reversal probe to be order-permissive).
- **P2 (skip-start).** Significant on every system whose net carries the
  start activity as obligatory (DDAHU and SFPU by X20's Q_obligatory; the
  others are predicted not significant).
- **P3 (swaps).** Flagged fraction rises monotonically in k on every system;
  significant by k = 8 on at least three systems.
- **P4 (skips).** Flagged fraction rises in k; single skips are absorbed on
  the loop-heavy nets (PFPU, SFPU).
- **P5 (dup-block).** Not significant on any system (loops absorb
  repetition; this is the known blind spot).

## Falsifiers (binding)

- **F-X22.a** reverse and skip-start are BOTH non-significant on every one
  of the five systems → the instrument is blind to order at the deployed
  gate; the null in ERPM cannot be attributed to the domain and the paper
  must say the channel was not shown to work.
- **F-X22.b** P1 fails in the other direction (PFPU or SFPU significant
  under reversal) → the reversal probe's "order-permissive" reading is
  wrong; correct it in ERPM.
- **F-X22.c** P3 fails (no monotone rise on ≥ 2 systems) → alignment
  fitness is not a graded order detector even where it detects reversal;
  report.

## What passes mean

If P1 holds, the ERPM null is instrument-validated on the three systems
where reversal fires (the channel can see order; the faults do not change
it) and, on the two fan-powered units, "cannot see order by construction"
is the honest statement, already the paper's third reading. Either
outcome is reported.

## Artefacts

`outputs/x22_positive_control.json`; guard `tests/test_x22_positive_control.py`.
