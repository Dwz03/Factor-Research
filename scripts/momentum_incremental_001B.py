"""Isolated incremental-return supplement; no held-out outcomes or inference."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import momentum_horizon_001B as base
from src.evaluation import forward_returns, ic_summary
from scripts.verify_momentum_001_validation import digest
INTERVALS={5:(1,5),10:(6,5),20:(11,10),60:(21,40)}
OUT=ROOT/'data/research/momentum_001B_incremental'
REPORT=ROOT/'reports/01B_momentum_incremental.md'
def labels(prices):
    return {h:forward_returns(prices,horizon=width,entry_lag=lag) for h,(lag,width) in INTERVALS.items()}
def integrity():
    result=base.verify()
    m=json.loads((base.OUT/'manifest.json').read_text())
    for group in ('source_sha256','artifact_sha256'):
        for path,sha in m[group].items():
            if digest(ROOT/path)!=sha: raise ValueError('Original #001-B hash mismatch: '+path)
    return result
def run():
    before=integrity()
    if OUT.exists() or REPORT.exists(): raise FileExistsError('Preserve prior supplement outputs')
    protocol=json.loads((ROOT/'config/momentum_001_final_test.json').read_text())
    universe=pd.read_csv(ROOT/protocol['universe']['path'])
    panel=base.load_prices(ROOT/protocol['data']['path'],universe.ticker.tolist())
    OUT.mkdir(parents=True)
    summaries=[]; annual=[]; audits=[]
    for period,(start,end) in base.PERIODS.items():
        print(period,flush=True)
        prices,f,_,warmup=base.period_inputs(panel,start,end)
        r=labels(prices)
        available,common,masks,intersection,retained=base.compare(f,r)
        folder=OUT/period; folder.mkdir()
        available.to_csv(folder/'available_ic.csv'); common.to_csv(folder/'common_ic.csv')
        intersection.to_csv(folder/'intersection.csv.gz'); retained.to_csv(folder/'retained.csv.gz')
        for sample,ic in [('individual',available),('common',common)]:
            for l in base.LOOKBACKS:
                for h in base.HORIZONS:
                    key=f'L{l}_H{h}'; series=ic[key]
                    mask=masks[l,h] if sample=='individual' else intersection
                    counts=mask.sum(axis=1); dates=prices.index.to_series()
                    lag,width=INTERVALS[h]
                    audit=pd.DataFrame(dict(Date=dates,entry=dates.shift(-lag),exit=dates.shift(-(lag+width)),pairs=counts,rank_ic=series))
                    audit=audit.assign(period=period,sample=sample,lookback=l,horizon=h)
                    audits.append(audit)
                    summaries.append(dict(period=period,sample=sample,lookback=l,horizon=h,**ic_summary(series).to_dict(),warmup_rows=warmup,boundary_excluded=min(h+1,len(prices)),mean_pairs=counts[series.notna()].mean(),min_pairs=counts[series.notna()].min()))
                    for year,s in series.groupby(series.index.year):
                        annual.append(dict(period=period,sample=sample,lookback=l,horizon=h,year=year,**ic_summary(s).to_dict(),mean_pairs=counts.loc[s.dropna().index].mean()))
    summary=pd.DataFrame(summaries); yearly=pd.DataFrame(annual)
    summary.to_csv(OUT/'summary.csv',index=False); yearly.to_csv(OUT/'annual.csv',index=False)
    pd.concat(audits).to_csv(OUT/'audit.csv',index=False)
    cumulative=pd.read_csv(base.OUT/'summary.csv')
    comparison=summary.merge(cumulative[['period','sample','lookback','horizon','mean','count']],on=['period','sample','lookback','horizon'],suffixes=('_incremental','_cumulative'))
    comparison.to_csv(OUT/'comparison.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(13,7),constrained_layout=True)
    limit=summary['mean'].abs().max()
    for col,period in enumerate(base.PERIODS):
        for row,sample in enumerate(['individual','common']):
            x=summary.query('period==@period and sample==@sample').pivot(index='lookback',columns='horizon',values='mean')
            ax=axes[row,col]; im=ax.imshow(x,cmap='RdBu_r',vmin=-limit,vmax=limit,aspect='auto')
            ax.set(xticks=range(4),xticklabels=['1?5','6?10','11?20','21?60'],yticks=range(3),yticklabels=base.LOOKBACKS,title=period+' / '+sample,xlabel='Incremental interval',ylabel='Lookback')
            for i in range(3):
                for j in range(4): ax.text(j,i,f'{x.iloc[i,j]:.4f}',ha='center',va='center',fontsize=8)
    fig.colorbar(im,ax=axes,label='Mean Rank IC'); fig.savefig(OUT/'heatmaps.png',dpi=160); plt.close(fig)
    sections=['# Momentum #001-B: Incremental Forward Return Supplement','Post-validation descriptive exploration. 2017?2019 is already-seen data. No final test executed or changed.','## Methodology','Frozen 300 securities; L=5,20,60; minimum 100 pairs. Intervals use endpoint offsets (1,6), (6,11), (11,21), (21,61) relative to signal t. Existing momentum and forward-return functions are reused without modification. Up to 60 pre-period rows warm factors only. Missing history/endpoints remain NaN. Each named period independently bounds both endpoints. Common samples intersect all factor/interval pairs before recomputing average ranks, then intersect valid dates across all 12 combinations. Standard deviation uses ddof=1; ICIR is unannualized; positive fraction means IC>0. Annual statistics group signal years within their named bounded period.','![Incremental IC](../data/research/momentum_001B_incremental/heatmaps.png)','## Statistics',base.markdown(summary),'## Comparison with existing cumulative results','Cumulative means come directly from the unchanged prior artifacts. Available samples may differ by endpoint availability. Strict common samples for cumulative and incremental grids use the same endpoint union (1,6,11,21,61), but zero-variance exclusions can still change retained dates. Correlations are not additive; differences are descriptive, not tests.',base.markdown(comparison[['period','sample','lookback','horizon','mean_incremental','mean_cumulative','count_incremental','count_cumulative']]),'## Annual statistics',base.markdown(yearly),'## Interpretation and limitations','Signs in the tables identify negative/positive associations; no interval is selected as optimal. Intervals are disjoint within a signal date, but returns still overlap across consecutive signal dates and share securities. Do not treat daily IC observations as independent. No significance tests, HAC bandwidth choices, backtesting or parameter optimization are performed. Multiple intervals, lookbacks, years, subperiods and samples create multiple comparisons. Current-constituent survivorship/selection bias, IPO histories, missing endpoints and vendor adjustments remain. The 2010 start has no pre-period history in the snapshot; initial factors are undefined. Boundaries exclude the final 6,11,21,61 rows respectively. Missing data are never filled.']
    REPORT.write_text('\n\n'.join(sections)+'\n',encoding='utf-8')
    after=integrity()
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[REPORT,Path(__file__),ROOT/'tests/test_momentum_incremental_001B.py']
    manifest=dict(original_integrity_before=before,original_integrity_after=after,original_B_manifest_sha256=digest(base.OUT/'manifest.json'),sha256={p.relative_to(ROOT).as_posix():digest(p) for p in paths})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(summary[['period','sample','lookback','horizon','mean','count','mean_pairs']].to_string(index=False))
if __name__=='__main__': run()
