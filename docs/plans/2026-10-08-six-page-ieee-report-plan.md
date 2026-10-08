# Six-page IEEE report for U-REAP: plan (2026-10-08)

Supervisor feedback (2026-10-01): no more than six pages, simple IEEE format, clear plain
language, built around the framework and a proof of concept of implementing it at TRU;
the current paper is too technical and reads as if AI-written. One-month extension requested.

## 1. Length and format norms (checked 2026-10-08)

| venue type | usual length | notes |
|---|---|---|
| IEEE conference paper | 6 pages, two-column, incl. figures and references; up to 2 extra pages for a fee (about $150–175 each) | CASE, ISCC, ITSC, ICC 2025 all follow this |
| IEEE Transactions / journal | 8–12 double-column pages typical; IEEE Access has no fixed limit | not the target now |
| Elsevier energy journals (Energy and Buildings, Applied Energy) | no hard limit; 25–35 manuscript pages typical | the long paper's eventual home, not this report |
| ICPM workshops (ERPM, R2PM) | 12 and 8 pages LNCS | already written, separate |

Decision: IEEE conference format (`IEEEtran`, `conference` option), 6 pages hard, no extra pages.

## 2. What the report is

Not a cut of the long paper. A new document with one job: present the framework simply and
show how it would be implemented at TRU. Two anchors on page 1: the framework diagram and a
one-paragraph statement of what a building operator gets.

Page budget (two-column, ~900 words per page):
1. Title, 150-word abstract, Introduction (the problem in one paragraph; what we built in one; what this report shows in one), framework figure.
2. The framework, stage by stage, in the order the diagram reads: data in, events, process models, calibrated checks, noise gate, explained alarm. One short paragraph each, no equations, one example per stage.
3. What it does on the benchmarks: the systems table (seven rows), the worked alarm, three sentences on results (158/175, 26/480, zone named 37/50 never wrong), one sentence on the Guideline 36 comparison, one on what process mining contributes.
4. Proof of concept at TRU: the Campus Activity Centre (equipment list from the SES 2022 study, Automated Logic BAS already logging), the four steps to deploy (fault-free period; sensor map as a configuration; silence pass; first alarms), what the operator would see, what it costs (one configuration, no code). A small table: step, input, output, time.
5. Limitations in plain words (simulated data; real building not yet done; slow faults caught late), and next steps (live trial at TRU; the self-healing direction in two sentences).
6. References (about 15–20) and a compact "what is where" box: paper, repository, data.

## 3. Writing rules (the clarity and "AI-sounding" problems)

What reviewers and editors flag as machine-sounding, and the fix used here:
- Every paragraph the same shape (claim, three-part list, qualifier). Fix: vary; some paragraphs are two sentences; one idea each.
- Abstract vocabulary ("falsification protocol", "stratified", "calibrated channels", "noise floor", "artefact"). Fix: say what the thing does ("we wrote down what would prove us wrong before each test"; "a check that only alarms when it beats its own false-alarm rate").
- Numbers in every sentence. Fix: one number per claim, the rest in the table.
- No first person, no concrete scene. Fix: "we seeded a stuck damper and the alarm came up on day one naming zone S" is clearer than any definition.
- Hedging stacked on hedging. Fix: one honest limitation sentence per topic, then move on.
- Restating the point at the end of each paragraph. Fix: stop when the content stops.
- Lists of three everywhere. Fix: lists only when the items are parallel and there are more than three.

Process: draft by hand from the diagram outward (not by condensing the long paper), read aloud,
then a single pass to remove every word the operator would not use. Keep the long paper and the
repository as background references only, as the supervisor asked.

## 4. Open items for the author
- The "TSN example" the supervisor referred to: obtain it, since the report should follow its shape.
- Confirm the TRU building to use for the proof of concept (Campus Activity Centre assumed, from the SES 2022 study).
- Update to the supervisor due next week (by 2026-10-15).
