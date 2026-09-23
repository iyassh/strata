# Phase 9 Results — Can process mining be made to detect? (X12, X13)

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
than the deployed detector (0 of 11; typically day 14 vs day 1).

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

## What this settles

1. **Why control-flow conformance found nothing**: for the faults it missed,
   the log carries no signal (fouling) or carries it in time and counts
   (valve faults), which the net does not encode. This is now measured, not
   argued.
2. **Process mining's remaining contribution here** is the event log and
   its non-control-flow perspectives: counts (the frequency and absence
   channels, deployed), and timing (X12: real, redundant, costly). The
   discovered net's order structure contributes nothing on these systems.
3. **The misses stand.** Eight of the twelve carry no log signal at 5 % in
   any count or duration; four carry count changes the frequency bands did
   not resolve; the coil residual did not carry the fouling ones either.

## Ledger

| ID | Pre-registered | Ran | Predictions | Falsifiers | Artefact |
|---|---|---|---|---|---|
| X12 | ee33d5e | 2026-09-23 | P1 ✓ P2 ✓ **P3 ✗** P4 ✓ (weak) | none fired | `x12_time_perspective.json` |
| X13 | 89ae874 | 2026-09-23 | P1 ✗ P2 ✓ P3 ✓ | **F-X13.b fired** (under both the shipped and the deployed denominator convention) | `x13_coil_effectiveness.json` |
