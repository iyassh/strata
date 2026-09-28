# Phase 12 — the coverage series (X33): every recorded column audited, one system at a time

*Pre-registration: `docs/plans/2026-09-25-x33-coverage-series-prereg.md` (per-system
sections appended before each system's configuration is changed). Standing rules,
adoption rule and budget are in that file. Ledger per system:
`scripts/x33_coverage.py --system <s> --before <commit>` →
`outputs/x33_coverage_<s>.json`; guards `tests/test_x33_coverage.py`,
`tests/test_sensor_coverage.py`.*

## Why this series exists

The X32 scan (2026-09-25, withdrawn before computation) found that for six of the
fourteen reachable misses the decisive signal is a column the dataset records
but no configuration maps. The configurations had been written from the control
sequences, not from an audit of every recorded column. X33 audits every column of
every system, maps every usable one, gives it a reader, and excludes the rest with
a written reason that a guard enforces. The state alphabet is not touched, so the
process-mining rows must regenerate identically; coverage acts through the
physics and statistical channels only.

## X33a — SDAHU (30 columns; 12 → 26 mapped, 4 excluded)

*Pre-configuration commit 8f06f19; configuration 16858e5 (healthy silence at
iteration 2: one band had been logged in the wrong unit and fired daily; corrected
against the fault-free file and recorded); artefacts regenerated after.*

| added | reader |
|---|---|
| SF_POWER, RF_POWER, SA_FLOW, RA_FLOW, SF_SPEED_CMD, RF_SPEED_CMD, RF_SPEED_POS, SF_CMD, RF_CMD | `sf_specific_power` = SF_POWER / SA_FLOW; `rf_specific_power`; `sf_flow_per_speed` = SA_FLOW / SF_SPEED_CMD (fan law); `rf_speed_mismatch` (position vs command) |
| ZONE_TEMP_1–5 | oscillation channel (daily direction reversals, 0.5 °F deadband) |
| excluded | OA_CFM (constant), SF_SPD (constant 0.9), SA_SP and SA_SPSPT (ERRATA E3 provenance leak) |

| | before | after |
|---|---|---|
| detected (naive / adjudicated) | 14 / 14 (13) | 14 / 14 (13) |
| deployed false alarms | 1 / 96 | 1 / 96 |
| new residual rules' own holdout false alarms (of each rule's evaluable holdout days) | — | 0 / 79, 0 / 79, 0 / 79 |
| model and device rows | — | byte-identical |
| time to detection | — | unchanged on every scenario |

Channel changes: the residual channel is now credited on `coi_stuck_010` and
`coi_stuck_025` (residual days 0 → 118 and 0 → 87; previously rules only) — a
stuck chilled-water valve moves the supply fan's operating point, and the
specific-power residual sees it; the oscillation channel joins the credits on
`coi_bias_−4`. Every prediction held; no falsifier; all three new residuals kept
under the adoption rule.

**Reading.** On the reference system, full coverage costs nothing (1/96 before
and after) and adds a second, physically distinct witness to two scenarios that
had a single one. No detection could be gained here (14/14 already), which is
why SDAHU went first: it proves the audit-and-remap loop leaves the reference
scorecard, the process-mining rows and the budget untouched.

## X33b — PFPU, parallel fan-powered unit (109 columns; 56 → 109 mapped, 0 excluded)

*Pre-configuration commit 6b7512a; configuration bbe6cd3 (healthy silence at
iteration 1); artefacts regenerated after. Credits diagnostic:
`outputs/x33_residual_credits_pfpu.json` (`scripts/x33_residual_credits.py`).*

Fifty-three columns added: zone setpoints, zone discharge temperature and
airflow, zone fan pressure and power, the air handler's fan power, airflow,
speed, static pressure and setpoint, humidities, and both coils' water-side
temperatures and pump flows. Eighteen residual rules and one setpoint rule were
written from the healthy year (bands logged in the configuration).

| | before | after |
|---|---|---|
| detected | 22 / 30 | **26 / 30** |
| gained | — | airside reheat fouling **moderate** and **severe**; room-temperature bias **+2 °C** and **+4 °C** |
| lost | — | none |
| deployed false alarms | 7 / 96 | 8 / 96 (residual channel 2 → 3) |
| new residual rules' own holdout false alarms (of each rule's evaluable holdout days) | — | 0 or 1 day each: 0/35, 1/52, 0/69, 1/63, 1/60, 0/52, 0/69, 0/63, 0/60, 0/69 ×4, 1/69, 1/69, 0/69, 0/69; `hwc_waterside_dT` never evaluates (0/0) |
| model and device rows | — | byte-identical |
| time to detection | — | not later on any scenario; all four gains on day 1 |

**Which physics carried each gain** (flagged days of 261, facade bands):

| scenario | carrying rule | days | reading |
|---|---|---|---|
| airside reheat fouling, moderate | `da_minus_pm_S` (zone S discharge airflow − primary airflow, zone fan off) | 172 | with the zone fan off, the primary airflow median is 201 cfm in the healthy, minor, moderate and severe files alike, while the measured discharge airflow rises 178 → 180 → 185 → 192 cfm; the relationship between the two flow sensors moves with fouling severity while every temperature the controller holds stays inside its band. The mechanism inside the simulation is not documented; the relation is reported as a witness, not an explanation |
| airside reheat fouling, severe | `da_minus_pm_S` | 227 | same; the minor file moves it on 1 day and stays missed |
| room-temperature bias +2 °C | `ra_minus_zone_S` (return air − zone S reading) | 187 | the controller over-cools the zone whose sensor reads high; the return air, which mixes the true zone temperatures, falls away from that zone's reading by the bias |
| room-temperature bias +4 °C | `ra_minus_zone_S`, `_I`, `_W` | 261, 233, 174 | as above, larger, and visible against every zone because the return air itself is cooler |

| P1 no loss | P2 budget | P3 a room-temperature bias detected | P4 fouling stays missed | P5 model rows identical | falsifiers |
|---|---|---|---|---|---|
| ✓ | ✓ (8/96; every new rule ≤ 1) | ✓ (both) | **✗ — positive surprise:** two of six fouling misses are now detected, through airflow, not temperature | ✓ | none |

**Reading.** The parallel unit's misses were not a detector limit but a
coverage limit. The two fouling detections come from a column pair the
configuration never read (zone discharge airflow beside primary airflow), and
the physics is the right one: airside fouling is a flow-resistance fault, and
the recorded temperatures never move because the controller holds them. The
four remaining fouling misses (airside minor, waterside minor/moderate/severe)
still sit inside every healthy band on every column. The one added false-alarm
day is a residual day on 2018-08-27 (the residual channel's 2018-10-29 and
2018-12-24 were already there), inside budget and inside the adoption rule.
Every new rule is kept. Two costs the ledger does not show: the four gains are
residual-only and name no device, so the attribution count moves from 36 named
of 43 to 36 of 46 (three more 'none'); and because the new rules evaluate on
more holdout days, the residual channel's per-day null denominator grows from
41 to 69 days, which lowers its floor from 7.3 % to 4.3 % for the pre-existing
rules as well — no verdict flipped (every credited scenario has ≥ 110 residual
days, every miss ≤ 6), but the null is looser than before and the manuscript's
'41 such days' sentence must change.

## X33c — SFPU, series fan-powered unit (109 columns; 56 → 109 mapped, 0 excluded)

*Pre-configuration commit 028a941; configuration ce3a9f4 (healthy silence at
iteration 2: a YAML literal format error, no band change); artefacts
regenerated after. Credits diagnostic: `outputs/x33_residual_credits_sfpu.json`.*

Same column map as the parallel unit, plus the series-fan readers the X32 scan
pointed at: zone-fan specific power (fan power / discharge airflow) and fan
pressure per airflow² for each of the four zones.

| | before | after |
|---|---|---|
| detected | 21 / 29 | **25 / 29** |
| gained | — | **VAV fan flow restriction**; airside reheat fouling **moderate** and **severe**; room-temperature bias **+2 °C** |
| lost | — | none |
| deployed false alarms | 6 / 96 | 9 / 96 (residual channel 0 → 3: 27 April, 25 June, 27 August) |
| new residual rules' own holdout false alarms (of each rule's evaluable holdout days) | — | 22 rules: 0 on 17 (one of them, `hwc_waterside_dT`, has no evaluable holdout day and an undefined band, so it can never flag), 1 on 3, 2 on `static_per_speed2` |
| model and device rows | — | byte-identical |
| time to detection | — | not later on any scenario; all four gains on day 1 |

**Which physics carried each gain** (flagged days of 261, facade bands):

| scenario | carrying rule | days | reading |
|---|---|---|---|
| VAV fan flow restriction | `zone_fan_spf_S` (zone S fan power per cfm delivered) | 261 | a restricted fan delivers less air for the same power; the healthy band is 0.02 W/cfm wide and the fault leaves it every day |
| airside reheat fouling, severe | `zone_fan_spf_S` | 261 | the fouled coil sits in the series fan's path: the same power moves less air |
| airside reheat fouling, moderate | `zone_fan_spf_S` | 145 | same, at half the days; the minor file moves it on 0 days and stays missed |
| room-temperature bias +2 °C | `dat_minus_sa_S`, `ra_minus_zone_W/E` | 180, 173, 152 | over-cooled zone: discharge air runs colder against supply, and the return air falls away from the other zones' readings |

**Adoption rule, per rule.** Four new rules carry a holdout day: `rf_specific_power`
(1), `sf_flow_per_speed` (1), `zone_fan_dp_per_cfm2_S` (1) and `static_per_speed2`
(2, on 25 June and 27 August). All four also flag scenario days (the static rule on
97 days of two valve scenarios, the pressure rule on 261 days of nine scenarios),
so all are kept under the rule as pre-registered. Removing `static_per_speed2`
alone would give 8 of 96 at no detection cost; it is kept because the rule says
so, and the option is recorded here rather than taken after the fact.

| P1 no loss | P2 budget | P3 fan restriction + severe fouling | P4 moderate fouling | P5 waterside fouling stays missed | P6 model rows identical | falsifiers |
|---|---|---|---|---|---|---|
| ✓ | ✓ (9/96 ≤ 6 + 3, at the bound) | ✓ | ✓ | ✓ | ✓ | none |

**Reading.** The series unit's zone fan runs continuously, so its power per
cfm is a permanent, tight witness of everything that changes the airflow
resistance downstream of it: a restricted fan and a fouled coil face both show
up as "same power, less air". Every prediction held. The cost is three residual
false-alarm days, all on different rules, which puts the deployed union at 9
of 96 — inside the budget but with one day of headroom, the least of the six
systems. As on the parallel unit, the new rules evaluate on more holdout days,
so the residual channel's per-day null denominator grows from 41 to 69 and its
floor falls from 7.3 % to 4.3 % for the pre-existing rules as well; no verdict
flipped.

### Gap analysis after X33a–c: what the remaining fan-powered misses look like

Eight scenarios remain missed on the two fan-powered units, all reheat-coil
fouling: airside minor on both units, and waterside minor, moderate and severe
on both. Their residual channels flag 3–18 of the 261 days on which the channel
evaluates; the strongest is the series unit's severe waterside file, whose union
of 18 days (6.9 %, mostly the water-side temperature drop) sits above the per-day
floor of 3 in 69 (4.3 %) but not significantly so (p = 0.04 against 10⁻³).

**The waterside fouling is visible, but not certifiable, on the parallel unit.**
The fault is implemented as a reduced maximum water flow: with the reheat valve
more than 90 % open, the healthy coil passes 6.03 gpm and the fouled coil 5.42,
4.22 and 3.01 gpm at minor, moderate and severe (day medians; every such day is
outside the healthy band of [5.910, 6.030]). Below 80 % open the flow tracks
the valve position identically in health and fault, so a flow-per-position
residual over the whole range does not move (occupied minutes at positions
0.02–0.8: healthy median 2.500, severe 2.455). The
witness therefore exists only on days when the valve saturates: 10 days in the
healthy year (5 training days, 1 holdout day) and 10–15 days in each fault file.
Two consequences, both of the framework's own discipline: the rule's healthy
band rests on five training days (four more fall in the calibration slice) and
its false-alarm rate on one holdout day, so no null can be estimated for it; and
under the per-day gate, 15 flagged days of 261 (5.7 %) sit above the residual
channel's 4.3 % floor but far from significance (p = 0.17). A one-year healthy record does not
contain enough saturated-valve days to certify a witness that only appears when
the valve saturates. On the series unit the reheat valve exceeds 80 % on two
healthy days, so the witness is not even measurable there.

This is recorded as a limit, not tuned around: lowering the gate for a rule
that is evaluable on ten days would be exactly the kind of decision the
pre-registration forbids. What would change it is data, not method: a second
healthy year, or a healthy period with more saturated-valve operation.

**Airside minor fouling** moves the parallel unit's discharge-minus-primary
airflow on 1 day and the series unit's fan power per cfm on 0 days; the
moderate files move them on 172 and 145. The minor level sits inside the
healthy band on every column the units record.

## X33d — DDAHU, dual-duct air handler (114 columns; 79 → 114 mapped, 0 excluded)

*Pre-configuration commit c40144d; configuration 08bf7ec (healthy silence
unchanged); artefacts regenerated after. Credits diagnostic:
`outputs/x33_residual_credits_ddahu.json`.*

Thirty-five columns added: the mixing-box inlet statics and entering-air
temperatures for both decks in all four zones, both deck fans' and the return
fan's power, airflow and pressure, the pump totals, humidities and the coils'
mixed-water temperatures. Twenty-five residual rules were written from the
healthy year; the mixing-box pairs are redundant sensors of the deck statics and
deck temperatures (identical to two decimals in health).

| | before | after |
|---|---|---|
| detected | 45 / 55 | **50 / 55** |
| gained | — | hot-deck static bias **−2 and −4 in.wg**; hot-deck supply-air temperature bias **+2 °C**; heating waterside fouling **minor**; cooling airside fouling **moderate** |
| lost | — | none |
| deployed false alarms | 3 / 96 | 3 / 96 (all three absence-channel days, unchanged) |
| new residual rules' own holdout false alarms (of 75 evaluable holdout days each) | — | 0 / 75 for all 25 |
| model and device rows | — | byte-identical |
| time to detection | — | not later on any scenario; five scenarios earlier (cooling airside fouling severe 15 → 5, cold-deck static bias −2 and −4 in.wg 15 → 1 each, heating waterside fouling moderate 8 → 1 and severe 3 → 1 days) |

**Which physics carried each gain** (flagged days of 282 evaluable, facade bands):

| scenario | carrying rule | days | reading |
|---|---|---|---|
| hot-deck static bias −2 / −4 in.wg | `box_static_H_{W,SB,SA,E}` | 282 each | the deck column does not move (the controller holds its own, biased, reading at setpoint) while all four mixing-box statics rise by +0.20 and +0.40 in.wg: the true duct static has moved and the boxes record it. The recorded shift is one tenth of the labelled bias (ERRATA E8) |
| hot-deck temperature bias +2 °C | `box_eat_H_{W,SB,SA,E}` | 282 each | same mechanism: the deck column stays at setpoint, the four box entering-air temperatures fall by 3.6 °F (the labelled 2 °C, exactly); the fixed rule band (±3 °F) also fires, so the rules channel joins the credit (as it now does on the four cold- and hot-deck biases already detected) |
| heating waterside fouling, minor | `hwp_bypass_flow` (hot-water pump total − coil flow) | 282 | the fault reduces the coil's water flow at the same valve command; the pump total is unchanged, so the bypass grows |
| cooling airside fouling, moderate | the residual channel's union of six fan-side rules (cold-deck fan specific power 20 days, fan-law static 10, return-fan power 9, fan pressure 9, two others 1 each) | 32 of 282 (p = 1.5 × 10⁻⁷ against 3 of 75) | no single rule is significant alone (the strongest, 20 days, gives p = 0.01); the gate clears on the pooled per-day union, and the ledger's per-rule credit rule credits none of them on this file. The weakest gain, first alarm on day 14 |

The cooling waterside minor miss stays missed: the chilled-water bypass residual moves it on 0 days
(its healthy band spans 0–27.6 gpm because the chilled-water pump total swings with load, unlike the
hot-water pump's). The three heating airside fouling files move the hot-deck fan's specific power on
at most 6 days.

| P1 no loss | P2 budget | P3 HSP biases | P4 HSA +2 °C | P5 both minor waterside | P6 airside stays missed | P7 model rows identical | falsifiers |
|---|---|---|---|---|---|---|---|
| ✓ | ✓ (3/96, every rule 0/75) | ✓ | ✓ | half: heating ✓, cooling ✗ | ✗ positive surprise: cooling airside moderate detected | ✓ | none |

**Reading.** The three sensor-bias misses were never a detector limit: the
dataset records the true duct static and true deck temperature at every mixing
box, while the deck columns carry the controller's own held readings; the
configuration had not mapped the boxes. The bias detections are exact (282 of
282 days, every zone) at zero false alarms, and their magnitudes expose a
labelling defect: the static-bias files shift the true static by one tenth of
the labelled bias (ERRATA E8), the temperature-bias file by exactly the label. The pump-bypass residual
catches the minor heating waterside fouling that the coil's own temperature
drop could not, because it reads the fault as a flow deficit rather than a heat
deficit. Remaining misses: the five fouling files (heating airside minor,
moderate, severe; cooling airside minor; cooling waterside minor) sit inside
every healthy band on every recorded column.

## X33e — FCU, fan coil unit (29 columns; all 29 mapped before, 0 excluded)

*Pre-configuration commit d8f5064; configuration 9bb107d (healthy silence at
iteration 1); artefacts regenerated after. Credits diagnostic:
`outputs/x33_residual_credits_fcu.json`.*

The audit found no unmapped column, but five mapped columns with no reader:
the outdoor-air flow, the fan power, the constant fan-mode flag and the four
humidities. Two readers were added: the outdoor-air flow as a fraction of
discharge flow at the damper's minimum position, and the fan's specific power.

| | before | after |
|---|---|---|
| detected | 40 / 47 | **43 / 47** |
| gained | — | outdoor-air damper leak **20 %** and **50 %**; heating waterside fouling **moderate** |
| lost | — | none |
| deployed false alarms | 4 / 96 | 5 / 96 (residual channel 3 → 4: 2018-08-27, a day both new rules flag) |
| new residual rules' own holdout false alarms | — | 1 / 69 and 1 / 72 (the same day) |
| model and device rows | — | byte-identical |
| time to detection | — | not later on any scenario; the 80 % leak now on day 1 (was day 11) |

**Which physics carried each gain:**

| scenario | carrying rule | days | reading |
|---|---|---|---|
| damper leak 20 % / 50 % | `oa_flow_ratio_min_pos` | 261 / 261 of 261 | at the same minimum damper position the outdoor-air fraction of discharge flow is 0.1054 in health and 0.1275 with the 20 % leak; the leak adds air without moving the position |
| heating waterside fouling, moderate | `fan_specific_power` **rule band** (rules channel, 11 days); severe also gains the residual credit (31 days) | 11 | **an operating-point witness, not a coil measurement**: the healthy year runs the fan at its low speed 99.1 % of the time and never at its high speed; with a fouled heating coil the controller drives the fan to the high speed (18.08) on 1 % of minutes at moderate and 8 % at severe, where the fan's specific power (0.0227 W per cfm) is outside every band the healthy year could set (0.0066 low, 0.0119 medium). The unit works harder to deliver the same heat |

The four cooling waterside fouling files and the minor heating waterside file
stay missed: the fan never leaves its healthy speeds on them, and every
recorded value sits inside its band.

| P1 no loss | P2 budget | P3 both leaks | P4 waterside stays missed | P5 model rows identical | falsifiers |
|---|---|---|---|---|---|
| ✓ | ✓ (5/96; both rules 1 day) | ✓ | ✗ positive surprise: heating waterside moderate, through the fan's operating point | ✓ | none |

**Reading.** The fan coil unit had no coverage gap in the mapping sense, only in
the reading sense: two mapped columns nobody read carried the damper leaks
outright. The fouling gain is real but should be read for what it is: the coil
is not measured, the fan's response to it is.

## Series summary (X33a–e)

| system | columns mapped | detected before → after | deployed false alarms | new rules kept / written | lost |
|---|---|---|---|---|---|
| SDAHU | 12 → 26 of 30 | 14 → 14 / 14 | 1 → 1 | 4 / 4 | 0 |
| PFPU | 56 → 109 of 109 | 22 → 26 / 30 | 7 → 8 | 19 / 19 | 0 |
| SFPU | 56 → 109 of 109 | 21 → 25 / 29 | 6 → 9 | 23 / 23 | 0 |
| DDAHU | 79 → 114 of 114 | 45 → 50 / 55 | 3 → 3 | 25 / 25 | 0 |
| FCU | 29 → 29 of 29 | 40 → 43 / 47 | 4 → 5 | 2 / 2 | 0 |
| **all five** | **232 → 387 of 391** | **142 → 158 / 175** | **21 → 26 of 480** | | **0** |

Sixteen scenarios recovered, none lost, five false-alarm days added across
480 held-out days, the model and device rows identical on every system (the
log hashes change, because the new readers emit signature events), and
every band from the fault-free file. The seventeen that remain are coil
fouling on every system (waterside on all four water-coil units; the minor
airside files), whose recorded values sit inside every healthy band on every
column; on the parallel unit the waterside fouling is visible only on the ten
days a year the reheat valve saturates, which is too few to estimate a null.
The claim the series supports is narrow and testable: on these datasets, the
misses that remain are limits of what is recorded and how often, not of the
detector's vocabulary or its gate.

## Series analysis: does it hold up?

Three checks run after the series closed, on the committed artefacts, before any
conclusion was written (2026-09-25 08:30).

**1. The gains do not depend on the noise floor that moved.** Adding residual
rules made the residual channel evaluable on more holdout days (41 → 69 on the
fan-powered units), which lowered its per-day floor from 7.3 % to 4.3 %. Every
one of the fifteen residual-carried recoveries also clears the *pre-series*
floor (3 of 41): the weakest, the dual-duct cooling airside moderate file at 32
of 282 days, has p = 2 × 10⁻⁷ under either. The sixteenth recovery, the fan coil
unit's heating waterside moderate, is carried by the **rules channel** (11 rule
days of 268), whose null is the healthy year's silence over 365 days (3/365 =
0.8 %); under the holdout-based floor the other channels use (3 of 72 = 4.2 %)
it would not be significant. That gain is gate-dependent and is marked as such.

**2. Five of the sixteen are edge detections.** Distance of the fault-day median
from the healthy band, in band widths (a `[min, max]` band over training days):

| recovery | carrying rule | band-widths outside |
|---|---|---|
| SFPU fan-flow restriction | zone-fan specific power | 8.0 |
| FCU damper leak 50 % / 20 % | outdoor-air flow fraction | 4.4 / 1.7 |
| SFPU airside fouling severe | zone-fan specific power | 3.7 |
| DDAHU hot-deck static bias −2 in.wg | box static − deck static | 3.7 |
| PFPU room-temperature bias +4 °C | return − zone S | 2.1 |
| DDAHU heating waterside fouling minor | pump bypass flow | **0.8** |
| SFPU airside fouling moderate | zone-fan specific power | **0.7** |
| PFPU airside fouling severe | discharge − primary airflow | **0.7** |
| PFPU room-temperature bias +2 °C | return − zone S | **0.6** |
| PFPU airside fouling moderate | discharge − primary airflow | **0.3** |

The five in bold sit less than one band width outside the healthy extremes.
They are significant because they sit there on most days of the year, but
X31 showed that a `[min, max]` band's edge is set by single training days; a
different healthy year could move those edges by the margin these faults
clear. The eleven others are robust in this sense. A quantile band, or a
second healthy year, is the experiment that would settle it; it was not run.

**3. Disclosure: the readers were chosen with the fault files in view.** The
standing rule that no threshold sees fault data was kept: every band came from
the fault-free file, and the configurations were committed before any scorecard
was regenerated. But *which* columns to read, and which residuals to write, was
decided after a read-only scan of the fault files (the withdrawn X32) had shown
which recorded columns separate which misses. Each reader is a standard physical
relation an HVAC engineer would write from the point list (fan laws, specific
power, redundant sensor pairs, flow fractions), and the same readers were then
applied to every scenario, healthy holdout and system; but the selection was
fault-informed in the sense the X13 design disclosure uses, and the series'
gains should be read with that in mind. The claim the series licenses is
therefore: *these misses were reachable from the recorded columns with blind
thresholds*, not *a blind onboarding would have reached them*.

**What the series does and does not conclude.**
- It does show that on these datasets the detector's ceiling was set more by
  which columns it read than by its method: sixteen of thirty-three misses were
  coverage, none of the sixteen came through the process-mining channels, and
  the process-mining null stands unchanged.
- It does show the budget survives full coverage: five false-alarm days added
  over 480 held-out days, none above 10 in 96.
- It does not show that the framework generalises to a new building without
  fault files to scan; that is exactly the blind-onboarding test X17 and X19
  were, and their counts (45 of 55, 40 of 47) are the honest prior for it.
- The seventeen remaining misses are coil fouling whose recorded values sit
  inside every healthy band; one of them is visible but uncertifiable from one
  healthy year.

## X34 — component attribution: where in the HVAC system does the alarm point?

*Pre-registered (`docs/plans/2026-09-25-x34-component-attribution-prereg.md`,
0ea96c4) before any score was computed. Artefact
`outputs/component_attribution.json`; guard `tests/test_component_attribution.py`.*

Zone-level attribution (which terminal unit) was already measured: 37 of 50
correct, 0 wrong. This test asks the next question: does the rule that carries
each detection point at the *component* the fault was seeded in? For each of the
158 detected scenarios the carrying rule (most flagged days) is mapped to a
(subsystem, component) by a table fixed before scoring, and compared with the
seeded component.

| system | detected | exact component | same subsystem | wrong subsystem | unnamed |
|---|---|---|---|---|---|
| SDAHU | 14 | 13 | 0 | 1 | 0 |
| PFPU | 26 | 15 | 6 | 0 | 5 |
| SFPU | 25 | 14 | 9 | 0 | 2 |
| DDAHU | 50 | 38 | 7 | 5 | 0 |
| FCU | 43 | 29 | 0 | 14 | 0 |
| **all** | **158** | **109 (69 %)** | **22 (14 %)** | **20 (12.7 %)** | **7 (4 %)** |

| P1 exact ≥ 60 % | P2 exact or subsystem ≥ 85 % | P3 wrong ≤ 10 % | P4 bias via redundancy exact | falsifier |
|---|---|---|---|---|
| ✓ 69 % | ✗ 83 % | ✗ 12.7 % | ✓ (all 8) | **F-X34.a fired**: the component-level claim is withdrawn; the paper reports subsystem-level attribution with these rates |

**Reading the 20 wrong cases** (the table was fixed before scoring and is not
retuned; this is analysis, not a re-score):
- Fourteen are on the fan coil unit, and all name the component that *responds*
  to the fault rather than the one that caused it: the four room-temperature
  sensor biases are carried by the cooling coil's water-side temperature drop
  (the controller trusts the biased reading and over-cools, and the coil shows
  it); the seven airside and waterside fouling files are carried by the fan's
  specific power (the fan works harder against a fouled coil); the three control
  faults are carried by the valves they mis-drive. On a single-zone unit with one
  coil of each kind there is no second sensor to separate cause from response.
- Five are dual-duct zone-damper faults carried by the mixing-box static of zone
  SA. The seeded zone is not stated in the file names, and the rule points at the
  zone's box; the table mapped the box statics to the deck sensor end of the
  redundant pair, which is the wrong end for a damper fault. A two-ended mapping
  would score these as exact if the seeded zone is SA — a question for the
  dataset's authors.
- One is the single-duct outdoor-air-bias run, which the branch adjudication
  (E5) already reads as provenance rather than fault.
- The seven unnamed are detections carried by the frequency or oscillation
  channel alone (instability faults and one fan restriction): those channels
  count events and do not name a component.

**What the framework can honestly say.** It names the *zone* correctly and never
wrongly; it names the *subsystem* (which coil, which fan, which damper section,
which zone's box) in 83 % of detections; it names the exact component in 69 %;
and where it is wrong, it names the component that is reacting to the fault,
which is the first place a technician would look anyway. It does not name root
cause, and the pre-registered bar for calling it component-level attribution
was missed by 2.7 points.

## X37 — a diagnosis layer: signed rule patterns and redundant-pair consensus

*Pre-registered (`docs/plans/2026-09-27-x37-diagnosis-layer-prereg.md`) before
any score was computed. Three runs: run 1 (kept as `outputs/x37_diagnosis_run1.json`)
ignored copies that moved through the rules channel; run 2 (kept as
`outputs/x37_diagnosis_run2.json`) counted three or more copies moving in any
direction as consensus where the pre-registration says every copy in the same
direction; run 3 (`outputs/x37_diagnosis.json`) implements the design as written.
Both script defects were found by reading the rows, and both fixes are the
pre-registered wording, not a re-tune. Guard `tests/test_x37_diagnosis.py`.*

X34 measured where the carrying rule points. X37 asked whether three
fault-agnostic ingredients — the *sign* of every significant residual against
its healthy band, a *consensus* rule over redundant copies of one quantity, and a
leave-one-out nearest-pattern *family* vote — turn that into a diagnosis.

| | resolved | unresolved | correct | accuracy (resolved) | unresolved rate |
|---|---|---|---|---|---|
| family, leave-one-out over 158 detections | 114 | 44 | 85 | **74.6 %** | **27.8 %** |

| component | exact | same subsystem | wrong subsystem | unnamed |
|---|---|---|---|---|
| X34 (carrying rule) | 109 (69 %) | 22 | 20 (12.7 %) | 7 |
| X37 run 3 (with consensus) | 112 (70.9 %) | 23 | **16 (10.1 %)** | 7 |

| P1 family ≥ 80 %, unresolved ≤ 15 % | P2 exact ≥ 78 %, wrong < 10 % | P3 dual-duct dampers → one zone; deck biases → deck | P4 FCU cause/response unresolved | falsifiers |
|---|---|---|---|---|
| ✗ 74.6 %, 27.8 % | ✗ 70.9 %, 10.1 % | ✓ dampers 6/6 single copy; biases 14/16 consensus | ✓ 14 wrong, unchanged | **F-X37.a and F-X37.b fired** |

**Verdict.** The diagnosis layer is not adoptable as designed. The paper's
future-work sentence stands, and the component-level claim stays withdrawn
(the wrong-subsystem rate missed the bar by one case of 158).

**What the consensus rule did, per system.**
- DDAHU: the five zone-damper faults X34 scored wrong now score exact (one
  mixing-box copy moves alone, so the diagnosis names that zone's box), and
  fourteen of the sixteen deck sensor biases are called at the deck because all
  four copies move the same way. This is the mechanism the pre-registration
  described, and it worked where the redundancy is real.
- SFPU and PFPU: the return-minus-zone group is *not* a redundant pair in the
  sense required. A fault in one zone moves that zone's copy one way and, because
  the return air is the mix of all zones, the other three copies the opposite
  way (SFPU damper stuck 0 %: zone S −10.6 °F, zones I/W/E +2.3 to +2.6 °F).
  Under the pre-registered rule this is "no consensus" (fourteen SFPU rows) and
  the verdict falls back to the carrying rule; run 2, which ignored direction,
  blamed the shared return-air sensor in eleven of them. One PFPU room-sensor
  bias (+4 °C) does move all four copies the same way and is now called at the
  return-air sensor: wrong.
- FCU and SDAHU: no redundant copy exists; verdicts identical to X34.

**Why the family vote misses.** The 29 wrong family calls are almost all pairs the
recorded signals cannot separate with signs alone: a stuck zone damper and a
biased zone airflow sensor (9 cases; the zone flow-tracking rule is a mismatch
kind and carries no sign); a restricted filter and a fouled cooling coil on the
fan coil unit (4; both are "same speed, less air"); cooling-side and heating-side
airside fouling on the fan coil unit (4; the fan-side witnesses are identical);
a leaking and a stuck valve (5). The 44 unresolved are scenarios whose signed
pattern has no neighbour above Jaccard 0.5 — sixteen on DDAHU, where most
families have one or two members, and the instability faults everywhere, which
only the frequency and oscillation channels see.

**What can honestly be said.** Signs and consensus fix the one class of error
X34 could name (the dual-duct damper cases) and otherwise leave the picture
where X34 left it: zone right, subsystem right in 85 %, exact component in 71 %,
family from pattern alone in three of four resolved cases. Separating cause from
response, or a stuck actuator from a biased sensor on the same loop, needs a
witness these datasets do not record or a test the detector cannot run
passively.

## X35 — field conditions on the post-coverage configurations, all five systems

*Pre-registered (`docs/plans/2026-09-27-x35-field-conditions-post-coverage-prereg.md`)
before any perturbed file was scored; configurations as of 36b9e6e. Same facade
and arms as X31 (`scripts/x31_field_conditions.py`, unchanged); ledger
`scripts/x31_ledger.py --x35` → `outputs/x35_field_conditions.json`; per-system
artefacts `outputs/x31_field_conditions_<system>.json` regenerated (the X31
artefacts of 2026-09-24 are under `outputs/x31_archive/`). Guard
`tests/test_x35_field_conditions.py`. Deviation: the ledger of 2026-09-27
evaluated X31's bars; X35's six bars were added to it after the arms had run,
copied from the pre-registration unchanged, and both sets are in the artefact.
The DDAHU `combined` arm was interrupted by a machine restart and re-run alone
(`--arms combined`), resuming the artefact; the other four arms are the original
run.*

The coverage series added 73 residual rules, some with healthy bands 0.01–0.02
units wide, and five of its sixteen recoveries sit less than one band width
outside the healthy extremes. X31's robustness claim was dated to before the
series. X35 asks whether the shipped configurations survive the same four
conditions.

| system | clean | field noise | COV + gaps | schedule | combined |
|---|---|---|---|---|---|
| SDAHU | 14/14 @ 1 | 14 @ 2 | 13 @ 0 | 14 @ 1 | 14 @ 2 |
| PFPU | 26/30 @ 6 | 25 @ 6 | 25 @ 6 | 26 @ 7 | 25 @ 5 |
| SFPU | 25/29 @ 4 | 25 @ 4 | 25 @ 6 | 25 @ 3 | 25 @ 3 |
| DDAHU | 50/55 @ 0 | 50 @ 1 | 50 @ 2 | 50 @ 0 | 49 @ 2 |
| FCU | 43/47 @ 4 | 43 @ 4 | 43 @ 4 | 43 @ 4 | 43 @ 2 |

(detected @ holdout false-alarm days of 96; alignment channels off, so the
absence channel is not exercised and DDAHU's clean arm shows 0 where the
scorecard's 3 are absence days.)

| P1 budget ≤ 10 and ≤ clean + 3 | P2 noise/COV within −4 | P3 ≥ 2 edge recoveries lost under noise | P4 schedule within ±3 | P5 combined within −6 | P6 clean arm = scorecard | falsifiers |
|---|---|---|---|---|---|---|
| ✓ worst 7/96 | ✓ worst −1 | ✗ one lost | ✓ worst 0 | ✓ worst −1 | ✓ all five | **none** |

**Detections lost, all named.**
- SDAHU outdoor-air bias 4 °C under COV + gaps (the same loss as X31; the
  branch adjudication E5 already reads this file as provenance rather than fault).
- PFPU reheat-coil airside fouling *moderate* under field noise, COV + gaps and
  combined: the one edge recovery that noise removes. Its margin was the
  smallest of the five (X33 series analysis), and it is the only one of the
  five that moved. The other four edge recoveries (PFPU airside severe, PFPU
  +2 °C bias, SFPU airside moderate, DDAHU heating waterside minor) held under
  every condition.
- DDAHU cooling-coil waterside fouling *moderate* under combined only.

**False alarms.** The worst condition on any system is PFPU under the schedule
shift at 7 of 96 (clean 6); no system exceeds clean + 2. The new narrow bands
did not turn field noise into false alarms: the residual channel's holdout
days under noise are 0, 3, 3, 1, 2 against clean 0, 3, 3, 0, 4.

**Reading.** P3 predicted that the coverage series had bought fragile
detections; one of five was fragile, four were not. The claim the papers can
carry is the one X31 carried, now on the shipped configurations of all five
systems: sensor error, change-of-value logging with gaps and schedule shifts
cost at most one detection per system per condition and never break the
budget.

## X36 — quantile bands instead of extreme bands: what the edge recoveries cost

*Pre-registered (`docs/plans/2026-09-27-x36-quantile-band-prereg.md`) before any
score was computed; configurations as of 36b9e6e. Alternative calibration arm,
not an adoption: bands at the 2nd and 98th percentiles of the training-day scores
(same floors) instead of [min, max], every residual rule on every system, through
the facade with the alignment channels off (as X31/X35), against the extreme-band
arm of the same facade. Script `scripts/x36_quantile_band.py`; artefact
`outputs/x36_quantile_band.json`; guard `tests/test_x36_quantile_band.py`.*

X31 showed a band edge set by a single training day; the series analysis found
five coverage recoveries less than one band width outside the healthy extremes.
The question was whether a calibration that ignores single days keeps those
recoveries, and what it costs.

| system | extreme: detected @ FP | quantile: detected @ FP | ΔFP | residual FP (extreme → quantile) | median band width ratio | edge recoveries kept |
|---|---|---|---|---|---|---|
| SDAHU | 14/14 @ 1 | 14/14 @ 1 | 0 | 0 → 0 | 0.95 | — |
| PFPU | 26/30 @ 6 | 26/30 @ 10 | **+4** | 3 → 8 | 0.88 | 3 of 3 |
| SFPU | 25/29 @ 4 | 25/29 @ 8 | **+4** | 3 → 7 | 0.92 | 1 of 1 |
| DDAHU | 50/55 @ 0 | 50/55 @ 3 | +3 | 0 → 3 | 0.93 | 1 of 1 |
| FCU | 43/47 @ 4 | 43/47 @ 6 | +2 | 4 → 6 | 0.91 | — |

| P1 FP rise ≤ 3 and ≤ 10 | P2 edge recoveries kept | P3 ≥ 2 new detections | P4 no loss | falsifiers |
|---|---|---|---|---|
| ✗ +4 on PFPU and SFPU | ✓ all five | ✗ none gained | ✓ none lost | **F-X36.a fired**: quantile bands are not a budget-safe alternative |

**Reading.** Bands about ten per cent narrower buy nothing: no scenario on any
system moves in either direction, and the false-alarm days added (13 over the
five systems, all on the residual channel) are healthy days that the extreme
band covered and the percentile band does not. The five edge recoveries survive
the narrower band, so they were not artefacts of the exact extreme; and no
currently missed scenario comes within reach, so the misses are not a
calibration margin away. The deployed calibration stays [min, max] with floors;
X31's single-day fragility is a property of the band edge, not a reason to move
it inward.

## X38 — the open-fdd Guideline 36 battery, repaired: current practice on the same exam

*Pre-registered (`docs/plans/2026-09-27-x38-guideline36-repaired-prereg.md`,
12dfa92) before the repaired adapter ran; the 2026-09-11 artefacts are void and
live in `outputs/void/`. Run 1 (2026-09-28 02:30–03:17) held every prediction
with the battery flagging 77, 96 and 96 of 96 healthy holdout days; two
independent audits then found six adapter defects and one defect of the
pre-registered design, all recorded in Amendment 1 (aa40f2a, written before the
re-run; run-1 artefacts kept as `*_run1.json`, not quoted). Run 2 is reported
here. Artefacts `outputs/openfdd_baseline_{sdahu,pfpu,sfpu}.json`,
`outputs/x38_guideline36.json`; guard `tests/test_x38_guideline36.py`.*

**What was repaired between the runs.** SDAHU's fan command was a dead constant
(SF_SPD = 0.9 on every row, which the project's own sensor map records), so FC1's
full-speed condition was always true; the terminal-unit rules were gated on the
box fan, which on a parallel unit runs only while heating; the hunting rule read
a binary fan status as a hunting loop; night-cycle was graded as occupied; a
single-duct leaving-air rule was applied to boxes that mix plenum air by design;
FC6 on SDAHU read a column that is not in cfm. The design defect: gating the
battery once, on the pooled union of its rules, is a tautology when the union
flags every healthy day (floor 1.0). Amendment 1 therefore reports three
framings and applies the falsifier to each: G1 pooled (as pre-registered), G2
per rule against its own holdout false alarms (STRATA's per-channel structure),
G3 the rules-channel treatment (only rules silent on the healthy year, ≤ 3 days
of 365, held to the 3/365 null), plus a site-datum arm S for FC6.

| system | scored | battery raw | G1 pooled (all / demoted) | G2 per rule | G3 silent rules @ FP | STRATA @ FP (minus-rate / all eight) |
|---|---|---|---|---|---|---|
| SDAHU | 14 | 14 | 1 / 7 @ 49 / 33 | 12 | **12 @ 1** | **13 @ 1** / 15 |
| PFPU | 30 | 30 | 0 / 0 @ 96 / 96 | 30† | **8 @ 0** | **26 @ 8** / 15 |
| SFPU | 29 | 29 | 0 / 0 @ 96 / 95 | 29† | **9 @ 0** | **25 @ 9** / 9 |

(FP = healthy holdout false-alarm days of 96. STRATA's SDAHU count is 13 because
the outdoor-air-bias detection is adjudicated as branch provenance, ERRATA E5.
† not detection: see below.)

| P1 | P2 | P3 (G1 / G2 / G3 / S) | P4 | P5 | P6 | P7 | falsifiers |
|---|---|---|---|---|---|---|---|
| ✓ | ✓ (vacuous) | ✓ / ✗ / ✗ / ✗ | ✓ | ✗ | ✗ | ✗ | **F-X38.a fired under G2 (PFPU, SFPU), G3 (all three) and S (PFPU, SFPU)** |

**G2 on the fan-powered units is not detection.** FC9, FC13 and FC14 flag the
*identical* day sets on the healthy file and on every fault file (88, 130 and 72
days of 365): the fault files' air-handler columns are the healthy file's. They
pass the per-rule gate because each rule's holdout rate (FC9 14 of 96, 14.6 %)
sits below its full-year rate (24 %), and 88 of 365 against a 14.6 % null is
significant at p < 10⁻³. That is the gate STRATA's channels are held to, and
STRATA does not suffer it because its onboarding silences every rule on the
whole training year before the holdout floor is measured. The lesson is a
property of the floor, recorded as such: a holdout-sample null is only valid for
a channel that is stationary across the year, and silence on the training year
is what makes STRATA's channels so.

**G3 is the framing that compares like with like.** With the battery treated
exactly as STRATA treats its own signature rules — keep what is silent on the
healthy year, hold it to 3/365 — the repaired open-fdd battery detects 12 of 14
on the single-duct air handler at 1 false-alarm day (FC8, FC10, FC13 carry the
coil faults; FC9 alone sees the 10 % and 25 % stuck dampers and is not silent),
against STRATA's 13 at 1. On the terminal units it detects 8 of 30 and 9 of 29
at 0 false-alarm days (PID-HUNT-1 on the unstable room loop; VAV-3/4/5 and
VAV-REHEAT on the larger stuck and leaking reheat valves and dampers), against
STRATA's 26 and 25 at 8 and 9. F-X38.a fired as worded on every system: on
SDAHU because equal false alarms is "matches", on the terminal units because
zero false alarms is fewer. The pre-registered claim ("STRATA detects at least
as many at a lower false-alarm rate") cannot be made. What can: on the air
handler the two are within one detection and one false-alarm day of each
other; on the terminal units STRATA detects three times as many faults and
pays eight or nine false-alarm days for them, and the difference is
*coverage* — STRATA's residual readers on the per-zone columns (X33b, X33c) —
not the gate.

**Arm S and P7.** Supplying FC6's design minimum outdoor-air flow from the
fault-free year (250 and 397 cfm) leaves it at 94 and 95 of 96: as implemented
the rule has no operating-state gate, so every economizing minute exceeds the
band. P7 was wrong. P5 (G2 SDAHU ≥ 1 and STRATA ≥ battery everywhere) and P6
(≤ 3 silent rules per system) were wrong on the fan-powered units (17–18 silent
rules there, because most AHU rules never fire on a unit whose air handler
holds 55 °F all year).

**Caveats for print.** (i) These are open-fdd 4.4.1's *installed defaults*, not
Guideline 36's: the library's own parameter labels cite GL36 values that are
looser on every rule that fired (sensor errors 1.15 °F vs 2–5 °F, fan heat rise
0.55 vs 2 °F, mode delay 0 vs 30 min, FC6 band 15 % vs 30 % and 5 vs 10 °F,
FC13 full-cooling 1 % vs 99 %); with GL36's values FC8 (fan heat rise 2.15 °F
on the fan-powered air handler) would largely not fire. (ii) The terminal rules
carry fixed comfort bands (VAV-1 70–75 °F against occupied setpoints 68/72;
VAV-2 68 °F against a 55 °F setback) and flow thresholds equal to the boxes'
minimum flow; none reads the building's setpoint columns. (iii) FC4 on SDAHU
counts damper crossings because the cooling valve never reads exactly zero.
(iv) A battery that flags every healthy day flags every fault day, so the raw
counts of P2 say nothing. (v) STRATA's rules channel is held to 3/365 while the
battery's per-rule floor under G2 is max(fp, 3)/96, looser for the battery;
G3 removes that asymmetry by construction.

**Re-audit of run 2 (audit A, after Amendment 1; audit B independently
reproduced every run-1 number and the SDAHU repair).** No adapter defect
remains; the six repairs are verified in the code and by independent
recomputation. Four caveats change what the framings may be said to show, and
travel with the numbers:
- *G2 admits rules that detect the healthy file itself.* Applied to the
  fault-free year's own training days, the per-rule gate "detects" the healthy
  file through FC9 and FC14 on PFPU and FC13 on SFPU. Excluding those
  self-detecting rules (post hoc, `G2_prime_post_hoc` in the ledger) gives 12 of
  14, 15 of 30 and 17 of 29 against STRATA's 13, 26 and 25, at a union
  false-alarm rate still 96 of 96 on the fan-powered units.
- *G3's rule selection is in-sample.* Silence is judged on the whole fault-free
  year including the 96 holdout days, then those rules' holdout days are
  reported; STRATA's channels are selected on training days only. No numeric
  effect here (FC13 has two training-day flags and stays silent), but the
  SDAHU tie of 1 against 1 pairs a post-selection count with an out-of-sample
  one.
- *The outdoor-air-bias file is adjudicated on one side only.* STRATA's
  detection of it was removed by the branch adjudication (E5); the battery's
  (FC8, 65 days) is counted and is the sole battery-only file. FC8 passes the
  same branch-immunity control (it fires on no fault-branch file whose fault
  cannot touch it), so the count is legitimate, but removing the file from both
  sides gives 11 of 13 against 13 of 13 and keeping it un-adjudicated on both
  gives 12 of 14 against 14 of 14: under every reading STRATA detects more on
  SDAHU, and "matches" rests on the false-alarm tie alone.
- *Scope.* STRATA's two SDAHU-only files (stuck damper 10 % and 25 %) are caught
  by position-against-command signature rules; open-fdd ships rules of that
  kind (DMP-1, VLV-1, CMD-1) which the pre-registered FC1–FC15 battery
  excludes. Arm S's design datum is the occupied-median outdoor-air flow, not
  the minimum-outdoor-air mode's; 63 % of FC6's remaining flags are economizing
  minutes and the rest minimum-position minutes at low total airflow.
- *Stated, not defects:* on SDAHU the fan status equals the occupancy bit, so
  every battery rule is scored in occupied mode only, as STRATA's universe is;
  the binomial gate treats days as independent on both sides; VAV-2's 68 °F
  setback threshold against a simulated 55 °F setback is a site constant, not a
  tolerance, and demotion removes only FC6, leaving VAV-2 at 94 of 96.

