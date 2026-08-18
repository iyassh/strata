# Onboarding Log — X4 portability evidence

Honest record of what it took to onboard each system. "Config lines" counts
non-comment, non-blank YAML lines. Times reconstructed from git commit
timestamps and session records; future onboardings should log wall-clock
directly.

## lbnl_sdahu (reference system, built during Phases 0-2)
- Not comparable (the pipeline itself was developed against this system).

## lbnl_pfpu (2026-08-10, commits 7715db9 -> aa92970)
- sensors.yaml: **45** canonical mappings AT THE ONBOARDING COMMIT (aa92970;
  corrected 2026-08-18 — the original "48" was a miscount. Today's config
  has 57 mappings + 39 rules after Phase-4 waterside-ΔT and oscillation
  additions; X4 evidence quotes the onboarding-commit numbers)
- rules.yaml: 35 rules (14 state + 21 signature) — all seven+two existing
  kinds, no new kind required
- equipment.ttl: copied from LBNL's published Brick model (0 lines written)
- Code changes attributable to THIS building: none
- Kind-level features added (one-time, reusable by every future building):
  `gates:` list on paired_residual; `stratum:` tag routing
- Healthy-only threshold tuning: 1 rule (sat_setpoint_deviation
  sustained_min 15 -> 30; measured healthy max run 17 min)
- Acceptance: healthy-silence gate PERFECT (0 signature events, 365 days)
- Wall-clock from first FPU commit to gate-pass commit: ~1.5 h, including
  the week-0 audit of all 62 files (dominated by compute, not authoring)

## lbnl_sfpu (2026-08-10, same session)
- sensors.yaml + rules.yaml: derived from lbnl_pfpu (identical point
  schema; 2 comment-line edits) — minutes, not hours
- equipment.ttl: copied from LBNL's published Brick model
- Healthy-only threshold tuning: none needed (PFPU tuning transferred)
- Acceptance: healthy-silence gate PERFECT (0 signature events, 365 days)

## Comparison anchors (from the literature)
- SeeQ (BuildSys '23): AHU fault detection app = 73 LoC in Mortar, 11 in
  Energon, 2 in SeeQ — config-line counting is the field's accepted metric.
- Lin et al. (Energies 2022): median FDD setup cost $13,000/building,
  12 h/building in-house install+configuration labor.
