"""Offline integration check; synthetic inputs, no saved research results."""
import numpy as np
import pandas as pd
import pytest

from src.data import clean_prices
from factors.momentum import calculate_momentum
from src.evaluation import forward_returns, pearson_ic, rank_ic, quantile_returns


def test_synthetic_research_pipeline():
    rng = np.random.default_rng(42)
    prices = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, .01, (60, 10)), axis=0)),
                          index=pd.bdate_range('2020-01-01', periods=60),
                          columns=[f'ASSET_{i}' for i in range(10)])
    dirty = prices.astype(object)
    dirty.iloc[3, 0] = 'bad'
    dirty.iloc[4, 1] = 0
    dirty.iloc[5, 2] = np.inf
    original = dirty.copy(deep=True)
    cleaned = clean_prices(dirty.iloc[::-1])
    pd.testing.assert_frame_equal(dirty, original)
    assert cleaned.isna().sum().sum() == 3

    factor = calculate_momentum(cleaned, window=20)
    labels = forward_returns(cleaned, horizon=5, entry_lag=1)
    assert factor.iloc[:20].isna().all().all()
    assert factor.iloc[20, 0] == pytest.approx(cleaned.iloc[20, 0] / cleaned.iloc[0, 0] - 1)
    assert labels.iloc[20, 0] == pytest.approx(cleaned.iloc[26, 0] / cleaned.iloc[21, 0] - 1)
    assert labels.iloc[-6:].isna().all().all()

    ic, ric = pearson_ic(factor, labels), rank_ic(factor, labels)
    assert ic.notna().sum() == ric.notna().sum() == 34
    assert ic.dropna().abs().le(1).all()
    assert ric.dropna().abs().le(1).all()
    daily, summary = quantile_returns(factor, labels, quantiles=5)
    assert summary.shape == (5, 3)
    assert summary['observations'].sum() == 337
    assert daily.loc[(prices.index[20], 1), 'count'] == 2
    assert daily.loc[(prices.index[20], 1), 'mean_return'] == pytest.approx(
        labels.loc[prices.index[20], factor.iloc[20].nsmallest(2).index].mean())
