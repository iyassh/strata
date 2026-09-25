# X29 — refrigerant-side observability: the simulated rooftop unit (pre-registration)

**Written 2026-09-24 (plan item B4) after reading the RTU documentation's
simulated-dataset sections and the baseline file's header only, before any
fault file is opened and before any rule is written.**

## Why

Four independent quantities computed from the recorded air- and water-side
points — a temperature band (X13), an enriched alphabet (X14/X15), the
water-side ΔT, and a coil UA (X28) — miss the same coil-fouling scenarios
on the dual-duct and fan coil units. The claim the write-ups now make is
that fouling on those datasets is a property of the recorded points, not
of the detector. That claim has a test: a dataset where the fouled
component's own physics *is* recorded. LBNL's simulated rooftop unit
(NREL Modelica–EnergyPlus co-simulation of a 5-ton unit, 100 days
2018-07-20 → 10-28, one-minute, 25 points) records refrigerant condensing,
discharge and suction pressures and temperatures, and seeds condenser
fouling and evaporator fouling at 10/20/30/40/50 % plus liquid-line and
suction-line restrictions and refrigerant over/undercharge (24 fault
files, one baseline). If the detector, configured from the documentation
and the baseline only, catches fouling here, the miss elsewhere is the
points; if it does not, the detector's vocabulary is the limit and the
write-ups must say so.

## What is and is not a field point

`RTU_SEN_CAPA` and `RTU_TOT_CAPA` (delivered capacity) are simulation
outputs no building records; they are excluded from every rule. The
refrigerant pressures and line temperatures are field-instrumentable (the
field RTU of X26 records the same ones).

## Config (fixed now; thresholds from the baseline only)

No schedule point exists and the unit behaves the same every day; the
supply fan runs continuously. Converter-derived `OPERATE` = 1 on every
minute (the day universe is the calendar), documented as the only
preprocessing. State alphabet: compressor stage from `RTU_STG_STA`
(stage 1 above 0.5, stage 2 above 1.5 → `cooling_active` / `stage2_entered`).
Residual channels, all gated on compressor on (`RTU_COMP_WATT` > 200 W):
- `cond_approach`: `REFG_COND_TEMP − OA_TEMP` (condenser fouling raises it);
- `discharge_superheat`: `REFG_DISC_TEMP − REFG_COND_TEMP`;
- `suction_superheat_proxy`: `REFG_SUCT_TEMP − SA_TEMP`;
- `pressure_ratio`: `REFG_DISC_PRES / REFG_SUCT_PRES` (op: ratio);
- `evap_approach`: `RA_TEMP − SA_TEMP` per unit of supply flow is not
  computable as a ratio of two columns in this framework, so instead
  `supply_dT`: `RA_TEMP − SA_TEMP` (evaporator fouling lowers the coil's
  sensible transfer);
- `comp_power_per_stage` is not attempted (stage is a state, not a scale).
Rule events: the same five with fixed bands set from the baseline
distribution (documented), sustained 60 min. Oscillation on `ZA_TEMP`.
Holdout 8 days per month, calibration 8 per month (the X25 gate).

## Predictions

- **P1.** Gates: 25 files, calendar-identical, no duplicates; healthy
  silence within three logged iterations.
- **P2 (budget).** Deployed union false alarms ≤ 10 % of holdout days.
- **P3 (condenser fouling).** ≥ 3 of 5 severities detected, the condenser
  approach or pressure ratio among the credited channels, and detection
  monotone in severity (if k % is detected, every higher severity is).
- **P4 (evaporator fouling).** ≥ 3 of 5 severities detected.
- **P5 (charge and restrictions).** ≥ 6 of 14 detected; reported by
  family.
- **P6.** No scenario detected by the conformance channels alone.

## Falsifiers

- **F-X29.a** P3 and P4 both fail → fouling is not seen even with its own
  physics recorded; the "property of the recorded points" claim is
  withdrawn from every write-up and replaced by "not seen by this
  detector on any dataset".
- **F-X29.b** P2 fails → the budget does not transfer to a refrigerant
  vocabulary; report.
- **F-X29.c** any `src/` change is required → config-only fails here.

## Artefacts

`configs/lbnl_rtu_sim/`, `scripts/08_convert_rtu_sim.py`,
`outputs/week0_audit_rtu_sim.json`, `benchmark_v6_rtu_sim.json`,
`union_fpr_rtu_sim.json`, `x29_refrigerant_observability.json`; guard
`tests/test_x29_refrigerant_observability.py`.

## Amendment 1 (2026-09-24 evening, after the hostile review of the closed X29; written before regeneration)

Three review findings on the closed artefacts (0274c72):

1. **Boundary day.** The baseline's last calendar date, 2018-10-28, holds one
   row (00:00). It is a holdout day, and the sole deployed false alarm (model
   and oscillation channels) falls on it: 1/29 was one flag on a one-minute
   "day". The residual channel already excludes it (0 of 28 evaluable).
   Change: the converter drops any calendar date with fewer than 720 rows
   (half a one-minute day) from every file; the only affected date is
   2018-10-28 (the first date, 2018-07-20, has 1,380 rows and stays). The
   week-0 gate audit reads the raw CSVs and is unchanged.
2. **Which residual carried each detection.** The scorecard records channel
   families only, so "a single physically named residual" was not an
   artefact-backed statement. New artefact `outputs/x29_residual_credits.json`
   (`scripts/x29_residual_credits.py`): per fault file, flagged days per
   residual rule under the facade's own bands. Already computed on the closed
   data: condenser fouling is carried by `cond_approach` (91–100 of 100 days
   at every severity); **evaporator fouling is carried by `supply_dT`
   (return − supply air, 100/100 at every severity), an air-side residual**,
   while the refrigerant-side residuals reach 3/9 days at 10 %, 10/9 at 20 %
   and 50/46 at 30 %. The documentation (S3) imposes both fouling types as fan
   mass-flow reduction. The refrigerant-side claim is therefore restricted to
   the condenser half and to evaporator fouling of 30 % and above; the
   evaporator detections at 10–20 % are air-side.
3. **Ledger.** `monotone()` returned true when nothing was detected; now
   false. P3's channel clause is scored on the named residual
   (`cond_approach` flagged on every condenser file), not on the family.

Predictions for the regeneration: deployed false alarms **0 of 28**; detected
20 of 24 with the same family counts; residual credits unchanged. A change
in any detection count is reported as such. Source (`src/`) unchanged from
this amendment's commit to the regeneration commit.
