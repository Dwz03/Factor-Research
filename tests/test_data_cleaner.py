import numpy as np
import pandas as pd
import pytest

from src.data import clean_prices


def test_unsorted_dates():

    prices = pd.DataFrame(
        {"AAPL": [110, 100, 105]},
        index=pd.to_datetime([
            "2025-01-03",
            "2025-01-01",
            "2025-01-02"
        ])
    )

    result = clean_prices(prices)

    assert result.index.is_monotonic_increasing
    assert result["AAPL"].iloc[0] == 100
    assert result["AAPL"].iloc[-1] == 110


def test_invalid_prices():

    prices = pd.DataFrame({
        "MSFT": [100, 0, -np.inf, np.inf, -10]
    })

    result = clean_prices(prices)

    assert result["MSFT"].iloc[0] == 100
    assert result["MSFT"].iloc[1:].isna().all()


def test_duplicate_dates():

    prices = pd.DataFrame(
        {"AAPL": [100, 105, 110]},
        index=pd.to_datetime([
            "2025-01-01",
            "2025-01-01",
            "2025-01-02"
        ])
    )

    with pytest.raises(ValueError):
        clean_prices(prices)


def test_original_unchanged():

    prices = pd.DataFrame({
        "AAPL": [100, 0, -10, 120]
    })

    original = prices.copy(deep=True)

    clean_prices(prices)

    pd.testing.assert_frame_equal(prices, original)


def test_missing_and_nonnumeric_are_not_filled():
    prices = pd.DataFrame({'A': ['10', None, 'bad', '20']})
    result = clean_prices(prices)
    assert result['A'].iloc[1:3].isna().all()
    assert result['A'].iloc[-1] == 20


def test_duplicate_assets_rejected():
    with pytest.raises(ValueError):
        clean_prices(pd.DataFrame([[1, 2]], columns=['A', 'A']))


def test_mixed_cleaning_preserves_input_and_positive_values():
    prices = pd.DataFrame({'A': ['12.5', 'bad', None, '0', '-2', 'inf', '15']},
                          index=pd.date_range('2020', periods=7)).iloc[::-1]
    original = prices.copy(deep=True)
    result = clean_prices(prices)
    pd.testing.assert_frame_equal(prices, original)
    assert result.index.is_monotonic_increasing
    assert result.iloc[[0, -1], 0].tolist() == [12.5, 15]
    assert result.iloc[1:-1, 0].isna().all()
