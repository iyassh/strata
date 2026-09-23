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

## Amendment 1 (2026-09-23, after a first run was stopped, before any result was read)

The first run (commit c9e19f5) was stopped after 3.5 minutes without
producing a system result. Two things were wrong, recorded here before the
re-run:

1. **Compliance bug.** The signal filter `startswith("ZONE_FLOW_")` also
   admitted the setpoint columns `ZONE_FLOW_SP_*`, which the alphabet above
   excludes ("actuator-position and flow signals"; setpoints are neither).
   Fixed: any canonical name containing `_SP` is excluded.
2. **Chatter.** A signal hovering at its 10th-percentile edge crosses it
   many times a day (zone-S flow: 71 low-band entries per day); the
   enriched PFPU log had 804 state events per day (max 4,792), against 162
   before. Alignment-based conformance on traces of that length is
   infeasible, and a net discovered from them is a flower by construction.
   **Design change:** every added band event carries a **15-minute minimum
   dwell** — a band state shorter than 15 minutes is absorbed into the
   preceding state before edges are emitted (new `min_dwell_min` option on
   the `mode` and `window` kinds; default off, so every existing event and
   every committed artefact is unchanged). Fifteen minutes is the
   sustained-window convention already used by the signature rules'
   shortest windows; it was chosen without reference to any fault file.

Predictions and falsifiers are unchanged. The stopped run produced no
numbers, so none were seen.

## Amendment 2 (2026-09-23, after the second run was stopped; SDAHU numbers had been seen, no fan-powered result had)

With the 15-minute dwell the parallel unit's enriched log is 213 state
events per day (max 1,174). Fitting took 1,061 s and the first scenario's
alignment-based evaluation had not finished after 47 minutes; thirty
scenarios on two systems would take days. **Design change:** on the two
fan-powered units the alignment-based channels — model, device and the
absence channel that reads the device model — are not evaluated on the
enriched alphabet; the artefact marks them `null` there. The enriched
alphabet is tested on those systems through the frequency channel and the
time perspective. SDAHU (no device stratum, 12.7 events per day) keeps the
model channel, and its enriched model-channel results, already printed
before this amendment, stand.

This narrows P1 and P3 on the fan-powered units and is recorded as a
finding in its own right: at this vocabulary, alignment-based conformance is
computationally impractical on these logs. Predictions and falsifiers are
otherwise unchanged. The SDAHU results seen before this amendment: the
enriched model channel is significant on the four coil-bias runs and
`oa_bias_4` (model days 33–186 against ≤ 5 before), all already detected;
holdout FP of state ∪ time 7 of 96.
