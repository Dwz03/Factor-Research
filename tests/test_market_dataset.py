import numpy as np
import pandas as pd

from scripts.build_market_dataset import select_universe, coverage


def test_universe_is_order_independent_and_sector_stratified():
    candidates = pd.DataFrame([
        {'Symbol': f'S{s:02d}T{n:02d}', 'Security': f'Company {s}-{n}', 'GICS Sector': f'Sector {s:02d}'}
        for s in range(11) for n in range(40)
    ])
    selected = select_universe(candidates)
    shuffled = select_universe(candidates.sample(frac=1, random_state=12))
    pd.testing.assert_frame_equal(selected, shuffled)
    assert len(selected) == 300
    assert selected.ticker.is_unique
    assert selected.sector.nunique() == 11
    assert selected.groupby('sector').size().between(27, 28).all()


def test_coverage_preserves_failed_and_partial_symbols():
    dates = pd.date_range('2020-01-01', periods=4)
    prices = pd.DataFrame({'A': [np.nan, 10, np.nan, 12], 'B': [np.nan]*4}, index=dates)
    universe = pd.DataFrame({'ticker': ['A', 'B'], 'sector': ['s1', 's2']})
    stock, daily = coverage(prices, universe, {'A': 'downloaded', 'B': 'batch_rejected'})
    assert stock.observed.tolist() == [2, 0]
    assert stock.coverage_ratio.tolist() == [.5, 0]
    assert stock.internal_missing.tolist() == [1, 0]
    assert daily.eligible_stocks.tolist() == [0, 1, 0, 1]
    assert pd.isna(stock.loc[1, 'first_date'])


def test_diagnostic_retains_good_columns_and_blocks_second_attempt(tmp_path, monkeypatch):
    import json
    import pytest
    import yfinance as yf
    from scripts import build_market_dataset as build
    monkeypatch.setattr(build, 'ROOT', tmp_path)
    monkeypatch.setattr(build, 'OUT', tmp_path / 'data')
    monkeypatch.setattr(build.time, 'sleep', lambda seconds: None)
    monkeypatch.delenv('HTTPS_PROXY', raising=False)
    monkeypatch.delenv('https_proxy', raising=False)
    for directory in ('config', 'data', 'reports'):
        (tmp_path / directory).mkdir()
    universe = pd.DataFrame({'ticker': ['A', 'B'], 'sector': ['s1', 's2']})
    universe.to_csv(tmp_path / 'config/universe.csv', index=False)
    dates = pd.date_range('2020-01-01', periods=3)
    pd.DataFrame(np.nan, index=dates, columns=['A', 'B']).to_csv(build.OUT / 'prices.csv')
    universe.assign(status='batch_rejected').to_csv(build.OUT / 'stock_coverage.csv', index=False)
    (build.OUT / 'batches.json').write_text(json.dumps([dict(batch=1, tickers=['A', 'B'], status='rejected')]))
    response = pd.DataFrame([[10., np.nan], [11., np.nan], [12., np.nan]], index=dates,
                            columns=pd.MultiIndex.from_product([['Close'], ['A', 'B']]))
    monkeypatch.setattr(yf, 'download', lambda *args, **kwargs: response.copy())
    build.recover_rejected()
    result = pd.read_csv(build.OUT / 'prices.csv', index_col=0)
    assert result.A.tolist() == [10, 11, 12]
    assert result.B.isna().all()
    assert (build.OUT / 'diagnostics/batch_1/raw.csv').exists()
    assert (build.OUT / 'diagnostics/batch_1/manifest.json').exists()
    with pytest.raises(ValueError, match='already attempted'):
        build.recover_rejected()
