"""Guard (X33): for every system whose sensors.yaml declares `coverage_audited: true`,
every numeric column of its fault-free file is either mapped in canonical_to_csv or
listed under `unmapped:` with a written reason. A recorded column can no longer go
unread silently."""
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
SYSTEMS = {"sdahu": "AHU_annual", "pfpu": "PFPU_FaultFree", "sfpu": "SFPU_FaultFree", "ddahu": "DualDuct_FaultFree", "fcu": "FCU_FaultFree"}


@pytest.mark.parametrize("system,healthy", list(SYSTEMS.items()))
def test_every_column_mapped_or_excluded(system, healthy):
    cfg = yaml.safe_load((REPO / f"configs/lbnl_{system}/sensors.yaml").read_text())
    if not cfg.get("coverage_audited"):
        pytest.skip(f"{system}: coverage audit not yet done (X33 series)")
    data = REPO / f"data/processed/{system}/{healthy}.parquet"
    if not data.exists():
        pytest.skip("data absent")
    cols = pd.read_parquet(data, columns=None)
    numeric = {c for c in cols.columns if c != "Datetime" and pd.api.types.is_numeric_dtype(cols[c])}
    mapped = set(cfg["canonical_to_csv"].values())
    excluded = cfg.get("unmapped", {}) or {}
    for c, reason in excluded.items():
        assert isinstance(reason, str) and len(reason) > 10, f"{system}: {c} excluded without a reason"
        assert c not in mapped, f"{system}: {c} both mapped and excluded"
    unread = sorted(numeric - mapped - set(excluded))
    assert unread == [], f"{system}: numeric columns neither mapped nor excluded: {unread}"
