"""Generate the results figures FROM COMPUTED RESULTS (outputs/benchmark_v2.json).

No hand-typed numbers: run scripts/benchmark.py first; these read its JSON so
figures can never drift from the reported results.

Produces:
  outputs/benchmark_perday.png      — per-scenario detection with ablation
  outputs/fitness_distributions.png — per-day fitness distributions vs threshold
  outputs/detector_summary.png      — rules vs structure vs combined head-to-head
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path("outputs/benchmark_v2.json")
if not RESULTS.exists():
    raise SystemExit("run scripts/benchmark.py first (outputs/benchmark_v2.json missing)")

data = json.loads(RESULTS.read_text())
rows = data["scenarios"]
s = data["summary"]
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

# ---------- figure 1: per-scenario detection with ablation ----------
labels = [r["category"] for r in rows]
days = np.array([r["days"] for r in rows], dtype=float)
rules = np.array([r["rules_only_flagged"] for r in rows]) / days * 100
structure = np.array([r["structure_only_flagged"] for r in rows]) / days * 100
combined = np.array([r["combined_flagged"] for r in rows]) / days * 100

y = np.arange(len(labels))
h = 0.27
fig, ax = plt.subplots(figsize=(11, 7))
ax.barh(y + h, rules, h, label="rules-only (signature events, no model)", color="#94a3b8")
ax.barh(y, structure, h, label="structure-only (model, signatures stripped)", color="#e8920c")
ax.barh(y - h, combined, h, label="combined (unified rule)", color="#1f6feb")
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("% of days flagged (per-day, out-of-sample threshold)")
ax.set_xlim(0, 105)
ax.set_title(
    "Per-scenario detection with ablation\n"
    f"combined: recall {s['combined']['recall']:.1%} "
    f"(95% CI {s['combined']['recall_ci'][0]:.1%}-{s['combined']['recall_ci'][1]:.1%}), "
    f"precision {s['combined']['precision']:.1%}, FPR {s['combined']['fpr']:.1%}",
    fontsize=11,
)
ax.legend(loc="lower right", fontsize=9)
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "benchmark_perday.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------- figure 2: per-day fitness distributions ----------
healthy_fit = np.array(data["holdout_fitness"], dtype=float)
actuator_fit = np.concatenate(
    [r["per_day_fitness"] for r in rows if r["is_fault"] and "bias" not in r["category"]]
)
bias_fit = np.concatenate(
    [r["per_day_fitness"] for r in rows if r["is_fault"] and "bias" in r["category"]]
)

bins = np.linspace(0, 1.0, 41)
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.hist(healthy_fit, bins=bins, density=True, histtype="stepfilled", alpha=0.45,
        color="#2e8b57", label=f"held-out healthy days (n={len(healthy_fit)})")
ax.hist(actuator_fit, bins=bins, density=True, histtype="stepfilled", alpha=0.40,
        color="#1f6feb", label=f"actuator-fault days (n={len(actuator_fit):,})")
ax.hist(bias_fit, bins=bins, density=True, histtype="stepfilled", alpha=0.40,
        color="#e8920c", label=f"sensor-bias days (n={len(bias_fit):,})")
ax.axvline(data["threshold"], color="#d33", linestyle="--", linewidth=1.6,
           label=f"calibrated threshold ({data['threshold']:.3f})")
ax.set_xlabel("per-day conformance fitness (1.0 = day fully fits the healthy model)")
ax.set_ylabel("density")
ax.set_title(
    "Why fitness alone is not enough: per-day fitness distributions\n"
    "Fault days overlap the healthy range — the signature events, not the fitness "
    "threshold, carry actuator detection",
    fontsize=11,
)
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "fitness_distributions.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------- figure 3: detector head-to-head ----------
detectors = ["rules", "structure", "combined"]
names = ["rules-only", "structure-only", "combined"]
colors = ["#94a3b8", "#e8920c", "#1f6feb"]
metrics = [("recall", "Recall\n(fault days flagged)"),
           ("precision", "Precision"),
           ("fpr", "False-positive rate\n(healthy days)")]

x = np.arange(len(metrics))
w = 0.26
fig, ax = plt.subplots(figsize=(10, 5.5))
for i, (det, name, color) in enumerate(zip(detectors, names, colors)):
    vals = [s[det][m[0]] * 100 for m in metrics]
    bars = ax.bar(x + (i - 1) * w, vals, w, label=name, color=color)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f}%",
                ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels([m[1] for m in metrics], fontsize=10)
ax.set_ylabel("%")
ax.set_ylim(0, 112)
ax.set_title(
    "Three detectors head-to-head (per-day, out-of-sample)\n"
    "The engineered events detect; the process model explains and adds "
    "missing-behaviour coverage; combined keeps both",
    fontsize=11,
)
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "detector_summary.png", dpi=150, bbox_inches="tight")
plt.close(fig)

print("wrote outputs/benchmark_perday.png, fitness_distributions.png, "
      "detector_summary.png (all from benchmark_v2.json)")
