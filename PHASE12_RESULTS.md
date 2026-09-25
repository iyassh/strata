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
| new residual rules' own holdout false alarms | — | 22 rules: 0 (17), 1 (4), 2 (`static_per_speed2`) |
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
systems.

### Gap analysis after X33a–c: what the remaining fan-powered misses look like

Eight scenarios remain missed on the two fan-powered units, all reheat-coil
fouling: airside minor on both units, and waterside minor, moderate and severe
on both. Their residual channels flag 3–18 of 365 days; the strongest witness is
the water-side temperature drop on the series unit's severe file (15 days), below
the per-day floor of 3 in 69 (4.3 %).

**The waterside fouling is visible, but not certifiable, on the parallel unit.**
The fault is implemented as a reduced maximum water flow: with the reheat valve
more than 90 % open, the healthy coil passes 6.03 gpm and the fouled coil 5.42,
4.22 and 3.01 gpm at minor, moderate and severe (day medians; every such day is
outside the healthy band of [6.015, 6.030]). Below 80 % open the flow tracks
the valve position identically in health and fault, so a flow-per-position
residual over the whole range does not move (median 2.143 against 2.136). The
witness therefore exists only on days when the valve saturates: 10 days in the
healthy year (5 training days, 1 holdout day) and 10–15 days in each fault file.
Two consequences, both of the framework's own discipline: the rule's healthy
band rests on five days and its false-alarm rate on one, so no null can be
estimated for it; and under the per-day gate, 15 flagged days of 365 (4.1 %)
sit below the residual channel's floor. A one-year healthy record does not
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
