# X36 — quantile bands instead of extreme bands: what the five edge recoveries cost (pre-registration)

**Written 2026-09-27 before any score is computed. Configurations as of 36b9e6e.**

## Why

The residual bands are `[min, max]` over training-day scores, widened to a sensor
floor. X31 showed a band edge is set by single days; the series analysis found five
of the sixteen coverage recoveries less than one band width outside the healthy
extremes. X36 asks what happens under a calibration that does not depend on single
days: bands at the 2nd and 98th percentiles of the training-day scores (same floors),
for every residual rule on every system, evaluated through the facade against the
same holdout. This is an alternative calibration arm, not an adoption: the deployed
detector is unchanged unless a separate pre-registration adopts it.

## Design

- `scripts/x36_quantile_band.py`: monkeypatches `calibrate_band` to use quantiles
  (q = 0.02 / 0.98) of the training-day scores, fits the facade on each fault-free
  year, scores every scenario and the holdout, alignment channels off (as X31),
  and diffs against the clean facade run of X35 (or, if X35 has not closed, a
  clean arm computed here).
- Tighter bands raise both detections and false alarms; the pre-registered
  reading is the *net* effect and which scenarios move.

## Predictions

- **P1.** Deployed false alarms (without absence) rise by ≤ 3 days per system and stay ≤ 10 of 96.
- **P2.** The five edge recoveries (PFPU airside moderate and severe, PFPU +2 °C bias, SFPU airside moderate, DDAHU heating waterside minor) all remain detected under quantile bands (a narrower band cannot lose them).
- **P3.** At least two currently missed scenarios become detected on some system (named).
- **P4.** No currently detected scenario is lost.

## Falsifiers

- **F-X36.a** P1 fails → quantile bands are not a budget-safe alternative; reported.
- **F-X36.b** P4 fails → named; a narrower band losing a detection would mean the band floor, not the band, was carrying it.
- A failed P2 or P3 is a wrong prediction.

## Artefacts

`outputs/x36_quantile_band.json`; guard `tests/test_x36_quantile_band.py`.
