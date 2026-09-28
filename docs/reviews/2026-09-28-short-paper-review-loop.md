# Short paper review loop — `paper/short/strata-short.tex`

Condensed from `paper/paper-v2.tex` (2026-09-28). Target: 12 pages of body
(title through conclusion) plus references and appendix, `article` 11pt letter,
1 in margins, same bibliography and figures as the long manuscript. Framing
rule (author's): lead with what the framework achieves; limitations after;
"process mining helps to get detection but it is not detecting on its own";
no number changed, no fired falsifier removed, conformance never credited with
a detection.

Every number was spot-checked against `outputs/*.json` before drafting:
`x33_coverage_*.json` (158/175, 26/480, per-system before/after),
`x38_guideline36.json` (12@1 / 13@1; 8@0 / 26@8; 9@0 / 25@9; pooled 1@49, 0@96,
0@96), `alarm_attribution.json` (37/13/0, 14 no stratum, 1 indeterminate),
`component_attribution.json` (109/22/20/7), `x37_diagnosis.json` (85/114,
44 unresolved, 112/23/16/7), `x36_quantile_band.json` (+4/+4/+3/+2/0, nothing
gained or lost), `x35_field_conditions.json` (P1 true, P3 false), `intervals.json`
(64 v 61 of 73, McNemar 0.25), `crywolf.json`, `x26_real_data_budget.json` (6.1 %).

## Round 1 — first draft (compiled: 21 pp total; References begins p. 15; body ≈ 14.6 pp)

| Section | Rating | Gaps |
|---|---|---|
| Abstract | 7 | Positively framed and complete, but 330 words; the scorecard clause with the adjudication aside is clunky. |
| Introduction | 7 | Carries every headline statistic from the long intro; the first paragraph can lose two. |
| Aim and objectives | 7 | All six objectives with status; items 2 and 4 too wordy for a short paper. |
| Related work | 6 | ~480 words, a list of citations rather than an argument; roughly double what the page budget allows. |
| Method | 7 | Circularity paragraph carries six numbers where three make the point; channels table fine. |
| Verification | 7 | Gate list and three-level regression can be one paragraph; the adversarial-audit list is the strongest part. |
| Results: detection, coverage, baseline, alarm | 8 / 7 / 8 / 8 | Coverage paragraph lists every recovered physics; can be halved. |
| Results: localisation and diagnosis | 7 | X34 and X37 both in full; dense. |
| Results: onboarding, field conditions | 7 | Onboarding repeats counts the systems table carries. |
| What process mining carries | 6 | One sentence presented the dual-duct absence channel's three false-alarm days as a contribution (fixed before compile); three paragraphs at ~600 words. |
| Against current practice | 6 | Voided-run history takes a third of the subsection. |
| Refuted or withdrawn | 7 | Complete (all ten), but one 500-word paragraph. |
| Errata | 8 | One table, eight rows; fine. |
| Limitations | 7 | Complete; the three-way-split paragraph can be shorter. |
| Conclusion | 8 | Carries the settled sentence. |
| Appendix ledger | 8 | 34 rows, one page, all outcomes and falsifiers. |

Defects found: (1) body 14.6 pp against 12; (2) `\ref{sec:coverage}` undefined
(paragraph had no label); (3) the absence-channel sentence above; (4) one
BibTeX warning inherited from the shared bibliography (`openfdd2025` entry type),
same as in the long manuscript.

Plan for round 2: cut ~1,500 words (related work, G36 history, coverage physics,
verification gates, PM subsection), label the coverage paragraph, keep every
number, recompile and measure.

## Round 2 — tightened draft (compiled: 20 pp total; References begins p. 14; body ≈ 13.1 pp)

Changes: every section cut (related work halved, Guideline 36 voided-run history
to one sentence, coverage physics to one sentence per recovery, verification
gates to one paragraph); `\label{sec:coverage}` added to the paragraph; the
by-family figure dropped (its counts are in the systems table and the fouling
statement moved into the text); the appendix ledger, which overflowed a single
`table[p]` and silently lost its rows after X25, split into two tables.

| Section | Rating | Remaining gaps |
|---|---|---|
| Abstract | 7 | Still ~330 words. |
| Introduction | 8 | Two paragraphs plus contributions; fine. |
| Aim and objectives | 8 | — |
| Related work | 7 | One dense paragraph; acceptable for the length. |
| Method | 8 | — |
| Verification | 7 | Third paragraph long; the lessons sentence is optional. |
| Results: detection, coverage, baseline, alarm | 8 / 8 / 8 / 8 | — |
| Results: localisation and diagnosis | 8 | — |
| Results: onboarding, field conditions | 8 / 8 | — |
| What process mining carries | 8 | Framing correct: strata and log channels carry, conformance alone does not; falsifiers kept. |
| Against current practice | 8 | Table plus one paragraph of caveats. |
| Refuted or withdrawn | 7 | Still one long paragraph; items 1, 5, 7 can be shorter. |
| Errata | 8 | — |
| Limitations | 7 | Paragraph two can be tighter. |
| Conclusion | 8 | — |
| Appendix ledger | 8 | Two tables, all 34 rows present (X38 row and part-2 caption verified in the text layer). |

Defect: body still 1.1 pp over. Plan for round 3: abstract to ~290 words, refuted
section and limitations trimmed, compact section spacing, lessons sentence cut.

## Round 3 — fits (compiled: 19 pp total; body ends at the foot of p. 12; Acknowledgements and References begin p. 13; appendix pp. 17–19)

Changes: abstract to ~300 words; compact section spacing (`titlesec`); the
refuted list, limitations and conclusion trimmed; framework figure at 0.92
width and the alarm listing at `\footnotesize`; errata table at `\scriptsize`;
ledger split moved to X24 so both halves fit with their captions (verified in
the text layer: "part 1 of 2", "part 2 of 2"). Every cut was prose; no number,
no fired falsifier and no caveat was removed. The families figure stays out;
the false-alarm, X22, X25 and X29 figures were never included.

| Section | Rating | Remaining gaps |
|---|---|---|
| Abstract | 8 | — |
| Introduction | 8 | — |
| Aim and objectives | 8 | — |
| Related work | 7 | One paragraph; dense but complete. |
| Method | 8 | — |
| Verification | 8 | — |
| Results (all paragraphs) | 8 | Full read-through still due (round 4). |
| What process mining carries | 8 | — |
| Against current practice | 8 | — |
| Refuted or withdrawn | 7 | One paragraph of ten numbered items; readable, dense. |
| Errata | 8 | Table at `\scriptsize`; legible in the PDF. |
| Limitations | 8 | — |
| Conclusion | 8 | Carries the settled sentence. |
| Appendix ledger | 8 | Both halves complete. |

Plan for round 4: read the compiled text end to end for wording, framing and
numbers; re-check every number against the artefacts by script; fix; recompile.
