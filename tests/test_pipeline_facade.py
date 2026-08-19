"""T3 facade guards: MIT-clean import path + regression vs committed artifacts.

The heavy regression (fit on SDAHU healthy, reproduce union_fpr channel
counts) self-skips without the data symlink, like test_pipeline.py.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_import_is_pm4py_free():
    """Importing the facade (and everything the MIT-clean channels need)
    must NOT pull pm4py — the AGPL boundary of LICENSING-NOTES.md."""
    code = (
        "import sys; sys.path.insert(0, 'src');"
        "import processheal.core.pipeline, processheal.core.significance,"
        "processheal.core.splits;"
        "assert 'pm4py' not in sys.modules, 'pm4py leaked into the clean path'"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_significance_gates_pure():
    sys.path.insert(0, str(ROOT / "src"))
    from processheal.core import significance as S

    # rule of three: 3 fire-days on 365 evaluable is NOT detection
    assert not S.rules_significant(3, 365)
    assert S.rules_significant(50, 365)
    # residual: k=0 never significant; near-half of windows always is
    assert not S.residual_significant(0, 148, 0, 36)
    assert S.residual_significant(70, 148, 0, 36)
    # device: Bonferroni + 2x margin, per-device
    any_sig, devs = S.device_significant({"TU_S": 36, "TU_I": 1}, 365, 4, 384, 4)
    assert any_sig and devs == ["TU_S"]
    # absence: rare-silence device far above healthy rate
    assert S.absence_significant({"boiler": (200, 300, 0.0)})
    assert not S.absence_significant({"boiler": (2, 300, 0.0)})


@pytest.mark.skipif(
    not (ROOT / "data/processed/sdahu/AHU_annual.parquet").exists(),
    reason="LBNL data not present",
)
def test_facade_reproduces_union_fpr_sdahu():
    """fit() + score() on the SDAHU healthy year must reproduce the
    committed per-channel healthy full-year flag counts in
    outputs/union_fpr_sdahu.json (the Phase-6 audited numbers)."""
    sys.path.insert(0, str(ROOT / "src"))
    import pandas as pd

    from processheal.core.pipeline import fit
    from processheal.io.config import load_config

    art = json.loads((ROOT / "outputs/union_fpr_sdahu.json").read_text())
    cfg = load_config(str(ROOT / "configs/lbnl_sdahu"))
    df = pd.read_parquet(ROOT / "data/processed/sdahu/AHU_annual.parquet")
    det = fit(cfg, df)
    s = det.score(df)

    expected = {  # union_fpr channel name -> facade channel name
        "rules": "rules", "resid": "residual", "model": "model",
        "device": "device", "absence": "absence", "freq": "frequency",
        "osc": "oscillation",
    }
    for art_name, fac_name in expected.items():
        assert int(s["channels"][fac_name].sum()) == \
            art["channels"][art_name]["full_year_days"], fac_name
    assert int(s["rate_diagnostic"].sum()) == art["channels"]["rate"]["full_year_days"]
    # deployed union excludes rate: healthy year must be quiet
    deployed_full_year = int(s["deployed_union"].sum())
    naive_with_rate = int((s["deployed_union"] | s["rate_diagnostic"]).sum())
    assert deployed_full_year < naive_with_rate  # rate demotion visible
    # evaluate(): a healthy year must NOT be "detected"
    rep = det.evaluate(df)
    assert rep["detected"] is False, rep["meaningful_channels"]
    # provenance disclosure present (L24)
    assert "calibration target" in rep["provenance"]["model"]

    # fault-side regression: damper_stuck_010 is rules-carried, TTD 1 in v12
    fdf = pd.read_parquet(ROOT / "data/processed/sdahu/damper_stuck_010_annual.parquet")
    frep = det.evaluate(fdf)
    assert frep["detected"] is True
    assert "rules" in frep["meaningful_channels"]
    assert frep["ttd_days"] == 1
    assert int(frep["counts"]["rules"]) == 365  # v12: rules_days 365
    # rate fires 211 raw days on this scenario but its every-30th-day
    # decision gate is NOT significant in v12 (meaningful_channels ==
    # "rules" alone) — the facade must agree, and rate must never appear
    # in the deployed meaningful list regardless
    assert "rate" not in frep["meaningful_channels"]
    assert frep["rate_corroborates"] is False
