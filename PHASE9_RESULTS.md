# Phase 9 Results — Can process mining be made to detect? (X12–X15) and does the detector survive jitter and a different holdout? (X9/X10)

*2026-09-23, overnight. Both experiments pre-registered and committed before
they ran (`docs/plans/2026-09-23-x12-*.md`, `…-x13-*.md`). Artefacts
`outputs/x12_time_perspective.json`, `outputs/x13_coil_effectiveness.json`,
pinned by `tests/test_x12_time_perspective.py`, `tests/test_x13_coil_effectiveness.py`.*

## The question

The ablation (Phase 8, paper §5) found no scenario detected only by the two
conformance channels; the reversal probe found two of three discovered nets
order-insensitive. The question asked tonight: **is that a property of
alignment-based control-flow conformance, or of the event log itself?** If
the log carries the fault and only the control-flow perspective misses it,
another perspective of the same discovered model could detect. If the log
does not carry the fault, no log-based method can.

## Diagnosis first (what the log contains)

Per-day state-activity counts and state durations were compared between
the fault-free PFPU year and two missed scenarios and one detected one:

| file | events/day | zone-S heating-on median (min) | zone-S fan cycles/day |
|---|---|---|---|
| PFPU_FaultFree | 162.4 | 124 | 16.3 |
| PFPU_ReheatCoilFouling_Waterside_Severe (**missed**) | 162.8 | 124 | 16.3 |
| PFPU_ReheatVLVLeak_50%MaxFlow (detected) | 182.0 | **11** | **26.6** |

Under waterside fouling the state-event log is identical to healthy to the
minute: the fault lives in heat-transfer magnitudes the abstraction
discards. Under valve leak the log changes — in **timing** and **counts**,
not in the set or order of activities. Control-flow conformance is blind to
timing by construction; the frequency channel already reads counts.

Made an artefact over all 73 scenarios (`scripts/x12_log_diagnosis.py` →
`outputs/x12_log_diagnosis.json`, 5 % tolerance on every activity's daily
count and every pair's on-duration median): **8 of the 12 scenarios the
deployed detector misses have a state log indistinguishable from healthy**
(all reheat-coil fouling; the twelfth miss is the single-duct branch
adjudication, not in the naive scorecard). The other four misses — PFPU
airside fouling moderate/severe and both +2 °C room-sensor-bias runs — do
change a daily count by 7–39 % (zone-S fan starts, zone-S heating
episodes); the frequency channel's train min/max bands did not turn that
into significant days. One detected scenario (SFPU waterside fouling,
severe) also has an indistinguishable log: it is caught by non-log
channels, which is consistent.

## X12 — the time perspective of the discovered state model

Time-infused state model: per state pair (unit and device strata, state
alphabet only), per-day median on-duration, off-gap and first-on minute;
train min/max bands ± 5 min; holdout false-alarm rate; the same binomial
gate (p < 10⁻³) as every channel. Compared against the committed scorecards'
per-channel flag days (never re-run).

| | SDAHU | PFPU | SFPU |
|---|---|---|---|
| statistics monitored | 8 | 37 | 36 |
| own holdout FP | 0/87 | 5/96 | 5/96 |
| joint FP, deployed union → + time channel | 1 → 1 of 96 | 5 → **10** of 96 | 4 → **9** of 96 |

Over the 73 scored scenarios: **significant on 11** (P1 held; 10 under the
rule-of-three floor the rules, frequency and oscillation channels use — the
suite carries two floors, and `coi_bias_-2` is significant only under the
permissive `max(fp,1)/n` one; both are in the artefact); **none of the
twelve fouling scenarios** (P2 held — the pre-registration miscounted them as
nine; for eight of the ten fouling misses the log carries nothing at 5 %); **no scenario
the deployed channels miss** (P3, the load-bearing prediction, **false**);
unique days beyond the frequency channel on 11 of 11 (P4 held — but P4 is a
low bar: unique against *one* channel, not against the deployed union, so it
cannot rescue P3; and the first run of the script did not compute it at all,
reading a scorecard key that does not exist, which review caught before
anything was adopted — disclosed here). Time-to-detect: **never earlier**
than the deployed detector (0 of 11; typically day 14 vs day 1) — a
comparison asymmetric in kind, the channel's first raw flag against the
scorecard's gated first flag, which favours the time channel and it still
loses.

What it adds is a **small day-level coverage supplement** on scenarios
already detected, measured against the union of the six exported channel
day lists (absence is not exported by the scorecards): 81 unique days on
`coi_bias_-4` (15 against the gated union), 16 on
`SFPU_SensorBias_RMTEMP_-4C`, 9 on `PFPU_ReheatVLVStuck_0%`, 2 on
`SFPU_RMTEMPUnstable` (whose deployed union is 263 days), 0 on the six
series-unit valve scenarios the rules already flag on every day. (A first
run reported 120 / 82 / 28 / 13 from the wrong scorecard keys; corrected.) The statistics that carry it are physically
legible: zone-heating on/off medians under an unstable room sensor, zone-fan
on-durations under a stuck reheat valve, cooling first-on minute under a
coil-bias fault on the single-duct unit.

**Reading.** The time perspective is not blind the way the control-flow
perspective is: it sees eleven scenarios with p-values down to 10⁻⁹⁴. But
everything it sees, the rules and residual channels see first, and adding
it costs five false-alarm days on each fan-powered system — on PFPU it
pushes the joint rate from 5.2 % to 10.4 %, over the 10 % budget. No
falsifier fired, and the honest verdict is still adverse for the claim "a
discovered model detects faults the hand-written channels miss": **as a
detector it is redundant; as a coverage supplement it is real and costs
false alarms.** No falsifier fired, so it is not counted among the adverse results; X13
below is the eighth.

## X13 — a coil-effectiveness residual for the fouling misses (fault-informed)

Design disclosed as fault-informed: the statistic (water-side ΔT per GPM)
was chosen after inspecting three fouling files' *means* (≈33 healthy, ≈23
airside, ≈40 waterside on zone S). Thresholds from fault-free train days
only; the residual channel's own band, floor and gate.

**F-X13.b fired.** One of the twelve fouling scenarios significant (the
pre-registration miscounted them as nine; the threshold fires either way)
(`SFPU_ReheatCoilFouling_Waterside_Severe`, already detected by other
channels); nothing newly detected. The day-median distribution overlaps
almost entirely with healthy — the bands are 0.6–94 °F/GPM on PFPU zone S
because the ratio explodes at low flow — so a difference of means is not a
day-level separation. The false-alarm budget held (own FP 1 of 83 and 0 of 80 holdout
rule-days, summed over zones as the deployed residual channel counts them;
joint unchanged), which is the only thing the design got right. SFPU zone I
has no evaluable healthy day at the 120-minute window, so its band is
undefined and that zone is disabled — stated in the artefact; the SFPU
result is over three zones.

**Reading.** The fouling misses are not a process-mining failure and not
fixed by one more residual. They need either a physics model of the coil
(UA estimation from flow, ΔT and air-side conditions) or a different
sensor. Recorded as a fired falsifier; the statistic is not adopted.

## X14 — an enriched state alphabet: was the model starved of vocabulary?

Pre-registered (c9e19f5), amended three times, each amendment committed
before the result it governs was read: setpoints excluded and a 15-minute
dwell after the first run proved infeasible (804 events/day); the
alignment-based channels dropped on the fan-powered units after the second
run's first PFPU scenario had not finished in 47 minutes; and the zone
actuators (`RH_VLV_POS_z`, `ZONE_DMPR_POS_z`) restored after review found
`endswith("_POS")` had dropped all eight. For every actuator position and
flow signal, two healthy-derived band states (above the occupied train 90th
percentile; at or below the 10th), wall intact: 3 / 20 / 18 signals, 6 /
40 / 36 events. SDAHU keeps the model channel; the fan-powered units are
tested through the frequency channel (unit and device strata) and the time
perspective.

| | SDAHU | PFPU | SFPU |
|---|---|---|---|
| enriched state ∪ time holdout FP (of 96) | **7** (model 1, frequency 2, time 4) | **18** (frequency 4, time 15) | **21** (frequency 3, time 19) |
| newly significant among the 12 misses | 0 | 0 | 1 (`ReheatCoilFouling_Airside_Moderate`: frequency 364 days, time 365) |
| enriched model channel significant | 14 of 14 (deployed: 0 of 14) | not evaluated | not evaluated |

**P1 held by the letter, P3 held, P2 failed; F-X14.a fired.** The enriched
channels false-alarm on 18 and 21 of 96 holdout days on the fan-powered
units — one clean day in five — which is the budget's definition of
unusable.

**The one new detection, with its mechanism measured.** It is carried by
the device-stratum frequency channel (SFPU holdout FP 3 of 96) and the time
model (19 of 96) on one added state, the zone-S damper's low band (≤ 0.32,
the healthy occupied 10th percentile). A committed fault-versus-fault
control over all 31 series-unit files (`scripts/x14_control.py` →
`outputs/x14_control.json`) shows a monotone dose ladder: the share of
occupied samples at or below the edge is 64.3 % healthy, 64.2 % minor,
11.9 % moderate, 3.5 % severe — the fault moves the zone-S damper up, so it
crosses the band in sustained stretches (9.0 and 8.7 entries per day for
moderate and severe against 0.7) instead of resting in it (off-gap median
30 minutes against 570). Severe fires on the same statistic at the same
strength and is simply not "new" because a deployed channel already
detects it; minor sits at the healthy rate. The claim is bounded to
**airside** fouling: the three waterside files sit exactly at the healthy
values (share 64.3 %, 0.73 entries per day, off-gap 570 minutes) at every
severity. (A first write-up called this a
threshold coincidence on a misread of the severe file's 10th percentile as
its minimum; the control corrected it.) Multiplicity: with 12 missed
scenarios and two evaluated channels the Bonferroni gate is 2.1 × 10⁻³
(0.05/24) and, at the suite's own 10⁻³, 4.2 × 10⁻⁵; moderate's p on the time
channel is 10⁻²⁵⁶·⁸ and below double precision on the frequency channel.
The run-3 detection it replaced (PFPU `SensorBias_RMTEMP_+2C`, p 1.8 × 10⁻⁴
under the smaller alphabet) vanished under the fuller alphabet's higher
time-channel floor (15 of 96). So the enriched alphabet does carry one
physically legible, dose-monotone fault signature the deployed alphabet
does not — and the channels that carry it false-alarm on one clean day in
five. **Post-hoc read, not a pre-registered result:** the per-channel
false-alarm attribution in the same artefact shows the time model is the
cost (15 and 19 of 96) while the frequency channel alone, on the enriched
alphabet, sits at 4 and 3 of 96 — inside the budget — and carries the new
detection at 364 of 365 days. Whether "enriched alphabet + frequency
channel only" holds as a deployable addition is the obvious next
pre-registered test (X15); it is not claimed here.

**Reading.** Vocabulary was part of the model channel's limit — on the
single-duct unit the enriched model channel is significant on 14 of 14
scenarios against 0 of 14 deployed, with model days 30–227 against ≤ 9 —
and richer vocabulary buys detections at false alarms the budget forbids.
Alignment-based conformance on the enriched fan-powered logs was also
computationally impractical (single-laptop console timings, printed and not
committed: 17 minutes to fit before Amendment 3; one scenario not scored in
47). Recorded as the ninth adverse result on the detection claim; the
vocabulary finding and the one mechanism-stated detection beside it.

## X15 — enriched alphabet, frequency channel only, under two holdouts: the one gain survives

Pre-registered (0d0c692) with its provenance stated first: motivated by a
post-hoc read of X14's per-channel attribution, so the test changes the
one thing that can still falsify it — the holdout. X14's alphabet exactly;
only the frequency channel (unit and device strata, the deployed code and
its own gate); bands and the healthy false-alarm rate recomputed under the
deployed last-8-days split and the mirrored first-8-days split. No
alignments.

| enriched frequency channel | SDAHU | PFPU | SFPU |
|---|---|---|---|
| holdout FP, last-8 / first-8 | 2 / 0 of 87 | 4 / 8 of 96 | 3 / 5 of 96 |
| deployed frequency channel's own holdout FP (`union_fpr_*.json`) | 1 of 96 | 1 of 96 | 1 of 96 |
| significant scenarios, last-8 / first-8 | 10 / 10 of 14 | 11 / 8 of 30 | 21 / 18 of 29 |
| newly significant under **both** splits | — | — | `ReheatCoilFouling_Airside_Moderate` (365 of 365 days under each) |

**All four predictions held; no falsifier fired.** Inside the budget under
both splits (P1); the airside-moderate fouling detection survives the
mirrored split (P2); nothing else new (P3); on the scenarios the deployed
detector already catches, the enriched frequency channel is significant on
41 of 61 against the deployed frequency channel's 12 of 61 (P4). (SDAHU's denominator
is 87: the days on which the state log has any event, as the frequency
channel counts them — an event-log day universe, against the pipeline's
rule that the day universe comes from the raw calendar; disclosed in the
pre-registration's amendment, no consequence at 2 and 0.)

**Reading.** The night's one constructive result. A healthy-derived
enrichment of the operating-state alphabet, read through the deployed
frequency channel, detects one reheat-coil fouling scenario the deployed
detector misses — the airside-moderate file, with its dose-monotone
zone-damper signature (X14 control) — inside the false-alarm budget under
two holdouts, and roughly triples the frequency channel's coverage of
already-detected scenarios. It is a **candidate deployable addition**, not an
adopted one: adoption changes every published scorecard and the false-alarm
budget accounting, and is a separate decision, to be pre-registered (X16). Like
for like, the enriched channel costs three to eight times the false alarms
of the channel it enriches — the price of the coverage. It
says nothing about alignment-based conformance, which remains at zero
unique detections and, on this alphabet, computationally impractical on
the fan-powered units.

## X9 / X10 — jitter and holdout-split robustness of the deployed detector

Pre-registered (289e53f), three amendments each recorded before the result
it governs: the 2×/4× stress arms made descriptive and the noise named as
i.i.d. per-sample **jitter**, not bias or drift (A1); the stress arms
dropped on the fan-powered units for compute (A2); the alignment-based
channels dropped on the fan-powered units for compute, with the clean
reference restated as the deployed detector minus those channels — which
changes no detection count and lowers the series unit's holdout FP from 4
to 1 (A3). SDAHU ran with every channel at every dose. The detector is
re-fitted on the jittered healthy year at each dose (1× = 0.5 °F on
temperatures, 2 % on flows, 0.01 on positions; static pressure is mapped
on no system and was never perturbed; seeds shared across doses).

| detected / holdout FP | clean reference | 1× jitter | 2× | 4× | first-8-days holdout |
|---|---|---|---|---|---|
| SDAHU (all channels) | 14 of 14 / 1 of 96 | 14 / 1 | 14 / 1 | 14 / 1 | 13 / 0 |
| PFPU (no alignment channels) | 23 of 30 / 5 of 96 | 23 / 4 | — | — | 23 / 2 |
| SFPU (no alignment channels) | 24 of 29 / 1 of 96 | 24 / 2 | — | — | 25 / 3 |

**Every binding prediction held; no falsifier fired.** Detection counts are
unchanged at 1× jitter on all three systems and within one under the
mirrored holdout; false-alarm rates stay at 0–4 of 96.

**What the counts hide.** The count is stable, the membership is not: at 1×
jitter the parallel unit loses two marginal room-sensor-bias scenarios
(−2 °C, −4 °C) and gains airside-severe fouling and +2 °C; under the
mirrored split it loses −2 °C and gains airside-severe; the series unit
gains waterside-moderate fouling; the single-duct unit loses `oa_bias_4`,
the very scenario the branch adjudication (X11) had already removed. The
deployed detector's *count* is robust to jitter and to the split; which
marginal scenarios sit on either side of the gate is not, and the fouling
family in particular is at the edge on both fan-powered units.

**What this does not show.** Jitter is not bias or drift, which is the
limitation the papers state; the 2×/4× arms ran only on SDAHU (identical
at every dose); the fan-powered arms exclude the conformance channels,
whose contribution on clean data is nil. A bias/drift arm is future work.

The run also exposed a performance bug in the deployed `score()` — the set
of event days was rebuilt inside a per-day loop, O(days × events), sixteen
minutes per file once jitter inflated the event count — fixed with results
byte-identical (780ec3e).

## What this settles

1. **Why control-flow conformance found nothing**: for the faults it missed,
   the log at the *deployed alphabet* carries no signal (fouling) or carries
   it in time and counts (valve faults), which the net does not encode.
   This is now measured, not argued — and scoped: X14 showed a richer
   alphabet does carry one of the fouling scenarios.
2. **Process mining's remaining contribution here** is the event log and
   its non-control-flow perspectives: counts (the frequency and absence
   channels, deployed), and timing (X12: real, redundant, costly). The
   discovered net's order structure contributes nothing on these systems
   at the deployed vocabulary; with a richer vocabulary (X14) the model
   channel fires far more, one more scenario becomes significant through a
   dose-monotone zone-damper signature, and the false-alarm rate breaks
   the budget.
3. **The misses stand at the deployed alphabet — and one of them falls
   to a richer one.** Eight of the twelve carry no log signal at 5 % in any
   count or duration on the deployed alphabet; four carry count changes
   the frequency bands did not resolve; the coil residual did not carry the
   fouling ones either. On the enriched alphabet, read through the
   frequency channel alone (X15), airside-moderate fouling is detected
   inside the budget under two holdouts — a candidate addition awaiting a
   separate adoption decision, to be pre-registered (X16).

## Ledger

| ID | Pre-registered | Ran | Predictions | Falsifiers | Artefact |
|---|---|---|---|---|---|
| X12 | ee33d5e | 2026-09-23 | P1 ✓ P2 ✓ **P3 ✗** P4 ✓ (weak) | none fired | `x12_time_perspective.json` |
| X13 | 89ae874 | 2026-09-23 | P1 ✗ P2 ✓ P3 ✓ | **F-X13.b fired** (under both the shipped and the deployed denominator convention) | `x13_coil_effectiveness.json` |
| X14 | c9e19f5 (A1 4187b97, A2 a1f5b3e, A3 06dea4c) | 2026-09-23 | P1 ✓ (by the letter) **P2 ✗** P3 ✓ | **F-X14.a fired** | `x14_enriched_alphabet.json` + `x14_control.json` |
| X15 | 0d0c692 (post-hoc-motivated, stated) | 2026-09-23 | P1 ✓ P2 ✓ P3 ✓ P4 ✓ | none fired | `x15_enriched_frequency.json` |
| X9/X10 | 289e53f (A1 65b7977, A2 823d339, A3 5b2be6d) | 2026-09-23 | all binding predictions ✓ | none fired | `x9_x10_robustness.json` |
