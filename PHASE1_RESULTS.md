# Phase 1 Results — Alphabet Split (2026-08-10)

**Question:** what does the discovered process model honestly detect, once it can no longer echo the signature rules?

**Change:** state/signature alphabet split enforced end to end (discovery, calibration, classification all state-events-only). Codebase: `Ureap/strata` (fork of processheal v1). 33/33 tests pass, including the new invariant test: injecting signature events into a day cannot change its model fitness.

## Numbers (SDAHU, per-day, out-of-sample; 4,540 fault days, 438 healthy negatives)

| arm | recall | FPR | precision | F1 |
|---|---|---|---|---|
| rules-only | 69.0% | 0.0% | 100.0% | 0.817 |
| model-only (state alphabet) | **1.8%** | 1.1% | 94.2% | 0.035 |
| combined | 69.4% | 1.1% | 99.8% | 0.819 |

Model-channel unique contribution: **18 of 4,540 fault days** (0.4%), all in the sensor-bias family — but the healthy-like negative run gets flagged at the same ~1% rate, so those unique flags are statistically indistinguishable from the model's false-alarm rate. **Honest verdict: on SDAHU, the unit-level day-cycle model contributes ≈ nothing beyond the rules.**

## The circularity, now measured

v1 "structure-only" recall (signature events reaching conformance): 5.2%.
v2 model-only recall (split enforced): 1.8%.
**→ ~3.4pp of the model's apparent v1 contribution was the model re-detecting our own rules.** This is the direct empirical confirmation of the circularity gap (v2 revision, Gap #1).

## Why this is the predicted result, not a failure

- Rules already flag 365/365 days on every stuck/leak scenario → zero recall headroom on SDAHU (predicted in v2 revision).
- The SDAHU unit net over neutral events is a near-deterministic daily schedule → little sequence signal to exploit (predicted).
- The bias family is invisible to sequence events entirely → Phase 2's analytic-redundancy events (mixed-air residual) are the designed answer.
- The device stratum's real test is FPU (command-less zone dampers) → Phase 3.

## Decision (per the plan's Phase 1 gate)

Proceed as planned. The burden of proof for the PM thesis now formally rests on:
1. Phase 2 — bias-family recall must move off zero via physics-residual events.
2. Phase 3 — device stratum on FPU must beat a matched rules baseline (pre-registered falsifiers stand).

The paper narrative gains a strong honest opening: "we measured our own method's circularity (3.4pp) and removed it."
