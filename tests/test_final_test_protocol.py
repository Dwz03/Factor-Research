"""Final-period contract checks use synthetic data only, never real market rows."""
from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm
from statsmodels.regression.linear_model import OLS

from scripts import execute_momentum_001_validation as engine


@pytest.fixture
def config():
    p = json.loads((engine.ROOT/'config/momentum_001_final_test.json').read_text(encoding='utf-8'))
    adapted = deepcopy(p)
    adapted['periods']['validation'] = deepcopy(p['periods']['final_test'])
    return adapted


def synthetic():
    dates = pd.bdate_range('2019-12-25', periods=65)
    rng = np.random.default_rng(2025)
    return pd.DataFrame(100*np.exp(np.cumsum(rng.normal(0,.02,(65,110)),axis=0)),
                        index=dates,columns=[f'S{i}' for i in range(110)])


def test_five_pre2020_rows_and_first_signal_rank_alignment(config):
    p=synthetic()
    original=p.copy()
    _,_,tables=engine.evaluate(p,config)
    audit=tables['daily_ic_audit']
    factor=p.iloc[5]/p.iloc[0]-1
    target=p.iloc[11]/p.iloc[6]-1
    assert audit.index[0]==p.index[5]
    assert audit.rank_ic.iloc[0]==pytest.approx(factor.rank().corr(target.rank()))
    assert audit.entry_date.iloc[0]==p.index[6]
    assert audit.exit_date.iloc[0]==p.index[11]
    _,_,reordered=engine.evaluate(p[p.columns[::-1]],config)
    pd.testing.assert_series_equal(audit.rank_ic,reordered['daily_ic_audit'].rank_ic)
    pd.testing.assert_frame_equal(p,original)
    with pytest.raises(ValueError): engine.evaluate(p.iloc[1:],config)


def test_loader_stops_at_end2025_and_keeps_only_five_warmup_rows(tmp_path,config):
    p=synthetic()
    older=p.iloc[:3].copy()
    older.index=pd.bdate_range('2019-11-01',periods=3)
    late=p.iloc[-20:].copy()
    late.index=pd.bdate_range(end='2025-12-31',periods=20)
    path=tmp_path/'synthetic.csv'
    pd.concat([older,p,late]).to_csv(path)
    with path.open('a') as stream:
        stream.write('2026-01-02,'+','.join(['DO_NOT_PARSE']*110)+'\n')
    loaded=engine.load_bounded_prices(path,p.columns.tolist(),config)
    assert (loaded.index<pd.Timestamp('2020-01-01')).sum()==5
    assert loaded.index.max()==pd.Timestamp('2025-12-31')
    _,_,tables=engine.evaluate(loaded,config)
    audit=tables['daily_ic_audit']
    assert audit.iloc[-6:].rank_ic.isna().all()
    assert audit.iloc[-6:].exclusion_reason.eq('forward_endpoint_outside_validation').all()
    assert audit.loc[audit.rank_ic.notna(),'exit_date'].le('2025-12-31').all()


def test_missing_data_not_filled_and_interior_gap_inconclusive(config):
    p=synthetic()
    p.iloc[25,:11]=np.nan
    primary,secondary,tables=engine.evaluate(p,config)
    assert primary['decision']=='Inconclusive'
    assert 'Interior' in primary['reason']
    assert secondary is None
    assert tables['daily_ic_audit'].missing_factor_assets.max()==11


def test_final_hac_lower_tail_matches_reference(config):
    rng=np.random.default_rng(29)
    s=pd.Series(rng.normal(-.04,.02,100),index=pd.bdate_range('2022-01-03',periods=100))
    for values in (s,-s):
        result=engine.assess_ic(values,config)
        ref=OLS(values.to_numpy(),np.ones((len(values),1))).fit().get_robustcov_results(
            cov_type='HAC',maxlags=5,kernel='bartlett',use_correction=True,use_t=False)
        assert result['one_sided_p']==pytest.approx(norm.cdf(ref.tvalues[0]))
        assert result['one_sided_upper_95']==pytest.approx(ref.params[0]+norm.ppf(.95)*ref.bse[0])
    assert engine.assess_ic(s,config)['decision']=='Pass'
    assert engine.assess_ic(-s,config)['decision']=='Not Supported'
    assert engine.assess_ic(s*0+.1,config)['decision']=='Inconclusive'


@pytest.mark.parametrize('mean,se,p,n,expected',[
    (-.01,.01,.049,100,'Pass'),(-.01,.01,.05,100,'Not Supported'),
    (-.01,.01,.051,100,'Not Supported'),(.01,.01,.01,100,'Not Supported'),
    (-.01,0,.01,100,'Inconclusive'),(-.01,.01,np.nan,100,'Inconclusive'),
    (-.01,.01,.01,5,'Inconclusive')])
def test_final_decision_rules(mean,se,p,n,expected):
    assert engine.decision(mean,se,p,n)==expected


def test_conventions_match_original_validation_except_period_metadata():
    original=json.loads(engine.PROTOCOL.read_text(encoding='utf-8'))
    final=json.loads((engine.ROOT/'config/momentum_001_final_test.json').read_text(encoding='utf-8'))
    for key in ('factor','universe','primary','secondary','missing_data','environment'):
        assert final[key]==original[key]
    assert final['timing']['horizon_rows']==5 and final['timing']['entry_lag_rows']==1
    assert final['periods']['final_test']=={'start':'2020-01-01','end_inclusive':'2025-12-31'}
    assert final['execution']['authorized_now'] is False
