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

## Amendment 1 (2026-09-28 03:40, written after the first run and its two audits, before the re-run)

The first run of the repaired adapter (artefacts of 2026-09-28 02:30–03:17, kept as
`outputs/openfdd_baseline_<system>_run1.json` and `outputs/x38_guideline36_run1.json`)
gave battery healthy-holdout false alarms of 77, 96 and 96 of 96 and gated
detections of 0 on every system; every prediction held. Two independent audits
found adapter defects that make those numbers artefacts of the adapter, and one
defect of the pre-registered design. Nothing from run 1 is quoted. The audits'
findings and the repairs, all applied before the re-run:

**Adapter repairs (audit A items 1–5, 7, 14, 22).**
- A1. SDAHU `fan-cmd` was `SF_SPD`, a constant 0.9 on every row (the project's own
  sensor map records it as dead); FC1's full-speed condition was therefore always
  true. Repaired to `SF_CS`, the speed command. Audit A's recomputation: FC1
  holdout days 77 → 26.
- A2. The terminal-unit rules were fan-gated on the box fan status. On a parallel
  box the plenum fan runs only while heating (30.8 % of occupied minutes), so the
  rules saw only those minutes; on a series box the fan tracks occupancy. Fan
  roles are no longer supplied to the terminal battery on either unit; the
  library's airflow proxy (primary airflow) gates the rules, uniformly.
- A3. PID-HUNT-1 sweeps every mapped control output and read the binary fan
  status as a hunting loop. It now runs on a frame holding the reheat valve only,
  as the pre-registration says.
- A4. `occupied` was `SYS_CTL > 0`, which graded night-cycle (value 2) as occupied
  and applied the 70–75 °F band to setback periods. Now `SYS_CTL == 1`.
- A5. VAV-AHU-LEAVE (box discharge within 8 °F of the AHU supply) is a single-duct
  rule; a fan-powered box mixes plenum air by design and the difference exceeds
  8 °F on about 90 % of healthy running minutes. Recorded not applicable on both
  fan-powered units (F-X38.b class).
- A6. FC6 on SDAHU: `SA_CFM` there is not in cfm (median 4.96 × 10⁵, no documented
  unit); recorded not applicable rather than "not fired".
- A7. STRATA's SDAHU count is quoted as 13 of 14: the outdoor-air-bias detection is
  adjudicated as branch provenance (ERRATA E5, `outputs/x11_branch.json`), as the
  pre-registration's own P1 already assumed.
- A8. The named guard `tests/test_x38_guideline36.py` did not exist; it is written
  with the re-run.

**Design defect (audit A items 10–11): the pooled gate is a tautology.** The
pre-registration gated the battery once, on the union of its rules, against the
union's holdout false alarms. STRATA gates each channel separately and ORs the
verdicts, and when a union flags every healthy holdout day its floor is 1.0 and
nothing can pass. Three framings are therefore reported, and the falsifier
F-X38.a is applied to every one of them:
- G1, as pre-registered: pooled union against the union's holdout false alarms,
  with the symmetric demotion.
- G2, STRATA's per-channel structure: each rule against its own holdout false
  alarms with the same floor max(fp, 3)/96, OR across rules.
- G3, STRATA's rules-channel treatment: a rule that is silent on the healthy year
  (≤ 3 flagged days of 365, the bar STRATA's onboarding applies to its own
  signature rules) is held to the rules channel's 3/365 null; a rule that is not
  silent is excluded, as onboarding would remove it.

**Site-datum arm (audit A item 8).** FC6 compares the temperature-estimated
outdoor-air fraction with `min_cfm_design / total airflow`; the installed default
of 5,000 cfm is about six times the fan-powered air handler's total airflow, so
the rule fires on every running minute. That number is the unit's design minimum
outdoor-air flow, a site datum every deployment supplies, not a tuning threshold.
Arm S runs FC6 with `min_cfm_design` set from the fault-free year (median OA_CFM
over occupied minutes) and every other parameter at its installed default; the
three framings are reported for this arm too. No other parameter is altered in
any arm.

**Predictions for the re-run** (P1–P4 stand as written and are evaluated under
G1; the following are added):
- **P5.** Under G2 the battery detects at least one scenario on SDAHU and STRATA
  still detects at least as many on every system.
- **P6.** Under G3 at most three battery rules per system are silent on the
  healthy year, and the battery's G3 detections are a subset of STRATA's.
- **P7.** Arm S brings FC6's healthy holdout days below 10 of 96 on both
  fan-powered units, and the union's false-alarm rate stays above 30 % because
  VAV-1 and VAV-2 saturate alone.
- Failed P5–P7 are wrong predictions; F-X38.a applies to G1, G2, G3 and arm S.

**Caveats to carry into print regardless of outcome** (audit A items 17–20):
open-fdd 4.4.1's installed defaults are tighter than the Guideline 36 values its
parameter labels cite (the write-up lists them), so the battery is "open-fdd
4.4.1 defaults", not "Guideline 36"; the terminal rules carry fixed comfort bands
(70–75 °F) and flow thresholds that do not read the building's own setpoint
columns; FC4 on SDAHU counts damper crossings because the cooling valve never
reads exactly zero; a battery that flags every healthy day flags every fault day
too, so the raw detection counts of P2 are vacuous.
