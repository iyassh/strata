# Design: The Proof Sprint — demonstrating STRATA's contribution to professors, then reviewers

*Approved 2026-09-11 (brainstorm with Yassh). Bounded: ~2 weeks, ends in a
scheduled meeting with A. Aighobahi & M. Sharma; every deliverable feeds the
UREAP report afterward. Venue submissions are secondary until after the
professor track.*

## Goal

Make the case, with measurements, that STRATA (1) works end-to-end,
(2) is a genuine and unique contribution, and (3) is better than the
traditional ways — where "traditional" means what buildings actually run
(WebCTRL-class rule libraries + operators watching trend graphs) and what
researchers have previously published on these datasets. Also: establish
the ongoing rigorous-testing program so the proof keeps growing.

## The user's framing (the spine of the demo and deck)

Three operator questions, answered in order, with measured evidence:
1. **Can it take the logs?** (raw BMS CSV in, no manual cleanup, gates run)
2. **Can it name the faults automatically?** (named symptom + evidence +
   fault family — the naming layer to be scored, see D3)
3. **Can it say where it's coming from?** (equipment + zone; 37/37 measured)

## Deliverables

### D1 — Traditional-rules baseline (the "what industry runs" proxy)
- **Import, don't write:** `open-fdd` (PyPI, MIT, third-party, actively
  maintained) implements the ASHRAE Guideline 36 AHU fault conditions —
  the same standard WebCTRL advertises compliance with. Using an
  independent implementation kills the strawman objection.
- Adapter maps benchmark columns to open-fdd's expected inputs; **default
  thresholds untouched** (the as-deployed condition). Roll its per-row
  flags to day level; grade on the identical exam (same scenarios, same
  clean years, same day-level scoring harness).
- Honest accounting of fault conditions that cannot run for lack of
  sensors (documented, not hidden).
- Manual graph-watching (the other "traditional way") is dispatched by
  citation: the vendor's own admission that trend-staring doesn't scale.
- Pre-registered falsifier: if the static battery matches STRATA's
  detections at equal false alarms, the "better than traditional" claim
  dies and is reported as such.
- Artifacts: `outputs/openfdd_baseline_*.json` + guard tests + hostile
  mini-audit before any number is quoted.

### D2 — Prior-work audit table
- Literature sweep of every published result on the LBNL SDAHU dataset
  (Chahine & Noura 2026, AFGCN, others); FPU = no prior results (first-ever,
  one row states it).
- Per paper: method, reported result, data usage, capabilities absent
  (explanations / FP budgets / localization) — **plus the audit column:**
  exposure to the dataset defects we documented (ERRATA E1–E5), i.e.
  which published scores may be inflated/invalidated. "Not directly
  comparable" stated where setups genuinely differ (no forced comparisons).
- Deliverable: `paper/PRIOR_WORK_COMPARISON.md`.

### D3 — The three-questions demo + fault-family naming score
- Finish the toolkit `report()` layer: evaluate() output rendered as the
  human alarm (fault name, physical evidence, equipment/zone, FP budget).
- **New measured claim:** a symptom→fault-family attribution layer
  (mapping fired channel patterns to fault families — the mapping already
  exists implicitly in the results) **scored retroactively on all 73
  scenarios**: does the implied family match the seeded fault family?
  Pre-registered; no cherry-picking; misattributions reported.
- Demo script (one command, meeting-playable): raw CSV ingestion with
  gates → train/load frozen → stream a fault year day-by-day → silence on
  healthy days → explained alarm appears. Three fault types shown (rules
  language, physics language, counting language). Localization shown
  (zone/equipment; honest granularity: equipment + zone served, not room
  numbers).
- WebCTRL integration is NOT claimed/tested; one deck slide only: "these
  logs are the same kind of file WebCTRL exports — that's the future
  pilot path."

### D4 — Fourth system, real experimental data (treadmill step one)
- Pick one never-touched LBNL dataset, preferring **experimental
  (FLEXLAB/field) data** to answer the "it's all simulation" caveat —
  candidates: FLEXLAB AHU, fan coil unit; corpus has 7 system families.
- **Go/no-go first (half day):** does the candidate have enough fault-free
  data to calibrate honestly? If no candidate passes, that finding is
  itself reported.
- Protocol: frozen method — config-only onboarding (timed with a
  stopwatch), healthy-silence gate re-run at the dataset's own sampling
  rate (per L31), pre-registered expectations + falsifiers, run once,
  hostile mini-audit, publish whatever happens.
- Framed as step one of the continuous-validation treadmill: each
  validated dataset becomes a permanent regression fixture.

### D5 — The ongoing testing program (regression machinery inside the rigor law)
- **L1 fast guards (every push):** existing 101-test suite (logic + pinned
  published numbers + pinned fired falsifiers) wired into GitHub Actions
  CI with a badge.
- **L2 full re-run gate (before any release/claim):** `scripts/regress.py`
  regenerates all artifacts and diffs against committed — verdict per
  artifact: IDENTICAL or CHANGED; a CHANGED is a bug or a documented,
  committed decision. Never silent.
- **L3 growing exam:** every new validated dataset's artifacts + guards
  are frozen into the suite permanently (proof compounds).
- One-page policy doc; treadmill rule written into MASTER_PLAN.

### D6 — Meeting package
- Deck (~12 slides): problem → framework figure (pointing script) →
  results → three-prong comparison (D1/D2) → demo (D3) → fourth-system
  result (D4) → the evaluation-machine close (D5) → next steps (UREAP
  report, TRU pilot path, venues).
- Q&A prep sheet from the drilled professor questions.
- The send: email Anthony & Medulla with repo + deck + proposed meeting
  dates. The sprint ENDS in a scheduled meeting — no open-ended polishing.

## The rigor law (governs every deliverable)

1. Pre-register expectations + falsifiers before running (committed to git).
2. Every result faces a control/baseline on the same exam.
3. Statistical gates, never eyeballs (channel-noise binomials, p<1e-3).
4. Held-out data only; strictest form = frozen-method run-once (D4).
5. Hostile audit (independent recomputation) before any number is quoted.
6. Every fired falsifier honored in print.
7. Every number regenerable by a stranger from the public repo.

## Explicitly deferred (logged, not done now)
- WebCTRL integration memo/testing (one slide only).
- L24 three-way calibration split; sub-daily rules alert tier;
  robust-quantile calibration; WebCTRL-format ingest adapter — logged in
  MASTER_PLAN.
- Venue submissions (journal route re-planned after the professor track).

## Success criteria
- Meeting held, live demo played, every "better than what exists?"
  question answerable with a number.
- The three operator questions each answered with a measured claim
  (ingestion demonstrated; naming scored on 73 scenarios; localization
  37/37 quoted with scope).
- UREAP report skeleton exists as a byproduct (D1–D5 sections reusable).
- CI badge green; regress.py verdict all-IDENTICAL at sprint end.
