# X15 — enriched alphabet, frequency channel only: does the one gain survive inside the budget? (pre-registration)

**Written 2026-09-23 (night), after X14 and before any computation. Committed before the script runs.**

## Provenance, stated first

This test is **motivated by a post-hoc read** of X14's artefact: the
per-channel false-alarm attribution showed the time model was the cost (15
and 19 of 96 fan-powered holdout days) while the frequency channel alone, on
the enriched alphabet, sat at 4 and 3 of 96 and still flagged the one newly
significant scenario (`SFPU_ReheatCoilFouling_Airside_Moderate`) on 364 of
365 days. Re-testing that on the same holdout would only restate the read.
So this test changes the one thing that can still falsify it: **the
holdout**. It is not an alphabet variant (the X14 amendment forbidding
those tonight is respected); it is a channel selection on X14's alphabet,
evaluated under the mirrored split.

## What runs

X14's enriched alphabet exactly (Amendments 1–3: positions and flows,
setpoints excluded, healthy-derived 10th/90th percentile bands, 15-minute
dwell, wall intact). Only the **frequency channel** (unit and device
strata, `build_frequency_detector` / `classify_frequency_days`, the deployed
code) is built and gated — no alignments, no time model. Two holdout
splits: the deployed **last-8-days** split and the mirrored **first-8-days**
split; bands and the healthy false-alarm rate are recomputed under each.
Significance: the frequency channel's own gate (`frequency_significant`,
rule-of-three floor). All three systems, all 73 scored scenarios; the
deployed detector's per-scenario result from the committed scorecards.

## Predictions

- **P1.** Under **both** splits the enriched frequency channel's holdout
  false-alarm days are ≤ 10 of 96 on each fan-powered unit and ≤ 9 of 96 on
  SDAHU.
- **P2.** `SFPU_ReheatCoilFouling_Airside_Moderate` is significant under
  **both** splits.
- **P3.** No other scenario the deployed detector misses becomes
  significant under both splits (the read found only one; a second would
  be a surprise to be explained, not a bonus).
- **P4.** On the scenarios the deployed detector already detects, the
  enriched frequency channel is significant on at least as many as the
  deployed frequency channel is (`frequency_days` significant in the
  scorecards), under the last-8 split.

## Falsifiers (binding)

- **F-X15.a** P1 false under either split → the enriched frequency channel
  is not deployable at the budget; the post-hoc read was split-specific.
- **F-X15.b** P2 false under the mirrored split → the detection is
  split-dependent; not a signature.

## What is and is not claimed

If P1 and P2 hold: *a healthy-derived enrichment of the operating-state
alphabet, read through the deployed frequency channel, detects one
reheat-coil fouling scenario the deployed detector misses, inside the
false-alarm budget, under two holdouts.* That is a candidate deployable
addition, not an adopted one: adoption changes the published scorecards
and is a separate decision. It says nothing about alignment-based
conformance.

## Artefact

`scripts/x15_enriched_frequency.py` → `outputs/x15_enriched_frequency.json`,
guarded by a test pinning fired/unfired falsifiers.
