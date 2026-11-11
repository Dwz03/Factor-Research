import numpy as np
import pandas as pd

def clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Copy and sort rows; coerce nonnumeric, infinite, or nonpositive values to NaN.

    Rows are observations (normally dates), columns are assets. Duplicate labels
    are rejected. Generic indexes remain supported for legacy callers. Missing
    prices are never filled; cleaning does not use future values or shift signals.
    """

    if not isinstance(prices, pd.DataFrame):
        raise TypeError("prices must be a DataFrame")

    if prices.index.has_duplicates or prices.columns.has_duplicates:
        raise ValueError("Duplicate dates or asset labels detected")
    if prices.index.hasnans:
        raise ValueError("Missing index labels")
    cleaned = prices.sort_index().apply(pd.to_numeric, errors="coerce")
    return cleaned.replace([np.inf, -np.inf], np.nan).mask(cleaned <= 0)
