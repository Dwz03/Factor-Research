"""Descriptive market states available at the signal-date close."""
from numbers import Integral
import pandas as pd
from src.data.validation import validate_panel


def market_trend_regime(prices: pd.Series, window: int = 200) -> pd.Series:
    """Bull when price[t] > trailing SMA[t], Bear otherwise (including equality).

    Input is a positive adjusted-price Series with unique, sorted, timezone-naive
    trading dates. The SMA includes t and the preceding window-1 rows, so labels
    are available only after the close at t. No future rows or centered windows
    are used. Supply pre-sample history before slicing labels to a study period.
    A full window of observed prices is required: warm-up or any NaN in the window
    yields a missing label, never Bear by default. No filling or calendar insertion
    is performed; callers must supply the intended trading-session grid.
    """
    if not isinstance(prices, pd.Series):
        raise TypeError('prices must be a Series')
    if isinstance(window, bool) or not isinstance(window, Integral) or window < 1:
        raise ValueError('window must be a positive integer')
    validate_panel(prices.to_frame('price'), positive=True)
    average = prices.rolling(window, min_periods=window).mean()
    labels = pd.Series(pd.NA, index=prices.index, dtype='string', name='regime')
    valid = prices.notna() & average.notna()
    labels.loc[valid & prices.gt(average)] = 'Bull'
    labels.loc[valid & prices.le(average)] = 'Bear'
    return labels
