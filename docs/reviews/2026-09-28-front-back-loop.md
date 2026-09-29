# Front/back review loop — abstract, introduction, aims and objectives, conclusion (paper/paper-v2.tex)

Reviewer: front-back agent, 2026-09-28, after the two manuscript editors' loops of the same day (docs/reviews/2026-09-28-manuscript-review-loop.md) and the X33–X38 closures. Scope: the four parts only; no other section and no references.bib edited. Framing rule: positive but true to the artefacts; no number changed, no fired falsifier removed or softened, no claim that conformance detected faults, no "deployed at TRU", no "self-healing achieved". Author's goal for these parts: show that the research is worth it and of use; the conclusion must say what was found, how it can be useful at TRU, how it scales, and the future of a self-healing system.

Inputs read before Round 1: PHASE12_RESULTS.md (X33 series summary and analysis, X34, X37, X35, X36, X38), RESEARCH_LOG.md rows L53–L67, README.md, the four parts as committed at 7528e20, the manuscript review loop of today, the original proposal (abstract, LCDES testbed, expected contributions, references), ProcessHeal_STRATA_Framework.md, and papers/12_tru_primary_sources/ses_consulting_2022_cac_energy_study.pdf (ASHRAE Level 1 study of TRU's Campus Activity Centre).

## Round 1 — 2026-09-28 (commit follows)

### Paragraph-by-paragraph reading of the four parts as committed at 7528e20

**Abstract** (one paragraph, 505 words)
- Claims, in order: framework + protocol; 158/175 and 157 adjudicated with the five per-system counts; median one day; 26/480; 1.0–9.4 %; 15.6 % all-channel; blind onboarding; sixteen recovered; 37/50 zone, 13 none, 0 wrong; 83 % subsystem; X35 worst 7/96; X26 3/49; the author's sentence; ablation 199 scenarios, 1.5 % bound, three systems' rates lowered; sealed transfer test; PCA three fewer of 73; G36 battery within one on the AHU, a third on terminal units, claim withdrawn on the AHU; eight errata; regenerates.
- Artefacts: every number was spot-checked by the two editors today; re-checked here: alarm_attribution 37/13/0 of 50 attributable (65 detected, 14 no stratum, 1 indeterminate); component_attribution exact-or-subsystem 0.829; x26 deployed_fp 3 of 49; x35 worst PFPU schedule 7/96, no falsifier; intervals 64 vs 61 of 73, three STRATA-only, none baseline-only; x38 G3 12/14 @ 1, 8/30 @ 0, 9/29 @ 0 vs 13/26/25 @ 1/8/9. All agree.
- Missing for an Energy and Buildings / Applied Energy reader: opens with "We report" (no problem statement); ends on "Every number regenerates" (no statement of why it matters); at 505 words it is long for either journal.
- Missing for the author's goal: nothing says what an operator is left with.

**Introduction**
- P1 (motivation). Claims 34 % of global energy-related CO2 cited to bi2024aihvacreview: **not supported by that source** (checked against the PDF: Bi states "HVAC up to 50 % of a building's consumption" and "15–30 % of commercial buildings' consumption wasted by fault operation and unreasonable control", citing its refs [4] and [5]; no 34 %). The 34 % is the proposal's ref [1], UNEP Global Status Report 2024/25, which is not in references.bib. pritoni2022faultcorrection states "40 % of primary energy globally, 33 % of direct and indirect carbon emissions from fuel combustion" and "5 to 30 % whole-building savings". Crowe numbers (60,000+, 317, 245/month, 40 % of AHUs, 55 % SAT setpoint) verified against the PDF and the folder notes.
- P2 (behaviour-based faults): supported by Crowe; but the Limitations section records that no benchmark seeds that class; the introduction did not say so.
- P3 (ML), P4 (reproducibility): supported; unchanged.
- P5 (opportunity, refutation, division of labour): supported; the author's sentence present. The gap (interpretable, localisable, low-false-alarm FDD from ordinary trend data, onboarded by configuration) was implied across four paragraphs and never stated in one place.
- P6 (contributions): prose "First … Fourth"; the detector contribution carried no numbers and did not mention the comparison against current practice; no roadmap; closed with "Deployment on an operating building remains the intended next phase", which belongs to the aims.

**Aims and objectives**
- Lead paragraphs: supported. "What the framework is meant to do" paragraph is the best statement of the operator's need in the paper.
- Objectives 1–6: Objective 4's Done/Done-against-the-claim/Status already matches X38 (12/14 @ 1 vs 13 @ 1; 8/30 and 9/29 @ 0 vs 26 and 25 @ 8 and 9; all three parts executed; improvement claim withdrawn on the air handler, coverage difference bought with false alarms on the terminal units). Objective 3's "3 of 49" and Objective 5's counts agree with the artefacts and the conclusion. Objective 1's "seven LBNL datasets" = five simulated + two rooftop units.
- Closing paragraphs: "deployment … the coverage audit is the checklist" — supported; no pointer to where the paper says what deployment would require.

**Conclusion** (three paragraphs)
- P1 (what was found + X38): supported, numbers as in the abstract.
- P2 (process-mining answer): supported; author's sentence present.
- P3 (protocol): supported (ten adverse results + four later falsifiers, as the Verification section counts).
- Missing for the author's goal: nothing on what the result is worth in practice (onboarding cost, budget on a real unit, what an alarm names); nothing on TRU, although the proposal names TRU's campus energy system as the intended testbed; nothing on scaling beyond "two onboarded blind"; nothing on the self-healing destination the project's name states; no cross-reference to X37 as the tested diagnosis layer.

### Ratings before Round 1 (1–10)

| Part | Score | Reason |
|---|---|---|
| Abstract | 8.5 | Every number verified; no problem opening, no closing on significance, 505 words |
| Introduction | 7.5 | 34 % attributed to a source that does not carry it; gap never stated in one sentence; contributions un-numbered and number-free; no roadmap |
| Aims and objectives | 9 | Structure and statuses match the artefacts (Objective 4 matches X38); only a pointer missing |
| Conclusion | 7 | Sound on findings and protocol; silent on practice, TRU, scaling and the self-healing programme the author asked for |

### Rewrites made (paper/paper-v2.tex)
1. **Abstract** rewritten: opens with the problem (faults persist because alarms are ignored or anomalies unactionable), then what STRATA does and the protocol it was built under, then every number in the previous abstract in the same order and value, the author's sentence verbatim, the PCA and Guideline 36 comparisons, the errata, and a closing sentence on what an operator is left with (budget, configuration onboarding, refutation-tested claims). 518 words: the brief asked for under 400 if possible; with every number kept, a problem opening and a closing sentence, 518 is the floor reached — the previous version was 505. No number changed.
2. **Introduction**: P1 reworded to what the cited sources state (40 % primary energy and a third of fuel-combustion carbon emissions from pritoni2022faultcorrection; HVAC up to half of a building's consumption, 15–30 % waste, 5–30 % savings from bi2024aihvacreview and pritoni2022faultcorrection) with two `%TODO-cite` comments for the proposal's primary sources (UNEP GSR 2024/25 for 34 %; DOE/EE-1703 2017 for 15–30 %). P2 gains one sentence that the benchmarks seed none of the behaviour-based class (cross-reference to Limitations). New gap paragraph stating the operator's requirement in one sentence and what rule libraries and anomaly detectors each lack (rule libraries: a fraction of the coverage on the terminal units measured here, no budget; anomaly detectors: no name, no budget). Contributions made a numbered list of four matching the body, with the detector's numbers (158/175, 26/480, 83 %, 37/50 none wrong, blind onboarding, PCA 64 vs 61 of 73, G36 claim fired its falsifier) and section cross-references. Roadmap paragraph added, pointing to every section including the new conclusion label.
3. **Aims**: closing sentence now points to Section conclusion for what deploying on the author's campus would require and deliver. Objective 4 unchanged (already matches X38).
4. **Conclusion** rewritten in six paragraphs, `\label{sec:conclusion}` added: (a) what was found — detection, localisation, robustness, baseline, first-application and the process-mining division of labour in the author's sentence, numbers as in the abstract; (b) practice — budget held on the real rooftop unit (182 days, 3 of 49), onboarding about 1.5 hours by commit timestamps for the second system type (45 mappings, 35 rules), the third in minutes, fourth and fifth blind with one and two healthy-silence iterations and two lines in a gate script, alarms name zone and subsystem, fourteen of the twenty wrong-subsystem cases name the responding component, seventeen misses are coil fouling inside every healthy band; (c) TRU — the proposal's LCDES testbed and the 2022 ASHRAE Level 1 study of the Campus Activity Centre (AHU with VAV boxes, fan coil units, five rooftop units, Automated Logic BAS, scheduled for connection to the district plant), both with `%TODO-cite`; deployment stated as the next step and not done; what it requires (fault-free period at the site's sampling rate audited for contamination, sensor map as configuration, healthy-silence pass at that rate) and delivers (per-day per-unit alarms with a site-measured false-alarm rate, a coverage account); the district plant named as an equipment class not yet onboarded; (d) scaling — four systems after the reference one plus two rooftop units through the same pipeline code, the healthy-silence gate, the regression gate and the pre-registration form travel with the configuration, the sampling-rate limit, the blind-onboarding counts 45/55 and 41/47 as the honest prior, the 2026 AHU datasets as the next target; (e) self-healing — ProcessHeal destination, detection → localisation → diagnosis → correction, what STRATA provides, what X37 showed (85 of 114 resolved, 44 unresolved, five dual-duct damper cases resolved, both bars missed, not adoptable; cause vs response not separable passively), what a loop would need (active tests, a witness, an operator study), citing lin2020faultcorrection, pritoni2022faultcorrection and singh2022pmselfhealing, stated as a research programme; (f) the protocol paragraph kept, with the closing sentence tied to the introduction's gap.

### Deviation from the brief, recorded
The brief said the 1.5-hour onboarding figure was for the dual-duct unit. configs/ONBOARDING_LOG.md and the Results section attribute the ~1.5 h (by commit timestamps) to the parallel fan-powered unit, the second system type; the dual-duct unit's onboarding (X17) has no wall-clock record, only its pre-registration and config commits (90dd88c, 2026-09-24 00:24). The conclusion therefore credits the 1.5 h to the second system type, as the Results section does.

### Citations needed but not in references.bib (for the citation agent; marked `%TODO-cite` in the .tex)
- UNEP, Global Status Report for Buildings and Construction 2024/25 (proposal ref [1]): the 34 % global energy-related CO2 share. The intro currently states what pritoni2022faultcorrection carries instead (40 % primary energy, 33 % of fuel-combustion emissions).
- U.S. Department of Energy, DOE/EE-1703 (2017), Energy Savings Potential and RD&D Opportunities for Commercial Building HVAC Systems (proposal ref [2]): the 15–30 % waste figure, which bi2024aihvacreview reports at second hand.
- Creative Energy, TRU Low-Carbon District Energy System project (2024) and Thompson Rivers University Facilities, LCDES project information (2024) (proposal refs [3], [21]): the LCDES sentences in the conclusion.
- SES Consulting, Thompson Rivers University ASHRAE Level 1 Energy Study, Campus Activity Centre, 25 May 2022 (papers/12_tru_primary_sources): the CAC equipment sentence in the conclusion.

### Not verified in this round
- The 1.5 h figure and the 45/35 onboarding counts were taken from ONBOARDING_LOG.md, not re-derived from git timestamps (the two editors left the same item open).
- The proposal's "$50M" and "late 2026" LCDES figures are not used in the paper because no bib source carries them.
- Bi 2024's own sources for the 50 % HVAC share and the 15–30 % waste figure (its refs [4] and [5]) were not opened.

Compile: tectonic in scratchpad front-back, exit 0, 46 pages (43 before: the numbered contributions, roadmap and six-paragraph conclusion), no undefined references or citations (font-shape warnings only), no new overfull box above 10 pt. PDF copied to paper/paper-v2.pdf and ~/Downloads/Ureap/docs/writing/paper-v2.pdf.

### Ratings after Round 1

| Part | Before → after | Reason |
|---|---|---|
| Abstract | 8.5 → 9 | Problem-first, closes on significance, every number kept; still 518 words |
| Introduction | 7.5 → 9 | Sources match what they state; gap stated; contributions numbered with numbers; roadmap |
| Aims and objectives | 9 → 9 | Pointer added; nothing else needed |
| Conclusion | 7 → 9 | All six parts the author asked for, each sentence tied to an artefact or marked TODO-cite |

Left for Round 2: read every rewritten paragraph in the rendered PDF for flow; check each cross-reference target; consider whether the abstract can lose non-number prose.

## Round 2 — 2026-09-28, rendered re-read (pages 1–6 and 32–34 of the compiled PDF)

### Paragraph check
- Abstract: reads as one argument (problem, what STRATA does, protocol, results, localisation, robustness, the author's sentence, refutations, baselines, errata, what an operator is left with). Every number matches Round 1's list. No further prose can go without dropping a number or the problem/closing sentences; 518 words stands and is reported to the lead.
- Introduction: the gap paragraph and the numbered contributions render correctly; every cross-reference resolves to the section named (Section 6 results, 7 refuted, 8 errata, 9 limitations, 9.1 commercial practice, 10 conclusion). The rule-library clause was tightened in Round 1's last edit to "a fraction of the coverage on the terminal units measured here", so it claims only what X38 measured.
- Aims: the closing pointer to Section 10 renders; Objective 4's status text matches the X38 ledger and the baseline subsection word for word on the counts.
- Conclusion: paragraphs (a)–(f) render in order; the one inexact phrase found was "scheduled for connection to the district plant" — the SES study says the building "is in the Phase 2 plan for connection to the district energy plant"; reworded to "in the second phase of the plan for connection". Nothing else found.

### Ratings after Round 2

| Part | Round 1 → Round 2 |
|---|---|
| Abstract | 9 → 9 (length is the only residue) |
| Introduction | 9 → 9.5 |
| Aims and objectives | 9 → 9.5 |
| Conclusion | 9 → 9.5 |

Round 2 found one wording fix and nothing else; a third round is run on the rendered text after recompilation.

Commit 2afd9b8 carries Rounds 1–2 (the lead's rule change of the same hour: commit the .tex as it stands, including the body agent's in-progress edits in other sections, and say so in the message).

## Round 3 — 2026-09-28, rendered re-read after recompilation (pages 1–6, 32–34)

- Abstract: 518 words in the rendered text; every number re-read against Round 1's list; nothing to change.
- Introduction, aims: nothing to change.
- Conclusion: the six paragraphs re-read; the Round 2 rewording renders; the cross-references to Section 7 (contamination, sampling rate), Section 6 (X37) and reference [17] (the 2026 AHU datasets) were checked against the .tex by search and land on the text they name. No "??" in the PDF text; tectonic exit 0; no undefined reference or citation.
- Nothing found. Two consecutive rounds (2 found one wording fix only; 3 found nothing) — the loop stops here.

### Final ratings

| Part | Score | What keeps it below 10 |
|---|---|---|
| Abstract | 9 | 518 words; the brief's target of under 400 is not reachable while every number is kept |
| Introduction | 9.5 | Two motivation primaries (UNEP, DOE) await keys from the citation agent |
| Aims and objectives | 9.5 | Nothing outstanding; the 1.5 h figure is still by commit timestamps, not a logged wall clock |
| Conclusion | 9.5 | Two TRU sources (LCDES project pages, the 2022 CAC energy study) await keys; deployment itself is future work by the artefacts |
