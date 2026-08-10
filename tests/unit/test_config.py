from processheal.io.config import load_config


def test_config_maps_canonical_names():
    cfg = load_config("configs/lbnl_sdahu")
    assert cfg.sensors["OA_DMPR_POS"] == "OA_DMPR"
    assert cfg.sensors["CHWC_VLV_CMD"] == "CHWC_VLV_DM"


def test_config_loads_live_event_thresholds():
    cfg = load_config("configs/lbnl_sdahu")
    # the LIVE keys the pipeline actually reads (the audit removed dead blocks)
    assert cfg.rules["events"]["economizer"]["high"] == 60.0
    assert cfg.rules["events"]["damper_command_mismatch"]["threshold"] == 0.05
    assert cfg.rules["detection"]["fpr_quantile"] == 0.01
