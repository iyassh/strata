"""Event abstraction: turn continuous HVAC sensor data into a discrete event log.

Rules are read from ``rules.yaml`` and dispatched by their ``kind`` — the code
iterates the config, so adding a rule to the YAML adds it to the pipeline with
no code change. ``sustained_min`` means minutes of CONSECUTIVE violation and is
converted to samples using the data's actual logging interval, so the same
config remains correct on 1-, 5-, or 15-minute data.

Rules whose sensors are not mapped for a building are skipped (portability);
rules with an unknown ``kind`` fail loudly.
"""

from __future__ import annotations

import math

import pandas as pd

from processheal.io.config import Config

# Which rule keys name canonical sensors, per kind (used for availability
# checks and for the event->sensor map that powers equipment localisation).
_SENSOR_KEYS = {
    "occupancy": ["signal"],
    "mode": ["signal"],
    "window": ["signal"],
    "mismatch": ["pos", "cmd"],
    "leak": ["pos", "cmd"],
    "setpoint_deviation": ["meas", "sp"],
    # Analytic-redundancy kinds (Phase 2): physics relations between sensors.
    # These catch faults that produce NO sequence anomaly (e.g. sensor bias:
    # the controller trusts the biased reading, so every recorded value tracks
    # its setpoint and all behavioural rules stay silent).
    "paired_residual": ["a", "b"],
    "envelope_residual": ["signal", "low_ref", "high_ref"],
}

# Sustained-condition kinds emit ONE event per day named after the rule.
_SUSTAINED_KINDS = (
    "mismatch",
    "leak",
    "setpoint_deviation",
    "paired_residual",
    "envelope_residual",
)

# Alphabet split (STRATA v2): `state` events describe what the equipment is
# doing and are the ONLY events model discovery and conformance may see;
# `signature` events are hand-written fault detectors and must never enter
# the discovered model's alphabet, or conformance just re-scores the rules.
# Configs may tag each rule explicitly; untagged rules fall back by kind.
_DEFAULT_ALPHABET = {
    "occupancy": "state",
    "mode": "state",
    "window": "state",
    "mismatch": "signature",
    "leak": "signature",
    "setpoint_deviation": "signature",
    "paired_residual": "signature",
    "envelope_residual": "signature",
}


def rule_alphabet(rule: dict) -> str:
    """A rule's alphabet: explicit ``alphabet:`` tag, else the kind default."""
    return rule.get("alphabet", _DEFAULT_ALPHABET[rule["kind"]])


def event_alphabet_map(cfg: Config) -> dict[str, str]:
    """Map every emitted event name to its alphabet (state | signature)."""
    out: dict[str, str] = {}
    for name, r in cfg.rules["events"].items():
        a = rule_alphabet(r)
        for key in ("on_event", "off_event", "enter_event", "exit_event"):
            if key in r:
                out[r[key]] = a
        if r.get("kind") in _SUSTAINED_KINDS:
            out[name] = a
    return out


def _sample_interval_minutes(dt: pd.Series) -> float:
    """Median spacing between samples, in minutes."""
    diffs = dt.diff().dropna().dt.total_seconds() / 60.0
    return float(diffs.median()) if len(diffs) else 1.0


def _rising_edges(cond: pd.Series) -> pd.Series:
    """True only where a condition turns False->True (never on the first row)."""
    prev = cond.shift(1)
    prev.iloc[0] = cond.iloc[0]  # first row is a state, not a transition
    return cond & ~prev.astype(bool)


def _falling_edges(cond: pd.Series) -> pd.Series:
    prev = cond.shift(1)
    prev.iloc[0] = cond.iloc[0]
    return ~cond & prev.astype(bool)


def _first_sustained_run(cond: pd.Series, min_samples: int) -> int | None:
    """Positional index of the first CONSECUTIVE True-run of >= min_samples."""
    if not cond.any():
        return None
    run_id = (cond != cond.shift()).cumsum()
    for _, grp in cond.groupby(run_id, sort=False):
        if grp.iloc[0] and len(grp) >= min_samples:
            return grp.index[0]
    return None


def _rule_condition(kind: str, r: dict, w: pd.DataFrame) -> pd.Series:
    if kind == "mismatch":
        return (w[r["pos"]] - w[r["cmd"]]).abs() > r["threshold"]
    if kind == "leak":
        return (w[r["cmd"]] <= r["idle_below"]) & (w[r["pos"]] > r["leak_above"])
    if kind == "setpoint_deviation":
        cond = (w[r["meas"]] - w[r["sp"]]).abs() > r["threshold"]
        gate = r.get("gate_signal")
        if gate and gate in w.columns:
            cond = cond & (w[gate] > r["gate_above"])
        return cond
    if kind == "paired_residual":
        # (a - b) must stay inside the healthy band [low, high]; only
        # meaningful while the gate holds (e.g. cooling coil NOT controlling,
        # so no control loop is hiding the residual).
        resid = w[r["a"]] - w[r["b"]]
        cond = (resid < r["low"]) | (resid > r["high"])
        gate = r.get("gate_signal")
        if gate and gate in w.columns:
            if "gate_below" in r:
                cond = cond & (w[gate] <= r["gate_below"])
            if "gate_above" in r:
                cond = cond & (w[gate] > r["gate_above"])
        occ = r.get("occ_signal")
        if occ and occ in w.columns:
            cond = cond & (w[occ] == 1)
        return cond
    if kind == "envelope_residual":
        # signal must lie between its two reference signals (physics: mixed
        # air is a blend of outdoor and return air), with tolerance.
        lo = w[[r["low_ref"], r["high_ref"]]].min(axis=1) - r["tolerance"]
        hi = w[[r["low_ref"], r["high_ref"]]].max(axis=1) + r["tolerance"]
        cond = (w[r["signal"]] < lo) | (w[r["signal"]] > hi)
        occ = r.get("occ_signal")
        if occ and occ in w.columns:
            cond = cond & (w[occ] == 1)
        return cond
    raise ValueError(f"no condition for kind {kind!r}")


def abstract_events(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Convert a continuous sensor frame into an event log.

    Returns a DataFrame with columns ``case_id`` (one day), ``activity`` and
    ``timestamp``.
    """
    s = cfg.sensors
    w = df.rename(columns={v: k for k, v in s.items()}).sort_values("Datetime")
    w = w.reset_index(drop=True)
    w["case_id"] = w["Datetime"].dt.date.astype(str)
    interval = _sample_interval_minutes(w["Datetime"])
    rows: list[tuple] = []

    def emit_edges(mask: pd.Series, activity: str) -> None:
        for ts in w.loc[mask, "Datetime"]:
            rows.append((str(ts.date()), activity, ts))

    def emit_sustained_per_day(cond: pd.Series, activity: str, sustained_min: float) -> None:
        min_samples = max(1, math.ceil(sustained_min / interval))
        for _, grp in w.assign(_c=cond).groupby("case_id", sort=False):
            idx = _first_sustained_run(grp["_c"], min_samples)
            if idx is not None:
                ts = w.loc[idx, "Datetime"]
                rows.append((str(ts.date()), activity, ts))

    for name, r in cfg.rules["events"].items():
        kind = r.get("kind")
        if kind not in _SENSOR_KEYS:
            raise ValueError(f"rule {name!r} has unknown kind {kind!r}")
        # portability: skip rules whose sensors this building does not expose.
        # Gates FAIL CLOSED (gap G8): a rule that declares a gate/occupancy
        # signal is skipped entirely when that signal is unmapped — running it
        # ungated on a new building would be an alarm storm, silently.
        needed = [r[k] for k in _SENSOR_KEYS[kind] if k in r]
        needed += [r[k] for k in ("gate_signal", "occ_signal") if k in r]
        if any(col not in w.columns for col in needed):
            continue

        if kind == "occupancy":
            occ = w[r["signal"]] == 1
            emit_edges(_rising_edges(occ), r["on_event"])
            emit_edges(_falling_edges(occ), r["off_event"])
        elif kind == "mode":
            on = w[r["signal"]] > r["on_above"]
            emit_edges(_rising_edges(on), r["on_event"])
            emit_edges(_falling_edges(on), r["off_event"])
        elif kind == "window":
            in_win = (w[r["signal"]] >= r["low"]) & (w[r["signal"]] <= r["high"])
            emit_edges(_rising_edges(in_win), r["enter_event"])
            emit_edges(_falling_edges(in_win), r["exit_event"])
        else:  # mismatch / leak / setpoint_deviation
            cond = _rule_condition(kind, r, w)
            emit_sustained_per_day(cond, name, r["sustained_min"])

    log = pd.DataFrame(rows, columns=["case_id", "activity", "timestamp"])
    log["alphabet"] = log["activity"].map(event_alphabet_map(cfg))
    return log.sort_values(["case_id", "timestamp"]).reset_index(drop=True)


def state_only(log: pd.DataFrame) -> pd.DataFrame:
    """The state-alphabet slice of an event log — the only slice discovery and
    conformance are allowed to see. Logs without an ``alphabet`` column (built
    before the split) pass through unchanged."""
    if "alphabet" not in log.columns:
        return log
    return log[log["alphabet"] == "state"].reset_index(drop=True)


def emitted_event_names(cfg: Config, kinds: tuple[str, ...] | None = None) -> set[str]:
    """All event names the config can emit, optionally filtered by rule kind."""
    names: set[str] = set()
    for name, r in cfg.rules["events"].items():
        if kinds and r.get("kind") not in kinds:
            continue
        for key in ("on_event", "off_event", "enter_event", "exit_event"):
            if key in r:
                names.add(r[key])
        if r.get("kind") in _SUSTAINED_KINDS:
            names.add(name)
    return names


def event_sensor_map(cfg: Config) -> dict[str, str]:
    """Map every emitted event name to the RAW sensor column that signals it.

    Derived from the config (rule sensor -> canonical name -> raw column via
    sensors.yaml), so equipment localisation works on any building without a
    hand-maintained table.
    """
    out: dict[str, str] = {}
    for name, r in cfg.rules["events"].items():
        kind = r.get("kind")
        primary = {"mismatch": "pos", "leak": "pos", "setpoint_deviation": "meas",
                   "paired_residual": "a", "envelope_residual": "signal"}.get(
            kind, "signal"
        )
        canonical = r.get(primary)
        raw = cfg.sensors.get(canonical, canonical)
        event_names = [r[k] for k in ("on_event", "off_event", "enter_event", "exit_event") if k in r]
        if kind in _SUSTAINED_KINDS:
            event_names.append(name)
        for ev in event_names:
            out[ev] = raw
    return out
