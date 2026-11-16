"""Post-validation descriptive extension; never evaluate prices after 2019.

Standalone output namespace. The sealed #001-A implementations and artifacts
are read-only. No inference, parameter selection, download, or portfolio logic.
"""
import argparse
from collections import deque
import csv
from datetime import datetime, timezone
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
from scripts.verify_momentum_001_final_test import verify
from scripts.verify_momentum_001_validation import digest

LOOKBACKS = (5, 20, 60)
HORIZONS = (5, 10, 20, 60)
MIN_ASSETS = 100
PERIODS = {
    '2010_2019': ('2010-01-01', '2019-12-31'),
    '2010_2016': ('2010-01-01', '2016-12-31'),
    '2017_2019': ('2017-01-01', '2019-12-31'),
}
OUT = ROOT / 'data/research/momentum_001B'
REPORT = ROOT / 'reports/01B_momentum_horizon.md'
FIGURES = ROOT / 'reports/figures/momentum_001B'


def load_prices(path, tickers):
    """Read date prefixes first; stop BEFORE reading the first post-2019 values.

    Keep at most 60 pre-2010 rows for factor warm-up. An absent warm-up is
    explicitly allowed and audited; no prices are fetched, filled or fabricated.
    This reader targets the frozen, single-line CSV date/price format.
    """
    warmup, rows = deque(maxlen=max(LOOKBACKS)), []
    previous = None
    with Path(path).open(newline='', encoding='utf-8') as stream:
        header = next(csv.reader([stream.readline()]))
        if len(set(tickers)) != len(tickers) or len(set(header[1:])) != len(header)-1 or set(header[1:]) != set(tickers):
            raise ValueError('Frozen ticker universe mismatch')
        while True:
            prefix = []
            while (char := stream.read(1)) not in (',', '', '\n', '\r'):
                prefix.append(char)
            if not prefix and char == '':
                break
            if char != ',':
                raise ValueError('Malformed date prefix')
            date = pd.Timestamp(''.join(prefix))
            if pd.isna(date) or date.tz is not None or (previous is not None and date <= previous):
                raise ValueError('Invalid, duplicate or unsorted date')
            if date > pd.Timestamp('2019-12-31'):
                break  # Even the CSV payload of this row is not read.
            previous = date
            values = next(csv.reader([stream.readline()]))
            if len(values) != len(tickers):
                raise ValueError('Malformed price row')
            row = (date, values)
            (warmup if date < pd.Timestamp('2010-01-01') else rows).append(row)
    if not rows:
        raise ValueError('No permitted research observations')
    selected = list(warmup) + rows
    panel = pd.DataFrame([v for _, v in selected], index=pd.DatetimeIndex([d for d, _ in selected], name='Date'), columns=header[1:])
    panel = panel.replace('', np.nan).apply(pd.to_numeric, errors='raise').reindex(columns=tickers)
    validate_panel(panel, positive=True)
    return panel


def period_inputs(panel, start, end):
    """Bound before shifts: pre-start rows feed factors only, labels stay inside.

    Yearly summaries later group by signal year within these bounded periods;
    they do not impose additional year-end cutoffs.
    """
    if panel.index.max() > pd.Timestamp('2019-12-31'):
        raise ValueError('Held-out rows forbidden')
    validate_panel(panel, positive=True)
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if start < pd.Timestamp('2010-01-01') or end > pd.Timestamp('2019-12-31') or start > end:
        raise ValueError('Invalid research period')
    prices = panel.loc[start:end]
    if prices.empty:
        raise ValueError('Empty research period')
    warmup = panel.loc[panel.index < start].tail(max(LOOKBACKS))
    bounded = pd.concat([warmup, prices])
    factors = {l: calculate_momentum(bounded, window=l).reindex(prices.index) for l in LOOKBACKS}
    labels = {h: forward_returns(prices, horizon=h, entry_lag=1) for h in HORIZONS}
    return prices, factors, labels, len(warmup)


def compare(factors, labels, min_assets=MIN_ASSETS):
    """Pairwise IC and strict all-combination common sample.

    Align dates/tickers by labels, intersect finite factor AND return pairs across
    all combinations, then recompute average ranks on that intersection. Also
    intersect valid IC dates (including zero-variance exclusions) across all
    combinations. Returns both the raw pair intersection and final retained mask.
    """
    panels = list(factors.values()) + list(labels.values())
    dates, tickers = panels[0].index, panels[0].columns
    for frame in panels:
        validate_panel(frame)
        dates = dates.intersection(frame.index, sort=False)
        tickers = tickers.intersection(frame.columns, sort=False)
    if dates.empty or tickers.empty:
        raise ValueError('No common dates or tickers')
    f = {l: x.reindex(index=dates, columns=tickers) for l, x in factors.items()}
    r = {h: x.reindex(index=dates, columns=tickers) for h, x in labels.items()}
    masks = {(l, h): f[l].notna() & r[h].notna() for l in f for h in r}
    common = pd.DataFrame(True, index=dates, columns=tickers)
    for mask in masks.values():
        common &= mask
    individual, strict = {}, {}
    for l, h in masks:
        key = f'L{l}_H{h}'
        individual[key] = rank_ic(f[l], r[h], min_assets=min_assets)
        strict[key] = rank_ic(f[l].where(common), r[h].where(common), min_assets=min_assets)
    individual, strict = pd.DataFrame(individual), pd.DataFrame(strict)
    valid_dates = strict.notna().all(axis=1)
    strict.loc[~valid_dates] = np.nan
    retained = common.copy()
    retained.loc[~valid_dates] = False
    return individual, strict, masks, common, retained


def analyze_period(panel, start, end):
    prices, factors, labels, warmup = period_inputs(panel, start, end)
    individual, common_ic, masks, common_pairs, retained = compare(factors, labels)
    dates = prices.index.to_series()
    summaries, audit = [], []
    for l in LOOKBACKS:
        for h in HORIZONS:
            key = f'L{l}_H{h}'
            endpoints = dates.shift(-(h+1)).notna()
            insufficient_history = pd.Series(np.arange(len(prices)) + warmup < l, index=dates.index)
            for sample, series, mask in [('individual', individual[key], masks[l, h]), ('common', common_ic[key], common_pairs)]:
                counts = mask.sum(axis=1)
                record = dict(sample=sample, lookback=l, horizon=h, **ic_summary(series).to_dict())
                record.update(total_signal_rows=len(prices), warmup_rows_available=warmup,
                              boundary_excluded_dates=int((~endpoints).sum()),
                              insufficient_lookback_rows=int(insufficient_history.sum()),
                              low_pair_dates_inside_boundary=int(((counts < MIN_ASSETS) & endpoints).sum()),
                              undefined_ic_with_enough_pairs=int((series.isna() & counts.ge(MIN_ASSETS) & endpoints).sum()),
                              valid_pairs_on_retained_dates=int(counts[series.notna()].sum()),
                              min_pairs_on_retained_dates=float(counts[series.notna()].min()),
                              mean_pairs_on_retained_dates=float(counts[series.notna()].mean()),
                              pair_coverage_inside_boundary=float(counts[endpoints].sum()/(endpoints.sum()*len(prices.columns))) if endpoints.any() else np.nan)
                summaries.append(record)
                daily = pd.DataFrame(dict(sample=sample, lookback=l, horizon=h, rank_ic=series,
                                         entry_date=dates.shift(-1), exit_date=dates.shift(-(h+1)),
                                         endpoints_valid=endpoints, insufficient_lookback=insufficient_history,
                                         available_pairs=counts, retained_date=series.notna(),
                                         missing_factor_assets=factors[l].isna().sum(axis=1),
                                         missing_label_assets=labels[h].isna().sum(axis=1)), index=prices.index)
                audit.append(daily.rename_axis('Date').reset_index())
    coverage = pd.DataFrame(dict(observed_prices=prices.count(), missing_prices=prices.isna().sum(),
                                 price_coverage=prices.notna().mean(),
                                 first_observed=prices.apply(lambda x: x.first_valid_index()),
                                 last_observed=prices.apply(lambda x: x.last_valid_index())))
    return dict(summary=pd.DataFrame(summaries), audit=pd.concat(audit, ignore_index=True),
                individual=individual, common=common_ic, common_pair_mask=common_pairs,
                common_retained_mask=retained, price_coverage=coverage)


def markdown(frame, digits=6):
    def fmt(x):
        if isinstance(x, (float, np.floating)):
            return f'{x:.{digits}f}' if np.isfinite(x) else 'NA'
        return str(x)
    return '\n'.join(['| ' + ' | '.join(map(str, frame.columns)) + ' |',
                      '| ' + ' | '.join(['---']*len(frame.columns)) + ' |'] +
                     ['| ' + ' | '.join(map(fmt, row)) + ' |' for row in frame.itertuples(index=False, name=None)])


def render(summary, yearly, coverage):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    FIGURES.mkdir(parents=True, exist_ok=False)
    scale = summary['mean'].abs().max()
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    for col, period in enumerate(PERIODS):
        for row, sample in enumerate(('individual', 'common')):
            data = summary.query('period == @period and sample == @sample').pivot(index='lookback', columns='horizon', values='mean')
            ax = axes[row, col]
            im = ax.imshow(data, cmap='RdBu_r', vmin=-scale, vmax=scale, aspect='auto')
            for i in range(3):
                for j in range(4):
                    ax.text(j, i, f'{data.iloc[i,j]:.3f}', ha='center', va='center', fontsize=9)
            ax.set(xticks=range(4), xticklabels=HORIZONS, yticks=range(3), yticklabels=LOOKBACKS,
                   xlabel='Return horizon H (trading days)', ylabel='Momentum lookback L', title=f'{period.replace("_", "–")} / {sample}')
    fig.colorbar(im, ax=axes, label='Mean daily Rank IC')
    fig.suptitle('#001-B: descriptive post-validation exploration; no significance tests')
    fig.savefig(FIGURES/'mean_ic_heatmaps.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True, constrained_layout=True)
    for ax, period in zip(axes, PERIODS):
        for l in LOOKBACKS:
            for sample, style in [('individual', '-'), ('common', '--')]:
                data = summary.query('period == @period and lookback == @l and sample == @sample').sort_values('horizon')
                ax.plot(data.horizon, data['mean'], style, marker='o', color={5:'C0',20:'C1',60:'C2'}[l], label=f'L={l} {sample}')
        ax.axhline(0, color='gray', lw=.8)
        ax.set(title=period.replace('_', '–'), xlabel='H (trading days)', xticks=HORIZONS)
    axes[0].set_ylabel('Mean daily Rank IC')
    axes[-1].legend(fontsize=7)
    fig.savefig(FIGURES/'horizon_profiles.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(2, 1, figsize=(13, 7), constrained_layout=True)
    for ax, sample in zip(axes, ('individual', 'common')):
        data = yearly.query('period != "2010_2019" and sample == @sample').pivot(index='year', columns='combination', values='mean')
        data = data.reindex(columns=[f'L{l}_H{h}' for l in LOOKBACKS for h in HORIZONS])
        lim = yearly['mean'].abs().max()
        im = ax.imshow(data, cmap='RdBu_r', vmin=-lim, vmax=lim, aspect='auto')
        ax.set(xticks=range(12), xticklabels=data.columns, yticks=range(len(data)), yticklabels=data.index, title=f'Yearly mean / {sample}; labels bounded by each subperiod')
        fig.colorbar(im, ax=ax, label='Mean Rank IC')
    fig.savefig(FIGURES/'yearly_ic_heatmaps.png', dpi=160)
    plt.close(fig)
    sections = ['# Momentum Research #001-B: Prediction Horizon Analysis',
        '**Post-validation descriptive exploration.** #001-A and its frozen, unexecuted final-test protocol are preserved. 2017–2019 is already-seen data, not fresh validation. No 2020–2025 price payloads, IC or quantile outcomes are read or calculated.',
        '## Fixed methodology',
        'Original frozen 300-security universe; adjusted Yahoo Close snapshot. L ∈ {5,20,60}; H ∈ {5,10,20,60}; factor P[t]/P[t−L]−1; target P[t+1+H]/P[t+1]−1. Signals are available after close; shifts count observed trading rows. Daily Spearman correlations use average ranks after pairwise deletion, at least 100 pairs and nonconstant cross sections. Dates are equally weighted. Standard deviation uses ddof=1; ICIR is mean/std, unannualized; positive fraction counts IC>0.',
        'For each period, retain up to 60 preceding observed price rows only for factor warm-up. No fill or calendar imputation. If pre-period history is unavailable, initial factors remain missing. Labels are constructed on that period alone; the last H+1 rows have no eligible exit. Intermediate missing prices do not invalidate endpoint-only formulas. The pooled 2010–2019 panel can cross 2016/2017; separately recomputed subperiod labels cannot. Yearly summaries group by signal year within the named period; endpoints can cross a year-end but never its period-end.',
        'Common sample means the intersection of all three observed factors and all four observed return labels by date/ticker, followed by a shared valid-date intersection across all 12 IC series. Ranks are recomputed after ticker intersection. Thus all common comparisons within a period share the same ticker pairs and dates; return values still differ by H. This is an availability-conditioned sample and can differ from individual samples. The paired mask and retained-date mask are saved separately.',
        'No p-values, HAC estimates, significance claims, parameter ranking, or optimal pair selection are made. In particular lag-5 HAC is not carried over to longer horizons.',
        '## Mean Rank IC matrices', '![Mean matrices](figures/momentum_001B/mean_ic_heatmaps.png)']
    for period in PERIODS:
        for sample in ('individual', 'common'):
            subset = summary.query('period == @period and sample == @sample')
            sections += [f'### {period.replace("_", "–")} — {sample}', markdown(subset.pivot(index='lookback', columns='horizon', values='mean').reset_index().rename(columns={'lookback':'L / H'})),
                         markdown(subset[['lookback','horizon','count','mean','std','icir','positive_fraction']])]
    sections += ['## Coverage and exclusions',
                 'Boundary counts refer to each combination’s own H. Common samples additionally lose dates/pairs due to all other combinations; the daily audit records available intersection pairs and retained dates separately. Low-pair counts include initial missing lookbacks. These diagnostics overlap and must not be added as disjoint exclusions. Price coverage includes all signal rows and all 300 frozen columns.', markdown(coverage),
                 markdown(summary[['period','sample','lookback','horizon','count','boundary_excluded_dates','insufficient_lookback_rows','low_pair_dates_inside_boundary','undefined_ic_with_enough_pairs','mean_pairs_on_retained_dates','pair_coverage_inside_boundary']]),
                 '## Yearly behavior', '![Yearly comparisons](figures/momentum_001B/yearly_ic_heatmaps.png)', markdown(yearly),
                 '## Descriptive horizon profiles', '![Horizon profiles](figures/momentum_001B/horizon_profiles.png)']
    for period in PERIODS:
        for sample in ('individual','common'):
            subset=summary.query('period == @period and sample == @sample')
            descriptions=[]
            for l in LOOKBACKS:
                values=subset.query('lookback == @l').sort_values('horizon')['mean']
                signs=['negative' if v<0 else 'positive' if v>0 else 'zero' for v in values]
                descriptions.append(f'L={l}: ' + ', '.join(f'H={h} {v:.4f} ({s})' for h,v,s in zip(HORIZONS,values,signs)) + ('; sign changes across horizons' if len(set(signs))>1 else '; no sign change across horizons'))
            sections.append(f'**{period.replace("_", "–")} / {sample}:** ' + '. '.join(descriptions) + '.')
    sections += ['## Interpretation and limitations',
        'These patterns characterize the fixed grid, not a selected trading rule. Sign changes and differences across horizons/subperiods are descriptive; they need not imply structural or causal changes. Unequal availability affects individual comparisons; the strict common sample controls shared observations but conditions on complete endpoints and loses data. Overlapping labels, shared securities and persistent factors create serial dependence, especially at H=60. No unadjusted comparison across the 12 combinations establishes significance. Multiple periods, years and sample variants add further comparisons. The 2017–2019 period was already used in #001-A validation, and this extension is explicitly post-validation exploration.',
        'The current-constituent frozen universe has survivorship and selection bias and does not reconstruct historical membership. IPO histories, delistings, missing prices, corporate actions, retrospective adjustments and vendor revisions limit interpretation. No executable portfolio, costs, liquidity or risk-adjusted Alpha is modeled. Overlapping returns are not compounded. The unexecuted #001-A 2020–2025 final protocol remains fixed; these results must not be used to amend it.',
        '## Reproduction and provenance',
        'Driver: `scripts/momentum_horizon_001B.py --run`; it refuses existing result/report paths. Notebook `research/01B_momentum_horizon.ipynb` reads saved #001-B outputs only. `data/research/momentum_001B/manifest.json` records source/data/universe hashes, dependencies, period boundaries, output hashes and before/after #001-A integrity checks. Per-period audit CSVs, common masks, ticker coverage, summary and yearly tables are local and Git-ignored. The original validation report append is verified using its recorded full hash and archived prefix; its old seal is not regenerated.']
    REPORT.write_text('\n\n'.join(sections)+'\n', encoding='utf-8')


def run():
    if OUT.exists() or REPORT.exists() or FIGURES.exists():
        raise FileExistsError('Preserve existing #001-B results; output already exists')
    before = verify()
    protocol = json.loads((ROOT/'config/momentum_001_final_test.json').read_text(encoding='utf-8'))
    universe = pd.read_csv(ROOT/protocol['universe']['path'])
    if len(universe) != 300 or not universe.ticker.is_unique:
        raise ValueError('Expected original 300 securities')
    prices = load_prices(ROOT/protocol['data']['path'], universe.ticker.tolist())
    OUT.mkdir(parents=True)
    summaries, years, coverage = [], [], []
    for period, (start, end) in PERIODS.items():
        print(f'Analyzing {period} (bounded labels), fixed 12 combinations', flush=True)
        tables = analyze_period(prices, start, end)
        folder = OUT/period
        folder.mkdir()
        for name, table in tables.items():
            table.to_csv(folder/(name+'.csv.gz' if 'mask' in name else name+'.csv'), index=name not in ('summary','audit'))
        summaries.append(tables['summary'].assign(period=period))
        pc = tables['price_coverage']
        coverage.append(dict(period=period, securities=len(pc), signal_rows=len(tables['individual']),
                             observed_prices=int(pc.observed_prices.sum()), missing_prices=int(pc.missing_prices.sum()),
                             price_coverage=float(pc.price_coverage.mean()), warmup_rows=int(tables['summary'].warmup_rows_available.iloc[0])))
        for sample in ('individual','common'):
            for year, frame in tables[sample].groupby(tables[sample].index.year):
                for key in frame:
                    years.append(dict(period=period, sample=sample, year=year, combination=key, **ic_summary(frame[key]).to_dict()))
    summary, yearly, coverage = pd.concat(summaries, ignore_index=True), pd.DataFrame(years), pd.DataFrame(coverage)
    summary.to_csv(OUT/'summary.csv', index=False)
    yearly.to_csv(OUT/'yearly.csv', index=False)
    coverage.to_csv(OUT/'coverage.csv', index=False)
    render(summary, yearly, coverage)
    after = verify()
    artifacts = sorted(p for p in OUT.rglob('*') if p.is_file()) + [REPORT] + sorted(FIGURES.glob('*.png'))
    sources = [Path(__file__), ROOT/'tests/test_momentum_horizon_001B.py', ROOT/'research/01B_momentum_horizon.ipynb']
    manifest = dict(research_id='momentum_001B', status='post-validation descriptive exploration', created_utc=datetime.now(timezone.utc).isoformat(),
                    design=dict(lookbacks=LOOKBACKS, horizons=HORIZONS, entry_lag=1, min_assets=MIN_ASSETS, periods=PERIODS),
                    data=protocol['data'], universe=protocol['universe'], environment=protocol['environment'],
                    original_integrity_before=before, original_integrity_after=after,
                    source_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in sources},
                    artifact_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in artifacts},
                    held_out_values_read=False, inference_performed=False, original_final_test_executed=False)
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(summary[['period','sample','lookback','horizon','count','mean']].to_string(index=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Run only the isolated, bounded 2010–2019 extension')
    if parser.parse_args().run:
        run()
