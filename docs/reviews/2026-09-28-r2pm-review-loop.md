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
