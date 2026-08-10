"""Build a human-readable, equipment-localised deviation report.

Equipment names are derived from the building config (event -> sensor via
rules.yaml, sensor -> equipment via the Brick TTL) — no hand-maintained table,
so localisation works on any building whose config is filled in.
"""

from __future__ import annotations

from processheal.hvac.events import event_sensor_map
from processheal.io.config import Config


def _equipment_lookup(cfg: Config, point_to_equip: dict[str, str]):
    ev2sensor = event_sensor_map(cfg)

    def lookup(event: str) -> str:
        sensor = ev2sensor.get(event)
        equip = point_to_equip.get(sensor) if sensor else None
        return (equip or "unmapped equipment").replace("_", " ")

    return lookup


def build_report(conf: dict, cfg: Config, point_to_equip: dict[str, str], source: str) -> str:
    """Render conformance results as a markdown deviation report."""
    lookup = _equipment_lookup(cfg, point_to_equip)
    lines = [
        f"# ProcessHeal deviation report: {source}",
        "",
        f"- Average per-day fitness against the healthy model: "
        f"**{conf['average_trace_fitness']:.3f}** (1.000 = perfect match)",
        f"- Days fully matching the model: {conf['percentage_fitting_traces']:.0f}%",
        "",
    ]

    unexpected = conf.get("unexpected_by_activity", {})
    missing = conf.get("missing_by_activity", {})

    lines += ["## Unexpected behaviour (events the healthy model does not allow)", ""]
    if unexpected:
        for activity, count in unexpected.items():
            lines.append(
                f"- **{lookup(activity)}**: `{activity}` occurred {count} time(s) "
                "that the healthy model did not expect."
            )
    else:
        lines.append("None.")

    lines += ["", "## Missing behaviour (expected by the healthy model, never observed)", ""]
    if missing:
        for activity, count in missing.items():
            lines.append(
                f"- **{lookup(activity)}**: `{activity}` was expected but did not "
                f"occur in {count} day(s)."
            )
    else:
        lines.append("None.")

    if not unexpected and not missing:
        lines += ["", "Behaviour matches the healthy model."]
    return "\n".join(lines)
