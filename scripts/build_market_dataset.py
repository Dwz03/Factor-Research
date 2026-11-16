"""Reproducible data preparation only; no factor computation or evaluation.

Run from repository root: python -B scripts/build_market_dataset.py [--download]
The frozen candidate snapshot is required. Without --download only builds universe.
Failed batches are recorded, never automatically retried. Rate limiting stops run.
"""
import argparse
from hashlib import sha256
import json
import logging
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import download_prices
from src.data.validation import validate_panel
from src.data.loader import _close

DATE = '2026-11-12'
SOURCE = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv'
SNAPSHOT = ROOT / 'data/universe' / DATE / 'constituents.csv'
OUT = ROOT / 'data/market' / DATE
SEED = 'factor-research-universe-v1'
SYMBOL_NOTES = [
    dict(ticker='FDXF', standalone_trading_date='2026-06-01',
         explanation='FedEx Freight spin-off began trading after requested end; do not substitute parent FDX.',
         source='https://newsroom.fedexfreight.com/fedex-freight-completes-spin-off-and-begins-trading-on-the-new-york-stock-exchange'),
    dict(ticker='HONA', standalone_trading_date='2026-06-29',
         explanation='Honeywell Aerospace spin-off began trading after requested end; do not substitute parent HON.',
         source='https://www.honeywell.com/us/en/news/press-releases/2026/06/honeywell-technologies-launches-independent-pure-play-automation-company-following-honeywell-aerospace-spin-off'),
]


def select_universe(candidates, size=300):
    """Largest-remainder sector quotas, fixed SHA-256 ranking within sectors."""
    f = candidates.rename(columns={'Symbol': 'source_ticker', 'Security': 'company_name',
                                    'GICS Sector': 'sector'}).copy()
    if f['source_ticker'].duplicated().any() or f[['source_ticker', 'sector', 'company_name']].isna().any().any():
        raise ValueError('Invalid candidates')
    if not 11 <= size <= len(f) or f.sector.nunique() != 11:
        raise ValueError('Expected 11 sectors and a feasible universe size')
    counts = f.groupby('sector').size().sort_index()
    exact = counts * size / len(f)
    quota = np.floor(exact).astype(int)
    order = (exact - quota).sort_values(ascending=False, kind='stable').index
    quota.loc[order[:size - quota.sum()]] += 1
    f['selection_rank_hash'] = f.source_ticker.map(lambda t: sha256(f'{SEED}|{t}'.encode()).hexdigest())
    chosen = pd.concat([g.sort_values(['selection_rank_hash', 'source_ticker']).head(quota[s])
                        for s, g in f.groupby('sector')])
    chosen['ticker'] = chosen.source_ticker.str.replace('.', '-', regex=False)
    chosen['selection_source'] = SOURCE
    chosen['construction_date'] = DATE
    chosen['survivorship_selection_bias'] = True
    columns = ['ticker', 'source_ticker', 'company_name', 'sector', 'selection_source',
               'construction_date', 'survivorship_selection_bias', 'selection_rank_hash']
    return chosen[columns].sort_values('ticker').reset_index(drop=True)


def coverage(prices, universe, statuses):
    """Coverage denominator is the union of observed dates, not an exchange calendar."""
    rows = []
    for ticker in universe.ticker:
        series = prices[ticker]
        first, last = series.first_valid_index(), series.last_valid_index()
        valid = series.notna().sum()
        internal = int(series.loc[first:last].isna().sum()) if valid else 0
        rows.append(dict(ticker=ticker, status=statuses[ticker], first_date=first,
                         last_date=last, observed=int(valid), missing=int(series.isna().sum()),
                         coverage_ratio=valid / len(series) if len(series) else np.nan,
                         internal_missing=internal))
    stock = universe.merge(pd.DataFrame(rows), on='ticker', validate='one_to_one')
    daily = prices.notna().sum(axis=1).rename('eligible_stocks').to_frame()
    daily.index.name = 'Date'
    daily['requested_stocks'] = len(universe)
    return stock, daily


class RateLimitLog(logging.Handler):
    def __init__(self):
        super().__init__()
        self.rate_limited = False

    def emit(self, record):
        message = record.getMessage().lower()
        if any(s in message for s in ('429', 'rate limit', 'too many requests')):
            self.rate_limited = True


def write_report(prices, universe, statuses, batches):
    stock, daily = coverage(prices, universe, statuses)
    stock.to_csv(OUT / 'stock_coverage.csv', index=False)
    daily.to_csv(OUT / 'daily_coverage.csv')
    sectors = stock.assign(success=stock.observed.gt(0)).groupby('sector').agg(
        requested=('ticker', 'size'), downloaded=('success', 'sum'))
    sectors.to_csv(OUT / 'sector_coverage.csv')
    failed = stock[stock.observed.eq(0)]
    failed.to_csv(OUT / 'unavailable_symbols.csv', index=False)
    stock[stock.missing.gt(0)].to_csv(OUT / 'partial_symbols.csv', index=False)
    pd.DataFrame(SYMBOL_NOTES).to_csv(OUT / 'symbol_notes.csv', index=False)
    (OUT / 'batches.json').write_text(json.dumps(batches, indent=2), encoding='utf-8')
    summary = dict(requested=len(universe), downloaded=int(stock.observed.gt(0).sum()),
                   rows=len(prices), columns=len(prices.columns),
                   first_date=str(prices.index.min()), last_date=str(prices.index.max()),
                   partial=int((stock.observed.gt(0) & stock.missing.gt(0)).sum()),
                   internal_missing=int(stock.internal_missing.sum()),
                   eligible_min=int(daily.eligible_stocks.min()) if len(daily) else 0,
                   eligible_max=int(daily.eligible_stocks.max()) if len(daily) else 0,
                   matrix_sha256=sha256((OUT / 'prices.csv').read_bytes()).hexdigest())
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    lines = ['# Market data coverage', '', f'Universe constructed: {DATE} (Asia/Shanghai).', '',
             '## Universe and methodology', '',
             '503 current constituent securities; 300 selected using proportional sector quotas ',
             '(largest remainder, alphabetical sector tie break), then the lowest SHA-256 hashes ',
             f'of `{SEED}|source_ticker` within each sector. No price/history filter or substitutions.',
             'Share classes are separate securities, not necessarily 300 distinct issuers.', '',
             f'Source: [Wikipedia-derived public CSV mirror]({SOURCE}). Direct Wikipedia access returned 403.',
             'Snapshot and checksum: `data/universe/2026-11-12/`; selection metadata: `config/universe.json`.',
             'Recent membership spot-check: [Okta replaces Kenvue, effective November 4](https://press.spglobal.com/2026-10-30-Okta-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600).',
             '**Survivorship and selection bias:** this is current membership sampled after the historical period.',
             'It does not represent historical S&P 500 membership; sector labels are current, too.', '',
             '## Download and coverage', '',
             'Yahoo daily Close, auto_adjust=True; 2010-01-01 inclusive through 2026-01-01 exclusive.',
             'Existing loader and environment proxy retained. Initial batch 10; subsequent batches up to 25,',
             '20 seconds apart, no application retries; stop on rate-limit indications.',
             'Independent validated caches under root data/raw and data/processed. No forward filling.', '',
             f'Requested: {summary["requested"]}; with observations: {summary["downloaded"]}; ',
             f'matrix: {len(prices)} dates × {len(universe)} tickers.',
             f'Observed range: {summary["first_date"]} through {summary["last_date"]}.',
             f'Partial histories: {summary["partial"]}; internal missing cells: {summary["internal_missing"]}.',
             f'Daily eligible count range: {summary["eligible_min"]}–{summary["eligible_max"]}.', '',
             'Eligibility here means a positive finite observed price on that date only; it does not imply',
             'a sufficient factor lookback, future label, liquidity, or historical index membership.',
             'Coverage ratios use the union of observed dates. No independent exchange calendar is used,',
             'so an all-universe missing session cannot be detected. Missing values remain NaN.', '',
             '| Sector | Requested | Downloaded |', '|---|---:|---:|']
    lines += [f'| {s} | {r.requested} | {r.downloaded} |' for s, r in sectors.iterrows()]
    lines += ['', '## Per-stock coverage', '',
              '| Ticker | First date | Last date | Missing | Coverage | Internal gaps | Status |',
              '|---|---|---|---:|---:|---:|---|']
    for r in stock.itertuples():
        first = str(r.first_date)[:10] if pd.notna(r.first_date) else 'unavailable'
        last = str(r.last_date)[:10] if pd.notna(r.last_date) else 'unavailable'
        lines.append(f'| {r.ticker} | {first} | {last} | {r.missing} | {r.coverage_ratio:.2%} | {r.internal_missing} | {r.status} |')
    lines += ['', '## Failures and ticker changes', '',
              'Unavailable symbols: ' + (', '.join(failed.ticker) or 'none') + '.',
              'Batch rejections do not prove every member failed at the vendor; such symbols are explicitly',
              'marked batch_rejected and not substituted. Unattempted symbols remain in the matrix as NaN.',
              'Dot share-class symbols are mapped to Yahoo hyphens; source symbols are retained.',
              'Other ticker changes and predecessor histories are not inferred or stitched automatically.', '',
              '## Structured outputs', '',
              'Under `data/market/2026-11-12/`: `prices.csv`, `stock_coverage.csv`, `daily_coverage.csv`',
              '(one eligible-count row per observed trading date), `sector_coverage.csv`,',
              '`partial_symbols.csv`, `unavailable_symbols.csv`, `batches.json`, and `summary.json`.', '',
              '## Limitations', '',
              'IPOs, spin-offs, ticker changes and vendor gaps can explain short histories; first observation',
              'is not verified IPO date. Missingness causes are not independently adjudicated. Delisted and',
              'former constituents are absent from this current-universe design. Corporate-action adjustment',
              'and historical prices can be revised; these are retrieval-time snapshots, not point-in-time data.',
              'Adjusted Close does not establish executable returns. No factor, IC or portfolio analysis ran.']
    if any(b.get('diagnostic') for b in batches):
        lines += ['', '## Rejected-batch diagnostics', '',
                  'A single diagnostic request per rejected batch preserved the complete response separately.',
                  'Valid individual columns were retained after the same strict panel validation; failed symbols',
                  'remain NaN. Diagnostic raw/processed CSVs and request/checksum manifests are stored under',
                  '`data/market/2026-11-12/diagnostics/`, separate from loader-managed caches.',
                  'No diagnostic request was allowed after a recorded rate-limit stop. No identity rotation.',
                  'no_observations means no valid history was returned, not a verified delisting or IPO cause.']
    lines += ['', '## Verified post-period spin-offs', '']
    for note in SYMBOL_NOTES:
        if note['ticker'] in set(failed.ticker):
            lines.append(f'- {note["ticker"]}: standalone trading began {note["standalone_trading_date"]}. '
                         f'{note["explanation"]} [Company announcement]({note["source"]}).')
    lines += ['', 'These verified dates explain the two wholly unavailable histories; neither symbol was removed.',
              'Other missing-history causes remain unverified. Structured notes: `symbol_notes.csv`.']
    (ROOT / 'reports/data_coverage.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(summary), flush=True)


def recover_rejected():
    """One explicit diagnostic pass; keep responses separate from validated caches."""
    import yfinance as yf
    from dotenv import load_dotenv
    import os
    batches = json.loads((OUT / 'batches.json').read_text())
    if any(b.get('rate_limit_stop') or b.get('diagnostic') for b in batches):
        raise ValueError('Rate limit recorded or diagnostics already attempted; refusing retry')
    universe = pd.read_csv(ROOT / 'config/universe.csv')
    prices = pd.read_csv(OUT / 'prices.csv', index_col=0, parse_dates=True)
    stock = pd.read_csv(OUT / 'stock_coverage.csv')
    statuses = dict(zip(stock.ticker, stock.status))
    load_dotenv(ROOT / '.env', override=False)
    proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
    if proxy:
        yf.config.network.proxy = proxy
    guard = RateLimitLog()
    logging.getLogger('yfinance').addHandler(guard)
    for b in batches:
        if b['status'] != 'rejected':
            continue
        time.sleep(20)
        print(f'Diagnostic batch {b["batch"]}: {len(b["tickers"])} symbols', flush=True)
        path = OUT / 'diagnostics' / f'batch_{b["batch"]}'
        path.mkdir(parents=True, exist_ok=False)
        b['diagnostic'] = True
        response = yf.download(b['tickers'], start='2010-01-01', end='2026-01-01',
                               auto_adjust=True, interval='1d', progress=False, timeout=30,
                               threads=False)
        response.to_csv(path / 'raw.csv')
        if guard.rate_limited:
            b['rate_limit_stop'] = True
            break
        good, failures = [], {}
        for ticker in b['tickers']:
            try:
                # Extract one ticker without inventing or filling observations.
                if isinstance(response.columns, pd.MultiIndex):
                    levels = [i for i in range(response.columns.nlevels)
                              if ticker in response.columns.get_level_values(i)]
                    one = response.xs(ticker, axis=1, level=levels[0])
                else:
                    raise ValueError('Unexpected vendor schema')
                close = _close(one, [ticker])
                if close.isna().all().all():
                    statuses[ticker] = 'no_observations'
                    failures[ticker] = 'no_observations_in_requested_period'
                    continue
                validate_panel(close, positive=True, require_observations=True)
                if (close.index < pd.Timestamp('2010-01-01')).any() or (close.index >= pd.Timestamp('2026-01-01')).any():
                    raise ValueError('Out-of-range dates')
                good.append(close)
                statuses[ticker] = 'downloaded_diagnostic'
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                failures[ticker] = type(exc).__name__
                statuses[ticker] = 'invalid_response'
        if good:
            recovered = pd.concat(good, axis=1).sort_index()
            validate_panel(recovered, positive=True, require_observations=True)
            recovered.to_csv(path / 'processed.csv')
            prices = prices.reindex(prices.index.union(recovered.index).sort_values())
            prices.loc[recovered.index, recovered.columns] = recovered
        b['diagnostic_failures'] = failures
        b['recovered_symbols'] = [c for p in good for c in p.columns]
        metadata = dict(source='yahoo', tickers=b['tickers'], start='2010-01-01', end='2026-01-01',
                        interval='1d', auto_adjust=True, retrieved_at=pd.Timestamp.now(tz='UTC').isoformat(),
                        failures=failures, recovered=b['recovered_symbols'],
                        checksums={p.name: sha256(p.read_bytes()).hexdigest() for p in path.glob('*.csv')})
        (path / 'manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        print(f'Recovered {len(good)}; unavailable {failures}', flush=True)
    validate_panel(prices, positive=True)
    prices.index.name = 'Date'
    prices.to_csv(OUT / 'prices.csv')
    write_report(prices, universe, statuses, batches)


def main(download=False):
    candidates = pd.read_csv(SNAPSHOT)
    universe = select_universe(candidates)
    universe_path = ROOT / 'config/universe.csv'
    if universe_path.exists() and universe_path.read_text() != universe.to_csv(index=False):
        raise ValueError('Existing universe differs; refusing overwrite')
    universe.to_csv(universe_path, index=False)
    metadata = dict(construction_date=DATE, source=SOURCE, candidates=len(candidates),
                    snapshot_sha256=sha256(SNAPSHOT.read_bytes()).hexdigest(), seed=SEED,
                    rule='sector proportional largest remainder; SHA256(seed|source_ticker) ascending',
                    survivorship_selection_bias=True, historical_membership=False)
    (ROOT / 'config/universe.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(universe.groupby('sector').size().to_string(), flush=True)
    if not download:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'prices.csv').exists():
        raise ValueError('Run outputs already exist; inspect before any rerun')
    symbols = universe.ticker.tolist()
    groups = [symbols[:10]] + [symbols[i:i+25] for i in range(10, len(symbols), 25)]
    panels, batches = [], []
    statuses = dict.fromkeys(symbols, 'not_attempted')
    handler = RateLimitLog()
    logging.getLogger('yfinance').addHandler(handler)
    for i, tickers in enumerate(groups):
        if i:
            time.sleep(20)
        print(f'Batch {i+1}/{len(groups)}: {len(tickers)} symbols', flush=True)
        try:
            panel = download_prices(tickers, '2010-01-01', '2026-01-01', auto_adjust=True)
            panels.append(panel)
            statuses.update(dict.fromkeys(tickers, 'downloaded'))
            batches.append(dict(batch=i+1, tickers=tickers, status='validated', rows=len(panel)))
        except Exception as exc:
            statuses.update(dict.fromkeys(tickers, 'batch_rejected'))
            batches.append(dict(batch=i+1, tickers=tickers, status='rejected', error_type=type(exc).__name__))
            print(f'Batch rejected: {type(exc).__name__}; no automatic retry', flush=True)
            if i == 0:
                break
        if handler.rate_limited:
            batches[-1]['rate_limit_stop'] = True
            break
    prices = (pd.concat(panels, axis=1).sort_index() if panels else
              pd.DataFrame(index=pd.DatetimeIndex([]))).reindex(columns=symbols)
    prices.index.name = 'Date'
    if len(prices):
        validate_panel(prices, positive=True)
        assert prices.index.min() >= pd.Timestamp('2010-01-01')
        assert prices.index.max() < pd.Timestamp('2026-01-01')
    prices.to_csv(OUT / 'prices.csv')
    write_report(prices, universe, statuses, batches)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--recover-rejected', action='store_true')
    args = parser.parse_args()
    if args.recover_rejected:
        recover_rejected()
    else:
        main(args.download)
