# Phase 3b Results — Cross-System Benchmark (2026-08-10, rev 2 post-audit)

Rev 2 supersedes the same-day rev 1 after a hostile audit of the results
(two agents + recomputation from raw data). Every change made the numbers
smaller and the claims harder. The audit record: see the "audit corrections"
section below; the falsifier outcome is reported as a finding, not hidden.

## Infrastructure delivered (unchanged from rev 1)

- day×device-safe holdout split; `device:` tag → device column
- `scripts/benchmark.py <system>` + per-config scenario manifests
- Per-scenario significance vs each channel's own healthy noise floor
  (binomial p<1e-3; rules channel gated by rule-of-three, NOT exempt)
- TTD reported only for meaningful detections; sensor-precision floor
  (0.5 °F) on the residual band; min-robust model counts alongside
  threshold-based counts. SDAHU regression: row-for-row ≡ v5. 55/55 tests.

## Headline results (noise-disciplined, regenerated artifacts)

| | SDAHU | PFPU | SFPU |
|---|---|---|---|
| scenarios meaningfully detected | 14/14 | **17/30** | **18/30** |
| median TTD (meaningful only) | 1–2 d | 1 d | 1 d |
| zone localization, scored scenarios | n/a | 18/18 | 19/19 |
| healthy-year signature days | 0 | 0 | 0 |

Strong families (≈100% alarm-days, TTD 1, correctly localized): reheat
valve stuck, reheat valve leak (waterside rule, all severities), damper
stuck (command-less, via flow tracking), airflow sensor bias.

**Localization is a SPECIFICITY claim, not discrimination**: every LBNL
fault is injected in Zone S (zero ground-truth variance), so correctness
cannot distinguish our localizer from "always answer S." What IS measured:
non-S zone rules fired at most 1 day in 365 across all 61 scenario files —
the localizer is quiet where it should be. Discrimination requires faults
in other zones (future data / TRU).

## The SFPU unit-model finding — honest version

**What is real (recomputed exactly):** SFPU healthy operation has a daily
AHU heating rhythm (357/365 days). Under VAVDMPRStuck 50/80/100 and
VAVAirflow −200/−400, that rhythm goes missing (~270–281 days) because
zone-S over-delivery removes the heating call — physics verified in flow
numbers, coherent with the +bias direction showing no signal, and the
series-topology coupling matches published engineering (Titus; Nailor;
ASHRAE RP-1292). The discovered healthy net flags days where the expected
heating moves are absent.

**Honest magnitudes:** threshold-based counts (135–140 days) are ~80%
attributable to a threshold interpolated off a single holdout day (G2
recurring). The min-robust count — days strictly worse than ANY healthy
holdout day — is **22–26 days per scenario**, still far above the noise
floor. Detection is heating-season-conditional (0 flags in July).

**The pre-registered falsifier FIRED, and we report it:** a one-line
matched rule ("occupied workday AND AHU heating never active") achieves
0/365 healthy false positives and covers 192–194 fault days — more than
the model channel — and a relaxed variant also covers the model's 15–17
unique weekend days. Therefore the defensible claim is NOT "detection no
rule can express." It is: **the discovered model found the load-bearing
healthy rhythm unsupervised — nobody had to know, in advance, that "AHU
heating runs daily" was the invariant a zone damper fault would break.**
The rule exists only after the model showed where to look. (The matched
rule becomes a permanent E2 ablation arm in Phase 4.)

**The PFPU contrast, corrected:** the fault couples into PFPU heating too
(healthy 166 heating-days → 90–92 under fault) — the earlier "parallel
decouples zones" claim was wrong as physics. PFPU's healthy heating has no
daily rhythm, so ORDER-based conformance has nothing to miss. Testable
prediction, pre-registered here: the Phase-4 frequency-aware channel should
see the PFPU heating-day-count collapse that order-only conformance cannot.

## Honest negatives (regenerated, gate applied everywhere)

- Coil fouling: 0/12 meaningful (waterside ΔT channel not yet built)
- Instability: 0/4 meaningful (frequency check is the Phase-4 answer;
  rev 1's "1 of 4" rested on a single rule-day — retracted by the gate)
- RMTEMP bias: 3/8 meaningful, weak and late; −2/−4 °C undetected
  (zone-temp comfort residual is the designed increment). The SFPU −2C
  scenario is excluded from family claims (source file calendar-rotated).
- SFPU residual detections on stuck/leak from rev 1 (21–117 days):
  **retracted** — they rode on 0.02–0.03 °F band exceedances; the 0.5 °F
  sensor-precision floor removes them (now ≤2 days). The rev-1 "residual
  cross-system contrast" was band geometry, not topology; dropped.

## Audit corrections ledger (rev 1 → rev 2)

1. Meaningful counts 20/30, 19/30 → **17/30, 18/30** (rules channel now
   inside the significance gate).
2. Model magnitude: report min-robust 22–26 alongside threshold 135–140;
   "13–14× noise floor" corrected (arithmetic error; it is ~36× on
   threshold counts, ~6× on min-robust).
3. "No rule can express this" → discovery-automation claim (falsifier
   honored).
4. "Parallel decouples" → baseline-irregularity explanation + Phase-4
   prediction.
5. Localization reframed as specificity; "two independent methods agree"
   downgraded (same data, different computations).
6. TTD/detected no longer reported for noise-only scenarios; family labels
   fixed (damper_stuck, not "other"); rotated file footnoted in manifest;
   FPU artifacts regenerated with full provenance.

## Positioning notes (fresh web sweep, 2026-08-10)

- Still nobody publishing on LBNL PFPU/SFPU ("to our knowledge, first").
- Detection-by-absence must be scoped: model-moves exist in BPM alignments
  and DES diagnosers; ours is its first application to discovered healthy
  models for HVAC terminal-unit FDD.
- **ICPM 2027 research track: abstract Sept 4, paper Sept 11, 2026** — the
  natural venue and the operative deadline.
