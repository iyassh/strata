# Phase 10 Results — A fourth system: the LBNL dual-duct AHU, onboarded blind (X17), the X15 gain that did not replicate (X18), a fifth system, the fan coil unit, that broke a rule the first four never exercised (X19), the transfer test re-run with four buildings (X20), and a net's reading of a foreign year (X21)

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


## X19 — a fifth system: the LBNL fan coil unit

*Pre-registered (`docs/plans/2026-09-24-x19-fcu-onboarding-prereg.md`,
f72d53f) after the documentation and before any data file; config committed
(beab656) before any fault file was scored; run 1 committed (3185623) with
two falsifiers fired; Amendment 1 committed (800f07d) before the two-script
fix (7d52587) and the re-run. Artefacts: `outputs/week0_audit_fcu.json`,
`benchmark_v6_fcu.json`, `union_fpr_fcu.json`, `x19_onboarding.json`, with
run-1 copies as `*_run1.json`; guards `tests/test_x19_onboarding.py`,
`tests/test_artefact_consistency.py`.*

### The system

LBNL FDD Data Sets: Fan Coil Unit (2022) — a vertical four-pipe unit with
a three-speed fan, cooling and heating coils, one outdoor-air damper held at
a 30 % minimum while occupied (no economizer), one zone; 29 points; 48
seeded faults in 17 families and one fault-free year at one-minute
resolution; Des Moines TMY; 3.8 GB. Four documentation-level fault families the first four systems do not
have — filter restriction, outdoor-air inlet blockage, fan outlet blockage,
and reverse-acting control — which the scorecard groups as two: airflow
restriction (5 files) and control faults (3, with unstable control). Weekends are setback
(`FCU_CTRL = 2`, 85/55 °F) and the unit is idle unless the room drifts past
those limits — the property that matters below.

### Onboarding (P1): configuration only

| | count |
|---|---|
| sensor mappings (`sensors.yaml`, excluding `Datetime`) | 29 |
| state-event rules | 7 |
| signature rules (existing kinds only) | 16 |
| healthy-silence iterations | 2 (logged beside each rule) |
| `src/` changes | **none** |
| `scripts/` touched | `06_convert_fcu.py` (new); two lines in `gates_system.py` so G5 reads this Brick file's `FCU:` names and G6 uses fan speed as the fan-on signal |

Iteration 1 was already silent — zero signature events on the fault-free
year — but two rules could not have fired on this data at all: the
fan-high threshold (20 rev/s) sat above both observed speeds (9.75 and
13.08), and the zone-tracking gate was on valve *position*. Iteration 2 split the
speeds at 11 rev/s and moved the zone-tracking gate to the valve *command*:
on the healthy year neither position nor command exceeds 0.95 (commands
reach 0.50 and 0.66), so the rule is equally silent either way there; the
reason is physical — under a stuck or starved valve the controller's
command saturates where the position cannot — and it comes from the
documentation's control sequence, not from any fault file. Still zero
signature events. A rule that is silent because it is dead is not evidence of
anything, which is why the iteration is logged.

### Gates (P2): two findings

49 files. **G1 found one byte-identical pair**:
`FCU_Fouling_Cooling_Airside_Minor` and
`FCU_Fouling_Heating_Airside_Minor` share an MD5 — one run shipped under
two *family* labels, and the data cannot say which is right. The content
is scored once and the second entry is excluded in the manifest
(ERRATA E6), so the fouling family is 11 scored scenarios, 47 in all.
**G5 is not attainable by name**: the FCU Brick file names its points by
class (`FCU:Valve_Command`, reused under both valves), not by column;
only the fan's two columns match. G2–G4 clean, G6 places the healthy file
inside the fault cluster on every axis — on the occupied-day axis at its
top, 261, tied with 44 fault files and exceeded by none. G6 also showed
four fault files with fewer occupied days (215–250): in the three
damper-stuck files a damper held open in winter drives mixed air below
the 35 °F low-temperature limit and the documented protection shuts the
unit down, 94 days in the stuck-80 % file (the healthy year has no minute
below 35 °F with the fan on in operate mode); the unstable-control file
(250 days) trips for a different reason, its damper never leaving the
normal 0.30. A physical consequence of the faults, not a defect; it changes those
files' occupied-day universe, and no channel is credited for it (the absence
channel flags no day on any FCU scenario). P2 as pre-registered ("gates clean") is therefore
**false**, and it is false because the battery worked.

### Run 1: every scenario "detected", and a fired falsifier

| | run 1 |
|---|---|
| scenarios detected / scored | 47 / 47 |
| deployed false alarms (union minus rate) | **28 / 96 → F-X19.b fired** |
| detected by the conformance channels alone | **6 → F-X19.d fired** |

The model channel flagged 25 of 96 holdout days, every one a Saturday or
Sunday: 24 were weekend days with no events, one a two-event weekend
trace. Both scoring scripts define a scheduled day as `OCCUPIED > 0` and
flag an event-less scheduled day as a model violation — "silent while
scheduled", written for the fan-powered units whose mode 2 is a night
cycle that *does* generate events. On the fan coil unit mode 2 is idle
setback, and the rule fired on 97 of 104 weekend days. The six model-only
"detections" (OA damper leaking 20 %, five waterside-fouling files) each
carried exactly 100 model days — the healthy year's own 100
weekend model days (97 silent, three two-event traces). They were called significant because the scorecard's
model gate compared them against a conformance-only baseline (1 of 72
event days) while the deployed count included the silence rule (25 of
96): two artefacts, one channel, two numbers. On the four earlier systems
the two numbers coincide (0, 1, 1, 0), so nothing had ever exposed it.

### Amendment 1 (scripts only)

Pre-registered before the change: (i) the silence rule's "scheduled"
becomes operate mode (`OCCUPIED == 1`), the definition the occupancy event
kind already uses — the day universe, the scheduled-day list and the
absence channel are untouched; (ii) the scorecard's model gate counts
silent-in-operate holdout days in its baseline so it can never again gate
against a smaller number than the deployed count. Predictions: the four
earlier systems regenerate unchanged (A1-P1); FCU false alarms ≤ 10 of 96,
expected 4 (A1-P2); the six model-only scenarios drop and nothing else
changes status, 41 of 47 (A1-P3); nothing by conformance alone (A1-P4).

### Run 2 (artefacts at 50510fc; scripts at 7d52587): every amendment prediction held

| | run 2 |
|---|---|
| SDAHU, PFPU, SFPU, DDAHU artefacts after the script change | **byte-identical** (A1-P1): all four scorecards and false-alarm artefacts were regenerated under the amended scripts at 7d52587 and `git status` reported no change; their MD5s at that state are in `outputs/x19_a1_regression.json` |

The change is not a no-op by construction: the silence rule's day domain shrinks by every day that has scheduled but no operate minutes — 104 on each fan-powered unit, 24 on the dual-duct unit, none on the single-duct — and the artefacts held only because every one of those days carries night-cycle events on those systems (0 event-less among them, checked).
| deployed false alarms (union minus rate) | **4 / 96** (4.2 %): residual 3, model 1 (A1-P2) |
| naive union of all eight | 21 / 96 (rate alone 17) |
| scenarios detected / scored | **41 / 47** (87 %): exactly the six model-only scenarios dropped, no other status changed (A1-P3) |
| detected by conformance alone | none (A1-P4) |

| family | detected / scored |
|---|---|
| OA damper stuck (5 positions) | **5 / 5** |
| OA damper leaking (20/50/80 %) | 2 / 3 |
| coil valve stuck (cooling, heating × 5 positions) | **10 / 10** |
| coil valve leaking (cooling, heating × 3) | **6 / 6** |
| room-temperature sensor bias (±2, ±4 °C) | **4 / 4** |
| coil fouling (air/water side × 3 severities, one duplicate excluded) | 6 / 11 |
| airflow restriction (filter 10/20/50 %, OA inlet, fan outlet) — new family | **5 / 5** |
| control faults (unstable, two reverse-acting) — new family | **3 / 3** |

Channel credits among the 41: residual 37, rules 25, frequency 23,
oscillation 18, model 7 (never alone), rate 1, absence 0, device n/a.
At day level the model channel is the sole flag on 15 days of the
unstable-control scenario (`model_unique_days`), which four other channels
catch; the scenario-level null is untouched, but this is the first system
since the dual-duct unit's zero on which the model channel is alone on any
day.
The six misses are OA damper leaking 20 % and five of the six
waterside-fouling files. A diagnostic read of those files (after
scoring; no threshold was touched; `scripts/x19_waterside_diagnostic.py`,
`outputs/x19_waterside_diagnostic.json`) shows why. On the cooling coil,
waterside fouling as simulated leaves the water-side ΔT channel's daily
median at -20.2 °F (severe) against -20.59 healthy, the
valve-open minutes at 109,885 against 109,868, and the flow at
0.622 against 0.604 gpm — about three per cent. On the heating coil the
minor and moderate files move flow by -1 % and +5 % with the ΔT
median within 0.5 °F of healthy; only the severe file, which cuts
valve-open time by 16 %, is caught. Whatever the fault does inside the
model, on the cooling coil it does not reach the recorded points at a size
the residual channel's healthy band can see. The pre-registered rule for
it exists — both coils' water-side ΔT residual channels are in the config
sketch and in `rules.yaml` — and it is silent because the effect sits
inside the healthy band; a rule that could see it would need a different
quantity, and it is not obvious one exists in these 29 points.

**What X19 adds to X17.** The onboarding claim survives a second class
with the same protocol (29 mappings, 23 rules, two silence iterations, no
`src/` change), the false-alarm budget transfers (4.2 %), the two new scorecard families
(four at the documentation's granularity) are caught in full, and the conformance null holds on a
fifth system — the model channel is credited on seven scenarios, every
one already caught by rules, residual, frequency or oscillation. The
new thing is the failure: the fifth system found an assumption in the
*scoring scripts* — "any non-zero mode is scheduled operation" — that
four systems had never exercised, and the inconsistency it exposed
between the scorecard's gate and the deployed count would have printed
six detections that were the healthy year's weekends. Run 1 is kept; the
repair was pre-registered; the four earlier scorecards did not move.

### Ledger

| P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | falsifiers |
|---|---|---|---|---|---|---|---|---|
| ✓ config only | **✗** G1 duplicate pair, G5 not by name (G2–G4, G6 clean) | ✓ 2 iterations | run 1 **28/96 → F-X19.b**; run 2 ✓ 4/96 | ✓ 41/47 | ✓ 6/11 ≤ 6 (bound set against 12; one file excluded by E6) | run 1 **6 → F-X19.d**; run 2 ✓ none | ✓ 5/5 airflow, 3/3 control | run 1: b, d; after Amendment 1: none |

| A1-P1 | A1-P2 | A1-P3 | A1-P4 | A1 falsifiers |
|---|---|---|---|---|
| ✓ four systems byte-identical (regenerated; no diff) | ✓ 4/96 (predicted 4) | ✓ 41/47, exactly the six | ✓ none | none fired |

The sealed transfer test's scorable pool is now four buildings (PFPU,
SFPU, DDAHU, FCU — the fan coil unit has a heating coil), so the floor
falls to 1/4! = 0.042: the first design in this project that can attain
p < 0.05. That re-run is X20, pre-registered separately; it has not been
run.


## X20 — the transfer test with four scorable buildings

*Pre-registered (`docs/plans/2026-09-24-x20-transfer-four-buildings-prereg.md`,
fd95da3) after X19 and before any quantity was computed on the two new
buildings. Artefacts: `outputs/discovery_predicts_transfer_q_four.json`
(the sealed Q code run unchanged on DDAHU and FCU via `--systems`),
`matched_rules_{ddahu,fcu}.json`, `x20_transfer_four.json`; guard
`tests/test_x20_transfer_four.py`. The original three-system Q artefact is
untouched.*

### Why this was pre-registered as a test of an identity, not of a correlation

The original test's Amendment 3 had recorded, as an observation, that the
model-derived predictor "equals the raw log count exactly." Checked before
X20 on the committed artefact: on PFPU and SFPU, `Q_support` (the fraction
of occupied days whose optimal alignment to the discovered net contains a
synchronous heating move) is exactly the fraction of occupied days whose
*log* contains `heating_active` — 166/365 and 357/365. And MR1, the one
transplanted rule whose firings vary, counts occupied workdays on which
heating never fires: the workday complement of the same day set. A
four-building Spearman between the two would be a correlation between a
count and its own complement. So the pre-registration made the identity
(P1) the decision: if it held on the new buildings the test was to be
withdrawn as uninformative at any n; if it failed, "the alignment carries
information" and the four-building test (P2) was to be scored and reported
straight. A control with no discovery in it — the raw heating-day fraction
as predictor — was implied by the disclosure and is computed alongside.

### Result

| building | Q_support | sync days / raw heating days / occupied | Q_obligatory | MR1 healthy firings |
|---|---|---|---|---|
| FCU | 0.203 | 74 / **118** / 365 | 0 | 149 |
| PFPU | 0.455 | 166 / 166 / 365 | 0 | 124 |
| DDAHU | 0.730 | 208 / 208 / 285 | 1 | 66 |
| SFPU | 0.978 | 357 / 357 / 365 | 1 | 0 |

- **P1 (identity)** holds exactly on DDAHU and **fails on FCU**: 44 of the
  118 heating days get no synchronous heating move. **F-X20.a fired**, so
  by the pre-registered rule P2 is scored. Diagnostic (after the fact): the
  FCU's unit net, mined at noise threshold 0.2 from 196 training days,
  carries `heating_active` but not `heating_inactive`; on 38 weekday and 6
  weekend traces the cheapest alignment moves the heating episode on the
  log side. What the alignment "carries" is the miner's noise filter, not a
  reading of an invariant.
- **P2 (four buildings)**: rho = −1.000, exact one-sided permutation
  p = 1/24 = **0.042** < 0.05, the four MR1 counts distinct. The
  pre-registered criterion is met.
- **Control**: the raw heating-day fraction orders the four buildings
  identically (0.32, 0.45, 0.73, 0.98) and gives rho = −1.000, p = 0.042.
- **P3 (obligatory form)** fails on every building — **F-X20.b fired**.
  `Q_obligatory` = 1 on SFPU and DDAHU although 8 and 77 occupied days lack
  heating; it is 1 because no *cost-zero* variant lacks heating, and the
  heating-less days' traces do not fit the net for other reasons. The
  structural form is a property of which variants the noise-filtered net
  admits, not of the year.

### Reading

The four-building transfer test passes as pre-registered, and it is the
first design in this project that could have. It is reported as a pass.
What the pass is worth is set by the control: a predictor with no
discovery in it — count the days with heating — passes identically,
because MR1 is a heating-absence rule and the ordering is the ordering of
heating-day counts. At n = 4 nothing can separate the two predictors, and
the one building on which they differ (FCU) differs by the miner's noise
filter. The claim "discovery locates invariants" therefore receives no
support beyond what the log's count provides, which is none that involves
discovery. This is the tenth adverse result: the test that finally had
power passed for a reason that has nothing to do with the hypothesis.

A test that could bear on the claim would need a predictor not computed
from the log it predicts — fit on building A, replay building B — and it
is an open question whether alignment support can escape being a count of
B's log. Not run.

### Ledger

| P1 identity | P2 four buildings | control | P3 obligatory | falsifiers |
|---|---|---|---|---|
| DDAHU exact; **FCU 74 ≠ 118 → F-X20.a** | rho −1, p 0.042 ✓ | rho −1, p 0.042, same order | **✗** on all four → F-X20.b | a, b fired; verdict: informative by rule, uninformative by control |


## X21 — can a net's reading of a *foreign* year escape being that year's count?

*Pre-registered (`docs/plans/2026-09-24-x21-foreign-net-support-prereg.md`,
7f75efc) after X20 and before any cross-building alignment. Artefact
`outputs/x21_foreign_net_support.json`; guard
`tests/test_x21_foreign_net_support.py`. Twelve ordered pairs of the four
heating-coil buildings: fit the unit net on A's fault-free training days,
align every variant of B's fault-free state log to it, `Q_AB` = fraction of
B's occupied days with a synchronous `heating_active` move; `raw_B` = B's
own heating-day fraction.*

| net from ↓ / log of → | PFPU (raw 0.455) | SFPU (0.978) | DDAHU (0.730) | FCU (0.323) |
|---|---|---|---|---|
| PFPU | — | 0.978 | 0.716 | 0.323 |
| SFPU | 0.455 | — | 0.730 | 0.323 |
| DDAHU | **0.066** | **0.403** | — | **0.151** |
| FCU | **0.000** | **0.000** | **0.000** | — |

- **P1 (bound)** holds on every pair.
- **P2 (the tautology persists)** fails on six pairs — **F-X21.a fired**.
  A fan-powered unit's net synchronises heating on every foreign log at
  exactly that log's count; the dual-duct net does so on a fraction; the
  fan coil unit's net never does. The alignments say why: the alphabets
  barely overlap (the fan-powered nets carry `night_cycle_*` and no
  `system_started`; the FCU net carries `fan_*`, `oa_damper_*`, `setback_*`
  and no `heating_inactive`), so a foreign trace's heating episode sits
  outside the block structure the net expects and the cheapest alignment
  moves it on the log side. `Q_AB` measures alphabet and block-structure
  overlap between two buildings, not where an invariant holds.
- **P3 (ordering)** fails: the foreign predictor (mean over the three
  foreign nets) orders the buildings PFPU 0.17 < FCU 0.27 < SFPU 0.46 <
  DDAHU 0.48, not the count's order, and against MR1 firings gives
  rho = −0.6, exact one-sided p = 5/24 = 0.21, where the count gives −1
  and 1/24.

**Reading.** X20 asked whether alignment-based support could be anything
other than the log's own count; X21 answers that it can — and that what it
becomes when it is not the count is a measure of how much of one
building's vocabulary and daily block structure another building's net
recognises, which predicts a transplanted rule's firings *worse* than the
count does. The pre-registration said that a differing ordering would be
"the first thing in this project that discovery contributes to transfer";
it is, and the contribution is negative. With n = 4 neither rho is a
measurement; the per-pair table is the result. Discovery locates alphabet
overlap; the transfer claim has no support in either direction of this
framework.

### Ledger

| P1 | P2 | P3 | falsifiers |
|---|---|---|---|
| ✓ | **✗** 6 of 12 pairs → F-X21.a | **✗** different ordering; rho −0.6 (p 0.21) vs control −1 (p 0.042) | F-X21.a fired |
