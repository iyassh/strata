# Gap Analysis — Post-Phase-2 Deep Review (2026-08-10)

Product of a 3-agent adversarial pass over the Phase 1–2 results: hostile methods
review of the strata codebase and numbers; vault sweep (41 papers + synthesis
notes); web verification (APAR primary sources, LBNL evaluation framework,
competing 2026 work). Eleven gaps found. Status legend: **FIXED** (in benchmark
v5 / code today) · **REFRAMED** (reporting/positioning corrected) ·
**SCHEDULED** (later phase, now with a precise spec).

## The gaps

**G1 · Residual band was data-snooped — MAJOR — FIXED.**
The Phase-2 band (−2.6…+3.3 °F) was placed knowing where the bias scenarios sit
(the config comments admitted it); the +2 °C detections had only a 0.31 °F
margin. Fix shipped: the detection channel is now a per-day CONTINUOUS score
(median coil-off occupied SA−MA residual) with the band calibrated on TRAIN
days only — no fault file, no holdout day touches calibration. The daily median
washes out shutdown transients, which is what forced the hand-tuning. The event
rule remains only for localization display and is excluded from scoring.

**G2 · "q0.01-calibrated" fitness threshold is really min-calibration on a
discrete 8-valued distribution — MAJOR — REFRAMED + SCHEDULED.**
Holdout fitness takes 8 distinct values (71/87 days at 1.0); the threshold sits
one float-ulp above 1/3, so the real rule is "worse than the worst healthy
day," and the achievable FPR ladder is discrete (next rung 4.6%). v5 states
min-calibration honestly. The real fix — a continuous conformance score
(alignment-cost / unexpected+missing counts) — goes into Phase 4 with the
frequency-aware upgrade.

**G3 · FPR denominator recycled the calibration set; only 351 independent
negative days exist, from a self-relabeled file — MAJOR — FIXED.**
v5 removes calibration days from the headline negatives, computes (never
asserts) the rules channel's healthy counts, reports the independent run
separately with a printed caveat that it is LBNL's oa_bias_4 relabeled healthy
after our byte-identity audit. Honest statement: FPR is measured on one
simulation run of one weather year.

**G4 · The model channel's 18 "unique" days are statistically its false-alarm
rate, yet inflated the combined headline — MAJOR — REFRAMED.**
Unique-day rate on bias scenarios (1.1–1.4%) equals its rate on the negative
run (1.4%). v5 reports the model channel as its own arm — a measured null on
SDAHU — and never adds noise days into a headline. This is Phase 1's honest
thesis, now enforced in the reporting code.

**G5 · Pooled per-day F1 over 4,540 correlated days was the wrong headline —
MAJOR — FIXED.**
Faults persist all year (day-recall = "a detection window existed that day");
under the V1 EVENT ALPHABET five scenarios were event-log-identical copies
(coi_stuck_010/025/050/075 + coi_leakage_010 shared one log;
damper_stuck_010=025) — **scope note (2026-08-18): true for the v1 alphabet
only; under the current alphabet all 14 SDAHU logs are distinct
(`event_identical_groups: {}` in v12). The BYTE-identical duplicate groups
(oa_bias ×4, coi_leakage ×4) are dataset facts and stand — see ERRATA.md
E1/E2**; 69% of positive days were the saturated stuck/leak family. v5 reports per scenario — detected
y/n, time-to-first-detection, alarm-day fraction — aggregates per family, tags
event-identical groups automatically by log hash, and demotes pooled rates to a
JSON appendix. (Frank et al. 2019 licenses day-slice samples; it also warns
against mixing sample definitions — v5 states its definition explicitly.)

**G6 · The 38–45% bias recall is structural and UNDERSOLD the result — FIXED
(now the strongest single number).**
Measured *(v5 numbers; v12: windows 137–164 days, window-conditional recall
measured 100%, per-scenario recall 39–47% — quote the Part V addendum)*:
detection windows (≥120 min coil-off occupied) exist on 134–158 days
per bias year; the rule detected on essentially all of them (conditional recall
≈98–100%). v5 reports the decomposition: window prevalence × window-conditional
recall. The honest claim — "we detect on essentially every day physics permits
a test; windows exist on ~40% of days in climate 5A" — is stronger than any
pooled recall. Bonus found by the audit: the bias itself changes coil duty and
hence window prevalence (explains the −bias > +bias asymmetry); the paper must
say so before a reviewer asks.

**G7 · Zero-event days silently vanished from the day universe — MAJOR for the
fail-silent hole — FIXED.**
The day universe now comes from raw data; unoccupied days are counted
not-evaluable explicitly; an OCCUPIED day with zero events is now FLAGGED
(silence on a scheduled day is a deviation) — closing the hole where a fault
that suppresses all activity would have been excluded instead of caught.

**G8 · Gates failed open on unmapped sensors — MAJOR for portability — FIXED.**
A rule that declares gate/occupancy signals is now skipped entirely when they
are unmapped (fail closed, tested). Previously the first FPU config missing
CHWC_VLV_POS would have run the setpoint rule ungated — a documented ~95%/day
alarm storm.

**G9 · No family-wise false-alarm budget as rules stack — SCHEDULED (Phase 4,
per plan).**
Each rule is individually 0-FP on ~686 clean sim days (upper bound ≈0.44%/day
each); OR-ing seven rules compounds. The joint-FPR budget was already planned;
the audit adds: report the union bound alongside observed zeros. Web sweep
found NO prior building-FDD work on joint alarm budgeting across a rule
battery — this is a claimable first if done properly (cite Benjamini-Hochberg).

**G10 · Sustained runs split at midnight — MINOR — SCHEDULED.**
Bites only when the residual gate extends to unoccupied hours (the known next
increment). Fix spec: find runs on the continuous series, assign the event to
the day the run completes.

**G11 · Jan-1 starts at 01:00 (23-hour first day) — MINOR — documented.**

## Two discoveries made WHILE fixing the gaps (2026-08-10, late)

**F1 · The oa_bias "healthy re-run" relabel is OVERTURNED — oa_bias_4 is a real
fault file, and SDAHU therefore has NO independent healthy negative.**
The blind residual channel "false-alarmed" on 148/303 days of the supposed
healthy-like run — which prompted a re-examination. Evidence: with the same
weather (OA_CFM bit-identical to healthy; recorded OA_TEMP within 0.33 °F,
mean 0.02 °F — nowhere near the labeled ±2–4 °F bias, so no sensor-side
bias exists in the data; the sub-degree residual is intake-node flow
feedback — precise stats in `week0_audit.json` gate 5 / ERRATA.md E1), the
building behaves differently — MA/SA/RA correlations drop to 0.78–0.84 with
|diff| p95 ≈ 15 °F, damper correlation 0.91. *(Scope corrections 2026-08-18:
(1) much of that healthy-vs-fault divergence is the configuration-branch
offset shared by ALL fault files — ERRATA.md E5 — not this fault; the
fault-specific signal is a ~2 °F shift in the cooling interlock only.
(2) The mechanism claim is bounded honestly in ERRATA.md E1: consistent
with a controller-side bias confined to the cooling interlock, but
observationally indistinguishable from a mislabeled cooling-lockout fault.
What is proven: the labeled sensor bias is not in the data and the run is
faulty.)* (The four
oa_bias files are byte-identical to each other: one run shipped four times;
the injected severity is not recoverable.) Consequences: (a) the residual
channel's 48.8% "FPR" was actually ~100%-of-window-days DETECTION of a fifth
fault family that rules, model, and every prior version missed entirely;
(b) v1–v4's FPR numbers were measured against a fault file (conservative,
in our disfavor — the honest direction); (c) SDAHU now has no independent
negative run — false-alarm evidence is holdout days only, until the FPU
FaultFree files arrive in Phase 3. Also citable: AFGCN's OA-bias class was
trained on this file believing the logged column carries the bias.

**F2 · The model channel's flags were "equipment active while unoccupied" —
the occupancy-masked G7 fix was wrong and is corrected.**
Debugging why the model channel zeroed out under v5 revealed where its flags
had been living all along: unoccupied days (holidays) where a stuck-open valve
kept cooling an empty building — short, weird traces the healthy net rejects.
That is a genuine sequence-fault signature (off-hours operation), not noise.
Corrected semantics: a day is evaluable if it emits events OR is occupied;
only silent unoccupied days are not evaluable; silence on an occupied day is
itself a flag. This also sharpens the model channel's story: what little it
catches on SDAHU is exactly the coordination class (running-while-unoccupied)
that neither rules nor residuals express.

## Positioning corrections (from the vault + web sweeps)

1. **Our residuals ARE APAR rules — cite, don't claim.** Supply-air residual =
   APAR Rule 7 (|Tsa − ΔTsf − Tma| > εt, coil-off mode; sensor error is one of
   its listed diagnoses) with siblings 1/11/16; mixed-air envelope = Rules
   26/27. Verified in the primary sources (Schein & Bushby 2006; House et al.
   2001; NISTIR 7365, which also gives the canonical parameters: εt = 3.6 °F,
   ΔTsf = 2.0 °F — our calibrated band sits inside the established range).
   Correct framing: "APAR Rules 7/26/27, statistically calibrated on healthy
   data" — lineage as credibility, novelty in the calibration + config-kind
   architecture + protocol. NISTIR 7365 itself documents that APAR practice
   was trial-and-error tuning — the perfect citable foil.
   *Action: Schein & Bushby 2006 PDF added to the vault reading list.*
2. **Per-day metrics are framework-sanctioned** (Frank et al., E&B 192, 2019:
   experts recommend day-or-longer regular slices) — cite it, and state the
   input-sample definition next to every metric.
3. **Chahine & Noura 2026 (Sensors 26(11):3465) must be cited**: LightGBM
   virtual-sensor residuals, near-perfect SAT-bias detection on the SAME
   dataset. Honest positioning: transparent, training-free rules recover the
   physics-permitted fraction of fault-days; learned per-sensor models are the
   upper bound. Also: they use Brick for auto-configuration — closest living
   relative of our config-only pipeline; differentiate on discovered models +
   localization + multi-system transfer.
4. **AFGCN's OA-bias class is trained on artifact data** (the oa_bias files
   contain no bias — our audit) — usable, carefully, when comparing.
5. **Naples group check (Aug 2026): still no buildings work.** New arXiv
   2604.18066 moves them toward alarm explanation — conceptually adjacent;
   the preprint clock is real.

## Where this leaves the results story

- Rules channel (APAR-style events, now snoop-free): the workhorse — stuck/
  leak/leakage at 100% of days, TTD 1 day.
- Residual channel (blind-calibrated): bias family detected in every scenario,
  on ~all physics-window days; the first unsupervised per-day bias numbers
  published on SDAHU.
- Model channel: measured null on SDAHU — reported as such, by design; its
  real test is FPU (Phase 3).
- All channels: FPR measured honestly on one independent run; family-wise
  budget scheduled for Phase 4.
