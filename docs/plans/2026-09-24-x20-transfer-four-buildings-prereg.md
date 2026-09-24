# X20 — the sealed transfer test with four scorable buildings, and whether it can mean anything (pre-registration)

**Written 2026-09-24 after X19 (HEAD 50510fc) and before any quantity below
is computed on DDAHU or FCU. Committed before any script is extended.**

## What the papers currently promise

With the dual-duct AHU and the fan coil unit both carrying a heating coil,
the transfer test of `docs/plans/2026-09-23-discovery-predicts-transfer-prereg.md`
has four scorable buildings (PFPU, SFPU, DDAHU, FCU). Its Amendment 3
fixed the unit of replication as the building, so the exact one-sided
permutation floor is 1/4! = 0.042 — "the first design that can attain
p < 0.05," as ERPM and the manuscript say, "not yet run."

## Disclosure: what is already known, and why it matters more than n

Amendment 3 recorded as an observation that "the unit-stratum support
equals the raw log count exactly." Checked today on the committed artefact
and the healthy logs (no new fit): on PFPU, `Q_support` = 0.4548 and the
fraction of occupied days whose *event log* contains `heating_active` is
166/365 = 0.4548; on SFPU 357/365 = 0.9781 both ways. The alignment
contributes nothing: `Q_support` is the log's own count of heating days.
MR1 — the only transplanted rule whose firings vary — counts occupied
workdays on which `heating_active` never fires, which is the complement of
the same day set restricted to workdays. If that identity holds on the two
new buildings, a four-building Spearman between Q and MR1 firings is a
correlation between a quantity and (approximately) its own complement. It
will be perfect, it will attain p = 0.042, and it will not be evidence
that discovery locates invariants. The pre-registration below is written
so that the identity, not the correlation, decides the verdict.

## Procedure

1. Extend the sealed Q computation (`scripts/discovery_predicts_transfer_q.py`)
   and the matched-rule script to DDAHU and FCU without changing any
   definition: unit-stratum net fitted as `pipeline.fit` does; Q_support,
   Q_obligatory, sync_days, occupied_days as before; MR1/MR3 healthy-year
   firings as before (MR2 is device-stratum and was voided by Amendment 3).
2. For each of the four buildings compute, from the state log alone,
   `raw_heating_frac` = occupied days whose log contains `heating_active`
   ÷ occupied days.
3. Score the building-level test: Spearman rho between Q_support and MR1
   healthy firings over four buildings; exact permutation p over 4! = 24
   assignments, one-sided (rho ≤ observed); the attainable floor given the
   observed tie structure is computed and reported before the p.

## Predictions

- **P1 (identity).** `Q_support` = `raw_heating_frac` on DDAHU and on FCU,
  exactly (sync_days = raw count).
- **P2 (the correlation).** If the four MR1 counts are distinct, rho = −1
  and p = 1/24 = 0.042.
- **P3 (obligatory form).** Q_obligatory = 1 on a building iff every
  occupied day of its healthy log contains `heating_active` — again a
  property of the log, not of the miner.

## Decision rule (binding)

- If **P1 holds** on both new buildings: the test is withdrawn as
  uninformative at any n. Its predictor is a re-description of its
  outcome. P2's pass, if it occurs, is reported as the demonstration of
  that fact, never as support for "discovery predicts transfer." The
  papers replace "the first design that can attain p < 0.05, not yet run"
  with this finding, and the manuscript's refuted-hypotheses table gains
  a row.
- **F-X20.a:** P1 fails on either building by more than one day → the
  net's reading of a year differs from the log's count; the alignment
  carries information and the four-building test is informative. Then P2
  is scored as the pre-registered transfer test with n = 4 and its outcome
  reported straight, whichever way it goes.
- **F-X20.b:** P3 fails on any building → the structural form is not a
  log property; report.

## What would be a real test (not run here)

A predictor that is not computed from the log it predicts: fit the net on
building A, replay building B's healthy log, and ask whether A's net
predicts where B's transplanted rule fires. Whether any alignment-based
support can escape being a count of B's log is the open question, and it
is stated as such.

## Artefacts

`outputs/discovery_predicts_transfer_q_four.json`,
`outputs/matched_rules_{ddahu,fcu}.json`,
`outputs/x20_transfer_four.json`; guard `tests/test_x20_transfer_four.py`.
