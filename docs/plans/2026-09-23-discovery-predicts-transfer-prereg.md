# Pre-registration — does discovery predict where a rule transfers?

**Committed 2026-09-23, BEFORE any quantity below is computed.**
Answers the one question left open by the round-1 hostile review: the
discovered process models contribute no detections (0 of 73 scenarios are
detected only by the model/device channels). The surviving claim is that
discovery *locates* invariants — that the models say, in advance, which
building a hand-written rule will hold on. This tests that claim.

## Disclosure of what the author of this document already knows

The drafting agent has seen `matched_rules_*.json` values for MR1's
healthy-year firings (231 / 124 / 0 on SDAHU / PFPU / SFPU) and two
scenario-level identities for MR2 (141 = 141 on SFPU, 206 = 206 on PFPU).
It has NOT seen MR2 or MR3 healthy-year firings on any system, nor MR1's
scenario-level figures beyond one. For that reason:

1. the quantity Q is fixed here before computation and is computed by a
   separate agent forbidden from reading `outputs/matched_rules_*.json`,
   `PHASE*_RESULTS.md`, `RESEARCH_LOG.md`, `README.md`, `MASTER_PLAN.md`,
   or `paper/`;
2. the primary test is over all nine (rule, system) cells, six of which
   are unknown to the drafter;
3. the three MR1 cells are reported as a secondary, disclosed-as-known
   check, never as the headline.

## The rules under test (definitions only, from `scripts/matched_rules.py`)

All three are heating invariants a domain expert wrote AFTER the models
had flagged heating behaviour on one building:

- **MR1** — occupied workday AND `heating_active` never fires that day.
- **MR2** — per-zone `zone_heating_active@<device>` episodes per day
  outside the healthy count band.
- **MR3** — trailing-30-day count of `heating_active` days outside the
  healthy band.

Anchor activity for all three: `heating_active` (unit stratum); for MR2
additionally `zone_heating_active@<device>` where the unit net carries it.

## The model-derived quantity Q (fixed now)

For each system, fit the unit-stratum net on the fault-free year exactly
as `strata.core.pipeline.fit` does (inductive miner, `noise_threshold`
= 0.2, state alphabet only). Then:

- **Q_support(system)** = fraction of healthy *occupied* days whose optimal
  alignment to that net contains a synchronous move on `heating_active`.
  Computed by alignment against the net, not by counting the log, so it is
  a property of the model's reading of the year.
- **Q_obligatory(system)** ∈ {0, 1} = 1 if the net accepts no complete trace
  that omits `heating_active` — operationally: take each healthy variant,
  delete every `heating_active` event, align; if ANY such trace aligns at
  cost 0, the activity is optional and Q_obligatory = 0.

Q for a (rule, system) cell is Q_support(system) for all three rules
(they share the anchor); Q_obligatory is reported alongside as the
structural form.

## Predictions (fixed now)

- **P1 (primary).** Across the nine (rule, system) cells, a transplanted
  rule's healthy-year firing count is monotonically decreasing in
  Q_support: Spearman rho < 0, with permutation p < 0.05 (10,000
  permutations of the nine firing counts across cells).
- **P2 (structural).** Every cell with Q_obligatory = 1 has healthy firings
  = 0; every cell with Q_obligatory = 0 has healthy firings > 0.
- **P3 (secondary, disclosed-as-known).** Q_support orders the three
  systems SFPU > PFPU > SDAHU, matching MR1's known firing order
  0 < 124 < 231.

## Falsifiers (binding)

- **F1.** P1 fails (rho ≥ 0, or permutation p ≥ 0.05) → "discovery predicts
  rule transferability" is dead; the paper reports process mining as
  design-time scaffolding that neither detects nor predicts, and the
  framing follows the protocol-and-refutations line.
- **F2.** P2 fails on any cell → the structural form of the claim is dead;
  only the graded form (P1) may be reported, if it survives.
- **F3.** P1 passes but P3 fails → the claim survives only on the six cells
  the drafter could not have fitted to, and the paper says so.

If P1 passes, the claim is stated narrowly: *on three buildings and three
heating rules, the discovered model's support for an invariant predicted
where the corresponding hand-written rule would false-alarm.* n = 9 cells
from n = 3 buildings; no wider generalisation.

## Artifacts

`outputs/discovery_predicts_transfer.json` (Q per system, firings per cell,
rho, p, P2 table) + guard test pinning the verdict, whichever way it goes.
