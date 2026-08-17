# Phase 5 Pre-Registration — The Cross-System Grammar Experiment

*Written and committed BEFORE any cross-replay is computed (rule L9: ground
truth and instruments pre-registered, never read off afterwards). Every
design choice below carries its citation anchor from the guidance sweep.*

## Hypotheses (stated before measurement)

- **H-G1 (shared grammar):** all three systems share a canonical core of
  healthy operation — schedule-driven start/stop with occupancy setting the
  rhythm — visible as high off-diagonal cross-fit in at least one dimension.
- **H-G2 (signatures):** each system type carries dialect features that do
  NOT transfer: SFPU's daily heating rhythm, PFPU's demand-driven fan
  irregularity, SDAHU's no-heating/no-night-cycle profile. Off-diagonal
  deficits must align with these known, already-measured contrasts.
- **H-G3 (counts beat order):** given the measured order-permissiveness
  (97% shuffle-pass), the COUNT dimension will separate systems that the
  order dimension cannot. (Pre-explained by the configuration-model
  framing: order-shuffling preserves exactly what the nets constrain.)
- **H-CS (cold start):** canonical count-bands calibrated on two systems
  detect a usable subset of the third system's faults zero-shot, with a
  quantified degradation delta vs the in-domain detector.

## The instruments (fixed now)

1. **Canonical alphabet projection (pre-registered mapping):**
   system_started/stopped, night_cycle_started/ended, heating_active/
   inactive, cooling_active/inactive, economizer_window_entered/exited —
   projected by identity from each system's unit-stratum state alphabet
   (absent activities stay absent; NO renaming beyond this list; zone/device
   events excluded — the grammar is unit-level). Projection bias is a
   documented pitfall (event-abstraction literature); the null controls it.
2. **Three 3×3 matrices, not one** (flower-vacuity defense; Tax et al. 2018
   says precision measures are unreliable — we do not lean on precision):
   - M1 alignment cross-fitness (log_j on model_i), reported as PER-TRACE
     DISTRIBUTIONS, never bare means (trace-length pitfall).
   - M2 count-band cross-violation rates (system_j's healthy days against
     system_i's canonical count-bands) — the dimension expected to carry
     signal (H-G3).
   - M3 model-free log-to-log distance (per-day activity-count profile EMD
     between systems) — separates "the logs are similar" from "the models
     are permissive" (Chapela-Campa metric family).
3. **The null model (configuration-model style):** within-trace event
   shuffles preserving per-day counts + cross-system trace swaps. What the
   null matrix shares is projection artifact; only structure ABOVE the null
   counts as grammar. (Cecconi et al. permutation precedent; Milo et al.
   analog.)
4. **Engineering-truth validation targets (fixed in advance, all already
   independently measured in Phases 3–4):** series fan schedule-locked vs
   parallel demand-driven; SFPU heating daily (357/365) vs PFPU irregular
   (166/365) vs SDAHU none; night-cycle FPU-only. The discovered canonical
   models must encode these without being told.
5. **Cold-start protocol (mirrors transfer-FDD reporting):** count-bands
   from systems {A,B} → detect on system C's scenario suite; report
   zero-shot scorecard vs C's in-domain scorecard and the DELTA, per
   family, all three leave-one-out rotations. Noise gates identical to
   Phase 4 (channel-noise nulls; rule-of-three floors).

## Pre-registered falsifiers and honesty rules

- If M1's off-diagonal structure does not exceed the null → the order
  grammar is projection artifact; report it dead and let M2/M3 carry.
- If M2's cross-violation matrix shows no system separation → H-G3 fails;
  the grammar claim reduces to the descriptive M3 contrast, stated as such.
- If cold-start detects nothing meaningful → H-CS fails; the portability
  claim stays config-only (as measured), without the day-one story.
- All matrices ship with the calendar caveat (same simulated weather year
  family — favorable to transfer; stated, not hidden).
- Compute-time guard: all runs under caffeinate (L: the sleeping-laptop
  lesson).

## Deliverables

- `core/grammar.py` + `scripts/grammar.py` (matrices, null, cold-start)
- `outputs/grammar_{matrices,null,coldstart}.json` + the paper's headline
  figure data
- PHASE5_RESULTS.md post-audit (the standard hostile audit applies)

## Citation anchors (locked)

Buijs et al. 2011 (cross-org n×n replay lineage) · Leemans et al. EMSC /
Polyvyanyy entropic relevance (stochastic dimension) · Tax et al. 2018
(precision axioms — why we don't lean on precision) · Chapela-Campa et al.
2023 (log-to-log NGD/EMD) · Cecconi et al. 2021 (permutation testing in PM)
· Milo et al. 2002 (configuration-model null analog) · cross-building
transfer-FDD line (B&E 2025; Fan/Liu 2021–23) for cold-start reporting ·
arXiv cs/0010010 (formal-language FDD ancestry for the "grammar" framing —
phrase itself verified unclaimed).

## Paper logistics (from the CFP, verified)

ICPM 2027: ACM single-column, MAX 13 pages incl. references; single-blind;
abstract due Sep 4, full paper Sep 11 (AoE); EasyChair icpm2027;
open-science artifact sharing encouraged (our repo is the artifact);
**generative-AI assistance must be disclosed in the acknowledgments — we
will disclose AI-assisted engineering and analysis plainly.**
