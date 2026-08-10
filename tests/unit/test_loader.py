import pandas as pd

from processheal.io.loader import operating_summary


def test_operating_summary_flags_damper_mismatch():
    # damper commanded near-closed (0.10) but stuck open (0.75) -> mean|diff| = 0.65
    df = pd.DataFrame(
        {
            "OA_DMPR": [0.75, 0.75],
            "OA_DMPR_DM": [0.10, 0.10],
            "CHWC_VLV": [0.0, 0.0],
            "CHWC_VLV_DM": [0.0, 0.0],
            "SYS_CTL": [1, 1],
            "OA_TEMP": [50, 50],
            "SA_TEMP": [55, 55],
        }
    )
    s = operating_summary(df)
    assert round(s["damper_cmd_pos_meanabs"], 2) == 0.65
    assert s["valve_cmd_pos_meanabs"] == 0.0


def test_operating_summary_healthy_has_no_discrepancy():
    df = pd.DataFrame(
        {
            "OA_DMPR": [0.10, 0.10],
            "OA_DMPR_DM": [0.10, 0.10],
            "CHWC_VLV": [0.2, 0.2],
            "CHWC_VLV_DM": [0.2, 0.2],
            "SYS_CTL": [1, 1],
            "OA_TEMP": [50, 50],
            "SA_TEMP": [55, 55],
        }
    )
    s = operating_summary(df)
    assert s["damper_cmd_pos_meanabs"] == 0.0
    assert s["valve_cmd_pos_meanabs"] == 0.0
