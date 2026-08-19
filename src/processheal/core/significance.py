"""Per-channel noise-floor significance gates (Phase 9 / T3 facade).

Lifted verbatim from scripts/benchmark.py lines ~314-368 (the audited v12
logic) so the scientific heart of STRATA — "detected" means significantly
above the channel's OWN measured noise floor — is importable and unit-
testable instead of script-local. Every gate takes plain counts and noise
statistics; nothing here touches data frames or pm4py.

Conventions (all from the phase audits):
- rules: 0 observed FP on a healthy year still only bounds the rate at
  ~3/365 (rule of three) — 1-3 fire-days are NOT detection.
- residual/model/freq/osc: exact binomial vs the channel's holdout rate,
  p < 1e-3, rule-of-three floored where the observed floor is zero.
- device: PER DEVICE (audit A4), Bonferroni across devices, and required
  to hold at 2x the estimated case rate (sensitivity margin).
- rate: scored only on every-30th calendar day (non-overlapping windows,
  audit A2) — and since Phase 6 the rate channel is DIAGNOSTIC-ONLY.
"""

from __future__ import annotations

from scipy.stats import binom

P_SIG = 1e-3
RULE_OF_THREE = 3.0 / 365.0


def binom_sf(k: int, n: int, p: float) -> float:
    """P[X >= k] for X ~ Binomial(n, p); 1.0 when n == 0."""
    return float(binom.sf(k - 1, n, min(p, 1.0))) if n else 1.0


def rules_significant(fire_days: int, n_eval: int) -> bool:
    return binom_sf(fire_days, n_eval, RULE_OF_THREE) < P_SIG


def residual_significant(flag_days: int, n_windows: int,
                         holdout_fp: int, holdout_n: int) -> bool:
    if not n_windows:
        return False
    p0 = max(holdout_fp, 1) / max(holdout_n, 1)
    return binom_sf(flag_days, n_windows, p0) < P_SIG


def model_significant(flag_days: int, n_eval: int,
                      holdout_fp: int, holdout_days: int) -> bool:
    p0 = max(holdout_fp, 1) / max(holdout_days, 1)
    return binom_sf(flag_days, n_eval, p0) < P_SIG


def device_significant(days_by_device: dict[str, int], n_eval: int,
                       case_fp: int, case_n: int,
                       n_devices: int) -> tuple[bool, list[str]]:
    """Per-device binomial, Bonferroni across devices, 2x sensitivity margin.
    Returns (any_significant, list of significant device names)."""
    p_case = max(case_fp, 1) / max(case_n, 1)
    alpha = P_SIG / max(n_devices, 1)
    sig_devices = [
        d for d, k in days_by_device.items()
        if binom_sf(k, n_eval, p_case) < alpha
        and binom_sf(k, n_eval, min(2 * p_case, 1.0)) < alpha
    ]
    return bool(sig_devices), sig_devices


def absence_significant(per_device: dict[str, tuple[int, int, float]]) -> bool:
    """per_device: device -> (silent_days, scheduled_days, healthy_silence_rate).
    Significant if ANY rare-silence device is silent far above its healthy
    rate (rule-of-three floor when the healthy rate is zero)."""
    for _dev, (k_sil, n_sched, hrate) in per_device.items():
        if hrate <= 0.05 and n_sched:
            if binom_sf(k_sil, n_sched, max(hrate, RULE_OF_THREE)) < P_SIG:
                return True
    return False


def frequency_significant(flag_days: int, n_eval: int,
                          unit_fp: int, unit_days: int,
                          dev_fp: int = 0, dev_days: int = 0) -> bool:
    if not unit_days:
        return False
    p0 = unit_fp / max(unit_days, 1)
    if dev_days:
        p0 += dev_fp / max(dev_days, 1)
    p0 = max(p0, 3.0 / max(unit_days, 1))
    return binom_sf(flag_days, n_eval, min(p0, 1.0)) < P_SIG


def oscillation_significant(flag_days: int, n_eval: int,
                            holdout_fp: int, holdout_days: int) -> bool:
    p0 = max(holdout_fp, 3) / max(holdout_days, 1)
    return binom_sf(flag_days, n_eval, min(p0, 1.0)) < P_SIG


def rate_significant(decision_day_flags: int, n_decision_days: int,
                     holdout_fp: int, holdout_days: int) -> bool:
    """Diagnostic-only since Phase 6 — never a lone alarm; kept for the
    corroboration report."""
    p0 = max(holdout_fp / max(holdout_days, 1), RULE_OF_THREE)
    return binom_sf(decision_day_flags, max(n_decision_days, 1),
                    min(p0, 1.0)) < P_SIG
