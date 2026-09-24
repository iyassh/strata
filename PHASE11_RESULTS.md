# Phase 11 Results — After the review round: the conformance positive control (X22), the outdoor-air-fraction residual (X24), the statistical repair (X25), the first real building (X26), the fan-law virtual static (X27) the coil heat-transfer channel that saw nothing (X28), and the refrigerant-side test that saw everything (X29)

*2026-09-24. Both pre-registered (`docs/plans/2026-09-24-x22-conformance-positive-control-prereg.md` 2780137, `docs/plans/2026-09-24-x24-oa-fraction-prereg.md` 04c37ef) after the review round (`docs/plans/2026-09-24-review-verdict-and-improvement-plan.md`) and before any injected log or new residual was scored. Artefacts: `outputs/x22_positive_control.json`, `outputs/x24_oa_fraction.json`, regenerated `benchmark_v6_{fcu,sdahu,ddahu}.json` and `union_fpr_{fcu,sdahu,ddahu}.json`; guards `tests/test_x22_positive_control.py`, `tests/test_x24_oa_fraction.py`.*

## X22 — does the conformance channel fire on genuine order violations?

The review's single largest objection to the process-mining null was that
nothing showed the channel *would* fire if order really were violated. X22
injects order violations into each system's healthy HOLDOUT traces (the
72–96 days per system that define the channel's false-alarm floor), scores
them with the deployed net, threshold and significance gate, and adds two
threshold-free measures: the AUC of perturbed against unperturbed per-day
fitness, and the hit rate a threshold set at the healthy holdout's worst
day would give (the best any zero-false-alarm threshold can do; in-sample,
since that worst day is one of the days perturbed). It was run twice: once
with the pre-X25 detector (kept as `outputs/x22_positive_control_prex25.json`)
and once, below, with the deployed detector after X25's calibration slice.

| system | net labels | healthy mean fitness / threshold | reversal: flagged / sig | AUC | hit rate at zero FP | swaps k=8: AUC / sig | skips k=4: flagged / sig |
|---|---|---|---|---|---|---|---|
| SDAHU | 6 | 0.89 / 0.20 | 0 / 87, no | 0.91 | **0.00** | 0.81 / no | 0 / 87, no |
| PFPU | 7 | 0.90 / 0.81 | 4 / 96, no | 0.49 | 0.00 | 0.50 / no | 4 / 96, no |
| SFPU | 8 | 0.95 / 0.90 | 5 / 96, no | 0.50 | 0.00 | 0.50 / no | 6 / 96, no |
| DDAHU | 14 | 0.91 / 0.50 | **59 / 83, yes** | 0.99 | 0.71 | 0.96 / **yes** | 14 / 83, **yes** |
| FCU | 11 | 0.89 / 0.37 | **55 / 72, yes** | 0.99 | 0.75 | 0.97 / **yes** | 6 / 72, **yes** |

Duplicated blocks reach significance nowhere (P5 held: loops absorb
repetition; they add a few flagged days on the fan-powered units).
Deleting the start event fires nowhere (P2 failed everywhere, including
the two systems whose nets treat it as obligatory — on the fan-powered
units it *raises* fitness, AUC 0.40 and 0.36). Swaps rise monotonically on
every system but reach significance on two, not three (P3 failed). P4
(skips rise in k; single skips absorbed on the loop-heavy nets) holds on
the absorption half and fails on the rise for PFPU and SFPU. No falsifier
fired — reversal is significant on two systems, so F-X22.a ("blind
everywhere") did not fire — but P1's prediction (SDAHU fires) was wrong.

**What the instrument is.** Three different things, by system:

1. On the **fan coil unit and the dual-duct unit** the channel sees order:
   a reversed day drops fitness from 0.89 and 0.91 to 0.25 and 0.46, 55
   of 72 and 59 of 83 days are flagged, and a zero-false-alarm threshold
   would still catch 75 % and 71 %. Eight swaps and four deletions are
   significant too. On these two systems the null is instrument-validated:
   the channel can see order, and the faults (42 of 47 and 45 of 55
   detected, the model channel never alone) do not change it. The
   dual-duct unit only joined this group under X25: with the old in-sample
   threshold (0.25, the holdout minimum itself) its reversed days were
   invisible; with a threshold calibrated on a separate slice (0.50) they
   are not.
2. On the **single-duct unit** the channel sees order on average (AUC
   0.91) but not at any gate that keeps the budget: the healthy holdout
   contains days whose fitness (0.20 at the 1 % quantile) is below that of
   a fully reversed day, so the hit rate at zero false alarms is exactly
   zero. Blind by the *spread of healthy fitness*, not by the net. (Before
   X25, deletions of two or more events were significant here; with the
   new training slice they are not.)
3. On the **fan-powered units** fitness does not move under any
   perturbation (AUC 0.49–0.51 on everything except skip-start and one
   skip arm at 0.513). Those
   nets accept any order: blind by *net structure*, the reading the
   earlier reversal probe already gave.

So the null paper's statement becomes: on two of five systems the
conformance channel can see order and the faults do not change it; on one
it cannot see order at any false-alarm budget because healthy days already
span the fitness a reversed day has; on two it cannot see order at all.
That is a stronger and more honest statement than "conformance adds no
detections", and it is the sentence a process-mining reviewer needs.

## X24 — the outdoor-air-fraction residual

A new residual option `op: oa_fraction`: the outdoor-air fraction the
mixed-air temperature implies, (RA − MA)/(RA − OA), minus the damper
position, abstaining where |RA − OA| ≤ 10 °F; scored as a residual channel
with fraction-unit floors (0.05) that a per-rule override now allows.
Implemented in `src/` with no config touched first: the SDAHU scorecard
regenerated byte-identically (P1). Added to the FCU, SDAHU and DDAHU
configs; healthy silence unchanged (P2); configs committed before scoring.

| system | detected before → after | deployed FP | gained | lost | status changes |
|---|---|---|---|---|---|
| FCU | 41 → **42** of 47 | 4 → 4 of 96 | `OADMPRLeak_20` (residual) | none | stuck-30 % gains a residual credit; OA blockage and fan-outlet blockage gain a rules credit |
| SDAHU | 14 → 14 | 1 → 1 | — | none | none |
| DDAHU | 45 → 45 of 55 | 3 → 3 | — | none | OA damper stuck 80 %/100 % gain residual credit (166–178 more days) |

P3 (the 20 % leak), P4 (budget) and P5 (no loss) all held; no falsifier
fired. On the FCU the healthy residual sits at −0.195 almost every day —
the damper at its 30 % minimum passes about 10 % outdoor air, so the
damper–flow relation is far from linear — and the learned band absorbs
that offset, which is why the rule was scored as a residual channel rather
than a fixed-band rule. A blocked outdoor-air inlet shows as the mirror
case (fraction below position, 173 more residual days, 226 of 365). The FCU's misses are now
the five waterside-fouling files.

## Ledger

| X22 (post-X25) | P1 ✗ (FCU and DDAHU, not SDAHU) | P2 ✗ | P3 ✗ (2 of 3 systems) | P4 ✗ (no rise on the FPUs) | P5 ✓ | falsifiers: none |
|---|---|---|---|---|---|
| X24 | P1 ✓ byte-identical | P2 ✓ silent | P3 ✓ leak 20 % | P4 ✓ 4/1/3 of 96 | P5 ✓ no loss; falsifiers: none |



## X25 — the statistical repair

*Pre-registered (`docs/plans/2026-09-24-x25-statistical-repair-prereg.md`,
06ea608) before any code changed. Step 1 (5bd7c5e): the calibration slice
with the key absent — SDAHU byte-identical (P0). Step 2 (b35d23b): the
uniform rule-of-three floor and `calibration_days_per_month: 8` in all five
configs, committed before regeneration. Artefacts: every
`benchmark_v6_*.json` and `union_fpr_*.json`; `outputs/x25_statistical_repair.json`;
guard `tests/test_x25_statistical_repair.py`.*

The two conformance channels had set their thresholds on the same holdout
days on which every false-alarm rate is reported; their rows were
calibration targets, disclosed since Phase 6 and flagged by every review
since. Now the eight days before each month's holdout block calibrate
those thresholds, discovery trains on the rest, and the holdout is
out-of-sample for every channel. The residual and model gates also use the
rules channel's rule-of-three floor instead of one holdout false alarm.

| system | detected | deployed FP before → after | model threshold | model FP row (in-sample → out-of-sample) | model credits |
|---|---|---|---|---|---|
| SDAHU | 14 → 14 | 1 → 1 | 0.333 → 0.200 | 0 → 0 | 0 → 0 |
| PFPU | 23 → 23 | 5 → **7** | 0.793 → 0.807 | 1 → **4** | 0 → 0 |
| SFPU | 24 → 24 | 4 → **6** | 0.882 → 0.902 | 1 → **5** | 5 → 5 |
| DDAHU | 45 → 45 | 3 → 3 | 0.250 → 0.500 | 0 → 0 | 0 → 2 |
| FCU | 42 → 42 | 4 → 4 | 0.362 → 0.371 | 1 → 1 | 7 → 9 |

Every prediction held and no falsifier fired: the rows are out-of-sample
(P1), every budget stays under 10 of 96 (P2), no count moved and nothing
is detected by conformance alone (P3), and the floor changed no verdict
at all (P4: zero status flips). The one thing the repair measured is what
the disclosure had been saying: the in-sample model rows on the two
fan-powered units understated their false alarms by three and four days.
Their deployed budgets are now 7.3 % and 6.2 %; the single-duct, dual-duct
and fan coil units did not move. The device channel's row on the series
unit fell from 3 to 1. Four scenarios gained a model credit beside channels
that already carried them.

The papers' budget range is therefore 1.0–7.3 %, out-of-sample. Three
things the review of this section added: (i) the calibration slice removes
96 days from discovery training, so X25 changed the discovered *nets*, not
only the thresholds (the FCU net has 11 labels after, 13 before; the
DDAHU net's behaviour under reversal in X22 changed accordingly); (ii) the
device-channel provenance string still read "calibration target" where
the device channel is absent (SDAHU, FCU), a fall-through in the script,
now "channel absent"; (iii) the floor as implemented in step 2 was
3/365 = 0.0082, which at 96 holdout days is *looser* than the one-false-
alarm floor it replaced (1/96 = 0.0104) and looser than the frequency and
oscillation gates' 3/96. That is an implementation error against the
pre-registration's intent ("the rules channel's rule of three" applied to
the holdout sample); step 3 below corrects it to max(fp, 3)/n and is
regenerated alone, which also separates the floor's effect from the
split's (the P4 claim above rests on the two applied together).

| P0 | P1 | P2 | P3 | P4 | falsifiers |
|---|---|---|---|---|---|
| ✓ byte-identical | ✓ out-of-sample | ✓ ≤ 10/96 | ✓ counts, none by conformance | ✓ 0 flips | none |

### Steps 3 and 4: the floor, done properly, costs detections

Step 2's floor was 3/365 at every n — at 96 holdout days *looser* than the
one-false-alarm floor it replaced. Step 3 (4db776e) made it max(fp, 3)/n
on the residual gate's n, which was holdout *window-days pooled over
channels* (509 on the dual-duct unit, 124 on the series unit): the same
rule was 3/509 on one system and 3/124 on another, so step 3 *gained* a
dual-duct scenario (hot-deck static bias −0.4 in.wg, 8 flagged days) while
losing a series-unit one. Amendment 1 (fbc95bb) made the null per day: the
residual channel's flag is an OR over its channels per day, so its
false-alarm count and denominator are holdout *days* flagged by any channel
over holdout days any channel could evaluate — the quantities the
false-alarm artefact reports — with the floor max(fp, 3)/n on those days
(3/41 on the fan-powered units, 3/72 on the fan coil, 3/74–75 on the air
handlers). That is a heavier floor than the pooled one wherever the
residual channels can evaluate few holdout days, and it removed
detections.

| system | before X25 | after step 4 | lost | gained | deployed FP |
|---|---|---|---|---|---|
| SDAHU | 13 / 14 adjudicated (14 / 14 naive, erratum E5) | 13 / 14 | — | — | 1 → 1 |
| PFPU | 23 / 30 | **22 / 30** | room-temperature bias +4 °C | — | 5 → 7 |
| SFPU | 24 / 29 | **21 / 29** | reheat fouling airside severe, waterside severe; fan restrict-flow | — | 4 → 6 |
| DDAHU | 45 / 55 | 45 / 55 | hot-deck SAT bias +2 °C (residual-only) | cold static +0.2 in.wg (X27) | 3 → 3 |
| FCU | 42 / 47 | **40 / 47** | OA damper leaking 20 % (the X24 gain), 50 % | — | 4 → 4 |

**F-X25.c fired** on the series unit (three detections lost, more than the
two the pre-registration allowed), so the repair is reported as what it is:
a detector change. Every lost scenario was carried by the residual channel
alone with a flagged-day count that the pooled null had certified and the
per-day null does not (fan-powered residual channels evaluate 41 holdout
days, so three false alarms is 7 %; a scenario needs roughly one flagged
day in six to clear it). No detection is conformance-only (P3 half holds);
eight detections changed verdict and nineteen scenarios changed channel
attribution in all (P4 failed as written). Seven residual-only detections
were lost across the five systems, one of them offset on the dual-duct
unit by X27's new channel. The
budgets are unchanged by steps 3–4. The step-3 → step-4 diff is
`outputs/x25_step4_perday.json`; the overall diff is regenerated in
`outputs/x25_statistical_repair.json`.

What the final gate is: every channel's null is a per-day rate on its own
evaluable holdout days, floored at three days, with conformance thresholds
calibrated on a separate slice. The papers' counts are now 13/14, 22/30,
21/29, 45/55, 40/47 at 1.0–7.3 % false-alarm days, all out-of-sample.

| step | P0 | P1 | P2 | P3 | P4 | falsifiers |
|---|---|---|---|---|---|---|
| 2 (split + 3/365) | ✓ | ✓ | ✓ | ✓ | ✓ 0 flips | none |
| 3 (max(fp,3)/pooled n) | — | ✓ | ✓ | ✓ (±1) | ✗ 2 flips | none |
| 4 (per-day null) | — | ✓ | ✓ | **✗ DDAHU −3 vs step 3; SFPU −3 vs pre-X25** | ✗ 8 verdicts | **F-X25.c** |

## X26 — the false-alarm budget on a real building

*Pre-registered (`docs/plans/2026-09-24-x26-real-data-budget-prereg.md`,
66de30d) after profiling the fault-free stream only; config committed
(52b9e94) before scoring; Amendment 1 (993cdbf) after run 1 and before the
rerun. Artefacts: `configs/lbnl_rtu_field/`, `scripts/07_convert_rtu_field.py`,
`outputs/week0_audit_rtu_field.json`, `benchmark_v6_rtu_field.json`,
`union_fpr_rtu_field.json` (+ `*_run1.json`), `x26_real_data_budget.json`;
guard `tests/test_x26_real_data_budget.py`.*

**The data.** LBNL's field rooftop unit, Site 2: a 10-ton RTU on a
distribution centre in Connecticut, 25 measured points (air temperatures
and humidities, fan and compressor power, airflow, refrigerant pressures
and line temperatures on two circuits), one-minute, °C and bar; 182
fault-free days across two summers and one 29-day fault case (40 %
undercharge on circuit B). No schedule, damper, valve or command point
exists. Site 1 (a 7.5-ton unit on a restaurant) ships 52 clean days and a
62-day staging fault on a different machine: too few clean days to
calibrate, so it is excluded and scored against Site 2's detector only to
show what a foreign unit looks like (model channel 41 of its 52 clean
days, residual 35). Site 2 is the measured stream this test uses, and
this test asks one thing of it: does the deployed detector's false-alarm
budget survive real data?

**Onboarding.** Config only, plus one documented derived column
(`FAN_ON` = supply-fan power > 100 W, mapped to the occupancy signal
because the unit has no schedule). Two logged healthy-silence iterations:
the field mixed-air probe reads below both outdoor and return air on 26 %
of fan-on minutes, by more than the 1.1 °C tolerance on 9 %, and by up to
2.3 °C sustained for an hour (tolerance 1.1 → 2.5 °C), and the evaporator keeps cooling the air after the compressor
stops (supply − mixed down to −6.9 °C; rule band −3..3 → −8..4.5). Gates:
no duplicates, monotonic; the rotation gate produced no output on this
subset; calendar identity is inapplicable
(the files cover different periods); no Brick file exists for the field
subset.

**The budget (P2): 3 of 49 holdout days, 6.1 %.** Rules 0, residual 1,
model 0 (threshold out-of-sample under X25), absence 0, frequency 2,
oscillation 1; rate 1 (advisory); naive union 4. Every residual channel
was evaluable on every holdout day, so P3 (some abstention) failed as a
prediction. The budget holds on the first real building, at a rate
above every simulated system's (1.0–7.3 % after X25).

**The case (P4, then A1-P2): not seen.** Run 1's config watched circuit
1's refrigerant sensors; the documented fault is on circuit B. Amendment 1
added the circuit-2 residuals. With both circuits the undercharge file
still flags 1 residual day and 1 model day of its 29 evaluable days (30
calendar days; the pre-registration's "29" counted the evaluable ones),
and the reason is in the
recorded points: during compressor operation, circuit-2 suction pressure
(6.51 vs 6.57 bar), suction-line temperature (26.5 vs 26.5 °C) and
condenser-outlet temperature (28.2 vs 27.1 °C) sit within a few per cent
of the healthy June. Whatever a 40 % undercharge did to this unit, it did
not reach these sensors at a size a healthy-calibrated band can see — or
the point labelled circuit 2 is not the circuit labelled B. One fault of
one kind on one unit is a case, and it is reported as one; nothing about
detection is claimed from it.

**What X26 changes.** The papers' "everything is simulation" limitation
is now stated with a number: on one real building the deployed budget is
6.1 %, and nothing about detection is claimed from it.

| P1 | P2 | P3 | P4 / A1-P2 | falsifiers |
|---|---|---|---|---|
| ✓ 2 iterations | ✓ 3/49 (6.1 %) | ✗ no abstention | ✗ case not seen (both circuits) | none |


## X27 — the fan-law virtual static

*Pre-registered (`docs/plans/2026-09-24-x27-fan-law-static-prereg.md`,
0477a56) before any change; step 1 (c7f35fc) `op: ratio_sq` with no config
touched — SDAHU byte-identical (a caveat string in the false-alarm artefact
differed, its committed copy predating the X25 wording; every number
identical); step 2 (9e7eead) the two channels in the DDAHU config, committed
before scoring. Artefacts: regenerated `benchmark_v6_ddahu.json`,
`union_fpr_ddahu.json`; `outputs/x27_fan_law_static.json`; guard
`tests/test_x27_fan_law_static.py`.*

*Scored under X25 step 2's floor (3/365); superseded by step 4, under which
DDAHU is 45 of 55, the airside-moderate fouling gain below is lost, and the
cold +0.2 in.wg bias gain survives — see the X25 addendum.*

A biased static-pressure sensor is unobservable from the static itself; the
loop hides it in fan speed. The existing per-speed proxy (static ÷ speed)
caught 5 of 8 biases; the fan law says static ∝ speed² at constant system
resistance, so static ÷ speed² was added for both decks, band learned on
healthy. The healthy band of the new ratio is *wider* than the old one
(cold deck 1.24–3.56 against 1.24–2.39 daily medians), because on a VAV
unit the system resistance is not constant — the zone dampers move — and
that was visible before scoring.

| | before | after |
|---|---|---|
| static-bias scenarios detected | 5 / 8 | **6 / 8** (cold +0.2 in.wg gained; hot −0.2, −0.4 still missed) |
| DDAHU detected | 45 / 55 | **47 / 55** |
| deployed false alarms | 3 / 96 | 3 / 96 |
| lost | — | none |

**F-X27.b fired** (the bar was 7 of 8). The unpredicted gain is the
cooling-coil *airside moderate* fouling: an airside-fouled coil raises the
airflow resistance, the fan runs faster for the same static, and static ÷
speed² falls — the fan-law channel is an airflow-resistance detector, which
is what a virtual static is. Residual-day counts on the already-detected
biases rose by 1.2× to 16× (cold −0.2/−0.4: 38 → 45; hot +0.2: 10 → 165;
hot +0.4: 74 → 260). The
two hot-deck negative biases remain invisible: a −0.2 in.wg reading on a
1.0 in.wg setpoint makes the loop run the fan slightly faster, and the
ratio shift sits inside a band that the moving zone dampers already widen.
A regression on speed *and* flow (the system curve) is the next form; it
is a fitted model, not a ratio, and is not attempted here.

| P0 | P1 | P2 | P3 | falsifiers |
|---|---|---|---|---|
| ✓ (numbers identical; one caveat string refreshed) | ✓ 3/96 | **✗** 6 of 8 | ✓ none lost | F-X27.b |


## X28 — the coil heat-transfer (UA) channel

*Pre-registered (`docs/plans/2026-09-24-x28-coil-ua-prereg.md`, 8ef5661)
before any code; step 1 (bc2dc4e) `op: ua` with no config touched — SDAHU
byte-identical; step 2 (73a475d) `chwc_ua` and `hwc_ua` on the dual-duct
and fan coil units with floors set once on the healthy year (5 % of the
training-day median UA), committed before scoring on the final X25 gate.
Artefacts: `outputs/x28_coil_ua_run1.json` (both systems with the
channels), `benchmark_v6_fcu_x28run1.json`, `union_fpr_fcu_x28run1.json`;
the live DDAHU scorecard keeps the channels; guard `tests/test_x28_coil_ua.py`.*

UA = Q / LMTD from the water side (flow × |EWT − LWT|) and the four
terminal temperatures, gated on the coil valve and flow, daily-median
scored, band learned on healthy. The healthy bands were wide before any
fault file was opened: the dual-duct cooling coil's daily-median UA runs
2.3–14.1 (gpm·°F per °F) on training days, the fan coil's 0.7–2.1; the
heating coils' are narrow (0.6–1.1, 0.2–0.5).

| system | fouling detected before → after | detected | deployed FP | residual-channel FP |
|---|---|---|---|---|
| DDAHU | 5 / 12 → 5 / 12 | 45 → 45 | 3 → 3 | 0 → 0 |
| FCU | 6 / 11 → 6 / 11 | 40 → 40 | 4 → **6** | 3 → **5** |

No fouling scenario gained on either system — **F-X28.b fired** — and on
the fan coil unit the two channels added two holdout false alarms for no
detection: the pre-registration's P1 (each channel ≤ 1 holdout false
alarm) is violated by the only change made, and **F-X28.a** ("P1 fails on
a system → the channels are removed there") removed them from that config
(the ledger script had tested only P1's budget clause; it now tests the
residual-row rise as well) (the scorecard was
regenerated without them; the run-1 artefacts are kept). On the dual-duct
unit they stay, inert: no gain, no false alarm. The per-scenario residual
day counts barely moved (fan coil waterside files: 3 → 5 or 6 of 365).

**Reading.** The X19 diagnostic had already shown that the fan coil's
recorded water-side signals sit within about three per cent of healthy
under waterside fouling; UA, being computed from those same signals, sees
what they see. On the dual-duct unit the cooling coil's healthy UA varies
by a factor of six across the year at partial load — the LMTD is small and
noisy when the valve throttles — and the fouling files sit inside that
spread. The domain review's expectation was right in the one case it
named and wrong in the other. Fouling on these two datasets is a property
of what was recorded, not of the detector's vocabulary: the temperature
band (X13), the enriched alphabet (X14/X15), the water-side ΔT, and now
the heat-transfer estimate all fail on the same files. The refrigerant-side
observability test on the simulated rooftop unit (plan item B4) is the
remaining way to show that fouling *can* be seen when its own physics is
recorded.

| P0 | P1 | P2 | P3 | P4 | falsifiers |
|---|---|---|---|---|---|
| ✓ | ✗ FCU (+2 FP) | ✗ 0 gained | ✗ 0 gained | ✓ | F-X28.a (FCU), F-X28.b |


## X29 — refrigerant-side observability: fouling is seen when its physics is recorded

*Pre-registered (`docs/plans/2026-09-24-x29-refrigerant-observability-prereg.md`,
df064db) after the documentation and the baseline header only; config
committed (379cca9) before scoring. Artefacts: `configs/lbnl_rtu_sim/`,
`scripts/08_convert_rtu_sim.py`, `outputs/week0_audit_rtu_sim.json`,
`benchmark_v6_rtu_sim.json`, `union_fpr_rtu_sim.json`,
`x29_refrigerant_observability.json`; guard `tests/test_x29_refrigerant_observability.py`.*

Four quantities from the air- and water-side points had failed on the same
fouling files (X13, X14/X15, water-side ΔT, X28). The claim that fouling on
those datasets is a property of the recorded points has one direct test: a
dataset that records the fouled component's own physics. LBNL's simulated
rooftop unit (NREL Modelica–EnergyPlus co-simulation of a 5-ton unit; 100
days, one-minute, 25 points including condensing, discharge and suction
pressures and line temperatures; one baseline and 24 fault files: condenser
and evaporator fouling at 10/20/30/40/50 %, liquid- and suction-line
restrictions, over- and undercharge) is that dataset. The two delivered-
capacity outputs, which no building records, were excluded from every rule.

**Onboarding.** Config only plus a derived `OPERATE` = 1 (no schedule; the
fan runs continuously). Five compressor-on residual channels written from
the physics — condenser approach (`REFG_COND_TEMP − OA_TEMP`), discharge
superheat, a suction-superheat proxy, the discharge/suction pressure
ratio, and return-minus-supply air — with fixed rule bands from the
baseline's compressor-on p0.1/p99.9. Gates clean (25 distinct files, one
shared calendar, Brick file covers every column); healthy silence at the
first iteration. Under the X25 gate: 8 holdout days per month of a
100-day record gives 29 holdout days.

| family | detected / scored | channels |
|---|---|---|
| condenser fouling 10–50 % | **5 / 5**, monotone | residual (condenser approach, pressure ratio) |
| evaporator fouling 10–50 % | **5 / 5**, monotone | residual; the 50 % file also rules, frequency, oscillation |
| liquid-line restriction (0.1–1.0 bar) | **4 / 4** | residual (+ oscillation on two) |
| suction-line restriction (0.1–0.9 bar) | **4 / 4** | residual, then rules/frequency/oscillation at higher restriction |
| refrigerant overcharge 10/15/20 % | 1 / 3 (20 % only) | residual, frequency, oscillation |
| refrigerant undercharge 10/15/20 % | 1 / 3 (20 % only) | residual, oscillation |
| **all** | **20 / 24** | residual on all 20; conformance on none |

Deployed false alarms: **1 of 29 holdout days (3.4 %)**; the naive union is
the same 1 (rate flags none). Every prediction held and no falsifier
fired; no source change.

**Reading.** The detector that misses coil fouling on the air handlers and
the fan coil unit, with the same calibration, the same gate and the same
rule kinds, catches every fouling severity down to 10 % on a unit whose
fouled component's pressures and temperatures are recorded — and catches
it with a single physically named residual (condensing temperature above
outdoor air rises with a fouled condenser; the pressure ratio rises with
either fouled coil). The fouling misses elsewhere are therefore a property
of what those datasets record, not of the detector's vocabulary or its
gate. The two families it does not fully see here are the small charge
faults (10 and 15 % over- or undercharge), whose superheat proxies sit
inside the healthy band; the 20 % cases are caught. The limits of this
test are the ones its data impose: one simulated unit, one summer-autumn
period, a 29-day false-alarm denominator, and a fixed room setpoint.

| P1 | P2 | P3 | P4 | P5 | P6 | falsifiers |
|---|---|---|---|---|---|---|
| ✓ gates, 1 iteration | ✓ 1/29 | ✓ 5/5 monotone | ✓ 5/5 monotone | ✓ 10/14 | ✓ | none |
