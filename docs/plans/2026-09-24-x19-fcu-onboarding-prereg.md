# X19 — a fifth LBNL system, the fan coil unit (pre-registration)

**Written 2026-09-24 after reading the FCU documentation (LBNL FDD Data
Sets: Fan Coil Unit; 29 points; 48 faults in 17 families; one fault-free
year; Des Moines TMY) and before opening any data file. Committed before any
script runs. Protocol identical to X17 (config only; thresholds from
documentation and the fault-free year; gates before science; deployed
pipeline unchanged; nothing under `src/`).**

## Why a fifth system

X17 showed the detector and the null transfer to a dual-duct AHU. The fan
coil unit is a different equipment class again — a single-zone four-pipe
unit with a three-speed fan, both coils, one outdoor-air damper, no duct
static, no terminal units — and it brings four fault families none of the
first four systems have: filter restriction, outdoor-air inlet blockage,
fan outlet blockage, and reverse-acting control. It also has a heating
coil, so it is scorable in the sealed transfer test, whose pool would
grow to four buildings (floor 1/4! = 0.042); that re-run is a separate
pre-registration (X20) and is not part of this test.

## Config sketch (from the documentation only)

State alphabet: operate/setback/shutdown (`FCU_CTRL`), fan on and speed
band (`FCU_SPD`), cooling and heating valve modes, OA damper above minimum,
economizer-style OA window. Signature: damper and both valves' command
mismatch and leak; discharge-air residuals against mixed air with each
coil off and the fan on (`FCU_DAT − FCU_MAT`); mixed-air envelope between
outdoor and return air; both coils' water-side ΔT residuals; zone-temperature
tracking against the active setpoint; a discharge-flow-per-fan-speed ratio
residual for the three airflow-restriction families (fault-informed only in
the sense that the documentation names them; thresholds healthy-only).

## Predictions

- **P1.** Config only; effort recorded (mappings, rules, silence iterations).
- **P2.** Gates G1–G6 clean (no duplicates, monotonic, calendar-identical,
  no rotation, TTL complete, healthy inside the fault cluster).
- **P3.** Healthy silence within three logged iterations.
- **P4.** Deployed union false alarms ≤ 10 of 96.
- **P5.** ≥ 60 % of the 48 scenarios detected.
- **P6.** Coil fouling ≤ 6 of 12 detected (the four-system pattern: 2, 5 of 12).
- **P7.** No scenario detected only by the conformance channels.
- **P8 (new families).** Airflow restriction (filter ×3, OA inlet blockage,
  fan outlet blockage): ≥ 2 of 5 detected; control faults (unstable, two
  reverse-acting): ≥ 2 of 3, through the oscillation or absence channels.

## Falsifiers (binding)

- **F-X19.a** a `src/` change is required → config-only fails on this class.
- **F-X19.b** P4 false → the budget does not transfer.
- **F-X19.c** < 40 % detected → the detector does not transfer.
- **F-X19.d** P7 false → the null does not generalise; examine.
- **F-X19.e** any threshold changed after a fault file was opened → not blind.

## Artefacts

`outputs/week0_audit_fcu.json`, `benchmark_v6_fcu.json`, `union_fpr_fcu.json`,
`x19_onboarding.json`; guard `tests/test_x19_onboarding.py`.
