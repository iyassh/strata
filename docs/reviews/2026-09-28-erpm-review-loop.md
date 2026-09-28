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
