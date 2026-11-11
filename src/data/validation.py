"""Validation for date-by-asset research panels."""
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_complex_dtype


def validate_panel(frame, *, positive=False, require_observations=False):
    """Require nonempty numeric panels with unique sorted timezone-naive dates.

    Missing values are allowed, infinities are not. No calendar completeness or
    point-in-time availability is inferred. Optional price validation requires
    positive observed values and at least one observation per asset.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("Expected DataFrame")
    if frame.empty or not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError("Expected nonempty panel with DatetimeIndex")
    if frame.index.tz is not None or frame.index.hasnans:
        raise ValueError("Dates must be timezone-naive and nonmissing")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("Dates must be unique and sorted")
    if frame.columns.has_duplicates or frame.columns.hasnans:
        raise ValueError("Asset labels must be unique and nonmissing")
    if not all(is_numeric_dtype(dtype) and not is_complex_dtype(dtype) for dtype in frame.dtypes):
        raise ValueError("Values must be real numeric values")
    values = frame.to_numpy(dtype=float, na_value=np.nan)
    if np.isinf(values).any() or (positive and (values <= 0).any()):
        raise ValueError("Invalid observed values")
    if require_observations and frame.isna().all().any():
        raise ValueError("Every asset must have observations")
