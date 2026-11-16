"""Final fixed-spec descriptive experiment for Research #001; offline only."""
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
from src.evaluation import forward_returns, quantile_groups, quantile_returns
from scripts.momentum_regime_001 import markdown_table

PRICE_PATH = ROOT / 'data/market/2026-11-12/prices.csv'
UNIVERSE_PATH = ROOT / 'config/universe.csv'
OUT = ROOT / 'data/research/momentum_001/quantiles_2010_2016'
REPORT = ROOT / 'reports/01_momentum.md'
FIGURE = ROOT / 'reports/figures/momentum_001_quantiles_2010_2016.png'
HEADING = '## Final exploratory experiment: Quantile Forward Return Analysis (2010–2016)'


def spread_stats(values):
    """Equally weighted date summaries; no compounding or inference."""
    observed = values.dropna()
    return pd.Series(dict(valid_dates=len(observed), mean_spread=observed.mean(),
                          std_daily_spread=observed.std(ddof=1),
                          positive_spread_fraction=(observed > 0).mean() if len(observed) else np.nan))


def summarize_quantiles(factor, targets):
    """Use framework membership before excluding missing labels, without new cutoffs.

    Group means use equal weights over observed returns in the preassigned group;
    the membership count can exceed the valid-return count. An empty group or
    group with zero valid returns has NaN mean. Q1-Q5 uses only paired dates.
    Summary membership ranges/averages are measured on each group's valid-return
    dates; full daily counts (including excluded dates) are retained separately.
    """
    groups = quantile_groups(factor, quantiles=5)
    daily, framework_summary = quantile_returns(factor, targets, quantiles=5)
    daily_returns = daily.mean_return.unstack('quantile').rename(columns=lambda q: f'Q{q}')
    spread = (daily_returns.Q1 - daily_returns.Q5).rename('Q1_minus_Q5')
    summary = framework_summary.rename(columns={'dates': 'valid_dates', 'observations': 'valid_return_total'})
    counts = daily.loc[daily['count'].gt(0)].groupby(level='quantile').agg(
        membership_total=('members', 'sum'), membership_min=('members', 'min'),
        membership_mean=('members', 'mean'), membership_max=('members', 'max'),
        valid_returns_min=('count', 'min'), valid_returns_mean=('count', 'mean'),
        valid_returns_max=('count', 'max'))
    summary = summary.join(counts)
    summary.index = pd.Index([f'Q{q}' for q in summary.index], name='quantile')
    summary['paired_date_mean_return'] = daily_returns.loc[spread.notna()].mean().reindex(summary.index).to_numpy()
    spread_summary = spread_stats(spread).to_frame().T
    spread_summary.index = pd.Index(['Q1 minus Q5'], name='contrast')
    yearly_returns = daily_returns.groupby(daily_returns.index.year).mean().reindex(range(2010, 2017))
    yearly_counts = daily_returns.groupby(daily_returns.index.year).count().reindex(range(2010, 2017), fill_value=0)
    yearly_spreads = pd.DataFrame({year: spread_stats(spread.loc[spread.index.year == year])
                                   for year in range(2010, 2017)}).T
    for frame in (yearly_returns, yearly_counts, yearly_spreads):
        frame.index.name = 'year'
    return dict(group_membership=groups, daily_quantiles=daily, daily_returns=daily_returns,
                daily_spread=spread.to_frame(), quantile_summary=summary,
                spread_summary=spread_summary, yearly_returns=yearly_returns,
                yearly_counts=yearly_counts, yearly_spreads=yearly_spreads)


def analyze(prices):
    """Slice before evaluation; 5D momentum and t+1 to t+6 labels only in 2010–2016."""
    bounded = prices.loc['2010-01-01':'2016-12-31'].copy()
    validate_panel(bounded, positive=True)
    factor = calculate_momentum(bounded, window=5)
    targets = forward_returns(bounded, horizon=5, entry_lag=1)
    dates = bounded.index.to_series()
    audit = pd.DataFrame({'entry_date': dates.shift(-1), 'exit_date': dates.shift(-6)})
    audit['endpoints_in_period'] = (audit.entry_date.ge('2010-01-01') & audit.entry_date.le('2016-12-31')
                                   & audit.exit_date.ge('2010-01-01') & audit.exit_date.le('2016-12-31'))
    targets.loc[~audit.endpoints_in_period] = np.nan
    result = summarize_quantiles(factor, targets)
    audit['observed_factors'] = factor.notna().sum(axis=1)
    audit['assigned_members'] = result['group_membership'].notna().sum(axis=1)
    audit['valid_factor_return_pairs'] = (factor.notna() & targets.notna()).sum(axis=1)
    audit['spread_included'] = result['daily_spread'].Q1_minus_Q5.notna()
    audit['all_five_groups_valid'] = result['daily_returns'].notna().all(axis=1)
    result['audit'] = audit
    return result


def run(append_report=False):
    prior = REPORT.read_bytes()
    if append_report and HEADING in prior.decode('utf-8'):
        raise ValueError('Quantile section already exists; refusing replacement')
    prices = pd.read_csv(PRICE_PATH, index_col=0, parse_dates=True)
    universe = pd.read_csv(UNIVERSE_PATH)
    if len(universe) != 300 or not universe.ticker.is_unique or set(prices.columns) != set(universe.ticker):
        raise ValueError('Prices must match the frozen 300-security universe')
    results = analyze(prices.reindex(columns=universe.ticker))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, table in results.items():
        table.to_csv(OUT / f'{name}.csv')
    valid = results['audit'].loc[results['audit'].spread_included]
    metadata = dict(exploration_start='2010-01-01', exploration_end='2016-12-31',
                    lookback=5, horizon=5, entry_lag=1, quantiles=5, contrast='Q1 minus Q5',
                    membership_rule='framework average-rank percentile midpoints; ties kept together',
                    minimum_observed_factors=5, minimum_valid_returns_per_group=1,
                    additional_minimum_asset_filter=False, forward_fill=False,
                    equity_warmup='five initial rows within 2010; no added pre-2010 equity data',
                    universe_size=300, equity_matrix_sha256=sha256(PRICE_PATH.read_bytes()).hexdigest(),
                    universe_sha256=sha256(UNIVERSE_PATH.read_bytes()).hexdigest(),
                    previous_report_sha256=sha256(prior).hexdigest(),
                    valid_spread_dates=len(valid), first_signal=str(valid.index.min()),
                    last_signal=str(valid.index.max()),
                    excluded_signal_dates=int((~results['audit'].spread_included).sum()),
                    all_five_groups_valid_dates=int(results['audit'].all_five_groups_valid.sum()))
    (OUT / 'methodology.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout='constrained')
    summary = results['quantile_summary']
    axes[0].bar(summary.index, summary.mean_return * 100, color='#247f74')
    axes[0].set_title('Mean 5-day forward label by quantile')
    axes[0].set_ylabel('Mean forward return (%)')
    yearly = results['yearly_spreads']
    axes[1].bar(yearly.index.astype(str), yearly.mean_spread * 100, color='#bd6546')
    axes[1].set_title('Annual mean Q1 minus Q5 label spread')
    axes[1].set_ylabel('Mean spread (percentage points)')
    for ax in axes:
        ax.axhline(0, color='black', linewidth=.7)
    fig.suptitle('Momentum #001 — 2010–2016 descriptive labels, not strategy returns')
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=160)
    plt.close(fig)
    core_summary = summary[['mean_return', 'valid_dates', 'valid_return_total', 'paired_date_mean_return']]
    membership = summary[['membership_total', 'membership_min', 'membership_mean', 'membership_max',
                          'valid_returns_min', 'valid_returns_mean', 'valid_returns_max']]
    stability = ', '.join(f'{year}: {value * 100:.4f} pp' for year, value in yearly.mean_spread.items())
    section = f'''{HEADING}

### Methodology and fixed scope

The frozen 300-security universe is unchanged. Existing local adjusted prices are
sliced to 2010-01-01 through 2016-12-31 **before** any factor or label calculation.
No 2017–2025 factor evaluation results are read or calculated. The existing
`calculate_momentum(prices, window=5)` gives P[t]/P[t-5]-1 with fill_method=None.
The target is `forward_returns(prices, horizon=5, entry_lag=1)`, P[t+6]/P[t+1]-1.
Entry and exit dates must both be in exploration. The first five signal rows
have no factor warm-up and the final six have no complete in-period endpoints.
No pre-2010 equity warm-up is introduced; prior studies and conclusions are preserved.

`quantile_groups` and `quantile_returns` use only same-date observed factor values
to establish membership, **before** excluding missing future returns. Q1 holds
the lowest Momentum and Q5 the highest. The fixed framework rule is
floor((average_rank - 0.5)/observed_factor_count * 5) + 1. Ties stay together,
so group sizes may differ and bins may be empty. Constant cross sections or fewer
than five observed factors remain unassigned. No alternative grouping rules were searched.

Each group's daily mean gives equal weight to its members with observed forward
endpoints; missing-return members remain counted as members but not as observed
returns. Zero members or zero valid returns produce NaN, never zero. At least
one valid return per group is required; no new arbitrary per-group threshold or
the earlier IC-specific 100-asset threshold is added. Counts below disclose small
groups. Missing prices are not filled. Endpoint-based factor/label formulas do
not require every intermediate price to exist. Membership can be recorded on
an endpoint-excluded date, but that date contributes no forward-return statistic.

Daily spread is Q1 mean minus Q5 mean, only when both are defined on the same
signal date. Time summaries equally weight available daily means, not pooled
stock/date observations. `paired_date_mean_return` restricts each group to valid
spread dates; this discloses any denominator difference. Daily membership and
valid-return counts are retained even for excluded dates.

### Quantile mean forward returns

All returns in the tables are decimal fractions (0.01 = 1%). These are overlapping
5-day labels, not daily, annualized, or compounded portfolio returns.

{markdown_table(core_summary)}

### Membership and valid-return counts

Ranges, averages and membership totals below refer to each group's valid-return
signal dates. `valid_return_total` above is the total observed stock/date label
count. Full date-by-group counts, including zero-count dates, are in `daily_quantiles.csv`.

{markdown_table(membership)}

### Primary descriptive contrast: Q1 minus Q5

{markdown_table(results['spread_summary'])}

Spread standard deviation uses ddof=1; positive fraction means spread strictly
greater than zero. Valid spread dates: {metadata['valid_spread_dates']}, from
{metadata['first_signal'][:10]} through {metadata['last_signal'][:10]}.
Excluded exploration dates: {metadata['excluded_signal_dates']}. Dates with valid
returns in all five groups: {metadata['all_five_groups_valid_dates']}.

### Yearly comparisons and stability

Yearly quantile means (decimal returns):

{markdown_table(results['yearly_returns'])}

Yearly valid-date counts for each quantile:

{markdown_table(results['yearly_counts'])}

Yearly Q1 minus Q5 spread statistics:

{markdown_table(yearly)}

Annual mean spread magnitudes: {stability}. These annual descriptions are
reported without selecting favorable years or changing the specification.

### Descriptive visualizations

![Quantile means and annual spread](figures/momentum_001_quantiles_2010_2016.png)

### Interpretation and limitations

The summaries describe the association between past 5-day Momentum ranks and
subsequent 5-day labels in this exploratory sample. The Q1-minus-Q5 sign reflects
the difference between low- and high-Momentum group outcomes; it does not prove
tradable reversal, Alpha, a causal effect, or an executable long-short return.
Overall and yearly means should be read alongside dispersion, sign fractions,
and membership/valid-return counts rather than as evidence from independent days.

Forward labels overlap, and lookbacks and observations share dates and securities,
creating serial dependence. No cumulative performance, portfolio backtest,
significance test or confidence interval is produced. Prior HAC results concerned
Rank IC and do not supply inference for these return spreads. Any inference for
spreads would require its own dependence-aware analysis and multiplicity plan.

Missing endpoints, IPOs, unassigned factors and ties can change effective weights
and available samples. Keeping missing-return stocks in membership counts does not
eliminate missing-data selection. Current constituents cause survivorship and
selection bias; this is not historical index membership. Adjusted Yahoo prices
can be revised. No transaction costs, turnover, liquidity, short availability,
execution timing, financing or market/sector-risk adjustment is modeled. Positive
mean group labels may reflect market exposure, not factor Alpha. This is another
exploration on an already examined sample; multiple-comparison concerns remain.
No alternative quantile definitions or parameters were searched, no winning group
or strategy is selected, and existing research conclusions are not modified.
Validation and held-out test datasets remain untouched.

Artifacts under `data/research/momentum_001/quantiles_2010_2016/` include
`group_membership.csv`, `daily_quantiles.csv`, `daily_returns.csv`, `daily_spread.csv`,
`quantile_summary.csv`, `spread_summary.csv`, `yearly_returns.csv`, `yearly_counts.csv`,
`yearly_spreads.csv`, `audit.csv`, `methodology.json` and `section.md`.
Reproduce offline: `python -B scripts/momentum_quantiles_001.py`.
`--append-report` appends once and refuses to replace an existing quantile section.
'''
    (OUT / 'section.md').write_text(section, encoding='utf-8')
    if append_report:
        REPORT.write_bytes(prior + b'\n\n' + section.encode('utf-8'))
        assert REPORT.read_bytes().startswith(prior)
    print(summary.to_string())
    print(results['spread_summary'].to_string())
    print(yearly.to_string())
    print(json.dumps(metadata, indent=2))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--append-report', action='store_true')
    run(append_report=parser.parse_args().append_report)
