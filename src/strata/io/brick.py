"""Parse a Brick Schema TTL file to map sensor points to their parent equipment."""

from __future__ import annotations

from pathlib import Path

import rdflib

BRICK = rdflib.Namespace("https://brickschema.org/schema/Brick#")


def point_to_equipment(ttl_path: str | Path) -> dict[str, str]:
    """Map each sensor point (e.g. ``OA_DMPR``) to its parent equipment.

    Returns a dict like ``{"OA_DMPR": "Outdoor_Air_Damper", ...}``.
    """
    g = rdflib.Graph()
    g.parse(ttl_path, format="turtle")
    out: dict[str, str] = {}
    for equip, _, point in g.triples((None, BRICK.hasPoint, None)):
        out[str(point).split("#")[-1]] = str(equip).split("#")[-1]
    return out
