"""Guard: X24 — outdoor-air-fraction residual (G36 FC6 lineage). FCU gains
the 20 % damper leak (41 -> 42 of 47) at unchanged false alarms (4/96);
SDAHU and DDAHU scorecards keep every detection and every false-alarm count;
no falsifier fired."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "outputs" / "x24_oa_fraction.json"


def test_x24_pinned():
    if not ART.exists():
        pytest.skip("artifact absent")
    a = json.loads(ART.read_text()); s = a["systems"]
    assert a["falsifiers_fired"] == [] and all(a["predictions"].values())
    assert (s["fcu"]["detected_before"], s["fcu"]["detected_after"], s["fcu"]["scored"]) == (41, 42, 47)
    assert s["fcu"]["gained"] == ["FCU_OADMPRLeak_20"] and s["fcu"]["lost"] == []
    assert (s["fcu"]["deployed_fp_before"], s["fcu"]["deployed_fp_after"]) == (4, 4)
    assert (s["sdahu"]["detected_after"], s["sdahu"]["deployed_fp_after"]) == (14, 1) and s["sdahu"]["status_changed"] == {}
    assert (s["ddahu"]["detected_after"], s["ddahu"]["deployed_fp_after"]) == (45, 3) and s["ddahu"]["lost"] == []
    live = json.loads((ROOT / "outputs" / "benchmark_v6_fcu.json").read_text())
    leak = next(x for x in live["scenarios"] if x["file"] == "FCU_OADMPRLeak_20")
    assert leak["meaningful_channels"] == "resid"
