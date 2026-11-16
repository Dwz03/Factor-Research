"""Single-use, gated execution of frozen Momentum #001 validation v1.0.0."""
import argparse
from collections import deque
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_momentum_001_validation import verify, digest
from src.data.validation import validate_panel
from factors.momentum import calculate_momentum
from src.evaluation import forward_returns, rank_ic, hac_mean, quantile_returns, quantile_groups

OUT = ROOT / 'data/validation/momentum_001_v1'
PROTOCOL = ROOT / 'config/momentum_001_validation.json'
DRIVER = Path(__file__).resolve()
HEADING = '## Frozen protocol validation execution: 2017–2019 (v1.0.0)'


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def source_tests():
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted((ROOT / 'tests').glob('*.py'))}


def preflight():
    verification = verify()
    if (OUT / 'started.json').exists():
        raise ValueError('Execution already started; no new preflight or run allowed')
    folder = OUT / 'preflight'
    folder.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               f'--junitxml={folder / "tests.xml"}']
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (folder / 'tests.log').write_text(run.stdout + run.stderr, encoding='utf-8')
    print(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError('Preflight tests failed; real outcomes remain unread')
    suites = list(ET.parse(folder / 'tests.xml').getroot().iter('testsuite'))
    counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites)
              for key in ('tests', 'failures', 'errors', 'skipped')}
    if not counts['tests'] or any(counts[key] for key in ('failures', 'errors', 'skipped')):
        raise RuntimeError('All required tests must pass without skips')
    verify()
    save_json(folder / 'passed.json', dict(driver_sha256=digest(DRIVER),
              tests_sha256=source_tests(), junit_sha256=digest(folder / 'tests.xml'),
              log_sha256=digest(folder / 'tests.log'), counts=counts, verification=verification,
              protocol_sha256=digest(PROTOCOL), completed_utc=datetime.now(timezone.utc).isoformat()))


def load_bounded_prices(path, tickers, protocol):
    """Read only five warm-up rows plus validation prices; stop before held-out values."""
    start = pd.Timestamp(protocol['periods']['validation']['start'])
    end = pd.Timestamp(protocol['periods']['validation']['end_inclusive'])
    warmup = deque(maxlen=protocol['timing']['warmup']['preceding_rows'])
    rows = []
    previous = None
    with Path(path).open(newline='', encoding='utf-8') as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if len(header[1:]) != len(set(header[1:])) or set(header[1:]) != set(tickers):
            raise ValueError('Frozen ticker universe mismatch')
        for row in reader:
            date = pd.Timestamp(row[0])
            if date > end:
                break  # Do not parse or evaluate this row's held-out price values.
            if pd.isna(date) or date.tz is not None or (previous is not None and date <= previous):
                raise ValueError('Unsorted, duplicate, missing or timezone-aware date')
            previous = date
            if len(row) != len(header):
                raise ValueError('Malformed price row')
            if date < start:
                warmup.append(row)
            else:
                rows.append(row)
    if len(warmup) != protocol['timing']['warmup']['preceding_rows'] or not rows:
        raise ValueError('Insufficient warm-up or no validation rows')
    selected = list(warmup) + rows
    panel = pd.DataFrame([r[1:] for r in selected], columns=header[1:],
                         index=pd.DatetimeIndex([r[0] for r in selected], name='Date'))
    panel = panel.replace('', np.nan).apply(pd.to_numeric, errors='raise').reindex(columns=tickers)
    validate_panel(panel, positive=True)
    return panel


def decision(mean, se, p, n, lag=5, alpha=.05):
    if n <= lag or not np.isfinite([mean, se, p]).all() or se <= 0 or not 0 <= p <= 1:
        return 'Inconclusive'
    return 'Pass' if mean < 0 and p < alpha else 'Not Supported'


def assess_ic(ic, protocol):
    rule = protocol['primary']['inference']
    observed = ic.dropna()
    result = dict(decision='Inconclusive', reason=None, valid_ic_observations=len(observed),
                  mean_rank_ic=None, hac_se=None, t_stat=None, one_sided_p=None,
                  one_sided_upper_95=None, leading_trim=0, trailing_trim=0)
    if observed.empty:
        result['reason'] = 'No valid IC observations'
        return result
    first, last = observed.index[0], observed.index[-1]
    result.update(first_signal=str(first.date()), last_signal=str(last.date()),
                  leading_trim=int((ic.index < first).sum()), trailing_trim=int((ic.index > last).sum()))
    contiguous = ic.loc[first:last]
    if contiguous.isna().any():
        result['reason'] = 'Interior undefined IC; no gap compression permitted'
        return result
    if len(contiguous) <= rule['minimum_n_exclusive']:
        result['reason'] = 'Insufficient observations for fixed HAC lag'
        return result
    try:
        estimate = hac_mean(contiguous, lag=rule['lag'], use_correction=rule['covariance_correction'])
        p = float(norm.cdf(estimate.t_stat))
        upper = float(estimate['mean'] + norm.ppf(1-rule['alpha']) * estimate.hac_se)
        label = decision(estimate['mean'], estimate.hac_se, p, len(contiguous), rule['lag'], rule['alpha'])
        if label == 'Inconclusive' or not np.isfinite([estimate.t_stat, upper]).all():
            result['reason'] = 'Nonfinite or nonpositive HAC variance/inference'
            return result
        result.update(decision=label, reason='Frozen primary lower-tail rule applied',
                      mean_rank_ic=float(estimate['mean']), hac_se=float(estimate.hac_se),
                      t_stat=float(estimate.t_stat), one_sided_p=p, one_sided_upper_95=upper)
    except (ValueError, ArithmeticError) as exc:
        result['reason'] = f'HAC eligibility failure: {exc}'
    return result


def evaluate(panel, protocol):
    """Pure driver logic, tested synthetically before a single authorized real call."""
    validate_panel(panel, positive=True)
    start = pd.Timestamp(protocol['periods']['validation']['start'])
    end = pd.Timestamp(protocol['periods']['validation']['end_inclusive'])
    if panel.index.max() > end or (panel.index < start).sum() != protocol['timing']['warmup']['preceding_rows']:
        raise ValueError('Input must contain exactly five warm-up rows and validation only')
    factor = calculate_momentum(panel, window=protocol['factor']['window']).loc[start:end]
    validation_prices = panel.loc[start:end]
    labels = forward_returns(validation_prices, horizon=protocol['timing']['horizon_rows'],
                             entry_lag=protocol['timing']['entry_lag_rows'])
    dates = validation_prices.index.to_series()
    lag = protocol['timing']['entry_lag_rows']
    horizon = protocol['timing']['horizon_rows']
    audit = pd.DataFrame({'entry_date': dates.shift(-lag), 'exit_date': dates.shift(-(lag+horizon))})
    audit['endpoints_valid'] = (audit.entry_date.ge(start) & audit.entry_date.le(end)
                               & audit.exit_date.ge(start) & audit.exit_date.le(end))
    labels.loc[~audit.endpoints_valid] = np.nan
    pairs = factor.notna() & labels.notna()
    ic = rank_ic(factor, labels, min_assets=protocol['primary']['min_assets'])
    audit['valid_pairs'] = pairs.sum(axis=1)
    audit['missing_factor_assets'] = factor.isna().sum(axis=1)
    audit['missing_return_assets'] = labels.isna().sum(axis=1)
    audit['factor_unique_paired'] = factor.where(pairs).nunique(axis=1)
    audit['return_unique_paired'] = labels.where(pairs).nunique(axis=1)
    audit['rank_ic'] = ic
    audit['exclusion_reason'] = ''
    audit.loc[ic.isna(), 'exclusion_reason'] = 'undefined_cross_section'
    audit.loc[ic.isna() & ((audit.factor_unique_paired < 2) | (audit.return_unique_paired < 2)),
              'exclusion_reason'] = 'zero_variance_paired_cross_section'
    audit.loc[audit.valid_pairs < protocol['primary']['min_assets'], 'exclusion_reason'] = 'fewer_than_100_pairs'
    audit.loc[~audit.endpoints_valid, 'exclusion_reason'] = 'forward_endpoint_outside_validation'
    primary = assess_ic(ic, protocol)
    tables = {'daily_ic_audit': audit, 'valid_pair_mask': pairs}
    if primary['decision'] == 'Inconclusive':
        return primary, None, tables  # Frozen eligibility rule requires stopping.
    groups = quantile_groups(factor, quantiles=protocol['secondary']['quantiles'])
    daily, summary = quantile_returns(factor, labels, quantiles=protocol['secondary']['quantiles'])
    means = daily.mean_return.unstack('quantile')
    spread = (means[1] - means[5]).rename('Q1_minus_Q5')
    valid = spread.dropna()
    secondary = dict(valid_dates=len(valid), mean_spread=float(valid.mean()) if len(valid) else None,
                     std_spread=float(valid.std(ddof=1)) if len(valid)>1 else None,
                     positive_fraction=float(valid.gt(0).mean()) if len(valid) else None)
    summary = summary.join(daily.loc[daily['count'].gt(0)].groupby(level='quantile').agg(
        membership_total=('members','sum'), members_min=('members','min'),
        members_mean=('members','mean'), members_max=('members','max'),
        valid_returns_min=('count','min'), valid_returns_mean=('count','mean'), valid_returns_max=('count','max')))
    tables.update(quantile_membership=groups, daily_quantiles=daily, quantile_summary=summary,
                  daily_spread=spread.to_frame())
    return primary, secondary, tables


def markdown(frame):
    table = frame.reset_index()
    rows = ['| ' + ' | '.join(map(str,table.columns)) + ' |', '| ' + ' | '.join(['---']*len(table.columns))+' |']
    for row in table.itertuples(index=False,name=None):
        rows.append('| '+' | '.join(f'{v:.9f}' if isinstance(v,float) else str(v) for v in row)+' |')
    return '\n'.join(rows)


def execute():
    # All gates occur before real price parsing or claiming the single execution.
    if (OUT / 'started.json').exists():
        raise ValueError('This protocol has already been attempted; reruns forbidden')
    verification = verify()
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    passed_path = OUT / 'preflight/passed.json'
    passed = json.loads(passed_path.read_text(encoding='utf-8'))
    if (passed['driver_sha256'] != digest(DRIVER) or passed['tests_sha256'] != source_tests()
        or passed['protocol_sha256'] != digest(PROTOCOL)
        or passed['junit_sha256'] != digest(OUT / 'preflight/tests.xml')
        or passed['log_sha256'] != digest(OUT / 'preflight/tests.log')):
        raise ValueError('Driver, tests, or preflight evidence changed after passing')
    if any(passed['counts'][k] for k in ('errors','failures','skipped')) or not passed['counts']['tests']:
        raise ValueError('Required tests not passed')
    stamp = dict(protocol_id=protocol['protocol_id'], started_utc=datetime.now(timezone.utc).isoformat(),
                 driver_sha256=digest(DRIVER), protocol_sha256=digest(PROTOCOL),
                 lock_sha256=digest(ROOT/'config/momentum_001_validation.lock.json'),
                 preflight_sha256=digest(passed_path), verification=verification)
    with (OUT / 'started.json').open('x', encoding='utf-8') as stream:
        json.dump(stamp, stream, indent=2)
    # No deletion or reset of this marker, even after an error.
    report = ROOT / 'reports/01_momentum.md'
    prior = report.read_bytes()
    (OUT / 'exploration_report_frozen.md').write_bytes(prior)
    (OUT / 'executed_driver.py').write_bytes(DRIVER.read_bytes())
    try:
        universe = pd.read_csv(ROOT/protocol['universe']['path'])
        if len(universe) != protocol['universe']['size'] or not universe.ticker.is_unique:
            raise ValueError('Invalid frozen universe')
        panel = load_bounded_prices(ROOT/protocol['data']['path'], universe.ticker.tolist(), protocol)
        primary, secondary, tables = evaluate(panel, protocol)
        for name, table in tables.items():
            table.to_csv(OUT/f'{name}.csv')
        input_coverage = dict(warmup_dates=[str(d.date()) for d in panel.index if d < pd.Timestamp('2017-01-01')],
                              last_price_date=str(panel.index.max().date()), securities=len(panel.columns),
                              validation_dates=len(panel.loc['2017-01-01':]),
                              entirely_missing_symbols=panel.columns[panel.isna().all()].tolist())
    except Exception as exc:
        primary = dict(decision='Inconclusive', reason=f'{type(exc).__name__}: {exc}')
        secondary, tables, input_coverage = None, {}, {}
    result = dict(primary=primary, secondary=secondary, input_coverage=input_coverage,
                  completed_utc=datetime.now(timezone.utc).isoformat(), tests=passed['counts'])
    save_json(OUT/'result.json',result)
    # Verify inputs and original report a second time before the authorized append.
    verify()
    section = f'''{HEADING}

This is the single authorized temporal validation execution, distinct from all
2010–2016 exploration above. Protocol and seal were verified before tests and
execution. No specification was amended. The 5D negative-IC hypothesis was selected
after exploration, not independently pre-specified before it. Validation covers
2017-01-01 through 2019-12-31; no 2020–2025 evaluation outcomes were read or computed.

### Primary outcome and frozen decision

**Decision: {primary['decision']}**. {primary['reason']}.

{markdown(pd.Series(primary, name='value').to_frame())}

The fixed target is P[t+6]/P[t+1]-1, factor is P[t]/P[t-5]-1, min_assets=100.
HAC uses lag 5, Bartlett weights, n/(n-1) correction, and an asymptotic normal
reference. The p-value is norm.cdf(t), one-sided lower tail, not half a two-sided
p-value regardless of sign. The one-sided 95% upper bound uses norm.ppf(0.95).
Only mean<0 AND p<0.05 passes; eligibility failure is Inconclusive. A Not Supported
result does not prove a zero or positive effect, and the hypothesis is not changed.

### Secondary descriptive outcome

{markdown(pd.Series(secondary, name='value').to_frame()) if secondary is not None else 'Not evaluated: primary eligibility required stopping.'}

{markdown(tables['quantile_summary']) if 'quantile_summary' in tables else ''}

Returns/spreads are decimal fractions, not percentages. Q1 is lowest Momentum;
Q5 highest. Membership precedes future-label exclusions. Group means use equal
weights over available labels; spread dates require both groups, without applying
the primary 100-asset filter. These descriptions cannot change the primary decision.
No secondary p-values, parameter searches, cumulative returns or backtest were run.

### Coverage, tests and provenance

Five preceding observed price rows warm up the factor, and only validation dates
enter outcomes. Labels extending beyond 2019 are missing; no filling is performed.
Daily exclusions, pair counts, membership and valid-return counts are saved locally.
Input coverage: `{json.dumps(input_coverage)}`.
Pre-outcome full pytest suite: `{json.dumps(passed['counts'])}`.
Driver SHA-256: `{stamp['driver_sha256']}`.
Protocol SHA-256: `{stamp['protocol_sha256']}`.

Artifacts: `data/validation/momentum_001_v1/` contains the single-use marker,
driver snapshot, preflight log/JUnit/results, daily audits, result tables, execution
metadata and SHA-256 artifact manifest. The exact sealed pre-validation report is
archived as `exploration_report_frozen.md`. Its bytes remain an unchanged prefix
of this report; the original protocol and integrity seal are unchanged.
Because this report was itself frozen, the original strict verifier will now
detect its authorized append. Post-execution auditing verifies the sealed report
archive/prefix separately and all other frozen files normally; the lock is not regenerated.

### Interpretation limits

The reported primary decision applies only to the predeclared directional test
in this frozen current-constituent sample. Exploration-driven selection,
survivorship bias, missing histories, retrospective adjustments, dependence beyond
lag 5 and temporal instability remain limitations. Secondary spreads do not prove
tradability or Alpha. Prior exploration conclusions are preserved. No outcome
authorizes tuning, rerunning this validation, or opening the 2020–2025 held-out period.
'''
    (OUT/'section.md').write_text(section,encoding='utf-8')
    report.write_bytes(prior+b'\n\n'+section.encode('utf-8'))
    assert report.read_bytes().startswith(prior)
    # Post-append audit: preserve the original frozen report bytes, never reseal.
    for relative, record in protocol['frozen_files'].items():
        path = OUT/'exploration_report_frozen.md' if relative == 'reports/01_momentum.md' else ROOT/relative
        if digest(path) != record['sha256']:
            raise ValueError(f'Post-execution preservation failure: {relative}')
        if record.get('snapshot') and digest(ROOT/record['snapshot']) != record['sha256']:
            raise ValueError(f'Snapshot changed: {relative}')
    lock = json.loads((ROOT/'config/momentum_001_validation.lock.json').read_text())
    for relative, expected in lock['sha256'].items():
        if digest(ROOT/relative) != expected:
            raise ValueError(f'Seal changed: {relative}')
    result['post_execution_preservation'] = 'all frozen artifacts match; report archive and prefix preserved'
    save_json(OUT/'result.json',result)
    artifacts = {str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file()}
    save_json(OUT/'artifacts.json',dict(sha256=artifacts, report_sha256=digest(report),
                                      report_prefix_bytes=len(prior), driver_sha256=digest(DRIVER)))
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight', action='store_true')
    group.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    preflight() if args.preflight else execute()
