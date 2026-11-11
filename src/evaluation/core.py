"""Inputs are wide panels: unique sorted naive dates x unique asset labels.

Factors at row t must be known at the stated signal time. Evaluation never shifts
signals implicitly. Pairwise finite observations are used after label alignment;
NaNs are never filled. Forward labels are descriptive outcomes, not executable
portfolio returns. Overlapping horizons create serial dependence.
"""
from numbers import Integral
from collections.abc import Mapping
import numpy as np
import pandas as pd
from src.data.validation import validate_panel


def _integer(value, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')


def _method(method):
    if method not in ('pearson', 'spearman'):
        raise ValueError('method must be pearson or spearman')


def _aligned(factor, labels):
    validate_panel(factor)
    validate_panel(labels)
    if factor.index.intersection(labels.index).empty or factor.columns.intersection(labels.columns).empty:
        raise ValueError('Panels have no shared dates or assets')
    return factor, labels.reindex(index=factor.index, columns=factor.columns)


def forward_returns(prices, horizon=1, *, entry_lag=1):
    """Label at t = P[t+entry_lag+horizon] / P[t+entry_lag] - 1.

    Index/columns are preserved. Horizons count observed rows, not calendar days.
    The default lag of one row places entry after a close-time signal; lag=0 is
    an explicit same-close descriptive convention, not a claim of execution.
    Missing endpoints/tails yield NaN; intermediate missing prices do not affect
    endpoint returns. No fill, calendar inference, or implicit signal shift.
    """
    validate_panel(prices, positive=True)
    _integer(horizon, 'horizon')
    _integer(entry_lag, 'entry_lag', 0)
    return prices.shift(-(entry_lag + horizon)).div(prices.shift(-entry_lag)) - 1


def cross_sectional_ic(factor, labels, *, method='pearson', min_assets=3):
    """Per-factor-date correlation across assets with labels at the same signal t.

    Align by date/asset names to the factor panel; unmatched labels become NaN.
    Pairwise NaNs are excluded. Too few pairs or either constant cross section
    gives NaN. Spearman uses average ranks of the paired sample (ties retained).
    Caller is responsible for constructing labels with appropriate entry timing.
    """
    _method(method)
    _integer(min_assets, 'min_assets', 2)
    factor, labels = _aligned(factor, labels)
    result = []
    for date in factor.index:
        pairs = pd.concat([factor.loc[date], labels.loc[date]], axis=1).dropna()
        if len(pairs) < min_assets or (pairs.nunique() < 2).any():
            result.append(np.nan)
            continue
        if method == 'spearman':
            pairs = pairs.rank(method='average')
        result.append(pairs.iloc[:, 0].corr(pairs.iloc[:, 1]))
    return pd.Series(result, index=factor.index, name='rank_ic' if method == 'spearman' else 'ic')


def pearson_ic(factor, labels, *, min_assets=3):
    """Pearson IC; see cross_sectional_ic for alignment, missingness and timing."""
    return cross_sectional_ic(factor, labels, min_assets=min_assets)


def rank_ic(factor, labels, *, min_assets=3):
    """Spearman IC; see cross_sectional_ic for alignment, missingness and timing."""
    return cross_sectional_ic(factor, labels, method='spearman', min_assets=min_assets)


def ic_summary(ic):
    """Summarize a dated IC Series after excluding NaN, without changing timing.

    ICIR is mean / sample standard deviation (ddof=1), unannualized. Undefined
    for fewer than two values or zero variance. No iid t-statistic or annualized
    inference is reported because forward labels can overlap.
    """
    if not isinstance(ic, pd.Series):
        raise TypeError('ic must be a Series')
    validate_panel(ic.to_frame('ic'))
    valid = ic.dropna()
    if (valid.abs() > 1 + 1e-12).any():
        raise ValueError('IC must lie in [-1, 1]')
    mean, std = valid.mean(), valid.std(ddof=1)
    # Repeated decimal values can have a tiny positive floating-point std.
    if len(valid) >= 2 and valid.nunique() == 1:
        std = 0.0
    return pd.Series(dict(count=len(valid), mean=mean, std=std,
                          icir=mean / std if pd.notna(std) and std > 0 else np.nan,
                          positive_fraction=(valid > 0).mean() if len(valid) else np.nan))


def quantile_groups(factor, quantiles=5):
    """Group each date's observed factors into 1 (low) through Q (high).

    Only same-date factor values determine membership; no labels are consulted.
    NaNs remain unassigned. Average ranks keep ties together. Their percentile
    midpoints define equal-width bins; tied/small sections can leave empty bins.
    Dates with fewer than Q observations or a constant factor are unassigned.
    """
    validate_panel(factor)
    _integer(quantiles, 'quantiles', 2)
    groups = np.floor((factor.rank(axis=1, method='average') - 0.5).div(
        factor.count(axis=1), axis=0) * quantiles) + 1
    groups.loc[(factor.count(axis=1) < quantiles) | (factor.nunique(axis=1) < 2)] = np.nan
    return groups


def quantile_returns(factor, labels, quantiles=5):
    """Return (by_date, summary) tables of descriptive mean forward labels.

    by_date has (date, quantile) index and mean_return, count, members columns.
    summary equally averages available date means, with dates and observations.
    Membership uses same-date factors before excluding missing aligned labels.
    All date/bin combinations are retained; empty bins have NaN means and zero
    counts. Overlapping labels must not be compounded into portfolio performance.
    """
    factor, labels = _aligned(factor, labels)
    groups = quantile_groups(factor, quantiles)
    rows = []
    for date in factor.index:
        for q in range(1, quantiles + 1):
            mask = groups.loc[date].eq(q)
            values = labels.loc[date, mask].dropna()
            rows.append((date, q, values.mean(), len(values), int(mask.sum())))
    by_date = pd.DataFrame(rows, columns=['date', 'quantile', 'mean_return', 'count', 'members']).set_index(['date', 'quantile'])
    summary = by_date.groupby(level='quantile').agg(
        mean_return=('mean_return', 'mean'), dates=('mean_return', 'count'),
        observations=('count', 'sum'))
    return by_date, summary


def factor_correlations(factors, *, method='spearman', min_assets=3):
    """Return (daily, mean) factor correlation tables, using same-date signals.

    factors maps names to panels. Dates are the sorted union; assets and NaNs
    are handled pairwise. daily index is (date, factor); columns are other factor
    names. mean equally weights valid dates for each pair. Zero variance or too
    few common assets gives NaN (including diagonal). No time shift is applied.
    """
    _method(method)
    _integer(min_assets, 'min_assets', 2)
    if not isinstance(factors, Mapping) or not factors:
        raise ValueError('Provide a nonempty mapping of factor panels')
    dates = pd.DatetimeIndex([])
    for panel in factors.values():
        validate_panel(panel)
        dates = dates.union(panel.index)
    names = list(factors)
    daily = pd.DataFrame(index=pd.MultiIndex.from_product([dates, names], names=['date', 'factor']),
                         columns=names, dtype=float)
    for a, left in factors.items():
        for b, right in factors.items():
            if left.columns.intersection(right.columns).empty or left.index.intersection(right.index).empty:
                continue
            values = cross_sectional_ic(left, right, method=method, min_assets=min_assets).reindex(dates)
            daily.loc[(slice(None), a), b] = values.to_numpy()
    return daily, daily.groupby(level='factor', sort=False).mean().reindex(names)
