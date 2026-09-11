"""L2 regression gate: regenerate every artifact, diff against committed.

Usage:
  uv run python scripts/regress.py            # diff-only (uses scratch dir)
  uv run python scripts/regress.py --list     # show the artifact->command map

A CHANGED verdict is a bug or a documented, committed decision — never
silent (design: docs/plans/2026-09-11-proof-sprint-design.md, D5).
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# artifact (relative to outputs/) -> command that regenerates it
PIPELINE = {
    "benchmark_v6_sdahu.json": "uv run python scripts/benchmark.py sdahu",
    "benchmark_v6_pfpu.json": "uv run python scripts/benchmark.py pfpu",
    "benchmark_v6_sfpu.json": "uv run python scripts/benchmark.py sfpu",
    "union_fpr_sdahu.json": "uv run python scripts/union_fpr.py sdahu",
    "union_fpr_pfpu.json": "uv run python scripts/union_fpr.py pfpu",
    "union_fpr_sfpu.json": "uv run python scripts/union_fpr.py sfpu",
    "crywolf.json": "uv run python scripts/crywolf.py",
    "sensor_coverage.json": "uv run python scripts/sensor_coverage.py",
    "x11_branch.json": "uv run python scripts/x11_branch.py",
    "x8_contamination.json": "uv run python scripts/x8_contamination.py",
    "x5_severity.json": "uv run python scripts/x5_severity.py",
    "x7_downsample.json": "uv run python scripts/x7_downsample.py",
}


def _flat(d, prefix=""):
    if isinstance(d, dict):
        for k, v in d.items():
            yield from _flat(v, f"{prefix}{k}." if prefix else f"{k}.")
    elif isinstance(d, list):
        for i, v in enumerate(d):
            yield from _flat(v, f"{prefix}{i}.")
    else:
        yield prefix.rstrip("."), d


def artifact_verdict(committed: Path, regenerated: Path) -> str:
    a = dict(_flat(json.loads(committed.read_text())))
    b = dict(_flat(json.loads(regenerated.read_text())))
    diffs = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
    if not diffs:
        return "IDENTICAL"
    return f"CHANGED ({len(diffs)} paths, e.g. {sorted(diffs)[:3]})"


def main() -> int:
    if "--list" in sys.argv:
        for art, cmd in PIPELINE.items():
            print(f"{art:34s} <- {cmd}")
        return 0
    outputs = ROOT / "outputs"
    stash = Path(tempfile.mkdtemp(prefix="regress_committed_"))
    failures = []
    for art, cmd in PIPELINE.items():
        committed = outputs / art
        if not committed.exists():
            print(f"{art:34s} SKIP (no committed artifact)")
            continue
        shutil.copy2(committed, stash / art)
        r = subprocess.run(cmd.split(), cwd=ROOT, capture_output=True, text=True)
        if r.returncode not in (0, 2):  # 2 = a script's falsifier exit, artifact still written
            print(f"{art:34s} RUN-ERROR\n{r.stderr[-500:]}")
            failures.append(art)
            continue
        verdict = artifact_verdict(stash / art, committed)
        print(f"{art:34s} {verdict}")
        if verdict != "IDENTICAL":
            failures.append(art)
            shutil.copy2(stash / art, committed)  # restore committed version
    print(f"\n{'ALL IDENTICAL' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
