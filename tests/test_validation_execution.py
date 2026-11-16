import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm
from statsmodels.regression.linear_model import OLS

from scripts import execute_momentum_001_validation as driver


@pytest.fixture
def protocol():
    return json.loads(driver.PROTOCOL.read_text(encoding='utf-8'))


def panel():
    rng = np.random.default_rng(37)
    return pd.DataFrame(100*np.exp(np.cumsum(rng.normal(0, .02, (60, 110)),axis=0)),
                        index=pd.bdate_range('2016-12-26', periods=60),
                        columns=[f'A{i}' for i in range(110)])


def test_warmup_boundaries_rank_alignment_and_nonmutation(protocol):
    prices = panel()
    original = prices.copy(deep=True)
    primary, secondary, tables = driver.evaluate(prices, protocol)
    audit = tables['daily_ic_audit']
    assert len(audit) == 55
    assert audit.iloc[-6:].rank_ic.isna().all()
    assert audit.iloc[-6:].exclusion_reason.eq('forward_endpoint_outside_validation').all()
    factor = prices.iloc[5]/prices.iloc[0]-1
    target = prices.iloc[11]/prices.iloc[6]-1
    expected = factor.rank().corr(target.rank())
    assert audit.rank_ic.iloc[0] == pytest.approx(expected)
    assert audit.entry_date.iloc[0] == prices.index[6]
    assert audit.exit_date.iloc[0] == prices.index[11]
    _, _, reordered = driver.evaluate(prices[prices.columns[::-1]], protocol)
    pd.testing.assert_series_equal(audit.rank_ic,reordered['daily_ic_audit'].rank_ic)
    pd.testing.assert_frame_equal(prices,original)
    assert primary['valid_ic_observations']==49
    assert secondary['valid_dates']==49


def test_bounded_loader_keeps_last_five_rows_and_never_parses_held_out_prices(tmp_path,protocol):
    prices = panel()
    old = prices.iloc[:3].copy()
    old.index = pd.bdate_range('2016-11-01',periods=3)
    path = tmp_path/'prices.csv'
    pd.concat([old,prices]).to_csv(path)
    with path.open('a') as stream:
        stream.write('2020-01-02,'+','.join(['DO_NOT_PARSE']*110)+'\n')
    result=driver.load_bounded_prices(path,prices.columns.tolist()[::-1],protocol)
    pd.testing.assert_frame_equal(result,prices[prices.columns[::-1]],check_names=False,check_freq=False)


def test_interior_missing_ic_stops_without_secondary(protocol):
    prices=panel()
    prices.iloc[20,:11]=np.nan
    primary,secondary,tables=driver.evaluate(prices,protocol)
    assert primary['decision']=='Inconclusive'
    assert 'Interior' in primary['reason']
    assert secondary is None
    assert tables['daily_ic_audit'].missing_factor_assets.max()==11


def test_leading_missing_trim_and_secondary_own_sample(protocol):
    prices=panel()
    prices.iloc[0,:11]=np.nan  # First validation factor has only 99 paired assets.
    primary,secondary,tables=driver.evaluate(prices,protocol)
    assert primary['decision']!='Inconclusive'
    assert primary['leading_trim']==1
    assert secondary['valid_dates']==primary['valid_ic_observations']+1
    first=tables['daily_quantiles'].iloc[:5]
    assert first['count'].sum()==99


def test_missing_future_labels_do_not_change_prior_membership(protocol):
    prices=panel()
    _,_,before=driver.evaluate(prices,protocol)
    prices.iloc[25,0]=np.nan
    _,_,after=driver.evaluate(prices,protocol)
    pd.testing.assert_frame_equal(before['quantile_membership'].loc[:prices.index[24]],
                                  after['quantile_membership'].loc[:prices.index[24]])
    assert after['daily_ic_audit'].loc[prices.index[19],'missing_return_assets']==1


def test_lower_tail_matches_reference_including_positive_sign(protocol):
    rng=np.random.default_rng(41)
    values=pd.Series(rng.normal(-.04,.02,100),index=pd.bdate_range('2018-01-01',periods=100))
    for s in [values,-values]:
        got=driver.assess_ic(s,protocol)
        ref=OLS(s.to_numpy(),np.ones((len(s),1))).fit().get_robustcov_results(
            cov_type='HAC',maxlags=5,kernel='bartlett',use_correction=True,use_t=False)
        assert got['one_sided_p']==pytest.approx(norm.cdf(ref.tvalues[0]))
        assert got['one_sided_upper_95']==pytest.approx(ref.params[0]+norm.ppf(.95)*ref.bse[0])
    assert driver.assess_ic(values,protocol)['decision']=='Pass'
    positive=driver.assess_ic(-values,protocol)
    assert positive['one_sided_p']>.5 and positive['decision']=='Not Supported'


@pytest.mark.parametrize('mean,se,p,n,expected',[
    (-.01,.002,.049,100,'Pass'),(-.01,.002,.05,100,'Not Supported'),
    (-.01,.002,.051,100,'Not Supported'),(.01,.002,.01,100,'Not Supported'),
    (-.01,0,.01,100,'Inconclusive'),(-.01,.002,np.nan,100,'Inconclusive'),
    (-.01,.002,.01,5,'Inconclusive')])
def test_decision_rules(mean,se,p,n,expected):
    assert driver.decision(mean,se,p,n)==expected


def test_undefined_and_constant_ic_are_inconclusive(protocol):
    dates=pd.bdate_range('2017-01-01',periods=20)
    for values in ([np.nan]*20,[.1]*20,[.1,.2,.3,.2,.1]+[np.nan]*15):
        assert driver.assess_ic(pd.Series(values,index=dates),protocol)['decision']=='Inconclusive'


def test_invalid_prices_or_wrong_warmup_rejected(protocol):
    prices=panel()
    with pytest.raises(ValueError): driver.evaluate(prices.iloc[1:],protocol)
    prices.iloc[7,0]=0
    with pytest.raises(ValueError): driver.evaluate(prices,protocol)


def test_repeated_execution_stops_before_any_verification_or_prices(tmp_path,monkeypatch):
    monkeypatch.setattr(driver,'OUT',tmp_path)
    (tmp_path/'started.json').write_text('{}')
    monkeypatch.setattr(driver,'verify',lambda: pytest.fail('Must not reach verification'))
    with pytest.raises(ValueError,match='reruns forbidden'): driver.execute()


def test_failed_verification_stops_before_marker_or_price_read(tmp_path,monkeypatch):
    monkeypatch.setattr(driver,'OUT',tmp_path)
    def failed(): raise ValueError('Seal mismatch')
    monkeypatch.setattr(driver,'verify',failed)
    monkeypatch.setattr(driver,'load_bounded_prices',lambda *a: pytest.fail('Price access forbidden'))
    with pytest.raises(ValueError,match='Seal mismatch'): driver.execute()
    assert not (tmp_path/'started.json').exists()
