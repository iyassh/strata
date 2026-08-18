# STRATA Research Log — Findings, Gaps, Causes, Fixes

*The honest ledger of 2026-08-10 (Phases 1 → 3b) and the decisions behind
every number. Written for the paper: much of the methods section, the
threats-to-validity section, and the "lessons" discussion live here.
Format per entry: WHAT we found · WHY it happened · WHAT we did · PAPER VALUE.*

Companion docs: `GAP_ANALYSIS_AUG2026.md` (gaps G1–G11), `PHASE1_RESULTS.md`,
`PHASE2_RESULTS.md`, `PHASE3B_RESULTS.md` (rev 2), `configs/ONBOARDING_LOG.md`,
`outputs/week0_audit.json`, benchmark JSONs v3–v6. Vault: `ProcessHeal_STRATA_v2_Revision.md`,
`ProcessHeal_Implementation_Plan.md`.

---

## Part I — The discoveries (things we now know that nobody wrote down before)

### D1. The circularity number: 3.4 percentage points
- **Found:** before the alphabet split, the "discovered model" channel showed 5.2%
  recall; after (discovery restricted to fault-agnostic state events) it shows 1.8%.
  The 3.4pp difference IS the circularity — the model re-detecting our own rules.
- **Why it happened:** v1's event alphabet mixed neutral state events with
  fault-signature events (mismatch/leak). The healthy net, discovered over that
  alphabet, flagged fault days mainly because signature events appeared as moves
  it had no transition for. The +0.4pp headline of the original pipeline was this
  circle in disguise.
- **Fix:** the state/signature alphabet split, enforced end-to-end with a tested
  invariant (injecting signature events cannot change a day's fitness).
- **Paper value:** a *measured* quantification of a methodological trap the whole
  PM-on-sensor-data literature warns about abstractly. Few papers measure their
  own circularity; ours does, to one decimal.

### D2. The oa_bias relabel, overturned twice
- **Found:** LBNL's four oa_bias files are byte-identical to each other and the
  logged OA_TEMP matches healthy to 2e-5 °F — so v1 relabeled them "healthy-like."
  Then the blind residual channel "false-alarmed" on 148/303 days of that file —
  which forced a re-examination: under bit-identical weather inputs, the building
  BEHAVES differently (MA/SA/RA correlations 0.78–0.84, damper corr 0.91). Verdict:
  it is a real fault run with a CONTROLLER-SIDE OA bias — the fault is applied to
  what the controller reads and never appears in the logged column.
- **Why it happened:** dataset packaging error (one run shipped four times) plus
  a subtle injection convention (bias at the controller input, not the logger).
- **Fix:** relabeled as a fifth SDAHU fault family (detected on ~100% of physics-
  window days by the residual channel); consequence accepted: SDAHU has NO
  independent healthy negative, stated on every output.
- **Paper value:** (a) a dataset-quality contribution the community needs; (b) the
  published AFGCN paper trained its OA-bias class on this file believing the
  logged column carries the bias — citable, carefully; (c) a case study in why
  "false positives" deserve investigation before dismissal — ours turned out to
  be detections.

### D3. Physics windows, not recall ceilings
- **Found:** sensor-bias recall looked like "38–45%" until decomposed: detection
  windows (coil off + zone occupied, ≥120 min) exist on ~40–45% of days in this
  climate, and the residual rule detects on essentially every window day
  (conditional recall ≈98–100%).
- **Why:** the residual is only physics-bound when no control loop is hiding it;
  summer all-day cooling gives no window. The fault itself changes window
  prevalence (bias alters coil duty) — explaining the −bias > +bias asymmetry.
- **Fix:** report window prevalence × window-conditional recall, never pooled
  recall; TTD as the operational metric (median 1–2 days).
- **Paper value:** an evaluation-methodology point: for gated detectors, pooled
  recall confounds climate with capability.

### D4. The SFPU unit-model finding (the honest version)
- **Found:** on the series FPU, zone damper-stuck and negative airflow-bias
  faults erase the AHU's daily heating rhythm (healthy 357/365 heating-days;
  ~273 missing under fault). The discovered healthy net flags the ABSENCE:
  22–26 robust days per scenario (threshold-inflated count 135–140), 15–17 of
  them caught by no other channel. Absent on the parallel FPU — but NOT because
  the fault doesn't couple (heating days drop 166→90 there too): because PFPU's
  healthy heating has no daily rhythm for order-based conformance to miss.
- **Why the mechanism exists:** series topology puts primary air and zone heating
  on one path (Titus/Nailor/ASHRAE RP-1292 confirm the engineering); zone-S
  over-delivery (+351 CFM above SP at stuck-80) removes the heating call.
- **The falsifier fired (and we honor it):** a one-line matched rule ("occupied
  workday AND heating never active", 0/365 healthy FP) out-covers the model
  channel (192 vs 135 days). Reframed claim: the discovered model FOUND the
  load-bearing invariant unsupervised — the rule exists only after the model
  showed where to look. The matched rule is now a permanent ablation arm.
- **Paper value:** the central narrative. Discovery-automation, detection-by-
  absence (scoped: model-moves exist in BPM; first application to discovered
  healthy models for HVAC terminal units), a measured cross-system contrast,
  and a pre-registered prediction: the Phase-4 frequency-aware channel should
  see the PFPU heating-count collapse that order-only conformance cannot.

### D5. Onboarding evidence (the scalability claim, measured)
- Two new systems onboarded config-only: 48 sensor mappings + ~35 rules each;
  SFPU derived from PFPU in minutes; ONE threshold tuned (on healthy data, with
  the measurement recorded: healthy SAT excursions max 17 consecutive minutes).
  Healthy-silence perfect on both FaultFree years. Field anchors: SeeQ's
  config-line metric; Lin et al. $13k/building setup cost.

---

## Part II — The gap ledger (what bit us, why, and the standing rule it produced)

Each entry became a permanent discipline. These are the paper's
threats-to-validity section, pre-answered.

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L1 | Residual thresholds data-snooped (G1) | Chose the band while able to see fault distributions | Per-day continuous score, TRAIN-only calibration. **Rule: no threshold may see fault data, ever.** |
| L2 | "q0.01 calibration" was min-calibration on an 8-valued discrete fitness (G2) | Tiny alphabets quantize alignment fitness | Stated honestly; min-robust counts reported alongside. **Rule: report the achievable FPR ladder, not the nominal quantile.** Recurred on SFPU (caught by audit) — now automatic in the harness. |
| L3 | FPR denominator recycled calibration days (G3) | Convenience | Calibration days never counted as negatives. **Rule: every negative must be sample-independent of calibration.** |
| L4 | Model channel's 18 "unique" days ≈ its noise rate (G4) | No per-channel noise floor | Binomial significance vs each channel's own holdout rate, p<1e-3, built into the harness. **Rule: "detected" = significantly above noise, per channel — the rules channel included** (it was silently exempt until the 3b audit; rule-of-three floor closed it). |
| L5 | Pooled F1 over 4,540 correlated days (G5) | Convention-following | Per-scenario detected/TTD/alarm-fraction; log-hash duplicate detection. **Rule: the scenario, not the day, is the unit of evidence.** |
| L6 | Zero-event days silently vanished (G7) | Day universe derived from the event log | Universe from raw data; silence on a scheduled day IS a flag. Refined again in 3b when the model's unoccupied-day catches turned out to be real (off-hours operation). **Rule: absence of data is a value, not a gap.** |
| L7 | Gates failed open on unmapped sensors (G8) | Optional-gate convenience | Fail closed, tested. **Rule: a rule missing its gate is skipped loudly, never run ungated.** |
| L8 | Position-based leak rules structurally deaf on FPU | LBNL's leak passes water through a CLOSED valve; position reads closed honestly | Waterside flow rule (0.2 GPM from healthy max 0.10). **Rule: every rule needs a positive control — silence ≠ competence.** This alone saved Phase 3c's leak-family numbers. |
| L9 | Week-0 ground truth was vacuous as stored (3a audit F-1) | Binary diff below solver noise; Zone-S read post-hoc via argmax | v2 method: normalized zone-own-column divergence, 2× margin, INDETERMINATE allowed. **Rule: ground truth must be pre-registered method + stored artifact, never a reading.** |
| L10 | One raw CSV date-rotated at source (F-2) | Dataset packaging; no monotonicity gate | Sort-on-convert + calendar-identity gate (62/62 pass). Rotated file's scenario excluded from family claims. **Rule: never trust file order; verify the calendar.** |
| L11 | "Perfect healthy silence" presented as calibration evidence (F-3) | One-sided tuning can only loosen | Noise-floor × stated-margin policy (flow threshold 150→50 CFM; VAVDMPRStuck-20 detection 132→177/262 days at zero cost). **Rule: report the margin factor; justify anything >5×.** |
| L12 | SYS_CTL semantics patchwork (F-5) | Three-state occupancy vs binary assumptions | occ_above knob; day universe counts any scheduled operation; night-cycle (16.8% of year, ALL weekends) no longer dropped. |
| L13 | SFPU residual band 0.22 °F wide; "detections" exceeded it by 0.02 °F (3b audit) | Extreme-calibration on an ultra-stable simulated year | Sensor-precision band floor (0.5 °F); 21–117-day counts retracted to ≤2. **Rule: no detection below sensor physics.** The rev-1 "residual topology contrast" was band geometry — dropped. |
| L14 | Localization 38/38 unfalsifiable as discrimination | Ground truth has zero variance (all faults in Zone S) | Reframed as specificity (non-S zones ≤1/365 days across 61 files). **Rule: check the ground truth's variance before claiming discrimination.** |
| L15 | Artifacts lagged the code (3b) | Post-hoc analysis not folded back | All benchmarks regenerated after every harness change. **Rule: the stored artifact must reproduce every published number.** |

### Phase-4 additions to the ledger (L16–L21)

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L16 | Any-of-N day-level significance died under noise-floor uncertainty | Union tests amplify estimation error | Per-instance tests (the stratum's own logic), Bonferroni, 2× margin. **Rule: test at the granularity the channel claims.** |
| L17 | Q1 "McNemar" awarded stars to noise (c=0 by construction) | Impossible null | Channel-noise-null binomial. **Rule: the null is always the channel's own measured noise, never a convention.** |
| L18 | Baseline detected file provenance, not faults (erratum columns) | Forgot our own gap ledger when building new code | Erratum columns dropped; cross-file consistency gate. **Rule: consult the erratum ledger before ANY new consumer of the data.** |
| L19 | Precision floor padded band WIDTH; detections rode sub-precision MARGINS | Floor bound the wrong quantity | Exceedance-margin floor. **Rule: floors bind the decision quantity, not a proxy.** |
| L20 | Oscillation counted temperature reversals at quantization scale | One deadband for all signal classes | Per-signal-class deadbands (≥ sensor precision for temps). **Rule: L13 applies to every derived statistic, not just residuals.** |
| L21 | Instrument iterated toward a known fault signature (P1 rate channel), then failed its own gate | Prediction-shaped instrument + ad hoc significance constants | Non-overlapping windows, ONE margin policy, mechanism re-attributed honestly. **Rule: an instrument shaped by fault-side knowledge tests engineering, not prediction — label it.** |

### Phase-4 discoveries for Part I

- **D6. The invariant-location claim, triple-tested:** MR2 = freq channel
  exactly (141=141) on RMTEMPUnstable → discovery-automation; MR1 fires 124
  healthy days on PFPU where the rhythm doesn't exist → the models tell you
  WHERE invariants hold; oscillation (calibrated classical rule) stands
  alone on VAVDMPRUnstable (349 vs 0) → some faults need the classical
  instrument, calibrated. One experiment, three verdicts, one coherent story.
- **D7. Dataset erratum #4:** SDAHU healthy file's SA_SP/SA_SPSPT differ in
  units/roles from all fault files — any ML baseline fed those columns
  scores file identity. Found by auditing OUR OWN baseline.

### Phase-5 additions (L22, D8-D9)

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L22 | L6 and the L16 pattern BOTH recurred in Phase 5 (event-log day universe; point-estimate cold-start gate) | Rules documented but not mechanized | Raw-calendar universes via a shared helper; CP-upper gating standard. **Rule: a lesson isn't closed until a helper/test ENFORCES it — documentation alone decays.** |

- **D8. The reversal probe:** reversing every trace and re-scoring certifies
  in one number whether a discovered net encodes order at all. Our three
  models split cleanly (SDAHU 0.886→0.553; FPU nets identical to 3-4
  decimals). Cheap, decisive, reusable — and it converted a mushy causal
  claim ("alphabet complexity") into demonstrated facts.
- **D9. The grammar geometry:** no symmetric clades — a tight FPU family
  (1-3% cross-violations, 0.58 profile distance) with SDAHU as a
  low-activity dialect NESTED in PFPU's count space (the 1.00 rejection was
  alphabet-presence artifact; shared-alphabet control collapsed it to
  0.00), behaviourally separated in 3 of 4 directional cells. The
  cross-system order finding: FPU logs beat their shuffles on the SDAHU
  net (+0.15/+0.18, 99% of days) — the shared start/stop grammar, above a
  configuration-model null. H-CS failed its pre-registered falsifier
  (CP-gated 0-1 detections per rotation): portability stays config-only.

### Phase-6 additions (L23-L25)

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L23 | No artifact measured the OR of all channels on healthy data; naive union false-alarmed 15.6% of SDAHU holdout days while the docs implied 0 | Each channel calibrated alone; nobody owned the composite | `union_fpr.py` + regression guards; rate channel demoted to diagnostic-only (verified zero scorecard/TTD cost). **Rule: per-channel FP floors do not compose — the union is a first-class, tested artifact.** |
| L24 | Model/device "holdout FP" rows are the calibration target (~fpr_quantile) by construction — their thresholds are quantile-fit ON the holdout days being reported | One day-set doing two jobs (set threshold AND certify it) | Provenance labels in artifact + table; caveat sentence standard. **Rule: the same data cannot both set a threshold and certify it; label calibration-target rows or three-way split (discover/calibrate/test — toolkit facade, Phase 9).** |
| L25 | First demotion-verification check accepted coverage from insignificant channels/devices — weaker than the property it claimed to verify (property held anyway, proven by the audit's strict recheck) | Guard written to pass the current data, not to enforce the stated property | Significance-gated, device-pessimistic check shipped; absence-dependence flags for manual review. **Rule: a guard must enforce the property at the strictness the CLAIM states — guards are part of the result.** |

## Part III — Why these gaps kept appearing (the honest meta-analysis)

1. **Simulation flatters.** Noise-free EnergyPlus years make 0-FP thresholds
   cheap, bands razor-thin, and silence easy. Half our gaps (L2, L11, L13) are
   the same lesson: a number earned on simulation must carry its sensor-physics
   and noise-floor caveats or it will not survive hardware.
2. **Every channel we add re-creates G4.** Rules, model, residual — each new
   channel needed its own noise-floor gate, and each time the temptation was to
   exempt it. The harness now enforces it structurally.
3. **Datasets lie in specific, recurring ways.** Duplicated files (SDAHU),
   mislabeled faults (oa_bias), rotated calendars (SFPU), controller-side
   injection conventions. The week-0 gate battery (MD5, monotonicity, calendar
   identity, TTL coverage, log-hash) is the reusable answer — and a paper
   contribution in itself.
4. **Positive results attract inflated framing within hours.** Rev-1 of Phase 3b
   was written the same day as the discovery and contained six overclaims. The
   two-agent audit + recompute-from-raw discipline caught all six the same day.
   The falsifiers only work if you run them BEFORE the claim ships.

## Part IV — Standing verification protocol (what "checked" means here)

1. Prove the signal in raw data before writing any rule (measured distributions).
2. Calibrate on train only; validate on holdout; state what negatives exist.
3. Positive control for every detector (silence ≠ deaf).
4. Per-channel noise-floor significance for every "detected."
5. Regression: SDAHU must reproduce bit-identically after every change.
6. Pre-registered falsifiers; a fired falsifier is a finding, reported.
7. Hostile audit (agents + recomputation) before any phase transition.
8. Artifacts regenerated so every published number is reproducible from disk.

## Part V — Paper assets as of tonight

- **Numbers:** SDAHU 14/14; PFPU 17/30; SFPU 18/30 meaningful; TTD 1–2 days;
  0 healthy signature days on all three systems; zone specificity ≤1/365;
  SFPU unit-model 22–26 robust days/scenario with 15–17 unique.
- **Contributions list (running):** measured circularity; alphabet split;
  window-decomposition evaluation; week-0 dataset-audit battery (+ two dataset
  errata: oa_bias, rotated file); config-only onboarding evidence; stratum
  routing; discovery-automation finding with honored falsifier; specificity-
  grade localization; noise-floor significance harness.
- **Must-cite ledger:** Schein & Bushby 2006 / House 2001 / NISTIR 7365 (APAR
  lineage + trial-and-error foil); Frank et al. 2019 (day-slice metrics);
  Leemans EMSC (stochastic line); Chahine & Noura 2026 (ML bias bar on SDAHU);
  Vitale/JMS 2025 (CPS mirror image); Qin ICCPS 2025; Titus/Nailor/RP-1292
  (topology); Lin et al. 2022 (cost anchors); Wu & Keogh / Kim et al.
  (evaluation rigor); Sensor2EventLog/IoT Miner (eventization context).
- **Deadline:** ICPM 2027 — abstract Sept 4, paper Sept 11, 2026.
- **Open experiments (pre-registered):** device stratum falsifiers (3c);
  PFPU frequency-channel prediction (Phase 4); matched-rule ablation arm
  (Phase 4); fouling waterside-ΔT channel; zone-temp comfort residual;
  cross-replay grammar with null model (Phase 5).

### Part V addendum — 2026-08-18 (the numbers above are FROZEN AT AUG 10; quote THESE)

Everything below recomputed from committed artifacts (see REPRODUCING.md §7
for the claim→artifact map). The Aug-10 list predates Phases 3c–6.

- **Scorecards (v12):** SDAHU **14/14**, PFPU **23/30**, SFPU **24/29**
  (SFPU excludes the rotated-calendar file, ERRATA.md E4). NOT 17/30, 18/30.
- **TTD:** **median 1 day**, with an honest tail — SDAHU {1×9, 2×5}; PFPU
  {1×19, 4, 11, 15, 21}; SFPU {1×19, 3, 15, 15, 37, 108}. Never write
  "TTD 1–2 days" without "median".
- **Joint FPR (Phase 6):** naive all-8 union 15.6/12.5/4.2% of healthy
  holdout days; deployed STRATA detector (rate diagnostic-only)
  **1.0/5.2/4.2%**, demotion verified zero-cost. Cry-wolf < 0.1% all
  systems (`outputs/crywolf.json`). Model/device rows are calibration
  targets, not out-of-sample (L24).
- **Week-0 zone ground truth:** **50** Zone-S + **10** INDETERMINATE (the
  artifact; earlier "51/9" was a transcription slip).
- **Matched rules:** MR2 = freq EXACTLY on both FPU systems (SFPU 141=141
  AND PFPU 206=206); MR1 fires 231 healthy SDAHU days and 124 PFPU days
  (both numbers, not just PFPU's).
- **PCA-strict head-to-head (comparable universes):** a dead heat —
  **61 = 61** (14v13, 23v23, 24v25) with complementary misses; STRATA-only:
  oa_bias+4, VAVDMPRUnstable, waterside-fouling-severe; PCA-only:
  RMTEMP+2C ×2, airside-fouling-moderate (via the unmapped zone-fan DP
  sensor — `outputs/sensor_coverage.json`).
- **Bias windows (v12):** window-conditional recall is measured **100%**
  (164/164, 164/164, 139/139, 137/137, 148/148); windows 137–164 days/yr.
- **Residual denominators:** benchmark's `residual_holdout_fp` n
  (36/124/121) counts channel-day pairs across residual channels;
  union_fpr's exposure (36/41/41) counts distinct days. Label whichever is
  used.
- **Model channel (SDAHU):** 23 unique model days in v12 (≈ noise, same
  conclusion as v5's "18" — silence-semantics change in F2).
- **Onboarding counts (corrected):** at onboarding commit aa92970 PFPU had
  **45 sensor mappings + 35 rules** (the log's "48" was a miscount);
  today's configs: 57 mappings + 39 rules (Phase-4 waterside ΔT +
  oscillation additions).
- **Errata:** canonical numbering and evidence now in **ERRATA.md** (E1–E4)
  + `week0_audit.json` gate 5. G5's "five event-log-identical scenarios"
  was true under the v1 alphabet only; under the current alphabet all 14
  SDAHU logs are distinct (`event_identical_groups: {}` in v12) — the
  BYTE-level duplicates (E1, E2) are unchanged.
