# Pre-registration — open-fdd traditional-rules baseline (D1)

**Written 2026-09-11, BEFORE any scoring run.** Project law: expectations and
falsifiers are committed before the experiment, never after. This document is
committed in its own commit; the adapter and the run land in later commits.

**Purpose.** Grade the standard industry method on STRATA's exam. `open-fdd`
(PyPI, MIT, third-party, v4.4.1) implements the ASHRAE Guideline 36 AHU fault
conditions — the same standard commercial BMS vendors advertise compliance
with. Using an independent implementation kills the strawman objection: we did
not write our competitor.

---

## 0. Deviation from the sprint plan (decided before running, with reason)

The plan specified mapping **our canonical sensors** to open-fdd's inputs. That
is wrong and would rig the result, so it is overridden here:

STRATA's canonical layer is a deliberate subset — SDAHU maps 12 of 30 raw
columns, because those 12 are all STRATA needs. The unmapped 18 include
`SF_CS`/`SF_SPD` (fan), `SA_SP`/`SA_SPSPT` (duct static), `SA_CFM` (airflow).
Mapping canonical-only would starve the battery of `fan-cmd` and silently
disable **six** of its fifteen conditions, including FC1 — and we would then
report "traditional rules miss fan faults" when in fact we withheld the fan
sensor.

**Decision: the adapter maps from the RAW dataset columns.** The battery gets
every sensor the building physically has. A sensor is declared missing only
when it is absent from the raw file. Approved by the user 2026-09-11.

**Scope decision.** open-fdd 4.4.1 ships 62 canonical rules, 41 AHU-applicable.
The **headline comparison is FC1–FC15**, the published Guideline 36 conditions.
The other 26 AHU rules (`ECON-*`, `SV-*`, `SCHED-*`, `TRIM-*`, `PID-HUNT-*`)
are open-fdd's own additions, not the standard; they are reported as a
secondary "full battery" row so we cannot be accused of grading the weak
version. No parameter of any rule is altered — defaults are the as-deployed
condition.

---

## 1. Adapter contract

open-fdd 4.4.1 addresses inputs by **role**, not column name (36 roles for AHU
rules). The adapter maps raw column → role, per system.

### Shared mapping (all three systems)

| open-fdd role | raw column | notes |
|---|---|---|
| `outside-air-temp` | `OA_TEMP` | °F, matches open-fdd hard range |
| `discharge-air-temp` | `SA_TEMP` | °F |
| `discharge-air-temp-sp` | `SA_TEMPSPT` | °F; constant in all three datasets |
| `mixed-air-temp` | `MA_TEMP` | °F |
| `return-air-temp` | `RA_TEMP` | °F |
| `cooling-valve` | `CHWC_VLV` | 0–1 fraction, matches defaults directly |
| `outside-air-damper` | `OA_DMPR` | 0–1 fraction |
| `occupied` | `SYS_CTL` | see per-system encoding below |

### Unit conversions (REQUIRED — verified from data, 2026-09-11)

1. **Duct static pressure is not in the same unit on both systems.**
   - SDAHU: `SA_SP` spans 401.8–410.6 while `SA_SPSPT` = 1.607 → `SA_SP` is
     **pascals**, the setpoint is **inH₂O** (402 Pa = 1.610 inH₂O ✓).
     Adapter divides `SA_SP` by **249.0889** before use.
   - PFPU/SFPU: `SA_SP` spans 0–2.49 against a 1.4 setpoint → already
     **inH₂O**. No conversion.
   Passing raw pascals against an inches setpoint would fire FC1 on every row
   and manufacture a ~100% false-alarm rate. This conversion is part of the
   contract, not a tuning choice.
2. **Airflow scale differs.** SDAHU `SA_CFM` reaches 1.27e6; PFPU/SFPU reach
   ~1.9e3. Only FC6 consumes it, and only as a `min_cfm_design=5000` gate (its
   OA-fraction test is temperature-based). The adapter passes airflow through
   unconverted and **FC6's verdict is reported with an explicit
   airflow-units caveat** rather than being silently trusted.

### Fan role, per system (the signals differ in meaning)

| system | `fan-cmd` | `fan-status` | evidence |
|---|---|---|---|
| SDAHU | `SF_SPD` (constant 0.900) | `SF_SPD_DM` (binary) | `SF_SPD` has 1 unique value → constant-speed fan; `SF_CS` is continuous 0–1 (fan current sensor, `SF_WAT` is its power) |
| PFPU/SFPU | `SF_SPD` (0–0.810, 67 levels) | `SF_CS` (binary) | roles are **inverted** vs SDAHU |

SDAHU's constant `SF_SPD` = 0.900 sits above FC1's `fan_hi` = 0.87 default,
so FC1 will treat the fan as always at high speed on SDAHU. This is a genuine
property of the dataset, is recorded here in advance, and will be reported —
not corrected.

### Occupancy encoding
- SDAHU: `SYS_CTL` ∈ {0,1} → used directly.
- PFPU/SFPU: `SYS_CTL` ∈ {0,1,2} → occupied ≔ `SYS_CTL > 0`.

### Conditions that cannot run, with the missing sensor (honest accounting)

| condition | SDAHU | PFPU / SFPU |
|---|---|---|
| FC5, FC7 | **unrunnable** — no heating valve (`HWC_VLV` absent; cooling-only AHU) | runnable (`HWC_VLV`) |
| FC15 | **unrunnable** — no heating-coil water temps | runnable (`HWC_EWT`/`HWC_LWT`) |
| FC14 | **unrunnable** — no chilled-water coil temps | runnable (`CHWC_EWT`/`CHWC_LWT`) |
| FC1–FC4, FC6, FC8–FC13 | runnable | runnable |

Caveat recorded in advance: on PFPU/SFPU the coil **entering** temps are
constants (`CHWC_EWT` = 45.0, `HWC_EWT` = 120.0, 1 unique value each), so
FC14/FC15 effectively test the leaving temp alone. Reported, not corrected.

---

## 2. Scoring protocol

Identical exam to STRATA — no separate grading curve.

- **Day-level roll-up:** a day is flagged by the battery if **any** fault
  condition fires on **any** row of that day. (The battery's advantage:
  fifteen independent chances per day.)
- **Scenarios:** the same non-excluded scenarios STRATA is graded on —
  SDAHU 14, PFPU 30, SFPU 29 (1 excluded) = **73**.
- **Clean-year false positives:** measured on the **same last-8-days-per-month
  holdout days** used by STRATA's calibration, for comparability; the
  **full clean year** FP day-rate is reported alongside it.
- **Day universe:** from the raw calendar via the shared helper (L6/L22), the
  same helper STRATA uses. No bespoke day construction.
- **No parameter is tuned.** Defaults as installed, recorded in the artifact.

**Artifacts:** `outputs/openfdd_baseline_{sdahu,pfpu,sfpu}.json` — per scenario:
flagged days; clean year: holdout + full-year FP days; per fault condition:
fired / not-fired / unrunnable-missing-sensor. Guard tests pin every number
before any of it is quoted anywhere.

---

## 3. Expectations (stated before seeing any result)

- **E1 — The battery catches mechanical-mismatch families.** Stuck dampers,
  stuck/leaking valves and similar produce the steady-state temperature and
  position contradictions FC2/FC3/FC6/FC8–FC13 are built to catch. If STRATA's
  only advantage were on these, the project's contribution would be thin.
- **E2 — The battery misses bias, rhythm and instability families.** Sensor
  bias shifts the whole envelope consistently, so threshold tests on that
  envelope stay satisfied; degradation-over-time and control-rhythm faults have
  no static-threshold signature at all. These are the families STRATA's
  event/rhythm channels exist for.
- **E3 — The battery's clean-year false-alarm day-rate exceeds STRATA's
  deployed 1.0–5.2% band.** Fifteen unbudgeted conditions each firing on any
  row of a day, with no per-channel noise floor and no statistical gate,
  should produce substantially more flagged clean days.

---

## 4. Falsifier (binding)

**F1 — If, on any system, the battery's detected-scenario count is ≥ STRATA's
at a clean-year false-positive rate ≤ STRATA's, then the "better than
traditional rules" claim is dead for that system and will be reported as
dead** — in the results doc, the deck, and the paper, with the number that
killed it.

No partial credit, no re-framing after the fact, no quiet scope narrowing to
the systems where we win. Project law: every fired falsifier is honored in
print.

Secondary honesty condition: if the battery underperforms only because of
unrunnable conditions, that must be stated as a **sensor-availability** result,
not a capability result — the count of unrunnable conditions is reported beside
every score.
