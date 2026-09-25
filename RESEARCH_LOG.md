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
  own circularity; ours does, to one decimal. *(E5 insurance note, 2026-08-19:
  both terms are measured across the same branch pair, so any branch component
  is common-mode and cancels in the 3.4pp delta; the v1 signature events are
  position-vs-command rules, which E5's own evidence certifies branch-immune.)*

### D2. The oa_bias relabel, overturned twice
- **Found:** LBNL's four oa_bias files are byte-identical to each other and the
  logged OA_TEMP matches healthy to 2e-5 °F *[correction 2026-08-18: mean |Δ| is 0.02 °F, max 0.33 °F — see ERRATA.md E1; conclusion unchanged]* — so v1 relabeled them "healthy-like."
  Then the blind residual channel "false-alarmed" on 148/303 days of that file —
  which forced a re-examination: with the labeled bias absent from the recorded stream *[was "bit-identical weather" — falsified by gate 5, see ERRATA.md E1/E5: much of the divergence vs healthy is the config-branch offset]*, the building
  BEHAVES differently (MA/SA/RA correlations 0.78–0.84, damper corr 0.91). Verdict:
  it is a real fault run with a CONTROLLER-SIDE OA bias — the fault is applied to
  what the controller reads and never appears in the logged column.
- **Why it happened:** dataset packaging error (one run shipped four times) plus
  a subtle injection convention (bias at the controller input, not the logger).
- **Fix:** relabeled as a fifth SDAHU fault family (detected on ~100% of physics-
  window days by the residual channel) *(X11, Phase 8: those flags are the
  E5 branch offset, not the fault — oa_bias is undetected in the
  adjudicated scorecard; the fault evidence is the cooling-interlock
  shift)*; consequence accepted: SDAHU has NO
  independent healthy negative, stated on every output.
- **Paper value:** (a) a dataset-quality contribution the community needs; (b) the
  published AFGCN paper trained its OA-bias class on this file believing the
  logged column carries the bias — citable, carefully; (c) a case study in why
  "false positives" deserve investigation before dismissal — ours turned out
  to be a real fault file but a BRANCH-PROVENANCE flag: the investigation
  found E5, and X11 removed the detection. The moral survives with the sign
  flipped: false positives deserve investigation — and so do true positives.

### D3. Physics windows, not recall ceilings
- **Found:** sensor-bias recall looked like "38–45%" *[v12: 39–47%]* until decomposed: detection
  windows (coil off + zone occupied, ≥120 min) exist on ~40–45% of days in this
  climate, and the residual rule detects on essentially every window day
  (conditional recall ≈98–100% *[v12: measured 100% — 164/164 ×2, 139/139, 137/137, 148/148]*).
- **Why:** the residual is only physics-bound when no control loop is hiding it;
  summer all-day cooling gives no window. The fault itself changes window
  prevalence (bias alters coil duty) — explaining the −bias > +bias asymmetry.
- **Fix:** report window prevalence × window-conditional recall, never pooled
  recall; TTD as the operational metric (median 1 day; tails in the Part V addendum).
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
- Two new systems onboarded config-only: 48 *[corrected 2026-08-18: 45 at the onboarding commit — see ONBOARDING_LOG]* sensor mappings + ~35 rules each;
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

### Phase-7 additions (L26-L28, erratum E5)

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L26 | Promoting the narrated oa_bias claim into ERRATA.md falsified its strongest wording ("OA_TEMP bit-identical" — actually max 0.33 °F node feedback) while STRENGTHENING the conclusion | Claims copied between docs without recomputation | Gate-5 artifact computes the real stats. **Rule: every claim promoted into a citable document is recomputed on promotion, never copied.** |
| L27 | The Phase-7 staleness sweep itself missed 8 stale locations — one inside the function computing the correction — and left MASTER_PLAN stale about itself | Curated file list instead of exhaustive search | Grep-list of retired numbers ("17/30", "38–45%", "51/60", "bit-identical", "1–2 days"…) over the WHOLE repo, code comments included. **Rule: a staleness sweep is defined by its search list, not its file list.** |
| L28 | **Erratum E5** hid for six phases: the healthy SDAHU file is on a different config branch than every fault file (occupied damper floor 0.0 vs 0.1; different schedules) — healthy-vs-fault divergence partly measures BRANCH, not fault | Every comparison ran against the healthy file; no fault-vs-fault control existed | ERRATA.md E5 + gate-5 config_branch evidence; X11 branch-sensitivity check queued. **Rule: healthy-vs-fault divergence is fault evidence only after a fault-vs-fault control.** |

### Phase-8 additions (L29-L31)

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L29 | X11's FPU battery first fired F-X11.d: SYS_CTL>0 occupancy counted night-cycle (fault-responsive) as branch difference | "Fault-responsive" and "branch-constant" are different axes | Schedule leg conditions on SYS_CTL==1; night-cycle reported separately; post-hoc re-specification DISCLOSED as a resolved pre-registration ambiguity, not a clean pass. **Rule: homogeneity instruments must condition on the scheduled state, or fault behaviour masquerades as branch difference** (third member of the L21/L28 conflation family). |
| L30 | Extreme-value calibration collapses at ONE silent-fault training day (demonstrated: single day -> both negative bias ladders 0/164) | min/max thresholds have breakdown point 1/n | Report with the visibility split: rules-visible contamination announces itself on 100% of days; signature-silent contamination is the dangerous case. **Rule: quote the breakdown AND the detectability split together, or the finding misleads in either direction.** |
| L31 | Configs tuned at 1-min gained 28-64 healthy signature days at 15-min (threshold degeneration when sustained_min <= interval; run merging under aliasing) | A silence-tuned threshold is a claim about that sampling rate's noise process, not about the building | Transfer claim scoped: method transfers via the silence gate re-run at the deployment rate; configs never transplant across rates; freq/osc are fine-sampling instruments. **Rule: re-run the healthy-silence gate at the deployment sampling rate, always.** |

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
  errata: oa_bias, rotated file); config-only onboarding evidence (1-min→1-min; sampling-rate scope per L31); stratum
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
  **X11 ADJUDICATED (Phase 8, `outputs/x11_branch.json`): SDAHU is
  "14/14 naive; 13/14 after branch correction (ERRATA E5)" — quote both
  numbers together. oa_bias's only deployed channel (residual) was branch
  provenance: 0 flags on its 148 evaluable window days under the
  branch-corrected band; all four coi_bias scenarios keep every detection.
  FPU scorecards verified single-branch (homogeneity battery, 0-min
  scheduled-occupancy difference) and unaffected.**
- **TTD:** **median 1 day**, with an honest tail — SDAHU {1×9, 2×5} naive,
  **{1×9, 2×4} adjudicated** (oa_bias's TTD-2 removed by X11; median
  unchanged); PFPU
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
- **PCA-strict head-to-head (comparable universes):** after X11, a
  **60 v 61 near-tie** (13v13, 23v23, 24v25); oa_bias+4 is a **shared
  miss** (both detectors miss it — PCA-strict `pca_sig_strict: false`);
  STRATA-only: VAVDMPRUnstable, waterside-fouling-severe; PCA-only:
  RMTEMP+2C ×2, airside-fouling-moderate (via the unmapped zone-fan DP
  sensor — `outputs/sensor_coverage.json`).
- **Bias windows (v12):** window-conditional recall is measured **100%**
  (164/164, 164/164, 139/139, 137/137, 148/148); windows 137–164 days/yr.
  The oa_bias 148/148 is window-conditional residual RESPONSE, adjudicated
  as branch provenance (X11), not fault detection — quote only the four
  coi_bias columns as recall.
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
- **Errata:** canonical numbering and evidence now in **ERRATA.md** (E1–E5)
  + `week0_audit.json` gate 5. G5's "five event-log-identical scenarios"
  was true under the v1 alphabet only; under the current alphabet all 14
  SDAHU logs are distinct (`event_identical_groups: {}` in v12) — the
  BYTE-level duplicates (E1, E2) are unchanged.

### 2026-09-23 addition (L32) — the SDAHU matched-rule "contrast" was a missing-sensor fact

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L32 | D6/Part V read "MR1 fires 231 healthy SDAHU days" as evidence that the models tell you WHERE invariants hold. SDAHU has no heating rule and no hot-water valve; `heating_active` never occurs in its log, so "occupied AND heating never active" fires on every occupied day for a reason no model predicted or could have. The SDAHU/SFPU contrast was equipment, not discovery. | A transplant test was run across buildings without first checking that the transplanted rule's sensor existed on the target | Retracted as evidence of invariant location (paper + `docs/plans/2026-09-23-discovery-predicts-transfer-prereg.md` Amendment 1). The only non-degenerate contrast is PFPU vs SFPU. **Rule: before a rule is transplanted to test a model, confirm the target has the rule's sensors — a rule that cannot fire for want of a sensor tests nothing.** Found by the sealed computing agent from configs alone, before any data. |

### 2026-09-23 addition (L33) — an erratum's own characterisation was wrong for two weeks after the repo knew better

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L33 | ERRATA E3 said "units and roles swapped". The sealed adapter audit (2026-09-11) showed an additive constant (401.86) applied to a different column in each branch, and a second independent analysis (2026-09-23) confirmed it; the repair plan recorded it, ERRATA did not. The wrong reading survived into a draft paper whose canonical source is ERRATA. | A correction was written where it was found (a plan document) instead of where it is cited (the erratum ledger) | ERRATA E3 rewritten with the retraction dated inside it; `outputs/e3_leakage.json` makes the consequence a measurement. **Rule: a correction to an erratum is made in ERRATA.md first, in the same commit as its discovery, or it does not exist.** Found by the R2PM hostile review. |

### 2026-09-23 night additions (L34, L35) — what the event log does and does not carry

| # | Gap | Root cause | Fix + standing rule |
|---|-----|-----------|---------------------|
| L34 | The conformance null was argued ("order-permissive nets") but never *diagnosed at the log*: nobody had checked whether the missed faults are in the event log at all. Measured tonight (`outputs/x12_log_diagnosis.json`): for 8 of the 12 missed scenarios (all fouling) the state log is indistinguishable from healthy at 5 % in every count and duration; under valve faults it changes in timing and counts, never in activity set or order. | The null was investigated on the model side only | X12 pre-registered and run: the time perspective of the discovered state model is significant on 11/73 (10 under the rule-of-three floor), never on a missed scenario, never earlier, and costs 5 holdout FP days per fan-powered system (PFPU joint 5→10/96). **Rule: before asking whether a method can detect a fault, show the fault is in that method's input.** (PHASE9_RESULTS.md) |
| L35 | A fault-informed residual (ΔT/GPM) chosen from *means* of three fouling files fired its falsifier at day level (1 of 12 significant; the pre-registration miscounted them as 9). | Difference of means is not day-level separability; the ratio explodes at low flow | X13 recorded as a fired falsifier with the fault-informed design disclosed; statistic not adopted. **Rule: a fault-informed statistic must be pre-registered with a day-level falsifier and its design disclosed wherever its result is quoted.** |
| L36 | X12/X13 compared their day flags against scorecard `flag_days` keys that do not exist (`absence`, `frequency`, `oscillation`; the scorecards export `freq`, `osc`, `sig_union`, no absence list). `dict.get(key, [])` returned empty lists silently; "unique days vs deployed" was inflated (120 → 2 on one scenario) and one prediction was never computed. Caught by the hostile review, before anything was adopted. | Silent default on a missing key in a cross-artefact comparison | Both scripts now assert the keys exist. **Rule: a script that reads another artefact's keys asserts they are present; never `.get(k, [])` across artefacts.** |
| L37 | X14 (enriched state alphabet, three recorded amendments): vocabulary was part of the model channel's limit (SDAHU model channel 14 of 14 significant against 0 of 14 deployed; one missed fouling scenario caught through a dose-monotone zone-damper signature, fault-versus-fault controlled in `x14_control.json`), but the enriched channels false-alarm on 18 and 21 of 96 holdout days and alignment-based conformance became computationally impractical on the enriched fan-powered logs (single-laptop console timings, not committed: fit 1,061 s and a scenario not scored in 47 min, before Amendment 3). F-X14.a fired. | Richer vocabulary widens every band's tail; alignment cost grows with net size, not only trace length | Recorded as the ninth adverse result; the vocabulary finding stated beside it. **Rule: an alphabet change is a false-alarm-budget change and a compute-budget change; pre-register both budgets with it.** |
| L38 | X15: the one X14 gain, re-tested through the frequency channel alone under the mirrored holdout (post-hoc-motivated, stated in the pre-registration), held on all four predictions — inside the budget under both splits, the airside-moderate fouling detection survives, 41 vs 12 significant on already-detected scenarios. | Reading a per-channel attribution and then changing the holdout is how a post-hoc read earns a pre-registered result | Candidate deployable addition; adoption is X16, to be pre-registered, and changes every scorecard. (The scorecard vocabulary key for P4's comparator was corrected after the first run's P4 line had been read — recorded as an amendment; the correction made P4 strictly harder.) **Rule: a post-hoc read becomes a claim only after a pre-registered test that changes the data it was read from.** |
| L39 | X9/X10: the deployed detector's counts survive 1× per-sample jitter (14/23/24, FP 1/4/2 of 96) and the mirrored holdout (13/23/25, FP 0/2/3); no falsifier fired. The run took a night because `score()` rebuilt the event-day set per day (O(days × events)) — invisible on clean logs, 16 min per jittered file on one laptop (console timing, not committed). | A per-day comprehension over a set built inside it; nobody had run the pipeline on a log ten times larger | Set built once, results byte-identical (780ec3e). Membership of marginal scenarios shifts under jitter/split while counts hold — reported. **Rule: a robustness test is also a performance test; profile the first slow scenario before waiting on thirty.** |
| L40 | X17: a fourth LBNL system (dual-duct AHU, 114 points, 55 faults) onboarded by configuration alone under a pre-registered protocol: gates clean, healthy silence in one iteration, 45/55 detected at 3/96 false alarms, nothing by conformance alone. One prediction (fouling ≤ 4) was wrong — five detected — and it was the one prediction that carried no falsifier. The union_fpr script's hard assertion that rate demotion is free crashed on what turned out to be its own blind spot: the scorecards export no absence day list, and the day-1 alarm it could not attribute was the absence channel's. | Ten healthy days of cold-fan saturation drove every noisy rule; a physical gate (duct static at setpoint) rather than a looser threshold fixed them | PHASE10_RESULTS.md. **Rules: (1) when a rule is noisy on healthy data, look for the healthy regime behind the noise before touching the threshold; (2) never assert an empirical invariant in a script — record it and exit 2.** |
| L41 | X18: X15's enriched-frequency gain does not replicate on the fourth system — inside the budget, triple the coverage on detected scenarios, none of the ten misses gained. F-X18.b fired. | One scenario on one system was a signature, not a mechanism | The channel stays unadopted. **Rule: a candidate addition earns adoption only by replicating on a system it was not read from.** |
| L42 | X19: a fifth LBNL system (fan coil unit, 29 points, 48 faults) onboarded config-only. Run 1: 47/47 "detected" at 28/96 false alarms — two falsifiers. Every model-channel false alarm was a weekend (25 of the 28; the other three were residual days in January and December): the scoring scripts flag an event-less *scheduled* day as a model violation and define scheduled as `OCCUPIED > 0`, which on this unit includes idle setback; the scorecard's model gate then judged six scenarios against a conformance-only baseline (1/72) while the deployed count included the silence rule (25/96). Pre-registered script fix; four earlier systems byte-identical; run 2: 41/47 at 4/96, no falsifier. | A rule written for the fan-powered units' night cycle (mode 2 generates events) was silently assumed for every mode-2 system; and two artefacts computed the same channel's false-alarm count two ways, which nothing checked because they had always agreed | `tests/test_artefact_consistency.py` pins the two counts equal on every system. **Rule: every semantic constant in a scoring script ("scheduled", "occupied", "silent") is a hypothesis about the equipment class; a new class tests it, and any two artefacts that report one quantity must be asserted equal.** |
| L43 | X20: the sealed transfer test with four scorable buildings passes as pre-registered (rho −1, exact p = 1/24 = 0.042) — and a discovery-free control that was not pre-registered (added after the result), the log's own heating-day fraction, orders the buildings identically and passes identically. The model-derived predictor equals the raw count on three buildings exactly and differs on the fourth only through the miner's noise filter (`heating_inactive` dropped). | MR1 is a heating-absence rule; its firings are the workday complement of the heating-day count that `Q_support` re-describes | Reported as a formal pass that supports nothing about discovery; the tenth adverse result. **Rule: before pre-registering a predictor, write down the discovery-free quantity it is most likely to reduce to and pre-register that as the control; a test whose predictor and outcome are computed from one log needs a cross-log design.** |
| L44 | X21: a net's reading of a foreign building's fault-free year is NOT that year's heating-day count on 6 of 12 pairs (fan-powered nets: exactly the count; DDAHU net: a fraction; FCU net: zero on every foreign log) — F-X21.a fired. The foreign predictor orders the buildings differently from the count and, at n = 4, no better (rho −0.6, p 5/24 vs −1, 1/24: one rank swap, not a measurement). | The asymmetry is in the reading net, not the read log: label overlap does not order the 12 pairs (rho −0.24; the PFPU net shares 3 of 14 FCU activities and syncs 118/118); what in the FCU/DDAHU nets blocks a foreign heating move is not measured | The transfer claim has no support in either direction; reported beside X20 as one finding. **Rule: when a predictor can be shown to reduce to a count, the escape is a cross-instance design — and the first thing to check about that design is what its number measures instead.** |
| L45 | X22 (pre-X25 run; amended by L48's split — under the X25 detector reversal also fires on DDAHU, 59/83): injected order violations into healthy holdout traces and scored them with the deployed conformance channel. Reversal fires on the FCU only (55/72); on SDAHU and DDAHU it cuts fitness sharply (AUC 0.91/0.96) but the healthy holdout's worst days fit worse than a reversed day, so no zero-false-alarm threshold sees it; on the fan-powered units fitness does not move (AUC 0.5). | The channel is three different instruments: order-seeing (FCU), blind by healthy dispersion (SDAHU, DDAHU), blind by net structure (PFPU, SFPU) | The null is now stated per system with its cause. **Rule: a null result needs a positive control run through the same gate, and the control must report a threshold-free separability measure beside the deployed verdict.** |
| L46 | X24: an outdoor-air-fraction residual (G36 FC6 lineage) added as a rule kind with per-rule floors; FCU gains the 20 % damper leak (42/47) at unchanged false alarms; SDAHU/DDAHU unchanged in count, DDAHU stuck-damper files gain residual coverage. | The rule set claimed APAR lineage without the one APAR check that reads the damper's effect rather than its position | Adopted on three systems. **Rule: when a domain reviewer names a standard invariant the rule set lacks, implement it as a pre-registered addition with a regression prediction first.** |
| L47 | X26: the deployed false-alarm budget on the first real building (LBNL field RTU Site 2, 182 measured clean days, no schedule point) is 3 of 49 holdout days (6.1 %), every channel inside budget, after two logged healthy-silence iterations (a mixed-air probe reading below both references; post-compressor evaporator carry-over). The one fault case (40 % undercharge on circuit B) is not seen even with the circuit-2 residuals added by amendment: the recorded circuit-2 pressures and temperatures sit within a few per cent of the healthy June. | Real sensors sit where they sit, and real faults do not always reach the points that were recorded | The limitation "simulation only" becomes a measured number; the case is reported as a case. **Rule: on real data, read the point list against the fault description before writing the config — and when a coverage error is found after a result, record it as an amendment, not a fix.** |
| L48 | X25: conformance thresholds moved to a calibration slice before each month's holdout, and residual/model gates to the rule-of-three floor. Detection counts and scenario statuses unchanged on all five systems; the model channel's out-of-sample false-alarm rows on the fan-powered units rose from 1 to 4 and 5 of 96, taking their deployed budgets from 5.2/4.2 % to 7.3/6.2 %. | The in-sample rows had understated the conformance channels' false alarms by 3–4 days each, exactly as the disclosure said they might | Budget range now 1.0–7.3 %, every row out-of-sample; the caveat is retired. **Rule: a disclosed calibration-target row is a debt; pay it before quoting the number it sits in.** |
| L49 | X27: static ÷ speed² (fan law) on the dual-duct unit catches one more static-sensor bias (6 of 8; F-X27.b fired at a bar of 7) and, unpredicted, the cooling-coil airside-moderate fouling; DDAHU 47/55 at 3/96 under X25 step 2's floor (45/55 and the fouling gain lost under step 4; the static-bias gain survives), nothing lost. The healthy band of the ratio is wider than the per-speed proxy's because zone dampers move the system curve. | A virtual static from speed alone is an airflow-resistance detector; a static bias that the loop absorbs into a small speed change stays inside the band the dampers already widen | The two hot-deck negative biases need a fitted system curve (speed and flow), not a ratio. **Rule: when a physical proxy is written, say what else it measures — this one measures airside resistance, which is why it found a fouling scenario the temperature channels miss.** |
| L50 | X25 steps 3–4: the "rule of three" as first coded (3/365) was looser than the floor it replaced; on pooled channel-days it was 3/509 on one system and 3/124 on another; made per day on each channel's own evaluable holdout days it is 3/41 on the fan-powered units and it removed seven residual-only detections, one offset by X27 (22/30, 21/29, 40/47). F-X25.c fired; reported as a detector change. | A floor is a rate, and a rate has a denominator; three different denominators had been used for the same word | The deployed counts fell and are quoted as they now are. **Rule: state every significance floor as a rate on a named denominator, and check it is stricter than what it replaces on every system before calling it a repair.** |
| L51 | X28: a coil UA = Q/LMTD channel (the field's standard for fouling) gains no fouling scenario on the dual-duct or fan coil unit and adds two false alarms on the fan coil; removed there (F-X28.a), inert on DDAHU; F-X28.b fired. | The dual-duct cooling coil's healthy UA spans a factor of six at partial load (small, noisy LMTD); the fan coil's fouled water-side signals are within 3 % of healthy, and UA is made of them | Fouling on these datasets is a property of the recorded points: temperature band, enriched alphabet, water-side ΔT and UA all fail on the same files. **Rule: when four independent quantities computed from the same recorded points miss the same scenarios, stop adding quantities and test observability with different points (B4).** |
| L52 | X29 (amended, L54): on LBNL's simulated rooftop unit, which records condenser/discharge/suction pressures and line temperatures, the same detector catches all five condenser-fouling and all five evaporator-fouling severities (10–50 %), monotone, plus 8/8 line restrictions, 20/24 in all at 1/29 holdout false alarms; the charge faults below 20 % are the misses. Config only, silence at iteration 1, no falsifier. | Fouling is observable when the fouled component's own physics is recorded; the air-handler and fan-coil misses were the points, not the method | The "property of the recorded points" claim now has its positive control. **Rule: a claim that a miss is the data's fault needs a dataset where the same fault is recorded differently — and the detector must catch it there without changing.** |
| L53 | X30: seven process-mining instruments (inductive miner at noise 0.0/0.5 with alignments, the deployed net with token replay, heuristics miner, log skeleton, Declare, temporal profile), each discovered on the training days and thresholded on the calibration slice, detect none of the 33 scenarios the deployed detector misses on four systems, at any false-alarm level; no cell exceeds 10 % holdout false alarms (worst 7/72); two heuristics-miner cells timed out (F-X30.b, reported as not evaluated). | The conformance null is a property of the log, not of the miner or the measure: what the state-event log does not carry, no conformance instrument over it recovers | Model-side complement of X12's log-side finding. **Rule: a null on one instrument is bounded to that instrument until the grid of instruments has been run under the deployed gate; a cell that times out is reported, never counted as a null.** |
| L54 | X29 Amendment 1 (hostile review of the closed X29): the lone false alarm (1/29) was a model/oscillation flag on a one-row boundary date (2018-10-28 00:00); the converter now drops dates under 720 rows and the regeneration gives 0/28 with identical detections. A per-residual credit artefact shows condenser fouling carried by the condensing-temperature approach (refrigerant side, 91–100/100 days at every severity) but evaporator fouling carried by return − supply air (air side, 100/100), the refrigerant residuals seeing it only from 30 %; the documentation imposes both as airflow reduction. | The refrigerant-side claim holds for the condenser half; the evaporator half is an air-side detection of an airflow fault | A scorecard that records channel families cannot support a claim about which residual fired. **Rule: a claim that names the physics behind a detection needs an artefact at that granularity; and a holdout day is a day only if it holds a day's samples.** |
