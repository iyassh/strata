# Phase 2 Results — Analytic-Redundancy Events (2026-08-10)

> **SUPERSEDED — historical record only (banner added 2026-08-18). Never
> quote this document's numbers: (a) its FPR was measured against oa_bias
> as a negative, overturned by F1/ERRATA.md E1; (b) "38–45%" bias recall is
> 39–47% in v12 (windows 137–164 days), with window-conditional recall
> measured at 100%; (c) its residual band was the G1 data-snooped band,
> replaced by the train-only [0.53, 1.37]. Current numbers:
> `outputs/benchmark_v6_sdahu.json` + RESEARCH_LOG Part V addendum.**

**Question:** can physics-residual events catch the sensor-bias family that sequence logic detects at 0%?

**Answer: yes — bias-family recall moved from 0% to 38–45%, with zero cost in false alarms.**

## What was built

Two new rule *kinds* (code written once, instantiable from any building's config):
- `paired_residual` — a physics relation between two sensors must stay inside a healthy band, gated on operating state. Instance: `supply_air_residual` — with the cooling coil off, SA_TEMP − MA_TEMP is just fan heat; a biased SA sensor appears verbatim in this residual.
- `envelope_residual` — a signal must lie between two reference signals. Instance: `mixed_air_envelope` — mixed air is a blend of outdoor and return air.

One free rule (zero code — the existing `mismatch` kind from config): `ra_damper_command_mismatch`, the return-air damper's third actuator pair.

## Method discipline

1. **Signal proven before any rule was written:** measured coil-off residual distributions — healthy median +1.05 °F (fan heat), p1 −2.18, p99.9 +3.02; the ±2 °C biases sit at ±3.6 °F, ±4 °C at ±7.2 °F. Clean separation.
2. **Thresholds grounded in those measurements** (band −2.6…+3.3 °F, sustained 120 min to ride out coil-shutdown transients) — not hand-waved.
3. **Healthy-silence gate passed perfectly:** 0 firings on all 335 healthy days AND 0 on the 351-day independent healthy-like run.
4. **45/45 tests** (12 new: both kinds, gating, transients, alphabet integration).

## Numbers (benchmark v4 vs v3)

| metric | Phase 1 (v3) | Phase 2 (v4) | change |
|---|---|---|---|
| rules-only recall | 69.0% | **81.8%** | +12.8pp |
| rules-only F1 | 0.817 | **0.900** | +0.083 |
| combined recall | 69.4% | **82.2%** | +12.8pp |
| combined F1 | 0.819 | **0.902** | +0.083 |
| FPR (438 healthy days) | 1.1% | 1.1% | none |
| SA bias −4°C recall | 0% | **45%** | +45pp |
| SA bias −2°C recall | 0% | **44%** | +44pp |
| SA bias +2°C recall | 0% | **38%** | +38pp |
| SA bias +4°C recall | 0% | **38%** | +38pp |

Regression check: every stuck/leak scenario stayed at 100%; the model channel is bit-identical to Phase 1 (1.8% recall, 18 unique days) — the alphabet split held; nothing leaked.

## Honest limits

- ~55–60% of bias days remain undetected: the residual is only physics-bound while the coil is **off and the zone occupied**, so summer days with all-day mechanical cooling offer no detection window. Extending the gate to unoccupied hours (recorded SA−MA equals the bias almost all night) is the obvious next increment — deferred until FPU priorities are met.
- The new events are **signature-alphabet** (they are accusations, not behaviour), so they strengthen the rules channel, not the process-mining claim. Detection credit goes to physics, and the paper will say so.
- `mixed_air_envelope` and `ra_damper_command_mismatch` fired on nothing new on SDAHU (expected: oa_bias files contain no fault; RA damper follows its own command when OA is stuck) — their value is portability to FPU, where MA/OA/RA bias faults exist.

## Decision (per the plan's Phase 2 gate)

Gate passed: bias recall moved decisively off zero. Proceed to Phase 3 — FPU onboarding + the device stratum, where the process-mining layer faces its own headroom test.
