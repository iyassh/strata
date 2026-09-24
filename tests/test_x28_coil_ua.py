"""Guard: X28 — coil UA channel. Run 1 (both systems with the channels): no
fouling scenario gained on DDAHU (5/12) or FCU (6/11); FCU residual false
alarms 3 -> 5, deployed 4 -> 6 (F-X28.a: removed there); F-X28.b fired.
DDAHU keeps the channels inert (45/55 at 3/96)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "outputs"


def test_x28_run1_pinned():
    p = ROOT / "x28_coil_ua_run1.json"
    if not p.exists():
        pytest.skip("artifact absent")
    a = json.loads(p.read_text()); s = a["systems"]
    assert "F-X28.b" in " ".join(a["falsifiers_fired"])
    assert (s["ddahu"]["fouling_before"], s["ddahu"]["fouling_after"], s["ddahu"]["fouling_scored"]) == (5, 5, 12)
    assert (s["fcu"]["fouling_before"], s["fcu"]["fouling_after"], s["fcu"]["fouling_scored"]) == (6, 6, 11)
    assert (s["fcu"]["deployed_fp_before"], s["fcu"]["deployed_fp_after"]) == (4, 6) and (s["fcu"]["residual_fp_before"], s["fcu"]["residual_fp_after"]) == (3, 5)
    assert (s["ddahu"]["deployed_fp_before"], s["ddahu"]["deployed_fp_after"]) == (3, 3)
    assert all(not v["gained"] and not v["lost"] for v in s.values())


def test_fcu_config_has_no_ua_channels_and_ddahu_keeps_them():
    import yaml
    fcu = yaml.safe_load((ROOT.parent / "configs/lbnl_fcu/rules.yaml").read_text())
    dd = yaml.safe_load((ROOT.parent / "configs/lbnl_ddahu/rules.yaml").read_text())
    assert "chwc_ua" not in fcu["events"] and "chwc_ua" not in fcu["detection"]["residual_channels"]
    assert "chwc_ua" in dd["detection"]["residual_channels"] and "hwc_ua" in dd["events"]
