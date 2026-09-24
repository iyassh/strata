# X25 — statistical repair: out-of-sample conformance thresholds and a uniform noise floor (pre-registration)

**Written 2026-09-24 (plan item A4) before any code is changed or any
scorecard regenerated.**

## The two defects

1. The two conformance channels (unit model, device model) set their
   per-day threshold as the 1 % quantile of fitness on the healthy HOLDOUT
   days — the same days on which every channel's false-alarm rate is then
   reported. Their false-alarm rows are therefore calibration targets, not
   measurements (disclosed since Phase 6; flagged by every review since).
2. The residual and model channels gate significance against a floor of
   one holdout false alarm, `max(fp, 1)/n`, while the rules, frequency and
   oscillation channels use the rule of three, `3/365`. A residual
   scenario can be "detected" with roughly a third of the flagged days the
   rules channel would need.

## The repair (fixed now)

- **Three-way calendar split.** Each month's last 8 days stay the holdout
  (unchanged: every reported false-alarm rate keeps its 96-day universe).
  The 8 days *before* them become a **calibration** slice
  (`detection.calibration_days_per_month: 8`); the rest of the month is
  discovery training. Conformance thresholds (unit and device) are the
  1 % quantile of fitness on the calibration slice; the holdout is then
  out-of-sample for every channel. Band-learning channels (residual,
  frequency, oscillation) keep learning on all non-holdout days, so their
  bands do not change. A config without the key keeps the old behaviour
  (regression prediction below).
- **Uniform floor.** `residual_significant` and `model_significant` use
  `max(fp/n, 3/365)`.

## Predictions

- **P0 (regression).** With the code changed and no config touched, all
  five scorecards regenerate byte-identically.
- **P1 (out-of-sample).** After the key is added to all five configs, the
  model and device holdout false-alarm rows are measurements; the
  artefacts drop the "calibration-target" provenance note.
- **P2 (budget).** The deployed union false-alarm count stays ≤ 10 of 96
  on every system.
- **P3 (counts).** Each system's detected count changes by at most 2, and
  no scenario becomes detected by the conformance channels alone.
- **P4 (floor).** The rule-of-three floor changes the verdict of at most 3
  scenarios across the five systems, all of them scenarios also credited
  to another channel.

## Falsifiers

- **F-X25.a** P2 fails on any system → the conformance channels'
  out-of-sample false-alarm rate breaks the budget; they are removed from
  the deployed union on that system and the paper reports it.
- **F-X25.b** a conformance-only detection appears → the null is revisited
  on that scenario before anything else is written.
- **F-X25.c** a system loses more than 2 detections → the change is
  reported as a detector change, not a repair, with the lost scenarios
  named.

## Artefacts

Regenerated `benchmark_v6_*.json` and `union_fpr_*.json` for all five;
`outputs/x25_statistical_repair.json` (before/after diff per system);
guard `tests/test_x25_statistical_repair.py`.

## Note (2026-09-24, before any run): order of the two changes

P0 is evaluated on the split code alone (calibration key absent, floor
unchanged): SDAHU must regenerate byte-identically. The floor change and the
five config keys are then applied together, and P1–P4 are read off that
"after" state against the committed "before" scorecards.
