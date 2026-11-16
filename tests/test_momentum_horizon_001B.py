"""Synthetic #001-B timing/alignment tests; no market files or networks."""
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import momentum_horizon_001B as study


def synthetic(n=240, assets=110, start='2016-09-01'):
    rng = np.random.default_rng(601020)
    return pd.DataFrame(100*np.exp(rng.normal(0,.02,(n,assets)).cumsum(axis=0)),
                        index=pd.bdate_range(start, periods=n), columns=[f'S{i}' for i in range(assets)])


def test_all_lookbacks_horizons_and_subperiod_boundaries():
    p = synthetic()
    original = p.copy()
    prices, factors, labels, warmup = study.period_inputs(p,'2017-01-01','2017-06-30')
    assert warmup == 60
    first = p.index.get_loc(prices.index[0])
    for l in study.LOOKBACKS:
        pd.testing.assert_series_equal(factors[l].iloc[0],p.iloc[first]/p.iloc[first-l]-1,check_names=False)
        for h in study.HORIZONS:
            pd.testing.assert_series_equal(labels[h].iloc[0],prices.iloc[1+h]/prices.iloc[1]-1,check_names=False)
            assert labels[h].iloc[-(h+1):].isna().all().all()
            assert labels[h].iloc[-(h+2)].notna().all()
    # Future rows of the input cannot influence bounded labels.
    changed = p.copy()
    changed.loc[changed.index > '2017-06-30'] *= 9
    _, f2, r2, _ = study.period_inputs(changed,'2017-01-01','2017-06-30')
    for l in factors: pd.testing.assert_frame_equal(factors[l],f2[l])
    for h in labels: pd.testing.assert_frame_equal(labels[h],r2[h])
    pd.testing.assert_frame_equal(p, original)


def test_rerank_after_common_ticker_and_date_intersection():
    dates = pd.bdate_range('2011-01-03', periods=4)
    # Exclude middle ranks: pre-ranking then correlating gives a different answer.
    f = pd.DataFrame([[1,3,2,8,4,9]]*4,index=dates,columns=list('abcdef'),dtype=float)
    r = pd.DataFrame([[3,1,7,2,9,4]]*4,index=dates,columns=list('abcdef'),dtype=float)
    f2=f.copy()
    f2.loc[:,['b','e']]=np.nan
    r2=r.copy()
    r2.iloc[2]=1  # Adequate pairs but zero variance; all common ICs lose date.
    indiv, strict, masks, intersection, retained=study.compare(
        {5:f,20:f2.iloc[1:][list('fedcba')]}, {5:r,10:r2},min_assets=3)
    assert strict.index.equals(dates[1:])
    valid=['a','c','d','f']
    expected=f.loc[dates[1],valid].rank().corr(r.loc[dates[1],valid].rank())
    assert strict.loc[dates[1],'L5_H5']==pytest.approx(expected)
    preranked=f.loc[dates[1]].rank()[valid].corr(r.loc[dates[1]].rank()[valid])
    assert not np.isclose(expected,preranked)
    assert strict.loc[dates[2]].isna().all()
    assert not retained.loc[dates[2]].any()
    assert intersection.loc[dates[2]].sum()==4
    assert indiv.loc[dates[2],'L5_H5']==pytest.approx(f.iloc[2].rank().corr(r.iloc[2].rank()))
    assert strict.notna().nunique(axis=1).eq(1).all()


def test_missing_endpoints_never_filled_and_minimum_100():
    p=synthetic(n=220,start='2010-01-01')
    p.iloc[80,:11]=np.nan
    _,f,r,warmup=study.period_inputs(p,'2010-01-01','2010-12-31')
    assert warmup==0
    assert f[5].iloc[80,:11].isna().all()
    assert f[5].iloc[85,:11].isna().all()
    assert r[5].iloc[74,:11].isna().all()  # Exit at 80.
    assert r[5].iloc[79,:11].isna().all()  # Entry at 80.
    assert r[5].iloc[77,:11].notna().all()  # Missing intermediate row allowed.
    individual,common,masks,_,retained=study.compare(f,r)
    assert masks[5,5].iloc[80].sum()==99
    assert np.isnan(individual.L5_H5.iloc[80])
    assert not retained.iloc[80].any()
    for l in study.LOOKBACKS:
        assert f[l].iloc[:l].isna().all().all()


def test_reader_stops_before_held_out_payload_and_preserves_universe(monkeypatch):
    text='Date,B,A\n2019-12-30,2,1\n2019-12-31,,3\n2020-01-02,FORBIDDEN,FORBIDDEN\n'
    limit=text.index('FORBIDDEN')
    class Guard(io.StringIO):
        def read(self,n=-1):
            assert n>=0 and self.tell()+n<=limit
            return super().read(n)
        def readline(self,*args):
            assert self.tell()<limit
            return super().readline(*args)
    monkeypatch.setattr(Path,'open',lambda *args,**kwargs:Guard(text))
    p=study.load_prices('synthetic.csv',['A','B'])
    assert p.columns.tolist()==['A','B']
    assert len(p)==2 and p.index.max()==pd.Timestamp('2019-12-31')
    assert p.iloc[1].A==3 and np.isnan(p.iloc[1].B)


@pytest.mark.parametrize('rows',[
    '2019-12-30,1,2\n2019-12-30,3,4\n',
    '2019-12-31,1,2\n2019-12-30,3,4\n',
    '2019-12-30,0,2\n', '2019-12-30,inf,2\n',
    '2019-12-30,bad,2\n', '2019-12-30,1\n'])
def test_reader_rejects_invalid_frozen_prices(tmp_path, rows):
    path=tmp_path/'synthetic.csv'
    path.write_text('Date,A,B\n'+rows)
    with pytest.raises(ValueError): study.load_prices(path,['A','B'])


def test_no_held_out_input_accepted_before_factor_calculation(monkeypatch):
    def forbidden(*args,**kwargs):
        pytest.fail('Factor calculation must not occur on held-out inputs')
    monkeypatch.setattr(study,'calculate_momentum',forbidden)
    with pytest.raises(ValueError,match='Held-out'):
        study.period_inputs(synthetic(n=10,start='2019-12-30'),'2010-01-01','2019-12-31')


def test_coverage_and_equal_common_dates():
    p=synthetic(n=140,start='2010-01-01')
    result=study.analyze_period(p,'2010-01-01','2010-12-31')
    s=result['summary']
    assert len(s)==24
    common=s.query('sample == "common"')
    assert common['count'].eq(140-60-61).all()
    assert common.min_pairs_on_retained_dates.eq(110).all()
    for row in s.query('sample == "individual"').itertuples():
        assert row.count==140-row.lookback-row.horizon-1
        assert row.boundary_excluded_dates==row.horizon+1
        assert row.insufficient_lookback_rows==row.lookback
    assert result['common_retained_mask'].sum(axis=1).gt(0).sum()==19
    assert result['price_coverage'].missing_prices.eq(0).all()
