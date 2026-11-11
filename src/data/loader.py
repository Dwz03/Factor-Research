"""Daily Yahoo Close ingestion with request-specific, validated CSV caches."""
from hashlib import sha256
import json
import os
from pathlib import Path
import warnings

import pandas as pd
from dotenv import load_dotenv
import yfinance as yf

from .validation import validate_panel

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class CacheError(ValueError):
    """An existing cache cannot safely satisfy the request."""


def _path(value):
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _request(tickers, start, end, auto_adjust, source):
    if isinstance(tickers, str):
        tickers = tickers.replace(',', ' ').split()
    tickers = list(tickers)
    if not tickers or any(not isinstance(t, str) or not t.strip() for t in tickers):
        raise ValueError('Provide nonempty ticker symbols')
    tickers = [t.strip().upper() for t in tickers]
    if len(set(tickers)) != len(tickers):
        raise ValueError('Duplicate tickers')
    if source != 'yahoo' or not isinstance(auto_adjust, bool):
        raise ValueError("source must be 'yahoo'; auto_adjust must be bool")
    dates = [pd.Timestamp(v) if v is not None else pd.NaT for v in (start, end)]
    if any(pd.isna(d) or d.tz is not None or d != d.normalize() for d in dates):
        raise ValueError('Explicit timezone-naive start/end dates required')
    if dates[0] >= dates[1]:
        raise ValueError('start must precede exclusive end')
    return dict(schema=1, tickers=sorted(tickers), start=dates[0].date().isoformat(),
                end=dates[1].date().isoformat(), auto_adjust=auto_adjust,
                source=source, interval='1d', field='Close')


def _validate(prices, request):
    validate_panel(prices, positive=True, require_observations=True)
    if list(prices.columns) != request['tickers']:
        raise ValueError('Ticker universe differs from request')
    if (prices.index < pd.Timestamp(request['start'])).any() or (
        prices.index >= pd.Timestamp(request['end'])
    ).any():
        raise ValueError('Dates outside requested [start, end) range')


def _close(response, tickers):
    if isinstance(response, pd.Series):
        if len(tickers) != 1:
            raise ValueError('Ambiguous single series response')
        return response.to_frame(tickers[0])
    if not isinstance(response, pd.DataFrame) or response.empty:
        raise ValueError('Empty market data response')
    if isinstance(response.columns, pd.MultiIndex):
        levels = [i for i in range(response.columns.nlevels)
                  if 'Close' in response.columns.get_level_values(i)]
        if len(levels) != 1:
            raise ValueError('Cannot identify Close field')
        prices = response.xs('Close', level=levels[0], axis=1)
    elif 'Close' in response.columns and len(tickers) == 1:
        prices = response[['Close']].rename(columns={'Close': tickers[0]})
    else:
        raise ValueError('Missing or ambiguous Close field')
    if set(prices.columns) != set(tickers) or prices.columns.has_duplicates:
        raise ValueError('Missing or duplicate requested tickers')
    return prices.reindex(columns=tickers)


def download_prices(tickers, start, end, cache_path=None, *, auto_adjust=True,
                    source='yahoo', cache_dir='data', refresh=False):
    """Return daily Close, dates by asset, inclusive start/exclusive end.

    Adjusted prices remain the default. NaNs are retained with a warning; invalid
    prices, duplicate/unsorted dates, and all-missing assets are rejected before
    caching. No filling or signal timing shift. Relative paths use PROJECT_ROOT.
    Raw vendor fields and processed Close are separate. Cache metadata includes
    the full request and checksums. Invalid caches raise CacheError; refresh=True
    explicitly replaces them. Legacy cache_path selects a processed CSV path,
    which now requires metadata (old unversioned files are never silently reused).
    Root .env is loaded without overriding environment settings; HTTPS_PROXY
    preserves local Hiddify configuration without embedding credentials.
    """
    request = _request(tickers, start, end, auto_adjust, source)
    key = sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    raw_path = _path(cache_dir) / 'raw' / f'{key}.csv'
    path = _path(cache_path) if cache_path is not None else _path(cache_dir) / 'processed' / f'{key}.csv'
    if path.resolve() == raw_path.resolve():
        raise ValueError('Raw and processed paths must differ')
    meta_path = path.with_suffix(path.suffix + '.json')
    if not refresh and (path.exists() or meta_path.exists()):
        try:
            metadata = json.loads(meta_path.read_text(encoding='utf-8'))
            if metadata['request'] != request:
                raise ValueError('Incompatible request metadata')
            for item, field in ((path, 'processed_sha256'), (raw_path, 'raw_sha256')):
                if sha256(item.read_bytes()).hexdigest() != metadata[field]:
                    raise ValueError('Checksum mismatch')
            prices = pd.read_csv(path, index_col=0, parse_dates=True)
            _validate(prices, request)
            return prices
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CacheError(f'Invalid cache {path}; explicitly refresh or choose a new path') from exc
    load_dotenv(PROJECT_ROOT / '.env', override=False)
    proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
    if proxy:
        yf.config.network.proxy = proxy
    response = yf.download(request['tickers'], start=request['start'], end=request['end'],
                           auto_adjust=auto_adjust, interval='1d', progress=False, timeout=30)
    prices = _close(response, request['tickers'])
    _validate(prices, request)
    if prices.isna().any().any():
        warnings.warn('Missing downloaded observations retained as NaN', UserWarning)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Metadata is the completion marker; incomplete writes fail checksum checks.
    response.to_csv(raw_path)
    prices.to_csv(path)
    metadata = dict(request=request, retrieved_at=pd.Timestamp.now(tz='UTC').isoformat(),
                    yfinance_version=yf.__version__,
                    raw_sha256=sha256(raw_path.read_bytes()).hexdigest(),
                    processed_sha256=sha256(path.read_bytes()).hexdigest())
    meta_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return prices
