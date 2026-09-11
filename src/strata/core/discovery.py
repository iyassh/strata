"""Process discovery: learn a Petri-net model of normal behaviour from an event log."""

from __future__ import annotations

import pandas as pd
import pm4py


def discover_model(event_log: pd.DataFrame, noise_threshold: float = 0.2):
    """Discover a Petri net from an event-log DataFrame via the inductive miner.

    Returns ``(net, initial_marking, final_marking)``.
    """
    log = pm4py.format_dataframe(
        event_log,
        case_id="case_id",
        activity_key="activity",
        timestamp_key="timestamp",
    )
    return pm4py.discover_petri_net_inductive(log, noise_threshold=noise_threshold)


def save_model(net, im, fm, png_path: str, pnml_path: str) -> None:
    """Save the discovered model as a PNG image and a PNML file."""
    pm4py.save_vis_petri_net(net, im, fm, png_path)
    pm4py.write_pnml(net, im, fm, pnml_path)
