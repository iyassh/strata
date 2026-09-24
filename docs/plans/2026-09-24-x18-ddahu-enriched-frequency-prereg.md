# X18 — does the X15 gain replicate on the fourth system? Enriched alphabet, frequency channel only, DDAHU, two holdouts (pre-registration)

**Written 2026-09-24 after X17's scorecard was read and before any enriched
run on DDAHU. Committed before the script runs.**

## Why

X15 found, on the series fan-powered unit, that a healthy-derived
enrichment of the operating-state alphabet read through the deployed
frequency channel detects one reheat-coil fouling scenario the deployed
detector misses, inside the false-alarm budget under two holdouts. One
scenario on one system is a candidate, not a result. The dual-duct AHU
(X17) has ten misses — seven coil-fouling files and three static-pressure
biases — and was onboarded blind, so it is the first chance to test the
X15 mechanism where nothing about it was tuned.

## What runs (X15's protocol, unchanged)

The X14 enrichment exactly: for every mapped actuator-position signal
(`_POS` anywhere in the canonical name; the X17 config also maps command-only
zone dampers as `_CMD`, which are **not** positions and are excluded) and
every flow signal (`ZONE_FLOW_*`, excluding setpoints), two band states
(above the occupied train 90th percentile; at or below the 10th) with the
15-minute dwell; wall intact. Only the frequency channel (unit and device
strata, deployed code and gate), bands and the healthy false-alarm rate
recomputed under the deployed last-8-days split and the mirrored
first-8-days split. Deployed per-scenario results from
`outputs/benchmark_v6_ddahu.json`.

## Predictions

- **P1.** Under both splits the enriched frequency channel's holdout
  false-alarm days are ≤ 10 of 96.
- **P2 (load-bearing).** At least one of X17's ten misses is significant
  under **both** splits, and it is a coil-fouling scenario (the X15
  mechanism was a fouling signature in a zone damper's band; the static
  biases are a different physics).
- **P3.** No static-pressure-bias miss becomes significant under both
  splits.
- **P4.** On the 45 detected scenarios the enriched frequency channel is
  significant on at least as many as the deployed frequency channel (8).

## Falsifiers (binding)

- **F-X18.a** P1 false under either split → not deployable at the budget on
  this system.
- **F-X18.b** P2 false → the X15 gain does not replicate on a fourth system;
  it stays a one-scenario, one-system observation.

## Artefact

`scripts/x18_ddahu_enriched_frequency.py` →
`outputs/x18_ddahu_enriched_frequency.json`, guarded by a test pinning
fired/unfired falsifiers.
