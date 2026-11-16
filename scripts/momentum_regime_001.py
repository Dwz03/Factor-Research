"""Fixed-spec exploratory appendix; never evaluate IC outside 2010–2016."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from factors.momentum import calculate_momentum
from src.data import download_prices
from src.evaluation import forward_returns, rank_ic, ic_summary, market_trend_regime

OUT = ROOT / 'data/research/momentum_001/regime_2010_2016'
PRICE_PATH = ROOT / 'data/market/2026-11-12/prices.csv'
FIGURE = ROOT / 'reports/figures/momentum_001_regime_2010_2016.png'


def exploration_rank_ic(prices):
    """Slice prices before label construction; endpoints cannot cross into 2017.

    Match existing Research #001: momentum(20), forward(5, lag=1), min_assets=100.
    No pre-2010 equity warm-up is added to the existing factor definition/sample.
    """
    bounded = prices.loc['2010-01-01':'2016-12-31']
    factor = calculate_momentum(bounded, window=20)
    targets = forward_returns(bounded, horizon=5, entry_lag=1)
    ic = rank_ic(factor, targets, min_assets=100)
    dates = bounded.index.to_series()
    endpoints = pd.DataFrame({'entry_date': dates.shift(-1), 'exit_date': dates.shift(-6)})
    return ic, endpoints


def conditional_tables(daily_ic, endpoints, regimes):
    """Join strictly by signal date; keep an exclusion audit and valid-date counts."""
    ic = daily_ic.loc['2010-01-01':'2016-12-31']
    audit = ic.rename('rank_ic').to_frame().join(endpoints).join(regimes)
    valid_endpoints = (audit.entry_date.ge('2010-01-01') & audit.entry_date.le('2016-12-31')
                       & audit.exit_date.ge('2010-01-01') & audit.exit_date.le('2016-12-31'))
    audit['included'] = audit.rank_ic.notna() & audit.regime.notna() & valid_endpoints
    used = audit.loc[audit.included]
    rows = {}
    for state in ('Bull', 'Bear'):
        values = used.loc[used.regime.eq(state), 'rank_ic']
        rows[state] = (ic_summary(values) if len(values) else pd.Series(
            dict(count=0, mean=np.nan, std=np.nan, icir=np.nan, positive_fraction=np.nan)))
    summary = pd.DataFrame(rows).T
    summary.index.name = 'regime'
    yearly = pd.crosstab(used.index.year, used.regime).reindex(
        index=range(2010, 2017), columns=['Bull', 'Bear'], fill_value=0)
    yearly.index.name = 'year'
    yearly['total'] = yearly.sum(axis=1)
    yearly['bull_fraction'] = yearly.Bull / yearly.total.replace(0, np.nan)
    return audit, summary, yearly


def markdown_table(frame):
    # Avoid an optional tabulate dependency.
    table = frame.reset_index()
    rows = ['| ' + ' | '.join(map(str, table.columns)) + ' |',
            '| ' + ' | '.join(['---'] * len(table.columns)) + ' |']
    for row in table.itertuples(index=False, name=None):
        rows.append('| ' + ' | '.join(f'{v:.6f}' if isinstance(v, float) else str(v) for v in row) + ' |')
    return '\n'.join(rows)


def run(daily_rank_ic=None):
    prices = pd.read_csv(PRICE_PATH, index_col=0, parse_dates=True)
    computed, endpoints = exploration_rank_ic(prices)
    if daily_rank_ic is not None:
        # Use the existing notebook series, after verifying the bounded reproduction.
        existing = daily_rank_ic.reindex(computed.index)
        pd.testing.assert_series_equal(existing, computed, check_names=False, check_freq=False)
        computed = existing
    spy = download_prices(['SPY'], '2008-01-01', '2017-01-01', auto_adjust=True)['SPY']
    regimes = market_trend_regime(spy, window=200)
    audit, summary, yearly = conditional_tables(computed, endpoints, regimes)
    OUT.mkdir(parents=True, exist_ok=True)
    audit.to_csv(OUT / 'daily_alignment.csv', index_label='signal_date')
    summary.to_csv(OUT / 'conditional_rank_ic.csv')
    yearly.to_csv(OUT / 'yearly_regime_counts.csv')
    pd.DataFrame({'spy_adjusted_close': spy, 'sma_200': spy.rolling(200, min_periods=200).mean(),
                  'regime': regimes}).to_csv(OUT / 'spy_regimes.csv', index_label='Date')
    metadata = dict(exploration_start='2010-01-01', exploration_end='2016-12-31',
                    momentum_window=20, horizon=5, entry_lag=1, min_assets=100,
                    market_proxy='SPY', regime_window=200, spy_request_start='2008-01-01',
                    spy_request_end_exclusive='2017-01-01', auto_adjust=True,
                    equity_matrix_sha256=sha256(PRICE_PATH.read_bytes()).hexdigest(),
                    included=int(audit.included.sum()), excluded=int((~audit.included).sum()),
                    valid_ic_before_regime_filter=int(computed.notna().sum()))
    (OUT / 'methodology.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    colors = ['#247f74', '#bd6546']
    axes[0].bar(summary.index, summary['mean'], color=colors)
    axes[0].axhline(0, color='black', linewidth=.7)
    axes[0].set_ylabel('Mean daily Rank IC')
    axes[0].set_title('Conditional means (no inference)')
    for i, row in enumerate(summary.itertuples()):
        axes[0].text(i, row.mean / 2, f'n={int(row.count)}', ha='center',
                     va='center', color='white')
    axes[1].boxplot([audit.loc[audit.included & audit.regime.eq(s), 'rank_ic']
                     for s in ('Bull', 'Bear')], tick_labels=['Bull', 'Bear'], showfliers=False)
    axes[1].axhline(0, color='black', linewidth=.7)
    axes[1].set_ylabel('Daily Rank IC')
    axes[1].set_title('Distribution (outlier markers omitted)')
    fig.suptitle('Momentum #001 — exploratory SPY regimes, 2010–2016 only')
    fig.tight_layout()
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=160)
    plt.close(fig)
    methodology = f'''## Exploratory appendix: SPY market-trend regimes (2010–2016 only)

This fixed-specification extension does not replace prior research results or conclusions.
Raw 20-day Momentum is unchanged. Target: P[t+6]/P[t+1]-1, with at least 100
paired assets per signal date, matching the existing daily Rank IC series.
Equity inputs are sliced to 2010–2016 before computing labels. Both endpoints
must fall inside this period. No 2017–2025 IC values are computed or used.
The initial equity factor warm-up remains unchanged (20 rows in 2010).

SPY adjusted daily Close is obtained through the existing validated loader for
2008-01-01 through 2017-01-01 exclusive, with raw and processed request caches.
Its trailing 200-row arithmetic moving average includes the signal-date close.
Bull means Close > SMA; Bear means Close <= SMA. Labels are known after that
close, consistent with next-row entry. The first 199 rows and windows containing
missing prices are unlabeled; no filling is used. Pre-2010 SPY data warms up
the SMA before labels are aligned by signal date, never by row position.

Included dates: {metadata['included']}; excluded exploration rows: {metadata['excluded']}.
Standard deviation uses ddof=1. ICIR is mean/std, unannualized. Positive fraction
is the proportion of valid daily IC values strictly greater than zero.
Yearly counts below refer to included IC observations, not all market sessions.

### Conditional Rank IC

{markdown_table(summary)}

### Yearly distribution of included observations

{markdown_table(yearly)}

### Descriptive visualization

![Conditional Rank IC](figures/momentum_001_regime_2010_2016.png)

### Scope and limitations

These are exploratory conditional descriptions, not a new research conclusion,
an executable strategy, or evidence of statistical significance. Five-day labels
overlap; IC observations and market regimes are serially dependent. No iid tests,
confidence intervals, or significance claims are made. Dependence-aware inference
would be necessary before assessing uncertainty. State counts are unequal.
The 200-day rule was specified in advance here; no thresholds or parameters were
tuned. Current-universe survivorship/selection bias remains. Yahoo adjusted prices
are retrieval-time snapshots subject to revisions and corporate-action adjustments,
not a certified point-in-time archive. Computational labeling uses only rows at or
before the signal date; this cannot remove vendor revision bias.

Structured outputs: `data/research/momentum_001/regime_2010_2016/` contains
daily alignment/inclusion flags, conditional statistics, yearly counts, SPY prices,
SMA/regimes, and methodology metadata. Reproduce with
`python -B scripts/momentum_regime_001.py`; in the notebook pass its existing
endpoint-filtered `daily_ic` to `run(daily_rank_ic=daily_ic)` for alignment verification.
'''
    (OUT / 'appendix.md').write_text(methodology, encoding='utf-8')
    return audit, summary, yearly, methodology


if __name__ == '__main__':
    _, summary, yearly, _ = run()
    print(summary.to_string())
    print(yearly.to_string())
