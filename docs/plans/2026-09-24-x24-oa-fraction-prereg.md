# X24 — an outdoor-air-fraction residual (Guideline 36 FC6 / APAR lineage) as a new rule kind (pre-registration)

**Written 2026-09-24 after the review round (plan item B1) and before the
kind is implemented or any healthy or fault file is scored with it.**

## Why

Every system records outdoor, return and mixed air temperature and the
outdoor-air damper position and command, yet no rule compares the damper's
*effect* — the outdoor-air fraction the mixed-air temperature implies —
with its position. The domain review called this the most conspicuous gap
in a rule set claiming APAR lineage. The fan coil unit's 20 % damper-leak
scenario is the one miss the rule is aimed at; the dual-duct and single-duct
damper faults are already caught by the mismatch rule, so on those systems
the rule may only add day-level coverage or false alarms.

## Definition (fixed now)

New `paired_residual` option `op: oa_fraction`: residual =
`(RA_TEMP − MA_TEMP) / (RA_TEMP − OA_TEMP) − OA_DMPR_POS`, defined only
where `|RA_TEMP − OA_TEMP| > 10 °F` (the PNNL/G36 conditioning gate; the
fraction is ill-posed when return and outdoor converge) and the unit is
moving air (fan on where a fan signal exists; operate mode otherwise). The
mixed-air temperature is assumed to be a mass-weighted blend of return and
outdoor air, i.e. the fraction is compared with damper *position*, not
flow, so on a unit whose damper–flow relation is non-linear the healthy
band absorbs the offset. It is scored as a residual channel (daily median,
band learned on healthy training days with the standing 0.5 width floor
and exceedance margin — in fraction units, floor and margin 0.05) and as a
rule event (sustained 60 min outside a fixed band of ±0.25 fraction).

Config keys per system: `oa_fraction_residual` under `events:` with
`a: RA_TEMP, b: MA_TEMP, c: OA_TEMP, pos: OA_DMPR_POS`, gates as above;
added to `detection.residual_channels`. Nothing else in any config changes.

## Predictions

- **P1 (regression).** With the kind implemented and no config touched, all
  five scorecards regenerate byte-identically.
- **P2 (healthy silence).** The rule event fires on ≤ 3 days of each
  fault-free year (rule-of-three floor) after at most one logged threshold
  adjustment made on healthy data alone.
- **P3 (target).** `FCU_OADMPRLeak_20` becomes significant on the residual
  or rules channel; `OADMPRLeak_50/80` stay detected.
- **P4 (budget).** Deployed union false alarms stay ≤ 10 of 96 on every
  system to which the rule is added.
- **P5 (no loss).** No previously detected scenario loses detection on any
  system.

## Falsifiers (binding)

- **F-X24.a** P1 fails → the implementation touched shared code paths;
  fix before anything is scored.
- **F-X24.b** P3 fails on FCU → the leak is not visible in the mixed-air
  temperature at 20 %; the rule stays (if P2/P4 hold) and the miss is
  reported as a limit of the recorded points.
- **F-X24.c** P4 fails on any system → the rule is removed from that
  system's config and the failure reported.
- **F-X24.d** P5 fails → investigate; the rule cannot be adopted while it
  removes a detection.

## Scope

Systems: all five have the points. Order of scoring: FCU first (target),
then SDAHU and DDAHU, then the fan-powered units (AHU-level points on
terminal-unit datasets; the rule may abstain there).

## Artefacts

Updated `benchmark_v6_*.json`, `union_fpr_*.json` for the systems where
the rule is added; `outputs/x24_oa_fraction.json` ledger; guard
`tests/test_x24_oa_fraction.py`.
