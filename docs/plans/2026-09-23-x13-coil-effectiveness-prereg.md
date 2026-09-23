# X13 — a coil-effectiveness residual for the nine reheat-coil fouling misses (pre-registration)

**Written 2026-09-23, before any computation on the residual. Committed before the script runs.**

## Disclosure first

This rule is **fault-informed**. After X12 showed the state-event log is
identical under fouling, I inspected three PFPU files (fault-free, waterside
fouling severe, airside fouling severe) and looked at the reheat physics
during heating on zone S: valve position, water flow (GPM), water-side ΔT.
Waterside fouling: same valve, less flow (0.68 vs 0.82 GPM), same ΔT.
Airside fouling: more flow (1.06 GPM), less ΔT (24 vs 27 °F). The statistic
that separates both from healthy in opposite directions is **ΔT per gallon**,
(EWT − LWT) / GPM: ≈ 33 healthy, ≈ 23 airside, ≈ 40 waterside on those means.
That inspection used fault files to *choose the statistic*. Nothing below
uses a fault file to choose a threshold: bands come from the fault-free
train days only, exactly as every residual channel's do. The detection
count that results is therefore an engineering result under disclosed
fault-informed design, not a blind pre-registered detection — and it is
reported as such wherever it is quoted.

## The rule (fixed here)

One residual per terminal unit (I, W, S, E), on both fan-powered systems:

- Statistic, per minute while gated: `(RH_EWT_z − RH_LWT_z) / RH_FLOW_z`,
  in °F per GPM (water-side temperature drop per gallon: heat extracted from
  the water per unit flow). Daily score = the day's median over gated
  minutes; a day is evaluable only with ≥ 120 gated minutes (the residual
  channel's sustained-window rule).
- Gates: `RH_VLV_POS_z > 0.10` and `RH_FLOW_z > 0.10`, occupied only —
  identical to the existing `rh_waterside_dT_z` gates.
- Bands: train-day min/max via the residual channel's own `calibrate_band`;
  day flags via its `flag_days`; both unchanged. (A generic `op: ratio`
  option was added to the `paired_residual` kind alongside this test for a
  future config-only two-signal ratio; this test computes the three-signal
  statistic directly and does not use it.)
- Band floor: minimum band width **2.0 °F/GPM**, minimum exceedance margin
  **1.0 °F/GPM** (three to four times the ΔT precision floor divided by a
  typical 0.8 GPM flow).
- Gate: the residual channel's exact-binomial test, p < 10⁻³, against the
  channel's own holdout false-alarm rate.

## Predictions

- **P1.** ≥ 6 of the 9 reheat-coil fouling scenarios (6 PFPU + 3 scored
  SFPU; the airside-severe and waterside-severe SFPU files are already
  detected by other channels and are counted here too) are significant on
  the new channel.
- **P2.** Per-system holdout false alarms of the new channel ≤ 3 of 96.
- **P3.** The joint false-alarm rate of the deployed union plus the new
  channel stays ≤ 8 of 96 on each system.

## Falsifiers (binding)

- **F-X13.a** Joint false-alarm rate > 10 % on either system → not adoptable.
- **F-X13.b** Fewer than 4 of 9 fouling scenarios significant → the
  statistic does not carry the fault at day level; report and stop.

## Artefact

`scripts/x13_coil_effectiveness.py` → `outputs/x13_coil_effectiveness.json`,
guarded by a test pinning fired/unfired falsifiers. Adoption into the
deployed configs (`residual_channels`) is a separate, later decision and
changes the published scorecards; it is not made by this test.

## Erratum to this pre-registration (2026-09-23, after review)

"Nine" reheat-coil fouling scenarios is a miscount: the scored universe holds **twelve**, ten of them deployed misses. The falsifier threshold (fewer than 4 significant) fires under either count; the artefact keeps the pre-registered string. The first run's "unique days vs deployed" used non-existent scorecard keys; corrected before anything was quoted.
