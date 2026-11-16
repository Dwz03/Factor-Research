import numpy as np
import pandas as pd
from scripts import momentum_incremental_001B as study
from scripts import momentum_horizon_001B as base

def test_incremental_endpoints_missing_and_boundaries():
    rng=np.random.default_rng(14)
    p=pd.DataFrame(np.exp(rng.normal(0,.03,(150,110)).cumsum(axis=0)),index=pd.bdate_range('2018-01-01',periods=150))
    original=p.copy()
    r=study.labels(p)
    for h,(lag,width) in study.INTERVALS.items():
        pd.testing.assert_series_equal(r[h].iloc[0],p.iloc[lag+width]/p.iloc[lag]-1,check_names=False)
        assert r[h].iloc[-(h+1):].isna().all().all()
    pd.testing.assert_frame_equal(p,original)
    p.iloc[6,0]=np.nan
    r=study.labels(p)
    assert np.isnan(r[5].iloc[0,0]) and np.isnan(r[10].iloc[0,0])
    assert pd.notna(r[20].iloc[0,0])

def test_common_endpoint_union_and_rank_alignment():
    rng=np.random.default_rng(15)
    p=pd.DataFrame(np.exp(rng.normal(0,.03,(200,110)).cumsum(axis=0)),index=pd.bdate_range('2018-01-01',periods=200))
    p.iloc[90,0]=np.nan
    _,f,c,_=base.period_inputs(p,'2018-01-01','2018-12-31')
    r=study.labels(p)
    _,ic,_,mask,retained=base.compare(f,r)
    _,_,_,cum_mask,_=base.compare(f,c)
    pd.testing.assert_frame_equal(mask,cum_mask)
    date=ic.dropna().index[0]; use=mask.loc[date]
    expected=f[5].loc[date,use].rank().corr(r[10].loc[date,use].rank())
    assert np.isclose(ic.loc[date,'L5_H10'],expected)
    assert ic.notna().nunique(axis=1).eq(1).all()
    assert retained.sum(axis=1).gt(0).equals(ic.notna().all(axis=1))
