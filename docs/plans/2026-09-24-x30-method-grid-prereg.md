# X30 — the method-coverage grid: does any other process-mining instrument detect what the deployed one misses? (pre-registration)

**Written 2026-09-24 (plan item A2) before any cell is computed.**

## Why

The null (conformance adds no detection on five systems) has been tested
with one miner (inductive, noise 0.2), one case notion (the calendar day),
and one conformance measure (alignment fitness, plus token-based device
conformance). The review's objection: a different instrument might see
what this one does not. X22 showed what alignment fitness can and cannot
see under injected violations; X30 asks the detection question directly
with the other instruments pm4py offers.

## Cells (fixed now)

Discovery on each system's fault-free training days (the X25 split),
threshold on the calibration slice at the 1 % quantile of the per-day
score, false alarms on the holdout, exactly as the deployed channel:

| id | discovery | per-day score |
|---|---|---|
| IM00-align | inductive miner, noise 0.0 | alignment fitness |
| IM05-align | inductive miner, noise 0.5 | alignment fitness |
| IM02-token | inductive miner, noise 0.2 (deployed net) | token-replay trace fitness |
| HM-align | heuristics miner (default dependency threshold) → Petri net | alignment fitness |
| SKEL | log skeleton (declarative: equivalence, always-before/after, never-together, activity frequency bounds) | 1 − violations per event |
| DECLARE | Declare constraints discovered on training days | Declare per-trace fitness |
| TEMPORAL | temporal profile (mean and std of inter-activity times) | 1 − deviations per event at ζ = 3 |

Case notion stays the calendar day; the alphabet stays the state alphabet
(the wall is not crossed). Scored scenarios: only the scenarios the
deployed detector misses under the final gate (8 + 8 + 10 + 7 on PFPU,
SFPU, DDAHU, FCU; SDAHU misses none), plus each system's healthy holdout.
A cell "detects" a scenario if its flagged-day count clears the deployed
model gate (`model_significant`, floor max(fp, 3)/n on the cell's own
holdout false alarms) — the same rule as the deployed channel.

## Predictions

- **P1.** No cell detects any deployed-missed scenario while keeping its
  holdout false alarms ≤ 3 of the holdout days.
- **P2.** At least one cell (TEMPORAL or SKEL) has holdout false alarms
  above 10 %: an instrument that "detects" the misses will do so by
  flagging healthy days too.
- **P3.** Every cell that runs completes on every system (no
  computational-impracticality exclusions at the day case notion).

## Falsifiers

- **F-X30.a** P1 fails → the null is bounded to the deployed instrument;
  the cell and scenario are named, and adoption goes through its own
  pre-registration with the full budget check.
- **F-X30.b** P3 fails on a cell → that cell is reported as not evaluated,
  never as a null.

## Artefacts

`outputs/x30_method_grid.json`; guard `tests/test_x30_method_grid.py`.
