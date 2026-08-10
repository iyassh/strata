# ProcessHeal

Process mining for fault detection and diagnosis in building HVAC systems.

ProcessHeal learns a Petri-net model of normal HVAC control behaviour from a
building's own healthy operating data, then uses conformance checking to detect
and localise deviations to specific equipment. It complements the rule-based
fault detection in commercial building automation systems by catching the
behaviour-based, sequence-level faults that fall outside fixed rule libraries.

UREAP 2026, Thompson Rivers University.
Author: Yassh Singh. Supervisors: Dr. Anthony Aighobahi, Dr. Mridula Sharma.

## Pipeline

Sensor CSV → event abstraction → process discovery (Petri net) →
conformance checking → equipment-localised deviation report.

## Quick start

```bash
uv sync
uv run python scripts/00_convert_to_parquet.py     # one-time data prep
uv run pytest                                       # run the tests
uv run processheal run \
  --config configs/lbnl_sdahu \
  --healthy data/processed/sdahu/AHU_annual.parquet \
  --faulty  data/processed/sdahu/damper_stuck_075_annual.parquet
```

## Layout

- `src/processheal/core/` — building-agnostic process mining (discovery, conformance, report)
- `src/processheal/hvac/` — HVAC event-abstraction templates
- `src/processheal/io/` — data loading, config, Brick parsing
- `configs/<building>/` — per-building config: equipment.ttl, sensors.yaml, rules.yaml
- `tests/` — unit and integration tests
