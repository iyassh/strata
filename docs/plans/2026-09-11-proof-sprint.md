# Proof Sprint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the measured "better than traditional" case (open-fdd baseline, prior-work audit, three-questions demo with a scored fault-naming layer, fourth-system frozen run) plus the standing testing program, ending in a meeting package for the professors.

**Architecture:** Everything reuses the existing harness (configs → events → channels → gates → day-level scoring in `scripts/`, library in `src/processheal/`). New work = one third-party baseline adapter, one naming/report layer in the facade, one regression runner, research documents, and a demo script. Project law applies to every experiment: pre-register (commit) → run → hostile mini-audit → artifact + guard tests.

**Tech Stack:** Python 3.12, uv, pandas, pytest, open-fdd (PyPI), GitHub Actions.

**Standing rules for the executor:**
- Run everything from `/Users/yassh/Downloads/Ureap/strata`. If Bash reports "Unable to read current working directory", the shell lost macOS file access — STOP and tell the user to restart the Claude Code app before continuing.
- Prefix any run >5 min with `caffeinate -i`.
- Commits carry NO Co-Authored-By trailer (user directive).
- Quote no number in any doc until its artifact + guard test exist.

---

## Task 0: Preflight

**Step 1:** `uv run pytest -q` → Expected: `101 passed`.
**Step 2:** `git status --short` → Expected: only `docs/plans/2026-09-11-proof-sprint-design.md` (+ this file) untracked/modified.
**Step 3:** Commit both plan docs:
```bash
git add docs/plans/ && git commit -m 'docs: proof-sprint design + implementation plan'
git push
```

---

## Task 1 (D5-L2): The regression runner

**Files:** Create `scripts/regress.py`, Test `tests/test_regress_runner.py`.

**Step 1: Write the failing test** (data-free; unit-tests the diff logic only):

```python
"""tests/test_regress_runner.py — regress.py diff-verdict logic."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from regress import artifact_verdict  # noqa: E402


def test_identical_verdict(tmp_path):
    a = tmp_path / "a.json"; b = tmp_path / "b.json"
    a.write_text(json.dumps({"x": 1})); b.write_text(json.dumps({"x": 1}))
    assert artifact_verdict(a, b) == "IDENTICAL"


def test_changed_verdict_names_paths(tmp_path):
    a = tmp_path / "a.json"; b = tmp_path / "b.json"
    a.write_text(json.dumps({"x": 1, "y": {"z": 2}}))
    b.write_text(json.dumps({"x": 1, "y": {"z": 3}}))
    v = artifact_verdict(a, b)
    assert v.startswith("CHANGED") and "y.z" in v
```

**Step 2:** `uv run pytest tests/test_regress_runner.py -q` → Expected: FAIL (no module `regress`).

**Step 3: Implement `scripts/regress.py`:**

```python
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
```

**Step 4:** `uv run pytest tests/test_regress_runner.py -q` → Expected: 2 passed.
**Step 5:** Full suite: `uv run pytest -q` → Expected: 103 passed.
**Step 6:** Smoke the runner on the two fastest artifacts only (edit nothing; just verify it runs): `caffeinate -i uv run python scripts/regress.py 2>&1 | tail -20` → Expected: every line `IDENTICAL` (multi-hour run — run overnight if needed; FPU rows may be deferred to Task 9 with a note).
**Step 7:** Commit: `git add scripts/regress.py tests/test_regress_runner.py && git commit -m 'feat: L2 regression runner (regenerate-and-diff with per-artifact verdicts)'`

## Task 2 (D5-L1): CI workflow

**Files:** Create `.github/workflows/tests.yml`.

**Step 1:**
```yaml
name: tests
on: [push, pull_request]
jobs:
  fast-guards:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run pytest -q
```
**Step 2:** Commit + push; open the Actions tab result. Expected: green (data-dependent tests self-skip on a dataless runner — verify the skip count in the log; if any test errors instead of skipping, fix its skip guard).
**Step 3:** Add badge to README top: `![tests](https://github.com/iyassh/strata/actions/workflows/tests.yml/badge.svg)` replacing the static badge. Commit `'ci: run fast guard suite on every push + live badge'`.

## Task 3 (D5): Testing-policy doc

**Files:** Create `TESTING.md` (~1 page): the three levels (L1 every push / L2 before any claim via `regress.py` / L3 new-dataset-becomes-fixture), the no-silent-CHANGED rule, the seven-point rigor law from the design doc. Add MASTER_PLAN line marking D5 delivered. Commit `'docs: standing testing program (three-level regression + rigor law)'`.

---

## Task 4 (D1): open-fdd baseline — exploration & pre-registration

**Files:** Create `docs/plans/2026-09-XX-openfdd-prereg.md` (date of execution day), Create `scripts/openfdd_baseline.py` (Task 5), Test `tests/test_openfdd_baseline.py` (Task 5).

**Step 1:** `uv add open-fdd` (falls back to `uv add g36-ahu-faults` if the former's install is broken; record which).
**Step 2:** Explore the installed API (30 min, read-only): `uv run python -c "import openfdd, inspect, pkgutil; ..."` — identify: the AHU fault-condition classes, their expected input column names, their default parameters, their per-row output format. Write findings into the pre-reg doc's "Adapter contract" section. **Do not adjust any default parameter.**
**Step 3:** Write the pre-registration doc BEFORE any scoring run. Must contain: (a) adapter contract (our canonical sensor -> open-fdd expected column, per system; unmappable conditions listed with the missing sensor); (b) scoring protocol — day-level roll-up: a day is flagged by the battery if ANY fault condition fires on any row of it; same non-excluded scenarios; clean-year FP measured on the same last-8-days-per-month holdout days for comparability, full clean year reported alongside; (c) expectations E1 "battery catches mechanical mismatch families", E2 "battery misses bias/rhythm/instability families", E3 "battery clean-year FP day-rate exceeds STRATA's deployed 1.0-5.2%"; (d) **falsifier F1: if the battery's detected-scenario count is >= STRATA's at a clean-year FP <= STRATA's on any system, the 'better than traditional' claim for that system is dead and will be reported as such.**
**Step 4:** Commit pre-reg doc: `'prereg: open-fdd traditional baseline (adapter contract, expectations, falsifier)'` — MUST be its own commit before Task 5 begins.

## Task 5 (D1): open-fdd baseline — adapter, run, guards

**Step 1: Failing test first** — `tests/test_openfdd_baseline.py`: (data-free) adapter column-mapping unit test: given a 5-row frame with canonical names, `to_openfdd_frame(df, "sdahu")` renames to the contract's names and preserves row count; artifact stasis guard (skips if artifact absent): scenario counts match `scenarios.yaml` non-excluded lists; every scenario row has `battery_flag_days` and `holdout_fp_days` ints; falsifier verdict field present.
**Step 2:** Run → FAIL. **Step 3:** Implement `scripts/openfdd_baseline.py`: loads each system's parquet + adapter, runs the battery with defaults, rolls to days, emits `outputs/openfdd_baseline_{system}.json` (per scenario: flag days; clean year: holdout + full-year FP days; per fault-condition: fired/not/unrunnable-missing-sensor). **Step 4:** `caffeinate -i uv run python scripts/openfdd_baseline.py sdahu` then pfpu, sfpu. **Step 5:** Tests pass (suite grows to ~106). **Step 6:** Commit `'feat: open-fdd G36 battery baseline (default thresholds) + artifacts + guards'`.
**Step 7: Hostile mini-audit (subagent):** brief = verify adapter mapping fidelity against open-fdd docs; recompute 2 scenarios' day-rollups independently; check we didn't accidentally tune any parameter; check the falsifier honestly evaluated. Apply required fixes; commit.
**Step 8:** Results doc `paper/OPENFDD_BASELINE_RESULTS.md`: the side-by-side table (battery vs STRATA per system: detected/N, FP days, capabilities row: explanations? budgets? localization?). Commit.

---

## Task 6 (D3): report() layer + fault-family naming score

**Step 1: Failing tests** — extend `tests/test_pipeline_facade.py`:
```python
def test_report_renders_alarm_sentence():
    # uses the SDAHU fault regression fixture already in this file
    rep = det.evaluate(fdf)
    text = render_report(rep, det)          # new function
    assert "rules" in rep["meaningful_channels"]
    assert "zone" in text.lower() or "TU_" in text or "damper" in text.lower()
    assert "%" in text                       # the budget line

def test_family_attribution_mapping_total():
    # every deployed channel pattern maps to exactly one family or 'unknown'
    from processheal.core.naming import attribute_family
    assert attribute_family({"rules"}, {"damper_command_mismatch"}) == "stuck_or_leak_actuator"
    assert attribute_family({"residual"}, set()) == "sensor_bias_or_coil_fault"
    assert attribute_family(set(), set()) == "unknown"
```
**Step 2:** FAIL. **Step 3:** Implement `src/processheal/core/naming.py`: `attribute_family(meaningful_channels, fired_signature_kinds) -> str` — an explicit, documented mapping table (mismatch/leak signatures -> stuck_or_leak_actuator; residual-led -> sensor_bias_or_coil_fault; oscillation-led -> control_instability; frequency-led -> control_instability; conformance/absence-led -> functional_failure_or_schedule; combinations resolved by precedence: signature kind first, else strongest channel). `render_report(rep, det) -> str`: name + family + evidence values + top device/zone + budget line from provenance/floors.
**Step 4:** Tests pass. **Step 5:** Commit `'feat: fault-family attribution + human alarm report rendering'`.
**Step 6: Pre-register the naming score** (small section appended to the D1 pre-reg doc or its own file): metric = for each of the 73 non-excluded scenarios, does `attribute_family` of its v12 meaningful channels match the seeded family (mapping of benchmark families -> our family labels stated in the doc)? Expectation: >=80% match; every mismatch listed. Commit pre-reg BEFORE running.
**Step 7:** `scripts/naming_score.py` reads committed benchmark artifacts only (no re-runs), emits `outputs/naming_score.json` + prints the confusion list. Guard test pins the score. Commit `'feat: fault-family naming scored on all 73 scenarios (pre-registered)'`.
**Step 8:** Mini-audit (subagent): recompute 10 random scenarios' attributions by hand from artifacts; check the mapping table wasn't fitted after seeing failures (git history of pre-reg proves order). Fix, commit.

## Task 7 (D3): the three-questions demo

**Files:** Create `scripts/demo.py`.
**Step 1:** Script: `uv run python scripts/demo.py sdahu coi_bias_-4_annual` — prints, with deliberate pacing: (A) ingestion lines (raw file -> gates passed -> events/day count); (B) day-by-day stream over the first N fault days: `2018-01-01  all channels quiet` ... then the full `render_report` alarm block on the detection day; (C) localization line + the 37/37 number with its scope sentence. Reuses `fit()`/frozen artifacts; add `--fast` flag using cached detector.
**Step 2:** Dry-run all three planned fault types (valve-stuck, sensor-bias, instability). Expected: silence-then-alarm in each, correct family names.
**Step 3:** Commit `'feat: three-questions demo (logs in -> named fault -> location)'`.

---

## Task 8 (D2): prior-work audit table

**Step 1:** Research subagent brief: find ALL published fault-detection results on LBNL SDAHU (and any FPU claims); for each: citation, method, metric+score, data columns used, train/test protocol; explicitly check exposure to ERRATA E1 (oa_bias x4/negative use), E2 (coi_leakage x4), E3 (SA_SP provenance), E5 (branch); return with URLs/DOIs.
**Step 2:** Write `paper/PRIOR_WORK_COMPARISON.md`: table + audit column + "not directly comparable" rows where honest + the FPU first-ever row + one paragraph on what the audit column means. Every exposure claim must cite the specific erratum evidence command.
**Step 3:** Second-agent verification pass on any paper whose exposure we assert (quote the paper's own methods text). Fix.
**Step 4:** Commit `'docs: prior-work comparison with errata-exposure audit'`.

---

## Task 9 (D4): fourth system — frozen-method run on experimental data

**Step 1: Candidate scan + go/no-go (half day, subagent + manual):** enumerate LBNL corpus experimental sets (FLEXLAB AHU, FCU, RTU...); for each: fault-free data duration, sampling rate, sensor list vs our rule kinds. GO requires: >=8 weeks fault-free (calibration + holdout), mappable core sensors. Write `docs/plans/2026-09-XX-fourth-system-gonogo.md` with the decision. If NO candidate passes: document, skip to Task 10, and the deck says exactly that (a finding, not a failure).
**Step 2:** User downloads the chosen archive (provide exact URL + expected layout). Convert via existing converter pattern (new small script if format differs; sort+monotonic assert per L10).
**Step 3: Onboard, timed:** copy nearest config; write sensors.yaml + rules.yaml for the new system; run week-0 gates + healthy-silence at the dataset's own sampling rate (L31). Record wall-clock honestly in `configs/ONBOARDING_LOG.md`.
**Step 4: Pre-register** (own doc, own commit, BEFORE benchmark run): expectations per fault family given its sensor coverage; falsifiers incl. "healthy-silence unachievable after documented tuning = method limit, reported"; frozen-method declaration (code SHA pinned).
**Step 5:** Run the benchmark + union scripts on it once. **Step 6:** Guard tests pin its artifacts (L3 fixture — permanent). **Step 7:** Hostile mini-audit; fixes; results doc `PHASE9_FOURTH_SYSTEM.md` (whatever the outcome). **Step 8:** Commits at each step; final `'feat: fourth system (frozen-method, experimental data) — treadmill fixture #4'`.

---

## Task 10 (D6): meeting package

**Step 1:** `paper/deck/` as markdown slides (one .md, `---` separators, convertible): 12 slides per the design's order; every number sourced from an artifact; the three-questions demo as the centerpiece slide sequence; one WebCTRL slide (future pilot path only); closing slide = the evaluation machine (CI badge + regress verdict + treadmill).
**Step 2:** `paper/QA_PREP.md`: the drilled professor questions + answers (from the explainer sessions) + the new ones (open-fdd fairness, fourth-system outcome, naming-score misses).
**Step 3:** `paper/EMAIL_DRAFT.md`: short email to Anthony & Medulla — repo link, deck attached, 3 proposed meeting slots, one-paragraph summary. (User sends it — not us.)
**Step 4:** Commit `'docs: meeting deck, Q&A prep, email draft'`.

## Task 11: Close the sprint

**Step 1:** `uv run pytest -q` all green; `caffeinate -i uv run python scripts/regress.py` -> ALL IDENTICAL (including any deferred FPU rows and the new fixture).
**Step 2:** MASTER_PLAN: mark D1-D6 delivered with artifact names; log deferred items (WebCTRL memo, L24 split, sub-daily tier, robust quantiles).
**Step 3:** Update memory file (strata_framework_decision.md) with sprint outcomes.
**Step 4:** Final commit + push. Tell the user: package ready, send the email.
