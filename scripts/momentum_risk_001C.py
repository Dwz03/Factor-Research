"""Isolated, fixed-spec post-validation risk exposure study. Offline and bounded."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import momentum_horizon_001B as base
from scripts import momentum_incremental_001B as inc
from src.evaluation import rank_ic, ic_summary
from scripts.verify_momentum_001_validation import digest
OUT=ROOT/'data/research/momentum_001C'
REPORT=ROOT/'reports/01C_momentum_risk.md'
MODELS={'sector':[], 'sector_vol20':['vol20'], 'sector_vol60':['vol60'], 'sector_both':['vol20','vol60']}

def integrity():
    result=inc.integrity()
    manifest=json.loads((inc.OUT/'manifest.json').read_text())
    for path,sha in manifest['sha256'].items():
        if digest(ROOT/path)!=sha: raise ValueError('Incremental artifact changed: '+path)
    return result

def design(frame, controls):
    """All observed-sector dummies, no redundant intercept; raw volatility units."""
    sectors=pd.get_dummies(frame.sector,dtype=float)
    return pd.concat([sectors,frame[controls]],axis=1).to_numpy(float)

def residualize(frame, controls, minimum=100):
    """Signal-only OLS residuals; future returns are not an input."""
    selected=frame[['momentum','sector']+controls].dropna()
    result=pd.Series(np.nan,index=frame.index,dtype=float)
    if len(selected)<minimum: return result
    x=design(selected,controls)
    if np.linalg.matrix_rank(x)<x.shape[1] or len(selected)<=x.shape[1]: return result
    y=selected.momentum.to_numpy()
    result.loc[selected.index]=y-x@np.linalg.lstsq(x,y,rcond=None)[0]
    return result

def regression(frame, controls, minimum=100):
    """Unweighted cross-sectional OLS; coefficient in raw decimal return units."""
    selected=frame[['momentum','sector','target']+controls].dropna()
    result=dict(count=len(selected),coefficient=np.nan,reason='fewer_than_100_pairs')
    if len(selected)<minimum: return result
    x=np.column_stack([design(selected,controls),selected.momentum.to_numpy()])
    if np.linalg.matrix_rank(x)<x.shape[1] or len(selected)<=x.shape[1]:
        result['reason']='rank_deficient_or_no_residual_df'; return result
    result.update(coefficient=float(np.linalg.lstsq(x,selected.target.to_numpy(),rcond=None)[0][-1]),reason='')
    return result

def features(panel,sectors,start,end):
    prices,f,labels,warmup=base.period_inputs(panel,start,end)
    history=pd.concat([panel.loc[panel.index<pd.Timestamp(start)].tail(60),prices])
    returns=history.pct_change(fill_method=None)
    vol={f'vol{w}':returns.rolling(w,min_periods=w).std(ddof=1).reindex(prices.index) for w in (20,60)}
    sectors=sectors.reindex(prices.columns)
    if sectors.isna().any(): raise ValueError('Missing frozen sector metadata')
    adjusted={name:pd.DataFrame(np.nan,index=prices.index,columns=prices.columns) for name in MODELS}
    frames={}
    for date in prices.index:
        frame=pd.DataFrame({'momentum':f[5].loc[date],'sector':sectors,**{k:v.loc[date] for k,v in vol.items()}})
        for model,controls in MODELS.items(): adjusted[model].loc[date]=residualize(frame,controls)
        frames[date]=frame
    return prices,{'raw':f[5],**adjusted},labels[5],vol,frames,warmup

def describe(series):
    v=series.dropna(); sd=v.std(ddof=1)
    return dict(count=len(v),mean=v.mean(),std=sd,positive_fraction=v.gt(0).mean() if len(v) else np.nan)

def analyze(panel,sectors,start,end):
    prices,f,y,vol,frames,warmup=features(panel,sectors,start,end)
    common=y.notna()
    for values in f.values(): common &= values.notna()
    daily={}; pairs={}
    for name,values in f.items():
        daily['available/'+name]=rank_ic(values,y,min_assets=100)
        pairs['available/'+name]=(values.notna()&y.notna()).sum(axis=1)
        daily['common/'+name]=rank_ic(values.where(common),y.where(common),min_assets=100)
        pairs['common/'+name]=common.sum(axis=1)
    ic=pd.DataFrame(daily); counts=pd.DataFrame(pairs)
    commoncols=[c for c in ic if c.startswith('common/')]
    ic.loc[ic[commoncols].isna().any(axis=1),commoncols]=np.nan
    regressions=[]; exposure=[]
    for date,frame in frames.items():
        frame=frame.assign(target=y.loc[date])
        for model,controls in MODELS.items():
            regressions.append(dict(Date=date,model=model,**regression(frame,controls)))
        for name,values in vol.items():
            observed=values.loc[date].dropna()
            exposure.append(dict(Date=date,volatility=name,count=len(observed),mean=observed.mean(),median=observed.median(),std=observed.std(ddof=1)))
    for name,values in vol.items():
        # Membership is fixed from observed volatility before future-return deletion.
        median=values.median(axis=1)
        for group,mask in [('low',values.le(median,axis=0)),('high',values.gt(median,axis=0))]:
            key=f'{name}/{group}'
            ic[key]=rank_ic(f['raw'].where(mask),y,min_assets=100)
            counts[key]=(mask&f['raw'].notna()&y.notna()).sum(axis=1)
        ic['exposure/'+name]=rank_ic(f['raw'],values,min_assets=100)
        counts['exposure/'+name]=(f['raw'].notna()&values.notna()).sum(axis=1)
    audit=pd.DataFrame({'entry_date':prices.index.to_series().shift(-1),'exit_date':prices.index.to_series().shift(-6),
                        'missing_prices':prices.isna().sum(axis=1),'missing_momentum':f['raw'].isna().sum(axis=1),
                        'missing_vol20':vol['vol20'].isna().sum(axis=1),'missing_vol60':vol['vol60'].isna().sum(axis=1),
                        'missing_target':y.isna().sum(axis=1)})
    summary=[]; annual=[]
    for key in ic:
        summary.append(dict(series=key,**ic_summary(ic[key]).to_dict(),mean_pairs=counts.loc[ic[key].notna(),key].mean(),min_pairs=counts.loc[ic[key].notna(),key].min()))
        for year,s in ic[key].groupby(ic.index.year):
            annual.append(dict(series=key,year=year,**ic_summary(s).to_dict(),mean_pairs=counts.loc[s.dropna().index,key].mean()))
    reg=pd.DataFrame(regressions)
    rs=[]; ra=[]
    for model,frame in reg.groupby('model'):
        rs.append(dict(model=model,**describe(frame.coefficient),mean_pairs=frame.loc[frame.coefficient.notna(),'count'].mean()))
        for year,g in frame.groupby(frame.Date.dt.year): ra.append(dict(model=model,year=year,**describe(g.coefficient)))
    return dict(ic=ic,pair_counts=counts,summary=pd.DataFrame(summary),annual=pd.DataFrame(annual),regressions=reg,
                regression_summary=pd.DataFrame(rs),regression_annual=pd.DataFrame(ra),volatility_characteristics=pd.DataFrame(exposure),audit=audit,
                common_pairs=common,price_coverage=pd.DataFrame({'observed':prices.count(),'missing':prices.isna().sum(),'coverage':prices.notna().mean()}))

def run():
    before=integrity()
    if OUT.exists() or REPORT.exists(): raise FileExistsError('Preserve existing study')
    p=json.loads((ROOT/'config/momentum_001_final_test.json').read_text())
    universe=pd.read_csv(ROOT/p['universe']['path'])
    panel=base.load_prices(ROOT/p['data']['path'],universe.ticker.tolist())
    sectors=universe.set_index('ticker').sector
    OUT.mkdir(parents=True)
    all_tables={}
    for period,(start,end) in base.PERIODS.items():
        print(period,flush=True)
        tables=analyze(panel,sectors,start,end); folder=OUT/period; folder.mkdir()
        for name,table in tables.items():
            indexed=name in ['ic','pair_counts','audit','common_pairs','price_coverage']
            table.to_csv(folder/(name+'.csv.gz' if name=='common_pairs' else name+'.csv'),index=indexed)
            all_tables.setdefault(name,[]).append(table.assign(period=period))
        prior=pd.read_csv(base.OUT/period/'individual.csv',index_col=0,parse_dates=True).L5_H5
        np.testing.assert_allclose(tables['ic']['available/raw'],prior,equal_nan=True,atol=1e-12)
    merged={k:pd.concat(v) for k,v in all_tables.items()}
    for name in ['summary','annual','regression_summary','regression_annual','volatility_characteristics']:
        merged[name].to_csv(OUT/(name+'.csv'),index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(14,4),constrained_layout=True)
    for ax,period in zip(axes,base.PERIODS):
        x=merged['summary'].query('period==@period and series.str.startswith("common/")',engine='python')
        ax.bar(x.series.str.replace('common/',''),x['mean']); ax.axhline(0,color='gray'); ax.tick_params(axis='x',rotation=40)
        ax.set(title=period,ylabel='Mean daily Rank IC (common sample)')
    fig.savefig(OUT/'adjusted_ic.png',dpi=160); plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(14,4),constrained_layout=True)
    for ax,period in zip(axes,base.PERIODS):
        for model in MODELS:
            x=merged['regression_annual'].query('period==@period and model==@model')
            ax.plot(x.year,x['mean'],marker='o',label=model)
        ax.axhline(0,color='gray'); ax.set(title=period,ylabel='Mean raw-unit Momentum coefficient'); ax.legend(fontsize=7)
    fig.savefig(OUT/'annual_coefficients.png',dpi=160); plt.close(fig)
    sections=['# Momentum Research #001-C: Risk Exposure and Incremental Predictive Power',
    'Isolated post-validation descriptive exploration. 2017?2019 is already-seen data. No 2020?2025 outcomes accessed; #001-A final test remains unexecuted.',
    '## Fixed methodology',
    'Frozen 300-security universe and current frozen sector labels. Existing Momentum P[t]/P[t-5]-1; target P[t+6]/P[t+1]-1. Each period independently bounds labels; last six signal rows excluded. Up to 60 pre-period price rows warm factors and controls only. No pre-2010 history exists in this snapshot. No forward filling. Realized volatility is the unannualized sample standard deviation (ddof=1) of trailing 20 or 60 daily simple returns ending on signal date, requiring all returns. A missing price invalidates adjacent daily returns. No present-day market-cap control.',
    'Daily unweighted OLS neutralizes Momentum on sector dummies alone, sector plus vol20, sector plus vol60, and sector plus both. All observed sector dummies are included without a redundant intercept. Models fit separately each signal date on feature-complete assets BEFORE any future-label filtering, minimum 100. Rank-deficient designs are undefined, not silently regularized. Residual Momentum is then evaluated against raw future returns with Spearman average ranks. Available samples and a strict all-feature common-pair/common-date comparison are reported; common ranks are recomputed. Transformations are not refitted using future-return availability.',
    'Cross-sectional regressions separately fit raw decimal future returns on raw decimal Momentum plus the same controls on outcome-complete samples (minimum 100). Coefficients therefore measure conditional linear slopes, not Spearman IC or causal effects. One unit of Momentum means a 100-percentage-point change; no cross-sectional standardization or winsorization is applied. Coefficient means equally weight eligible dates. Sector-only is a reference; volatility-controlled specifications are fixed, not selected on performance.',
    'Low volatility is at/below the signal-date median; high is above. Membership is determined before observing labels, separately for vol20 and vol60. Each group needs at least 100 observed Momentum/return pairs; fewer pairs or constant ranks give undefined IC. Correlation between Momentum and volatility is a same-date exposure statistic, not a prediction result. Annual means group signal dates within bounded named periods; annual rows are not additional boundary cutoffs.',
    '## IC and exposure summaries',base.markdown(merged['summary']),
    '![Adjusted IC](../data/research/momentum_001C/adjusted_ic.png)',
    '## Conditional Momentum regression coefficients',base.markdown(merged['regression_summary']),
    '## Annual regression stability',base.markdown(merged['regression_annual']),
    '![Annual coefficients](../data/research/momentum_001C/annual_coefficients.png)',
    '## Annual IC and group comparisons',base.markdown(merged['annual']),
    '## Coverage and limitations',
    'Per-date pair counts, feature/target missing counts, boundary endpoints, regression eligibility reasons, common pair masks and per-security price coverage are saved under data/research/momentum_001C. Observations overlap across signal dates and share securities; serial dependence makes iid inference inappropriate. No p-values, HAC lag borrowing, significance claims, causal claims, winning model, optimization or portfolio backtests are produced. Multiple models, controls, groups, years and periods create multiple comparisons. The universe is selected from current constituents, with survivorship/selection bias; frozen sector labels are present-day classifications, not historical point-in-time sectors. Missing data and complete-window requirements select different samples. Conditioning on volatility and sectors does not remove every risk exposure or establish incremental tradable Alpha.',
    '## Reproduction',
    'Run scripts/momentum_risk_001C.py only into new output paths; it refuses existing study artifacts. Original #001-A/#001-B/incremental manifests are verified before and after. Baseline IC is reconciled to saved #001-B values. This study has separate hashes; original implementations and integrity manifests are never modified.']
    REPORT.write_text('\n\n'.join(sections)+'\n',encoding='utf-8')
    after=integrity()
    paths=[x for x in OUT.rglob('*') if x.is_file()]+[REPORT,Path(__file__),ROOT/'tests/test_momentum_risk_001C.py',ROOT/'research/01C_momentum_risk.ipynb']
    manifest=dict(original_integrity_before=before,original_integrity_after=after,data=p['data'],universe=p['universe'],environment=p['environment'],sha256={x.relative_to(ROOT).as_posix():digest(x) for x in paths})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(merged['summary'].to_string(index=False),flush=True)
    print(merged['regression_summary'].to_string(index=False),flush=True)
if __name__=='__main__': run()
