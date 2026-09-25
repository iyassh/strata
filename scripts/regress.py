"""L2 regression gate: regenerate every artifact, diff against committed.

Usage:
  uv run python scripts/regress.py            # diff-only (uses scratch dir)
  uv run python scripts/regress.py --list     # show the artifact->command map

A CHANGED verdict is a bug or a documented, committed decision — never
silent (design: docs/plans/2026-09-11-proof-sprint-design.md, D5).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Closed experiments (X25's calibration slice and per-day null changed the deployed detector on
# 2026-09-24; these artefacts are records of experiments run under the detector of their day
# and are compared against their closing commit, not regenerated — design D5: a documented decision)
FROZEN = {
    "x5_severity.json": "ea6bb81",
    "x12_log_diagnosis.json": "cabd2c4",
    "x12_time_perspective.json": "800a531",
    "x13_coil_effectiveness.json": "6f295f6",
    "x14_enriched_alphabet.json": "38afc62",
    "x15_enriched_frequency.json": "36edae1",
    "x18_ddahu_enriched_frequency.json": "50eb13f",
    "x21_foreign_net_support.json": "b2575b9",
    "x22_positive_control.json": "b18aa84",
}

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
    # Added after the 2026-09-23 repo audit: five claim families the paper
    # quotes sat outside the gate. (benchmark_v3.json and
    # benchmark_v2_processheal_v1.json are historical/imported and have no
    # regenerating script — see REPRODUCING.md §6.)
    "baselines_sdahu.json": "uv run python scripts/baselines.py sdahu",
    "baselines_pfpu.json": "uv run python scripts/baselines.py pfpu",
    "baselines_sfpu.json": "uv run python scripts/baselines.py sfpu",
    "matched_rules_sdahu.json": "uv run python scripts/matched_rules.py sdahu",
    "matched_rules_pfpu.json": "uv run python scripts/matched_rules.py pfpu",
    "matched_rules_sfpu.json": "uv run python scripts/matched_rules.py sfpu",
    "grammar_results.json": "uv run python scripts/grammar.py",
    "week0_audit.json": "uv run python scripts/02_week0_audit.py all",
    # 2026-09-23 sealed test: Q first, then the scorer that consumes it.
    "alarm_attribution.json": "uv run python scripts/alarm_attribution.py",
    "e3_leakage.json": "uv run python scripts/e3_leakage.py",
    "e5_schedule.json": "uv run python scripts/e5_schedule.py",
    # 2026-09-23 night: the two perspectives tested after the conformance null
    "x12_log_diagnosis.json": "uv run python scripts/x12_log_diagnosis.py",
    "x12_time_perspective.json": "uv run python scripts/x12_time_perspective.py",
    "x13_coil_effectiveness.json": "uv run python scripts/x13_coil_effectiveness.py",
    "x14_enriched_alphabet.json": "uv run python scripts/x14_enriched_alphabet.py",   # ~30 min
    "x14_control.json": "uv run python scripts/x14_control.py",
    "x15_enriched_frequency.json": "uv run python scripts/x15_enriched_frequency.py",
    # 2026-09-24 fourth system (X17); union_fpr exits 2 by design (recorded TTD cost)
    "benchmark_v6_ddahu.json": "uv run python scripts/benchmark.py ddahu",
    "union_fpr_ddahu.json": "uv run python scripts/union_fpr.py ddahu",
    "x17_onboarding.json": "uv run python scripts/x17_onboarding.py",
    "x18_ddahu_enriched_frequency.json": "uv run python scripts/x18_ddahu_enriched_frequency.py",
    # 2026-09-24 fifth system (X19), the fan coil unit
    "benchmark_v6_fcu.json": "uv run python scripts/benchmark.py fcu",
    "union_fpr_fcu.json": "uv run python scripts/union_fpr.py fcu",
    "x19_onboarding.json": "uv run python scripts/x19_onboarding.py",
    "x19_waterside_diagnostic.json": "uv run python scripts/x19_waterside_diagnostic.py",
    "matched_rules_ddahu.json": "uv run python scripts/matched_rules.py ddahu",
    "matched_rules_fcu.json": "uv run python scripts/matched_rules.py fcu",
    "discovery_predicts_transfer_q_four.json": "uv run python scripts/discovery_predicts_transfer_q.py --systems ddahu,fcu --out outputs/discovery_predicts_transfer_q_four.json",
    "x20_transfer_four.json": "uv run python scripts/x20_transfer_four.py",
    "x21_foreign_net_support.json": "uv run python scripts/x21_foreign_net_support.py",
    "x22_positive_control.json": "uv run python scripts/x22_positive_control.py",
    "x24_oa_fraction.json": "uv run python scripts/x24_oa_fraction.py",
    "benchmark_v6_rtu_field.json": "uv run python scripts/benchmark.py rtu_field",
    "union_fpr_rtu_field.json": "uv run python scripts/union_fpr.py rtu_field",
    "x26_real_data_budget.json": "uv run python scripts/x26_real_data_budget.py",
    "x25_statistical_repair.json": "uv run python scripts/x25_statistical_repair.py",
    "x27_fan_law_static.json": "uv run python scripts/x27_fan_law_static.py",
    "x28_coil_ua.json": "uv run python scripts/x28_coil_ua.py",
    "benchmark_v6_rtu_sim.json": "uv run python scripts/benchmark.py rtu_sim",
    "union_fpr_rtu_sim.json": "uv run python scripts/union_fpr.py rtu_sim",
    "x29_residual_credits.json": "uv run python scripts/x29_residual_credits.py",
    "x29_refrigerant_observability.json": "uv run python scripts/x29_refrigerant_observability.py",
    # x31_field_conditions*.json: ~1 h in three per-system processes; not in the gate — guard tests/test_x31_field_conditions.py pins it.
    # x30_method_grid.json: ~2 h (alignments on 365-day logs; per-cell 15-min budget); not in the gate — guard tests/test_x30_method_grid.py pins it.
    # x9_x10_robustness.json: ~1 h in three per-system processes (see its pre-registration); not in the gate.
    "discovery_predicts_transfer_q.json": "uv run python scripts/discovery_predicts_transfer_q.py",
    "discovery_predicts_transfer.json": "uv run python scripts/discovery_predicts_transfer.py --q outputs/discovery_predicts_transfer_q.json",
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


def verdict_from_text(committed_text: str, regenerated_text: str) -> str:
    a = dict(_flat(json.loads(committed_text)))
    b = dict(_flat(json.loads(regenerated_text)))
    diffs = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
    if not diffs:
        return "IDENTICAL"
    return f"CHANGED ({len(diffs)} paths, e.g. {sorted(diffs)[:3]})"


def artifact_verdict(committed: Path, regenerated: Path) -> str:
    return verdict_from_text(committed.read_text(), regenerated.read_text())


def main() -> int:
    if "--list" in sys.argv:
        for art, cmd in PIPELINE.items():
            print(f"{art:34s} <- {cmd}", flush=True)
        return 0
    outputs = ROOT / "outputs"
    failures = []
    for art, cmd in PIPELINE.items():
        committed = outputs / art
        if not committed.exists():
            print(f"{art:34s} SKIP (no committed artifact)", flush=True)
            continue
        if art in FROZEN:
            head_text = subprocess.run(["git", "show", f"HEAD:outputs/{art}"], cwd=ROOT, capture_output=True, text=True).stdout
            same = head_text == committed.read_text()
            print(f"{art:34s} FROZEN at {FROZEN[art]} ({'unchanged since' if same else 'DIFFERS FROM HEAD'})", flush=True)
            if not same:
                failures.append(art)
            continue
        # Hold the committed copy IN MEMORY. A previous version stashed it in
        # a scratch directory under TMPDIR; the OS emptied that directory
        # during a 28-minute regeneration, losing the baseline and killing the
        # sweep on artifact 2 of 12. Scratch files on disk are not a
        # dependency this gate can afford.
        committed_text = committed.read_text()
        mtime_before = committed.stat().st_mtime_ns
        r = subprocess.run(cmd.split(), cwd=ROOT, capture_output=True, text=True)
        if r.returncode not in (0, 2):  # 2 = a script's falsifier exit, artifact still written
            print(f"{art:34s} RUN-ERROR\n{r.stderr[-500:]}", flush=True)
            failures.append(art)
            committed.write_text(committed_text)  # never leave it half-written
            continue
        # Write check (gap audit 2026-09-24): a script that exits cleanly without
        # rewriting its artefact must not be reported IDENTICAL.
        if committed.stat().st_mtime_ns == mtime_before:
            print(f"{art:34s} NOT-REWRITTEN (exit {r.returncode}; artefact untouched)", flush=True)
            failures.append(art)
            continue
        try:
            verdict = verdict_from_text(committed_text, committed.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{art:34s} READ-ERROR ({exc})", flush=True)
            failures.append(art)
            committed.write_text(committed_text)
            continue
        print(f"{art:34s} {verdict}", flush=True)
        if verdict != "IDENTICAL":
            failures.append(art)
            committed.write_text(committed_text)  # restore the committed record
    print(f"\n{'ALL IDENTICAL' if not failures else 'FAILURES: ' + ', '.join(failures)}", flush=True)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
