"""Pre-specified 5/20/60D sensitivity, 2010–2016 only; entirely offline."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from factors.momentum import calculate_momentum
from src.data.validation import validate_panel
from src.evaluation import forward_returns, rank_ic, ic_summary
from scripts.momentum_regime_001 import markdown_table

WINDOWS = (5, 20, 60)
MIN_ASSETS = 100
OUT = ROOT / 'data/research/momentum_001/window_sensitivity_2010_2016'
PRICE_PATH = ROOT / 'data/market/2026-11-12/prices.csv'
UNIVERSE_PATH = ROOT / 'config/universe.csv'
REPORT = ROOT / 'reports/01_momentum.md'
FIGURE = ROOT / 'reports/figures/momentum_001_window_sensitivity_2010_2016.png'
HEADING = '## Pre-specified Window Sensitivity Analysis (2010–2016 only)'


def analyze(prices):
    """Compute fixed-window ICs and a strict date AND ticker-pair common sample.

    Slice before constructing factors/labels: no post-2016 endpoints and no
    extra pre-2010 equity warm-up, matching Research #001. Momentum uses the
    existing endpoint pct_change definition; intermediate missing prices are
    not filled and do not independently invalidate endpoint momentum/returns.
    The common mask intersects observed factors at ALL three windows and the
    same forward label. Rank IC is recomputed after masking (ranks are not reused
    from larger samples). Dates with <100 pairs or undefined IC for any window
    are excluded from ALL common-series summaries. A zero-variance section is
    undefined, never replaced by zero. No window selection is performed.
    """
    bounded = prices.loc['2010-01-01':'2016-12-31'].copy()
    validate_panel(bounded, positive=True)
    targets = forward_returns(bounded, horizon=5, entry_lag=1)
    dates = bounded.index.to_series()
    endpoints = pd.DataFrame({'entry_date': dates.shift(-1), 'exit_date': dates.shift(-6)})
    in_period = (endpoints.entry_date.ge('2010-01-01') & endpoints.entry_date.le('2016-12-31')
                 & endpoints.exit_date.ge('2010-01-01') & endpoints.exit_date.le('2016-12-31'))
    targets.loc[~in_period] = np.nan
    factors = {w: calculate_momentum(bounded, window=w) for w in WINDOWS}
    masks = {w: factors[w].notna() & targets.notna() for w in WINDOWS}
    available = pd.DataFrame({f'{w}D': rank_ic(factors[w], targets, min_assets=MIN_ASSETS)
                              for w in WINDOWS})
    shared_pairs = targets.notna()
    for w in WINDOWS:
        shared_pairs &= masks[w]
    paired_targets = targets.where(shared_pairs)
    common = pd.DataFrame({f'{w}D': rank_ic(factors[w].where(shared_pairs), paired_targets,
                                          min_assets=MIN_ASSETS) for w in WINDOWS})
    common_dates = common.notna().all(axis=1)
    common.loc[~common_dates] = np.nan
    used_common_pairs = shared_pairs.copy()
    used_common_pairs.loc[~common_dates] = False
    audit = endpoints.copy()
    audit['endpoints_in_period'] = in_period
    for w in WINDOWS:
        audit[f'{w}D_valid_pairs'] = masks[w].sum(axis=1)
        audit[f'{w}D_included'] = available[f'{w}D'].notna()
    audit['common_candidate_pairs'] = shared_pairs.sum(axis=1)
    audit['common_included'] = common_dates
    audit['common_used_pairs'] = used_common_pairs.sum(axis=1)
    summaries, yearly_means, yearly_counts = {}, {}, {}
    for sample, daily in [('available', available), ('common', common)]:
        for column in daily:
            summaries[(sample, column)] = ic_summary(daily[column])
        yearly_means[sample] = daily.groupby(daily.index.year).mean().reindex(range(2010, 2017))
        yearly_counts[sample] = daily.groupby(daily.index.year).count().reindex(range(2010, 2017), fill_value=0)
    summary = pd.DataFrame(summaries).T
    summary.index.names = ['sample', 'window']
    summary['count'] = summary['count'].astype(int)
    return dict(available=available, common=common, summary=summary, audit=audit,
                common_pairs=used_common_pairs,
                yearly_means=pd.concat(yearly_means, names=['sample', 'year']),
                yearly_counts=pd.concat(yearly_counts, names=['sample', 'year']))


def run(append_report=False):
    prior_report = REPORT.read_bytes()
    if append_report and HEADING in prior_report.decode('utf-8'):
        raise ValueError('Sensitivity section already exists; refusing to duplicate or replace it')
    prices = pd.read_csv(PRICE_PATH, index_col=0, parse_dates=True)
    universe = pd.read_csv(UNIVERSE_PATH)
    if not universe.ticker.is_unique or set(prices.columns) != set(universe.ticker):
        raise ValueError('Price columns must match the frozen universe exactly')
    results = analyze(prices.reindex(columns=universe.ticker))
    # Regression check against the existing saved 20D research series, restricted
    # to the exploration period; no other IC results are loaded or computed.
    baseline_path = ROOT / 'data/research/momentum_001/regime_2010_2016/daily_alignment.csv'
    baseline = pd.read_csv(baseline_path, index_col=0, parse_dates=True)['rank_ic'].loc['2010':'2016']
    pd.testing.assert_series_equal(results['available']['20D'], baseline,
                                   check_names=False, check_freq=False)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, table in results.items():
        table.to_csv(OUT / f'{name}.csv')
    audit = results['audit']
    included = audit.loc[audit.common_included]
    metadata = dict(windows=list(WINDOWS), exploration_start='2010-01-01', exploration_end='2016-12-31',
                    prediction_horizon=5, entry_lag=1, min_assets=MIN_ASSETS,
                    primary_metric='Spearman Rank IC', icir='unannualized mean / sample std (ddof=1)',
                    universe_size=len(universe), universe_sha256=sha256(UNIVERSE_PATH.read_bytes()).hexdigest(),
                    equity_matrix_sha256=sha256(PRICE_PATH.read_bytes()).hexdigest(),
                    baseline_20d_daily_series_matches=True,
                    common_dates=len(included), common_first_signal=str(included.index.min()),
                    common_last_signal=str(included.index.max()),
                    common_asset_pairs=int(included.common_used_pairs.sum()),
                    common_assets_min=int(included.common_used_pairs.min()) if len(included) else None,
                    common_assets_max=int(included.common_used_pairs.max()) if len(included) else None,
                    pre_2010_equity_warmup=False, previous_report_sha256=sha256(prior_report).hexdigest())
    (OUT / 'methodology.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout='constrained')
    x = np.arange(3)
    for offset, sample, color in [(-.18, 'available', '#247f74'), (.18, 'common', '#bd6546')]:
        stats = results['summary'].loc[sample]
        axes[0].bar(x + offset, stats['mean'], width=.36, label=sample, color=color)
    axes[0].set_xticks(x, ['5D', '20D', '60D'])
    axes[0].set_title('Mean Rank IC by sample')
    axes[0].legend()
    yearly = results['yearly_means'].loc['common']
    for w, color in zip(WINDOWS, ['#247f74', '#bd6546', '#5965a6']):
        axes[1].plot(yearly.index, yearly[f'{w}D'], marker='o', label=f'{w}D', color=color)
    axes[1].set_title('Yearly means — common dates and pairs')
    axes[1].legend()
    for ax in axes:
        ax.axhline(0, color='black', linewidth=.7)
        ax.set_ylabel('Mean daily Spearman Rank IC')
    fig.suptitle('Momentum #001: fixed windows, 2010–2016 (descriptive only)')
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=160)
    plt.close(fig)
    section = f'''{HEADING}

### Fixed specification and preservation

Exploration only: 2010-01-01 through 2016-12-31. Lookbacks are exactly 5, 20,
and 60 observed trading rows; no values were tuned or selected after inspecting
results. All call the existing `calculate_momentum` function unchanged:
P[t]/P[t-window]-1, with fill_method=None. The frozen 300-security universe from
`config/universe.csv` is retained, including securities without usable histories.
No prior findings or conclusions are replaced. Validation and held-out test
periods are unchanged; no 2017–2025 IC values are computed or used.

Prices are sliced to exploration before factor/label construction. As in the
existing 20D study, no pre-2010 equity warm-up is added. The shared label is
P[t+6]/P[t+1]-1 (5-day horizon, entry_lag=1). Entry and exit dates must both lie
within exploration; the final six rows cannot contribute. No missing price is
filled. Momentum and returns use observed endpoints, not a requirement that every
intermediate row be nonmissing, preserving the existing factor mathematics.

Rank IC uses pairwise observed factor/return values and at least 100 valid assets.
Average ranks handle ties. Zero-variance cross sections yield undefined IC and
are excluded. Statistics equally weight valid signal dates. Standard deviation
uses ddof=1; ICIR is unannualized mean/std; positive fraction counts IC > 0.
The available-sample 20D daily series matches the prior saved series value by value.

### Available-sample and strict common-sample statistics

Available samples independently use each window's valid ticker/return pairs.
For the common comparison, intersect valid labels and all three factors **per
date and ticker**, recompute ranks/IC on those same pairs, then retain only dates
with defined IC for every window. Merely intersecting dates would not suffice.
This produces {metadata['common_dates']} common dates, from
{metadata['common_first_signal'][:10]} through {metadata['common_last_signal'][:10]},
with {metadata['common_assets_min']}–{metadata['common_assets_max']} identical pairs per date
({metadata['common_asset_pairs']} date/ticker pairs in total). Both dates and pairs
are identical across windows, although the shared ticker set can vary over time.

{markdown_table(results['summary'])}

### Yearly Mean Rank IC

{markdown_table(results['yearly_means'])}

Yearly valid signal-date counts (common counts must match across windows):

{markdown_table(results['yearly_counts'])}

### Descriptive visualization

![Fixed-window sensitivity](figures/momentum_001_window_sensitivity_2010_2016.png)

### Limitations and interpretation boundaries

Overlapping 5-day outcomes, overlapping lookbacks, and shared securities create
serial and cross-window dependence. These descriptive summaries and the figure
have no significance tests, confidence intervals, or executable-return claims.
Missing endpoints, IPOs, and longer warm-up requirements change the available
samples. The common sample addresses comparability but conditions on availability
at all three lookbacks and does not remove selection bias. Current constituents
and current sector assignments create survivorship/selection bias; historical
index membership is not reconstructed. Yahoo prices can be revised and adjusted
retrospectively. Comparing three windows and seven yearly slices involves multiple
comparisons, even with a fixed specification. No winning window is selected and
no prior research conclusion is changed. Dependence-aware inference and a separate
validation protocol would be required before stronger claims.

Artifacts: `data/research/momentum_001/window_sensitivity_2010_2016/` contains
`available.csv`, `common.csv` (daily IC), `summary.csv`, `yearly_means.csv`,
`yearly_counts.csv`, `audit.csv` (endpoints, pair counts, date eligibility),
`common_pairs.csv` (exact used Date × Ticker mask), and `methodology.json`
(fixed settings and source hashes). The section is also saved as `section.md`.
Reproduce offline with `python -B scripts/momentum_window_sensitivity_001.py`.
`--append-report` appends once and refuses to overwrite an existing section.
'''
    (OUT / 'section.md').write_text(section, encoding='utf-8')
    if append_report:
        REPORT.write_bytes(prior_report + b'\n\n' + section.encode('utf-8'))
        assert REPORT.read_bytes().startswith(prior_report)
    print(results['summary'].to_string())
    print(json.dumps(metadata, indent=2))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--append-report', action='store_true')
    run(append_report=parser.parse_args().append_report)
