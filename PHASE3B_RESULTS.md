# Phase 3b Results — Cross-System Benchmark (2026-08-10)

First full evaluation on all three systems, one parameterized harness, zero
per-system code. All v5 protocol discipline retained; new: zone localization
(E3) and per-scenario noise-floor significance (no "detected" claim unless a
channel fires significantly above its own healthy holdout rate, binomial
p < 1e-3).

## Infrastructure delivered

- `holdout_mask` handles composite day×device cases (calendar-based: a day
  never straddles the split) — the device-stratum blocker is gone
- `device:` rule tag → `device` column in the event log (localization + 3c)
- `scripts/benchmark.py <system>` + per-config `scenarios.yaml` manifest
- SDAHU regression under the new harness: row-for-row identical to v5
- 55/55 tests

## Headline results (meaningful detections only — noise-floor disciplined)

| | SDAHU | PFPU | SFPU |
|---|---|---|---|
| scenarios meaningfully detected | 14/14 | 20/30 | 19/30 |
| median TTD (meaningful) | 1–2 days | 1 day | 1 day |
| zone localization (scored scenarios) | n/a | **18/18** | **20/20** |
| healthy-year signature days | 0/303 | 0/365 | 0/365 |

Detected at 100% of alarm-days with TTD 1, both FPU systems: reheat valve
stuck (incl. the 0% severity) and leak (all severities, waterside rule).
Detected at ~74–76% of days, TTD 1: damper stuck (command-less! via flow
tracking) and airflow sensor bias. Zone localization is perfect on every
scenario where the pre-registered ground truth permits scoring.

## The Phase 3b discovery: a genuine, system-type-dependent unit-model signal

On SFPU (series fans), the unit-stratum conformance channel fires on
135–140 days for VAVDMPRStuck 50/80/100 and VAVAirflow −200/−400 —
**13–14× its noise floor (1/96 holdout), with 15–17 uniquely-caught days
per scenario** (days neither rules nor residual flagged). Mechanism
(inspected, not guessed): the stuck zone damper disturbs primary flow, the
AHU heating coil stops cycling normally, and `heating_active/inactive` go
MISSING from the day trace (273/365 days) — the healthy net expects the
rhythm; absence drives fitness down. On PFPU the parallel fan decouples
zones from the AHU and the signal does not exist (model ≈ noise there).

This is the first genuinely non-circular process-model contribution in the
project: detection by absence, at the unit level, expressible by no zone
rule, and present only in the topology where physics says it should be.
It is also a measured cross-system CONTRAST — direct input to the Stratum-S
grammar story (the same fault class is unit-visible in series systems and
unit-invisible in parallel ones).

## Honest negatives (pre-registered expectations, now measured)

- **Coil fouling: 0 meaningful detection anywhere** (12 scenarios). As
  pre-registered: needs the waterside ΔT channel (RH_EWT−RH_LWT exists in
  the data, unused). Phase 3c/4 target.
- **Instability (RMTEMP/VAVDMPR Unstable): noise-only on 3 of 4.** As
  pre-registered: these are the count/frequency-check targets (Phase 4
  stochastic conformance). Current channels see levels and order, not rates.
- **RMTEMP bias: asymmetric and weak.** +2/+4 °C meaningful but late
  (rules/residual side-effects); −2/−4 °C noise-only. The unmapped
  ZONE_TEMP comfort-band vs setpoint residual is the designed increment.
- Fault-family coverage claim for the paper: 5 of 8 FPU families
  meaningfully detected today; the 3 misses each have a designed,
  pre-registered channel that is not yet built. No family is written off.

## Watch items (carried into 3c)

1. SFPU residual band is razor-thin ([+1.36, +1.58] °F, 0.22 wide) — ultra-
   stable train medians. Holdout clean (0/41), but fragile under real
   variation; consider a min-width floor derived from sensor precision.
2. `sat_setpoint_deviation` still has no positive-control opportunity on
   FPU (all faults are zone-level); its FPU thresholds are silence-only.
3. The source-rotated SFPU file (RMTEMP −2C) has broken calendar alignment;
   its weak result is not interpretable — excluded from family claims.
4. Economizer window still SDAHU-derived; FPU OA_TEMP is floor-clamped at
   14.00 °F (documented; re-derive per system in 3c).

## Comparison against previous results — consistency ledger

- SDAHU v6 ≡ v5 row-for-row (harness change is non-invasive) ✓
- FPU positive controls (pre-benchmark) match benchmark counts exactly
  (e.g. flow-tracking on damper-stuck-20: 177 days both) ✓
- Week-0 ground truth (Zone S) vs detector localization: agreement on all
  38 scored scenarios ✓ — two independent methods, same answer
- The unit-model null on SDAHU/PFPU and signal on SFPU are all *predicted*
  by the same principle: the unit stratum sees only what couples into
  unit-level rhythm. One principle, three systems, three correct outcomes.
