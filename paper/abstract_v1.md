# ICPM 2027 Abstract — v1 (2026-08-19, for mentor review)

**Target:** ICPM industry/case-study track (abstract due Sep 4, paper
Sep 11, 2026; ACM 1-column, ≤13 pp, AI-use disclosure in acknowledgments).
Every number below quotes RESEARCH_LOG Part V addendum / committed
artifacts. ~250 words.

---

## Discovery Locates, Calibration Detects: Stratified Process Models for Building HVAC Fault Detection

Building HVAC fault-detection tools face a trust problem: rule libraries
flood operators with unexplained alarms, and machine-learning detectors
flag anomalies they cannot name. We present STRATA, a framework in which
process models discovered from fault-free operation **locate** a
building's behavioural invariants — which device, which unit, which
operating regime — while calibrated, physically interpretable channels
**detect** violations of them, so every alarm ships with a name, an
explanation, and a false-positive budget.

On three public LBNL benchmark systems (a single-duct AHU and two
fan-powered-unit types never before benchmarked), STRATA detects 13 of 14,
23 of 30, and 24 of 29 fault scenarios at a median time-to-detect of one
day, with a measured joint false-alarm budget of 1.0–5.2% of fault-free
days and a cry-wolf ratio below 0.1%. A matched-rule control shows the
discovered models' value is *discovery automation*: hand-written twins
match individual channels only after the models reveal where each
invariant holds — transplanted blindly, they false-alarm on up to 231
days per year.

The evaluation protocol is itself a contribution: pre-registered
falsifiers whose every firing is honored in print — including one that
revealed a 14th "detection" to be an artifact of a previously
undocumented dataset defect — a measured 3.4-percentage-point circularity
bound on model self-confirmation, five machine-verified errata for the
most widely used public FDD datasets, and full reproducibility: every
table regenerates from the public repository's documented runbook.

---

## Notes for Anthony & Medulla (not part of the abstract)

- The "13 of 14" is deliberate honesty: our detector initially scored
  14/14, but our own audit protocol discovered the healthy training file
  was simulated under a different configuration than the fault files
  (dataset erratum E5), and one "detection" was provenance, not fault.
  We adjudicated it away and report both numbers. Reviewers reward this;
  it is the paper's character witness.
- Framing follows the program-committee simulation: methodology-first
  ("discovery locates, calibration detects"), never "first process
  mining for FDD."
- Terminology: "fault-free/baseline training" (community standard), not
  "healthy-only". "Stratified" is unclaimed in process mining.
- Word budget: ~255; ICPM abstracts are typically 150–300.
- Self-review 2026-08-19: removed an unverifiable falsifier count ("six"),
  a premature "one command" claim (that CLI is toolkit work in progress),
  and "strongest detection" puffery — every remaining number traces to
  RESEARCH_LOG Part V addendum.
- Ask: does the framing land for a building-science reader? Is anything
  overclaimed or underclaimed? Reply-by hoped: Aug 25, so v2 can loop
  once more before Sep 3 submission (one day early per project law).
