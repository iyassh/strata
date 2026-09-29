# Citation audit of `paper/paper-v2.tex` and `paper/references.bib`
Date: 2026-09-28. Auditor: citation-audit agent (session `session_01QesAGJmei32gYhxSZRiRnY`). Scope: every `\cite` key in the manuscript, every entry in the bibliography, citation gaps, and proposal material worth importing. The manuscript was **not** edited; `references.bib` was.
Method. Keys were extracted with a regex over `\cite{}`/`\citep{}`/`\citet{}`. For each bib entry the DOI (via `https://doi.org/`), arXiv id (via `https://arxiv.org/abs/`) or URL was fetched with `curl -sIL` and the final HTTP status recorded. Metadata was then pulled from the Crossref REST API (DOIs), the arXiv export API (preprints), DataCite (4TU and OpenEI datasets), PubMed (JAMA 1983) or the document's own first page (PDF reports) and compared field by field (title, authors, year, volume, issue, pages, venue) with a script; every discrepancy below was checked by hand before it was changed. Scripts and raw results are in the session scratchpad (`cite-audit/check.py`, `check.json`, `diff.py`).
Reading the HTTP column: `403` and `202` are publisher landing pages (Taylor & Francis, MDPI, Wiley, ACM, IEEE, ASCE, Inderscience) that block non-browser clients after the DOI has already redirected to them; in every such case the DOI itself resolved and Crossref returned the record, so the identifier is valid. `200` is a clean landing page.
## Summary
| Count | |
|---|---|
| Distinct keys cited in the manuscript | 57 |
| Bib entries before / after the audit | 84 / 107 |
| Cited keys missing from the bib | 0 |
| Bib entries never cited (before the audit) | 27 |
| Cited entries whose identifier resolved and metadata matched (no change) | 42 |
| Cited entries with metadata fixed (see table) | 15 |
| Cited entries with a wrong DOI (resolved to a different paper) | 2 (frank2018fddevaluation, abdollah2024transformerssl) |
| Cited entries with no identifier at start, now identified | 2 (vitale2025roadcps, granderson2017fddtoolsurvey) |
| Cited entries UNVERIFIABLE | 0 |
| Uncited entries fixed | 2 (bose2013dataquality: wrong DOI; jung2025vavfaultdata: article number) |
| New entries added, all with tested DOI/URL | 23 |
| Companion papers left untouched | singh2027erratacompanion, singh2027erpmcompanion |
Compile check: `paper/` copied to the scratchpad and `tectonic --keep-logs paper-v2.tex` run after every edit. Exit 0, PDF produced, zero undefined citations, one BibTeX warning (the pre-existing `@software` type of `openfdd2025`, known).
## 1. Inventory
### 1a. Keys cited in `paper-v2.tex` (57)
abdollah2024transformerssl, akhramovich2024pmindustry40, berti2023pm4py, bezerra2013anomalytraces, bi2024aihvacreview (5 uses), brzychczy2025pmsensorreview, buijs2012quality, carmona2018conformancechecking, casillas2024ahufaultmodels, crowe2023faultprevalence, deabes2023fuzzyptn, deng2024afgcn, elmokhtari2024aebas, frank2018fddevaluation, ghalamsiah2025canhvac, ghalamsiah2026ahudatasets, gomes2007petribas, granderson2017fddtoolsurvey (3), granderson2020lbnlfdddata (3), granderson2023lbnlfdddata, gunay2022logicfaults, hofman2023preregistration, husom2026udava, janssen2021sensoreventlog, jimenez2017popper, leemans2013inductiveminer, leemans2014inductiveminerinfrequent, mahmoudan2025fcu, martinezlagunas2024constructionpm, moradbeikie2025pasteurization, moradbeikie2026sensor2eventlog, mukhtar2025reproducibility (3), munozgama2010precision, nolle2022binet, openfdd2025, pawel2022pitfalls, pitsch2025hypothesistesting, pradhan2021dbng36, prince2025improved1dcnnlstm, pritoni2022faultcorrection, rozinat2008conformance, saydirasulov2026fcu, tax2018imprecisions, tun2021hybridrfsvm, vandenbroucke2014negativeevents, vanderaalst2012replaying, vanderaalst2016processmining, vanzelst2021eventabstraction, villani2004hybridpetri, vitale2025kbsfeatures, vitale2025roadcps, wang2025xmhac, weytjens2022dataleakage, xu2015chillerpetri, yuill2013fddprotocol, zhong2022pmids, zhu2021chillertransfer.
Note: `casillas2024ahufaultmodels` and `frank2018fddevaluation` are cited only in the Results/Errata sections (lines 294--579), which were outside the prose read for gaps but inside the verification.
### 1b. Cited but missing from the bib

None.
### 1c. In the bib but never cited (27)
bose2013dataquality, buijs2014receipt, chen2025transferinterpretability, deluzi2025bpmiotreview, feng2024attentiontl, gao2026contrastivessl, he2025unsupervisedvrf, islam2024mlahuhospital, jung2025vavfaultdata, kapoor2023leakage, lei2025crossbuildinguda, li2023cnnlrp, li2024interpretablegnn, lin2020faultcorrection, lin2023controlhunting, mannhardt2016sepsis, mazzetto2025danishbas, pan2024physicsguided, singh2022pmselfhealing, singh2027erpmcompanion, singh2027erratacompanion, suriadi2017imperfection, vandongen2016antialignments, vaneck2015pm2, wang2025realahudata, xiong2024imlrp, zabadi2026digitaltwinapar.
Nine of these are proposed for insertion in Section 3 (deluzi2025bpmiotreview, feng2024attentiontl, kapoor2023leakage, lei2025crossbuildinguda, li2023cnnlrp, lin2020faultcorrection, lin2023controlhunting, singh2022pmselfhealing, xiong2024imlrp). The rest are harmless: BibTeX only prints cited entries.
## 2. Verification of every cited entry
| Key | Identifier tested | HTTP | Verdict / action |
|---|---|---|---|
| abdollah2024transformerssl | doi:10.1016/j.buildenv.2024.111568 | 200 | FIXED DOI: 10.1016/j.buildenv.2024.111481 resolved to an aPMV comfort paper; correct DOI 10.1016/j.buildenv.2024.111568 (= article number in bib) |
| akhramovich2024pmindustry40 | doi:10.1007/s10115-023-02042-x | 200 | OK: title, authors, year, venue, volume/pages match |
| berti2023pm4py | doi:10.1016/j.simpa.2023.100556 | 200 | OK: title, authors, year, venue, volume/pages match |
| bezerra2013anomalytraces | doi:10.1016/j.is.2012.04.004 | 200 | OK: title, authors, year, venue, volume/pages match |
| bi2024aihvacreview | doi:10.1016/j.enrev.2024.100071 | 200 | OK: title, authors, year, venue, volume/pages match |
| brzychczy2025pmsensorreview | doi:10.1007/s10115-024-02297-y | 200 | OK: title, authors, year, venue, volume/pages match |
| buijs2012quality | doi:10.1007/978-3-642-33606-5_19 | 200 | OK: title, authors, year, venue, volume/pages match |
| carmona2018conformancechecking | doi:10.1007/978-3-319-99414-7 | 200 | OK (subtitle not in Crossref; correct) |
| casillas2024ahufaultmodels | doi:10.1080/19401493.2024.2382757 | 403 | OK: title, authors, year, venue, volume/pages match |
| crowe2023faultprevalence | doi:10.1080/23744731.2023.2263324 | 403 | FIXED pages 1042--1057 -> 1027--1038 (Crossref) |
| deabes2023fuzzyptn | doi:10.3390/s23135985 | 403 | OK: title, authors, year, venue, volume/pages match |
| deng2024afgcn | doi:10.1016/j.enbuild.2024.114901 | 200 | OK: title, authors, year, venue, volume/pages match |
| elmokhtari2024aebas | doi:10.1016/j.aei.2024.102810 | 200 | OK: title, authors, year, venue, volume/pages match |
| frank2018fddevaluation | doi:10.1016/j.enbuild.2019.03.024 | 200 | FIXED DOI: 10.1016/j.enbuild.2019.03.010 resolved to an unrelated Brisbane housing paper; correct DOI 10.1016/j.enbuild.2019.03.024 (title, authors, vol 192, pp 84--92 match) |
| ghalamsiah2025canhvac | doi:10.1016/j.enbuild.2025.115659 | 200 | OK: title, authors, year, venue, volume/pages match |
| ghalamsiah2026ahudatasets | doi:10.1038/s41597-025-06179-y | 200 | FIXED authors (Li, Guowen not Guanjing; full list of 8), number 15 -> article 15 in issue 1 |
| gomes2007petribas | doi:10.1109/INDIN.2007.4384731 | 202 | FIXED authors: "Lima, Paulo" was not an author; actual byline Gomes, Costa, Barros, Pais, Rodrigues, Ferreira; pages 57--62 added |
| granderson2017fddtoolsurvey | url:https://eta-publications.lbl.gov/sites/default/files/lbnl-2001075.pdf | 200 | FIXED: had no identifier; URL added (LBNL publications PDF, 200, first page matches title/authors/LBNL-2001075/Nov 2017) |
| granderson2020lbnlfdddata | doi:10.1038/s41597-020-0398-6 | 200 | OK: title, authors, year, venue, volume/pages match |
| granderson2023lbnlfdddata | doi:10.1038/s41597-023-02197-w | 200 | OK: title, authors, year, venue, volume/pages match |
| gunay2022logicfaults | doi:10.1016/j.buildenv.2021.108732 | 200 | OK: title, authors, year, venue, volume/pages match |
| hofman2023preregistration | arxiv:2311.18807 | 200 | OK (arXiv only, no journal version found on Crossref); eprint/url fields added |
| husom2026udava | doi:10.1145/3777897 | 403 | FIXED pages "Article 17" -> 1--34 (Crossref/OpenAlex; article number could not be confirmed, ACM page blocks fetch) |
| janssen2021sensoreventlog | doi:10.1007/978-3-030-72693-5_6 | 200 | OK (LNBIP 406, pp 69--81, ICPM 2020 workshops confirmed) |
| jimenez2017popper | doi:10.1109/IPDPSW.2017.157 | 202 | OK: title, authors, year, venue, volume/pages match |
| leemans2013inductiveminer | doi:10.1007/978-3-642-38697-8_17 | 200 | OK: title, authors, year, venue, volume/pages match |
| leemans2014inductiveminerinfrequent | doi:10.1007/978-3-319-06257-0_6 | 200 | OK: title, authors, year, venue, volume/pages match |
| mahmoudan2025fcu | doi:10.1088/1742-6596/3140/2/022028 | 200 | OK: title, authors, year, venue, volume/pages match |
| martinezlagunas2024constructionpm | doi:10.1061/JCEMD4.COENG-14727 | 403 | OK: title, authors, year, venue, volume/pages match |
| moradbeikie2025pasteurization | doi:10.3390/systems13110935 | 403 | OK: title, authors, year, venue, volume/pages match |
| moradbeikie2026sensor2eventlog | doi:10.1007/978-3-032-28110-4_10 | 200 | FIXED booktitle -> CAiSE 2026 Part I (LNCS), pages 177--194 added |
| mukhtar2025reproducibility | doi:10.1016/j.egyai.2025.100658 | 200 | FIXED: now published, Energy and AI 22:100658 (2025), DOI 10.1016/j.egyai.2025.100658; converted @misc -> @article, arXiv kept in note; editorial note removed from bib (65 studies / 72% / two code links confirmed from the PDF) |
| munozgama2010precision | doi:10.1007/978-3-642-15618-2_16 | 200 | OK |
| nolle2022binet | doi:10.1016/j.is.2019.101458 | 200 | OK: title, authors, year, venue, volume/pages match |
| openfdd2025 | url:https://pypi.org/project/open-fdd/ | 200 | FIXED: PyPI confirms version 4.4.1 (released 2026-08-15; latest 4.4.8), author Ben Bartling, MIT, repo github.com/bbartling/open-fdd (200); author/year/repo updated |
| pawel2022pitfalls | doi:10.1002/bimj.202200091 | 403 | FIXED: now published, Biometrical Journal 66(1):e2200091 (2024), DOI 10.1002/bimj.202200091; @misc -> @article |
| pitsch2025hypothesistesting | doi:10.1109/ICPM66919.2025.11220677 | 202 | OK (ICPM 2025, pp 1--8) |
| pradhan2021dbng36 | doi:10.1145/3486611.3491124 | 403 | OK: title, authors, year, venue, volume/pages match |
| prince2025improved1dcnnlstm | doi:10.3390/systems13050330 | 403 | OK: title, authors, year, venue, volume/pages match |
| pritoni2022faultcorrection | doi:10.1016/j.buildenv.2022.108900 | 200 | OK: title, authors, year, venue, volume/pages match |
| rozinat2008conformance | doi:10.1016/j.is.2007.07.001 | 200 | OK: title, authors, year, venue, volume/pages match |
| saydirasulov2026fcu | doi:10.3390/s26165025 | 403 | OK: title, authors, year, venue, volume/pages match |
| tax2018imprecisions | doi:10.1016/j.ipl.2018.01.013 | 200 | OK: title, authors, year, venue, volume/pages match |
| tun2021hybridrfsvm | doi:10.3390/s21248163 | 403 | OK: title, authors, year, venue, volume/pages match |
| vandenbroucke2014negativeevents | doi:10.1109/TKDE.2013.130 | 202 | OK: title, authors, year, venue, volume/pages match |
| vanderaalst2012replaying | doi:10.1002/widm.1045 | 403 | OK: title, authors, year, venue, volume/pages match |
| vanderaalst2016processmining | doi:10.1007/978-3-662-49851-4 | 200 | OK (Crossref gives short title "Process Mining"; subtitle correct) |
| vanzelst2021eventabstraction | doi:10.1007/s41066-020-00226-2 | 200 | OK: title, authors, year, venue, volume/pages match |
| villani2004hybridpetri | doi:10.1590/S0103-17592004000200003 | 302 | OK: title, authors, year, venue, volume/pages match |
| vitale2025kbsfeatures | doi:10.1016/j.knosys.2025.112970 | 200 | OK: title, authors, year, venue, volume/pages match |
| vitale2025roadcps | doi:10.1016/j.jmsy.2025.12.005 | 200 | FIXED: had no identifier; now published, J. Manufacturing Systems 84:189--206 (2026), DOI 10.1016/j.jmsy.2025.12.005 (arXiv 2506.21502 lists this DOI); year 2025 -> 2026, key unchanged |
| wang2025xmhac | doi:10.1016/j.buildenv.2025.113504 | 200 | OK: title, authors, year, venue, volume/pages match |
| weytjens2022dataleakage | doi:10.1007/978-3-030-94343-1_2 | 200 | OK: title, authors, year, venue, volume/pages match |
| xu2015chillerpetri | doi:10.1504/IJWMC.2015.071684 | 403 | FIXED authors "Xu, Xiaodong and others" -> Xu, Bing; Su, Jun; Fan, Qiu Min; Zhu, Ya Cheng; issue 3 -> 1; pages 43--48 (Inderscience page) |
| yuill2013fddprotocol | doi:10.1080/10789669.2013.808135 | 403 | OK: title, authors, year, venue, volume/pages match |
| zhong2022pmids | arxiv:2206.10379 | 200 | OK (arXiv only, no journal version found on Crossref); eprint/url fields added |
| zhu2021chillertransfer | doi:10.1016/j.buildenv.2021.107957 | 200 | OK: title, authors, year, venue, volume/pages match |

Uncited entries were checked the same way. Two were wrong and are fixed: `bose2013dataquality` had DOI 10.1109/CIDM.2013.6597225, which is a different CIDM 2013 paper ("Discovering signature patterns from event logs"); the correct DOI is 10.1109/CIDM.2013.6597227. `jung2025vavfaultdata` listed article 798; Scientific Data gives 763. All other uncited entries resolved with matching metadata (4TU dataset DOIs verified through DataCite).
### Side findings about the supporting material (not bib changes)
- `/Users/yassh/Downloads/Ureap/papers/03_interpretable_ml/chen_2023_interpretable_ml_buildings.pdf` is **not** Chen, Xiao, Guo & Yan's review. Its first page is Zhao, Zhang, Yang, Yan & You, "Emerging information and communication technologies for smart energy systems and renewable transition", Advances in Applied Energy 9 (2023) 100125. The real review is article 100123 (DOI 10.1016/j.adapen.2023.100123, verified) and is now in the bib as `chen2023interpretablereview`.
- `_Sorted_Papers_Inventory.md` carries wrong bylines for at least nine PDFs (e.g. `liu_2024_afgcn` is Deng et al.; `zhang_2024_imlrp` is Xiong et al.; `wang_2025_transfer_interpretability` is Chen et al.; `xing_2025_cross_building_uda` is Lei et al.; `movahed_2024_ae_bas` is El Mokhtari & McArthur; `atif_2025_digital_twin_apar` is Zabadi et al.; `chakraborty_2024_physics_guided` is Pan et al.; `sorensen_2025_rule_ml_danish_bas` is Mazzetto; `chen_2025_vav_fault_datasets` is Jung, Yoon & Im). The bib entries are correct; the inventory is not. Nothing in the manuscript inherits the errors.
- The proposal's reference list has Mukhtar et al. with the wrong coauthors ("Hirsch, Glock"); the bib is right (Hadwiger, Wotawa, Schweiger). The proposal also says Mukhtar reproduced "ten" papers; the paper analysed 65 primary studies (PDF line "in total 65 studies"), which is what the manuscript says.
## 3. Citation gaps
Format: manuscript line, first words of the claim, key(s) to cite, justification. Keys marked **new** were added to `references.bib` in this audit with tested identifiers; keys marked *bib* already existed. All are ready for `\cite{}` insertion by another agent. Suggested placement is at the end of the quoted clause unless stated.
| Line | Claim (first words) | Cite | Why |
|---|---|---|---|
| 112 | "Buildings account for approximately 34\% of global energy-related" | **unep2025gsr** | the 34 % (and 32 % of final energy) figure is UNEP/GlobalABC's; Bi et al. is a secondary source for it. Add beside `bi2024aihvacreview`. |
| 112 | "The fraction of HVAC energy wasted by undetected faults has" | **katipamula2005fddreview1**, **doe2017hvacsavings** | Katipamula & Brambley's 2005 review is the origin of the 15--30 % waste estimate the field repeats; the DOE/Navigant 2017 report is the proposal's ref [2] and puts HVAC at 30 % of commercial building energy. Cite both with the existing two. |
| 114 | "a pre-programmed rule fires when a named fault pattern is matched" | **schein2006apar** | APAR (Schein, Bushby, Castro, House) is the canonical rule library; the manuscript later calls its rules "NIST APAR lineage" without ever citing APAR. |
| 116 | "a post-hoc explanation method such as layer-wise relevance propagation" | *li2023cnnlrp*, *xiong2024imlrp*, **chen2023interpretablereview** | LRP applied to HVAC FDD is exactly Li et al. 2023 and Xiong et al. 2024 (both in bib, uncited); Chen et al. 2023 is the interpretable-ML-in-buildings survey a referee will expect. |
| 116 / 154 | "on RP-1312 data" | (none) | the ASHRAE RP-1312 final report (Wen & Li 2011) has no DOI or stable URL on Crossref/OSTI; leave as is or spell out "ASHRAE Research Project 1312" in prose. Not added. |
| 120 | "an alignment-based deviation signal that carries formal fitness and precision semantics" | *vanderaalst2012replaying*, **adriansyah2011alignments** | alignments are Adriansyah et al.; the textbook is not the alignment paper. `vanderaalst2012replaying` is already cited at l.209 and can be cited here too. |
| 120 (also 132, 172, 197, 220, 606) | "ASHRAE Guideline 36 control sequences as the conceptual reference" | **ashrae2021guideline36** | the guideline is named eleven times and never cited. Cite at first mention (l.120) and at l.606 where open-fdd implements it. |
| 120 | "discover a Petri-net model of expected behaviour" | **murata1989petrinets** | optional; standard reference for the formalism if the venue expects it. |
| 162 | "The established response is domain adaptation, which transfers learned network weights" | *lei2025crossbuildinguda*, *feng2024attentiontl* | two further cross-building/transfer HVAC FDD papers already in the bib; strengthens "the literature above studies". |
| 166 | "Process mining was formalised by van der Aalst as a methodology" | **vanderaalst2012manifesto** | the Manifesto is the field's founding statement; cite with the textbook. |
| 166 | "applied across cyber-physical and sensor-driven domains adjacent to building energy" | **myers2018pmics**, *singh2022pmselfhealing* | Myers et al. is the ICS/SCADA process-mining anomaly-detection precedent (proposal ref [10]); Singh et al. 2022 is the IoT self-healing paper (proposal ref [11], in bib, uncited). |
| 166 | "The technical barrier common to all these applications is event abstraction" | *deluzi2025bpmiotreview*, **mangler2024iotbp** | De Luzi et al. name event abstraction as the enabler for PM on IoT (in bib, uncited); Mangler et al. state the three challenges (granularity, noise, temporal semantics) the alphabet wall answers. |
| 168 | "our own exact-phrase searches of the OpenAlex corpus" | **priem2022openalex** | the corpus searched should be cited. |
| 174 | "the Lawrence Berkeley National Laboratory team's automated fault-correction line" | *lin2020faultcorrection*, *lin2023controlhunting* | the "line" is three papers; only Pritoni 2022 is cited. Both others are in the bib. |
| 176 / 290 | "The LBNL FDD dataset family" / "The datasets are public and citable by DOI" | **granderson2022lbnlfdddatasets**, *granderson2023lbnlfdddata* | the dataset DOI itself (10.25984/1881324, OEDI) and the 2023 Scientific Data descriptor that covers the terminal-unit and rooftop systems; l.290 currently cites only the 2020 paper. |
| 199 | "the process-mining form of the data-leakage problem" | *kapoor2023leakage* | the ML-side leakage/reproducibility reference (in bib, uncited); pairs with Weytjens & De Weerdt. |
| 209 / 220 | "physics rules descended from the NIST APAR lineage" | **schein2006apar** | as at l.114. |
| 107, 234, 606 | "one-sided 95\% upper bound of 1.5\%" / "floored at three days" / "the same 3/365 null" | **hanley1983zeronumerators** (alt. **eypasch1995ruleofthree**) | 3/199 = 1.5 % is the rule of three; the three-day floor is the same rule. Hanley & Lippman-Hand is the original; Eypasch et al. the accessible restatement. |
| 246 | "Every experiment is pre-registered: the hypothesis, and the specific observation that would refute it" | **nosek2018preregistration** | the pre-registration reference a referee outside process mining will look for. |
| 254 | "checks coverage of the Brick semantic model" | **balaji2016brick** | Brick is used and never cited. |
| 375 / 384 | "a principal-component-analysis baseline using squared prediction error" | **wang2004pcaahu**, **jackson1979spe** | PCA-SPE for AHU sensor FDD is Wang & Xiao 2004; the SPE/Q statistic is Jackson & Mudholkar 1979. |
| 395 / 418 | "Wilson 95\% intervals" / "an exact McNemar test" | **wilson1927interval**, **mcnemar1947test** | named methods; cheap to cite. |
| 595 | "Bonferroni correction" | (none) | standard; no citation needed. |

Not found / not added: a DOI-bearing source for ASHRAE RP-1312; a journal version of Hofman et al. 2023 or Zhong & Lisitsa 2022 (both remain arXiv-only on Crossref).
## 4. Proposal lines worth importing
From `proposal.txt` (ProcessHeal UREAP proposal v2). Reference numbers are the proposal's; each is resolved to a verified bib key. Figures were checked against the source where the source was reachable.
| Where | Sentence | Verified source |
|---|---|---|
| Intro | "Buildings are responsible for 34% of global energy-related CO2 emissions [1], with HVAC systems as the dominant energy consumer." | **unep2025gsr** (GlobalABC page verified: 32 % of energy, 34 % of CO2). The manuscript already states the figure at l.112 but credits Bi et al.; swap or add the primary source. |
| Intro | "The U.S. Department of Energy estimates that 15--30% of HVAC energy is wasted due to undetected operational faults [2]" | **doe2017hvacsavings** for the DOE report; but the 15--30 % sentence is Katipamula & Brambley's (**katipamula2005fddreview1**). The DOE PDF does not contain the 15--30 % fault-waste sentence (it gives HVAC as 30 % of commercial building energy), so attribute the range to Katipamula & Brambley, not to DOE. |
| Intro | "LBNL's analysis ... found that systematic commissioning yields a median 6% energy savings [16], but most buildings never receive it" | **crowe2020commissioning** (Crowe, Mills, ... Granderson, Energy and Buildings 227:110408, 2020; DOI verified). The proposal's ref [16] is unnamed; this is the LBNL commissioning meta-analysis. Verify the "median 6 %" figure against the paper's abstract before quoting; only the citation was verified here. Useful in the conclusion as the payoff of detection that reaches an operator. |
| Abstract / 3.2 | "PM has been successfully applied to manufacturing [9, 35], cybersecurity [10], and industrial IoT [11, 37] --- yet it has never been applied to building energy systems [4, 5, 6]." | *vitale2025roadcps*, *moradbeikie2025pasteurization*, **myers2018pmics**, *singh2022pmselfhealing*, *husom2026udava*, then *bi2024aihvacreview*, *akhramovich2024pmindustry40*, *brzychczy2025pmsensorreview*. The manuscript's related-work paragraph (l.166) covers all but Myers and Singh; adding them makes the sentence citable verbatim in the introduction. |
| Intro | "HVAC faults are fundamentally process failures --- operational sequences that deviate from designed behavior." | *crowe2023faultprevalence* (seven of the ten most common AHU faults are behaviour-based). The manuscript makes this argument at l.114; the proposal's one-sentence form is a sharper opening for the introduction or conclusion. |
| 3.3 | "Mangler et al. (2024) ... identify three key challenges ...: determining appropriate granularity for event abstraction, handling noise and missing data in sensor streams, and preserving the temporal semantics of physical processes." | **mangler2024iotbp** (arXiv 2405.08528 verified). Fits the event-abstraction paragraph at l.166 or l.197: the strata answer granularity, the alphabet wall and the noise floor answer noise. |
| 3.1 | "Mukhtar et al.'s 2025 empirical study ... found significant discrepancies" | *mukhtar2025reproducibility*, now the Energy and AI version. The proposal's "ten papers" is wrong (65 primary studies, 72 % unstated data provenance, two code links, one broken, all confirmed in the PDF); the manuscript's numbers are right. Cite the journal version, not the preprint, at l.118, 122 and 242, and drop "circulated as a preprint" at l.118. |
| Policy (proposal ref [17]) | "EU EPBD 2024 Recast --- mandatory building automation and control systems for large non-residential buildings" | Directive (EU) 2024/1275, https://eur-lex.europa.eu/eli/dir/2024/1275/oj/eng (EUR-Lex responds 202 to curl; page exists). Not added to the bib because the proposal's threshold ("70 kW by 2029") could not be verified here; if the conclusion wants a regulatory driver for FDD, add an entry after reading Article 13 of the directive. |

## 5. Changes made to `paper/references.bib`
Edited (17): crowe2023faultprevalence, frank2018fddevaluation, jung2025vavfaultdata, abdollah2024transformerssl, mukhtar2025reproducibility, vitale2025roadcps, husom2026udava, gomes2007petribas, xu2015chillerpetri, ghalamsiah2026ahudatasets, bose2013dataquality, pawel2022pitfalls, hofman2023preregistration, zhong2022pmids, granderson2017fddtoolsurvey, openfdd2025, moradbeikie2026sensor2eventlog. No key was renamed, so the manuscript needs no change to keep compiling.
Added (23), each with a DOI or URL that was fetched and whose metadata was checked: katipamula2005fddreview1, katipamula2005fddreview2, doe2017hvacsavings, schein2006apar, chen2023interpretablereview, nosek2018preregistration, hanley1983zeronumerators, eypasch1995ruleofthree, wang2004pcaahu, jackson1979spe, balaji2016brick, vanderaalst2012manifesto, adriansyah2011alignments, murata1989petrinets, priem2022openalex, granderson2022lbnlfdddatasets, unep2025gsr, ashrae2021guideline36, wilson1927interval, mcnemar1947test, crowe2020commissioning, myers2018pmics, mangler2024iotbp.
Two URL caveats. `unep2025gsr` points at the GlobalABC publication page (HTTP 200; unep.org itself sits behind Cloudflare and refuses non-browser clients, though the web search confirmed the UNEP page exists). `ashrae2021guideline36` points at ASHRAE's standards-and-guidelines page (HTTP 200), because every store page for the guideline (ASHRAE Store, ANSI webstore, Techstreet) is Cloudflare-gated; the 2021 designation is confirmed by the ANSI webstore and ASHRAE Store listings returned by the search.

The manuscript still needs `\cite{}` commands inserted for the gap table; that is deliberately left to the agent editing `paper-v2.tex`.

## 6. Addendum (same day): TRU primary sources for the front/back agent

Requested keys: (1) UNEP 2024/25 -> `unep2025gsr` (already added). (2) DOE/EE-1703 -> `doe2017hvacsavings` (already added; note the 15--30 % fault-waste sentence is Katipamula & Brambley's, `katipamula2005fddreview1`, not the DOE report's). (3) TRU LCDES -> `tru2026lcdes` (tru.ca/sustainability/lcdes.html, 200; the page dates construction to fall 2024, system on 1 Sept 2026, Powerhouse opening 28 Sept 2026, partners Creative Energy and BC Hydro) and `tru2025lcdesmilestone` (TRU Newsroom, 26 June 2025, 200). No Creative Energy project page for TRU exists (creativeenergycanada.com/projects/thompson-rivers-university returns 404), so Creative Energy is credited inside the TRU entries rather than as an author. (4) SES Consulting study -> `ses2022cacstudy` (tru.ca PDF, 200, application/pdf; first page matches: ASHRAE Level 1 Energy Study, Campus Activity Centre, SES Consulting Inc., Vancouver, 25 May 2022). Compile re-checked: clean.

## 7. Citation insertion (same day, cite-insert agent)

Twenty-seven edits to `paper/paper-v2.tex`: 24 `\cite` insertions and the deletion of the three body `%TODO-cite` comments (Guideline 36, APAR, Brick). The four front/back TODOs had already been resolved by the front/back agent before this pass (unep2025gsr and doe2017hvacsavings in the introduction, katipamula2005fddreview1 on the 15--30 % clause, tru2026lcdes / tru2025lcdesmilestone / ses2022cacstudy in the conclusion), so nothing was left uncited and no TODO comment remains. Distinct cited keys: 65 before this pass, 89 after. Compile: tectonic exit 0, zero undefined citations or references, the one known openfdd2025 style warning; every new first author found in the rendered bibliography.

| Sentence (first words) | Key(s) added |
|---|---|
| "A threshold alarm fires ... a pre-programmed rule fires when a named fault pattern is matched" | schein2006apar |
| "a post-hoc explanation method such as layer-wise relevance propagation" | li2023cnnlrp, xiong2024imlrp, chen2023interpretablereview (added to existing cite) |
| "discover a Petri-net model of expected behaviour" | murata1989petrinets |
| "an alignment-based deviation signal that carries formal fitness and precision semantics" | adriansyah2011alignments, vanderaalst2012replaying (added to existing cite) |
| "ASHRAE Guideline 36 control sequences as the conceptual reference" | ashrae2021guideline36 |
| "The established response is domain adaptation, which transfers learned network weights" | lei2025crossbuildinguda, feng2024attentiontl |
| "Process mining was formalised by van der Aalst" | vanderaalst2012manifesto (added to existing cite) |
| "The methodology has also been applied across cyber-physical and sensor-driven domains" | myers2018pmics, singh2022pmselfhealing |
| "The technical barrier common to all these applications is event abstraction" | deluzi2025bpmiotreview, mangler2024iotbp |
| "our own exact-phrase searches of the OpenAlex corpus" | priem2022openalex |
| "the Lawrence Berkeley National Laboratory team's automated fault-correction line" | lin2020faultcorrection, lin2023controlhunting |
| "The LBNL FDD dataset family" | granderson2022lbnlfdddatasets, granderson2023lbnlfdddata (added to existing cite) |
| "The datasets are public and citable by DOI" | granderson2022lbnlfdddatasets, granderson2023lbnlfdddata (added to existing cite) |
| "the process-mining form of the data-leakage problem" | kapoor2023leakage (added to existing cite) |
| "Continuous sensor streams are converted ... grounded in ASHRAE Guideline 36" | ashrae2021guideline36 |
| "physics rules descended from the NIST APAR lineage" | schein2006apar |
| "on the fault-free holdout days it could evaluate, floored at three days" | hanley1983zeronumerators |
| "Every experiment is pre-registered ... before the experiment runs" | nosek2018preregistration |
| "checks coverage of the Brick semantic model" | balaji2016brick |
| "a principal-component-analysis baseline using squared prediction error" | wang2004pcaahu, jackson1979spe |
| "with Wilson 95% intervals in brackets" (Table caption) | wilson1927interval |
| "an exact McNemar test on the three discordant scenarios" | mcnemar1947test |
| "imports a third-party open-source implementation of the Guideline 36 fault conditions" | ashrae2021guideline36 |
| "hold them to the same 3/365 null" | hanley1983zeronumerators |

Not inserted, by design: the abstract's "one-sided 95 % upper bound of 1.5 %" (no citations in the abstract); eypasch1995ruleofthree (Hanley & Lippman-Hand used instead); katipamula2005fddreview2 and crowe2020commissioning (no existing sentence for them; section 4 proposals were not turned into prose); the two "(none)" rows (RP-1312, Bonferroni).
