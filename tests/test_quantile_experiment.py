import numpy as np
import pandas as pd
import pytest

from scripts.momentum_quantiles_001 import analyze, summarize_quantiles


def panels(rows=4):
    dates = pd.bdate_range('2010-01-04', periods=rows)
    factor = pd.DataFrame([np.arange(1., 11.)] * rows, index=dates, columns=list('ABCDEFGHIJ'))
    targets = pd.DataFrame([np.arange(10., 0., -1.) / 100] * rows, index=dates, columns=factor.columns)
    return factor, targets


def test_equal_weight_means_and_paired_spread_arithmetic():
    factor, targets = panels()
    result = summarize_quantiles(factor, targets[targets.columns[::-1]])
    np.testing.assert_allclose(result['daily_returns'].iloc[0], [.095, .075, .055, .035, .015])
    assert result['daily_quantiles']['members'].eq(2).all()
    assert result['daily_quantiles']['count'].eq(2).all()
    spread = result['spread_summary'].iloc[0]
    assert spread.mean_spread == pytest.approx(.08)
    assert spread.std_daily_spread == pytest.approx(0)
    assert spread.positive_spread_fraction == 1
    assert spread.valid_dates == 4
    assert result['yearly_spreads'].loc[2010, 'mean_spread'] == pytest.approx(.08)


def test_missing_future_returns_do_not_change_membership_or_reassign_stocks():
    factor, targets = panels()
    before = summarize_quantiles(factor, targets)
    targets.iloc[0, 0] = np.nan
    targets.iloc[1, :2] = np.nan
    targets.iloc[2] *= -1
    after = summarize_quantiles(factor, targets)
    pd.testing.assert_frame_equal(before['group_membership'], after['group_membership'])
    first_q1 = after['daily_quantiles'].loc[(factor.index[0], 1)]
    assert first_q1.members == 2 and first_q1['count'] == 1
    assert first_q1.mean_return == pytest.approx(.09)
    assert np.isnan(after['daily_spread'].iloc[1, 0])
    spread = after['daily_spread'].iloc[:, 0].dropna()
    assert len(spread) == 3
    stats = after['spread_summary'].iloc[0]
    assert stats.mean_spread == pytest.approx(spread.mean())
    assert stats.std_daily_spread == pytest.approx(spread.std(ddof=1))
    assert stats.positive_spread_fraction == pytest.approx(2/3)
    # Q5 has four independent valid dates, but paired means use only three.
    assert after['quantile_summary'].loc['Q5', 'valid_dates'] == 4
    assert after['quantile_summary'].loc['Q5', 'paired_date_mean_return'] == pytest.approx(
        after['daily_returns'].loc[spread.index, 'Q5'].mean())


def test_constant_insufficient_and_tied_cross_sections():
    factor, targets = panels()
    factor.iloc[0] = 1
    factor.iloc[1, :6] = np.nan  # Four observed factors: no groups.
    factor.iloc[2, :6] = 1  # Ties stay together; Q1 is empty.
    factor.iloc[3, 5:] = np.nan  # Five factors: exactly one member per group.
    result = summarize_quantiles(factor, targets)
    assert result['group_membership'].iloc[:2].isna().all().all()
    assert result['group_membership'].iloc[2, :6].nunique() == 1
    assert result['daily_returns'].iloc[2].isna()['Q1']
    assert result['daily_spread'].iloc[:3].isna().all().all()
    assert result['daily_quantiles'].loc[factor.index[3], 'count'].eq(1).all()
    assert result['spread_summary'].iloc[0].valid_dates == 1
    assert np.isnan(result['spread_summary'].iloc[0].std_daily_spread)


def synthetic_prices():
    rng = np.random.default_rng(81)
    return pd.DataFrame(100*np.exp(np.cumsum(rng.normal(0, .02, (100, 10)), axis=0)),
                        index=pd.bdate_range('2016-10-03', periods=100), columns=list('ABCDEFGHIJ'))


def test_period_boundary_and_held_out_values_have_no_effect():
    p = synthetic_prices()
    original = p.copy()
    before = analyze(p)
    pd.testing.assert_frame_equal(p, original)
    assert before['daily_returns'].index.max() < pd.Timestamp('2017-01-01')
    assert before['group_membership'].iloc[:5].isna().all().all()
    assert before['daily_returns'].iloc[-6:].isna().all().all()
    audit = before['audit'].loc[before['audit'].spread_included]
    assert audit.entry_date.ge('2010-01-01').all() and audit.exit_date.le('2016-12-31').all()
    p.loc['2017-01-01':] = np.nan
    after = analyze(p)
    for name in before:
        pd.testing.assert_frame_equal(before[name], after[name])


def test_future_price_change_does_not_change_prior_membership():
    p = synthetic_prices()
    before = analyze(p)
    p.iloc[40] *= np.arange(1, 11)
    after = analyze(p)
    pd.testing.assert_frame_equal(before['group_membership'].iloc[:40], after['group_membership'].iloc[:40])
    assert not before['daily_returns'].iloc[34].equals(after['daily_returns'].iloc[34])
