# X37 — a diagnosis layer: signed rule patterns and redundant-pair consensus (pre-registration)

**Written 2026-09-27 before any score is computed. Configurations as of 36b9e6e.**

## Why

X34 showed the carrying rule names the seeded component exactly in 69 % of detections
and the wrong subsystem in 12.7 %, and a read-only pre-analysis showed that the
*unsigned* carrying-rule pattern predicts the fault family in 94 of 144 detections
that have a same-pattern neighbour. The ambiguities are physical and resolvable:
a zone airflow-sensor bias and a stuck zone damper both move `zone_flow_tracking`
but in opposite directions relative to the setpoint; a deck static-sensor bias
moves all four mixing-box residuals together while a stuck zone damper moves one;
a room-sensor bias and an outdoor-air bias both move the supply-air residual but
with different signs against the mixed-air envelope. X37 builds the diagnosis
layer the manuscript names as future work ("mapping symptom-and-channel patterns
to fault families") from three ingredients only, all computed from the scorecards
and the fault-free bands, with no fault-specific tuning:

1. **Signed pattern.** For every significant rule on a detected scenario, the sign
   of the scenario's median residual relative to the healthy band (above / below;
   mismatch and leak rules are unsigned). The pattern is the set of (rule stem,
   sign) pairs, zone suffixes stripped.
2. **Redundant-pair consensus.** For rule groups that are copies of one quantity
   (the four mixing-box statics per deck, the four box entering-air temperatures
   per deck, the four return-minus-zone residuals), if every copy moves in the
   same direction the diagnosis points at the *shared* end (the deck sensor, the
   return-air sensor); if one copy moves alone it points at that zone.
3. **Nearest-pattern family and component.** Leave-one-out over the 158 detected
   scenarios: the diagnosis of a scenario is the majority family (and component)
   among the other scenarios of the same system whose signed pattern matches
   exactly, else the closest pattern by Jaccard similarity above 0.5, else
   "unresolved".

Family labels are the scenario file's family (`configs/lbnl_<s>/scenarios.yaml`)
refined by direction word where the file name carries one (airside/waterside,
cooling/heating); component labels are those of X34.

## Predictions

- **P1.** Leave-one-out family accuracy ≥ 80 % over detected scenarios that are not "unresolved"; unresolved ≤ 15 %.
- **P2.** Component accuracy (X34's "exact") rises from 69 % to ≥ 78 % with the consensus rule, and the wrong-subsystem rate falls below 10 %.
- **P3.** The five dual-duct zone-damper cases X34 scored wrong resolve to a single zone's box (consensus fails, one copy moves) and the eight deck-sensor biases to the deck (all four copies move).
- **P4.** The fan coil unit's cause-versus-response cases remain unresolved at component level (no redundant copy exists), and are reported as such.

## Falsifiers

- **F-X37.a** P1 fails → the diagnosis layer is reported as not adoptable; the paper's future-work sentence stands.
- **F-X37.b** P2 fails on the wrong-subsystem rate → the component claim stays withdrawn.
- A failed P3 or P4 is a wrong prediction.

## Artefacts

`outputs/x37_diagnosis.json`; guard `tests/test_x37_diagnosis.py`; script `scripts/x37_diagnosis.py`.
