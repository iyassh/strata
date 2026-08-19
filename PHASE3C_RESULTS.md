# Phase 3c Results — Device Stratum (post-audit, final)

The device stratum (pooled per-device lifecycle models + absence channel)
was built, benchmarked, and then subjected to the standard hostile audit.
This document is the post-audit record; the pre-audit claims lived only in
a commit message and are superseded here.

## What was built

- `core/devices.py`: lifecycle events normalized to class templates
  (zone_fan_S_started → zone_fan_started); healthy traces POOLED across the
  four identical terminal units (one class model, 4× training data);
  conformance scored PER INSTANCE so diagnosis keeps the zone.
- Absence channel: per-device rate of zero-event scheduled days vs that
  device's own healthy silence baseline (train-only calibrated after the
  audit; holdout-validated).
- Pooling homogeneity check (Kruskal-Wallis), wired into every run and
  stored in the artifacts.

## Findings that survived the audit (recomputed from raw data)

1. **First solo device-level catch:** SFPU SensorBias_RMTEMP_−4C —
   undetected by rules, residuals, and the unit model — flags via device
   conformance: 27 days on the CORRECT zone TU_S (36 total). Per-device
   significance p ≈ 5×10⁻¹⁵, robust to holdout-estimation uncertainty and
   Bonferroni across devices. Mechanism verified in traces: heating
   episodes jump 0.45 → 15.5/day in the biased zone (sensor reads low →
   controller over-heats, oscillating). SFPU scorecard: 18 → 19/30.
2. **Dose-response and one-sidedness are coherent:** TU_S flagged days
   fall −4C: 27, −2C: 7, +2C: 2, +4C: 0 (baseline 4). Negative bias ADDS
   events (visible); positive bias REMOVES them (order-blind) — +4C is
   caught by the rules channel instead (zone flow tracking, 99 days).
   Scope: "device channel detects RMTEMP bias" means NEGATIVE bias.
3. **Strong secondary signal with a localization counterexample:**
   VAVDMPRStuck_0% flags 81 device-days on TU_I — the COUPLED NEIGHBOR —
   while the faulted TU_S flags zero (its deviation is event-REMOVAL,
   invisible to the permissive net; the neighbor's is event-ADDITION —
   summer reheat + continuous fan from over-supply, verified). This is a
   localization miss, reported as such; the rules channel (zone flow
   tracking, 302 days, correct zone) remains the localizer.

## Audit corrections applied (the honest ledger)

- **Significance rebuilt per device** (audit A4): the original any-of-4-
  devices day-level test died under noise-floor estimation uncertainty
  (fails at 1.5× the estimated rate). The per-instance test — the
  stratum's own logic — is CI-robust and now standard, with Bonferroni and
  a built-in 2× sensitivity margin.
- **The falsifier fired twice more** (A5, C): train-calibrated one-line
  count rules cover both findings (34 days/0 FP on −4C; 88 days/0 FP on
  stuck-0%, covering all 81 TU_I days). Claim reframed to discovery-
  automation, as in 3b: the pooled models FOUND the per-device count
  invariants unsupervised; the rules exist because the models pointed.
- **The net is order-blind — measured** (D): 97% of randomly shuffled
  healthy traces pass the threshold. What the net actually constrains is
  episode COUNTS (soft cardinality via alignment cost). Both real
  detections are frequency deviations. Consequence embraced: Phase 4's
  frequency channel is the mechanism done properly (and it has since
  confirmed predictions P1/P3 — see Phase 4 results).
- **Threshold honesty** (B): SFPU device threshold rides a discrete
  fitness ladder (robust count 21 vs headline 36 — both reported); the
  PFPU threshold (0.5) is a degenerate min-calibration floor — the device
  channel is near-dead on PFPU by construction, reported as an honest null.
- **TTD contamination fixed** (G): time-to-detection now computed only
  from channels that passed their significance gates (SFPU +4C corrected
  from a phantom day-11 to the true day-108).
- **Absence-channel hygiene** (E): baselines now train-only with holdout
  validation. Status: armed on SFPU (healthy silence 0.0), correctly inert
  on PFPU (fans legitimately silent 28–45% of days), untriggered — no
  benchmark fault fully silences a device. The hard rare-silence gate
  ironically disables the channel on the system whose failure mode
  motivated it; per-device binomial gating is the Phase-4 refinement.
- **Pooling homogeneity** (F): the check existed as dead code with a
  too-weak criterion; now wired with Kruskal-Wallis: SFPU pooling
  statistically clean (H=0.9), **PFPU pooling heterogeneous (H=92.5,
  p≈4×10⁻²⁰)** — the interior zone genuinely differs; caveat attached to
  every PFPU device-stratum statement.
- **Doc correction:** PHASE3B's "RMTEMP bias 3/8 meaningful" was stale;
  the archived rev-2 artifacts say 1/8 (adjudicated from git history).

## Standing verdicts after 3c

- Scorecards: SDAHU 14/14 · PFPU 17/30 · SFPU 19/30 (noise-gated).
  *[stale as of Phase 4 — v12: PFPU 23/30, SFPU 24/29; SDAHU 14/14 is naive, 13/14 adjudicated (X11); quote the addendum]*
- The stratified thesis now has catches at BOTH discovered-model levels
  (unit: heating-rhythm absence; device: per-zone count deviations), each
  honest-sized by its falsifier, each feeding the same conclusion: the
  strata LOCATE invariants; calibrated counting holds them. That
  conclusion is Phase 4's mandate.
