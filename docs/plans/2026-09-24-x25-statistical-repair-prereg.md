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

## Amendment 1 — 2026-09-24, after step 3 and before step 4

**Step 2's floor was wrong** (3/365 at every n; looser than max(fp, 1)/n at
n = 96) and **step 3's is inconsistent**: max(fp, 3)/n with the residual
gate's n being holdout *window-days pooled over channels* (509 on DDAHU,
124 on SFPU), so the same rule is 3/509 = 0.006 on one system and
3/124 = 0.024 on another, and looser than step 2 wherever the pool exceeds
365 days. That is why step 3 *gained* a DDAHU scenario (hot-deck static
bias −0.4, 8 flagged days of 279) while *losing* an SFPU one (reheat-coil
airside-severe fouling). The residual channel's flag is a per-day OR over
its channels, so its null must be per day too.

**Step 4 (fixed now):** the residual gate's holdout false-alarm count and
denominator are the number of holdout *days* flagged by any residual
channel and the number of holdout days on which any channel was
evaluable (the same quantities the false-alarm artefact reports), with
the floor max(fp, 3)/n on those days. Nothing else changes. All five
systems regenerate; the step-3 → step-4 diff is recorded as
`outputs/x25_step4_perday.json`; the ledger against the pre-X25 state is
regenerated. Predictions P2 and P3 apply to the step-4 state; the
step-3 SFPU loss and DDAHU gain are expected to reverse or persist and
either is reported. No detection may become conformance-only.
