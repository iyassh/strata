"""Phase 5 runner — pre-registered grammar experiment, post-audit version.

All seven audit fixes are in (see PHASE5_AUDIT_TODO.md): raw-calendar day
universes (L6), full + shared-alphabet M2/M3, Clopper-Pearson-gated
cold-start with config-derived target alphabet, per-day artifact
persistence (L15), the reversal probe that grounds the order claims, and
the standing caveats in the artifact itself.

    caffeinate -i uv run python scripts/grammar.py
"""

import json
import os
import sys
import warnings
from math import comb
from pathlib import Path

os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")

import pandas as pd
import yaml
from scipy.stats import beta as beta_dist

sys.path.insert(0, "src")

from processheal.core.grammar import (CANONICAL, band_violation_days, canonical_day_counts,
                                      canonical_log, count_bands, fitness_distribution,
                                      log_profile_distance, shuffle_within_traces,
                                      split_train_holdout)
from processheal.core.discovery import discover_model
from processheal.core.conformance import check_conformance
from processheal.hvac.events import abstract_events
from processheal.io.config import load_config

SYSTEMS = ["sdahu", "pfpu", "sfpu"]
HEALTHY = {"sdahu": "AHU_annual", "pfpu": "PFPU_FaultFree", "sfpu": "SFPU_FaultFree"}
NULL_SEEDS = [11, 22, 33, 44, 55]


def binom_sf(k, n, p):
    if n <= 0:
        return 1.0
    return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(min(k, n), n + 1))


def cp_upper(k, n, conf=0.95):
    """Clopper-Pearson upper bound on a rate (audit: gates must survive
    noise-floor estimation uncertainty — the L16 lesson, again)."""
    if n == 0:
        return 1.0
    if k >= n:
        return 1.0
    return float(beta_dist.ppf(1 - (1 - conf) / 2, k + 1, n - k))


def config_canonical_alphabet(cfg) -> set:
    """Canonical activities this CONFIG can emit (day-one knowledge; the
    audit caught the code using the target's healthy LOG instead)."""
    out = set()
    for r in cfg.rules["events"].values():
        for key in ("on_event", "off_event", "enter_event", "exit_event"):
            if key in r and r[key] in CANONICAL:
                out.add(r[key])
    return out


def raw_days(df: pd.DataFrame) -> list:
    return sorted(set(df["Datetime"].dt.date.astype(str)))


print("=" * 90)
print("Phase 5 — cross-system grammar (post-audit runner)")
print("=" * 90)

data = {}
for s in SYSTEMS:
    cfg = load_config(f"configs/lbnl_{s}")
    df = pd.read_parquet(f"data/processed/{s}/{HEALTHY[s]}.parquet")
    days = raw_days(df)
    log = canonical_log(abstract_events(df, cfg))
    hn = cfg.rules["detection"]["holdout_days_per_month"]
    train, hold = split_train_holdout(log, hn)
    counts = canonical_day_counts(log, all_days=days)  # L6: raw calendar
    hold_days = set(pd.Series(days)[__import__("processheal.core.detection",
                    fromlist=["holdout_mask"]).holdout_mask(pd.Series(days), hn)])
    tmask = ~counts.index.astype(str).isin(hold_days)
    data[s] = {
        "cfg": cfg, "hn": hn, "train": train, "hold": hold, "days": days,
        "counts_train": counts[tmask], "counts_hold": counts[~tmask],
        "alphabet_log": sorted(log["activity"].unique()),
        "alphabet_cfg": sorted(config_canonical_alphabet(cfg)),
        "n_event_days": int(log["case_id"].nunique()),
    }
    print(f"[{s}] cfg alphabet {len(data[s]['alphabet_cfg'])}/10 | event days "
          f"{data[s]['n_event_days']}/{len(days)} | hold days {len(hold_days)}")

SHARED = sorted(set.intersection(*[set(data[s]["alphabet_cfg"]) for s in SYSTEMS]))
print(f"shared config alphabet ({len(SHARED)}): {SHARED}")

for s in SYSTEMS:
    net, im, fm = discover_model(data[s]["train"][["case_id", "activity", "timestamp"]])
    data[s]["model"] = (net, im, fm)
    data[s]["bands"] = count_bands(data[s]["counts_train"])
    data[s]["bands_shared"] = {k: v for k, v in data[s]["bands"].items() if k in SHARED}

# ---- M1 + null + reversal probe ----
M1, M1_null, M1_perday = {}, {}, {}
for i in SYSTEMS:
    net, im, fm = data[i]["model"]
    for j in SYSTEMS:
        cell = f"{j}_on_{i}"
        conf = check_conformance(data[j]["hold"][["case_id", "activity", "timestamp"]], net, im, fm)
        M1[cell] = fitness_distribution(conf["per_day"])
        M1_perday[cell] = {r["case_id"]: round(float(r["fitness"]), 4)
                           for _, r in conf["per_day"].iterrows()}
        seed_means = []
        for seed in NULL_SEEDS:
            sh = shuffle_within_traces(data[j]["hold"], seed)
            nc = check_conformance(sh[["case_id", "activity", "timestamp"]], net, im, fm)
            seed_means.append(round(float(nc["per_day"]["fitness"].mean()), 4))
        nm = sum(seed_means) / len(seed_means)
        M1_null[cell] = {"seed_means": seed_means, "null_mean": round(nm, 4),
                         "observed_mean": M1[cell]["mean"],
                         "order_signal": round(M1[cell]["mean"] - nm, 4)}
        print(f"M1 {cell:16s} mean {M1[cell]['mean']:.3f} null {nm:.3f} "
              f"order {M1_null[cell]['order_signal']:+.3f}")

REVERSAL = {}
for s in SYSTEMS:
    net, im, fm = data[s]["model"]
    rev = data[s]["hold"].sort_values(["case_id", "timestamp"],
                                      ascending=[True, False]).reset_index(drop=True)
    rev["timestamp"] = data[s]["hold"].sort_values(["case_id", "timestamp"])["timestamp"].values
    rc = check_conformance(rev[["case_id", "activity", "timestamp"]], net, im, fm)
    REVERSAL[s] = {"original_mean": M1[f"{s}_on_{s}"]["mean"],
                   "reversed_mean": round(float(rc["per_day"]["fitness"].mean()), 4)}
    print(f"reversal {s}: {REVERSAL[s]['original_mean']:.3f} -> {REVERSAL[s]['reversed_mean']:.3f}")

# ---- M2 full + shared ----
M2 = {}
for variant, bkey in (("full", "bands"), ("shared", "bands_shared")):
    for i in SYSTEMS:
        for j in SYSTEMS:
            v = band_violation_days(data[j]["counts_hold"], data[i][bkey])
            # per-activity decomposition
            m = data[j]["counts_hold"].reindex(columns=list(data[i][bkey]), fill_value=0)
            dec = {}
            for a, (lo, hi) in data[i][bkey].items():
                viol = int(((m[a] < lo) | (m[a] > hi)).sum())
                if viol:
                    dec[a] = viol
            M2[f"{variant}:{j}_on_{i}"] = {
                "violation_rate": round(float(v.mean()), 4) if len(v) else None,
                "n_days": int(len(v)),
                "by_activity": dict(sorted(dec.items(), key=lambda kv: -kv[1])[:4]),
            }
print("\nM2 (full | shared-alphabet):")
for i in SYSTEMS:
    row_f = " ".join(f"{M2[f'full:{j}_on_{i}']['violation_rate']:.2f}" for j in SYSTEMS)
    row_s = " ".join(f"{M2[f'shared:{j}_on_{i}']['violation_rate']:.2f}" for j in SYSTEMS)
    print(f"  bands of {i:6s}: full [{row_f}]  shared [{row_s}]  (cols: {SYSTEMS})")

# ---- M3 full + shared ----
M3 = {}
for i in SYSTEMS:
    for j in SYSTEMS:
        M3[f"full:{i}_vs_{j}"] = log_profile_distance(data[i]["counts_train"], data[j]["counts_train"])
        M3[f"shared:{i}_vs_{j}"] = log_profile_distance(data[i]["counts_train"],
                                                        data[j]["counts_train"], activities=SHARED)
print("\nM3 shared-alphabet distances:")
for i in SYSTEMS:
    print("  " + " ".join(f"{M3[f'shared:{i}_vs_{j}']:.2f}" for j in SYSTEMS) + f"  <- {i}")

# ---- engineering truth (L21-labeled) ----
truth = {"_label": ("L21: the rhythm instrument (active-day fraction >= 0.95) was fixed "
                    "after its first version (train-min) failed on a pre-registered target "
                    "(SFPU 357/365); verdict threshold-insensitive across 0.90-0.97. "
                    "Presence rows validate the projection, not the models; only the "
                    "rhythm row is non-trivial.")}
for s in SYSTEMS:
    ct = data[s]["counts_train"]
    heat_frac = float((ct["heating_active"] > 0).mean()) if "heating_active" in ct.columns else 0.0
    truth[s] = {"has_night_cycle": "night_cycle_started" in data[s]["alphabet_cfg"]
                                   and "night_cycle_started" in data[s]["alphabet_log"],
                "has_heating": "heating_active" in data[s]["alphabet_log"],
                "heating_active_day_fraction": round(heat_frac, 3),
                "heating_daily_rhythm": bool(heat_frac >= 0.95),
                "has_economizer": "economizer_window_entered" in data[s]["alphabet_log"]}
    print(f"truth {s}: {truth[s]}")

# ---- cold-start (CP-gated, config alphabet, k/n persisted) ----
coldstart = {}
for target in SYSTEMS:
    sources = [s for s in SYSTEMS if s != target]
    shared_cs = (set(data[sources[0]]["bands"]) & set(data[sources[1]]["bands"])
                 & set(data[target]["alphabet_cfg"]))
    bands = {a: (min(data[sources[0]]["bands"][a][0], data[sources[1]]["bands"][a][0]),
                 max(data[sources[0]]["bands"][a][1], data[sources[1]]["bands"][a][1]))
             for a in shared_cs}
    fp_v = band_violation_days(data[target]["counts_hold"], bands)
    k_fp, n_fp = int(fp_v.sum()), int(len(fp_v))
    p0_point = max(k_fp / max(n_fp, 1), 3.0 / 365.0)
    p0_upper = max(cp_upper(k_fp, n_fp), 3.0 / 365.0)
    manifest = yaml.safe_load(Path(f"configs/lbnl_{target}/scenarios.yaml").read_text())
    rows, det_point, det_upper, tot = [], 0, 0, 0
    fam_u = {}
    for sc in manifest["scenarios"]:
        if sc.get("exclude"):
            continue
        df = pd.read_parquet(f"data/processed/{target}/{sc['file']}.parquet")
        counts = canonical_day_counts(abstract_events(df, data[target]["cfg"]),
                                      all_days=raw_days(df))
        v = band_violation_days(counts, bands)
        k, n = int(v.sum()), int(len(v))
        sp = binom_sf(k, n, min(p0_point, 1.0)) < 1e-3
        su = binom_sf(k, n, min(p0_upper, 1.0)) < 1e-3
        tot += 1
        det_point += int(sp)
        det_upper += int(su)
        f = fam_u.setdefault(sc["family"], [0, 0])
        f[1] += 1
        f[0] += int(su)
        rows.append({"file": sc["file"], "family": sc["family"], "k": k, "n": n,
                     "sig_point": sp, "sig_cp_upper": su})
    coldstart[target] = {
        "sources": sources, "band_activities": sorted(shared_cs),
        "note": ("bands are zero-shot (source train data only); the ALARM GATE is "
                 "target-calibrated (fp estimated on the target's healthy holdout)"),
        "fp_holdout": [k_fp, n_fp], "p0_point": round(p0_point, 4),
        "p0_cp_upper": round(p0_upper, 4),
        "detected_point_gate": det_point, "detected_cp_gate": det_upper, "of": tot,
        "per_family_cp_gate": {k: f"{a}/{b}" for k, (a, b) in sorted(fam_u.items())},
        "scenarios": rows,
    }
    print(f"cold-start -> {target}: point-gate {det_point}/{tot} | CP-gate {det_upper}/{tot} "
          f"(fp {k_fp}/{n_fp}, p0 {p0_point:.3f}/{p0_upper:.3f})")

Path("outputs").mkdir(exist_ok=True)
Path("outputs/grammar_results.json").write_text(json.dumps({
    "caveats": [
        "SDAHU has no independent healthy negative run (D2); its fp estimates share the calibration year.",
        "Per-day flags are autocorrelated (weather); binomial p-values are optimistic (stated limitation).",
        "All systems share the same simulated weather-year family - favorable to transfer; stated.",
        "M1 alignment cells cover event-bearing days only (n stated per cell); count matrices cover the full raw calendar (L6).",
    ],
    "canonical_alphabet": CANONICAL, "shared_config_alphabet": SHARED,
    "alphabets_cfg": {s: data[s]["alphabet_cfg"] for s in SYSTEMS},
    "event_days": {s: [data[s]["n_event_days"], len(data[s]["days"])] for s in SYSTEMS},
    "bands": {s: data[s]["bands"] for s in SYSTEMS},
    "M1": M1, "M1_null": M1_null, "M1_perday": M1_perday, "reversal_probe": REVERSAL,
    "M2": M2, "M3": M3, "engineering_truth": truth, "coldstart": coldstart,
}, indent=2))
print("\nwrote outputs/grammar_results.json")
