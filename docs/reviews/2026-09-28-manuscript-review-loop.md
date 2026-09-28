# Manuscript review-rate-fix loop — paper/paper-v2.tex (long manuscript)

Reviewer: manuscript-loop agent. Facts as of 2026-09-28 (X33–X38 closed; X38 Amendment 1 re-audit applied at b69d870).
Framing rule applied throughout: every section leads with what the framework achieves, limitations follow in their own sentences; no number changed, no fired falsifier softened, errata and audit trail intact. Author's settled sentence: "process mining helps to get detection but it is not detecting on its own."

## Round 1 — 2026-09-28 04:15–05:00 PDT

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
