import numpy as np
import pandas as pd
import pytest
from scripts import momentum_risk_001C as study

def fixture():
    rng=np.random.default_rng(123)
    p=pd.DataFrame(100*np.exp(rng.normal(0,.02,(180,110)).cumsum(axis=0)),index=pd.bdate_range('2016-09-01',periods=180),columns=[f'A{i}' for i in range(110)])
    s=pd.Series(['a','b']*55,index=p.columns)
    return p,s

def test_signal_features_no_future_leakage_and_volatility_definition():
    p,s=fixture(); date=p.index[95]
    result=study.features(p,s,'2017-01-01','2017-04-30')
    changed=p.copy(); changed.loc[changed.index>date]*=3
    other=study.features(changed,s,'2017-01-01','2017-04-30')
    for name in result[1]:
        pd.testing.assert_frame_equal(result[1][name].loc[:date],other[1][name].loc[:date])
    for w in (20,60):
        expected=p.pct_change(fill_method=None).loc[:date].tail(w).std(ddof=1)
        pd.testing.assert_series_equal(result[3][f'vol{w}'].loc[date],expected,check_names=False)
    assert result[2].tail(6).isna().all().all()
    assert result[0].index.max()<=pd.Timestamp('2017-04-30')

def test_regression_recovers_known_controls_and_residual_orthogonality():
    rng=np.random.default_rng(20); n=200
    f=pd.DataFrame(dict(momentum=rng.normal(size=n),vol20=rng.uniform(.01,.1,n),vol60=rng.uniform(.01,.1,n),sector=['a','b']*100))
    f['target']=-.3*f.momentum+2*f.vol20-3*f.vol60+f.sector.map({'a':.4,'b':-.2})
    fit=study.regression(f,['vol20','vol60'])
    assert fit['coefficient']==pytest.approx(-.3)
    residual=study.residualize(f,['vol20','vol60'])
    assert np.max(np.abs(study.design(f,['vol20','vol60']).T@residual))<1e-10
    altered=f.copy(); altered.target=np.nan
    pd.testing.assert_series_equal(residual,study.residualize(altered,['vol20','vol60']))
    shuffled=f.sample(frac=1,random_state=5)
    assert study.regression(shuffled,['vol20','vol60'])['coefficient']==pytest.approx(-.3)

def test_missing_data_and_rank_deficiency_are_explicit():
    rng=np.random.default_rng(3)
    f=pd.DataFrame(dict(momentum=rng.normal(size=110),vol20=rng.normal(size=110),target=rng.normal(size=110),sector=['a']*110))
    f.loc[:10,'vol20']=np.nan
    assert study.regression(f,['vol20'])['count']==99
    assert np.isnan(study.regression(f,['vol20'])['coefficient'])
    assert study.residualize(f,['vol20']).isna().all()
    f.vol20=1
    assert study.regression(f,['vol20'])['reason']=='rank_deficient_or_no_residual_df'

def test_missing_returns_not_filled():
    p,s=fixture(); p.iloc[80,0]=np.nan
    result=study.features(p,s,'2017-01-01','2017-04-30')
    assert np.isnan(result[3]['vol60'].loc[p.index[100],p.columns[0]])
    assert pd.notna(result[3]['vol60'].loc[p.index[145],p.columns[0]])

def test_heldout_rejected_and_sectors_label_aligned():
    p,s=fixture()
    a=study.features(p,s,'2017-01-01','2017-04-30')
    b=study.features(p,s.iloc[::-1],'2017-01-01','2017-04-30')
    pd.testing.assert_frame_equal(a[1]['sector_both'],b[1]['sector_both'])
    p.index=pd.bdate_range('2020-01-01',periods=len(p))
    with pytest.raises(ValueError,match='Held-out'): study.features(p,s,'2017-01-01','2019-12-31')
