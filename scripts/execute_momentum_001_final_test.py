"""Single-use execution of the unchanged final-test v1.0.0 protocol."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import execute_momentum_001_validation as frozen
from scripts.verify_momentum_001_final_test import verify
from scripts.verify_momentum_001_validation import digest
from scripts import momentum_risk_001C as risk
OUT=ROOT/'data/final_test/momentum_001_v1'
DRIVER=Path(__file__).resolve()
PROTOCOL=ROOT/'config/momentum_001_final_test.json'
REPORT=ROOT/'reports/01_momentum_final_test_results.md'

def save(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def config():
    p=json.loads(PROTOCOL.read_text(encoding='utf-8'))
    adapted=deepcopy(p)
    adapted['periods']['validation']=deepcopy(p['periods']['final_test'])
    return adapted

def evaluate(panel,p=None):
    return frozen.evaluate(panel, config() if p is None else p)

def preservation():
    # All pre-existing research and implementation bytes, excluding generated caches.
    paths=[]
    for name in ['reports','research','config','src','factors','scripts','tests','data/research','data/validation','data/protocols']:
        paths.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo'))
    return {p.relative_to(ROOT).as_posix():digest(p) for p in paths if p!=REPORT}

def verify_history():
    final=verify()
    risk.integrity()
    m=json.loads((risk.OUT/'manifest.json').read_text())
    for path,sha in m['sha256'].items():
        if digest(ROOT/path)!=sha: raise ValueError('001-C integrity mismatch: '+path)
    return final

def require_unused():
    if (OUT/'started.json').exists() or REPORT.exists():
        raise ValueError('Final test already attempted or results exist; no rerun')

def preflight():
    require_unused()
    checked=verify_history()
    folder=OUT/'preflight'
    if folder.exists(): raise ValueError('Preflight already exists; do not silently replace failed evidence')
    preserved=preservation()
    folder.mkdir(parents=True)
    driver_hash=digest(DRIVER)
    command=[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','--junitxml='+str(folder/'tests.xml')]
    run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    (folder/'tests.log').write_text(run.stdout+run.stderr,encoding='utf-8')
    print(run.stdout+run.stderr)
    if run.returncode: raise RuntimeError('Preflight tests failed; no real outcomes allowed')
    suites=ET.parse(folder/'tests.xml').getroot().iter('testsuite')
    totals={k:0 for k in ['tests','failures','errors','skipped']}
    for suite in suites:
        for k in totals: totals[k]+=int(suite.get(k,0))
    if not totals['tests'] or any(totals[k] for k in ['failures','errors','skipped']): raise ValueError('Required tests not all passed')
    if preservation()!=preserved or digest(DRIVER)!=driver_hash: raise ValueError('Source or prior research changed during tests')
    verify_history(); require_unused()
    save(folder/'passed.json',dict(driver_sha256=driver_hash,preserved_sha256=preserved,
        protocol_sha256=digest(PROTOCOL),seal_sha256=digest(ROOT/'config/momentum_001_final_test.lock.json'),
        test_xml_sha256=digest(folder/'tests.xml'),test_log_sha256=digest(folder/'tests.log'),counts=totals,
        verification=checked,completed_utc=datetime.now(timezone.utc).isoformat(),command=command))

def execution_gate():
    require_unused(); verify_history()
    passed=json.loads((OUT/'preflight/passed.json').read_text())
    if digest(DRIVER)!=passed['driver_sha256'] or preservation()!=passed['preserved_sha256']:
        raise ValueError('Tested driver/source/prior artifacts changed')
    for name,key in [('tests.xml','test_xml_sha256'),('tests.log','test_log_sha256')]:
        if digest(OUT/'preflight'/name)!=passed[key]: raise ValueError('Test evidence mismatch')
    if digest(PROTOCOL)!=passed['protocol_sha256'] or digest(ROOT/'config/momentum_001_final_test.lock.json')!=passed['seal_sha256']:
        raise ValueError('Frozen protocol or seal mismatch')
    if not passed['counts']['tests'] or any(passed['counts'][k] for k in ['failures','errors','skipped']): raise ValueError('Invalid preflight result')
    return passed

def execute():
    passed=execution_gate()
    stamp=dict(started_utc=datetime.now(timezone.utc).isoformat(),driver_sha256=passed['driver_sha256'],
        protocol_sha256=passed['protocol_sha256'],seal_sha256=passed['seal_sha256'],
        preflight_sha256=digest(OUT/'preflight/passed.json'),authorization='Explicit user request: execute frozen final test exactly once')
    # Atomic exclusive claim precedes all real final-price parsing; never removed.
    with (OUT/'started.json').open('x',encoding='utf-8') as f: json.dump(stamp,f,indent=2)
    (OUT/'executed_driver.py').write_bytes(DRIVER.read_bytes())
    tables={}; coverage={}; secondary=None
    try:
        p=config()
        universe=pd.read_csv(ROOT/p['universe']['path'])
        if len(universe)!=300 or not universe.ticker.is_unique: raise ValueError('Universe invalid')
        panel=frozen.load_bounded_prices(ROOT/p['data']['path'],universe.ticker.tolist(),p)
        primary,secondary,tables=evaluate(panel,p)
        audit=tables['daily_ic_audit']
        # Display terminology only; computation and frozen exclusion rules unchanged.
        audit['exclusion_reason']=audit.exclusion_reason.replace({'forward_endpoint_outside_validation':'forward_endpoint_outside_final_test'})
        for name,table in tables.items(): table.to_csv(OUT/(name+'.csv'))
        coverage=dict(warmup_dates=[str(d.date()) for d in panel.index if d<pd.Timestamp('2020-01-01')],
            securities=len(panel.columns),final_period_rows=len(panel.loc['2020-01-01':]),last_price_date=str(panel.index.max().date()),
            entirely_missing_symbols=panel.columns[panel.loc['2020-01-01':].isna().all()].tolist(),
            exclusions=audit.exclusion_reason.value_counts().to_dict())
    except Exception as exc:
        primary=dict(decision='Inconclusive',reason=f'{type(exc).__name__}: {exc}')
    result=dict(primary=primary,secondary=secondary,input_coverage=coverage,tests=passed['counts'],completed_utc=datetime.now(timezone.utc).isoformat())
    save(OUT/'result.json',result)
    checked=verify_history()
    if preservation()!=passed['preserved_sha256']: raise ValueError('Prior artifacts changed; preserve result and investigate')
    text='# Momentum #001-A: Final Held-Out Test v1.0.0 Results\n\nSingle execution of the unchanged frozen 2020-2025 protocol. This is final-test evidence, distinct from exploration and 2017-2019 validation. No Factor Library classification is finalized here; review is pending.\n\n## Primary\n\n'+frozen.markdown(pd.Series(primary,name='value').to_frame())
    text+='\n\nHAC lag 5, Bartlett kernel, n/(n-1) correction, asymptotic standard normal lower tail; p=norm.cdf(mean/SE), upper95=mean+norm.ppf(.95)*SE. Pass requires eligible mean<0 and p<.05. Secondary results cannot override this decision.\n\n## Secondary descriptive results\n\n'
    text+=frozen.markdown(pd.Series(secondary,name='value').to_frame()) if secondary is not None else 'Not evaluated: primary eligibility failure.'
    if 'quantile_summary' in tables: text+='\n\n'+frozen.markdown(tables['quantile_summary'])
    text+='\n\nAll returns are decimal fractions. Q1 is lowest raw Momentum; Q5 highest. Membership uses factor values before label exclusions. Full daily membership and valid-return counts are saved. No spread inference or portfolio performance is claimed.\n\n## Execution and limitations\n\n'
    text+=f'Coverage: `{json.dumps(coverage)}`. Tests: `{json.dumps(passed["counts"])}`. Driver SHA-256: `{passed["driver_sha256"]}`.\n\n'
    text+='Exactly five preceding observed rows warm factors; endpoints stay within the final period. Exclusive started.json, tested driver snapshot, preflight evidence, result and audit tables are retained under data/final_test/momentum_001_v1. Original reports, protocols, seals and pre-test assessment remain unchanged. No reruns or tuning are permitted. Current-constituent survivorship bias, current sector labels, vendor adjustments, missing history and serial dependence remain limitations. Lag-5 HAC does not guarantee protection against longer dependence. No costs, liquidity, implementation, portfolio backtest or comprehensive risk-adjusted Alpha is modeled. The final classification awaits review.\n'
    with REPORT.open('x',encoding='utf-8') as f:f.write(text)
    save(OUT/'preservation.json',dict(verification=checked,all_prior_hashes_unchanged=True,
        note='Legacy verifier status text describes the frozen preparation record; started.json and result.json record actual execution.'))
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[REPORT]
    save(OUT/'artifacts.json',dict(sha256={p.relative_to(ROOT).as_posix():digest(p) for p in paths},driver_sha256=digest(DRIVER)))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight',action='store_true'); group.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    preflight() if args.preflight else execute()
