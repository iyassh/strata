"""Loads a building's configuration: sensor-name mapping and event rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Config:
    """All building-specific knowledge needed by the pipeline."""

    sensors: dict  # canonical name -> CSV column name
    rules: dict  # event thresholds and parameters


def load_config(config_dir: str | Path) -> Config:
    """Read sensors.yaml and rules.yaml from a building's config directory."""
    d = Path(config_dir)
    sensors = yaml.safe_load((d / "sensors.yaml").read_text())["canonical_to_csv"]
    rules = yaml.safe_load((d / "rules.yaml").read_text())
    return Config(sensors=sensors, rules=rules)
