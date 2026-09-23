"""The generalisable week-0 gates, run on public process-mining event logs.

Thin wrapper over strata.log_gates (the same code `strata gates` runs):
four of the project's six pre-analysis gates make no reference to HVAC and
apply to any event log — MD5 duplicate files, within-case monotonicity,
calendar sanity, trace hashing. The two HVAC-specific gates do not apply.

    uv run python scripts/gates_public_log.py LOG.xes [LOG2.xes ...]
    -> outputs/gates_public_log.json   (runtime printed, not committed)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from strata.log_gates import run_gates, summary_line  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "gates_public_log.json"


def main() -> int:
    out, results = run_gates([Path(p) for p in sys.argv[1:]])
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    for r in results:
        print(summary_line(r))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
