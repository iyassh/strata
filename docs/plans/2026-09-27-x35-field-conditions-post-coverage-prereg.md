# X35 — field conditions on the post-coverage configurations, all five systems (pre-registration)

**Written 2026-09-27 before any perturbed file is scored. Configurations as of commit 36b9e6e.**

## Why

X31 injected sensor error, change-of-value logging and schedule shifts into three
systems under the configurations of 2026-09-24. The coverage series (X33) then
added 73 residual rules, several with healthy bands only 0.01–0.02 units wide
(zone-fan specific power, outdoor-air flow fraction, mixing-box redundancy), and
five of its sixteen recoveries sit less than one band width outside the healthy
extremes. The robustness claim in the papers is dated to before the series. X35
repeats X31's four conditions plus the clean reference arm on all five simulated
systems under the current configurations, through the repaired facade
(`scripts/x31_field_conditions.py`, unchanged; arms: clean, field_noise,
cov_gaps, schedule, combined; ledger `scripts/x31_ledger.py` extended to five
systems and written to `outputs/x35_field_conditions.json`).

## Predictions

- **P1 (budget).** Deployed false alarms ≤ 10 of 96 and ≤ clean + 3 on every system and condition.
- **P2 (noise, COV).** Detected count within −4 of the clean arm under field_noise and cov_gaps on every system (X31 allowed −3; the tighter bands justify one more).
- **P3 (edge recoveries).** At least two of the five edge recoveries (PFPU airside moderate/severe, PFPU +2 °C bias, SFPU airside moderate, DDAHU heating waterside minor) are lost under field_noise; they are named.
- **P4 (schedule).** Detected count within ±3 of clean under schedule (X31 saw +3 from a band-setting day becoming a holiday; the same mechanism can act on more bands now).
- **P5 (combined).** Within −6 of clean.
- **P6 (clean arm).** The clean arm reproduces the scorecard's deployed-channel count on every system (14, 26, 25, 50, 43) and its false alarms without the absence channel.

## Falsifiers

- **F-X35.a** P1 fails → the budget does not survive that condition on the post-coverage configuration; the rule responsible is named and the coverage-series claim is qualified for it.
- **F-X35.b** P2 or P5 fails → detections lost beyond the bar are named; the count claim is qualified.
- **F-X35.c** P6 fails → facade defect, investigated first.
- A failed P3 or P4 is a wrong prediction.

## Artefacts

`outputs/x31_field_conditions_<system>.json` regenerated for all five systems (the X31 artefacts of 2026-09-24 are kept under `outputs/x31_archive/` for the record), `outputs/x35_field_conditions.json`; guard `tests/test_x35_field_conditions.py`.
