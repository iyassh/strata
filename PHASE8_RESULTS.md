# Phase 8 Results — The Missing Experiments (X11, X8, X5, X7)

Pre-registered in PHASE8_PLAN.md (commit 65fe3b8 before any computation;
X7 addendum committed before X7 ran). Artifacts:
`outputs/x11_branch.json`, `x8_contamination.json`, `x5_severity.json`,
`x7_downsample.json`. Scripts: `scripts/x{11,8,5,7}_*.py`.

## X11 — branch adjudication: **ADJUDICATED, SDAHU is 13/14**

All four pre-registered hypotheses held. Honest falsifier accounting
(audit-corrected wording): **F-X11.d FIRED on the first run** under one
admissible reading of battery leg (a) (SYS_CTL>0 — the reading closest to
the pipeline's own residual gating, occ_above 0.5). Diagnosis: the entire
day-difference is night-cycle runtime (==2), fault-responsive; scheduled
occupancy (==1) is identical to the minute. Leg (a) was re-specified to
the scheduled state post hoc — a resolved ambiguity in the pre-registered
text, reported as such, NOT as a clean pass. Leg (c) independently covers
the night-cycle-inclusive windows: the full rmtemp family (±2C, ±4C,
Unstable) sits inside the healthy bands — PFPU by a razor 0.01 °F margin,
stated. No other falsifier fired.

- **H-X11.1 ✓** Five independent estimators of the fault-branch no-fault
  residual baseline agree to **0.001 °F** (coi_bias ladder debiased:
  0.008, 0.008, 0.008, 0.008; oa_bias as-is: 0.007). Branch offset
  δ = **+1.0625 °F**; corrected band [−0.536, +0.310].
- **H-X11.2 ✓** oa_bias under the corrected band: **0 flags on its 148
  evaluable window days (365 calendar days)** — was 148/148. Its only
  deployed significant channel vanishes →
  **adjudicated scorecard 14/14 → 13/14**. The residual channel's oa_bias
  "detection" was branch provenance (ERRATA E5), exactly the trap E3
  documents for ML baselines — caught by our own protocol (L28's
  fault-vs-fault control), not by a reviewer.
- **H-X11.3 ✓** All four coi_bias scenarios keep every window-day
  detection under the corrected band (164/164, 164/164, 139/139,
  137/137) — margins of 3.0–7.5 °F dwarf the 1.06 offset. Perfect debias
  consistency: day-level debiased coi_bias series flag 0.0% against the
  corrected band. damper_stuck 075/100 residual days survive too
  (155, 70) — corroboration intact.
- **H-X11.4 ✓** FPU homogeneity battery clean: scheduled-occupancy
  (SYS_CTL==1) day-difference **exactly 0 minutes** on every PFPU and
  SFPU file; zero damper-floor mismatches; rmtemp_bias residual medians
  inside the healthy bands. "FPU unaffected by E5" is now an artifact,
  not an assertion.
- **Left-tail honesty (audit finding):** oa_bias has a real left tail
  (min −0.83, p1 −0.71; 4/148 days below the corrected band edge, 0 past
  the 0.5 °F flag line). Under ANY band-width choice the tail stays below
  the significance floor — the verdict is "no SIGNIFICANT SA-path
  deviation," not "residual identically at baseline." The audit
  stress-tested a razor fault-branch band (IQR 0.0047, ~40× tighter than
  healthy's): still ~4/148, p≈0.03 ≫ 1e-3 — 13/14 is robust to the band
  construction. (Instrument-correction ledger: L29.)

**Consequences (to land in the docs after this phase's audit):** paper
quotes "14/14 naive; **13/14 after branch correction (ERRATA E5)**"; PCA
comparison becomes **60 v 61** ("near-tie, complementary misses" — PCA
also misses oa_bias); D2's narrative is reframed: the file IS faulty
(cooling-interlock evidence, fault-vs-fault), but our channel detected
its branch, not its fault.

## X8 — contamination: **extreme-value calibration breaks at ONE silent-fault day (demonstrated)**

All three hypotheses held; both falsifier checks clean. The breakdown is
now demonstrated literally (audit fix, `k="1day"` rows): **a single
score-carrying contaminated day** drops the train-min band edge to −7.19
and collapses **coi_bias_-4 AND −2 coverage 164/164 → 0/164**. The
k-sweeps confirm k = 2/5/10% add nothing further (note: 2 of the 5 k=2%
days abstain in the worst-case source — only 46% of its train days carry
scores). Positive-side
coverage (139/139, 137/137) and healthy-holdout FP (0) are untouched;
frequency bands never widen.

The mitigating structure is real and measured: the mild contamination
(damper_stuck_010) drifts NOTHING (band unchanged at every k, zero
recall loss) — and **100% of its contaminated days are visible to the
rules channel** (5/5, 13/13, 27/27 signature days), while the dangerous
contamination is signature-silent (0/27). Honest paper sentence: *the
fault-free-training assumption is load-bearing specifically for faults
that are silent in the signature alphabet; contamination the physics
rules can see announces itself. Robust (quantile) calibration with an
honest FP ladder is the designed future fix; the exceedance floor does
not help against a −7 °F contaminant.*

## X5 — severity monotonicity: **dose ladders positive, no anti-monotone ladder**

- No ladder is significantly anti-monotone (falsifier clean; H-X5.1 ✓).
- True DOSE ladders behave: SFPU fouling ρ = +0.87 (air and water — a
  severe-only step, honestly a step not a slope), |rmtemp bias| ρ =
  +0.45/+0.87, reheat-stuck-vs-open ρ = +0.71 with 4/5 rungs at the
  365-day ceiling (reported).
- **Audit correction (regex bug, fixed and rerun):** the airflow-bias
  ladders were silently dropped by a `-?` regex that cannot match
  `+200CFM` filenames — a pre-registered ladder missing from the first
  artifact. Fixed: PFPU airflow is a flat plateau (271 days at every
  rung; ρ undefined), SFPU ρ = +0.24. No anti-monotone finding; the
  omission is disclosed here per L26/L27.
- **Symmetric position-ladder handling (audit prescription):** BOTH stuck
  families (damper 0–100% AND reheat-valve 0–100%) are position ladders,
  not dose ladders — classifying reheat as "dose" because its ρ is +0.71
  was convenient, not principled. The honest reading: reheat's ladder is
  a STEP driven entirely by the 0% rung (stuck-closed = loss of function,
  193/137 days) with 4/5 rungs at the 365-day ceiling; damper's ρ (−0.05,
  0.00) is meaningless by design. Both reported as position ladders.
- PFPU fouling is undetected by deployed channels (all-zero → ρ
  undefined): dose-response is unmeasurable where the family is unseen —
  a sensor-coverage fact (waterside ΔT), not a monotonicity failure.
- F-X5.a is nearly unfireable at these n (only a perfect −1 at n=5
  reaches p<0.05): "falsifier-clean" is weak evidence here; the rung
  tables are the content.

## X7 — 15-min downsample: **falsifiers FIRED (honored); configs are sampling-rate-specific**

F-X7.a fired on all three systems: healthy years gain **28 / 64 / 64**
signature days at 15-min. F-X7.b fired once (PFPU fan_restrict residual
31→1). Fault-side rules inflate (PFPU instability 1→217 days) and the
frequency channel collapses (206→2, 135→8, 141→3). Mechanism — TWO aliasing
sub-mechanisms (audit-verified on a concrete case): (1) **threshold
degeneration**: rules with sustained_min ≤ the sampling interval collapse
to single-instant spot checks (SDAHU's 28 healthy firings are ENTIRELY
this — e.g. valve_leak fired on 2018-05-19 from one 15-min sample whose
1-min record shows 2 violating minutes, longest run 1 minute); (2) **run
merging**: intermittency between samples is invisible, so sub-threshold
runs fuse past sustained-minutes thresholds (the fault-side rules
inflation). Count/oscillation information needs fine sampling.

**The residual channel is the sampling-robust one on SDAHU** (sensor_bias
164→165, oa_bias 148→148; small-count residuals die) — with an honest
H-X7.3 partial miss the falsifiers did not cover: **PFPU's 15-min band is
[−1.64, 2.17] vs 1-min [0.60, 2.17]** — the lower edge moved 2.2 °F, so
daily-median robustness to 15× thinning held on SDAHU only. And a scope
caveat: `iloc[::15]` models SNAPSHOT/polled logging; interval-AVERAGED
15-min data (also common in BAS trends) is a different noise process and
is untested.

**Scoping this forces (the honest claim):** the METHOD transfers — the
onboarding healthy-silence gate re-tunes sustained-minutes thresholds on
the target site's own data at its own sampling rate (its designed job) —
but **tuned configs are sampling-rate-specific and must never be
transplanted across rates**, and the frequency/oscillation channels are
structurally fine-sampling instruments. The transfer claim is scoped to
"config-only onboarding at a comparable sampling rate; rate changes
re-run the silence gate." Demonstrating full re-tuned 15-min performance
is future work; the fired falsifier is the result we report.

## Phase scoreboard

| Experiment | Verdict | Headline |
|---|---|---|
| X11 | ADJUDICATED, falsifier-clean | **SDAHU 13/14**; PCA 60v61; FPU homogeneity is an artifact |
| X8 | Hypotheses held | Breakdown at ONE silent-fault day; rules-visible contamination announces itself |
| X5 | Falsifier-clean | Dose ladders positive; position ladders and unseen families honestly scoped |
| X7 | **Falsifiers FIRED, honored** | Configs are sampling-rate-specific; residual channel robust; freq/osc are 1-min instruments |

## Pre-registration deviations (full disclosure, per audit)

Six deviations beyond the documented F-X11.d correction — none flips a
verdict; all disclosed:
1. X11 significance first ran with a healthy all-days noise rate instead
   of the registered benchmark formula — fixed, rerun with
   p0 = max(holdout FP, 1)/holdout evaluable; outcome unchanged.
2. X11 leg (c) first tested only the ±2C rmtemp files (glob bug) — now
   the full family (±2C, ±4C, Unstable), all inside band.
3. X8's registered "monthly rate bands" recompute was scoped out (rate is
   diagnostic-only since Phase 6 and branch-confounded on SDAHU since
   X11; no deployed consequence) — stated in the artifact.
4. X8 contaminates at the daily-aggregate level, not row level — exactly
   equivalent for the residual channel; two structural frequency caveats
   stated in the artifact (state-alphabet-only counts; column reindex).
5. X5's airflow ladders were dropped by a regex bug on the first run —
   fixed, rerun, disclosed above.
6. X7's F-X7.b check covered rules+residual only, narrower than the
   registered "any family's coverage"; the frequency collapse is reported
   openly and scoped instead — disclosed.

## Ledger

- **L29** (X11 first run): "fault-responsive" and "branch-constant" are
  different axes — a homogeneity instrument must condition on the
  scheduled state (SYS_CTL==1), not on any-activity (&gt;0), or fault
  behaviour masquerades as branch difference. Third member of the
  L21/L28 conflation family; the falsifier caught it before adjudication.
- **L30** (X8): an extreme-value threshold's contamination breakdown
  point is exactly ONE adversarial day — but detectability of the
  contamination splits on signature-visibility. Report both halves
  together or the finding misleads in either direction.
- **L31** (X7): a threshold tuned to silence at one sampling rate is a
  claim about that rate's noise process, not about the building.
  Sustained-minutes discipline weakens under aliasing; silence gates
  must re-run at the deployment rate.

**Audit status: PASSED with required fixes — all applied above and in the
scripts/artifacts (X5 rerun, X8 1-day rows, X11 registered noise floor +
left-tail + valid JSON, F-X7.b pinned). The 13/14 propagation reframes
land with this commit, per the audited reframe list.**
