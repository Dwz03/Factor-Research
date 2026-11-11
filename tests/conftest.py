"""All tests are offline; explicitly mocked vendor calls are required."""
import pytest


@pytest.fixture(autouse=True)
def block_live_downloads(monkeypatch):
    import yfinance
    def blocked(*args, **kwargs):
        raise AssertionError('Live market-data downloads are forbidden in tests')
    monkeypatch.setattr(yfinance, 'download', blocked)
