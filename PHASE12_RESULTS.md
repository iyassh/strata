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
| new residual rules' own holdout false alarms | — | 0 / 79, 0 / 79, 0 / 79 |
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
| new residual rules' own holdout false alarms | — | 0 or 1 day each (18 rules; the heating-coil rule never evaluates) |
| model and device rows | — | byte-identical |
| time to detection | — | not later on any scenario; all four gains on day 1 |

**Which physics carried each gain** (flagged days of 261, facade bands):

| scenario | carrying rule | days | reading |
|---|---|---|---|
| airside reheat fouling, moderate | `da_minus_pm_S` (zone S discharge airflow − primary airflow, zone fan off) | 172 | with the zone fan off the discharge-minus-primary airflow sits at −27 cfm in health (5th–95th percentile −45 to −23); at severe fouling it sits at −10 (−15 to −9) and at minor fouling it does not move (−25); the coil's airside resistance is in the primary air's path, and the flow relationship moves while every temperature the controller holds stays inside its band |
| airside reheat fouling, severe | `da_minus_pm_S` | 227 | same; the minor file moves it on 0 days and stays missed |
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
day is a residual day on 2018-12-24, inside budget and inside the adoption
rule. Every new rule is kept.
