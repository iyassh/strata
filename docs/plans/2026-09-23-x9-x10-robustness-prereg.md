# X9 (sensor noise) and X10 (holdout split) — robustness of the detector claim (pre-registration)

**Written 2026-09-23 (night), before any computation. Committed before the script runs.**

## Why

Every published number comes from noise-free simulation, and the papers say
so as a limitation. Two cheap tests turn the limitation into a measurement:
does the deployed detector survive realistic sensor noise, and does its
false-alarm rate depend on which eight days of each month were held out?

## X9 — sensor noise

Gaussian noise, seeded per file (seed = CRC32 of the file name), added to
every mapped sensor of the pipeline's vocabulary before anything else runs,
on healthy and fault files alike, at a **dose** d ∈ {1, 2, 4}:

| signal family (canonical name pattern) | 1× noise (sd) |
|---|---|
| temperatures (`*_TEMP*`, `*_EWT_*`, `*_LWT_*`) | 0.5 °F |
| flows (`*_FLOW*`, `*_CFM*`) | 2 % of the value |
| positions (`*_POS*`) | 0.01 (clipped to [0, 1]) |
| static pressure (`SA_SP`) | 2 % of the value |
| commands, statuses, occupancy, setpoints | untouched |

1× is a conservative reading of building-grade sensor accuracy (±1 °F, ±2–5 %
flow); 2× and 4× are the stress arms. The detector is **re-fitted on the
noisy healthy year** at each dose (bands recalibrate; that is what a
deployment would do), then every scored scenario is evaluated. Metrics per
dose and system: detected scenarios (of 14 / 30 / 29, naive, matching the
scorecards), and healthy-holdout false-alarm days of the deployed union
(rate advisory excluded).

### Predictions

- **P-X9.1** At 1×, detections change by **≤ 3 scenarios per system** from
  the clean scorecard and the holdout false-alarm rate stays **≤ 10 %** on
  every system.
- **P-X9.2** Degradation is monotone in dose (4× no better than 2× no better
  than 1× on detections, for each system) — a sanity check on the instrument.

### Falsifiers

- **F-X9.a** At 1×, detections fall by > 3 on any system → the published
  detection count is a noise-free artefact for that system; report it as such.
- **F-X9.b** At 1×, holdout false-alarm rate > 10 % on any system → the
  published false-alarm rate is a noise-free artefact for that system.

## X10 — holdout split

Same detector, same data, holdout = the **first** 8 days of each month
instead of the last 8 (the `holdout_mask` used by every channel is swapped
for its mirror; nothing else changes). Metrics as above.

### Predictions

- **P-X10.1** Detections within **± 3 per system** of the scorecards.
- **P-X10.2** Holdout false-alarm rate ≤ 10 % on every system.

### Falsifier

- **F-X10.a** Either prediction false on any system → the published rates
  are split-dependent; report the pair.

## Artefact

`scripts/x9_x10_robustness.py` → `outputs/x9_x10_robustness.json`, guarded by
a test pinning fired/unfired falsifiers. Machine time is printed, not
committed.

## Amendment 1 (2026-09-23, after the SDAHU arms had been seen, before any fan-powered result)

Two review points, recorded before the fan-powered arms are read:

1. **The 2× and 4× arms carry no falsifier.** They are dose-response
   description only; they are reported as such and no verdict rests on
   them. (Position noise at 4× has sd 0.04 against `mode` thresholds of
   0.05 with no dwell, so chatter is expected there; that is what the arm
   will show, not a failure of the detector.)
2. **The noise is i.i.d. per-sample jitter, not bias or drift.** Sensor
   accuracy specifications describe bias and drift; daily medians and
   sustained-window rules average white noise away while edge detectors
   amplify it. X9 therefore measures robustness to **jitter**, not to the
   bias/drift limitation the papers state. A bias/drift arm is future work
   and every sentence quoting X9 will say "jitter".

Predictions, falsifiers and the 1× arm are unchanged. SDAHU arms seen before
this amendment: 14/14 and 1/96 at every dose; 13/14 and 0/96 under the
first-8-days split.

## Errata to this pre-registration (2026-09-23, after review, before any fan-powered result)

- `SA_SP` is mapped on none of the three systems, so the static-pressure row above is dead: static pressure was never perturbed.
- Seeds are per file and shared across doses (common random numbers): the 2×/4× draws are the 1× draws scaled, so the dose arms are perfectly rank-correlated, which strengthens the monotonicity check and is stated wherever they are quoted.
- `clean_detected` is the naive scorecard count (SDAHU 14), not the branch-adjudicated 13; the noisy side uses `evaluate()["detected"]`, which excludes the advisory rate channel, while the clean count reads `meaningful_channels`; no scenario is rate-only on any scorecard, so the baselines coincide today.
- P-X9.1 was coded one-sided (`clean − noisy ≤ 3`); the text is two-sided. Fixed to `abs(...) ≤ 3` before the fan-powered arms were read; F-X9.a stays one-sided as written. The running process carries the old code; predictions are recomputed from the committed systems block with `--from-artefact` when it finishes.

## Amendment 2 (2026-09-23, before any fan-powered result was read)

The single-process run reached the parallel unit's 1× arm and had not
finished it after 2 h 30 (the jitter multiplies state-log events and every
alignment with them); the four arms on two fan-powered units would take
the better part of a day. **Design change, for compute only:** the 2× and
4× stress arms — which Amendment 1 had already made descriptive, with no
falsifier — are dropped on the fan-powered units; they stay on SDAHU. The
1× arm and the mirrored-split arm, which carry every binding falsifier,
are unchanged. The run is restarted as three processes (one per system)
that merge into one artefact; the SDAHU arms seen earlier (14/14 and 1/96
at every dose; 13/14 and 0/96 under the split) are recomputed, not reused.
No fan-powered number had been produced when this was written.

## Amendment 3 (2026-09-23, before any fan-powered result was read)

The per-system fan-powered runs were still inside the 1× arm after 4 h 15;
a timing probe showed a noisy PFPU fit at 334 s and a single noisy scenario
evaluation not finishing in 25 minutes through the alignment-based
channels (the jitter multiplies state events, and alignment cost grows
with trace length and net size). Thirty scenarios × two arms × two
systems is out of reach. **Design change, for compute only, on the
fan-powered units:** the alignment-based channels — model, device, and
the absence channel that reads the device model — are dropped from the
re-fitted detector (`--no-alignment`). On clean data their removal changes
no detection count (the ablation's "conformance sole = 0"; absence is
meaningful on no scenario) and lowers the series unit's holdout
false-alarm days from 4 to 1, so the clean reference for those arms is the
deployed detector minus those channels: detections 23 / 24, holdout FP 5 / 1
of 96. Predictions and falsifiers are otherwise unchanged and are read
against that reference. SDAHU's completed arms, with every channel, stand.
No fan-powered number had been produced when this was written.
