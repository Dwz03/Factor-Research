import json
import numpy as np
import pandas as pd
import pytest
from src.data import loader


@pytest.fixture
def vendor(monkeypatch, tmp_path):
    from types import SimpleNamespace
    monkeypatch.setattr(loader.yf, 'config', SimpleNamespace(network=SimpleNamespace(proxy=None)))
    frame = pd.DataFrame([[10., 20.], [11., 22.], [12., 24.]],
                         index=pd.date_range('2020-01-01', periods=3),
                         columns=pd.MultiIndex.from_product([['Close'], ['A', 'B']]))
    calls = []
    def download(*args, **kwargs):
        calls.append((args, kwargs))
        return frame.copy()
    monkeypatch.setattr(loader.yf, 'download', download)
    monkeypatch.setattr(loader, 'PROJECT_ROOT', tmp_path)
    return frame, calls


def get(**kwargs):
    return loader.download_prices(['B', 'A'], '2020-01-01', '2020-01-04', **kwargs)


def test_cache_roundtrip_root_and_separation(vendor, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path.parent)
    first = get()
    second = get()
    pd.testing.assert_frame_equal(first, second, check_freq=False, check_names=False)
    assert len(vendor[1]) == 1
    assert len(list((tmp_path / 'data/raw').glob('*.csv'))) == 1
    assert len(list((tmp_path / 'data/processed').glob('*.csv'))) == 1
    meta = json.loads(next((tmp_path / 'data/processed').glob('*.json')).read_text())
    assert meta['request']['tickers'] == ['A', 'B']
    get(auto_adjust=False)
    assert len(vendor[1]) == 2


def test_identity_covers_request():
    base = loader._request(['A'], '2020-01-01', '2020-01-04', True, 'yahoo')
    assert base != loader._request(['B'], '2020-01-01', '2020-01-04', True, 'yahoo')
    assert base != loader._request(['A'], '2020-01-02', '2020-01-04', True, 'yahoo')
    assert base['source'] == 'yahoo'


@pytest.mark.parametrize('kind', ['empty', 'zero', 'negative', 'infinite', 'all_missing', 'duplicate', 'unsorted', 'missing_ticker'])
def test_bad_download_not_cached(vendor, tmp_path, monkeypatch, kind):
    frame = vendor[0].copy()
    if kind == 'empty': frame = frame.iloc[:0]
    if kind == 'zero': frame.iloc[0, 0] = 0
    if kind == 'negative': frame.iloc[0, 0] = -1
    if kind == 'infinite': frame.iloc[0, 0] = np.inf
    if kind == 'all_missing': frame.iloc[:, 0] = np.nan
    if kind == 'duplicate': frame.index = [frame.index[0]] * 3
    if kind == 'unsorted': frame = frame.iloc[::-1]
    if kind == 'missing_ticker': frame = frame.iloc[:, :1]
    monkeypatch.setattr(loader.yf, 'download', lambda *a, **k: frame)
    with pytest.raises(ValueError): get()
    assert not list(tmp_path.rglob('*.csv'))


def test_partial_missing_preserved(vendor):
    vendor[0].iloc[1, 0] = np.nan
    with pytest.warns(UserWarning): result = get()
    assert np.isnan(result.iloc[1, 0])


def test_corrupt_and_incompatible_cache(vendor, tmp_path):
    get(cache_path='custom.csv')
    with pytest.raises(loader.CacheError): get(cache_path='custom.csv', auto_adjust=False)
    (tmp_path / 'custom.csv').write_text('')
    with pytest.raises(loader.CacheError): get(cache_path='custom.csv')
    assert len(vendor[1]) == 1
    get(cache_path='custom.csv', refresh=True)
    assert len(vendor[1]) == 2


def test_unversioned_cache_rejected(vendor, tmp_path):
    (tmp_path / 'legacy.csv').write_text('Date,A\n2020-01-01,10\n')
    with pytest.raises(loader.CacheError): get(cache_path='legacy.csv')
    assert not vendor[1]


def test_single_ticker_and_proxy(vendor, monkeypatch):
    monkeypatch.setenv('HTTPS_PROXY', 'http://proxy.example.invalid:1234')
    monkeypatch.setattr(loader.yf.config.network, 'proxy', None)
    monkeypatch.setattr(loader.yf, 'download', lambda *a, **k: vendor[0].xs('A', level=1, axis=1))
    result = loader.download_prices('A', '2020-01-01', '2020-01-04')
    assert list(result.columns) == ['A']
    assert loader.yf.config.network.proxy == 'http://proxy.example.invalid:1234'


@pytest.mark.parametrize('args', [([], '2020', '2021'), (['A', 'A'], '2020', '2021'),
                                 (['A'], '2021', '2020'), (['A'], None, '2021')])
def test_invalid_request(vendor, args):
    with pytest.raises(ValueError): loader.download_prices(*args)
    assert not vendor[1]


def test_end_date_exclusive(vendor):
    with pytest.raises(ValueError, match='outside'):
        loader.download_prices(['A', 'B'], '2020-01-01', '2020-01-03')


def test_raw_corruption_rejected(vendor, tmp_path):
    get()
    next((tmp_path / 'data/raw').glob('*.csv')).write_text('corrupt')
    with pytest.raises(loader.CacheError): get()
    assert len(vendor[1]) == 1


def test_alternate_multiindex_orientation(vendor, monkeypatch):
    response = vendor[0].swaplevel(axis=1)
    monkeypatch.setattr(loader.yf, 'download', lambda *a, **k: response)
    assert get().iloc[0].tolist() == [10, 20]


def test_root_dotenv_proxy_and_environment_precedence(vendor, tmp_path, monkeypatch):
    monkeypatch.delenv('HTTPS_PROXY', raising=False)
    monkeypatch.delenv('https_proxy', raising=False)
    (tmp_path / '.env').write_text('HTTPS_PROXY=http://dotenv.example.invalid\n')
    get()
    assert loader.yf.config.network.proxy == 'http://dotenv.example.invalid'
    monkeypatch.setenv('HTTPS_PROXY', 'http://environment.example.invalid')
    get(refresh=True)
    assert loader.yf.config.network.proxy == 'http://environment.example.invalid'
