# Phase 5 audit fixes — status at checkpoint (resume here)

Audit report: in the session log (7 required fixes). Core module fixes are
APPLIED and committed; the runner fixes and final re-run are PENDING.

## DONE (core/grammar.py, committed)
1. Exact 1-Wasserstein via scipy (99-quantile approx underestimated ≤3.9%).
2. `log_profile_distance(activities=...)` for shared-alphabet M3 reporting.
3. `canonical_day_counts(all_days=...)` — raw-calendar day universe (L6
   recurrence fix: zero-canonical-event days become zero rows).

## PENDING (scripts/grammar.py + re-run + docs)
4. M2: compute BOTH full and shared-6-activity matrices + per-activity
   violation decomposition. Reframe: no symmetric "clades" — FPU family
   mutually compatible (0.03); SDAHU nested inside PFPU count space
   (sdahu_on_pfpu 1.00 -> 0.00 shared-6); sdahu_on_sfpu 0.94 behavioral
   (cooling below SFPU min); FPU->SDAHU 0.68/0.94 behavioral.
5. M3: report full + shared-only (audit recomputed: 2.08 / 2.60 / 1.43).
6. Cold-start: (a) target alphabet from CONFIG (rules.yaml), not from the
   target's healthy log; (b) gate detections against the Clopper-Pearson
   95% UPPER bound of the target-holdout fp estimate (audit: SFPU 5/29 ->
   ~1/29 conservative; H-CS = FAIL per pre-registered falsifier; DROP the
   "survives within-family" clause — post-hoc and direction-asymmetric:
   PFPU->SFPU 10/29 but SFPU->PFPU 1/30); (c) qualify "zero-shot" (bands
   zero-shot; alarm gate target-calibrated); (d) store per-scenario k/n.
7. Persist per-day M1 fitness vectors + per-seed null means (L15); add
   top-level caveats (D2 no-independent-negative; day-autocorrelation);
   pass all_days from raw parquet calendars everywhere; fix the wrong
   comment (SFPU has SIX zero-heating train days, not one); label the
   truth-table rhythm row per L21 (instrument fixed after seeing failure;
   target pre-registered; threshold-insensitive 0.90-0.97).
8. Order-claim wording: replace "alphabet-complexity-dependent" with the
   demonstrated facts: FPU nets are REVERSAL-INVARIANT (0.9021->0.9026,
   0.9533->0.9533) = order-vacuous; SDAHU net constrains order (reversed
   0.886->0.553); the genuine cross-system order finding is FPU logs
   beating their shuffles on the SDAHU net (+0.15/+0.18, 99% of days).
9. Re-run `caffeinate -i uv run python scripts/grammar.py`; write
   PHASE5_RESULTS.md from the regenerated artifact (falsifier accounting:
   H-G1 narrow pass, H-G2 pass w/ tautology caveat, H-G3 pass w/ nested
   reframe, H-CS FAIL); update RESEARCH_LOG (L6 + L16-pattern recurrences);
   commit.
