# X38 — the Guideline 36 rule battery, repaired: current commercial practice on the same exam (pre-registration)

**Written 2026-09-27 before the repaired adapter is run. The three artefacts
`outputs/openfdd_baseline_{sdahu,pfpu,sfpu}.json` of 2026-09-11 are VOID
(`docs/plans/NEXT-openfdd-baseline-repair.md`) and are replaced by this run.**

## What was wrong, and the repair

The 2026-09-11 run graded the fan-powered units with the air-handler battery
(FC1–FC15) although every seeded fault on them is a terminal-unit fault; mapped
FC14/FC15 to water temperatures although they are air-side rules (a constant
120 °F placeholder made FC15 fire on every day); fed the SDAHU duct static with
its E3 additive constant; and never recorded which rule caused the healthy-year
false alarms. The repaired adapter (`scripts/openfdd_baseline.py`, this commit):

1. **Equipment matching, stated system-agnostically and applied uniformly.** An
   air handler is graded with Guideline 36's FC1–FC15 (open-fdd 4.4.1 installed
   defaults, no parameter altered). A VAV terminal unit is graded with open-fdd's
   terminal-unit rules VAV-1 … VAV-7, VAV-REHEAT and VAV-AHU-LEAVE, run once per
   zone on that zone's columns, plus SCHED-247 and PID-HUNT-1 on the reheat valve.
   The fan-powered datasets contain both an air handler and four terminal units,
   so both batteries run; a day is flagged by the terminal battery if any rule
   fires in any zone, and the per-zone, per-rule counts are recorded.
2. **Air-side FC14/FC15 roles**: cooling-coil entering = `HWC_DAT`, leaving =
   `CHWC_DAT`; heating-coil entering = `MA_TEMP`, leaving = `HWC_DAT`. SDAHU has no
   heating coil and no coil air temperatures: FC5, FC7, FC14, FC15 are recorded as
   not applicable there.
3. **SDAHU duct static repaired additively per file** by the sign of the E3
   constant (healthy file: subtract 401.85999 from `SA_SP`; fault files: add it to
   `SA_SPSPT`), so FC1 runs on values in its valid range.
4. **The healthy year is scored per rule**, so the artefact records which rule
   produced every false-alarm day.
5. The dead `occupied` mapping is dropped; `SYS_CTL` is supplied to SCHED-247 as
   fan status where the rule wants it.

## Scoring (fixed now; the same gate on both sides)

- **Raw framing** (as the 2026-09-11 run defined it): a scenario is detected if any
  applicable rule fires on any of its days; false alarms are the healthy holdout
  days (last 8 of each month) on which any rule fires.
- **Gated framing** (primary): a scenario is detected if its flagged-day count
  clears STRATA's significance gate against the battery's own healthy-holdout
  false-alarm rate — `model_significant(k, n, fp, n_hold)`, p < 10⁻³, floor
  max(fp, 3)/n_hold — exactly the rule every STRATA channel is held to.
- **Demotion, symmetric**: two rows are reported for each side — neither side
  demoted (STRATA `union_all8`; battery, all rules) and both sides demoted (STRATA
  `union_minus_rate`; battery minus its single noisiest rule on the healthy
  holdout, named). No other rule is set aside.

## Predictions (written to be falsifiable in either direction)

- **P1.** On SDAHU the corrected AHU battery's raw healthy-holdout false-alarm rate
  is above 30 % of days (the audit's additive repair alone moved it to 80 %), and
  its gated detection count is below STRATA's 13.
- **P2.** On the fan-powered units the terminal-unit battery detects, raw, at least
  half of the 30 / 29 scenarios (it is purpose-built for reheat and damper faults),
  at a raw false-alarm rate above 10 % of holdout days.
- **P3.** Gated, STRATA detects at least as many scenarios as the battery on each of
  the three systems, at a lower false-alarm rate under both demotion framings.
- **P4.** The battery's gated detections are a subset of STRATA's on the fan-powered
  units except for at most two scenarios, which are named.

## Falsifiers

- **F-X38.a** P3 fails on any system → current practice matches or beats STRATA
  there under the same gate; honoured in print as such, with the scenarios named.
- **F-X38.b** The repaired adapter cannot run a rule for a structural reason on a
  system where the pre-registration expects it → recorded as not applicable, never
  as a null.
- A failed P1, P2 or P4 is a wrong prediction.

## Artefacts

`outputs/openfdd_baseline_{sdahu,pfpu,sfpu}.json` (regenerated; the void ones are
moved to `outputs/void/`), `outputs/x38_guideline36.json` (ledger); guard
`tests/test_x38_guideline36.py`; two independent audits before any number is quoted.
