# Phase 5 Results — The Cross-System Grammar (final, post-audit)

Pre-registered in PHASE5_PLAN.md (commit af4b616, before any computation);
audited hostile; all seven audit fixes applied; artifact regenerated
(`outputs/grammar_results.json`, with per-day vectors, per-seed nulls,
per-scenario k/n, and the standing caveats embedded). Every number below
was independently recomputed by the audit before it was accepted.

## Hypothesis accounting (the pre-registered scoreboard)

**H-G1 (shared grammar) — PASS, narrowly, and only where the plan's
fallback said it might.** The one above-null ORDER structure that crosses
systems: FPU logs replayed on the SDAHU model beat their own shuffles by
+0.18/+0.15 on ~99% of days — a shared start→work→stop alternation grammar
visible to the only net that encodes order. All FPU-model cells are
order-dead (falsifier #1 fired for them; counts carry, below).

**H-G2 (signatures) — PASS, with the tautology caveat stated.** The
discovered artifacts reproduce all four engineering-truth targets without
being told: SFPU heats on 97.8% of days (daily rhythm TRUE — the series
signature), PFPU 46.8% (demand-driven FALSE — parallel), SDAHU none;
night-cycle FPU-only; economizer everywhere it exists. Honesty label
(L21): the presence rows validate the projection, not the models; the
rhythm row is the non-trivial one, and its instrument was corrected after
a first-version failure against a pre-registered target (fraction-based,
threshold-insensitive 0.90–0.97; SFPU has six zero-heating train days).

**H-G3 (counts beat order) — PASS, with the geometry made precise.**
- The decisive instrument is the REVERSAL PROBE, now in the artifact:
  fully reversed healthy traces score IDENTICALLY on the FPU nets
  (0.902→0.903; 0.953→0.953 — certifiably order-vacuous) but collapse on
  the SDAHU net (0.886→0.553 — genuine order constraints). We claim the
  demonstrated facts, not a causal story about alphabet complexity.
- The count matrices carry the cross-system signal — but the audit's
  shared-alphabet control reshaped the headline: **there are no symmetric
  clades.** The honest geometry: {PFPU, SFPU} are a tight mutual family
  (cross-violations 1–3%; shared-alphabet profile distance 0.58); SDAHU is
  a LOW-ACTIVITY DIALECT NESTED inside PFPU's count space (its days
  violate PFPU's shared-alphabet bands 0.0% — the former 1.00 rejection
  was pure alphabet-presence artifact) while remaining behaviourally
  separated in three of four directional cells (SDAHU days violate SFPU
  bands 95% — too few cooling cycles; FPU days violate SDAHU bands 68–94%
  — too many). Both matrices (full and shared-6) ship, with per-activity
  decomposition.

**H-CS (cold-start) — FAIL, cleanly, per its own pre-registered
falsifier.** Under the uncertainty-aware gate (Clopper-Pearson upper bound
on the zero-shot false-alarm estimate — the L16 lesson applied in
advance): 0/14 → SDAHU, 0/30 → PFPU, 1/29 → SFPU. The point-estimate gate's
5/29 was statistically fragile (two detections flipped at 2× the noise
floor) and is reported but not claimed. The portability claim therefore
stays exactly what Phases 3–4 measured: config-only onboarding — without a
day-one zero-shot detection story. "Zero-shot" itself is qualified in the
artifact: bands never touch the target's data; the alarm gate is
calibrated on the target's healthy holdout.

## What Phase 5 contributes to the paper

1. **The reversal probe** — a two-line instrument that certifies whether a
   discovered net encodes order at all; it cleanly split our three models
   and grounds every order claim in the paper.
2. **The corrected grammar figure**: a family + nested-dialect geometry
   across three matrices (order where minable, counts everywhere,
   model-free distances confirming), each cell above a configuration-model
   null or reported dead.
3. **A pre-registered hypothesis failing in public** (H-CS) — the fourth
   falsifier to fire in this project, and the paper reports it with the
   same prominence as the passes.
4. **Engineering truth discovered, not asserted** — the series/parallel/
   AHU contrast read off artifacts the algorithm built unsupervised.

## Ledger notes (recurrences — the honest part)

- **L6 recurred** (day universe from event log; 9 SDAHU holdout days
  vanished silently) — caught by audit, fixed via raw-calendar universes;
  the rule now has a shared helper so the next consumer can't skip it.
- **L16 pattern recurred** (a decision gate on an uncertainty-free noise
  point estimate, in cold-start) — caught, CP-upper gating now standard.
- Two recurrences of logged lessons in one phase: ledger-check-at-design
  (the Phase-4 meta-lesson) is necessary but not yet sufficient; gate
  helpers must ENFORCE rules, not document them.

## Standing caveats (also embedded in the artifact)

Same simulated weather-year family across systems (favorable to transfer);
per-day autocorrelation makes binomial p-values optimistic; SDAHU has no
independent healthy negative (D2); M1 cells cover event-bearing days only
(n per cell stated), count matrices the full raw calendar.
