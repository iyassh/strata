# R2PM paper — review-rate-fix loop (2026-09-28)

File: `paper/r2pm/r2pm.tex` (llncs, `\bibliography{../references}`, splncs04). Hard limit 8 pages.
Framing rule (author, binding): lead with what the protocol and framework achieve; limitations
after; never change a number, remove a fired falsifier or an erratum, or claim conformance detected
faults. Errata and voided runs are evidence of rigour.

## Round 1 — 2026-09-28 (start)

**Spot-checked numbers (all match):** E1/E2 MD5 prefixes 89b13704 / 63b857d7 / a9fdfc50 / 5133132d
(`week0_audit.json`); OA_TEMP |diff| max 0.3331, mean 0.0214; E3 constant 401.85999, healthy SA_SP
day-median range [401.85, 403.48], fault range [-0.60, 5.97] over 20 files, 365/365 and 7150/7150,
accuracy 1.0 (`e3_leakage.json`); E4 rotation 2,880 rows, 1 wrap point, first row 01/03 vs 01/01
(`sfpu_rotation_evidence`); E5 damper floor 0.0 vs 0.1, first occupied minute 05:01 79 + 05:02 121 =
200, 06:01 33, 06:02 70 (`e5_schedule.json`); x11 healthy median 1.0706, fault-branch baseline 0.008,
delta 1.0625, oa_bias estimator 0.0072, adjudicated 13/14 (`x11_branch.json`); Sepsis 10 midnight
stamps, 1050 cases / 15214 events, receipt 1434 / 8577 (`gates_public_log.json`); injection rows: each
class fires exactly its gate, leak fires none (`gates_injection.json`); E7 57 S / 3 indeterminate of 60
(`e7_zone_label.json`); E8 +0.2 / +0.4 in.wg, -3.6 F (`e8_bias_magnitude.json`); E6 MD5 a0b885fe
(`week0_audit_fcu.json`). 14 bib keys all resolve. Baseline PDF: 8 pages, no undefined refs.

**Ratings (1–10):** Abstract 7 · Intro 7 · Gates 7 · Defects (table + E1–E5) 8 · Leak 8 ·
Taxonomy 8 · Recommendations 7 · Disclosure 6 (author TODO, left) · Conclusion 5 · Overall 7.

**Gaps found:**
1. Table caption says "Six machine-verified defects"; the table has eight rows. Evidence list omits
   `e5_schedule.json`, `e7_zone_label.json`, `e8_bias_magnitude.json`, `week0_audit_fcu.json`.
2. Conclusion: "Of five LBNL archives three carry a defect; the dual-duct AHU passed every gate" —
   wrong: E7 (PFPU, SFPU) and E8 (DDAHU) mean all five carry at least one. Contradicts the paper's own
   table.
3. Table floats alone onto page 8 *after* the references (llncs top-float fraction). Wastes half a page.
4. Gates section opens "Six checks" then enumerates seven (healthy-silence is a detector-side gate).
5. The pre-registration protocol, the regression gate, the audit trail and the voided-run record —
   which the paper is supposed to cover — are one clause ("a lesson is not closed until a test
   enforces it"). The X38 (voided twice, third execution quoted), X37 (three runs) and X35/X36 cases
   are absent. Title claims the gate battery "found them" while §1 says three of eight were found by
   gates.
6. The author's settled framing sentence for the companion is absent from the intro.

**Fixes applied this round:** (1) caption → "Eight", evidence list completed; (2) conclusion
rewritten per system; (3) `\topfraction`/`\floatpagefraction` raised, table `[!t]`; (4) "Six checks
… a seventh, on the detector side"; (5) new §3 "The Protocol Around the Gates" (pre-registration,
amendments before re-runs, voided artefacts kept and never quoted, `scripts/regress.py` byte
regeneration with FROZEN closing commits, 154 guard tests; X38/X37/X35/X36 as worked examples),
abstract sentence added, title → "…and the Protocol That Found Them" (flagged for the author: §1
already says only three of eight came from gates); (6) settled sentence added where the companion is
cited.

**Round 1 close (page budget):** adding §3 pushed the PDF to 9 pages; recovered by restructuring
Table 1 to four columns (files folded into the defect cell, `\scriptsize`), merging the two gate
footnotes, and cutting sentences that carried no number or evidence: the `coi_bias` documentary
naming note (still in ERRATA.md), E4's "inadvertent time travel" analogy (the taxonomy section
still places E4), the leak section's closing generalisation (kept in Recommendations), the
E5-footnote aside, and the conclusion's restatement of E3. Also fixed on the read-through: §1 said
"four systems" while E8 and the conclusion cover the dual-duct AHU — now five (DDAHU, 56 files,
`week0_audit_ddahu.json`). No number changed; no erratum or fired falsifier removed. Result: 8 pages,
no undefined references, 14/14 citations resolve.

## Round 2 — 2026-09-28 (after commit 9805a72)

**Spot-checked numbers (all match):** PFPU/SFPU 31 + 31 = 62 hashes (`week0_audit.json`); E3
thresholds 200.92543 = 401.85086/2 and 0.80373 = 1.60746/2 (midpoint rule as stated,
`e3_leakage.json`); SA_SP per-file mean of day-medians 1.103–1.145 ("between 1.10 and 1.15");
E5 five concordant estimators (four coi_bias + oa_bias_4), spread 0.001 (`x11_branch.json`);
"forty years" = `DateOffset(years=40)` in `scripts/gates_injection.py`; FCU 49 files, one
duplicate group; DDAHU 56 files (`week0_audit_ddahu.json`); 28 pre-registration plans in
`docs/plans/`; 154 `def test` functions under `tests/`; FROZEN dict holds 12 closed artefacts at
their closing commits; the 2026-09-11 open-fdd void was declared by two auditors
(`docs/plans/NEXT-openfdd-baseline-repair.md`), Amendment 1 by two more.
**ERRATA-only numbers (no JSON carries them):** "38 % exact zeros" (E1), "48.8 %" false-alarm rate
(E1 relabel history), "0.05–0.14 °F" fault-vs-fault divergence (E5). Left as ERRATA.md is canonical;
flagged here. "In under a second each" (public-log gates) is a runtime the script prints and does not
commit — softened to "in seconds".

**Ratings:** Abstract 8 · Intro 8 · Gates 8 · Protocol 8 · Defects 8 · Leak 8 · Taxonomy 8 ·
Recommendations 7 · Disclosure 6 (author TODO) · Conclusion 7 · Overall 8.

**Gaps found and fixed:**
1. §3 said the regression gate "fails on any byte that differs"; `verdict_from_text` compares
   flattened JSON values, not bytes → "any value".
2. §3 said "an audit voided the first run" of X38; the 2026-09-11 void was two auditors
   independently → "two hostile audits … two more voided the second".
3. §2 credited the hash gate with E1 and E2 only; it also produced E6 (FCU) → "E1, E2 and E6".
4. Comma splice in the voided-run sentence.
5. "in under a second each" → "in seconds" (see above).
Result: 8 pages, no undefined references.

## Round 3 — 2026-09-28 (after commit a1001ce)

**Spot-checked:** E4 found in Phase 3B (`PHASE3B_RESULTS.md` l.85), raw-rotation gate added in the
Phase 7 audit (commit 517f13a, 2026-08-18) → "four phases later" holds; E1 OA_TEMP "bit-identical
across all fault files" matches ERRATA (the JSON note retracts only the "identical to healthy"
reading, which the paper does not make); E8 +2 °C file shifts −3.6 °F = its label; E5 damper
floors of the three damper_stuck files sit at 0.25/0.75/1.0 above the 0.1 floor (table says "every
fault file floors at 0.100" for the non-stuck files — ERRATA wording, acceptable); thresholds and
day counts re-confirmed; gates_public_log G4 = the paper's "log hashing" gate. Table page rendered
and inspected at 70 dpi: legible, no overflow.

**Ratings:** Abstract 8 · Intro 8 · Gates 8 · Protocol 8 · Defects 8 · Leak 8 · Taxonomy 8 ·
Recommendations 7 · Disclosure 6 (author TODO) · Conclusion 7 · Overall 8.

**Gap found and fixed:** §6 claimed the fourth class (E4, E7, E8) is "caught by log-generic gates";
only E4's misalignment is (the injection test confirms), while the E7/E8 mislabels came from
audits → "the first class, and the misalignment in the fourth, are caught by log-generic gates; the
mislabels and the second and third classes cannot be". Nothing else worth fixing. 8 pages.

## Round 4 — 2026-09-28 (after commit 63ab07e)

**Spot-checked:** damper floors per file in `week0_audit.json` `config_branch.occupied_oa_dmpr_min`:
healthy 0.0; sixteen fault files 0.1; damper_stuck 025/075/100 at 0.25/0.75/1.0; damper_stuck_010 at
0.1 (its stuck value equals the floor). "Every fault file floors at exactly 0.100" in §4.4 was
therefore overstated for three files → parenthetical added, matching ERRATA E5's wording.
Twenty-eight plan files, 154 tests and 12 FROZEN entries re-confirmed unchanged.

**Ratings:** Abstract 8 · Intro 8 · Gates 8 · Protocol 8 · Defects 8 · Leak 8 · Taxonomy 8 ·
Recommendations 7 · Disclosure 6 (author TODO) · Conclusion 7 · Overall 8.

**Fixes:** the E5 damper-floor parenthetical above; a double-semicolon sentence in §3 split in two.
8 pages, no undefined references.

## Round 5 — 2026-09-28 (after commit a49b42f)

**Spot-checked:** x11 adjudicated scorecard 13/14 with rules carrying 7 scenarios alone and 2 with
the residual channel (the "nine rules-carried scenarios"); DDAHU week-0 gates: 56 distinct hashes,
no duplicate group, no raw rotation, calendar and monotonicity clean on all 56, every column
declared in the TTL — "passed every gate" holds; E3 healthy SA_SP mean 402.788 ("near 402");
E1 OA_TEMP |diff| mean 0.0214 / max 0.3331; injection row `dup_case` fires G4 alone; the committed
`paper/r2pm/r2pm.pdf`, the scratch build and `~/Downloads/Ureap/docs/writing/r2pm.pdf` share one
MD5; the four loop commits touch only the three permitted paths and carry no attribution lines.

**Ratings:** unchanged from Round 4 (Overall 8). **Gaps:** none worth fixing. No edit this round.

## Round 6 — 2026-09-28 (after commit 0f1d7cf)

**Checked:** pages 1, 3 and 4 rendered and inspected (title wraps to three lines cleanly, footnotes
in place, table legible). The whitespace at the foot of page 3 is not float-induced: `[!tb]`,
`[tbp]`, `[!t]` give identical pagination and `[H]` goes to 9 pages. Source re-read in full; every
number in the paper traces to `ERRATA.md` or an `outputs/*.json` artefact (three ERRATA-only numbers
noted in Round 2). **Gaps:** none. No edit this round. Two consecutive rounds without a fix → loop
closed.

**Open for the author (not changed by this loop):** the title now reads "…and the Protocol That
Found Them" (was "…the Gate Battery That Found Them", contradicted by §1's "three by gates");
the Disclosure Status section's TODO; the supervisor co-authorship TODO at the file head; and the
three ERRATA-only numbers (38 % exact zeros, 48.8 %, 0.05–0.14 °F) which have no JSON artefact.

**Trajectory:** overall 7 → 8 → 8 → 8 → 8 → 8; Conclusion 5 → 7; Gates 7 → 8; Protocol (new) 8.

## Round 1 (second editor) — 2026-09-28 (after commit 8a14ef5)

Independent hostile pass by a second editor; every paragraph re-read against `ERRATA.md`,
`PHASE12_RESULTS.md` §X37/§X38, the X38 pre-registration and Amendment 1, `scripts/regress.py`,
`src/strata/log_gates.py`, `docs/plans/`, `tests/` and the JSON artefacts.

**Spot-checked (all match):** X38 executed three times (2026-09-11 void → `outputs/void/`; run 1 of
the repaired adapter kept as `*_run1.json`; run 2 quoted), F-X38.a fired on every system, the
2026-09-11 void's two defects and run 1's three named defects all in the pre-registration and
Amendment 1; X37 three runs, two script defects fixed to the pre-registered wording; 28 files named
`*-prereg.md` in `docs/plans/`; injection rows fire G1/G4/G2/G3 alone and `leak` fires none;
`strata gates LOG.xes` exists (`src/strata/cli.py`); 20 × 365 − 150 = 7,150 fault-file days (the
215-day `damper_stuck_100` file); E5 first-occupied-minute counts 200 + 33 + 70 = 303; E3 midpoint
thresholds; DDAHU/PFPU/SFPU/FCU/SDAHU file counts; `OA_TEMP` mean 0.0214 / max 0.3331; E8 +0.20 /
+0.40 in.wg and −3.6 °F; 14 bib keys resolve.

**Ratings before fixes:** Abstract 8 · Intro 8 · Gates 7 · Protocol 6 · Defects 8 · Leak 8 ·
Taxonomy 8 · Recommendations 6 · Disclosure 6 (author TODO) · Conclusion 6 · Overall 7.

**Gaps found (claims outrunning the artefacts, or contradictions):**
1. §3 called X38 "a Guideline 36 rule battery"; the X38 write-up's own print caveat (i) says the
   battery is open-fdd 4.4.1's installed defaults, tighter than the GL36 values its labels cite,
   and must not be called Guideline 36 → "the open-fdd rule battery (X38; Guideline 36-derived
   rules at the library's installed defaults)".
2. §3 "154 guard tests pin the published numbers": 154 is the whole suite (84 top-level + 66
   `tests/unit` code tests + 4 integration); the unit tests pin no published number → "the test
   suite (154 tests) pins …". (Disagreement with Round 1's "154 guard tests".)
3. §3 "artefacts are kept under a run-number suffix": the 2026-09-11 void lives in
   `outputs/void/`, only run 1 under `_run1` → "in a void directory or under a run-number suffix".
4. §3 "every quoted number regenerates" was contradicted by this paper's own three ERRATA-only
   numbers (38 %, 48.8 %, 0.05–0.14 °F, flagged in Round 2 but never surfaced to the reader) →
   "every benchmark number regenerates from the current code", plus a footnote at the 38 % naming
   the three numbers that have no JSON artefact. A reproducibility reviewer would test that
   sentence against the paper first.
5. §2 "Six checks run against the raw files": log hashing runs on the derived event logs → "Six
   checks run before any science". "We ran them unchanged over two public logs": the public-log
   run is a separate XES packaging (`strata.log_gates`, pm4py), not the week-0 script → "packaged
   the four for XES logs and ran them". "Trace-hash gate" in the injection paragraph vs "log
   hashing" in the gate list → one name.
6. Conclusion "found not by insight but by … audits" contradicts §4's hostile audits (E5 needed
   the damper-floor reading); "Each would have inflated a published result" is false for E4
   (misaligns) and E7 (a reader scoring against the documented zone marks correct alarms wrong,
   which deflates) → "silently altered"; "the gates cost a second" vs §2's "in seconds" (Round 2
   softened one and not the other) → "seconds".
7. §5 "E1, E2, E4 and E6 corrupt an accounting" left E7 and E8 unplaced → "… E7 and E8 corrupt an
   accounting or a label".
8. §7 reviewers' sentence did not parse ("which columns … would have caught E3") → rewritten as
   the two questions a reviewer should ask.
9. Stale traceability comment at the file head (listed four artefacts of nine).

**Page budget:** the footnote and the X38 rename pushed the PDF to 9 pages; recovered by tightening
five sentences that carried no number (intro leak sentence, gate-rule sentence, E4 sort sentence,
the new footnote and reviewers' sentence). No number changed; no erratum or fired falsifier removed
or softened; no conformance-detection claim added; the author's settled sentence kept.
Result: 8 pages, no undefined references; committed PDF = `docs/writing/r2pm.pdf` (one MD5).

**Ratings after fixes:** Abstract 8 · Intro 8 · Gates 8 · Protocol 8 · Defects 8 · Leak 8 ·
Taxonomy 8 · Recommendations 7 · Disclosure 6 (author TODO) · Conclusion 7 · Overall 8.

## Round 2 (second editor) — 2026-09-28 (after commit 73d178f)

**Spot-checked (all match):** E4 `sfpu_rotation_evidence` (set identical, 1 wrap point, first row
01/03 vs 01/01); E5 damper floors (healthy 0.0; sixteen fault files 0.1; `damper_stuck_010` 0.1 =
the floor; 025/075/100 at 0.25/0.75/1.0); E5 first-occupied-minute 05:01 79 + 05:02 121 = 200,
06:01 33, 06:02 70, 303 occupied days on every full-year file; X11 healthy median 1.0706 (→ 1.071),
fault-branch baseline 0.008 from five estimators with spread 0.001, delta 1.0625 (→ 1.06), oa_bias
0.0072; E7 `moving_zone` counts S 57 / indeterminate 3 of 60; E8 deck shift 0.0 and box shifts
+0.2 / +0.4 / −3.6; Sepsis 1050 cases, 15214 events, 10 midnight stamps; E6 MD5 `a0b885fe` in
`week0_audit_fcu.json`; E3 thresholds and healthy range [401.85086, 403.478475].

**Ratings before fixes:** unchanged from Round 1 close (Overall 8).

**Gaps found and fixed:**
1. §4.4 "the three stuck-damper files" — there are four; `damper_stuck_010`'s stuck value equals
   the 0.1 floor → "three of the four stuck-damper files at their stuck value above it".
2. §4.1 "The mislabel was overturned twice" — the label never changed; our reading did → "Our
   reading of the files was overturned twice".
3. §7 "count scenarios as distinct runs" read backwards → "count distinct runs, not labels, as
   scenarios".

**Not fixable here, flagged for the author:** the claim that Deng and colleagues trained an
outdoor-air-bias class on the `oa_bias` files rests on the project's own reading
(`RESEARCH_LOG.md` l.52, `GAP_ANALYSIS_AUG2026.md` l.172, "citable, carefully"); the publisher
page could not be fetched from this session, so the claim was not verified against the paper's
dataset section. The hedge "we assert only that the bias it names is not in the data" stays.

**Page budget:** the three fixes tipped the PDF to 9 pages. Page 3 ends with a third of the page
blank; diagnosed this round as *not* float-, footnote- or penalty-induced (the same 41-line page 3
appears with the table removed, with the new footnote removed, with the E1 paragraph split and
with club/widow penalties at 150), so it was left alone. Recovered the page by cutting on pages
4–8 only: E4's "cannot recur" clause, "and we measured how free", the leak section's "property of
the data, not of any published result" lead-in (the remedy sentence stays), the Disclosure
sentence's opener, and E3's "with every file's range". No number changed; no erratum or fired
falsifier removed or softened. Result: 8 pages, no undefined references; committed PDF =
`docs/writing/r2pm.pdf` (one MD5).

**Ratings after fixes:** Abstract 8 · Intro 8 · Gates 8 · Protocol 8 · Defects 8 · Leak 8 ·
Taxonomy 8 · Recommendations 7 · Disclosure 6 (author TODO) · Conclusion 7 · Overall 8.

**Disagreements with the first editor's changes:** (a) Round 1's "154 guard tests" counted the
whole suite, including 66 unit tests of code that pin no published number (fixed in second-editor
Round 1); (b) Round 2 softened "in under a second" in §2 but left "the gates cost a second" in the
conclusion (fixed); (c) Rounds 2–6 flagged the three ERRATA-only numbers in the log but left §3
asserting "every quoted number regenerates" — a reproducibility reviewer would test that sentence
against the paper first (fixed, and the three are now footnoted for the reader); (d) §3 named the
X38 battery "Guideline 36" although the X38 write-up's own print caveat forbids it (fixed).
The title question ("…the Protocol That Found Them") is left with the author; under the current
§1 wording the protocol includes the gates and the audits, so the title is defensible.
