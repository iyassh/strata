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

## Round 4 — full read-through of the compiled text (19 pp total; body ends at the foot of p. 12; Acknowledgements and References p. 13–17; ledger pp. 18–19)

Read end to end from `pdftotext`. Fixed: the introduction's dangling
"buildings that run..." clause; the related-work sentence that cited two
individual studies as surveys; "attributable" in the abstract (one of the 51 is
indeterminate, so "in the attribution universe"); a handful of word-level trims
to keep the conclusion on p. 12 after those fixes. Secondary numbers re-checked
against artefacts: X15 deployed frequency significant on 12 (matches
`x15_enriched_frequency.json`), X22 single-duct reversal AUC 0.908 → 0.91 and
fan-powered AUCs 0.40–0.51 (`x22_positive_control.json`), X14 six added events
on the single-duct unit and 7 state-channel held-out days
(`x14_enriched_alphabet.json`), X30 seven cells (`x30_method_grid.json`).

Framing check: every section leads with what the framework achieves; the
conformance result is stated as a measured finding ("process mining helps to
get detection; it is not detecting on its own") in the introduction, the
process-mining subsection and the conclusion; conformance is nowhere credited
with a detection; all ten adverse results, every fired falsifier (F-X7, F-X11.d,
F-X13.b, F-X14.a, F-X18.b, F-X19.b/d, F-X20, F-X21.a, F-X25.c, F-X27.b, F-X28,
F-X30.b, F-X34.a, F-X36.a, F-X37.a/b, F-X38.a) and both disclosure caveats
(rate-channel demotion, 15.6 %; three-way-split debt) are present.

| Section | Rating |
|---|---|
| Abstract | 9 |
| Introduction | 8 |
| Aim and objectives | 8 |
| Related work | 7 |
| Method | 8 |
| Verification | 8 |
| Results (detection, coverage, baseline, alarm, localisation, onboarding, field) | 8 |
| What process mining carries | 9 |
| Against current practice | 8 |
| Refuted or withdrawn | 7 |
| Errata | 8 |
| Limitations | 8 |
| Conclusion | 8 |
| Appendix ledger | 8 |

Trajectory (mean over sections): round 1 ≈ 7.1 → round 2 ≈ 7.7 → round 3 ≈ 7.9 →
round 4 ≈ 8.1. What remains below 9 is density, not error: related work and the
refuted list are each a single dense paragraph by necessity of the page limit.

Not verified: the ~1.5 h onboarding time (reconstructed from commit timestamps
in the long paper; not re-derived here), and the cry-wolf "47–99 to 1" ratio and
the 0.36 lower AUC bound, both quoted from the long manuscript.

## Round 5 — second editor, round 1 (hostile-referee read against `paper-v2.tex` and the artefacts; compiled: 19 pp; body ends at the foot of p. 12; Acknowledgements and References p. 13; ledger pp. 18–19)

Method: every paragraph read; the short paper diffed claim by claim against
the long manuscript; 32 further numbers checked against `outputs/*.json` and
`ERRATA.md` (reversal probe, circularity, union rates, time to detection,
cry-wolf, coil-bias windows, PCA baseline, X7, X8, X12–X15, X17–X22, X24–X31,
X33–X36, E3, E7, matched rules, attribution universe). All confirmed except
the items fixed below.

Substantive fixes (all in `paper/short/strata-short.tex`):

1. **Headline attribution figures were the unadopted layer's.** The abstract,
   the end of the localisation paragraph and the conclusion quoted "subsystem
   85 %, exact component 71 %", which are the X37 diagnosis layer's lifted
   numbers, while the same paragraph says that layer "is not adopted". The long
   manuscript headlines the carrying rule's 83 % at subsystem level (X34,
   `component_attribution.json`: 109 + 22 of 158). Abstract and conclusion now
   say 83 %; the paragraph closes on 37 of 50, 83 %, 69 %; X37's 85 % / 71 %
   remain in the body as the non-adopted result. Added the long paper's caveat
   that X37 does nothing on the fan-powered units.
2. **Attribution denominator.** Abstract said "37 of the 51 detections in the
   attribution universe"; the long paper and `alarm_attribution.json` give
   37 of the 50 with determinable ground truth (51 less one indeterminate).
   Conclusion's "never wrongly" replaced by "37 of 50 checkable detections and
   a wrong one in none".
3. **Adjudicated total.** Abstract now states 157 after the E5 adjudication,
   as the long paper does in every headline.
4. **Oscillation is not a log channel.** Abstract, introduction and conclusion
   said "the absence, frequency and oscillation channels over the log"; the
   channels table and the long paper have oscillation reading raw signals.
   Now "the absence and frequency channels over the log".
5. **Seven no-rule detections mis-described.** "seven detections … carried by
   the frequency or oscillation channel alone, instability faults and one fan
   restriction" — `component_attribution.json` shows only four of the seven
   (the instability faults) are frequency/oscillation-only; three carry
   residual credits. Rewritten to match the artefact. (The long paper's
   parenthetical "frequency- or oscillation-only" at its X34 sentence has the
   same imprecision — flagged to the manuscript loop.)
6. **Conformance removal lowers three systems, not two.** Added the fan coil
   unit's 5/96 → 4/96 (long paper §results; `union_fpr_fcu.json`).
7. **X25 step-4 ledger row.** Both papers' ledgers say "series unit loses 3";
   `x25_step4_perday.json` records the dual-duct unit losing 3 (48 → 45, the
   fired F-X25.c names ddahu) and the series unit 2. Short ledger corrected;
   flagged to the manuscript loop.
8. **X38 caveats.** The first caveat said STRATA's false-alarm day "is out of
   sample" where the long manuscript (second-editor round 1) made it
   symmetric: STRATA's signature rules are silenced on the same whole year, so
   the rules-channel zero is post-selection on both sides. Restored. Removed
   the unsupported parenthetical "(removing it from both gives 11 of 13
   against 13 of 13)", which appears in no artefact and not in the long paper;
   added the long paper's "under every reading STRATA detects more on that
   unit, the match resting on the false-alarm tie alone".
9. **Rule-count contradictions.** Onboarding text (26 and 16 signature rules;
   45 mappings / 35 rules) contradicted the systems table (56, 19; 109 / 58).
   Added the long paper's reconciliations (counts at onboarding vs the
   committed configuration) and the fan coil's 41 → 42 → 40 → 43 chain, which
   the table's "40 → 43" needed.
10. **Abstract omissions relative to the long abstract.** Added: the
    improvement claim over current practice is withdrawn on the air handler;
    the PCA baseline has fewer false alarms on the terminal units; the sealed
    transfer test never had attainable power and is a protocol failure.
    "Thirty" → "more than thirty" (the ledger has 35 rows) throughout; the four
    later fired falsifiers (X34, X36–X38) are now named beside the ten adverse
    results.
11. **Dropped caveats restored.** Benchmark scope (no dataset seeds a schedule,
    override or setpoint-reset fault, so the introduction's behavioural-fault
    case is motivated, not tested; the practice comparison covers three
    systems and one library); "no code change" qualified by the fan coil gate
    script's two lines; 1.5 h onboarding "by commit timestamps"; the X15 gain
    is a scenario the PCA baseline also detects; X30's two not-evaluated cells;
    the rate-channel demotion is post hoc and its split-half probe fails on the
    series unit; "the channel turned out to be three instruments"; the transfer
    quantity is constant "across rules within a building".
12. **Claims softened to the long paper's.** "Absent from every review whose
    scope could have caught it" → one review whose scope would have, three
    whose scope or period would not necessarily; "guarding that a caveat
    survives is, to our knowledge, new" → "we have not found it reported".
    Research question restored to "and what survives when they cannot";
    objective 2 "in the form its falsification required … and the founding
    hypothesis is refuted". Conclusion now carries the long conclusion's
    Guideline 36 sentence.
13. **Results intro** no longer says every false-alarm count is on 96 held-out
    days (the rooftop rows are 28 and 49): now "on the five simulated systems".

Space (all prose, no number, falsifier or caveat removed): the phase-report
overclaim anecdote, the "none would have been caught by a test suite" and
"exactly as a lost feature would" sentences, the pre-ledger jitter sentence
compressed to a clause with its X9/X10 pointer, the hybrid-deferral sentence in
Limitations (stated in the objectives), the "first place a technician would
look" tail, and framework figure at 0.66 width, alarm listing at `\scriptsize`,
coverage and Guideline 36 tables at `\footnotesize`, tighter heading and float
spacing.

Not changed, disagreements and notes for the author: (a) the naive all-channel
union is 15.6 % on the parallel unit too and 21.9 % on the fan coil unit
(`union_fpr_*.json` `union_all8`); both papers quote only the single-duct 15.6 %
— consistent between them, left as is, but a referee may ask. (b) X17 mappings:
`x17_onboarding.json` records 80, both papers say 79; left consistent with the
long paper. (c) First pass rated the abstract 9 while it carried the unadopted
85 % / 71 % and the wrong attribution denominator; the density-not-error
verdict of round 4 did not hold for those items.

| Section | Rating |
|---|---|
| Abstract | 8 (was carrying unadopted figures; now aligned with the long abstract) |
| Introduction | 8 |
| Aim and objectives | 8 |
| Related work | 7 |
| Method | 8 |
| Verification | 8 |
| Results (detection, coverage, baseline, alarm, localisation, onboarding, field) | 8 |
| What process mining carries | 8 |
| Against current practice | 8 |
| Refuted or withdrawn | 7 |
| Errata | 8 |
| Limitations | 8 |
| Conclusion | 8 |
| Appendix ledger | 8 |

Overall ≈ 7.9 on entry by this reading (the 8.1 of round 4 did not survive the
cross-check), ≈ 8.1 after the fixes.

## Round 6 — second editor, round 2 (compiled: 19 pp; body ends at the foot of p. 12; Acknowledgements and References p. 13; ledger pp. 18–19)

Every passage edited in the previous round re-read in the rendered text
(`pdftotext`): all 25 edited sentences present and grammatical, both ledger
halves intact ("part 1 of 2", "part 2 of 2"), no undefined reference, the
only overfull boxes the two pre-existing sub-3 pt ones in the channels table
and the ledger. Numbers re-checked in the rendered text: 157 adjudicated,
37 of 50, 83 % / 69 % (carrying rule) beside 85 % / 71 % (X37, stated as not
adopted), 5/96 → 4/96 on the fan coil unit, dual-duct 48 → 45 in the X25
step-4 row. Nothing further found; loop closed on the second editor's side.
Ratings unchanged from the previous block (overall ≈ 8.1).

Open items handed to the manuscript loop rather than fixed here, because they
are in `paper-v2.tex` too: the X25 step-4 ledger row ("series unit loses 3";
artefact says dual-duct 3, series 2), the "frequency- or oscillation-only"
parenthetical on the seven unnamed-component detections (three carry residual
credits), and X17's 79 mappings against the artefact's 80.
