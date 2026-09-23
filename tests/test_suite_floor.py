"""The suite may only grow. A pinned integer trains people to bump it; a
floor catches the real risk (silent deletion of guards) and never fires on
a legitimate addition. Floor = the count at the 2026-09-23 repo audit."""
import subprocess
import sys
from pathlib import Path

FLOOR = 109


def test_collected_tests_at_least_floor():
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "--ignore=tests/test_suite_floor.py"],
                       cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if "collected" in l or "tests collected" in l][-1]
    n = int(line.split()[0])
    assert n >= FLOOR, f"{n} tests collected, floor is {FLOOR} — guards were deleted"
