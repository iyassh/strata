# X17 — onboarding a fourth LBNL system, the dual-duct AHU (pre-registration)

**Written 2026-09-24, after reading the DDAHU documentation (LBNL FDD Data
Sets: Dual Duct Air Handling Unit, 2022-09-01: control sequence, the 114
data points, the fault inventory) and before opening any data file.
Committed before any script runs.**

## What is being tested

The framework's onboarding claim: a new building system is a configuration
directory (sensor map, rules, Brick file, scenario manifest), not code. The
three systems so far (single-duct AHU; parallel and series fan-powered
units) share a family. The dual-duct AHU has two decks (hot and cold), two
coils, two supply fans, three AHU dampers and four zone mixing boxes with
command-only dampers, on a different building (Energy Resource Station,
Des Moines TMY) — a different system type with 55 seeded faults in 15
families, including two the existing systems do not have (static-pressure
sensor bias; unstable control sequences).

## Protocol (fixed here)

1. **Config only.** `configs/lbnl_ddahu/{sensors.yaml, rules.yaml,
   equipment.ttl, scenarios.yaml}` plus a CSV→parquet converter script with
   the same shape as the existing two. No change under `src/` is permitted
   for this test; if one is needed, the test stops and the falsifier below
   fires. The rules reuse the existing kinds only (occupancy, mode, window,
   mismatch, leak, setpoint_deviation, paired_residual, envelope_residual).
2. **Thresholds from documentation and the fault-free year only.** Initial
   values by physics/convention (the same G1 discipline as SDAHU: 0.05
   actuator mismatch, 2 °F setpoint deviation, ±2 °F residual floor);
   validated by the healthy-silence gate on `DualDuct_FaultFree` and
   loosened only on that file's evidence, every change logged in the
   config. Residual bands, frequency bands, oscillation bands, model and
   device thresholds are calibrated on the fault-free year's train days by
   the deployed code, exactly as for the other systems. **No fault file is
   opened until the gates and the healthy-silence gate have passed and this
   config is committed.**
3. **Gates before science.** MD5 duplicates, within-file timestamp
   monotonicity, calendar identity against the fault-free file, raw-file
   rotation, Brick/TTL coverage against the 114 columns, healthy silence.
   Any dataset defect found is recorded in ERRATA.md as E6+ before any
   result is computed.
4. **Scoring.** The deployed pipeline (`scripts/benchmark.py ddahu`,
   `scripts/union_fpr.py ddahu`), unchanged: eight channels, noise gate
   p < 10⁻³, last-8-days-per-month holdout, union minus rate as the deployed
   verdict. Then the conformance ablation read from the scorecard.

## Predictions

- **P1 (onboarding).** The system runs end to end with configuration
  changes only. Onboarding effort recorded: number of sensor mappings,
  rules, and healthy-silence iterations.
- **P2 (gates).** No byte-duplicate files; all 56 files monotonic and
  calendar-identical to the fault-free file; TTL coverage complete.
- **P3 (healthy silence).** Every signature rule is silent on the fault-free
  year after at most three documented threshold adjustments.
- **P4 (false alarms).** The deployed union's holdout false-alarm rate is
  ≤ 10 of 96 days.
- **P5 (detection).** ≥ 60 % of the 55 fault scenarios are detected
  (significant on at least one deployed channel). The three systems so far
  gave 100 %, 77 % and 83 %.
- **P6 (the fouling families).** Of the 12 coil-fouling scenarios, at most 4
  are detected (the pattern on the fan-powered units: 2 of 12).
- **P7 (the null generalises).** No scenario is detected only by the two
  conformance channels (model, device).
- **P8 (new fault families).** The eight static-pressure-bias scenarios are
  detected on ≥ 4 (the pressure setpoint-deviation rule is gated on fan
  status, the controller trusts the biased reading, so detection must come
  from a residual — fan speed against pressure — which the config attempts
  with the existing `paired_residual` kind); the two unstable-control
  scenarios are detected by the oscillation channel.

## Falsifiers (binding)

- **F-X17.a** A `src/` change is required to run → the config-only claim is
  false for this system type; report the change needed and stop.
- **F-X17.b** P4 false → the false-alarm budget does not transfer; report.
- **F-X17.c** Fewer than 40 % of scenarios detected → the detector does not
  transfer to a dual-duct AHU; report.
- **F-X17.d** P7 false (a scenario detected only by conformance) → the
  central null does not generalise; that is a positive finding to be
  examined, not buried.
- **F-X17.e** Any threshold changed after a fault file was opened → the
  result is not blind; report the change and re-run from the committed
  config.

## Artefacts

`outputs/benchmark_v6_ddahu.json`, `outputs/union_fpr_ddahu.json`,
`outputs/week0_audit_ddahu.json` (or the audit's DDAHU block),
`outputs/x17_onboarding.json` (effort ledger, predictions, falsifiers),
guarded by a test pinning fired/unfired falsifiers.
