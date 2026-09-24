"""Guard (X19 Amendment 1, library side): the day universe distinguishes
scheduled minutes (OCCUPIED > 0, incl. setback/night-cycle) from OPERATE
minutes (OCCUPIED == 1), and the silence rule must key on the latter. The
scripts were repaired in 7d52587; the facade had silently kept the old
semantics until the gap audit of 2026-09-24."""
import pandas as pd

from strata.core.pipeline import day_universe


class _Cfg:
    sensors = {"OCCUPIED": "MODE", "Datetime": "Datetime"}


def test_operate_minutes_exclude_setback():
    ts = pd.date_range("2018-01-06 00:00", periods=2 * 1440, freq="1min")   # a Saturday and a Sunday
    mode = [2] * 1440 + [1] * 720 + [0] * 720                                # day 1 all setback; day 2 half operate
    uni = day_universe(pd.DataFrame({"Datetime": ts, "MODE": mode}), _Cfg())
    assert uni.loc["2018-01-06", "occupied_min"] == 1440 and uni.loc["2018-01-06", "operate_min"] == 0
    assert uni.loc["2018-01-07", "occupied_min"] == 720 and uni.loc["2018-01-07", "operate_min"] == 720


def test_silence_rule_uses_operate_minutes():
    import inspect
    import strata.core.pipeline as p
    src = inspect.getsource(p)
    assert '~has_events & (uni["operate_min"] > 0)' in src
    assert '~has_events & (uni["occupied_min"] > 0)' not in src
