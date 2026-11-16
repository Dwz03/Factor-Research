"""Synthetic-only tests for the dedicated final execution adapter and gates."""
import json
import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm
from statsmodels.regression.linear_model import OLS
from scripts import execute_momentum_001_final_test as driver

def prices():
    rng=np.random.default_rng(450)
    return pd.DataFrame(100*np.exp(rng.normal(0,.02,(90,110)).cumsum(axis=0)),index=pd.bdate_range('2019-12-25',periods=90),columns=[f'A{i}' for i in range(110)])

def test_adapter_warmup_rank_alignment_and_missing():
    p=prices(); original=p.copy()
    _,_,tables=driver.evaluate(p)
    audit=tables['daily_ic_audit']
    f=p.iloc[5]/p.iloc[0]-1; y=p.iloc[11]/p.iloc[6]-1
    assert audit.rank_ic.iloc[0]==pytest.approx(f.rank().corr(y.rank()))
    assert audit.entry_date.iloc[0]==p.index[6] and audit.exit_date.iloc[0]==p.index[11]
    _,_,reordered=driver.evaluate(p[p.columns[::-1]])
    pd.testing.assert_series_equal(audit.rank_ic,reordered['daily_ic_audit'].rank_ic)
    pd.testing.assert_frame_equal(p,original)
    with pytest.raises(ValueError): driver.evaluate(p.iloc[1:])
    p.iloc[30,:11]=np.nan
    primary,secondary,_=driver.evaluate(p)
    assert primary['decision']=='Inconclusive' and secondary is None

def test_end_boundary_loader(tmp_path):
    p=prices(); tail=p.iloc[-20:].copy(); tail.index=pd.bdate_range(end='2025-12-31',periods=20)
    path=tmp_path/'synthetic.csv'; pd.concat([p,tail]).to_csv(path)
    with path.open('a') as f:f.write('2026-01-02,'+','.join(['invalid']*110)+'\n')
    bounded=driver.frozen.load_bounded_prices(path,p.columns.tolist(),driver.config())
    assert bounded.index.max()==pd.Timestamp('2025-12-31')
    assert (bounded.index<'2020-01-01').sum()==5
    _,_,tables=driver.evaluate(bounded)
    a=tables['daily_ic_audit']; assert a.rank_ic.tail(6).isna().all()
    assert a.loc[a.rank_ic.notna(),'exit_date'].le('2025-12-31').all()

def test_lower_tail_reference_and_decisions():
    rng=np.random.default_rng(55)
    s=pd.Series(rng.normal(-.04,.02,150),index=pd.bdate_range('2021-01-01',periods=150))
    for values,decision in [(s,'Pass'),(-s,'Not Supported')]:
        result=driver.frozen.assess_ic(values,driver.config())
        ref=OLS(values.to_numpy(),np.ones((len(values),1))).fit().get_robustcov_results(cov_type='HAC',maxlags=5,kernel='bartlett',use_correction=True,use_t=False)
        assert result['decision']==decision
        assert result['hac_se']==pytest.approx(ref.bse[0])
        assert result['one_sided_p']==pytest.approx(norm.cdf(ref.tvalues[0]))
        assert result['one_sided_upper_95']==pytest.approx(ref.params[0]+norm.ppf(.95)*ref.bse[0])
    assert driver.frozen.assess_ic(s*0,driver.config())['decision']=='Inconclusive'
    assert driver.frozen.decision(-.01,.01,.05,100)=='Not Supported'

def test_marker_and_tested_hash_gate(tmp_path,monkeypatch):
    monkeypatch.setattr(driver,'OUT',tmp_path)
    monkeypatch.setattr(driver,'REPORT',tmp_path/'report.md')
    (tmp_path/'started.json').write_text('{}')
    with pytest.raises(ValueError,match='already'): driver.require_unused()

def test_driver_hash_mismatch_stops_before_price_access(tmp_path,monkeypatch):
    monkeypatch.setattr(driver,'OUT',tmp_path)
    monkeypatch.setattr(driver,'REPORT',tmp_path/'report.md')
    monkeypatch.setattr(driver,'verify_history',lambda: {})
    (tmp_path/'preflight').mkdir()
    (tmp_path/'preflight/passed.json').write_text(json.dumps({'driver_sha256':'wrong'}))
    with pytest.raises(ValueError,match='Tested driver'): driver.execution_gate()
    assert not (tmp_path/'started.json').exists()
