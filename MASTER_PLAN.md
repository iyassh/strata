# MASTER PLAN — from validated framework to paper + public toolkit

Written 2026-08-17, after six independent deep-research passes:
four /ult agents (simulated ICPM program committee; whole-project
cross-phase gap audit; web paper-strengthening sweep; ranked feasibility
study) and two toolkit agents (open-source FDD landscape sweep;
repo toolkit-readiness audit). This document consolidates every gap
they found and sequences all remaining work. It supersedes the
"open experiments" list in RESEARCH_LOG Part V (frozen at Aug 10).

Standing verdicts the plan builds on:
- **Worth a paper: yes** (all four /ult agents converge). Winning
  framing: **"Discovery Locates, Calibration Detects"** — never
  "first process mining for FDD."
- **Toolkit: yes** — pip-installable Python package (NOT .NET; wrong
  ecosystem for both our stack and audience). The niche is empty:
  LBNL publishes the benchmark datasets with zero detection code;
  the open category leader (open-fdd, 157★, MIT) is rule-thresholds
  only; no conformance-based anomaly-detection package exists
  anywhere. JOSS is a free, precedented second publication
  (ConStrain/PNNL 2026 is the domain precedent) and is explicitly
  compatible with a companion ICPM methods paper.

---

## PART 0 — Consolidated gap register (what the six passes found)

### Science gaps (cross-phase audit, recomputed from disk)

| ID | Gap | Severity | Status |
|----|-----|----------|--------|
| S1 | **No joint/union FPR number anywhere** (promised as G9, "a claimable first"). Auditor computed it: naive 9-channel OR false-alarms 15/96 healthy days on SDAHU (15.6%), 12/96 PFPU, 4/96 SFPU. The seasonal **rate channel is the entire problem** (14 and 7 of those days); no scenario anywhere is carried solely by rate. Demoting rate to diagnostic-only → **1.0% / 5.2% / 4.2%** union at zero scorecard cost. | CRITICAL — flips the "0 false-alarm days" headline if a reviewer computes it first | ✅ DONE Phase 6 |
| S2 | **No single "STRATA detector" definition** — paper currently reads as 9 detectors glued by per-scenario significance gates | CRITICAL (same fix as S1) | ✅ DONE Phase 6 |
| S3 | **X8 contamination experiment absent.** Web sweep: training-set contamination is a hot named 2025–26 topic at ICPM and attacks our core assumption ("what if the fault-free year isn't?"). Priority ABOVE X7 (reverses the strategist's initial ranking). Cheap version: inject k∈{2,5,10}% fault days into SDAHU train, rerun calibration + healthy silence, report threshold drift only | HIGH | Open |
| S4 | **X7 noise/15-min downsample absent.** Deferrable with a citable argument (event abstraction + sustained-minutes discretize amplitude noise); do after X8 if capacity allows, else limitations paragraph | MEDIUM | Open |
| S5 | **Stale numbers that will bite** if the paper is drafted from old docs: RESEARCH_LOG Part V frozen at Aug 10 ("PFPU 17/30"); GAP_ANALYSIS G5's "five identical logs" claim is FALSE under the current alphabet (true only for v1 alphabet — refutable from our own artifacts); ONBOARDING_LOG counts (48/35) vs commit-time recount (45/35) vs today (57/39); PHASE1 "18 unique model days" is 23 in v12; PHASE2_RESULTS superseded three ways (never quote directly); D3 "≈98–100%" is measured 100% (164/164 ×2, 139/139, 137/137, 148/148). **Post-Phase-6 reconciliation additions (2026-08-17):** (a) week-0 zone GT is **50 Zone S + 10 INDETERMINATE** in the artifact; DAYLOG/summaries say 51/9 — artifact wins; (b) "TTD 1–2 days" is only true as a MEDIAN — the honest distribution is SDAHU {1:9, 2:5}, PFPU {1:19, 4,11,15,21}, SFPU {1:19, 3,15,15,37,108}; always write "median TTD 1 day" with the tail stated; scope union_fpr.py's docstring phrase to rate-significant scenarios; (c) MR2=freq exact identity holds on BOTH FPU systems (SFPU 141=141 AND PFPU 206=206 — stronger than the doc's single example) and MR1 fires **231** healthy SDAHU days (only PFPU's 124 is documented); (d) PCA-strict head-to-head on comparable universes is a **dead heat: 61=61 total (14v13, 23v23, 24v25) with complementary misses** — sharper honest sentence than "comparable-to-better"; (e) residual denominators differ by design: benchmark's residual_holdout_fp n (124/121) is channel-day pairs summed over the 4 residual channels, union_fpr's exposure (36–41) is distinct days — label both or a reviewer sees a contradiction | HIGH (1 hour total) | ✅ DONE Phase 7 (+ 8 audit-found locations fixed post-audit) |
| S6 | **X5 severity monotonicity (Spearman ρ)** never computed; dose-response only narrated. ~30 lines over existing v12 flag_days per family ladder | MEDIUM | Open |
| S7 | **Cry-wolf ratio** (FP_days/(FP+TP alarm days)) — derivable from artifacts, one number | LOW | ✅ DONE Phase 7 (crywolf.json) |
| S8 | **SDAHU config missing `residual_min_band_width: 0.5`** (FPU configs have it; no numeric effect — SDAHU band is 0.846 wide — but breaks the "one margin policy" uniformity claim) | LOW (one line) | Open |
| S9 | **Errata scattered, not citable**: 4 dataset errata live as fragments across GAP_ANALYSIS/RESEARCH_LOG/code comments/vault; erratum #3 (coi_leakage_050 SA_SP swap) is not in the repo at all; oa_bias byte-identity evidence narrated but stored nowhere as an artifact | HIGH as a contribution (docs claim "a dataset-quality contribution the community needs" without a citable object) | ✅ DONE Phase 7 (ERRATA.md E1–E5 + gates 5/6; E5 config-branch erratum NEW from the Phase-7 hostile audit) |
| S10 | **Reproducibility broken for a stranger**: no dataset acquisition docs/DOIs; hardcoded absolute paths in convert scripts; data/ is a gitignored symlink into ~/Downloads/processheal; no runbook (00→01→02→benchmark×3→baselines×3→matched_rules×3→stats×3→grammar documented nowhere); make_figures.py dead (reads nonexistent benchmark_v2.json); the 3.4pp claim's v1 side (5.2%) lives in the OTHER repo | HIGH (and ironic — we cite the 72%-irreproducibility statistic) | ✅ DONE Phase 7 (REPRODUCING.md; env-var paths; v1 artifact imported; make_figures deleted) |
| S11 | **Sensor-coverage honesty list** now computed definitively: FPU 53/110 columns unmapped (incl. VAV_FAN_DP_* — the sensor PCA used to beat us on SFPU airside fouling), SDAHU 18/31 (incl. ZONE_TEMP_1..5, flow-balance CFMs). Zero cost — paste into honesty section | LOW as gap, HIGH as honesty ammunition | ✅ DONE Phase 7 (sensor_coverage.json; artifact says 12/30 + 56/109 excl. Datetime) |
| S12 | **Paper-text items** from the web sweep: terminology "fault-free/baseline" (not "healthy-only"); must-cite Vitale et al. JMS 2026 (closest rival pipeline — differentiate explicitly), vanden Broucke artificial negative events (ancestor of our falsifiers), ICPM 2025 "Hypothesis Testing for Processes"; "stratified" is safe, "hierarchical" is taken; reversal probe is claimably novel (no precedent found) | HIGH for review survival | Open |
| S13 | Never-built physics (flow_balance, fan cmd-vs-status, zone-comfort residual) and the heterogeneity stress test | LOW — honesty-table lines, don't build | Document only |

### Toolkit gaps (repo audit)

| ID | Gap | Severity |
|----|-----|----------|
| T1 | **No LICENSE file** — nobody can legally reuse anything. Norm in this space: MIT/BSD-3 | BLOCKING |
| T2 | **pm4py is AGPL** — a hard dependency makes the whole toolkit effectively AGPL (poison for consultant/vendor adoption). Must become optional extra (`strata[pm4py]`) or be replaced natively for our restricted event-log class. ARCHITECTURAL — decide before repo goes public | BLOCKING |
| T3 | **The real detector exists only inside scripts/benchmark.py** (480 lines welded to fault manifests, ground truth, data/ symlink). All significance gates — the scientific heart — are script-local, un-importable, untested. Needs a `StrataDetector` facade: `load_config → fit(healthy_df) → score(new_df) → report()` (~3–5 days; channel modules need almost no change) | BLOCKING |
| T4 | **No fault-free-only entry point**: shipped `processheal run` CLI is the stale v1 single-channel pipeline (also demands a --faulty file and equipment.ttl); processheal-web crashes at import on a fresh clone | BLOCKING |
| T5 | **Data ingestion**: convert scripts default to /Users/yassh/... paths (env-var overridable since Phase 7, but they no-op silently on empty source dirs); data/ dangling symlink on fresh clones; no tz handling (naive dt.date); needs `strata ingest` | BLOCKING |
| T6 | **Zero config validation**; typo'd sensor silently disables a rule with no warning; `OCCUPIED` is a hardcoded mandatory canonical (oscillation.py:36); `supply_air_residual` name + `occ_signal` KeyError traps; **no units declared anywhere** (°C user copies °F thresholds → silent garbage) | HIGH |
| T7 | **No config template/schema docs**: canonical-sensor vocabulary implicit across three configs; OCCUPIED 0/1/2 semantics buried in a comment; the SFPU-minutes onboarding story holds for strangers only with template + vocab + validate command | HIGH |
| T8 | **LBNL leaks in src/**: io/loader.py reads raw LBNL column names bypassing sensors.yaml; web/app.py hardcodes lbnl_sdahu at import; grammar.py CANONICAL hardcodes 10 event names; devices.py zone-parsing assumes TU_<zone> naming; rate channel's validity caveat (shared simulated weather year) lives in research prose not user docs | MEDIUM |
| T9 | Packaging debris: scipy used but undeclared (transitive); system Graphviz binary undeclared; binom_sf duplicated 3×; season map duplicated; build_rate_detector_monthly returns raw dict; no py.typed; no CI; .pytest_cache tracked; README quickstart is v1-era | MEDIUM |
| T10 | scenarios.yaml is an *evaluation manifest*, not building config — must move to experiments/lbnl/ fixtures so strangers don't copy it; ERRATUM_COLS hardcoded in baselines.py belongs in the manifest | MEDIUM |

### Landscape facts that shape the plan

- LBNL datasets are **CC BY 4.0** — we may ship loaders and even
  repackaged fault-free slices with attribution (Granderson et al.,
  DOI 10.25984/1881324).
- Realistic users, honestly: (1) FDD researchers — near-certain if
  LBNL benchmark reproduction is one command (every paper currently
  rewrites its own harness; LBNL ships no code); (2) energy
  engineers/commissioning consultants — the proven open-fdd
  audience; (3) NOT building operators (they live in WebCTRL/Metasys).
  Adoption ceiling ~150★ = category leadership in this niche.
- **Brick auto-config is the unclaimed differentiator**: LBNL
  datasets ship .ttl files; the research frontier (ASIM 2024
  plug-and-play AFDD, FSBrick, Chahine & Noura Sensors 2026) chases
  exactly this; nobody auto-configures ANY FDD method from Brick
  yet, and Brick's device/equipment/system hierarchy maps naturally
  onto our three strata. `strata configure --brick site.ttl` = v2 flagship.
- No canonical Python APAR exists — our calibrated APAR-lineage
  channel is itself a minor first.
- JOSS requirements = the maturation the toolkit needs anyway:
  OSI license, tests, CI, docs, examples, CONTRIBUTING, tagged
  releases, paper.md with statement of need; no fees; co-publication
  with ICPM explicitly sanctioned (disclose it).

---

## PART 1 — The plan, in phases

Ordering principle: protect the science first (S1 flips a headline),
then make the repo tell the truth (staleness/reproducibility), then
run the missing experiments, then build the toolkit on the cleaned
core, then write the two papers. Timelines intentionally omitted per
direction; phases are dependency-ordered.

### Phase 6 — Defend the headline (S1, S2, S8) — ✅ DONE 2026-08-17
(commits 51ccae3 + 1e9b009; hostile-audited, all six required fixes
applied; see PHASE6_RESULTS.md. Union 15.6/12.5/4.2% naive →
1.0/5.2/4.2% deployed, zero cost verified; model/device threshold
circularity disclosed as L24; novelty claim narrowed. NEW ITEM fed
forward to Phase 9: three-way discover/calibrate/test split in the
toolkit facade so model/device FP becomes a measurement.)
1. Commit `scripts/union_fpr.py` (cleaned from scratchpad), emit the
   per-channel healthy-holdout FP table + union row into the
   benchmark artifacts.
2. Write the single-detector definition: "the STRATA detector" =
   significance-gated channels, **rate channel demoted to
   diagnostic-only**. Verify (recompute) zero scorecard loss.
   Publish union FPR 1.0/5.2/4.2% WITH the standing caveat (negatives
   are the calibration year's holdout; no independent healthy
   negative exists — D2).
3. Add `residual_min_band_width: 0.5` to SDAHU rules.yaml (uniform
   margin policy).
4. Hostile mini-audit of the new numbers before they're quoted anywhere.
   Exit: G9 delivered — the "first joint alarm-budget in building FDD"
   claim becomes real.

### Phase 7 — Make the record true (S5, S7, S9, S10, S11) — ✅ DONE 2026-08-18
(commit fb80099 + audit-fix commit; hostile-audited: E1 mechanism reworded,
NEW erratum E5 (healthy file on a different config branch — occupied damper
floor 0.0 vs 0.1), 8 missed stale locations fixed, experiment tags renamed
E→X, guards strengthened. See PHASE7_RESULTS.md.)
1. Staleness sweep: dated addendum to RESEARCH_LOG Part V; rescope
   G5 to "under the v1 event alphabet"; timestamp + recount
   ONBOARDING_LOG (at commit aa92970 vs today); banner on
   PHASE2_RESULTS ("superseded — see v12"); fix "18→23 model days."
2. `ERRATA.md`: all four LBNL errata in one citable file (files
   affected, evidence, recompute command, consequence, who it bites);
   extend 02_week0_audit.py to emit the SDAHU MD5/byte-identity
   table so erratum #1's evidence becomes an artifact; import
   erratum #3 from the vault into the repo.
3. `REPRODUCING.md`: dataset DOIs + acquisition, directory layout,
   the 9-command runbook; parameterize the two hardcoded SRC paths
   (env var/argv); copy benchmark_v2.json from the processheal repo
   into outputs/ with a provenance note (3.4pp claim's v1 side);
   fix or delete make_figures.py (decide: v12 figure script).
4. Compute cry-wolf ratio; place the sensor-coverage gap list (S11)
   into GAP_ANALYSIS/honesty material.
   Exit: a stranger can clone, fetch data, and reproduce every quoted number.

### Phase 8 — The missing experiments (S3, S6, then S4)
1. **X8 contamination** (priority per web sweep): inject k∈{2,5,10}%
   fault days into SDAHU training; rerun calibration + healthy
   silence ×3; report threshold drift and any FP-guarantee erosion.
   Pre-register expectations + falsifier before running (project law).
2. **X5 severity Spearman ρ** over existing v12 flag_days
   (stuck 0–100%, leak 20/50/80, fouling grades) + autocorrelation caveat.
3. **X11 branch-sensitivity check (NEW, from ERRATA E5)**: does any
   SDAHU detection change when the branch-signature columns (occupied
   OA_DMPR floor) are harmonized between healthy and fault files? The
   FPU systems (single branch) are the control.
4. **X7 15-min downsample** — only after X8, only if capacity: 3
   healthy years + one fault per family, rules/resid/freq channels.
   Otherwise: limitations paragraph with the discretization argument.
   Exit: the two reviewer-anticipated experiments answered or honestly scoped.

### Phase 9 — Toolkit Tier A: stranger-runnable (T1–T6)
1. **LICENSE: MIT** + pyproject license metadata + CITATION.cff.
2. **pm4py decision**: make it an optional extra now
   (import-guarded, `strata[pm4py]`), document the AGPL consequence;
   native inductive-miner-for-our-log-class goes on the v2 roadmap.
3. **StrataDetector facade** in src/: lift day_universe, channel
   orchestration, ALL significance gates (binom_sf, rule-of-three,
   per-device Bonferroni+2×, absence binomial, meaningful_channels),
   gated TTD, DEV_META out of benchmark.py → `core/pipeline.py` +
   `core/significance.py`; benchmark.py becomes a thin consumer
   (regression-check: v12 numbers unchanged). Dedupe binom_sf ×3 +
   season map. Proper explanation return types (kill the fragile
   pandas .attrs channel).
4. **CLI rewrite**: `strata ingest / validate / fit / score / report`;
   make equipment.ttl optional; fix or retire processheal-web's
   import-time crash. `processheal` → keep as alias or rename
   decision (brand is STRATA; PyPI name check needed).
5. **Config validation** (pydantic/jsonschema): required keys, kind
   schema, cross-references, units field (°F/°C declared,
   auto-convert), "N rules skipped because sensors X,Y unmapped"
   report; graceful degrade for missing OCCUPIED / residual-rule
   name traps.
   Exit: Jordan-the-stranger runs fit/score on their own AHU CSV without reading source.

### Phase 10 — Toolkit Tier B: credible public release (T7–T10 + JOSS checklist)
1. `configs/_template/` fully annotated + canonical-sensor
   vocabulary doc (incl. OCCUPIED 0/1/2 semantics) + physics
   rationale per rule kind (extract from docstrings/ONBOARDING_LOG).
2. Quarantine: scripts/* + scenarios.yaml + week0 ground truth →
   `experiments/lbnl/`; purge src/ leaks (delete/canonicalize
   io/loader.py, config-drive web demo, grammar CANONICAL from
   config, explicit device-template field in rules.yaml);
   ERRATUM_COLS → manifest.
3. Tests for everything that moved (significance gates, day_universe,
   facade end-to-end on synthetic data); declare scipy; document
   system-Graphviz; CI (GitHub Actions: ruff + pytest, 3.12/3.13);
   py.typed; untrack .pytest_cache.
4. **One-command LBNL benchmark**: `strata benchmark lbnl-sdahu`
   (CC BY 4.0 loaders incl. the 14-distinct-scenarios curation) —
   the feature that converts every future FDD paper into users/citers.
5. Worked example runnable out of the box (synthetic or downsampled
   public data); `examples/onboard_your_ahu.md`; README rewrite
   around the own-data path; CONTRIBUTING.md; move research docs →
   docs/research-log/; tagged v0.2.0 release; repo public; PyPI publish.
   Exit: JOSS submission checklist fully green.

### Phase 11 — The two papers
1. **ICPM methods paper** ("Discovery Locates, Calibration Detects"):
   assemble from post-Phase-6/7/8 artifacts ONLY (never PHASE2/Part V
   directly); terminology "fault-free/baseline"; must-cites (Vitale
   JMS 2026 differentiation, vanden Broucke, ICPM 2025 hypothesis
   testing, Tax et al. re: precision → reversal probe); honesty
   section = sensor-coverage list + errata + fired falsifiers +
   H-CS FAIL; joint-FPR table as a headline contribution; AI
   disclosure in acknowledgments; hostile manuscript audit before
   submission (project law); mentors loop (Aighobahi & Sharma).
2. **JOSS software paper** after ICPM submission/arXiv: paper.md =
   statement of need (LBNL ships no code; rule libraries flood
   alarms; PM-fitness-thresholding lacks calibration) + comparison
   table (open-fdd, VOLTTRON AFDD, pm4py) + disclosure of the ICPM
   paper. SoftwareX only if an indexed-journal line is needed later.

### Phase 12 — v2 roadmap (post-publication, deferred by design)
- **Brick auto-config** (`strata configure --brick site.ttl`) — the
  headline differentiator; map Brick hierarchy → three strata.
- Native discovery/conformance core (drop pm4py entirely → clean MIT).
- X10 external dataset (2025 Sci-Data AHU) — journal extension.
- Multi-year/real-weather seasonal rate support; tz/DST test suite.
- TRU deployment (WebCTRL CSV export path); VOLTTRON agent wrapper;
  open-fdd-style operator stack. SKIP: DFM (per feasibility study).

---

## Standing project laws that govern all phases
Pre-register before running (falsifiers included); hostile audit
before results are quoted; positive controls for every new channel
("silence ≠ deaf"); CP-upper/uncertainty-aware gates, never point
estimates (L16); day universes from the raw calendar via the shared
helper (L6/L22 — helpers ENFORCE, not document); caffeinate every
long run; log every lesson in RESEARCH_LOG with an L-number;
commit everything.
