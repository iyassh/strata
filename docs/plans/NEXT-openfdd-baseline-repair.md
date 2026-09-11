# PARKED: open-fdd baseline repair (D1 re-run)

**Status: NOT STARTED. Parked 2026-09-11 by user request to work on the paper first.**

> **The three published artifacts `outputs/openfdd_baseline_{sdahu,pfpu,sfpu}.json`
> are VOID. Do not quote any number from them, in any document, until this
> repair is done and re-audited.** Both auditors said so independently.

## Why they are void (hostile audit, 2026-09-11)

1. **Category error (the big one).** PFPU and SFPU are *fan power units* — VAV
   terminal boxes. Every injected fault is a terminal-unit fault (reheat valve
   stuck/leaking, reheat coil fouling, VAV damper unstable, VAV fan restricted,
   VAV airflow sensor bias). They were graded with FC1–FC15, the **air handler**
   battery. Wrong rulebook for the equipment and for the faults.
2. **FC14/FC15 mapped to WATER temps** (`CHWC_EWT/LWT`, `HWC_EWT/LWT`); GL36
   FC14/FC15 are **air-side** rules. `HWC_EWT` is a constant 120 °F placeholder,
   so FC15 fired 365/365 clean days on both FPUs — fabricating the 100% headline.
   Corrected air-side mapping (validated): heating coil entering `MA_TEMP`,
   leaving `HWC_DAT`; cooling coil entering `HWC_DAT`, leaving `CHWC_DAT`.
   FC15 then goes 365 → 0.
3. **Duct static is an additive corruption, not a unit difference.** Constant
   `401.85999`: the healthy file has it added to `SA_SP`; the 20 scenario files
   have it subtracted from `SA_SPSPT`. The pre-reg's pascal/inH₂O story is wrong,
   and its stated justification ("would fire FC1 on every row") was asserted
   untested — unconverted, FC1 is *skipped* (out of open-fdd's valid range).
   Repair additively per file by the sign of `SA_SPSPT`. SDAHU battery FP then
   moves 44.8% → **80.2%**. Confirmed independently by both auditors.
4. **FC6's `min_cfm_design=5000` is a reference value, not a gate** (the pre-reg
   says gate — wrong). FPU airflow tops out at 1896/2757 CFM, so FC6 is
   arithmetically incapable of passing and alarms daily. The promised
   "airflow-units caveat" never made it into any artifact (grep: no matches).
5. **`per_condition` aggregates scenarios only, never the healthy year**, so no
   artifact records *which rule* caused the false alarms — the most load-bearing
   fact in the study is absent by construction.
6. `occupied` is mapped on all three systems but consumed by no FC1–FC15 rule.

## The comparison was also not like-for-like

STRATA's headline FP (1.04% SDAHU) excludes its noisiest channel; the battery's
day-flag ORs all fifteen conditions with nothing held back. Two symmetric
framings are defensible — report both:

| framing | STRATA | battery (as published) | lead |
|---|---|---|---|
| neither side demoted | 15.6% (`union_all8`) | 44.8% | 2.9× |
| both sides demoted | 1.04% (`union_minus_rate`) | 11.5% (minus FC4) | 11.0× |

Recompute both under the **corrected** adapter — the numbers above use the void
artifacts. Note also: on SFPU the rate channel contributes 0 FP days, so the
demotion is a no-op there.

Also disclose: the rate-channel demotion is **post-hoc**, dated to
`MASTER_PLAN.md` commit `e56356f` (2026-08-17 21:50), adopted after the union
numbers were known. Fully disclosed in RESEARCH_LOG L23 and shipped alongside
`union_all8` — disclosed post-hoc, not hidden, but post-hoc.

And: ~90% of SDAHU's battery FP rides on FC4 alone, whose shipped default
(`delta_os_max=5`) is stricter than the GL36 value its own label cites (7).
Nothing was tuned — but say so.

## The repair, in order

1. **Fix the adapter**: air-side FC14/FC15; additive duct-static repair;
   `per_condition` to cover the healthy year too; drop the dead `occupied` map.
2. **Pre-register BEFORE re-running** (new doc, own commit) the equipment-matching
   rule, stated system-agnostically and applied uniformly:
   - air handlers → FC1–FC15
   - VAV terminal units → open-fdd's 16 VAV-applicable rules (`VAV-REHEAT`,
     `VAV-3`…`VAV-7`, `SV-*`, `PID-HUNT-1`, `SCHED-247`)
   Required columns are all present: `RH_VLV`, `VAV_DAT_*`, `VAV_PM_CFM_*`,
   `VAV_DA_CFM_*`, `RM_TEMP_*`.
   Also pre-register the symmetric demotion policy: either both sides may set
   aside their noisiest channel, or neither may.
   **This is the honest test and it may go against us** — the VAV rules are
   purpose-built for exactly these faults, so F1 could fire on one or both FPUs.
   Project law: a fired falsifier is honored in print.
3. **Re-run** all three systems.
4. **Re-audit** (two independent agents; the adapter-fidelity + independent-
   recomputation split worked well).
5. Only then consider more datasets. Do not add systems to a broken comparison.

## Corrections owed to the existing pre-registration

`docs/plans/2026-09-11-openfdd-prereg.md` needs a dated correction notice:
the pascal rationale is wrong and was never tested; the honesty table says FC1
is runnable on SDAHU while the artifact says unrunnable; the FC6 "gate"
mechanism is misdescribed; the promised FC6 caveat was never emitted.

## What is NOT in doubt

- STRATA's own inputs are clean — the 401.86 corruption touches only
  `SA_SP`/`SA_SPSPT`, neither of which is in `configs/lbnl_sdahu/sensors.yaml`.
- The L2 regression gate ran **ALL IDENTICAL, 12 of 12**: every published
  STRATA number still reproduces from source.
- The 110 °F simulation runaway in `AHU_annual` (10 days, 3 in holdout) does not
  contaminate STRATA's published numbers — none appears as an FP in any channel.
