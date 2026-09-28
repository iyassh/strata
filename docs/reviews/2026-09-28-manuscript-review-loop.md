# Manuscript review-rate-fix loop — paper/paper-v2.tex (long manuscript)

Reviewer: manuscript-loop agent. Facts as of 2026-09-28 (X33–X38 closed; X38 Amendment 1 re-audit applied at b69d870).
Framing rule applied throughout: every section leads with what the framework achieves, limitations follow in their own sentences; no number changed, no fired falsifier softened, errata and audit trail intact. Author's settled sentence: "process mining helps to get detection but it is not detecting on its own."

## Round 1 — 2026-09-28 04:13–04:58 PDT (commit 3a19b6b)

### Ratings (clarity / correctness / achievement-first → section score, 1–10)

| Section | Before | Notes |
|---|---|---|
| Abstract | 6 | Second sentence led with the refutation; no X38 or subsystem attribution; five-system totals absent |
| Introduction | 6.5 | Contributions ordered protocol → negative result → detector; "not that it succeeded" |
| Aims and objectives | 8 | Objective 2 status phrased as refutation first; "thirty" experiments and "ten adverse results" stale |
| Related work | 8 | No forward reference from the rule-library limitation to the X38 measurement |
| Method | 7.5 | No statement of what the stratified structure does; figure caption "without detecting or predicting anything" |
| Verification | 7 | "Three of the six errata" (there are eight); "thirty-two numbered lessons" (RESEARCH_LOG carries 67); "ten results" without the four later falsifiers |
| Results | 7 | No headline lead; attribution paragraph led with the specificity caveat; portability paragraph's committed-config counts stale (56/39 → 109/58); coverage disclosure not bounded by X35/X36 |
| Refuted or withdrawn | 7.5 | Sound; no lead sentence tying it to what stands |
| Errata | 7.5 | Table caption said "Six", table lists E1–E8 |
| Limitations | 6.5 | Led with "simulation flatters"; "comparison against deployed rule-based practice is incomplete" is stale after X38 |
| Comparison against commercial practice | 6.5 | Title carried "the falsifier fired"; result stated last; five of six adapter defects listed |
| Conclusion | 6 | Led with the protocol; "three public benchmark systems" stale; ten-result count without X34/X36–X38 |
| Appendix ledger | 8.5 | Complete through X38 |
| **Overall** | **7** | |

### Numbers spot-checked against committed artefacts (all agree)
union_fpr_* deployed 1/8/9/3/5 of 96 and naive 15/15/9/8/21; component_attribution 109/22/20/7 (exact 0.69, exact-or-subsystem 0.829, wrong 0.127); x37_diagnosis 85/114 resolved, 44 unresolved, 112 exact, 16 wrong (0.101); x35 worst cell PFPU schedule 7/96, losses SDAHU oa_bias (COV), PFPU airside moderate (noise/COV/combined), DDAHU cooling waterside moderate (combined), no falsifier; x36 ΔFP 0/+4/+4/+3/+2, no gain, no loss, all five edge recoveries kept, F-X36.a; x38 run 2 G3 12/14 @1, 8/30 @0, 9/29 @0, G2' 12/15/17, F-X38.a under G2/G3/S; alarm_attribution 37/13/0 (+14 no stratum, 1 indeterminate) of 65; crywolf 0.0003/0.0011/0.0012; intervals 64 vs 61 of 73, McNemar p = 0.25, three STRATA-only; e3_leakage 365/365 and 0/7150 on both columns; x26 3/49 deployed; TTD SDAHU {1×9, 2×5} naive, PFPU 26×1, SFPU 25×1; x33 ledgers 14→14, 22→26, 21→25, 45→50, 40→43; configs/lbnl_pfpu rules.yaml events 58 (13 state + 45 signature), sensors 109 recorded columns mapped.

### Gaps found → fixes made (all in paper/paper-v2.tex)
1. Abstract rewritten to lead with the framework and five-system totals (158/175, 26/480, zone 37/50 never wrong, subsystem 83 %, X35 worst 7/96, X26 3/49), then the process-mining division of labour in the author's sentence, then the refutations as results, then PCA and X38 comparisons, then errata. No number changed.
2. Introduction: paragraph five now states the stratified structure and the division of labour before the refutation; contributions reordered framework → process-mining answer → protocol → errata; "not that it succeeded" replaced by a statement of what the application contributes.
3. Objective 2 status and Objective 5 counts updated ("more than thirty" experiments; ten adverse results plus four later fired falsifiers).
4. Related work: forward reference from the rule-library limitation to the X38 measurement.
5. Method: new paragraph stating what the stratification does and that conformance is one channel of eight; figure caption reworded (models supply strata and invariants, no detection of their own through conformance).
6. Verification: eight errata (E1, E2 and E6 by the integrity hash); sixty-seven lessons; sentence adding the four later falsifiers (X34, X37, X36, X38) with cross-references.
7. Results: headline lead paragraph; attribution paragraph leads with 37/50 never wrong and the 83 %/85 % subsystem rates, then the missed bars; X37's gains stated before its two fired falsifiers; portability paragraph's committed-config counts corrected to 109 mappings and 58 rules; coverage disclosure bounded by X36 (all five edge recoveries survive narrower bands) and X35 (four of five survive field conditions).
8. Refuted section: one lead sentence tying it to what stands.
9. Errata table caption: "Eight".
10. Limitations: lead paragraph with the X35/X36 robustness result; "comparison … incomplete" replaced by the three-system, one-library scope with a cross-reference.
11. Baseline subsection: title shortened; result paragraph moved to the head (like-for-like counts, within one on the air handler, three times on the terminal units, falsifier fired, claim withdrawn); sixth adapter defect (FC6 on a non-cfm column) added; G2 floor lesson stated; no caveat removed.
12. Conclusion rewritten in three paragraphs: what the framework achieves (five-system totals, budget, localisation, X38 position), the process-mining answer in the author's sentence, then the protocol with the four later falsifiers counted.

### Left for Round 2
- Two pre-existing overfull table rows: tab:results cry-wolf multicolumn (80 pt) and tab:refuted row 10 (100 pt, an unbreakable \texttt key).
- Re-read every edited passage in the compiled PDF for flow.
- Check the Objective 4 "Done, against the claim" wording against the new baseline lead.

Compile: tectonic in scratchpad ms-loop, exit 0, 43 pages, no undefined references or citations (four "undefined" log hits are TU/ptm font-shape warnings from the times package). PDF copied to paper/paper-v2.pdf and ~/Downloads/Ureap/docs/writing/paper-v2.pdf.

## Round 2 — 2026-09-28 04:58–05:01 PDT (commit 05f403d)

### Ratings after Round 1 fixes (re-read of the whole manuscript)

| Section | Round 1 → Round 2 | Notes |
|---|---|---|
| Abstract | 6 → 8.5 | Leads with the framework; all five-system numbers verified |
| Introduction | 6.5 → 8 | Oscillation channel was listed among log readers (it reads raw signals, Table 1); fixed |
| Aims and objectives | 8 → 8.5 | Consistent with the new baseline lead |
| Related work | 8 → 8.5 | |
| Method | 7.5 → 8.5 | Same oscillation slip in the new paragraph; fixed |
| Verification | 7 → 8.5 | "most recently … invalid for three reasons" now covers both voided X38 executions |
| Results | 7 → 8.5 | Lead sentence tightened; cry-wolf row no longer overflows the margin; alarm-figure caption said family mapping "is future work" although X37 has run; fixed |
| Refuted or withdrawn | 7.5 → 8 | Row 8 quoted "24 fouling misses" (pre-coverage); the committed scorecards leave 17 (4/4/5/4), fixed; row 10's unbreakable JSON key overflowed 100 pt, fixed |
| Errata | 7.5 → 8.5 | "The last of them" no longer true (E5 of eight); three overflowing file names given break points |
| Limitations | 6.5 → 8 | Giant paragraph split at the X35 sentence; X35 footnote moved to its sentence; "no systematic scoring of alarm text" updated for X34/X37 |
| Comparison against commercial practice | 6.5 → 8.5 | Reads achievement first, caveats intact |
| Conclusion | 6 → 8.5 | |
| Appendix ledger | 8.5 → 8.5 | |
| **Overall** | **7 → 8.3** | |

### Numbers spot-checked this round (all agree)
x22 reversal arm: FCU 55 of 72 flagged, AUC 0.989, oracle hit 0.75; DDAHU 59 of 83, AUC 0.992, 0.71; SDAHU 0 flagged, AUC 0.908; PFPU AUC 0.49. Per-channel holdout false alarms union_fpr_*: SFPU model 5 + device 1, PFPU model 4, FCU model 1 (ablation sentence consistent). Remaining misses under the final gate from benchmark_v6_*: PFPU 4, SFPU 4, DDAHU 5, FCU 4, SDAHU 0 = 17, all coil fouling. X35 per-condition detected/FP/lost per system match the Limitations sentence (SDAHU 13 @0 COV lost oa_bias; PFPU 25 @6/6/5 lost airside moderate under noise/COV/combined, 26 @7 schedule; DDAHU 49 @2 combined lost cooling waterside moderate). Grammar reversal probe 0.8861/0.5526, 0.9533, 0.9021/0.9026 in x22 unperturbed means and grammar_results.

### Gaps found → fixes made
1. Oscillation channel described as a log reader in the Introduction and the new Method paragraph; corrected to raw-signal reader (matches Table 1).
2. Results lead: "The subsections that follow" → "What follows" (the lead precedes unsectioned paragraphs).
3. tab:results: cry-wolf multicolumn cell (80 pt overfull) replaced by three per-system cells; the day counts moved to the caption.
4. tab:refuted row 8: "24 fouling misses" → "17 fouling misses that remain … after the coverage audit".
5. tab:refuted row 10: \allowbreak in the JSON key (100 pt overfull removed).
6. Limitations: paragraph split before the X35 sentence; X35 footnote attached to its own sentence; X36 sentence now states what the edge recoveries are not (artefacts of the exact extreme); "no systematic scoring of alarm text" replaced by what X34/X37 scored and what remains unscored.
7. Alarm figure caption: "future work" → the X37 layer's result and status.
8. Errata: "The last of them" → "One of them … (E5)".
9. Adversarial audit: the X38 sentence now covers both voided executions (three reasons; six adapter defects and one design defect).
10. Errata table: \allowbreak in three file names (35–72 pt overfulls removed).
11. Traceability comment: X34, X35, X37 lines added.

Compile: exit 0, 43 pages, no undefined references or citations, no overfull box above 10 pt. PDF copied to both destinations.

### Left for Round 3
- Full re-read for flow with fresh eyes; check every cross-reference target still says what the referring sentence claims.
- Confirm the ledger appendix rows X34–X38 against the section text (bars and outcomes).

## Round 3 — 2026-09-28 05:01–05:03 PDT (commit 032938b)

### Ratings after Round 2 fixes

| Section | Round 2 → Round 3 | Notes |
|---|---|---|
| Abstract | 8.5 → 9 | Rendered text read; nothing to change |
| Introduction | 8 → 8.5 | |
| Aims and objectives | 8.5 → 8.5 | Objective 3's "statistical repair, Section protocol" pointed at a section that does not describe the repair; redirected to the Limitations disclosure where it is described |
| Related work | 8.5 → 8.5 | |
| Method | 8.5 → 8.5 | Same misdirected reference in the noise-gate paragraph; fixed |
| Verification | 8.5 → 8.5 | A self-reference ("the per-day repair of Section protocol" inside that section) redirected |
| Results | 8.5 → 9 | Two misdirected references to the split/repair fixed; the opening sentence now says where the two rooftop units are reported |
| Refuted or withdrawn | 8 → 8.5 | Ledger rows X34–X38 checked against the section text: consistent |
| Errata | 8.5 → 8.5 | |
| Limitations | 8 → 8.5 | "as the paragraph below records" → paragraphs; jitter cross-reference pointed to the wrong section, now "described below" |
| Comparison against commercial practice | 8.5 → 9 | Refutation condition was stated twice after the Round 1 reorder; second statement removed |
| Conclusion | 8.5 → 9 | "the division of labour the title names" → "the introduction states" (the title names the framework, not the division) |
| Appendix ledger | 8.5 → 9 | |
| **Overall** | **8.3 → 8.7** | |

### Checks this round
- Every \ref has a \label and every \cite a bibliography entry (scripted check; none missing).
- Paragraph-opening scan for negative-leading sentences: the remaining ones open descriptive paragraphs (related work, protocol mechanics, the refuted-test narrative) and are not results framing.
- Rendered abstract, baseline subsection and conclusion read in the PDF text for flow.

### Gaps found → fixes made
1. Five cross-references to "the statistical repair / three-way split of Section protocol" now point to the Limitations disclosure paragraph (and Figure 5) where the repair is described; one pointed from inside the protocol section to itself.
2. Limitations: "as the paragraph below records" → "paragraphs"; jitter reference reworded.
3. Results opening: rooftop units' sections named.
4. Conclusion: "the title names" → "the introduction states".
5. Baseline subsection: duplicate statement of the refutation condition removed.

Compile: exit 0, 43 pages, no undefined references, no overfull box above 10 pt. PDF copied to both destinations.

## Round 4 — 2026-09-28 05:03–05:04 PDT (commit c92e8c6)

### Ratings after Round 3 fixes

| Section | Round 3 → Round 4 |
|---|---|
| Abstract 9 → 9 · Introduction 8.5 → 8.5 · Aims 8.5 → 8.5 · Related work 8.5 → 8.5 · Method 8.5 → 8.5 · Verification 8.5 → 8.5 · Results 9 → 9 · Refuted 8.5 → 8.5 · Errata 8.5 → 8.5 · Limitations 8.5 → 8.5 · Baseline 9 → 9 · Conclusion 9 → 9 · Ledger 9 → 9 | **Overall 8.7 → 8.8** |

### Numbers spot-checked this round (all agree)
matched_rules_*: SFPU mr2 141 = frequency 141; PFPU mr2 206 = frequency 206; MR1 healthy firings 231 / 124 / 0; SFPU oscillation-only instability scenario. x11_branch F-X11.d disclosure present. x12 worst holdout rate 0.0521 (five of 96). x27 static biases 6 of 8, deployed FP 3 → 3, F-X27.b. x28 F-X28.b. x30 F-X30.b with the two HM-align cells named. x24 and x22 no falsifier. Union artefacts' per-channel day lists: deployed false-alarm days without the two conformance channels are SFPU 9 → 4, PFPU 8 → 6, FCU 5 → 4 (one model-only day on the fan coil unit).

### Gaps found → fixes made
1. The abstract says removing the conformance channels lowers three systems' false-alarm rates; the results ablation paragraph named only two. The fan coil unit (5/96 → 4/96) added, with the recomputation stated.

Nothing else found on the rendered Results opening, Limitations opening and attribution paragraph. Compile: exit 0, 43 pages, clean log. PDF copied to both destinations.

## Round 5 — 2026-09-28 05:04–05:08 PDT

### Ratings after Round 4 fixes
Unchanged from Round 4 on every section; **overall 8.8**.

### Numbers spot-checked this round (all agree)
Circularity bound (benchmark_v2_processheal_v1 vs benchmark_v3): rules tp 3,134 on 4,540 fault days in both; structure tp 238 (5.24 %) vs 81 (1.78 %); 5 false positives in both; combined recall 0.6943 = 3,152 tp. x7_downsample: F-X7.a on three systems (28, 64, 64 signature days) and F-X7.b on the PFPU fan-restriction residual. x8_contamination: no falsifier. e8_bias_magnitude: box statics shift +0.20 and +0.40 in.wg against 0.0 on the deck column; the +2 °C file shifts 3.6 °F, exactly its label. e7_zone_label: documentation names _W, artefact covers PFPU and SFPU.

### Checks
- British spelling scan over the prose: no American forms introduced ("claim-to-artifact table" is the repository's own name and predates the loop).
- No stray double spaces or broken dashes outside the verbatim alarm listing.
- Rendered Verification lead paragraph reads correctly with the four later falsifiers sentence.

### Gaps found → fixes made
None in the manuscript. In this review file the Round 1–4 time ranges were estimates and did not match the commit clock; corrected to the commit times above.

## Round 6 — 2026-09-28 05:08–05:12 PDT

### Ratings
Unchanged; **overall 8.8**. Trajectory across the loop: 7 → 8.3 → 8.7 → 8.8 → 8.8 → 8.8.

### Numbers spot-checked this round (all agree)
Table 3 rooftop rows: benchmark_v6_rtu_sim 20 of 24 scored, union_fpr_rtu_sim 0 of 28 held-out days over 100; rtu_field one case, 3 of 49 over 182. Table 3 rule columns against configs/*/rules.yaml: SDAHU 3 state / 12 signature-side, PFPU 13 / 45, SFPU 13 / 49, DDAHU 15 / 56, FCU 7 / 19, RTU-sim 3 / 5, RTU-field 2 / 7; PFPU and SFPU sensors.yaml carry 109 recorded columns mapped with coverage_audited true and unmapped 0.

### Gaps found
None. Two consecutive rounds (5 and 6) found no gap worth fixing; the loop stops here.

### Not verified in this loop
- E7's "57 of 60 files; three indeterminate" split was not recomputed (the artefact records the documentation claim and the two systems; the per-file split lives in ERRATA.md).
- The onboarding wall-clock figure (about 1.5 hours, reconstructed from commit timestamps) and the 45-mapping / 35-rule onboarding counts were not re-derived from git history.
- Figures were not regenerated; captions were read against the artefacts, not against the PDFs of the figures.
