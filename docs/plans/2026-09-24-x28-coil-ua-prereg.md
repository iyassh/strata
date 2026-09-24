# X28 — a coil heat-transfer (UA) channel for the fouling misses (pre-registration)

**Written 2026-09-24 (plan item B3) before any code or config change, and
before any healthy UA value is computed.**

## Why

Coil fouling is the dominant miss family (DDAHU 7 of 12, FCU 5 of 11). The
field's standard for it is not a temperature band but a heat-transfer
estimate: UA = Q / LMTD, with Q from the water side (flow × ΔT) and the
log-mean temperature difference from the four terminal temperatures. Both
systems record entering and leaving water temperature, water flow, the air
entering the coil (mixed air) and the air leaving it (deck or discharge
temperature). X13 tried the cheap proxy (ΔT per gallon) and its falsifier
fired; the domain review's item 4 asks for the real quantity.

## Definition (fixed now)

New `paired_residual` option `op: ua` with keys `ewt`, `lwt`, `flow`,
`ta_in`, `ta_out` and `coil: cooling|heating`. Per sample, gated as the
water-side ΔT rules are (valve > 0.10, flow > 0.05, scheduled):
Q = flow × |EWT − LWT| (gpm·°F; the constant 500 is irrelevant to a band);
counterflow LMTD from ΔT1 = |ta_in − LWT|, ΔT2 = |ta_out − EWT| (cooling)
or ΔT1 = |EWT − ta_out|, ΔT2 = |LWT − ta_in| (heating), requiring both
> 0.5 °F and defined as (ΔT1 − ΔT2)/ln(ΔT1/ΔT2) (their mean when equal);
UA = Q / LMTD; the day's score is the median UA over gated minutes. The
channel's band is learned on training days; its floors (width and
exceedance) are set once, on the healthy year only, at 5 % of the healthy
training-day median UA, and logged.

Channels: DDAHU `chwc_ua` (CHWC_EWT/LWT/FLOW, MA_TEMP → SA_TEMP i.e.
cold-deck) and `hwc_ua` (HWC_*, MA_TEMP → HSA_TEMP); FCU `chwc_ua` and
`hwc_ua` (FCU water points, FCU_MAT → FCU_DAT). Existing channels stay.

## Predictions

- **P0.** Code change, no config touched: five scorecards byte-identical.
- **P1.** Healthy silence unchanged; each UA channel ≤ 1 holdout false
  alarm; deployed budgets ≤ 10 of 96.
- **P2 (DDAHU).** ≥ 3 of the 7 fouling misses become significant.
- **P3 (FCU).** ≥ 2 of the 5 waterside-fouling misses become significant —
  with the stated expectation, from X19's diagnostic, that the *cooling*
  waterside files may not (their recorded water-side signals sit within
  about 3 % of healthy), so the two are most likely heating files.
- **P4.** No previously detected scenario loses detection on either system.

## Falsifiers

- **F-X28.a** P1 fails on a system → the UA channels are removed there.
- **F-X28.b** P2 and P3 both fail → UA from these points does not see the
  simulated fouling; the miss is a property of the recorded points, and the
  papers say so (the refrigerant-side observability test remains).
- **F-X28.c** P4 fails → investigate before writing.

## Artefacts

Regenerated DDAHU and FCU scorecards; `outputs/x28_coil_ua.json`; guard
`tests/test_x28_coil_ua.py`.
