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
