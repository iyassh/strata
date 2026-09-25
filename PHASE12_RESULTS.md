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
