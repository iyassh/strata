# X34 — component attribution: does the carrying rule point at the seeded component? (pre-registration)

**Written 2026-09-25 morning, before any score is computed.** Question asked by the
project owner: the detector says *where* the fault is (zone-level attribution,
37 of 50 correct, 0 wrong on the fan-powered units); does it also say *which
component*? The alarm names the physical relationship that broke; this test
scores whether that relationship points at the component the fault was seeded in.

## Design (fixed now)

- Universe: every detected scenario on the five simulated systems (158) under
  the final scorecards (`outputs/benchmark_v6_*.json`).
- Carrying rule: the signature rule with the most flagged days on the scenario —
  residual rules from `outputs/x33_residual_credits_<s>.json`, other signature
  rules (mismatch, leak, setpoint deviation) by counting the days on which the
  rule emitted an event (`abstract_events`). If the scenario's credited channels
  contain no rules or residual channel (frequency / oscillation / absence /
  conformance only), the attribution is **unnamed**.
- Each rule maps to a (subsystem, component) by a fixed table written from the
  rule's inputs (e.g. `zone_fan_spf_S` → (zone S, zone fan); `box_static_H_W` →
  (hot deck, static sensor); `chwc_valve_mismatch` → (cooling coil, valve)).
  Each scenario maps to its seeded (subsystem, component) from its file name and
  the LBNL documentation (e.g. `SFPU_VAVFanRestrictFlow` → (zone S, zone fan);
  `DualDuct_SensorBias_HSP_-2inwg` → (hot deck, static sensor)). Both tables are
  in `scripts/component_attribution.py` and are the only judgement in the test.
- Score per detected scenario: **exact** (same subsystem and component), **subsystem**
  (same subsystem, different component — e.g. the coil's valve named for a coil
  fouling), **wrong** (different subsystem), **unnamed**.
- Ties for the carrying rule count as exact if any tied rule is exact, else
  subsystem if any is, else wrong.

## Predictions

- **P1.** Exact component on ≥ 60 % of detected scenarios.
- **P2.** Exact or same subsystem on ≥ 85 %.
- **P3.** Wrong subsystem on ≤ 10 %.
- **P4.** Every sensor-bias scenario detected through a redundant-sensor or
  return-minus-zone residual is exact.

## Falsifiers

- **F-X34.a** P3 fails → the component-level claim is withdrawn; the paper keeps
  the zone-level attribution only and reports the wrong-subsystem rate.
- A failed P1 or P2 is a wrong prediction, reported with the rate observed.

## Artefacts

`outputs/component_attribution.json`; guard `tests/test_component_attribution.py`.
