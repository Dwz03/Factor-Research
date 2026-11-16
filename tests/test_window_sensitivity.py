import numpy as np
import pandas as pd
import pytest

from factors.momentum import calculate_momentum
from scripts.momentum_window_sensitivity_001 import analyze, WINDOWS
from src.evaluation import forward_returns


def prices():
    rng = np.random.default_rng(123)
    return pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, .02, (160, 110)), axis=0)),
                        index=pd.bdate_range('2016-07-01', periods=160),
                        columns=[f'A{i}' for i in range(110)])


def test_common_sample_uses_identical_pairs_and_recomputes_ranks():
    p = prices()
    p.iloc[25, :5] = np.nan  # Removes five 60D factors at signal row 85 only.
    original = p.copy(deep=True)
    results = analyze(p)
    bounded = p.loc[:'2016-12-31']
    target = forward_returns(bounded, horizon=5, entry_lag=1)
    factors = {w: calculate_momentum(bounded, window=w) for w in WINDOWS}
    date = p.index[85]
    mask = results['common_pairs'].loc[date]
    assert mask.sum() == 105
    assert not mask.iloc[:5].any()
    assert results['audit'].loc[date, '5D_valid_pairs'] == 110
    for w in WINDOWS:
        # Manual paired Spearman calculation after intersecting the ticker sets.
        expected = factors[w].loc[date, mask].rank().corr(target.loc[date, mask].rank())
        assert results['common'].loc[date, f'{w}D'] == pytest.approx(expected)
    pd.testing.assert_frame_equal(p, original)
    assert results['common'].notna().nunique(axis=1).eq(1).all()
    assert results['yearly_counts'].loc['common'].nunique(axis=1).eq(1).all()
    assert results['summary'].loc['common', 'count'].nunique() == 1
    assert results['common_pairs'].loc[~results['audit'].common_included].sum().sum() == 0


def test_common_minimum_assets_and_zero_variance_remove_entire_date():
    p = prices()
    p.iloc[25, :15] = np.nan  # 95 common pairs at row 85, below fixed minimum 100.
    p.iloc[80] = p.iloc[75]  # Exactly constant zero 5D momentum at row 80.
    results = analyze(p)
    assert results['audit'].loc[p.index[85], 'common_candidate_pairs'] == 95
    assert results['common'].loc[p.index[85]].isna().all()
    assert pd.notna(results['available'].loc[p.index[85], '5D'])
    assert results['common'].loc[p.index[80]].isna().all()
    assert pd.notna(results['available'].loc[p.index[80], '60D'])


def test_period_boundaries_and_no_held_out_influence():
    p = prices()
    before = analyze(p)
    assert before['audit'].index.max() < pd.Timestamp('2017-01-01')
    assert before['available'].iloc[-6:].isna().all().all()
    assert before['common'].iloc[-6:].isna().all().all()
    assert before['common'].iloc[:60].isna().all().all()
    included = before['audit'].loc[before['audit'].common_included]
    assert included.entry_date.ge('2010-01-01').all()
    assert included.exit_date.le('2016-12-31').all()
    p.loc['2017-01-01':] = np.nan
    after = analyze(p)
    for key in before:
        pd.testing.assert_frame_equal(before[key], after[key])
