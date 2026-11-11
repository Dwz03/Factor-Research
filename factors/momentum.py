import pandas as pd


def calculate_momentum(prices: pd.DataFrame, window: int = 20) -> pd.DataFrame:

    """
    Calculate price momentum for each stock.

    Parameters
    ----------
    prices : pd.DataFrame
        Adjusted prices, dates as index, stocks as columns.

    window : int
        Lookback window in trading days.

    Returns
    -------
    pd.DataFrame
        Momentum factor values.
    """

    if window < 1:
        raise ValueError("window must be positive")

    momentum = prices.pct_change(
        periods=window,
        fill_method=None
    )

    return momentum