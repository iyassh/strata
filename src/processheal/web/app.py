"""ProcessHeal live demo: a FastAPI app that runs the real pipeline interactively."""

from __future__ import annotations

import functools
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from processheal.core.conformance import check_conformance
from processheal.core.detection import build_detector, holdout_mask
from processheal.hvac.events import abstract_events, emitted_event_names, event_sensor_map
from processheal.io.brick import point_to_equipment
from processheal.io.config import load_config

ROOT = Path(__file__).resolve().parents[3]  # processheal/
CONFIG = ROOT / "configs" / "lbnl_sdahu"
DATA = ROOT / "data" / "processed" / "sdahu"
STATIC = Path(__file__).resolve().parent / "static"

cfg = load_config(CONFIG)
p2e = point_to_equipment(CONFIG / "equipment.ttl")

# Discover the healthy model once at startup (a few seconds).
print("ProcessHeal: discovering healthy model ...")
_healthy_log = abstract_events(pd.read_parquet(DATA / "AHU_annual.parquet"), cfg)
_det = build_detector(cfg, _healthy_log)
NET, IM, FM = _det.net, _det.im, _det.fm
THRESH = _det.threshold  # calibrated on held-out healthy days: SAME rule as the benchmark
HEALTHY_FIT = float(_det.holdout_per_day["fitness"].mean())
ACTUATOR = emitted_event_names(cfg, kinds=("mismatch", "leak"))
EV2SENSOR = event_sensor_map(cfg)

# trace variants of the TRAINING days (what the miner actually learned from),
# used by the walkthrough's "healthy days become traces" step
_train_log = _healthy_log[
    ~holdout_mask(_healthy_log["case_id"], cfg.rules["detection"]["holdout_days_per_month"])
]
_variant_counts = (
    _train_log.sort_values(["case_id", "timestamp"])
    .groupby("case_id")["activity"]
    .agg(tuple)
    .value_counts()
)
HEALTHY_VARIANTS = [
    {"trace": list(v), "days": int(c)} for v, c in _variant_counts.head(5).items()
]
N_TRAIN_TRACES = int(_variant_counts.sum())
N_VARIANTS = int(len(_variant_counts))

print(f"ProcessHeal: ready. held-out healthy mean fitness={HEALTHY_FIT:.3f}, "
      f"calibrated threshold={THRESH:.3f}")

app = FastAPI(title="ProcessHeal Live Demo")


def _equipment_for(event: str) -> str:
    sensor = EV2SENSOR.get(event)
    equip = p2e.get(sensor) if sensor else None
    return (equip or "unmapped equipment").replace("_", " ")


SCENARIOS = {
    "AHU_annual": "Healthy (fault-free)",
    "damper_stuck_010_annual": "OA damper stuck 10%",
    "damper_stuck_075_annual": "OA damper stuck 75%",
    "coi_stuck_010_annual": "Cooling valve stuck 10%",
    "coi_stuck_050_annual": "Cooling valve stuck 50%",
    "coi_leakage_010_annual": "Cooling valve leaking",
    "coi_bias_4_annual": "Supply-air sensor bias +4C",
    "coi_bias_2_annual": "Supply-air sensor bias +2C",
}


@app.get("/api/scenarios")
def scenarios() -> list[dict]:
    return [{"file": f, "label": lbl} for f, lbl in SCENARIOS.items()]


@functools.lru_cache(maxsize=16)
def _walkthrough_cached(fname: str) -> str:
    """Compute every stage's REAL artifacts for one representative day."""
    import json

    df = pd.read_parquet(DATA / f"{fname}.parquet")
    log = abstract_events(df, cfg)
    conf = check_conformance(log, NET, IM, FM)
    per_day = conf["per_day"]

    # pick a representative day: prefer a June signature-event day (richer
    # chart), else any signature day, else first fitness-flagged day, else mid-year
    sig_days = sorted(set(log.loc[log["activity"].isin(ACTUATOR), "case_id"]))
    flagged = per_day.loc[per_day["fitness"] < THRESH, "case_id"].tolist()
    june_sig = [d for d in sig_days if "-06-" in d]
    day = (june_sig or sig_days or flagged or [per_day["case_id"].iloc[len(per_day) // 2]])[0]

    day_df = df[df["Datetime"].dt.date.astype(str) == day]

    def series(canon: str):
        col = cfg.sensors.get(canon)
        if col not in day_df.columns:
            return None
        sub = day_df.iloc[::5]  # downsample 1-min -> 5-min for the chart
        return [
            [t.strftime("%H:%M"), round(float(v), 3)]
            for t, v in zip(sub["Datetime"], sub[col])
        ]

    signals = {
        k: series(k)
        for k in ("OA_DMPR_POS", "OA_DMPR_CMD", "CHWC_VLV_POS", "CHWC_VLV_CMD", "OCCUPIED")
    }

    day_log = log[log["case_id"] == day]
    events = [
        {
            "time": ts.strftime("%H:%M"),
            "activity": a,
            "signature": a in ACTUATOR,
        }
        for ts, a in zip(day_log["timestamp"], day_log["activity"])
    ]

    day_conf = check_conformance(day_log, NET, IM, FM) if len(day_log) else None
    day_fitness = day_conf["average_trace_fitness"] if day_conf else 1.0
    unexpected = [
        {"event": e, "count": n, "equipment": _equipment_for(e)}
        for e, n in (day_conf["unexpected_by_activity"] if day_conf else {}).items()
    ]
    missing = [
        {"event": e, "count": n, "equipment": _equipment_for(e)}
        for e, n in (day_conf["missing_by_activity"] if day_conf else {}).items()
    ]
    has_sig = any(e["signature"] for e in events)
    is_flagged = bool(day_fitness < THRESH or has_sig)
    top_equip = (
        next((u["equipment"] for u in unexpected if u["event"] in ACTUATOR), None)
        or (unexpected[0]["equipment"] if unexpected else None)
    )

    bench = None
    row = None
    bench_path = ROOT / "outputs" / "benchmark_v2.json"
    if bench_path.exists():
        b = json.loads(bench_path.read_text())
        s = b["summary"]["combined"]
        bench = {
            "recall": s["recall"],
            "recall_lo": s["recall_ci"][0],
            "recall_hi": s["recall_ci"][1],
            "precision": s["precision"],
            "fpr": s["fpr"],
        }
        row = next((r for r in b["scenarios"] if r["file"] == fname), None)
        if row:
            row = {"days": row["days"], "combined_flagged": row["combined_flagged"]}

    return json.dumps(
        {
            "label": SCENARIOS[fname],
            "day": day,
            "n_day_rows": int(len(day_df)),
            "signals": signals,
            "events": events,
            "n_events": len(events),
            "day_fitness": round(float(day_fitness), 3),
            "threshold": round(float(THRESH), 3),
            "healthy_fitness": round(float(HEALTHY_FIT), 3),
            "flagged": is_flagged,
            "has_signature": has_sig,
            "equipment": top_equip,
            "unexpected": unexpected,
            "missing": missing,
            "n_train_days": _det.n_train_days,
            "n_holdout_days": int(len(_det.holdout_per_day)),
            "day_trace": day_log["activity"].tolist(),
            "healthy_variants": HEALTHY_VARIANTS,
            "n_variants": N_VARIANTS,
            "n_train_traces": N_TRAIN_TRACES,
            "benchmark": bench,
            "scenario_row": row,
        }
    )


@app.get("/api/walkthrough/{fname}")
def walkthrough(fname: str) -> dict:
    """All five pipeline stages, computed from the real pipeline for one day."""
    import json

    if fname not in SCENARIOS:
        return {"error": "unknown scenario"}
    return json.loads(_walkthrough_cached(fname))


@app.get("/api/figure/{name}")
def figure(name: str):
    safe = {
        "benchmark_perday.png",
        "fitness_distributions.png",
        "detector_summary.png",
        "healthy_net.png",
    }
    if name not in safe:
        return {"error": "not found"}
    return FileResponse(ROOT / "outputs" / name)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")


def main() -> None:
    import uvicorn

    uvicorn.run("processheal.web.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
