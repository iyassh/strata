"""Validate event abstraction on the real SDAHU files against the success criteria.

Success = events are discriminative: silent on healthy data, present on the
matching fault. Prints PASS/FAIL per expectation and exits non-zero on failure
so this can gate CI or a benchmark run.
"""

import sys
from pathlib import Path

import pandas as pd

from processheal.hvac.events import abstract_events
from processheal.io.config import load_config

DATA = Path("data/processed/sdahu")
cfg = load_config("configs/lbnl_sdahu")

# file -> {event: expectation}, 0 = never fires, "high" = fires on >=95% of days
CASES = {
    "AHU_annual": {
        "damper_command_mismatch": 0,
        "valve_command_mismatch": 0,
        "valve_leak": 0,
        "setpoint_deviation": 0,  # gated on cooling; must be silent on healthy
    },
    "damper_stuck_075_annual": {"damper_command_mismatch": "high"},
    "coi_stuck_010_annual": {"valve_command_mismatch": "high"},
    "coi_leakage_010_annual": {"valve_leak": "high"},
}

all_pass = True
for fname, expect in CASES.items():
    df = pd.read_parquet(DATA / f"{fname}.parquet")
    log = abstract_events(df, cfg)
    n_days = df["Datetime"].dt.date.nunique()
    counts = log["activity"].value_counts().to_dict()

    print(f"\n=== {fname}  ({n_days} days, {len(log) / n_days:.1f} events/day) ===")
    for act in sorted(counts):
        days_with = log[log.activity == act]["case_id"].nunique()
        print(f"    {act:28s} {counts[act]:>6} events on {days_with:>3} days "
              f"({100 * days_with / n_days:.0f}%)")

    for act, want in expect.items():
        days_with = log[log.activity == act]["case_id"].nunique()
        frac = days_with / n_days
        if want == 0:
            ok = days_with == 0
            print(f"  [{'PASS' if ok else 'FAIL'}] {act}: expected 0 days, got {days_with}")
        else:  # "high"
            ok = frac >= 0.95
            print(f"  [{'PASS' if ok else 'FAIL'}] {act}: expected >=95% of days, "
                  f"got {100 * frac:.0f}%")
        all_pass = all_pass and ok

print(f"\n{'=' * 50}\nALL CHECKS: {'PASS' if all_pass else 'FAIL'}")
sys.exit(0 if all_pass else 1)
