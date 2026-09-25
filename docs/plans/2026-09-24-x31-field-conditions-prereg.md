# X31 — field conditions the jitter test did not cover: sensor error, feedback resolution, change-of-value logging with gaps, and schedule shifts (pre-registration)

**Written 2026-09-24 (plan item C3; the domain review's failure modes 2, 3
and 5) before any perturbed file is scored.**

## Why

X9/X10 injected i.i.d. per-sample jitter at sensor precision and found the
detector unmoved. Real buildings differ from simulation in four other ways
that no experiment has touched: field duct sensors err by ±0.9 °F, damper
feedback is quantised to 5 % steps, building automation systems log by
change-of-value (stale repeats, irregular intervals, gaps), and schedules
move (optimum start, holidays). X26 measured the budget on one real unit
but could not separate these effects. X31 injects each one, and all of
them together, into the simulated files, then re-fits and re-scores the
deployed detector.

## Conditions (fixed now; common random numbers per file across arms)

- **field_noise**: temperatures + N(0, 0.9 °F), flows × (1 + N(0, 0.02)),
  positions quantised to 0.05 steps then + N(0, 0.01), clipped to [0, 1].
- **cov_gaps**: change-of-value logging — a sample is kept only when the
  signal moves by more than a deadband (temperatures 0.5 °F, positions
  0.02, flows 2 %) and the last value is carried forward on the one-minute
  grid; plus 2 % of minutes removed in 30-minute blocks (gaps). Applied
  per column, so columns update at different instants, as in a BAS trend.
- **schedule**: on a seeded 20 % of weekdays the occupancy signal starts
  30 minutes earlier (optimum start); six seeded weekdays a year are
  holidays (occupancy 0 all day). The same calendar is applied to every
  file of a system (a schedule is a property of the building).
- **combined**: all three.

Systems: SDAHU, DDAHU, FCU (three equipment classes; the fan-powered
units are added if compute allows). Detector: the deployed facade
(`pipeline.fit` / `evaluate`) re-fitted on the perturbed fault-free year,
under the X25 gate, without the alignment channels (their removal changes
no clean detection; X9/X10 Amendment 3 established their cost on
inflated logs); false alarms on the last-8 holdout.

## Predictions

- **P1 (budget).** Deployed false alarms ≤ 10 of 96 and ≤ 2× the clean
  count + 2 on every system and condition.
- **P2 (noise, COV).** Detected count within −3 of clean under field_noise
  and cov_gaps.
- **P3 (schedule).** Detected count within ±1 of clean; false alarms
  ≤ clean + 2. The channel most likely to break is absence (a holiday is a
  silent scheduled day at the data's level even though the occupancy
  signal is 0) — stated as the risk.
- **P4 (combined).** Detected count within −4 of clean; P1 holds.

## Falsifiers

- **F-X31.a** P1 fails on any condition → the budget does not survive that
  condition; the channel responsible is named and the deployment claim is
  qualified for it.
- **F-X31.b** P2 or P4 fails → the detections lost are named; the count
  claim is qualified.
- **F-X31.c** a condition cannot be scored → reported as not evaluated.

## Artefacts

`outputs/x31_field_conditions.json`; guard `tests/test_x31_field_conditions.py`.

## Amendment 1 (2026-09-24 evening, after the first pass; written before the re-run)

The first pass (all four conditions on the three systems, plus the clean
scorecard as comparator) showed every DDAHU condition detecting 50 of 55
against the scorecard's 45, with the same four scenarios gained under every
condition including the schedule shift, which touches only the occupancy
signal. That is not a perturbation effect. Cause, found in the library
facade (`src/strata/core/pipeline.py`, `fit`): its residual noise floor was
still the pooled channel-day count of X25 step 3 (3/509 on DDAHU), while
`scripts/benchmark.py` had been moved to the per-day null of step 4 (3/124).
The facade therefore ran a looser gate than the published scorecards — a
gap between the library and the scripts that the regression gate does not
see, because the gate regenerates artefacts through the scripts.

Changes: (1) the facade's residual null is now the per-day OR over channels,
identical to the benchmark's; guard `tests/test_facade_residual_null.py`
asserts the facade's `residual_holdout` equals the scorecard's
`residual_holdout_fp` on SDAHU and DDAHU. (2) A `clean` arm — the same
facade on the unperturbed files — is the comparator for every condition,
instead of the scorecard count; both are reported. (3) All arms are re-run
on all three systems. Predictions P1–P4 are unchanged and are now tested
against the clean arm's count. Prediction for the clean arm: detections
equal the scorecard's deployed-channel count (14, 45, 40) and false alarms
equal its deployed-union count without the alignment channels (1, 3, 3);
any difference is reported as a facade defect, not as a condition effect.
