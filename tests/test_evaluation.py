import numpy as np
import pandas as pd
import pytest
from src.evaluation import (forward_returns, pearson_ic, rank_ic, ic_summary,
                            quantile_groups, quantile_returns, factor_correlations)


def panel(values=None):
    return pd.DataFrame(values if values is not None else [[1., 2., 3., 4.]] * 5,
                        index=pd.date_range('2020-01-01', periods=5), columns=list('ABCD'))


def test_forward_timing_and_missing():
    prices = panel([[10., 20., 30., 40.], [20., 40., 60., 80.],
                    [60., np.nan, 180., 240.], [120., 240., 360., 480.],
                    [240., 480., 720., 960.]])
    result = forward_returns(prices)
    assert result.iloc[0, 0] == 2
    assert pd.isna(result.iloc[0, 1])
    assert result.iloc[-2:].isna().all().all()
    assert forward_returns(prices, entry_lag=0).iloc[0, 0] == 1
    # Endpoint returns do not fill or depend on intervening missing prices.
    assert forward_returns(prices, horizon=2).iloc[0, 1] == 5


def test_ic_alignment_and_rank():
    f = panel()
    labels = panel([[1., 4., 9., 16.]] * 5)
    result = pearson_ic(f, labels[list('DCBA')])
    assert result.iloc[0] == pytest.approx(np.corrcoef([1, 2, 3, 4], [1, 4, 9, 16])[0, 1])
    assert rank_ic(f, labels).iloc[0] == pytest.approx(1)
    labels = labels.iloc[1:].drop(columns='A')
    result = pearson_ic(f, labels)
    assert pd.isna(result.iloc[0])
    assert result.iloc[1:].notna().all()


def test_missing_constant_and_ties():
    f = panel()
    f.iloc[0] = 1
    f.iloc[1, :2] = np.nan
    f.iloc[2] = [1, 1, 3, 4]
    result = rank_ic(f, panel())
    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(np.corrcoef([1.5, 1.5, 3, 4], [1, 2, 3, 4])[0, 1])
    assert pearson_ic(panel(), panel() * 0).isna().all()


def test_ic_summary():
    s = pd.Series([.1, .3, np.nan], index=pd.date_range('2020', periods=3))
    summary = ic_summary(s)
    assert summary['count'] == 2
    assert summary['icir'] == pytest.approx(.2 / np.std([.1, .3], ddof=1))
    assert np.isnan(ic_summary(s * 0)['icir'])
    assert np.isnan(ic_summary(s * np.nan)['mean'])


def test_constant_decimal_ic_has_undefined_icir():
    s = pd.Series([.1] * 3, index=pd.date_range('2020', periods=3))
    summary = ic_summary(s)
    assert summary['std'] == 0
    assert np.isnan(summary['icir'])


def test_complex_panels_rejected():
    p = panel().astype(complex) + 1j
    with pytest.raises(ValueError, match='real numeric'):
        forward_returns(p)
    with pytest.raises(ValueError, match='real numeric'):
        pearson_ic(p, panel())


def test_correlations_align_different_date_and_asset_sets():
    left = panel()
    right = -panel().iloc[2:][['D', 'C', 'B']]
    daily, mean = factor_correlations({'a': left, 'b': right})
    assert daily.loc[(left.index[0], 'a'), 'b'] != daily.loc[(left.index[0], 'a'), 'b']
    assert mean.loc['a', 'b'] == pytest.approx(-1)
    assert mean.loc['b', 'a'] == pytest.approx(-1)


def test_quantiles_and_missing_labels():
    f = panel()
    labels = panel()
    labels.iloc[0, 0] = np.nan
    groups = quantile_groups(f, 2)
    assert groups.iloc[0].tolist() == [1, 1, 2, 2]
    daily, summary = quantile_returns(f, labels, 2)
    assert daily.iloc[0].to_dict() == dict(mean_return=2, count=1, members=2)
    assert summary.loc[2, 'mean_return'] == 3.5
    f.iloc[0] = [1, 1, 1, 4]
    assert quantile_groups(f, 2).iloc[0, :3].nunique() == 1
    assert quantile_groups(f * 0, 2).isna().all().all()


def test_future_data_does_not_change_signals_or_groups():
    from factors.momentum import calculate_momentum
    prices = panel(np.arange(1, 21, dtype=float).reshape(5, 4))
    modified = prices.copy()
    modified.iloc[-1] *= 10
    first = calculate_momentum(prices, 1)
    second = calculate_momentum(modified, 1)
    pd.testing.assert_frame_equal(first.iloc[:-1], second.iloc[:-1])
    pd.testing.assert_frame_equal(quantile_groups(first, 2).iloc[:-1], quantile_groups(second, 2).iloc[:-1])
    pd.testing.assert_frame_equal(forward_returns(prices).iloc[:2], forward_returns(modified).iloc[:2])


def test_factor_correlations():
    daily, mean = factor_correlations({'a': panel(), 'b': -panel()[list('DCBA')]})
    assert mean.loc['a', 'b'] == pytest.approx(-1)
    assert mean.loc['b', 'a'] == pytest.approx(-1)
    assert daily.shape == (10, 2)


@pytest.mark.parametrize('kwargs', [{'horizon': 0}, {'horizon': 1.5}, {'entry_lag': -1}, {'horizon': True}])
def test_invalid_horizons(kwargs):
    with pytest.raises(ValueError):
        forward_returns(panel(), **kwargs)


@pytest.mark.parametrize('kind', ['unsorted', 'duplicate', 'infinite', 'zero', 'index', 'columns', 'empty'])
def test_invalid_panels(kind):
    p = panel()
    if kind == 'unsorted': p = p.iloc[::-1]
    if kind == 'duplicate': p.index = [p.index[0]] * 5
    if kind == 'infinite': p.iloc[0, 0] = np.inf
    if kind == 'zero': p.iloc[0, 0] = 0
    if kind == 'index': p.index = range(5)
    if kind == 'columns': p.columns = ['A'] * 4
    if kind == 'empty': p = p.iloc[:0]
    with pytest.raises(ValueError): forward_returns(p)


def test_invalid_evaluation_options():
    from src.evaluation import cross_sectional_ic
    with pytest.raises(ValueError): cross_sectional_ic(panel(), panel(), method='bad')
    with pytest.raises(ValueError): pearson_ic(panel(), panel(), min_assets=1)
    with pytest.raises(ValueError): quantile_groups(panel(), 1)
    with pytest.raises(ValueError): factor_correlations({})
    with pytest.raises(ValueError): pearson_ic(panel(), panel().rename(columns=lambda c: c + 'X'))
