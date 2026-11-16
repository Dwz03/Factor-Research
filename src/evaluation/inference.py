"""Dependence-aware inference for the mean of one dated series."""
from numbers import Integral
import numpy as np
import pandas as pd
from scipy.stats import norm
from src.data.validation import validate_panel


def hac_mean(values: pd.Series, lag: int = 5, *, use_correction: bool = True):
    """Newey–West inference for H0: mean=0, equivalent to intercept-only OLS.

    Input must be finite, complete, and ordered on unique naive trading dates.
    No dropping, filling, sorting, or timing shift is implicit. Lags count input
    observations, not calendar days; caller must ensure consecutive trading rows.
    For demeaned u, covariance of the mean is
    [sum(u²) + 2*sum_{j=1..L}(1-j/(L+1))*sum(u[j:]*u[:-j])] / n².
    If use_correction=True, multiply covariance by n/(n-1), the n/(n-k)
    intercept-only OLS correction with k=1. Autocovariances use denominator n,
    not n-j. No automatic bandwidth choice or annualization is performed.

    The t_stat is mean/HAC_SE, evaluated using asymptotic N(0,1); two-sided
    p=2*norm.sf(abs(t_stat)), 95% CI=mean +/- norm.ppf(.975)*SE. These are
    pointwise intervals, not simultaneous intervals. Zero estimated variance
    returns SE=0 and undefined test/interval values (NaN), not certainty.
    """
    if not isinstance(values, pd.Series):
        raise TypeError('values must be a Series')
    validate_panel(values.to_frame('value'))
    if values.isna().any():
        raise ValueError('Missing observations must be handled explicitly before HAC inference')
    n = len(values)
    if n < 2:
        raise ValueError('At least two observations required')
    if isinstance(lag, bool) or not isinstance(lag, Integral) or not 0 <= lag < n:
        raise ValueError('lag must be an integer in [0, n-1]')
    if not isinstance(use_correction, bool):
        raise TypeError('use_correction must be bool')
    y = values.to_numpy(dtype=float)
    mean = y.mean()
    u = y - mean
    meat = float(u @ u)
    for j in range(1, lag + 1):
        meat += 2 * (1 - j / (lag + 1)) * float(u[j:] @ u[:-j])
    if values.nunique() == 1:
        meat = 0.0
    if meat < 0:
        raise ArithmeticError('Numerically negative HAC covariance')
    correction = n / (n - 1) if use_correction else 1.0
    covariance = meat / n**2 * correction
    se = np.sqrt(covariance)
    statistic = mean / se if se > 0 else np.nan
    p = 2 * norm.sf(abs(statistic)) if se > 0 else np.nan
    margin = norm.ppf(.975) * se if se > 0 else np.nan
    return pd.Series(dict(n=n, lag=lag, mean=mean, hac_variance=covariance, hac_se=se,
                          t_stat=statistic, p_value=p, ci_low=mean-margin, ci_high=mean+margin))
