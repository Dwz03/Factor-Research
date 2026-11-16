import numpy as np
import pandas as pd
import pytest
from src.evaluation import market_trend_regime


def test_warmup_equality_and_direction():
    s = pd.Series([10., 10., 10., 12., 8.], index=pd.bdate_range('2009-12-29', periods=5))
    original = s.copy()
    labels = market_trend_regime(s, window=3)
    assert labels.iloc[:2].isna().all()
    assert labels.iloc[2:].tolist() == ['Bear', 'Bull', 'Bear']
    pd.testing.assert_series_equal(s, original)


def test_200_day_warmup_missing_and_no_future_dependence():
    s = pd.Series(np.arange(1., 451.), index=pd.bdate_range('2009-01-01', periods=450))
    original = s.copy()
    labels = market_trend_regime(s)
    assert labels.iloc[:199].isna().all()
    assert labels.iloc[199:].eq('Bull').all()
    altered = s.copy()
    altered.iloc[350:] *= 100
    pd.testing.assert_series_equal(labels.iloc[:350], market_trend_regime(altered).iloc[:350])
    pd.testing.assert_series_equal(s, original)
    s.iloc[210] = np.nan
    result = market_trend_regime(s)
    assert result.iloc[210:410].isna().all()
    assert result.iloc[410] == 'Bull'


@pytest.mark.parametrize('window', [0, -1, 2.5, True])
def test_invalid_window(window):
    with pytest.raises(ValueError):
        market_trend_regime(pd.Series([1.], index=pd.to_datetime(['2020-01-01'])), window)


@pytest.mark.parametrize('kind', ['duplicate', 'unsorted', 'zero', 'inf'])
def test_invalid_prices(kind):
    s = pd.Series([1., 2., 3.], index=pd.date_range('2020', periods=3))
    if kind == 'duplicate': s.index = [s.index[0]] * 3
    if kind == 'unsorted': s = s.iloc[::-1]
    if kind == 'zero': s.iloc[0] = 0
    if kind == 'inf': s.iloc[0] = np.inf
    with pytest.raises(ValueError): market_trend_regime(s)


def test_exploration_excludes_future_endpoints_and_later_data():
    from scripts.momentum_regime_001 import exploration_rank_ic
    rng = np.random.default_rng(22)
    dates = pd.bdate_range('2016-10-01', '2017-02-01')
    prices = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, .01, (len(dates), 110)), axis=0)), index=dates)
    ic, endpoints = exploration_rank_ic(prices)
    assert ic.index.max().year == 2016
    assert ic.iloc[-6:].isna().all()
    assert endpoints.exit_date.iloc[-6:].isna().all()
    prices.loc['2017-01-01':] *= 1000
    later, _ = exploration_rank_ic(prices)
    pd.testing.assert_series_equal(ic, later)


def test_signal_date_alignment_and_exclusion():
    from scripts.momentum_regime_001 import conditional_tables
    dates = pd.to_datetime(['2016-12-20', '2016-12-21', '2016-12-22', '2016-12-23'])
    ic = pd.Series([.1, -.2, .9, .5], index=dates)
    endpoints = pd.DataFrame({'entry_date': dates, 'exit_date': pd.to_datetime(
        ['2016-12-28', '2016-12-29', '2017-01-03', '2016-12-30'])}, index=dates)
    regime = pd.Series(['Bear', 'Bull', 'Bull'], index=dates[[1, 0, 2]], name='regime')
    audit, summary, yearly = conditional_tables(ic, endpoints, regime)
    assert audit.included.tolist() == [True, True, False, False]
    assert summary.loc['Bull', 'mean'] == .1
    assert summary.loc['Bear', 'mean'] == -.2
    assert summary['icir'].isna().all()
    assert yearly.loc[2016, ['Bull', 'Bear']].tolist() == [1, 1]
