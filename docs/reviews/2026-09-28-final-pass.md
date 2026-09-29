# Final whole-paper pass — paper/paper-v2.tex — 2026-09-28

Reviewer brief: read the rendered PDF page by page, read the abstract, introduction and conclusion as a hostile Energy and Buildings referee and as the author's professor, spot-check numbers against `outputs/*.json` and `PHASE12_RESULTS.md`, open cited sources at random, rate every part 1–10, fix, recompile, commit; repeat until every part is 10 or two consecutive rounds find nothing. Framing rule honoured: no number changed, no fired falsifier softened, no claim that conformance checking detected faults, no "deployed at TRU", no "self-healing achieved"; the author's sentence stays in abstract, introduction and conclusion.

## Round 1 — rendered PDF (52 pp), artefact spot-checks, citation spot-checks

### Rendered PDF
Compiled with tectonic in the scratchpad (exit 0; 52 pages; overfull boxes ≤ 6.5 pt, none visible). `pdftotext -layout` read page by page: every table row present (Tables 1–9, including the longtable continuations of Tables 7 and 9), every figure present with its caption (Figures 1–7), no "??", no undefined citation, section order 1–10 then Acknowledgements, Appendix A, References [1]–[89]. Pages 10, 12, 30 and 43 also inspected as images: Figure 1, Table 1, Table 7 (cont.) and Table 9 (cont.) fit their pages.

### Artefact spot-checks (all match)
| Claim in the manuscript | Artefact | Result |
|---|---|---|
| 158 of 175 detected; 14/14, 26/30, 25/29, 50/55, 43/47; RTU sim 20/24 | `benchmark_v6_*.json` (is_fault, not excluded, ttd_days) | match |
| False-alarm days 1, 8, 9, 3, 5 of 96; naive unions 15, 15, 9, 8, 21 of 96; RTU sim 0/28; field RTU 3/49 | `union_fpr_*.json`, `intervals.json`, `x26_real_data_budget.json` | match |
| Time-to-detection tails 3, 5, 14, 114, 114 (DDAHU); 3, 3, 4, 15 (FCU); 14 (RTU); SDAHU 9 at day 1 and 4 at day 2 adjudicated | `benchmark_v6_*.json` | match (SDAHU naive 9/5; the adjudicated-away oa_bias run has TTD 2) |
| Removing the conformance channels: SFPU 9→4, PFPU 8→6, FCU 5→4 | recomputed from per-channel holdout date lists in `union_fpr_*.json` | match |
| Terminal unit named 37 / none 13 / wrong 0 / indeterminate 1 / no device stratum 14 (65 naive) | `alarm_attribution.json` | match |
| Component attribution 109 (69 %) / 22 / 20 (12.7 %) / 7; 83 % subsystem | `component_attribution.json` | match |
| Diagnosis layer 112 (70.9 %), 85 of 114 (74.6 %), 44 unresolved (27.8 %), wrong 10.1 %, 85 % subsystem | `x37_diagnosis.json` | match |
| PCA baseline 64 vs 61 of 73, Wilson [78.2, 93.4] / [73.4, 90.3], McNemar p = 0.25, baseline FA 1/79, 1/96, 1/96 | `intervals.json` | match |
| Guideline 36 battery 12/14 at 1 FA vs 13 at 1; 8/30, 9/29 at 0 FA vs 26, 25 at 8, 9; falsifier fired on every system | `x38_guideline36.json` | match |
| Field conditions worst 7 of 96 (PFPU schedule), at most one detection lost per system and condition, clean arm = scorecard | `x35_field_conditions.json` | match |
| Positive control: 55 of 72 and 59 of 83 reversed days flagged, AUC 0.99; SDAHU AUC 0.91 with zero hit rate; FPU AUC ≈ 0.5 | `x22_positive_control.json` | match |
| Method grid: no cell detects a miss; worst 7 of 72 (9.7 %) | `x30_method_grid.json` | match |
| Enriched frequency: FA 4 and 8, 3 and 5 of 96; 41 significant vs 12 deployed | `x15_enriched_frequency.json` | match |
| Enriched alphabet: 6, 40, 36 added events; 7, 18, 21 FA of 96; time model 15 and 19; frequency alone 4 and 3 | `x14_enriched_alphabet.json` | match |
| Reversal probe 0.8861→0.5526; 0.9533 = 0.9533; 0.9021 vs 0.9026 | `grammar_results.json` | match |
| Columns mapped 26/30, 109, 109, 114, 29, 23/25, 26 | `sensor_coverage.json` | match |
| Onboarding effort: DDAHU 80 mappings, 15 + 26 rules, 1 iteration; FCU 29, 7 + 16, 2 iterations; 45/55 and 41/47 | `x17_onboarding.json`, `x19_onboarding.json` | match |
| Cry-wolf 0.03 %, 0.11 %, 0.12 % | `crywolf.json` | match |
| Sixty-seven numbered lessons | `RESEARCH_LOG.md` (L1–L67) | match (README's "31" is stale repo prose, not the paper's) |
| E3 constant ≈ 401.86, accuracy 1.0 on both columns, 365 + 7,150 days | `e3_leakage.json` | match |

### Citation spot-checks (opened via DOI/URL)
1. Mukhtar et al. 2025 [51] (arXiv 2508.00880 PDF): "in total 65 studies"; "only two papers share a link to their code — one of which was broken"; "72 % of the articles do not specify whether the dataset used is public, proprietary, or commercially available". Claim matches.
2. Zhong and Lisitsa 2022 [88] (arXiv 2206.10379): abstract states "naive process mining with network data is ineffective" for intrusion detection. Claim matches, and the manuscript correctly marks it a preprint.
3. UNEP/GlobalABC Global Status Report 2024/2025 [72] (publication page): 32 % of global energy, 34 % of CO2 emissions. Claim matches.
4. Ghalamsiah et al. 2026 [23] (Scientific Data, via DOI metadata and abstract): "presents the publication of eight new datasets" for AHUs. Claim matches.
5. Brzychczy et al. 2025 [10] (KAIS, via DOI metadata and abstract): "a total of 36 related papers" — matches the "36" in Section 3.3. The per-domain breakdown quoted there (14 + 11 + 7 + 2 + 2 + 1 = 37) could not be checked because the full text sits behind Springer's login from this session; either one paper is counted in two domains in the source or one count is off by one. Left unchanged (no number changed without the source); flagged for the author to confirm against the review's domain table.
6. Crowe et al. 2023 [15] (abstract via DOI metadata): "over 60,000 pieces of HVAC equipment" and "on any given day, 40 % of AHUs" confirmed; the 317 buildings, 245 faults per building per month and 55 % setpoint-reset figures are body-text claims the abstract does not carry, and OSTI's full text refused the connection. Not contradicted; not re-verified here.
7. TRU LCDES page [70]: partners Creative Energy and BC Hydro, construction from fall 2024, "Sept. 1 — System is turned on", 13 buildings including the Campus Activity Centre, Powerhouse opening Sept. 28. Claim matches.
8. SES Consulting 2022 CAC study [66] (PDF): AHU-1 with VAV boxes, FCU-1 and nine fan coils, RTU-1 to RTU-5, Automated Logic front end since 2021, "Phase 2 plan for connection to the district energy plant". One inexactness found: the report says all major systems are on the BAS *except* the heat pumps serving FC-1 to FC-9, whereas the conclusion said "all on an Automated Logic building automation system". Fixed (see below).

### Hostile reading of abstract, introduction, conclusion
- Abstract: every sentence traceable to an artefact; the author's sentence present; refutations stated as refutations; the withdrawn improvement claim stated. Residue: 521 words, long for a journal abstract (the venue's guide for authors could not be fetched to confirm its limit), and every number is one the author asked to keep.
- Introduction: motivation sources match what they state (UNEP, DOE, Katipamula and Brambley, Crowe, Mukhtar); the gap paragraph and four contributions map onto delivered sections (6, 7, 5, 8) and the roadmap names every section including 10. The framing "process mining helps to get detection but is not detecting on its own" present.
- Conclusion: six paragraphs — what was found; what it is worth to an operator; TRU (named as intended testbed, "is the next step and is not done", three requirements, what it would deliver, the district plant as an un-onboarded class); scaling (four systems plus two rooftop units through the same code, two limits); ProcessHeal (diagnosis layer reported as not adoptable, three things a self-healing loop needs, "a research programme and is stated as one"); the protocol. No overclaim found beyond the BAS clause above.

### Body consistency
Contribution list vs sections, Section 2 objective statuses vs Sections 6, 7, 9 and 9.1, Table 2/3/5/6 vs Section 6 prose, Table 7 vs Section 7 prose, Table 9 vs the ledgers: consistent. One informal phrase found in Section 6.1 ("the one constructive result of the night").

### Fixes made in Round 1
1. Conclusion: "Each alarm names the correct terminal unit in 37 of 50 … and carries" → "The alarms name … and each carries" (a single alarm cannot name a unit "in 37 of 50").
2. Conclusion: CAC equipment clause now "every major system except the heat pumps serving nine of the fan coils on an Automated Logic building automation system", as the SES report states.
3. Section 6.1: "the one constructive result of the night" → "of the four vocabulary experiments (X12–X15)".
4. `references.bib` formatting (no entry removed, no key renamed): `ses2022cacstudy` title case protected ("Thompson Rivers University", "Campus Activity Centre"); `pradhan2021dbng36` "Bayesian" and "Guideline" protected; `ashrae2021guideline36` "Guideline" protected; `tru2025lcdesmilestone` date moved out of `howpublished` so the entry no longer prints "26 June 2025, 2025", and "$50M" protected; `janssen2021sensoreventlog` series expanded from "LNBIP"; `martinezlagunas2024constructionpm` article number 04024158 added (Crossref); `villani2004hybridpetri` pages 135–148 added (Crossref).

### Ratings after Round 1
| Part | Score | Justification |
|---|---|---|
| Abstract | 9 | Every number verified; the author's framing intact; 521 words is the only residue, and it cannot fall without dropping a number the author asked to keep |
| Introduction | 9.5 | Sources match; contributions map to sections; Crowe's body figures (317, 245, 55 %) rest on the earlier audit's reading, not re-opened here |
| Aims and objectives | 10 | Each status matches its ledger word for word, including the two "done, against the claim" outcomes |
| 3 Related work | 9.5 | Novelty claim scoped and corroborated; Brzychczy's domain counts sum to 37 for a 36-paper review and need the author's check against the source |
| 4 Method | 9.5 | Channels, split and gate exact; the circularity bound is a cross-version comparison and says so |
| 5 Verification | 10 | Machinery described to be adoptable; what it caught is listed with artefacts |
| 6 Results | 9.5 | Every checked figure matches; density is high but each paragraph carries a distinct finding |
| 7 Refuted or withdrawn | 10 | Ten rows, each with what fired and what survived, consistent with Sections 5 and 10 |
| 8 Errata | 10 | Eight rows with consequences; reproducing commands in ERRATA.md |
| 9 Limitations and 9.1 | 9.5 | Post-hoc choices disclosed; the comparison's three framings and caveats are complete |
| Conclusion | 9.5 | All six parts present and true to the artefacts after the BAS fix; deployment is future work by the artefacts, so a field result cannot be claimed |
| Bibliography | 9.5 | 89 entries render with authors, years and venues; one review's domain breakdown unverifiable from here |
| Overall | 9.5 | |

What keeps parts below 10 and what evidence is missing: (a) abstract length, an editorial choice; (b) Brzychczy's per-domain counts and Crowe's body figures need the full texts, which are login-gated from this session; (c) a field detection result, which the repository does not contain.
