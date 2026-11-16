import numpy as np
import pandas as pd
import pytest
from statsmodels.regression.linear_model import OLS

from src.evaluation import hac_mean
from scripts.momentum_hac_001 import complete_common_sample, infer


def series():
    rng = np.random.default_rng(17)
    innovations = rng.normal(size=400) * np.linspace(.02, .1, 400)
    values = np.zeros(400)
    for t in range(1, len(values)):
        values[t] = .7 * values[t-1] + innovations[t]
    return pd.Series(values + .01, index=pd.bdate_range('2012-01-01', periods=400))


@pytest.mark.parametrize('lag', [0, 5, 10, 20])
@pytest.mark.parametrize('correct', [False, True])
def test_matches_statsmodels_autocorrelated_heteroskedastic(lag, correct):
    s = series()
    before = s.copy()
    got = hac_mean(s, lag, use_correction=correct)
    ref = OLS(s.to_numpy(), np.ones((len(s), 1))).fit().get_robustcov_results(
        cov_type='HAC', maxlags=lag, kernel='bartlett', use_correction=correct, use_t=False)
    np.testing.assert_allclose(
        got[['mean', 'hac_variance', 'hac_se', 't_stat', 'p_value', 'ci_low', 'ci_high']],
        [ref.params[0], ref.cov_params()[0, 0], ref.bse[0], ref.tvalues[0], ref.pvalues[0],
         *ref.conf_int()[0]], rtol=1e-10, atol=1e-12)
    pd.testing.assert_series_equal(s, before)


def test_manual_bartlett_covariance_and_correction():
    s = pd.Series([1., 2., 4., 3., -1.], index=pd.date_range('2010', periods=5))
    u = s.to_numpy() - s.mean()
    manual = (sum(u*u) + 2 * (2/3) * sum(u[1:]*u[:-1]) + 2 * (1/3) * sum(u[2:]*u[:-2])) / 25
    assert hac_mean(s, 2, use_correction=False).hac_variance == pytest.approx(manual)
    assert hac_mean(s, 2).hac_variance == pytest.approx(manual * 5/4)
    assert hac_mean(s, 0).hac_se == pytest.approx(s.std(ddof=1)/np.sqrt(5))


def test_paired_inference_uses_difference_covariance():
    a = series()
    rng = np.random.default_rng(12)
    b = a + rng.normal(0, .003, len(a)) + .002
    frame = pd.DataFrame({'5D': a, '20D': b, '60D': a * .7})
    _, results, checks = infer(frame)
    paired = results.loc[(results.series == '5D minus 20D') & (results.lag == 5)].iloc[0]
    direct = hac_mean(a-b, lag=5)
    assert paired.hac_se == pytest.approx(direct.hac_se)
    assert paired['mean'] == pytest.approx(a.mean()-b.mean())
    assert paired.hac_se < np.hypot(hac_mean(a).hac_se, hac_mean(b).hac_se) / 5
    assert len(results) == 18 and len(checks) == 126
    opposite = hac_mean(b-a)
    assert opposite.p_value == pytest.approx(direct.p_value)
    assert opposite.ci_low == pytest.approx(-direct.ci_high)


@pytest.mark.parametrize('lag', [-1, 400, 1.5, True])
def test_invalid_lag(lag):
    with pytest.raises(ValueError): hac_mean(series(), lag)


@pytest.mark.parametrize('kind', ['missing', 'inf', 'duplicate', 'unsorted', 'one'])
def test_invalid_input(kind):
    s = series()
    if kind == 'missing': s.iloc[3] = np.nan
    if kind == 'inf': s.iloc[3] = np.inf
    if kind == 'duplicate': s.index = [s.index[0]] * len(s)
    if kind == 'unsorted': s = s.iloc[::-1]
    if kind == 'one': s = s.iloc[:1]
    with pytest.raises(ValueError): hac_mean(s)


def test_constant_series_has_undefined_inference():
    result = hac_mean(series() * 0 + .1)
    assert result.hac_se == 0
    assert result[['t_stat', 'p_value', 'ci_low', 'ci_high']].isna().all()


@pytest.mark.parametrize('kind', ['partial', 'interior', 'held_out'])
def test_common_sample_rejects_misalignment_or_later_data(kind):
    s = series()
    f = pd.DataFrame({'5D': s, '20D': s/2, '60D': -s})
    if kind == 'partial': f.iloc[3, 0] = np.nan
    if kind == 'interior': f.iloc[3] = np.nan
    if kind == 'held_out': f.index = pd.bdate_range('2017-01-01', periods=len(f))
    with pytest.raises(ValueError): complete_common_sample(f)


def test_common_sample_trims_only_joint_boundary_missing_rows():
    s = series()
    f = pd.DataFrame({'5D': s, '20D': s/2, '60D': -s})
    f.iloc[:10] = np.nan
    f.iloc[-6:] = np.nan
    pd.testing.assert_frame_equal(complete_common_sample(f), f.iloc[10:-6])
