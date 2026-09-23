# X12 — the time perspective of the discovered model (pre-registration)

**Written 2026-09-23, before any computation. Committed before the script is run.**

## Why this test exists

The conformance channels replay each day's state trace against a Petri net
discovered from the fault-free year and score control-flow fitness. The
ablation over 73 scenarios found no scenario detected only by them, and the
reversal probe found two of the three nets order-insensitive. Tonight's
diagnosis of the misses (reheat-coil fouling, all nine scenarios) showed the
state-event log under fouling is *identical* to healthy — same per-day
activity counts, same state durations to the minute — so no method that
reads the event log can see those faults, process mining or otherwise. But
under valve leak/stuck faults the log *does* change, and it changes in the
**time perspective**: the zone-S heating-on median falls from 100 to 11
minutes under `PFPU_ReheatVLVLeak_50%MaxFlow`, with the activity set and its
order unchanged. Control-flow conformance is blind to that by construction.

Multi-perspective conformance is standard in process mining (data-aware
alignments; time-infused models; time Petri nets). The pipeline has never
tested the time perspective. This test asks whether it adds detections that
no deployed channel already makes.

## The channel (fixed here)

*Time-infused state model.* For every on/off state pair in the **state**
alphabet (kinds `occupancy`, `mode`, `window`, at unit and device strata; the
signature alphabet is never read — the wall holds), the model records, per
healthy **train** day (the same 248/365-day split as every other channel):

- `on_med`: the day's median on-duration in minutes (off − on, paired in
  order within the day);
- `off_med`: the day's median off-gap in minutes (next on − off);
- `first_on`: minute-of-day of the first on-event.

Bands are `[min, max]` over train days, widened by a floor of **5 minutes**
on each side (sensor/timestamp granularity; mirrors the residual channel's
0.5 °F floor). A pair is monitored only if it occurs on ≥ 5 % of train days
(the frequency channel's rule). A day is **flagged** if any monitored
statistic of any monitored pair lies outside its band. The healthy holdout
(the last 8 days of each month) gives the channel's false-alarm rate; a
scenario is **significant** when its flagged-day count beats that rate at
the same exact-binomial gate every other channel uses, p < 10⁻³.

No fault file is consulted while building bands. The band rule, the floor,
the 5 % rule, the statistics and the gate are fixed by this document.

## Unit of comparison

The deployed channels' per-day flags are read from the committed scorecards
(`outputs/benchmark_v6_*.json`, `flag_days`), not re-run, so the comparison is
against exactly the numbers the papers quote. "Deployed union" = rules ∪
residual ∪ model ∪ device ∪ absence ∪ frequency ∪ oscillation (rate is
advisory, excluded). Scenario universe: the 73 scored scenarios (E4 excluded).

## Predictions

- **P1.** The time channel is significant on **≥ 5** of the 73 scenarios.
- **P2 (negative).** It is significant on **none** of the nine reheat-coil
  fouling scenarios (the log carries no signal).
- **P3 (the load-bearing one).** It is significant on **≥ 1 scenario that no
  deployed channel detects** (`meaningful_channels` empty in the scorecard),
  i.e. it reduces the 13 misses.
- **P4.** On scenarios it shares with the frequency channel, it flags days the
  frequency channel does not (unique days > 0 on ≥ 3 scenarios) — otherwise it
  is a restatement of counting.

## Falsifiers (binding)

- **F-X12.a** Healthy-holdout false-alarm rate > 10 % on any system → the
  channel is unusable as built; report and stop.
- **F-X12.b** P3 false **and** P4 false → the time perspective is redundant
  with the deployed statistical channels; the honest conclusion is that the
  discovered model's time annotation adds nothing, and it is reported as the
  eighth adverse result.
- **F-X12.c** P2 false (a fouling scenario is significant) → the diagnosis
  "the log is identical under fouling" is wrong somewhere; find where before
  quoting anything.

## What is and is not claimed

If P3 holds, the claim is: *the time perspective of a discovered state model
detects faults the control-flow perspective and the deployed statistical
channels miss.* It is not a claim that alignment-based conformance works. The
matched-rule discipline applies: whichever pair/statistic carries a unique
detection will be named, and a one-line hand-written duration rule on that
pair becomes a permanent ablation arm (as the heating-absence rule did).

## Artefact

`scripts/x12_time_perspective.py` → `outputs/x12_time_perspective.json`,
guarded by a test that pins the fired/unfired falsifiers.

## Errata to this pre-registration (2026-09-23, after review)

- The zone-S heating-on median quoted above as 100 minutes was from an ad-hoc pairing; the channel's own statistic gives **124** minutes (`outputs/x12_log_diagnosis.json`). The fall to 11 minutes under the valve leak stands.
- "Nine" reheat-coil fouling scenarios is a miscount: the scored universe holds **twelve** (six per fan-powered system), ten of them deployed misses. P2 is evaluated over all twelve; it held.
- The first run of the scorer compared against scorecard keys that do not exist (`absence`, `frequency`, `oscillation`), inflating "unique days vs deployed" and leaving P4 uncomputed. Corrected to the six exported keys plus `sig_union`; P1–P3 unchanged, P4 recomputed and still held; the unique-day figures shrank (120 → 2 on `SFPU_RMTEMPUnstable`).
