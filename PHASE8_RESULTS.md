# Phase 8 Results — The Missing Experiments (X11, X8, X5, X7)

Pre-registered in PHASE8_PLAN.md (commit 65fe3b8 before any computation;
X7 addendum committed before X7 ran). Artifacts:
`outputs/x11_branch.json`, `x8_contamination.json`, `x5_severity.json`,
`x7_downsample.json`. Scripts: `scripts/x{11,8,5,7}_*.py`.

## X11 — branch adjudication: **ADJUDICATED, SDAHU is 13/14**

All four pre-registered hypotheses held; zero falsifiers fired (one
instrument correction en route, below).

- **H-X11.1 ✓** Five independent estimators of the fault-branch no-fault
  residual baseline agree to **0.001 °F** (coi_bias ladder debiased:
  0.008, 0.008, 0.008, 0.008; oa_bias as-is: 0.007). Branch offset
  δ = **+1.0625 °F**; corrected band [−0.536, +0.310].
- **H-X11.2 ✓** oa_bias under the corrected band: **0/365 flags** (was
  148/148 window days). Its only deployed significant channel vanishes →
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
- **Instrument correction (first run fired F-X11.d, diagnosed, fixed):**
  the schedule leg initially compared SYS_CTL &gt; 0, which includes
  night-cycle (==2) — FAULT-RESPONSIVE behaviour (an alphabet event).
  All of the apparent 1201/1230-minute day-diffs were night-cycle;
  scheduled occupancy differs by 0. Same conflation class as L21/L28,
  caught by its own falsifier. (Ledger L29.)

**Consequences (to land in the docs after this phase's audit):** paper
quotes "14/14 naive; **13/14 after branch correction (ERRATA E5)**"; PCA
comparison becomes **60 v 61** ("near-tie, complementary misses" — PCA
also misses oa_bias); D2's narrative is reframed: the file IS faulty
(cooling-interlock evidence, fault-vs-fault), but our channel detected
its branch, not its fault.

## X8 — contamination: **extreme-value calibration breaks at ONE silent-fault day**

All three hypotheses held; both falsifier checks clean. The result, in
one row: with the residual-extreme fault (coi_bias_-4, −7.2 °F) at
**k = 2%** (5 train days), the train-min band edge drops to −7.20 —
**coi_bias_-4 AND −2 coverage collapse 164/164 → 0/164**. k = 5%, 10%
add nothing (the damage is done by the first extreme day). Positive-side
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
- Two honest notes: (1) stuck-POSITION ladders (damper 0–100%) are not
  dose ladders — position 0% is severe too; ρ there (−0.05, 0.00) is
  meaningless by design and reported as such; (2) PFPU fouling is
  undetected by deployed channels (all-zero → ρ undefined): dose-response
  is unmeasurable where the family is unseen — a sensor-coverage fact
  (waterside ΔT), not a monotonicity failure.

## X7 — 15-min downsample: **falsifiers FIRED (honored); configs are sampling-rate-specific**

F-X7.a fired on all three systems: healthy years gain **28 / 64 / 64**
signature days at 15-min. F-X7.b fired once (PFPU fan_restrict residual
31→1). Fault-side rules inflate (PFPU instability 1→217 days) and the
frequency channel collapses (206→2, 135→8, 141→3). Mechanism: aliasing —
intermittency between 15-min samples is invisible, so runs merge and
sustained-minutes thresholds tuned on 1-min healthy silence fire
spuriously; count/oscillation information needs fine sampling.

**The residual channel is the sampling-robust one** (sensor_bias
164→165, oa_bias 148→148; small-count residuals die).

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

Doc reframes (D2/E1/F1/Part V/ERRATA E5, the 13/14 propagation, PCA
sentence) land AFTER this phase's hostile audit, per the plan.
