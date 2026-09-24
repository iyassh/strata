# Phase 10 Results — A fourth system: the LBNL dual-duct AHU, onboarded blind (X17), and the X15 gain that did not replicate (X18)

*2026-09-24. Pre-registered (`docs/plans/2026-09-24-x17-ddahu-onboarding-prereg.md`,
b8fadc8) after the documentation was read and before any data file was
opened; config committed (90dd88c) before any fault file was scored; one
amendment (a script assertion turned into a recorded cost) after the
scorecard and before the false-alarm artefact. Artefacts:
`outputs/week0_audit_ddahu.json`, `benchmark_v6_ddahu.json`,
`union_fpr_ddahu.json`, `x17_onboarding.json`; guard
`tests/test_x17_onboarding.py`.*

## The system

LBNL FDD Data Sets: Dual Duct Air Handling Unit (2022) — hot and cold decks,
two coils, two supply fans, three AHU dampers, four zone mixing boxes with
command-only dampers; 114 points; 55 seeded faults in 15 families and one
fault-free year at one-minute resolution; Des Moines TMY; 17 GB. Two fault
families the first three systems do not have: static-pressure sensor bias
and unstable control sequences.

## Onboarding (P1): configuration only

| | count |
|---|---|
| sensor mappings (`sensors.yaml`, excluding `Datetime`) | 79 |
| state-event rules (unit + four zone boxes as device stratum) | 15 |
| signature rules (existing kinds only) | 26 |
| healthy-silence iterations | 1 (logged beside each rule) |
| `src/` changes | **none** |

Healthy-silence gate, iteration 1: the initial config's first run printed
73 signature events on 8 rules (cold SAT deviation 17, cold static
deviation 11, zone flow tracking 10 on each of four boxes, hot SAT
deviation 4, hot-deck residual 1 — a console figure; the pre-iteration
config was not committed, and reverting the changes the comments log
reproduces 51 events on 13 days, 47 of them on the ten days below). Nearly
all of it came from ten specific days on which the cold-deck fan saturates (speed 1.0, duct static 1.39 against a
1.6 in.wg setpoint) and the deck cannot hold 55 °F or deliver demanded
zone flow. Rather than loosen thresholds, those rules got a physical gate —
"duct static at setpoint" — expressed with the existing two-gate residual
kind; zone-damper state thresholds were set to the healthy command
baselines (0.42 / 0.60). Result: **1 signature event on 1 day of 365**.

## Gates (P2): clean

56 files, 56 distinct MD5s, all monotonic, all calendar-identical to the
fault-free file, no rotation, Brick model covers all 114 columns. A G6
configuration-branch comparison (occupied-day universe, first occupied
minute, outdoor-air damper floor while the fan runs, every setpoint
constant) places the healthy file inside the fault files' cluster on every
axis. Unlike SDAHU and SFPU, this dataset carries no defect the battery
can see.

## Scorecard (P5–P8)

| family | detected / scored |
|---|---|
| unstable control sequence (cooling, heating) | **2 / 2** |
| zone mixing-box damper stuck (cold, hot × 5 positions) | **10 / 10** |
| OA damper stuck (5 positions) | **5 / 5** |
| coil fouling (cooling, heating × air/water side × 3 severities) | 5 / 12 |
| deck SAT sensor bias (±2, ±4 °C, both decks) | **8 / 8** |
| deck static-pressure sensor bias (±0.2, ±0.4 in.wg, both decks) | 5 / 8 |
| coil valve stuck (cooling, heating × 5 positions) | **10 / 10** |
| **all** | **45 / 55 (82 %)** |

Channel credits among the 45: residual 39, rules 35, oscillation 15,
absence 14, rate 9, frequency 8, device 1, **model 0**. No scenario is
detected only by the conformance channels (P7 holds: the null generalises
to a fourth system type). The ten misses: seven coil-fouling files (all four minor, both airside
moderate, and heating airside severe — so at the documentation's
15-family granularity heating airside fouling is missed entirely, 0 of 3)
and three static-pressure biases (cold +0.2, hot −0.2, hot −0.4 in.wg).

**P6 was wrong.** Five of twelve fouling scenarios were detected (the
waterside moderate/severe of both coils and cooling airside severe, through
the waterside ΔT rules and the residual channel) against a predicted
ceiling of four. The prediction was a limitation forecast calibrated on the
fan-powered units (2 of 12) and it under-predicted by one scenario. No
falsifier was attached to P6, so nothing follows for the protocol — which
is itself worth recording: the one prediction that failed is the one that
carried no consequence.

## False alarms (P4)

| | of 96 holdout days |
|---|---|
| deployed union (minus rate) | **3** (3.1 %) — all from the absence channel |
| naive union of all eight | 8 (8.3 %) |
| per channel | rules 0, residual 0, model 0, device 0, absence 3, frequency 0, oscillation 0, rate 7 |

**Rate demotion is free here after all** (Amendment 1, corrected on
review): the false-alarm script's demotion check reported that `cooling
valve stuck 0%`'s first alarm day (2018-01-01) was covered by no non-rate
channel. Recomputing every channel on that file with `pipeline.score()`
shows the day-1 alarm is the **absence** channel's (135 flagged days,
first 2018-01-01; rate's first is 2018-04-23; rules 04-03, oscillation
02-04). The scorecards export no absence day list, so the check could not
see it — a blind spot in the check, not a cost of demotion. The check now
records such cases as unresolved rather than as violations. Detection
count and every time-to-detect are unaffected by demoting rate on this
system.


## X18 — does the X15 gain replicate here? No.

Pre-registered (fae33da) after the scorecard and before any enriched run:
X15's protocol unchanged — healthy-derived band states for every actuator
position and flow (17 signals on this system; command-only zone dampers
excluded as non-positions), 15-minute dwell, frequency channel only, bands
and the false-alarm rate recomputed under both holdout splits.

| enriched frequency channel | last-8 | first-8 |
|---|---|---|
| holdout FP (of 83 event-days) | 2 | 2 |
| significant scenarios (of 55) | 22 | 21 |
| newly significant among the 10 misses | none | none |

Inside the budget under both splits (P1), no static-bias miss gained (P3),
and coverage on already-detected scenarios rises from the deployed
frequency channel's 8 to 22 (P4) — but **no missed scenario becomes
significant under either split; F-X18.b fired.** The seven fouling misses
flag 3–11 days each against a floor of 2 or 3 in 83.

**Reading.** X15's fouling detection was a one-scenario, one-system
signature (the series unit's zone-S damper band under airside fouling); on
a fourth system with seven fouling misses the same mechanism finds none of
them. The enriched frequency channel remains what X15 showed it to be —
cheap extra day-level coverage on scenarios the detector already catches,
inside the budget — and nothing more. It is not adopted.

## Ledger

| P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | falsifiers |
|---|---|---|---|---|---|---|---|---|
| ✓ config only | ✓ clean | ✓ 1 iteration | ✓ 3/96 | ✓ 45/55 | **✗** 5 > 4 (better) | ✓ none by conformance | ✓ 5/8 static, 2/2 unstable | none fired |

| X18 | P1 ✓ budget (2/83 both splits) | P2 **✗** no fouling miss gained | P3 ✓ | P4 ✓ 22 vs 8 | **F-X18.b fired** |
|---|---|---|---|---|---|

## Reading

The detector transfers to a different air-handler type on a different
building with a configuration file and one healthy-silence iteration:
82 % detection at 3 % false alarms, every family except coil fouling and
static-pressure bias caught in full, both new fault families caught at
least partly. The process-mining null transfers with it: the discovered
model channel flags zero days on every scenario (threshold 0.25 at
min-calibration on a 28-event-per-day alphabet), and nothing is detected
by conformance alone. What did the work is what did it before — rules and
residuals first, then oscillation and absence.

Two things this changes upstream. The sealed transfer test's scorable
pool grows from two buildings to three: its Amendment 1 excluded the
single-duct system *structurally* (no heating activity in its sensor
map), so the floor moves from 1/2! = 0.5 to 1/3! = 0.167 — still above
0.05; the test remains unpowered and has not been re-run. (A first
write-up said 1/4! = 0.042 with four buildings; that counted a building
the test cannot score.) And the benchmark-defect finding is bounded: the
gate battery — G1–G5 plus a G6 configuration-branch comparison of the
E5 class, ported for this run — found nothing on this LBNL dataset, so the
five defects are properties of two archives, not of the collection.
