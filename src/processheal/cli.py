"""ProcessHeal command-line interface: run the full four-stage pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from processheal.core.conformance import check_conformance
from processheal.core.discovery import discover_model, save_model
from processheal.core.report import build_report
from processheal.hvac.events import abstract_events
from processheal.io.brick import point_to_equipment
from processheal.io.config import load_config

app = typer.Typer(help="Process mining for HVAC fault detection.")


@app.callback()
def main() -> None:
    """ProcessHeal: process mining for HVAC fault detection."""


@app.command()
def run(
    config: str = typer.Option(..., help="Building config directory"),
    healthy: str = typer.Option(..., help="Parquet of fault-free reference data"),
    faulty: str = typer.Option(..., help="Parquet of data to diagnose"),
    output: str = typer.Option("outputs/report.md", help="Report output path"),
) -> None:
    """Discover a model from HEALTHY data, diagnose FAULTY data, write a report."""
    cfg = load_config(config)
    p2e = point_to_equipment(Path(config) / "equipment.ttl")
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)

    typer.echo("1/4 abstracting events from healthy data ...")
    healthy_log = abstract_events(pd.read_parquet(healthy), cfg)
    typer.echo("2/4 discovering the Petri-net model ...")
    net, im, fm = discover_model(healthy_log)
    save_model(net, im, fm, "outputs/healthy_net.png", "outputs/healthy_net.pnml")

    typer.echo("3/4 abstracting events from data to diagnose ...")
    faulty_log = abstract_events(pd.read_parquet(faulty), cfg)
    typer.echo("4/4 conformance checking ...")
    conf = check_conformance(faulty_log, net, im, fm)

    md = build_report(conf, cfg, p2e, source=Path(faulty).stem)
    out_path.write_text(md)
    typer.echo(
        f"\nDone. avg per-day fitness = {conf['average_trace_fitness']:.3f}  ->  {output}\n"
        f"Petri net image: outputs/healthy_net.png"
    )


if __name__ == "__main__":
    app()
