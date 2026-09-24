# Review verdict and improvement plan — 2026-09-24

*Four independent agents ran on HEAD 6bdf51c–c6a5b60: a simulated ICPM /
building-energy program-committee reviewer, an HVAC FDD domain expert, an
internal structural gap audit, and a web-research strategist. Their reports
are condensed here with corrections where they were wrong; the actions below
are ranked by what they would change for the project's goals.*

## 1. Verdict

**Does the framework work?** Yes, as a detector: five equipment classes,
config-only onboarding, 13/14, 23/30, 24/29, 45/55, 41/47 at 1.0–5.2 %
false-alarm days, every number regenerating from a committed command
(regression gate 44/44 identical). No, as the mechanism the project
proposed: the discovered process models detect nothing the calibrated
channels miss, on any system, and the two transfer tests (X20, X21) leave
"discovery locates invariants" with no support in either direction.

**Is the contribution enough?** By venue:

| paper | reviewer score | verdict | single biggest reason |
|---|---|---|---|
| R2PM (six benchmark defects) | 4/5 | accept at workshop, **after disclosure to LBNL** | self-contained, every claim machine-checkable |
| ERPM (process-mining null) | 3/5 | borderline at an empirical workshop; reject at ICPM main | **no positive control**: nothing shows the conformance channel *would* fire on genuine order violations, so the null can be attributed to the pipeline rather than the domain |
| manuscript ("Ten Adverse Results and a Detector") | 2/5 | a thesis, not a submission | no target venue, a voided baseline section, a title counting a post-hoc result |

**The detector alone** is "a competent applied paper, not a strong one" for a
building-FDD venue: one self-built baseline, simulated weather years only,
a voided commercial comparison. The domain expert's view of novelty: nearly
every rule kind has prior art (APAR actuator checks, Guideline 36 FC2/3/4/13,
PNNL fan-heat residual); what is defensible when claimed narrowly is (i) the
alphabet wall with leakage measured at 3.4 pp, (ii) config-only onboarding
across five classes with no source change, (iii) the six dataset errata, and
(iv) a *reporting standard* — per-channel and union false-alarm rates with
the day as the decision unit — rather than a method.

## 2. What the reviews found wrong, and what is already fixed today

Fixed and pushed (ad8002f, 256380d, 62cf901, c6a5b60):
- README banner no longer claims discovered models locate invariants; the
  table now prints the naive-union false-alarm rate beside the deployed one
  and the time-to-detect tail; the cry-wolf ratio (an artefact of fault days
  outnumbering fault-free days ~50:1) is gone.
- The library facade (`core/pipeline.py`) still carried the pre-X19 silence
  rule (`OCCUPIED > 0`); it now keys on operate minutes like the scripts,
  with a guard test. The same defect class the fifth system taught had
  recurred inside the library.
- The regression gate fails an artefact whose script exits without rewriting
  it; the week-0 audit script now emits the E5 note it had carried by hand
  (gate 44/44).
- `significance.py` docstring states the residual/model floor honestly
  (max(fp,1)/n, weaker than rule-of-three; no verdict flips on five systems).

Still open from the reviews (carried into the plan):
- Residual bands at the sensor-precision floor: the FCU supply-air band is
  exactly the 0.5 °F width floor, and field duct sensors are ±0.36–0.9 °F.
- Gates that trade a fault mode for healthy silence (DDAHU cold-deck SAT
  gated on static; fan saturation *is* a fault mode).
- Controller-tuned thresholds (DDAHU zone-damper 0.42/0.60 from idle rest
  values) and fan-law proxies that ignore ΔP ∝ ω².
- Standing alarms never close (rules fire 365/365 on 20 of 48 FCU files).
- Localisation evidence covers 61 of 146 detections; no precision@1 number.
- 24 of 28 test files assert literals copied from the JSON they read; one
  test recomputes from raw data and it skips in CI.
- Two of five systems have no acquisition path in REPRODUCING.md.
- Semantic constants encoding a full one-minute calendar year, northern
  seasons, a 30-day window, a 0.05 rarity cutoff and the residual rule's
  name are hard-coded in `src/` (list in the gap audit).

## 3. Corrections to the reviewers

- The research agent called the ORNL laboratory RTU "roughly 120 healthy
  days". Measured: the unfaulted files hold **14 clean days** (8, 2, 2, 2 by
  season); each fault is a single day. The domain expert is right that this
  is a qualitative transfer case, not a sixth scorecard.
- The field RTU subset is two real units with refrigerant-side points, one
  fault each, no command/position pairs. Its value is the **only real
  fault-free stream in the project**: Site 2 has ~181 clean days. It can test
  the false-alarm budget on real data; it cannot support a detection claim.

## 4. The plan, ranked

Each item is pre-registered before it runs, with the falsifier stated.
Effort is one person with the existing tooling.

### Tier A — make the record safe and the science answerable (1–2 weeks)

| # | action | hypothesis / falsifier | effort | what it produces |
|---|---|---|---|---|
| A1 | **Positive control for conformance** (X22): inject genuine order violations (skips, swaps, duplicated blocks) into healthy state logs at graded rates; the model channel must fire above its floor. | P: fires at ≥ 10 % injection on all five systems. F: silent on any system → the null is attributable to the pipeline; report as such. | 4–6 days | the one experiment that converts the ERPM null from "we found nothing" to "the instrument works and there was nothing to find" |
| A2 | **Method-coverage grid** (X23): miners (inductive, heuristics), noise 0.0/0.2/0.5, case notion (day, occupied period), conformance measure (alignment fitness, token replay, **stochastic alignment**, timed). | P: no cell detects a scenario the deployed channels miss. F: any cell does → bound the null and adopt the cell under the budget. | 3–5 days compute | closes "wrong instrument" |
| A3 | **Disclose E1–E6 to LBNL** through the OpenEI contact; check release notes for prior mention; record the dated disclosure in R2PM. | — | 1 day + waiting | precondition several venues apply |
| A4 | **Statistical repair**: rule-of-three floor for residual/model; three-way discover/calibrate/test split so model and device false-alarm rows are out-of-sample; multiplicity statement across ~750 tests; repeated holdouts with intervals. | P: no scenario changes status (checked for the floor on five systems already). F: any change → report which and why. | 3–4 days | removes the two "calibration-target" rows every reviewer flags |
| A5 | **Reconcile public claims**: footnote the tenth adverse result as post-hoc in the manuscript title area, present sensor-bias recall unconditionally (raw ≈ 40 %), state alarm lifecycle (standing alarms) as a limitation, add DDAHU/FCU acquisition rows to REPRODUCING. | — | 1 day | removes the easiest reviewer kills |

### Tier B — improve detection with physics, healthy-calibrated (2–3 weeks)

| # | action | hypothesis / falsifier | effort | target |
|---|---|---|---|---|
| B1 | **Dual-bracket outdoor-air fraction** (temperature form and humidity-ratio form; use the better-conditioned bracket; compare to damper command). Guideline 36 FC6 lineage. | P: FCU 20 % damper leak becomes significant inside budget. F: stays insignificant. | 2 days | 1 miss; the most conspicuous gap in an "APAR-lineage" rule set |
| B2 | **Fan-law virtual static** from speed, flow and power on DDAHU (healthy fit; residual names one sensor and one relation). | P: ≥ 7 of 8 DDAHU static-bias scenarios inside budget (now 5/8). F: < 7. | 4 days | 3 misses |
| B3 | **Fouling as UA / effectiveness with degradation trending** (LMTD from EWT/LWT/flow/MAT/SAT on DDAHU and FCU), plus valve-position-at-matched-load and fan-affinity airflow residuals. Pre-register the expected failure on FCU cooling waterside (signal ≈ 1σ of instruments) so the negative is not a surprise. | P: ≥ 3 of 7 DDAHU fouling misses and ≥ 2 of 5 FCU misses inside budget. F: fewer. | 5–7 days | the dominant miss family |
| B4 | **Refrigerant-side observability test** on the simulated RTU (condenser/evaporator fouling 10–50 % with pressures and temperatures recorded). | P: fouling is detectable when refrigerant-side points exist. F: still undetected → the miss belongs to the method, not the points; reframe. | 3 days | converts the main weakness into a measured claim either way |

### Tier C — real data and deployability (3–6 weeks)

| # | action | hypothesis / falsifier | effort | target |
|---|---|---|---|---|
| C1 | **False-alarm budget on real data**: field RTU Site 2 (181 clean days, 25 refrigerant-side points) with a refrigerant-vocabulary config (superheat, subcooling, compressor power vs OAT). Report per-channel and union false-alarm and abstain rates; a detection claim at n = 2 faults is not made. | P: deployed union ≤ 10 % on real days. F: > 10 % → the budget does not survive real noise; report the channels that broke. | 4–5 days | first non-simulated number in the project |
| C2 | **ORNL real-hardware RTU** as a qualitative transfer case: config-only onboarding; do the signature rules fire on the correct single day for damper-stuck and setpoint faults, with the 14 clean days silent? No budget, no significance. | F: a `src/` change is needed, or clean days fire. | 3–4 days | evidence that rules written from documentation transfer to physical equipment |
| C3 | **Noise and schedule injection** (extends X9/X10): sensor error ±0.36–0.9 °F, 5 % damper feedback resolution, change-of-value sampling with gaps, holiday and optimum-start shifts. | P: budget holds at ≤ 2× on every system. F: any system exceeds. | 4 days | answers the domain expert's failure modes 2, 3, 5 |
| C4 | **Repair the Guideline 36 / open-fdd comparison** under the pre-registered equipment-matched protocol; add the Lin–Kramer–Granderson 2020 day-level comparator (TPR 70–94 % at FPR 36–86 %) as the published reference. | — | 3–4 days | the external baseline; turns the 1–5 % budget into a headline against practice |
| C5 | **Data-hygiene and alarm-lifecycle layer**: flatline/range/staleness gates before abstraction; standing-alarm suppression; portfolio-level budget statement. | — | 4–6 days | deployability (TRU LCDES) |

### Tier D — engineering (parallelisable)

| # | action | effort |
|---|---|---|
| D1 | Make the facade the only detector: `benchmark.py` and `union_fpr.py` become thin consumers; facade test on all five systems (currently SDAHU only). | 4–6 days |
| D2 | Move every semantic constant into a validated config schema (units, sampling interval, season map, holdout policy, rarity and inclusion cutoffs, residual channel names) with a "N rules skipped, sensors X unmapped" report. | 3–4 days |
| D3 | Regression gate: dataless CI tier with a synthetic fixture that recomputes one end-to-end scorecard. | 2 days |
| D4 | Brick auto-configuration from the shipped TTLs (the RTU archive has two; the G5 gate already parses them). Falsifier: coverage < 80 % or any scorecard byte changes. | 6–8 days |
| D5 | Toolkit: `ingest/validate/fit/score/report` CLI, config template, CONTRIBUTING, archived release with a DOI; ICPM demo track. | 1–2 weeks |

## 5. The "AI layer" question

Answer: not as a detector, possibly as an explanation layer, and only with a
measured benefit.

- No 2025–2026 language-model paper on building FDD reports a false-alarm
  rate on fault-free operation or calibrates healthy-only; the one on LBNL
  data uses a supervised split. Time-series foundation models lose to
  one-line statistical baselines on public anomaly benchmarks. Adding one as
  a detector imports the flaw this project was built to avoid.
- A hybrid "conformance features into an ML classifier" (the proposal's RQ3)
  has nothing to carry: the conformance features add zero detections, and a
  supervised classifier needs labelled faults, which the healthy-only design
  rejects.
- What could be tested honestly: an LLM that turns a fired channel, its
  device and its physical statement into a technician-facing explanation
  and a ranked list of root-cause candidates (seized actuator vs linkage vs
  position sensor). The measurable outcome is time-to-correct-diagnosis in
  a small operator study, not detection. That needs human subjects and is a
  paper on its own; it is listed, not scheduled.

## 6. Recommended order

A5, A3 (a day each) → A1 (the single biggest lever) → B1 (two days, one
miss) → A4 → C1 (first real number) → B2, B3, B4 → A2 → C3, C2 → C4 → D1–D3
alongside → C5, D4, D5 last.

## 7. Sources the reviews relied on

- Lin, Kramer, Granderson 2020 (day-level comparator with FPR): https://escholarship.org/uc/item/5cb0g38t
- Frank et al. 2019 (LBNL evaluation protocol): https://doi.org/10.1016/j.enbuild.2019.03.024
- Random scores beat point-adjusted F1: https://arxiv.org/abs/2109.05257
- TSB-AD (statistical methods dominate): https://thedatumorg.github.io/TSB-AD/
- PNNL bracket checks and damper leakage: https://www.pnnl.gov/main/publications/external/technical_reports/pnnl-19104.pdf
- Stochastic alignments: https://arxiv.org/abs/2507.06472
- LBNL RTU documentation: https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU.pdf
