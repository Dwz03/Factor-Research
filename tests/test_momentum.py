import pandas as pd
import pytest

from factors.momentum import calculate_momentum


def test_calculate_momentum():

    prices = pd.DataFrame({
        "AAPL": [100, 105, 110, 121],
        "MSFT": [200, 190, 210, 220]
    })

    result = calculate_momentum(prices, window=2)

    assert result["AAPL"].iloc[2] == pytest.approx(0.10)
    assert result["MSFT"].iloc[2] == pytest.approx(0.05)
    assert result["AAPL"].iloc[3] == pytest.approx(121 / 105 - 1)
    
def test_not_enough_data():
    
    prices = pd.DataFrame({
        "AAPL": [100, 105, 110, 121, 130],
        "MSFT": [200, 190, 210, 220, 100]
        })
    
    result = calculate_momentum(prices, window = 5)
    
    assert result.isna().all().all()
    
def test_invalid_window():

    prices = pd.DataFrame({
        "AAPL": [100, 105, 110]
    })

    with pytest.raises(ValueError):
        calculate_momentum(prices, window=0)