"""Paper figures, regenerated from committed artefacts only (no recomputation).

    uv run python scripts/make_figures.py -> paper/figures/fig_*.pdf (+ .png previews)

Every number drawn here is read from outputs/*.json; the script never opens a
parquet file, so a figure can only show what an artefact records.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
SYSTEMS = [("sdahu", "SDAHU"), ("pfpu", "PFPU"), ("sfpu", "SFPU"), ("ddahu", "DDAHU"), ("fcu", "FCU"), ("rtu_sim", "RTU (sim.)")]
CHANNELS = [("rules", "rules"), ("resid", "residual"), ("freq", "frequency"), ("osc", "oscillation"), ("absence", "absence"), ("model", "model conf."), ("device", "device conf."), ("rate", "rate (advisory)")]
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})


def load(name):
    return json.loads((REPO / "outputs" / name).read_text())


def save(fig, stem):
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("wrote", stem)


# ---------------------------------------------------------------- 1. detections by family per system
def fig_detection_by_family():
    fig, axes = plt.subplots(2, 3, figsize=(10, 5.2), sharey=False)
    axes = axes.ravel()
    for ax, (s, label) in zip(axes, SYSTEMS):
        card = load(f"benchmark_v6_{s}.json"); man = yaml.safe_load((REPO / f"configs/lbnl_{s}/scenarios.yaml").read_text())
        fam = {m["file"]: m["family"] for m in man["scenarios"]}
        rows = {}
        for x in card["scenarios"]:
            if not x["is_fault"] or x["excluded"]:
                continue
            f = fam[x["file"]].replace("_", " "); rows.setdefault(f, [0, 0]); rows[f][1] += 1; rows[f][0] += int(bool(x["meaningful_channels"]))
        fams = sorted(rows, key=lambda k: -rows[k][1])
        det = [rows[f][0] for f in fams]; tot = [rows[f][1] for f in fams]
        y = np.arange(len(fams))
        ax.barh(y, tot, color="#e6e6e6", edgecolor="none")
        ax.barh(y, det, color="#2b6cb0", edgecolor="none")
        ax.set_yticks(y); ax.set_yticklabels(fams, fontsize=6.5); ax.invert_yaxis()
        n_det = sum(det); n_tot = sum(tot)
        title = f"{label}: {n_det}/{n_tot}" + (" naive (13/14 adjudicated)" if s == "sdahu" else "")
        ax.set_title(title, fontsize=8.5)
        ax.set_xlabel("scenarios", fontsize=7)
        for yi, (d, t) in enumerate(zip(det, tot)):
            ax.text(t + 0.2, yi, f"{d}/{t}", va="center", fontsize=6)
        ax.set_xlim(0, max(tot) * 1.35)
    fig.subplots_adjust(wspace=0.85, hspace=0.45)
    fig.suptitle("Detected scenarios by fault family (blue) of scored scenarios (grey); final gate", fontsize=9, y=0.98)
    save(fig, "fig_detection_by_family")


# ---------------------------------------------------------------- 2. per-channel holdout false alarms
def fig_false_alarms():
    fig, ax = plt.subplots(figsize=(7, 2.6))
    width = 0.1
    x = np.arange(len(SYSTEMS))
    for i, (ch, lab) in enumerate(CHANNELS):
        vals = []
        for s, _ in SYSTEMS:
            u = load(f"union_fpr_{s}.json"); c = u["channels"].get(ch)
            vals.append(100 * c["holdout_fp_days"] / u["holdout_days"] if c else 0)
        ax.bar(x + (i - 3.5) * width, vals, width, label=lab, color=None if ch != "rate" else "#bbbbbb", hatch="//" if ch == "rate" else None)
    dep = [100 * load(f"union_fpr_{s}.json")["union_minus_rate"]["holdout_fp_days"] / load(f"union_fpr_{s}.json")["holdout_days"] for s, _ in SYSTEMS]
    ax.plot(x, dep, "k_", markersize=18, markeredgewidth=2, label="deployed union")
    ax.plot([-0.5, 4.5], [100 * 10 / 96] * 2, color="#c0392b", lw=0.8, ls="--"); ax.text(4.45, 10.7, "pre-registered budget, 10 of 96 (annual systems)", color="#c0392b", fontsize=6.5, ha="right")
    ax.set_xticks(x); ax.set_xticklabels([l for _, l in SYSTEMS]); ax.set_ylabel("% of held-out fault-free days"); ax.set_ylim(0, 20)
    ax.legend(ncol=5, fontsize=6, frameon=False, loc="upper left")
    ax.set_title("Per-channel and deployed-union false alarms on the fault-free holdout (every threshold out-of-sample)", fontsize=8.5)
    save(fig, "fig_false_alarms")


# ---------------------------------------------------------------- 3. X22: what the conformance channel can see
def fig_x22():
    a = load("x22_positive_control.json")["systems"]
    arms = [("reverse", "reverse"), ("swap_8", "8 swaps"), ("skip_4", "4 deletions"), ("skip_start", "delete start"), ("dup_block", "duplicate block")]
    sysl = [("sdahu", "SDAHU"), ("pfpu", "PFPU"), ("sfpu", "SFPU"), ("ddahu", "DDAHU"), ("fcu", "FCU")]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 2.6))
    x = np.arange(len(sysl)); w = 0.15
    for i, (arm, lab) in enumerate(arms):
        ax1.bar(x + (i - 2) * w, [a[s]["arms"][arm]["auc_perturbed_below_healthy"] for s, _ in sysl], w, label=lab)
        ax2.bar(x + (i - 2) * w, [100 * a[s]["arms"][arm]["flagged_frac"] for s, _ in sysl], w, label=lab)
    ax1.axhline(0.5, color="k", lw=0.6, ls=":"); ax1.set_ylim(0.3, 1.02); ax1.set_ylabel("AUC (perturbed below healthy)"); ax1.set_title("Threshold-free separability", fontsize=8.5)
    ax2.set_ylabel("% holdout days flagged at the deployed gate"); ax2.set_title("What the deployed gate flags", fontsize=8.5)
    for ax in (ax1, ax2):
        ax.set_xticks(x); ax.set_xticklabels([l for _, l in sysl])
    ax1.legend(fontsize=6, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.42))
    fig.suptitle("X22 positive control: order violations injected into fault-free holdout traces", fontsize=9, y=1.03)
    save(fig, "fig_x22_positive_control")


# ---------------------------------------------------------------- 4. X29: which residual carries fouling, by severity
def fig_x29():
    cr = load("x29_residual_credits.json")["scenarios"]
    sev = [10, 20, 30, 40, 50]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
    series = {ax1: [("condfouling", "cond_approach", "#2b6cb0", "-o", "condensing $-$ outdoor temp. (refrigerant side)"),
                    ("condfouling", "pressure_ratio", "#2b6cb0", "--s", "discharge / suction pressure (refrigerant side)"),
                    ("condfouling", "supply_dT", "#c0392b", ":^", "return $-$ supply air (air side)")],
              ax2: [("evapfouling", "supply_dT", "#c0392b", ":^", "return $-$ supply air (air side)"),
                    ("evapfouling", "pressure_ratio", "#2b6cb0", "--s", "discharge / suction pressure (refrigerant side)"),
                    ("evapfouling", "discharge_superheat", "#2b6cb0", "-.d", "discharge superheat (refrigerant side)")]}
    for ax, rows in series.items():
        for fam, rule, color, style, lab in rows:
            ax.plot(sev, [cr[f"RTU_sim_{fam}{k}"]["per_rule_flagged_days"][rule] for k in sev], style, color=color, label=lab, markersize=4)
        ax.set_xlabel("seeded airflow reduction (%)"); ax.set_xticks(sev); ax.set_ylim(-3, 105)
        ax.legend(fontsize=6, frameon=False, loc="center right")
    ax1.set_ylabel("days flagged (of 100)"); ax1.set_title("Condenser fouling", fontsize=8.5); ax2.set_title("Evaporator fouling", fontsize=8.5)
    fig.suptitle("X29: which residual carries each fouling detection on the simulated rooftop unit", fontsize=9, y=1.03)
    save(fig, "fig_x29_fouling_severity")


# ---------------------------------------------------------------- 5. X25: budgets before/after the statistical repair
def fig_x25():
    a = load("x25_statistical_repair.json")["systems"]
    sysl = [("sdahu", "SDAHU"), ("pfpu", "PFPU"), ("sfpu", "SFPU"), ("ddahu", "DDAHU"), ("fcu", "FCU")]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 2.5))
    x = np.arange(len(sysl)); w = 0.36
    ax1.bar(x - w / 2, [a[s]["model_holdout_fp_before"] for s, _ in sysl], w, label="in-sample (calibration target)", color="#bbbbbb")
    ax1.bar(x + w / 2, [a[s]["model_holdout_fp_after"] for s, _ in sysl], w, label="out-of-sample (calibration slice)", color="#2b6cb0")
    ax1.set_ylabel("model-channel false-alarm days"); ax1.set_title("Conformance false alarms, before / after", fontsize=8.5); ax1.set_ylim(0, 7); ax1.legend(fontsize=6.5, frameon=False, loc="upper left")
    ax2.bar(x - w / 2, [a[s]["detected_before"] for s, _ in sysl], w, label="before X25", color="#bbbbbb")
    ax2.bar(x + w / 2, [a[s]["detected_after"] for s, _ in sysl], w, label="final gate", color="#2b6cb0")
    for xi, (s, _) in enumerate(sysl):
        ax2.text(xi + w / 2, a[s]["detected_after"] + 0.5, f"{a[s]['detected_after']}/{a[s]['scored']}", ha="center", fontsize=6)
    ax2.set_ylabel("scenarios detected"); ax2.set_title("Detections, before / after", fontsize=8.5); ax2.legend(fontsize=6.5, frameon=False)
    for ax in (ax1, ax2):
        ax.set_xticks(x); ax.set_xticklabels([l for _, l in sysl])
    fig.suptitle("X25 statistical repair: out-of-sample thresholds and a per-day noise floor", fontsize=9, y=1.03)
    save(fig, "fig_x25_repair")


if __name__ == "__main__":
    fig_detection_by_family(); fig_false_alarms(); fig_x22(); fig_x29(); fig_x25()
