"""Offline inference using ONLY saved 2010–2016 common-sample daily Rank IC."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from importlib.metadata import version

import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.validation import validate_panel
from src.evaluation import hac_mean

SOURCE = ROOT / 'data/research/momentum_001/window_sensitivity_2010_2016/common.csv'
OUT = ROOT / 'data/research/momentum_001/hac_2010_2016'
REPORT = ROOT / 'reports/01_momentum.md'
HEADING = '## Exploratory dependence-aware inference (2010–2016 only)'
LAGS = (5, 10, 20)


def complete_common_sample(frame):
    """Reject out-of-period, mismatched, or internally gapped saved IC samples."""
    validate_panel(frame)
    if list(frame.columns) != ['5D', '20D', '60D']:
        raise ValueError('Expected the three saved common-sample columns in fixed order')
    if (frame.index < pd.Timestamp('2010-01-01')).any() or (frame.index > pd.Timestamp('2016-12-31')).any():
        raise ValueError('Inference input must contain only 2010–2016 IC data')
    if frame.abs().gt(1 + 1e-12).any().any():
        raise ValueError('Invalid Rank IC outside [-1, 1]')
    complete = frame.notna().all(axis=1)
    if (frame.notna().any(axis=1) & ~complete).any() or not complete.any():
        raise ValueError('Common sample is empty or windows have different valid dates')
    result = frame.loc[complete]
    if not complete.loc[result.index.min():result.index.max()].all():
        raise ValueError('Interior excluded rows would compress trading-day HAC lags')
    return result


def infer(frame):
    """Paired differences are formed first; HAC is applied directly to each series."""
    sample = complete_common_sample(frame)
    series = {w: sample[w] for w in sample}
    series.update({f'{a} minus {b}': sample[a] - sample[b]
                   for a, b in [('5D', '20D'), ('5D', '60D'), ('20D', '60D')]})
    rows, verification = [], []
    for name, values in series.items():
        for lag in LAGS:
            ours = hac_mean(values, lag=lag, use_correction=True)
            reference = OLS(values.to_numpy(), np.ones((len(values), 1))).fit().get_robustcov_results(
                cov_type='HAC', maxlags=lag, kernel='bartlett', use_correction=True, use_t=False)
            ci = reference.conf_int(alpha=.05)[0]
            expected = dict(mean=reference.params[0], hac_variance=reference.cov_params()[0, 0],
                            hac_se=reference.bse[0], t_stat=reference.tvalues[0],
                            p_value=reference.pvalues[0], ci_low=ci[0], ci_high=ci[1])
            for metric, value in expected.items():
                np.testing.assert_allclose(ours[metric], value, rtol=1e-10, atol=1e-12)
                verification.append(dict(series=name, lag=lag, metric=metric, ours=ours[metric],
                                         statsmodels=value, absolute_difference=abs(ours[metric]-value)))
            rows.append(dict(series=name, kind='paired difference' if 'minus' in name else 'window mean',
                             **ours.to_dict()))
    results = pd.DataFrame(rows)
    results[['n', 'lag']] = results[['n', 'lag']].astype(int)
    return sample, results, pd.DataFrame(verification)


def markdown(frame):
    rows = ['| ' + ' | '.join(map(str, frame.columns)) + ' |',
            '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |']
    for row in frame.itertuples(index=False, name=None):
        rows.append('| ' + ' | '.join(f'{v:.6f}' if isinstance(v, float) else str(v) for v in row) + ' |')
    return '\n'.join(rows)


def run(append_report=False):
    prior = REPORT.read_bytes()
    if append_report and HEADING in prior.decode('utf-8'):
        raise ValueError('Inference section already exists; refusing to replace prior results')
    source_bytes = SOURCE.read_bytes()
    frame = pd.read_csv(SOURCE, index_col=0, parse_dates=True)
    sample, results, verification = infer(frame)  # Must pass reference checks BEFORE reporting.
    OUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT / 'hac_results.csv', index=False)
    verification.to_csv(OUT / 'statsmodels_verification.csv', index=False)
    sensitivity = results.pivot(index='series', columns='lag', values='p_value').reindex(
        results.series.drop_duplicates())
    sensitivity.to_csv(OUT / 'p_value_sensitivity.csv')
    metadata = dict(source=str(SOURCE.relative_to(ROOT)), source_sha256=sha256(source_bytes).hexdigest(),
                    n=len(sample), first_signal=str(sample.index.min()), last_signal=str(sample.index.max()),
                    primary_lag=5, sensitivity_lags=[10, 20], kernel='Bartlett',
                    covariance_correction='n/(n-1); intercept-only k=1', reference_distribution='normal',
                    confidence_level=.95, test='two-sided; null mean or paired mean difference = 0',
                    p_values_adjusted=False, statsmodels_version=version('statsmodels'),
                    scipy_version=version('scipy'), reference_checks=len(verification),
                    max_reference_absolute_difference=float(verification.absolute_difference.max()),
                    previous_report_sha256=sha256(prior).hexdigest())
    (OUT / 'methodology.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    columns = ['series', 'lag', 'n', 'mean', 'hac_se', 't_stat', 'p_value', 'ci_low', 'ci_high']
    comparisons = []
    for name, row in sensitivity.iterrows():
        below = [str(lag) for lag in LAGS if row[lag] < .05]
        comparisons.append(f'- {name}: unadjusted exploratory p < 0.05 at ' +
                           ('lags ' + ', '.join(below) if below else 'none of the specified lags') +
                           '; p-values at lags 5/10/20 = ' + '/'.join(f'{row[l]:.6f}' for l in LAGS) + '.')
    stable = sensitivity.lt(.05).nunique(axis=1).eq(1).all()
    stability_note = ('The nominal threshold pattern is unchanged across all three lag choices.'
                      if stable else 'At least one nominal threshold comparison changes across lag choices.')
    section = f'''{HEADING}

### Scope and pre-specified conventions

Only `data/research/momentum_001/window_sensitivity_2010_2016/common.csv` was
used as the statistical input. No prices, factor matrices, other research IC
series, or validation/test data were read or evaluated. All three windows use
the existing strict common dates and ticker/return pairs. There are {len(sample)}
observations, {sample.index.min().date()} through {sample.index.max().date()}.
All-missing leading warm-up and trailing endpoint rows are trimmed jointly;
there are no interior excluded rows or partially missing cross-window IC rows.
HAC lags count consecutive saved trading observations, not calendar days.
This verifies continuity within the saved grid, not an independent exchange calendar.
The 5-day prediction horizon and lag-1 entry of the saved results are unchanged.

Primary bandwidth: **5**. Sensitivity bandwidths: **10 and 20**, fixed before
viewing inference. Null hypotheses are mean IC = 0, and mean paired difference = 0.
Each difference is constructed date by date first; its own HAC covariance is
estimated directly. Separate window SEs are not combined as if independent.

For residuals u[t] = IC[t] - mean(IC), Bartlett weights are w[j]=1-j/(L+1).
Cov(mean) = (sum(u[t]^2) + 2 sum(j=1..L) w[j] sum(t=j+1..n) u[t]u[t-j]) / n^2,
multiplied by **n/(n-1)**. This is the n/(n-k) correction for intercept-only OLS
with k=1. Autocovariances use denominator n, not n-j. No annualization is used.
The reported t-statistic is mean/HAC_SE, with an **asymptotic standard-normal**
reference: two-sided p = 2 Phi(-abs(t)); 95% CI = mean +/- 1.959964 HAC_SE.
The finite-sample covariance multiplier does not make this an exact finite-sample
Student-t test. CIs are pointwise, not simultaneous.

Convention references: [statsmodels cov_hac](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html)
and [robust covariance inference](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html).
The explicit reference configuration is intercept-only OLS followed by
`get_robustcov_results(cov_type="HAC", maxlags=L, kernel="bartlett", use_correction=True, use_t=False)`.

### Numerical verification before interpretation

An independently implemented scalar HAC estimator was compared with statsmodels
{metadata['statsmodels_version']} on all six actual series at all three lags.
All {len(verification)} comparisons (mean, covariance, SE, t, p and CI endpoints)
passed rtol=1e-10, atol=1e-12. Maximum absolute discrepancy:
{metadata['max_reference_absolute_difference']:.3g}. Synthetic reference tests also cover
autocorrelation, heteroskedasticity, paired dependence and correction conventions.

### Primary inference: HAC lag 5

{markdown(results.loc[results.lag.eq(5), columns])}

### Sensitivity: HAC lags 10 and 20

{markdown(results.loc[results.lag.ne(5), columns])}

### Exploratory threshold sensitivity, not revised research conclusions

The following tracks the nominal unadjusted 0.05 threshold only; it does not
establish a window ranking or confirmatory evidence. A CI including zero does
not demonstrate equivalence or absence of an effect.

{chr(10).join(comparisons)}

{stability_note}

### Limitations and confirmatory boundary

These are **exploratory p-values** from an already investigated sample, not
confirmatory evidence. Six hypotheses at three lag choices produce 18 correlated
reported tests, in addition to prior window, yearly and regime explorations.
P-values are unadjusted; intervals do not control familywise coverage. Fixed
bandwidths do not remove multiple-testing or researcher-selection concerns, and
lag sensitivity must not be used to pick a favorable p-value. No winning window
is selected and prior findings/conclusions are preserved.

Newey–West accounts for heteroskedasticity and weighted serial covariance through
the selected lag. It does not guarantee correct coverage under longer dependence,
structural breaks or nonstationarity. Overlapping 5-day labels and momentum
lookbacks can induce dependence beyond lag 5, motivating the specified sensitivity
checks without optimizing them. Changes in the valid ticker set, missing-history
selection, current-universe survivorship bias and vendor revisions remain. HAC
does not correct any of those biases. Confirmatory claims would require a separate
pre-specified hypothesis family, multiplicity handling and validation protocol;
validation and held-out test periods are unchanged and untouched here.

Artifacts under `data/research/momentum_001/hac_2010_2016/`: `hac_results.csv`,
`p_value_sensitivity.csv`, `statsmodels_verification.csv`, `methodology.json`,
and `section.md`. Reproduce offline with `python -B scripts/momentum_hac_001.py`.
`--append-report` appends once without replacing any earlier report text.
'''
    (OUT / 'section.md').write_text(section, encoding='utf-8')
    if append_report:
        REPORT.write_bytes(prior + b'\n\n' + section.encode('utf-8'))
        assert REPORT.read_bytes().startswith(prior)
    print(results[columns].to_string(index=False))
    print(json.dumps(metadata, indent=2))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--append-report', action='store_true')
    run(append_report=parser.parse_args().append_report)
