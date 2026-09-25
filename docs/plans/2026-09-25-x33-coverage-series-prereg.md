# X33 — the coverage series: every recorded column audited, mapped or excluded with a reason, one system at a time (pre-registration)

**Written 2026-09-25 02:30, before any configuration is changed. Pre-configuration commit: `8f06f19`.**

## Why

The X32 scan found that for six of the fourteen reachable misses the decisive
signal is a recorded column that no configuration maps (zone-fan power,
pressure and discharge flow on the series unit; pump flows on the dual-duct
unit). The configurations were written from the control sequences, not from
an audit of every recorded column. X33 audits every column of every system,
maps every usable one, gives each a reader (a rule, a physics-named residual,
a gate or an oscillation signal), and excludes the rest with a written reason.
Order: SDAHU, PFPU, SFPU, DDAHU, FCU — the project's onboarding order, simplest
first. Each system is scored, analysed and closed before the next is opened.

## Standing rules for every system in the series

- Thresholds and bands come from the documentation and the fault-free file
  only; no fault file is opened before scoring.
- Configuration only. A column that needs a new residual operator is
  reported and pre-registered as a source change before it is used.
- Leaked columns (ERRATA E3: `SA_SP`, `SA_SPSPT` on SDAHU) and constant
  columns are excluded with the reason written in `sensors.yaml` under
  `unmapped:`; a new guard (`tests/test_sensor_coverage.py`) fails if any
  numeric column of an audited system is neither mapped nor excluded.
- The state alphabet is not changed in this series, so the model and device
  rows must regenerate identically; coverage acts through the physics and
  statistical channels only.
- **Adoption rule (fixed now):** a new channel is kept if it is credited on at
  least one scenario or its own holdout false alarms are ≤ 1 day; a channel
  that is credited nowhere and costs more than one holdout day is removed
  before the next system opens, and the removal is recorded.
- Budget: deployed false alarms ≤ 10 of 96 and ≤ clean + 3 on every system.
- Ledger: `scripts/x33_coverage.py --system <s> --before <commit>` →
  `outputs/x33_coverage_<s>.json` (before/after diff, per-channel credits,
  each new channel's own holdout false alarms); guard
  `tests/test_x33_coverage.py`; results in `PHASE12_RESULTS.md`.

## X33a — SDAHU (30 columns, 12 mapped before)

| column | meaning (documentation) | decision |
|---|---|---|
| SF_WAT, RF_WAT | supply / return fan power (W) | map (SF_POWER, RF_POWER); residuals below |
| SA_CFM, RA_CFM | supply / return airflow (cfm) | map (SA_FLOW, RA_FLOW); residuals below |
| SF_CS, RF_CS | fan speed control signal | map (SF_SPEED_CMD, RF_SPEED_CMD) |
| RF_SPD | return fan speed position | map (RF_SPEED_POS); mismatch rule vs RF_SPEED_CMD |
| SF_SPD | supply fan speed position | **exclude: constant 0.9 for the whole year** |
| SF_SPD_DM, RF_SPD_DM | fan enable commands (0/1) | map (SF_CMD, RF_CMD); gates |
| ZONE_TEMP_1–5 | zone air temperatures | map; oscillation signals (healthy occupied range reaches 110 °F, so no level rule is possible) |
| OA_CFM | outdoor airflow | **exclude: constant for the whole year** |
| SA_SP, SA_SPSPT | duct static and its setpoint | **exclude: ERRATA E3 provenance leak** |

New readers (all bands from the healthy year; residual bands learned on
training days with per-rule floors at ~10 % of the healthy median):
1. `sf_specific_power` = SF_POWER / SA_FLOW (W per cfm), gated on SF_CMD, occupied.
2. `rf_specific_power` = RF_POWER / RA_FLOW, gated on RF_CMD, occupied.
3. `sf_flow_per_speed` = SA_FLOW / SF_SPEED_CMD (fan law, flow ∝ speed), gated on SF_CMD and SF_SPEED_CMD > 0.05, occupied.
4. `rf_speed_mismatch`: |RF_SPEED_POS − RF_SPEED_CMD| > 0.05 sustained 60 min (silent on the healthy year: the two columns are identical).
5. Oscillation channel on ZONE_TEMP_1–5, deadband 0.5 °F (healthy holdout exceedance 0 of 96 on every zone in the pre-check).
Not added: RA_FLOW / SA_FLOW (identically 1.000 in the simulation; carries nothing).

### Predictions (SDAHU already scores 14/14, so the test here is cost and coverage, not gain)
- **P1.** No scenario lost: 14/14 naive (13 adjudicated) after.
- **P2.** Deployed false alarms ≤ 4 of 96 (1 before); no new residual channel exceeds 3 holdout days on its own.
- **P3.** At least one new channel is credited on at least one scenario (the fan-side channels on a stuck-damper or stuck-coil scenario, whose changed operating point the supply fan must follow).
- **P4.** Time to detection not later on any scenario.
- **P5.** Model and device rows byte-identical (state alphabet unchanged).

### Falsifiers
- **F-X33a.a** P1 fails → the channel responsible is named and removed; the loss is reported.
- **F-X33a.b** P2 fails → the channel responsible is removed under the adoption rule; reported.
- **F-X33a.c** P5 fails → a coverage change reached the process-mining channels; investigated before anything else.
- A failed P3 or P4 is reported as a wrong prediction.

## X33b — PFPU, parallel fan-powered unit (109 columns, 56 mapped before)

**Written 2026-09-25 03:30 after X33a closed, before the PFPU configuration is changed. Pre-configuration commit: `6b7512a`.** Bands below come from the fault-free file's occupied, supply-fan-on minutes (quantiles logged in the configuration); no fault file opened.

| columns | decision / reader |
|---|---|
| RMCLGSPT_i, RMHTGSPT_i (zone cooling/heating setpoints, two values each) | map (ZONE_CLG_SP_i, ZONE_HTG_SP_i); context for the zone-temperature rules; no new reader (the recorded zone temperature is the controller's own reading, which tracks its setpoint even when biased) |
| VAV_DAT_i (zone discharge air temperature) | map; residual `dat_minus_sa_i` = ZONE_DAT_i − SA_TEMP gated reheat valve closed (< 0.02) and zone fan off |
| VAV_DA_CFM_i (zone discharge airflow) | map; residual `da_minus_pm_i` = ZONE_DA_FLOW_i − ZONE_FLOW_i gated zone fan off (discharge equals primary when the parallel fan is off) |
| VAV_FAN_DP_i, VAV_FAN_WAT_i (zone fan pressure, power) | map as context; no reader (the parallel fan runs intermittently at a near-constant 18.9 W; no seeded fault touches it on this unit) |
| SF_WAT, RF_WAT, SA_CFM, RA_CFM, SF_SPD, RF_SPD, SF_CS, SF_DP, RF_DP, RF%SFSPD | map; readers `sf_specific_power`, `rf_specific_power`, `sf_flow_per_speed`, `static_per_speed2` (SA_SP / SF_SPD², X27 kind) |
| SA_SP, SA_SPSPT (duct static and setpoint; not E3 — that erratum is SDAHU-only, and here SA_SP varies) | map; rule `static_setpoint_deviation` (|SA_SP − SA_SPSPT| > 0.3 in.wg sustained 30 min, fan on; healthy p99.9 0.17) |
| OA_CFM, OA_HUMD, RA_HUMD, SA_HUMD, CHWC_EAH | map as context (no humidity or outdoor-flow rule in the sequence; recorded for the operator) |
| HWC_DAT, HWC_EWT, HWC_LWT, HWC_MWT, HWP_GPMC, HWP_GPMT, CHWC_DAT, CHWC_EWT, CHWC_LWT, CHWC_MWT, CHWP_GPMC, CHWP_GPMT | map; readers `chwc_waterside_dT` (CHWC_LWT − CHWC_EWT, valve open), `hwc_waterside_dT` (valve open; the AHU heating valve opens on 128 healthy minutes, so this channel will mostly abstain) |
| RA_TEMP vs zones | residuals `ra_minus_zone_i` = RA_TEMP − ZONE_TEMP_i (occupied, fan on): the return air is the mix of the true zone temperatures, so a biased zone sensor shifts this residual by the bias |
| excluded | none: every column is either mapped with a reader or mapped as context |

### Predictions
- **P1.** No scenario lost (22 of 30 before).
- **P2.** Deployed false alarms ≤ 10 of 96 and ≤ 7 + 3 (7 before); no new residual rule > 3 holdout days on its own; channels failing this are removed under the adoption rule.
- **P3.** At least one of the two room-temperature-bias misses (+2 °C, +4 °C) is detected, through `ra_minus_zone_i`.
- **P4.** All six reheat-coil fouling misses stay missed (their recorded signals sit within a few per cent of healthy on every column; the X32 scan found no unmapped column that separates them).
- **P5.** Model and device rows byte-identical.

### Falsifiers
- **F-X33b.a** P1 fails → channel named and removed; loss reported.
- **F-X33b.b** P2 fails → channel removed under the adoption rule; reported.
- **F-X33b.c** P5 fails → investigated before anything else.
- A failed P3 is a wrong prediction; a failed P4 is a positive surprise, reported as such.
