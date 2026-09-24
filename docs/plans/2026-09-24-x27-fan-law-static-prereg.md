# X27 — a fan-law virtual static for the dual-duct unit's static-pressure-bias misses (pre-registration)

**Written 2026-09-24 (plan item B2) before any code or config change.**

## Why

Three of eight static-pressure sensor-bias scenarios on the dual-duct unit
are missed (cold +0.2 in.wg, hot −0.2, hot −0.4). A biased static sensor
is unobservable from the static itself — the loop holds the reading at
setpoint — and shows up in fan speed and power instead. The existing
`cold_static_per_speed` / `hot_static_per_speed` residuals use the ratio
static ÷ speed, a proxy the config itself calls crude; the fan law says
static ∝ speed² at constant system resistance, so the ratio static ÷ speed²
is the quantity that stays constant on a healthy unit and shifts under a
bias (the domain review's item 3).

## Definition (fixed now)

New `paired_residual` option `op: ratio_sq`: residual = a / b², undefined
where b ≤ 0 (mirrors `op: ratio`). Two new residual channels on DDAHU,
`cold_static_per_speed2` (a = `CSA_STATIC`, b = `CSF_SPEED`) and
`hot_static_per_speed2` (a = `HSA_STATIC`, b = `HSF_SPEED`), with the same
gates and occupancy as the existing per-speed rules, daily-median scored,
band learned on training days with floors 0.05 in.wg per unit speed² and
0.05 exceedance. The existing per-speed rules stay (so nothing already
detected can be lost by replacement). No other config changes.

## Predictions

- **P0 (regression).** Code change with no config touched: all five
  scorecards byte-identical.
- **P1 (healthy).** The two channels' healthy-holdout false alarms ≤ 1 day
  each; deployed union ≤ 10 of 96 on DDAHU.
- **P2 (target).** Static-bias detections rise from 5 to ≥ 7 of 8.
- **P3 (no loss).** No previously detected DDAHU scenario loses detection.

## Falsifiers

- **F-X27.a** P1 fails → the channels are removed and the failure
  reported.
- **F-X27.b** P2 fails (≤ 6 of 8) → the fan-law form does not resolve the
  small biases on this unit; reported, channels kept only if P1/P3 hold.
- **F-X27.c** P3 fails → investigate before anything is written.

## Artefacts

Regenerated `benchmark_v6_ddahu.json`, `union_fpr_ddahu.json`;
`outputs/x27_fan_law_static.json`; guard `tests/test_x27_fan_law_static.py`.
