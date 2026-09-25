# X32 — profile-deviation events: the healthy day as a time-of-day envelope, deviations from it as events (pre-registration)

**Written 2026-09-25 (user's proposal: "the graph of a normal day; a deviation from it is an event") before any event is computed.**

## Why

X14 turned quantities into events with one fixed band per signal for the whole
year, and the model channel then flagged 18 and 21 healthy days in 96. A
healthy year varies a lot; a healthy *9 am on a winter weekday* varies much
less. X32 builds, for every continuous mapped signal, a healthy envelope per
(month, weekday/weekend, hour of day) from the training days of the X25 split,
and emits an event when the signal leaves that envelope for a sustained
stretch, with its direction. Three things are then measured.

## Design (fixed now)

- **Signals:** every mapped sensor whose canonical name marks a temperature,
  flow, position, pressure or power (setpoints, status and command columns
  excluded, as in X31's `family`).
- **Envelope:** per signal, per bucket (month, weekday-type, hour), the 2.5th
  and 97.5th percentiles of the training-day minutes; a bucket with fewer than
  300 minutes inherits the same hour across all months of that weekday-type.
- **Events:** `<SIGNAL>_above_entered` / `_exited` and `_below_entered` /
  `_exited` when the signal is outside the envelope for at least 30
  consecutive minutes; deviation events join the state alphabet
  (`night_cycle`, `heating_active`, …) with a `dev:` prefix; the fault-signature
  alphabet is untouched (the wall stands).
- **Arm A, counts:** per day, the number of deviation events per signal;
  healthy band = [min, max] over training days, per signal; a day is flagged
  if any signal exceeds its band; false alarms on the holdout; scenario
  detection through `model_significant` against the arm's own holdout null.
- **Arm B, order:** inductive miner (noise 0.2) on training days of the
  state + deviation log; threshold at the 1 % quantile of per-day token-replay
  fitness on the calibration slice (alignments attempted under a 15-minute
  cell budget, reported as not evaluated if exceeded); same gate.
- **Arm C, cascade:** on every scenario Arm A detects, the median minute of
  each signal's first deviation over the scenario's flagged days, giving the
  order in which signals leave their envelopes — a diagnosis, not a detection.
- **Systems:** SDAHU, PFPU, SFPU (the misses of X30 are 8 + 8 on the fan-
  powered units); DDAHU and FCU if compute allows.
- **Gate:** X25 three-way split; holdout = last 8 days per month; nothing sees
  fault data before scoring.

## Predictions

- **P1 (budget).** Arm A's holdout false alarms ≤ 10 of 96 on every system.
- **P2 (new detections).** Arm A detects at least one scenario the deployed
  detector misses on PFPU or SFPU among the non-fouling misses (room-temperature
  bias +2/+4 °C, VAV fan flow restriction).
- **P3 (the fouling wall).** Reheat-coil fouling stays missed: its recorded
  signals sit within ~3 % of healthy, inside any envelope that passes P1.
- **P4 (order adds nothing).** Arm B detects no scenario Arm A does not.
- **P5 (cascade).** On the stuck-damper scenarios Arm A detects, zone airflow
  leaves its envelope before the reheat valve does (median first-deviation
  minute).

## Falsifiers

- **F-X32.a** P1 fails → the envelope alphabet is not adoptable as written;
  reported with the signals responsible.
- **F-X32.b** P4 fails → order among deviation events carries detection
  information the counts do not; the scenario and instrument are named and
  adoption goes through its own pre-registration.
- **F-X32.c** P3 fails → the envelope sees fouling; a positive surprise,
  reported as such.
- A failed P2 or P5 is reported as a wrong prediction.

## Artefacts

`outputs/x32_profile_deviation_events.json`; guard
`tests/test_x32_profile_deviation_events.py`.
