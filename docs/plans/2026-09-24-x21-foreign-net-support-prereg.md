# X21 — can a discovered net's reading of a *foreign* year escape being that year's own count? (pre-registration)

**Written 2026-09-24 after X20 (HEAD af090c2) and before any cross-building
alignment is computed. Committed before the script exists.**

## The question X20 left open

X20 showed that the transfer test's predictor, `Q_support` — the fraction of
a building's occupied days whose optimal alignment to *its own* discovered
net contains a synchronous `heating_active` move — is the building's own
count of heating days on three of four buildings exactly, and differs on the
fourth only through the miner's noise filter. The write-up proposed the one
design that is not circular by construction: fit the net on building A,
replay building B's fault-free state log, and ask whether A's net reads B
differently from B's own count. This pre-registers that computation. It is
cheap (twelve ordered pairs of four buildings; alignments over a few hundred
variants each) and decisive either way.

## Definitions (fixed now)

- Buildings: the four with a heating coil — PFPU, SFPU, DDAHU, FCU.
- Net_A: the unit-stratum net `pipeline.fit` discovers on A's fault-free
  training days (inductive miner, noise 0.2, state alphabet), exactly as
  in the sealed Q computation.
- For each ordered pair (A, B), A ≠ B: align every distinct variant of B's
  fault-free state log to Net_A (same alignment variant as the sealed
  code); `Q_AB` = fraction of B's occupied days whose alignment contains a
  synchronous move on `heating_active`. Activities in B's alphabet that
  Net_A lacks become log moves; that is the point, not a defect.
- `raw_B` = fraction of B's occupied days whose log contains
  `heating_active` (the X20 control).
- Foreign predictor for B: `Q_foreign(B)` = mean of `Q_AB` over the three
  A ≠ B.

## Predictions

- **P1 (bound).** `Q_AB ≤ raw_B` for every pair: a synchronous move needs
  the activity in the trace. (Sanity, not a hypothesis.)
- **P2 (the tautology persists).** For every pair, `Q_AB` is within 0.05 of
  `raw_B` — a foreign net synchronises heating wherever the trace has it,
  so the reading is again the count. If P2 holds, no alignment-based
  support on this alphabet can carry information beyond the count, and
  the "discovery locates invariants" claim has no testable form in this
  framework; X20's control is the final word.
- **P3 (ordering).** `Q_foreign` orders the four buildings as `raw_B` does
  (FCU < PFPU < DDAHU < SFPU) and therefore correlates with MR1 firings
  at rho = −1 like the control.

## Falsifiers (binding)

- **F-X21.a** P2 fails on at least one pair by more than 0.05 → a foreign
  net reads a year differently from its count. Then report `Q_foreign`
  against MR1 with the four-building exact permutation p *and* against
  the control; if the ordering differs from the control's, the difference
  is the first thing in this project that discovery contributes to
  transfer, and it is reported as such with n = 4 stated.
- **F-X21.b** P1 fails → the alignment code or the alphabet mapping is
  wrong; stop and fix before reading anything else.

## What is not claimed

Whatever the outcome, n = 4 buildings; no permutation test over four
buildings can separate two predictors whose rank orderings agree. The
value of X21 is in P2, which is a per-pair identity check, not a
significance test.

## Artefacts

`outputs/x21_foreign_net_support.json`; guard
`tests/test_x21_foreign_net_support.py`.
