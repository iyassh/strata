# X26 — the false-alarm budget on a real building: LBNL field RTU, Site 2 (pre-registration)

**Written 2026-09-24 (plan item C1) after profiling the fault-free stream
only (interval, gaps, ranges, fan schedule) and before any rule is written
or the fault file is opened.**

## The data

LBNL FDD Data Sets: Rooftop Unit, field subset, Site 2 (Colchester CT,
distribution centre, 10-ton RTU, Enerfit FDD instrumentation): 25 points
at one-minute resolution, °C and bar; `Site2_Unfaulted.csv` = 182 clean
days across two summers (2020-07-31 → 09-30, 2021-06-01 → 09-30), ten
gaps longer than five minutes, one of 5,832 hours between the summers;
`Site2_Undercharged40.csv` = 29 days with circuit B at 40 % undercharge
(2020-06-01 → 06-29). No schedule, damper, valve or command point exists;
the fan cycles on demand (off 23:00–04:00, on 90 % of minutes at midday).
This is the only measured fault-free stream in the project.

## What is claimed and what is not

Claimed: a measurement of the deployed detector's false-alarm and abstain
rates on real, noisy, unscheduled data, under the same protocol (bands
learned on training days, thresholds on the calibration slice, false
alarms on the holdout). Not claimed: a detection rate. One fault of one
kind on one unit is a case report; it is scored and described, never
counted.

## Config (from the documentation and the fault-free profile only)

Derived column, documented as the only preprocessing: `FAN_ON` = supply-fan
power > 100 W (the fan idles at 0 W and runs above 1,000 W), mapped to
`OCCUPIED` (1 = fan on) because the unit has no schedule point.
State: fan on/off, compressor on/off (`RTU_COMP_WATT` > 200 W).
Signature/residual channels (all healthy-calibrated): supply − mixed air
with the compressor off and fan on (fan heat); mixed-air envelope between
outdoor and return; condenser-approach residual `REFG_COND_TEMP_1 −
OA_TEMP` with the compressor on; suction-line residual `REFG_SUCT_TEMP_1 −
SA_TEMP` with the compressor on; compressor power per unit of (OA − zone)
temperature difference with the compressor on (op: ratio); supply-air
flow per fan watt (op: ratio). Oscillation on `ZA_TEMP` and
`RTU_SA_TEMP`. Holdout: last 8 days of each of the seven months
(≈ 56 days); calibration slice the 8 before.

## Predictions

- **P1.** Healthy silence within three logged iterations (signature events
  ≤ 3 days on the clean stream).
- **P2 (the budget).** Deployed union false alarms ≤ 10 % of holdout days;
  per-channel and abstain rates reported.
- **P3.** At least one residual channel abstains on ≥ 20 % of holdout days
  (real data has gaps and unconditioned periods); reported, not scored.
- **P4 (case report).** On the undercharge file, the condenser-approach or
  suction residual flags ≥ 50 % of its 29 days; whichever way it goes, it
  is reported as a case, not a detection rate.

## Falsifiers

- **F-X26.a** P2 fails → the budget does not survive real data; the channels
  that break are named and the papers' limitation is rewritten from
  "simulation only" to the measured number.
- **F-X26.b** a `src/` change is needed beyond the derived fan column →
  config-only fails on real data; report.

## Artefacts

`configs/lbnl_rtu_field/`, `scripts/07_convert_rtu_field.py`,
`outputs/week0_audit_rtu_field.json`, `outputs/union_fpr_rtu_field.json`,
`outputs/x26_real_data_budget.json`; guard `tests/test_x26_real_data_budget.py`.
