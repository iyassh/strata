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

---

## Amendment 1 — 2026-09-23, BEFORE any Q value was computed

Raised by the computing agent from configuration files alone, before any
fit ran. Recorded here, dated, before the numbers exist.

**A. The seal is narrower than stated.** The disclosure section above
contains MR1's healthy firings (231 / 124 / 0), and the computing agent was
instructed to read this document. So the agent has seen MR1's counts. The
blind-computation property holds ONLY for the six MR2/MR3 cells, which is
the scope items 2–3 above already claim for the primary test. P3 is
therefore not blind at all and is demoted from "secondary check" to
"consistency check on disclosed values". This was the drafter's error.

**B. SDAHU cannot test the claim.** `configs/lbnl_sdahu/rules.yaml` has no
heating rule: the SDAHU sensor map carries a chilled-water valve and no
hot-water valve. `heating_active` therefore never occurs in SDAHU's log,
Q_support(sdahu) = Q_obligatory(sdahu) = 0 by configuration, and MR1 fires
on every occupied SDAHU day because there is no heating to be active — a
fact about the building's equipment, not a prediction by any model.
Including SDAHU would inflate P1 for a reason unrelated to discovery.
**SDAHU's three cells are reported but excluded from P1 and P2.** The
same reasoning retracts the research log's reading of "MR1 fires 231
healthy SDAHU days" as evidence that the models locate invariants: on
SDAHU it is evidence of a missing sensor.

**C. MR2's anchor is not in the unit net.** `zone_heating_active@<device>`
events are device-stratum and are removed before unit discovery, so no
unit net can carry them. MR2's cells use Q_support for `heating_active`
under the shared-anchor simplification already stated; this is disclosed
as a weaker test for MR2 than for MR1/MR3.

**D. Consequence for P1.** P1 is now scored on six cells (MR1–MR3 ×
PFPU/SFPU), in which Q takes only two distinct values. That is a thin
test — two buildings — and the permutation null over six cells is coarse
(p can be no smaller than 1/20 for a perfect ordering). It is reported as
such. If P1 passes it supports the claim on exactly two buildings and
three rules; it cannot support more. **Falsifiers F1–F3 are unchanged in
form and apply to the six-cell test.**

---

## Amendment 2 — 2026-09-23, AFTER computation; a protocol failure, recorded as one

Raised by the round-two hostile review of the paper. Both points are
correct and neither was disclosed at the time.

**A. The amended test could not pass.** Amendment 1 reduced P1 to six cells
in two Q-groups of three. Under that design the smallest exact permutation
p attainable by any data is 3!·3!/6! = 36/720 = **0.05**, and F1 fires at
p ≥ 0.05. Amendment 1 §D recorded the bound ("p can be no smaller than
1/20") and the test was run anyway. The reported p = 0.200 is the floor the
observed firing multiset {124, 1, 0, 0, 0, 0} permits, not a measurement
against a null the design could have rejected. **P(F1 fires) = 1 by
construction. The verdict F1_FIRED licenses no conclusion about whether
discovery predicts transfer.** The nine-cell design had power (minimum p
≈ 0.0006); excluding SDAHU was scientifically correct and destroyed it;
the obligation at that moment was to declare the test unpowered, not to
run it.

**B. The scorer was changed after Q existed without an amendment.** Commit
dbffbbb replaced the pre-registered 10,000-draw Monte Carlo p with exact
enumeration over 720 permutations. Exact enumeration is strictly better
and the change cannot alter the verdict, but it was made as a commit
message rather than as a dated amendment under this document's own
discipline. Recorded here as the deviation it was.

**Disposition.** The artifact keeps the computed values and adds a
`power` block stating the design's minimum attainable p and that the
criterion was unattainable; `conclusion_licensed` is set false. The paper
reports this test as a pre-registered design that, as amended, had no
power — a failure of the protocol's authors, not a refutation of the
claim — and draws no inference from it in either direction. A powered
test needs more buildings and is future work. The descriptive numbers
(SFPU's net treats heating as obligatory; the unit-stratum support equals
the raw log count exactly; the device stratum orders the buildings the
opposite way) are reported as observations, not as a test outcome.
