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

## Amendment 1 — written after run 1 (3185623), before any script change or re-run

**Run 1 outcome.** Gates: G1 found one byte-identical pair (ERRATA E6;
scored once), G5 is not attainable by name (the FCU Brick file names Brick
classes, not columns), G2–G4 and G6 clean. Healthy silence in two logged
iterations. Scorecard: 47 of 47 scored scenarios nominally detected;
deployed union-minus-rate false alarms **28 of 96 → F-X19.b fired**; six
scenarios detected by the model channel alone → **F-X19.d fired**.

**Diagnosis (from the healthy year and the scripts, no fault file).** The
model channel flags 25 holdout days, every one a Saturday or Sunday. 24 have
no events at all: the FCU sits in setback (`FCU_CTRL = 2`) all weekend and,
unlike the fan-powered units' night-cycle, setback on this unit is idle
unless the room drifts past 85/55 °F. `benchmark.py` and `union_fpr.py`
define a scheduled day as `OCCUPIED > 0` and flag an event-less scheduled
day as a model violation ("silent while scheduled"); on this system that
rule fires on 97 of 104 weekends. The 25th day is a conformance flag on a
two-event weekend trace. The six model-only "detections" carry exactly 100
model days each — the healthy year's own 100 weekend-silence days — and the
scorecard's model gate compared them against a conformance-only baseline
(1 of 72 event days) while the deployed count includes the silence rule
(25 of 96): the two artefacts disagreed about the same channel. On the four
earlier systems the two counts are equal (0, 1, 1, 0), so this
inconsistency had no effect there.

**Change (scripts only, nothing under `src/`).** (i) In both scripts the
silence rule's "scheduled" becomes operate mode (`OCCUPIED == 1`), the
same definition the occupancy event kind already uses; the `occupied_min`
day universe, `sched`, and the absence channel are untouched. (ii) The
scorecard's model gate counts silent-scheduled holdout days in its
false-alarm numerator, so it can never again gate against a smaller
baseline than the deployed count. No FCU threshold changes.

**Predictions.** A1-P1: the committed artefacts of SDAHU, PFPU, SFPU and
DDAHU regenerate unchanged (SDAHU byte-identical; the others
count-identical). A1-P2: FCU run 2 deployed false alarms ≤ 10 of 96
(expected 4: model 1, residual 3). A1-P3: the six model-only scenarios are
no longer detected and no other scenario changes status: 41 of 47. A1-P4:
no scenario detected by conformance alone.

**Falsifiers.** A1-F.a: any earlier-system artefact changes → the change
is a detector change, not a repair, and is reported as such in every paper
that quotes those numbers. A1-F.b: run-2 false alarms > 10 of 96 → the
budget does not transfer to this class; report. A1-F.c: a scenario other
than the six changes status → the silence rule was contributing real
detections; report which.
