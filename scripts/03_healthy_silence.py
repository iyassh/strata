"""Healthy-silence acceptance gate for a new building config (G1 discipline).

Runs event abstraction on the FaultFree year ONLY and reports, per rule:
- signature events: total firings + distinct days (target: ~zero; anything
  noisy gets its threshold loosened HERE, against healthy data, documented)
- state events: volume stats (events/day) — sanity check that traces stay
  minable (an alphabet that fires thousands of times a day drowns discovery)

Usage: uv run python scripts/03_healthy_silence.py <config_dir> <healthy_parquet>
"""

import sys

import pandas as pd

from processheal.hvac.events import abstract_events, event_alphabet_map
from processheal.io.config import load_config


def main(config_dir: str, parquet: str) -> None:
    cfg = load_config(config_dir)
    df = pd.read_parquet(parquet)
    log = abstract_events(df, cfg)
    amap = event_alphabet_map(cfg)
    n_days = log["case_id"].nunique()

    print(f"config={config_dir} file={parquet}")
    print(f"days with events: {n_days} | total events: {len(log):,}")

    sig = log[log["alphabet"] == "signature"]
    print(f"\n-- SIGNATURE events (target: silence) — {len(sig)} total --")
    if len(sig):
        by = sig.groupby("activity")["case_id"].agg(["count", "nunique"])
        for name, row in by.sort_values("count", ascending=False).iterrows():
            print(f"  {name:28s} {row['count']:>6} events on {row['nunique']:>4} days   <-- TUNE")
    else:
        print("  perfect silence")

    state = log[log["alphabet"] == "state"]
    per_day = state.groupby("case_id").size()
    print(f"\n-- STATE events — {len(state):,} total, "
          f"per-day median {per_day.median():.0f}, p95 {per_day.quantile(0.95):.0f}, "
          f"max {per_day.max()} --")
    by = state.groupby("activity").size().sort_values(ascending=False)
    for name, count in by.items():
        print(f"  {name:28s} {count:>7,}  ({count / n_days:>6.1f}/day)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
