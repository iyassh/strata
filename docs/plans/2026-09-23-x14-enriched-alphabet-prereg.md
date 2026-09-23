# X14 — an enriched state alphabet: was the discovered model starved of vocabulary? (pre-registration)

**Written 2026-09-23 (night), before any computation. Committed before the script runs.**

## The hypothesis

The discovered models have seen 6 (SDAHU), 10 (PFPU/SFPU unit stratum) or 26
(with zone events) activities: on/off modes of a few controls. X12 showed
the log carries valve faults in timing and counts; nothing so far has
asked whether the log would carry *more* faults if the abstraction emitted
richer **operating states** — actuator positions and flows in bands — while
keeping the alphabet wall exactly as it is (no rule, setpoint or fault
reference; states describe what the equipment is doing). If the model
channel, device channel, absence channel, frequency channel or time
perspective, rebuilt on that alphabet, detect a scenario the deployed
detector misses, the model was starved of vocabulary rather than wrong in
kind. If not, the vocabulary was not the limit.

## The alphabet (fixed here, thresholds healthy-derived)

For every mapped actuator-position signal (`*_POS`) and flow signal
(`RH_FLOW_*`, `ZONE_FLOW_*`) on each system, two additional state events:

- `<signal>_high`: `mode` kind, on when the signal exceeds the **90th
  percentile of its occupied fault-free train-day values**;
- `<signal>_low`: `window` kind, entered when the signal lies at or below
  the **10th percentile** of the same values.

Thresholds are computed on the fault-free year's train days only (last 8
days of each month excluded), written to the artefact, and never read from
a fault file. Zone signals carry `stratum: device` and their terminal-unit
tag, as the existing zone events do. Signals constant on the healthy year
(10th = 90th percentile) are skipped. Everything else in the config is
unchanged; the signature alphabet and the rules/residual channels are
untouched, so their outputs are identical by construction.

## What runs

Per system: `strata.core.pipeline.fit` on the fault-free year with the
enriched config; `evaluate` on every scored scenario; the X12 time model on
the enriched healthy log. Healthy-holdout false alarms of the enriched
state channels (model ∪ device ∪ absence ∪ frequency ∪ time) measured on the
same holdout. Deployed per-channel results read from the committed
scorecards for comparison.

## Predictions

- **P1 (load-bearing).** At least one of the 13 scenarios the deployed
  detector misses is significant on at least one enriched state channel.
- **P2.** The enriched state channels' joint holdout false-alarm rate is
  ≤ 10 of 96 on each fan-powered system and ≤ 9 of 87 on SDAHU.
- **P3.** The enriched model channel is significant on at least as many
  scenarios as the deployed model channel (more vocabulary, not less).

## Falsifiers (binding)

- **F-X14.a** P2 false → the enriched alphabet is unusable at the budget.
- **F-X14.b** P1 false → the vocabulary was not the limit; the
  alphabet-starvation hypothesis is refuted and recorded as an adverse
  result. No further alphabet variants are tried tonight.

## Artefact

`scripts/x14_enriched_alphabet.py` → `outputs/x14_enriched_alphabet.json`,
guarded by a test pinning fired/unfired falsifiers.
