# ERPM paper review-rate-fix loop (paper/erpm/erpm.tex)

Hard limit 12 pages (LNCS llncs, bibliography ../references.bib). Framing
rule from the author: lead with what STRATA achieves and what process mining
contributes; state the limitation as a limitation ("process mining helps to
get detection but it is not detecting on its own"); no number changes, no
fired falsifier removed or softened, negative results stay reported.

## Round 1 — 2026-09-28 05:10 PDT

### Numbers spot-checked against committed artefacts (python3 reads)

| claim in paper | artefact | result |
|---|---|---|
| canonical alphabet 10 activities; SDAHU 6, FPUs 10 | grammar_results.json `canonical_alphabet`, `alphabets_cfg` | ✓ |
| reversal probe 0.8861/0.5526, 0.9021/0.9026, 0.9533/0.9533 | grammar_results.json `reversal_probe` | ✓ |
| cooling-active healthy band 4–44 on SFPU | grammar_results.json `bands.sfpu` | ✓ |
| circularity 81 vs 238 TP over 4,540; rules 3,134; combined 3,152 / 5 FP; threshold 0.333, 248/87 | benchmark_v3.json, benchmark_v2_processheal_v1.json `summary` | ✓ |
| 86 of 4,891 evaluable fault days, 1.76 % | benchmark_v6_sdahu.json | ✓ but the field is `model_days_minrobust` (sum 86), not `model_days` (sum 0) — footnote corrected |
| ablation: 14/14 (0 cred), 26/30 (0), 25/29 (7 cred, 0 sole); DDAHU 50/55 (3 cred), FCU 43/47 (6 cred), 0 sole anywhere | benchmark_v6_*.json `meaningful_channels` | ✓ |
| series unit FA 9 → 4 without model/device; parallel 8 → 6 | union_fpr_sfpu/pfpu.json `channels.*.holdout_fp_dates` | ✓ (recomputed from dates) |
| FA per system 1/8/9/3/5 = 26 of 480 | union_fpr_*.json `union_minus_rate` | ✓ |
| matched rule mr1 = 192, model = 178, healthy_fp 0 | matched_rules_sfpu.json | ✓ |
| X22 reversed days flagged 55/72 (FCU), 59/83 (DDAHU), AUC 0.91 (SDAHU) | x22_positive_control.json | ✓ (traces_changed 72 / 81 — paper says 83 for DDAHU; see gaps) |
| X30 worst realised FA 7/72 = 9.7 %, two HM cells not evaluated | x30_method_grid.json | ✓ |
| X17 45/55 @ 3; X19 run 1 47/47 @ 28 (model 25), run 2 41/47 @ 4 | x17_onboarding.json, x19_onboarding*.json | ✓ (paper's "40 of 47" is the post-X25 count per PHASE11/PHASE12) |
| sync_days 0/166/357; supports 0.455/0.978 vs device 0.437/0.014 | discovery_predicts_transfer.json `Q` | ✓ (unit-stratum values; device values from the same artefact) |
| X20 four buildings rho = −1, p = 1/24, falsifiers F-X20.a/b | x20_transfer_four.json | ✓ |
| X35 worst 7/96, ≤ 1 lost per cell, no falsifier | x35_field_conditions.json | ✓ |
| attribution 37 correct / 13 none / 0 wrong / 1 indeterminate | alarm_attribution.json `counts` | ✓ |
| coverage 142 → 158 of 175, model rows identical | x33_coverage_*.json | ✓ |
| X29 ten fouling severities at 0/28 | x29_refrigerant_observability.json | ✓ |
| X12 11 of 73; X14 18 and 21 FA/96; X15 no new detection | x12/x14/x15 artefacts | ✓ |
| median time to detection 1 day over 158 detections | benchmark_v6_*.json `ttd_days` | ✓ (median 1.0) |
| component attribution exact 71 %, subsystem 85 % | PHASE12 X37 (x37_diagnosis.json) | ✓ per PHASE12 table |

### Ratings before → after this round (1–10)

| section | before | after | note |
|---|---|---|---|
| Title + abstract | 4 | 8 | framing inverted per rule; stale "six days in 96 to one" (pre-coverage) replaced by the verified 9 → 4 |
| 1 Introduction | 5 | 8 | leads with what was built and what the log channels carry |
| 2 Related work | 7 | 7 | precision paragraph folded into 4.1 |
| 3 Abstraction / wall / bound | 8 | 8 | footnote field name corrected; 3.4 folded into 3.2 |
| 4 Discovery / reversal / counting | 8 | 8 | unchanged in substance |
| 5 Scorecard / ablation / matched rule / reading | 6 | 8 | new 5.1 with five-system table (158/175 @ 26/480, FA column, credited/sole); "199 scenarios of all five systems" corrected to six systems (five + rooftop unit) |
| 6 Transfer test | 7 | 7 | compressed, nothing removed |
| 7 Tests that pin | 7 | 7 | compressed |
| 8 Limitations | 7 | 8 | X35 kept; coverage-audit fault-informed-selection disclosure added |
| 9 Conclusion | 5 | 8 | author's settled sentence closes the paper |
| **overall** | **6** | **8** | |

### Gaps found

1. Framing (binding rule): title, abstract, introduction and conclusion read
   as a negative-results paper. Fixed: title now "STRATA: What Process Mining
   Contributes to HVAC Fault Detection" with a subtitle naming the measured
   limit; abstract/intro/conclusion lead with the achievements and the log's
   contributions, then state the conformance limitation.
2. Abstract quoted the pre-coverage false-alarm change (six days to one);
   the body and union_fpr_sfpu.json say 9 → 4 on the series unit. Fixed.
3. "below 1.5 % over the 199 scenarios of all five systems": 199 = 175 (five
   systems) + 24 (simulated rooftop unit, X29, P6 none conformance-only).
   Fixed to "six systems".
4. Footnote named `model_days` for the 86-of-4,891 figure; that field sums
   to 0 in benchmark_v6_sdahu.json, `model_days_minrobust` sums to 86. Fixed.
5. The paper nowhere stated the deployed scorecard on the five systems, the
   zone attribution, or which channels the event log carries. Added 5.1 and
   extended Table 2 to five systems with an FA column (all values verified).
6. Oscillation channel described as "bands on reversals"; the code reads
   signal direction changes from the raw frame. Reworded.
7. X38 (Guideline 36 battery): considered; not included this round — the
   paper is at exactly 12 pages with about three lines of slack and X38's
   comparison is rules vs residual coverage, not a process-mining claim.
   Candidate one-sentence insertion for a later round if space is found.
8. X22 DDAHU denominator checked: `n_holdout_days` = 83 (81 traces changed),
   so "59 of 83" is the holdout-day denominator the manuscript also uses. OK.
   Unverified / not mine to fix: the companion-paper bib entry title says
   "Five defects" while the text says eight; the entry lives in the shared
   references.bib, owned by the R2PM agent — flagged to the lead.

### Page budget

Reframing added about 1.5 pages; recovered by prose compression across all
sections and by dropping five citations that carried no claim (Popper
convention, Muñoz-Gama precision, anti-alignments, pm4py, Yuill protocol).
Compiled: 12 pages, no undefined references.

## Round 2 — 2026-09-28 05:16 PDT

### Numbers spot-checked this round

| claim | artefact | result |
|---|---|---|
| Table 1 nets 16/17/11, 15/18/11, 15/17/9; variants 102/343/364; labels in net 6/7/8 | discovery_predicts_transfer.json `Q.*.net`, `variants_tested`, `_aux.net_labels` | ✓ |
| Q supports 0.000 / 0.455 / 0.978 | discovery_predicts_transfer.json `Q_support` | ✓ |
| one series-unit file excluded (73 of 74 scored) | benchmark_v6_sfpu.json `excluded` (SFPU_SensorBias_RMTEMP_-2C) | ✓ |
| eight of twelve then-missed scenarios have an indistinguishable state log | x12_log_diagnosis.json `summary` | ✓ |
| time-infused model: five extra FA days per fan-powered unit | x12_time_perspective.json `holdout_fp_days` 5 / 5 | ✓ |
| X22 DDAHU 59 of 83 | x22_positive_control.json `n_holdout_days` 83 | ✓ |
| X38 G3: 12/14 @ 1, 8/30 @ 0, 9/29 @ 0 vs STRATA 13 @ 1, 26 @ 8, 25 @ 9; F-X38.a fired under G2/G3/S | x38_guideline36.json `systems.*`, `falsifiers_fired` | ✓ |
| "roughly 750 binomial tests" | not in paper-v2.tex at c489460 nor HEAD, nor any PHASE file or the research log | ✗ unverifiable — replaced (see gaps) |
| p_min = 0.05 for two groups of three; 1/3! = 0.167; 1/2! = 0.5; 1/4! = 0.042 | arithmetic | ✓ |

### Ratings (1–10)

| section | round 1 | round 2 | note |
|---|---|---|---|
| Title + abstract | 8 | 8 | absence-channel clause dropped from the abstract for space; the fact stays in 5.1 |
| 1 Introduction | 8 | 8 | |
| 2 Related work | 7 | 7 | protocol paragraph trimmed to the Pitsch sentence |
| 3 Abstraction / wall / bound | 8 | 8 | activity list compacted |
| 4 Discovery / reversal / counting | 8 | 8 | |
| 5 Scorecard / ablation / matched rule / reading | 8 | 9 | X38 comparison with current practice added as one sentence with its fired falsifier |
| 6 Transfer test | 7 | 7 | |
| 7 Tests that pin | 7 | 7 | |
| 8 Limitations | 8 | 8 | unverifiable "750" replaced by what the gate does |
| 9 Conclusion | 8 | 8 | |
| **overall** | **8** | **8** | |

### Gaps found and fixes

1. "The noise-floor gate applies no correction across roughly 750 binomial
   tests" — the 750 has no source in any committed document or the
   manuscript's history. Replaced by "one binomial test per scenario and
   channel, several hundred at α = 10⁻³, with no multiplicity correction",
   which is what the gate does (73 × 7 gated channels = 511 on the three
   systems; 175 × 7 = 1,225 on five).
2. X38 now included (Section 5.1, one sentence, footnote to
   outputs/x38_guideline36.json): within one detection and one false-alarm
   day on the air handler, three times the terminal-unit detections at 8 and
   9 false alarms against 0, the falsifier reported as fired and the
   difference named as coverage. Fits the ERPM argument as "what the
   framework achieves against current practice", not as a process-mining
   claim.
3. Acknowledgement overfull box (12 pt) removed by using a run-in paragraph
   heading; remaining overfull boxes are 0.6 pt and 1.9 pt.
4. Five citations that carried no claim were dropped in round 1 for space
   (Popper, Muñoz-Gama, anti-alignments, pm4py, Yuill); the LBNL 2020 and
   2023 dataset papers, the Bi review and every conformance/abstraction/
   leakage/protocol citation remain.
5. Left as is: the companion-paper bib title ("Five defects") vs the text's
   "eight" — shared references.bib, R2PM agent's.

Compiled: 12 pages (page 12 has 44 lines), no undefined references.

## Round 3 — 2026-09-28 05:22 PDT

### Numbers spot-checked this round

| claim | artefact | result |
|---|---|---|
| matched frequency rule 141 vs 141 (SFPU), 206 vs 206 (PFPU) on RMTEMPUnstable | matched_rules_sfpu/pfpu.json `mr2` = `freq` | ✓ |
| transplanted heating rule fires 231 / 124 / 0 fault-free days | matched_rules_{sdahu,pfpu,sfpu}.json `healthy_fp.mr1` | ✓ |
| jitter arms: detection drop 0, FA ≤ 4/96 | x9_x10_robustness.json `predictions` (det_drop_1x 0 on all three) | ✓ |
| 22–26 min-robust days behind the 135 | PHASE3B_RESULTS.md, RESEARCH_LOG.md L-row | ✓ |
| X38 SDAHU 13 of 14 is the E5-adjudicated count | x38_guideline36.json `strata_detected` 13 | ✓ (now stated beside Table 2's naive 14) |

### Ratings (1–10)

| section | round 2 | round 3 |
|---|---|---|
| Title + abstract | 8 | 8 |
| 1 Introduction | 8 | 8 |
| 2 Related work | 7 | 7 |
| 3 Abstraction / wall / bound | 8 | 8 |
| 4 Discovery / reversal / counting | 8 | 8 |
| 5 Scorecard / ablation / matched rule / reading | 9 | 9 |
| 6 Transfer test | 7 | 7 |
| 7 Tests that pin | 7 | 7 |
| 8 Limitations | 8 | 8 |
| 9 Conclusion | 8 | 8 |
| **overall** | **8** | **8** |

### Gaps found and fixes (all minor)

1. Section 5.1 quoted STRATA's air-handler count as 13 of 14 beside a Table 2
   row of 14; the sentence now says "after the adjudication noted in Table 2".
2. The compacted activity-pair list said "each started and ended", which is
   not the heating/cooling pair's wording; now "each with an entry and an
   exit event".
3. Framing: "entire measurable contribution ... was five false alarms"
   reworded to "their only measurable effect on this detector's output,
   then, is those five false alarms" — same fact, stated as what was
   measured rather than as a verdict.
4. Full read of Sections 1–5 in the compiled PDF: no broken sentence, no
   dangling reference; Sections 6–9 unchanged since the round-1 read apart
   from the compressions, re-read at compile.

Compiled: 12 pages, no undefined references, two overfull boxes under 2 pt.
Nothing substantive left to fix; one more round to confirm.

## Round 4 — 2026-09-28 05:26 PDT (confirmation round)

### Numbers spot-checked this round

| claim | artefact | result |
|---|---|---|
| eight machine-verified benchmark defects | ERRATA.md E1–E8 | ✓ |
| 3.5-point bound = 5.24 − 1.78 | arithmetic (3.46) | ✓ |
| seventeen misses = 175 − 158; sixteen recoveries = 158 − 142 | x33_coverage_*.json | ✓ |
| X31 detection change −1 / −3 / 0, FA worst 3/96 ("within three", "≤ 4") | RESEARCH_LOG.md L56, x31_field_conditions.json | ✓ |

### Ratings (1–10): unchanged from round 3 (overall 8).

### Gaps found

1. Conclusion said the frequency channel "carries detections nothing else
   carries"; the unstable-room-temperature detections are shared with the
   direction-change band. Now "no rule or residual carries", matching the
   abstract and introduction. Wording only.

Nothing else found. Rounds 3 and 4 found nothing substantive; loop closed.

### Title proposal (for the author)

Adopted: "STRATA: What Process Mining Contributes to HVAC Fault Detection",
subtitle "Event abstraction, stratified discovery and count channels on five
public benchmarks, and the measured limit of conformance checking on its
own". Alternative if a shorter subtitle is wanted: "Measured contributions,
and the limit of conformance checking alone".

### Left for others

- references.bib entry `singh2027erratacompanion` is titled "Five defects";
  the text (and ERRATA.md) say eight. Shared file; R2PM agent.
- Author-block TODOs (co-author order, contact e-mail) remain as comments
  in the source.
