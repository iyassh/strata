"""STRATA command-line interface.

`strata gates` runs the four log-generic week-0 gates on any XES log.
`strata run` is the original single-model conformance demo, kept for the
record: that detector was refuted (see the paper's refutations), and the
deployed detector is strata.core.pipeline.fit()/evaluate().
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import typer

app = typer.Typer(help="Process mining for HVAC fault detection.")


@app.callback()
def main() -> None:
    """STRATA: process mining for HVAC fault detection."""


@app.command()
def gates(
    logs: list[Path] = typer.Argument(..., help="One or more XES event logs"),
    output: Path = typer.Option(None, help="Write the gate artefact (JSON) here; default: stdout summary only"),
) -> None:
    """Run the four log-generic gates (MD5 duplicates, monotonicity, calendar, trace hashing)."""
    from strata.log_gates import run_gates, summary_line

    out, results = run_gates(list(logs))
    for r in results:
        typer.echo(summary_line(r))
    if out["G1_duplicate_files"]:
        typer.echo(f"G1: duplicate files by MD5: {out['G1_duplicate_files']}")
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(out, indent=2) + "\n")
        typer.echo(f"wrote {output}")


@app.command()
def run(
    config: str = typer.Option(..., help="Building config directory"),
    healthy: str = typer.Option(..., help="Parquet of fault-free reference data"),
    faulty: str = typer.Option(..., help="Parquet of data to diagnose"),
    output: str = typer.Option("outputs/report.md", help="Report output path"),
) -> None:
    """Discover a model from HEALTHY data, diagnose FAULTY data, write a report (refuted demo path)."""
    print("NOTE: `strata run` is the original single-model conformance demo. That detector was "
          "refuted (see paper, Section on refutations): it runs without the alphabet wall, "
          "without the eight calibrated channels, and without noise gates or a false-alarm budget. "
          "For the deployed detector use strata.core.pipeline.fit()/evaluate(). See README.", file=sys.stderr)
    from strata.core.conformance import check_conformance
    from strata.core.discovery import discover_model, save_model
    from strata.core.report import build_report
    from strata.hvac.events import abstract_events
    from strata.io.brick import point_to_equipment
    from strata.io.config import load_config

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
