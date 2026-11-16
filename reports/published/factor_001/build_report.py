"""Publication only: format saved evidence; never construct factors or evaluate outcomes."""
import base64
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
SOURCES = [
    '01_momentum.md', '01_momentum_exploration_summary.md', '01B_momentum_horizon.md',
    '01B_momentum_incremental.md', '01C_momentum_risk.md', '01_momentum_validation_protocol.md',
    '01_momentum_final_test_results.md', '01_momentum_alpha_assessment_final.md', 'FACTOR_LIBRARY.md',
]
USED = {}
PARTS = []
FIGURES = []
DATE = '2026-11-16'
TITLE = 'Momentum Factor #001 — Comprehensive Quantitative Research Report'


def read(path):
    raw = (ROOT / path).read_bytes()
    USED[path] = hashlib.sha256(raw).hexdigest()
    return raw


def js(path):
    return json.loads(read(path))


def rows(path):
    return list(csv.DictReader(read(path).decode('utf-8-sig').splitlines()))


def e(value):
    return html.escape(str(value))


def p(text):
    PARTS.append('<p>' + text + '</p>')


def table(headers, values, caption=''):
    PARTS.append('<div class="table-wrap"><table>' + (f'<caption>{e(caption)}</caption>' if caption else '') +
                 '<thead><tr>' + ''.join('<th>'+e(x)+'</th>' for x in headers) + '</tr></thead><tbody>' +
                 ''.join('<tr>'+''.join('<td>'+e(x)+'</td>' for x in row)+'</tr>' for row in values) + '</tbody></table></div>')


def fmt(value, digits=6):
    return f'{float(value):.{digits}f}'


def figure(path, caption):
    raw = read(path)
    FIGURES.append(path)
    PARTS.append(f'<figure><img alt="{e(caption)}" src="data:image/png;base64,{base64.b64encode(raw).decode()}">'
                 f'<figcaption><strong>Figure {len(FIGURES)}.</strong> {e(caption)}<span class="source">Saved source: {e(path)}</span></figcaption></figure>')


HEADINGS = [
    'Executive Summary and Final Classification', 'Economic Motivation and Mathematical Definition',
    'Dataset and Research Methodology', 'Exploratory Rank IC and Quantile Analysis',
    'Lookback and Prediction Horizon Analysis', 'Incremental Forward Return Analysis',
    'Sector and Volatility Risk Controls', 'Temporal Validation (2017–2019)',
    'Final Held-Out Test (2020–2025)', 'Final Research Assessment and Alpha Signal Implications',
    'Limitations and Reproducibility', 'Appendix: Detailed Statistics and Research References',
]


def section(n):
    PARTS.append(f'<h2 id="s{n}"><span>{n:02d}</span> {HEADINGS[n-1]}</h2>')


def verify_originals():
    from scripts import execute_momentum_001_final_test as frozen
    from scripts.verify_momentum_001_validation import digest
    checks = frozen.verify_history()  # Byte/version checks only; never an execution driver.
    proof = json.loads((ROOT/'reports/archive/momentum_001/closure_integrity.json').read_text(encoding='utf-8'))
    for key in ['preserved_prior_sha256', 'preserved_final_artifacts_sha256', 'new_archive_sha256']:
        for path, sha in proof[key].items():
            assert digest(ROOT/path) == sha, path
    assert digest(frozen.OUT/'artifacts.json') == proof['original_final_manifest_sha256']
    return checks


def content():
    source_text = {name: read('reports/'+name).decode('utf-8') for name in SOURCES}
    final = js('data/final_test/momentum_001_v1/result.json')
    validation = js('data/validation/momentum_001_v1/result.json')
    library = js('config/factor_library/001_momentum.json')
    assert final['primary']['decision'] == 'Not Supported'
    assert validation['primary']['decision'] == 'Pass'
    assert library['research_classification'] == 'Watchlist' and library['research_status'] == 'Closed'
    assert '0.19232841654620408' in source_text['01_momentum_alpha_assessment_final.md']
    assert '0.007305374754399302' in source_text['01_momentum_alpha_assessment_final.md']
    sensitivity = rows('data/research/momentum_001/window_sensitivity_2010_2016/summary.csv')
    horizon = rows('data/research/momentum_001B/summary.csv')
    incremental = rows('data/research/momentum_001B_incremental/summary.csv')
    risk = rows('data/research/momentum_001C/summary.csv')
    coefficients = rows('data/research/momentum_001C/regression_summary.csv')
    annual = rows('data/research/momentum_001C/regression_annual.csv')
    coverage = rows('data/research/momentum_001C/coverage.csv')
    quant = rows('data/research/momentum_001/quantiles_2010_2016/quantile_summary.csv')
    spread = rows('data/research/momentum_001/quantiles_2010_2016/spread_summary.csv')[0]
    fq = rows('data/final_test/momentum_001_v1/quantile_summary.csv')
    vq = rows('data/validation/momentum_001_v1/quantile_summary.csv')
    fp = final['primary']; vp = validation['primary']
    PARTS.append(f'<div class="cover"><div class="eyebrow">FACTOR RESEARCH / CLOSED RESEARCH ARCHIVE</div><h1>{TITLE}</h1>'
                 '<div class="cover-rule"></div><div class="classification">Watchlist — Mixed Temporal Evidence</div>'
                 f'<p class="cover-meta">Factor ID 001 &nbsp; • &nbsp; Publication date {DATE}<br>Research status: Closed</p>'
                 '<div class="cover-status"><b>Validation: Pass</b><b>Final Held-Out Test: Not Supported</b></div>'
                 '<p class="cover-note">A consolidated presentation of completed research. No new market evaluation, statistical test, parameter search or portfolio backtest.</p></div>')
    PARTS.append('<nav aria-label="Table of contents"><h2>Contents</h2><ol>'+''.join(f'<li><a href="#s{i}">{e(h)}</a></li>' for i,h in enumerate(HEADINGS,1))+'</ol></nav>')
    section(1)
    p('<strong>Final classification: Watchlist — Mixed Temporal Evidence.</strong> Negative 5D Momentum was supported by exploration and passed a frozen temporal validation. The single final held-out test did not meet the predeclared evidence threshold. The research is closed; the original hypothesis and result are preserved. [R1, R7, R8, R9]')
    table(['Final primary metric', 'Recorded value'], [['Mean Rank IC',fmt(fp['mean_rank_ic'],9)],['HAC standard error',fmt(fp['hac_se'],9)],['Lower-tail p-value',fmt(fp['one_sided_p'],9)],['One-sided 95% upper bound',fmt(fp['one_sided_upper_95'],9)],['Valid dates',fp['valid_ic_observations']]])
    p('The mean remains negative, but p ≥ 0.05 and the upper confidence bound is above zero. Failure to reject the null does not prove a zero effect or establish equivalence. It does mean that the predefined final evidence standard for a robust predictive candidate was not met.')
    table(['Evidence stage','Period','Mean raw 5D Rank IC','Decision/status'], [['Exploration','2010–2016','−0.013475','Exploratory selection'],['Frozen validation','2017–2019',fmt(vp['mean_rank_ic']),'Pass'],['Single final test','2020–2025',fmt(fp['mean_rank_ic']),'Not Supported']], 'Temporal evidence comparison — saved results, not a new test')
    p('Statistical validation is a protocol-specific evidence decision. Tradable Alpha additionally requires credible risk adjustment and executable returns after costs, financing, capacity and trading constraints. None is established by these factor correlations or overlapping forward labels.')
    section(2)
    p('The original implementation is unchanged and defaults to a 20-day lookback. The investigated candidate and both frozen tests use L = 5. Prices are adjusted daily Close; periods count observed trading rows, not calendar days. No missing-price filling is performed. [R1, R2, R8]')
    PARTS.append('<div class="equation"><math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><msub><mi>M</mi><mi>L</mi></msub><mo>(</mo><mi>t</mi><mo>)</mo><mo>=</mo><mfrac><msub><mi>P</mi><mi>t</mi></msub><msub><mi>P</mi><mrow><mi>t</mi><mo>−</mo><mi>L</mi></mrow></msub></mfrac><mo>−</mo><mn>1</mn></math><p>Investigated orientation: S(t) = −M₅(t). Target: R(t) = P[t+6] / P[t+1] − 1.</p></div>')
    p('Continuation is the natural hypothesis for positively oriented raw Momentum. The observed short-horizon negative relationship instead motivates a reversal interpretation: recent relative losers outperform winners. Temporary price pressure, liquidity provision and overreaction are possible explanations, not identified causal mechanisms. Negating the signal is an orientation convention and supplies no new evidence. Frozen tests retain raw Momentum and the alternative mean IC &lt; 0.')
    section(3)
    p('The original 300-security universe was deterministically selected from current S&amp;P 500 constituents with sector coverage. The adjusted Yahoo Finance snapshot and current sector metadata are frozen; the sample is not historical index membership. Exploration covers 2010–2016; frozen validation covers 2017–2019; the single final test covers 2020–2025. #001-B and #001-C subsequently reused 2010–2019 as post-validation exploration. [R2–R8]')
    table(['Period','Universe','Price coverage','Raw IC dates','Risk common dates','Mean common pairs'], [[x['period'].replace('_','–'),x['securities'],f"{float(x['price_coverage'])*100:.2f}%",x['raw_dates'],x['common_dates'],fmt(x['mean_common_pairs'],2)] for x in coverage], 'Saved #001-C coverage diagnostics; pooled and subperiod rows overlap')
    p('Daily Spearman IC uses aligned signal-date/ticker pairs, average ranks for ties, at least 100 pairs and nonconstant cross sections. Means equally weight eligible dates; dispersion uses sample SD (ddof = 1); ICIR is unannualized mean/SD. Available samples differ by specification. Strict common samples intersect paired assets before recomputing ranks and then intersect valid dates.')
    p('Labels are bounded independently within each reported period. Up to 60 pre-period rows warm longer controls where available; no pre-2010 history exists in the snapshot. The final protocol uses exactly five pre-2020 rows. Its last six signal rows lack in-boundary exits and are excluded. Missing endpoints remain undefined; no synthetic prices are introduced.')
    section(4)
    table(['Lookback','Sample','Dates','Mean Rank IC','SD','ICIR'], [[x['window'],x['sample'],x['count'],fmt(x['mean']),fmt(x['std']),fmt(x['icir'])] for x in sensitivity], '2010–2016 fixed-window exploration [R2]')
    p('Exploratory 5D common-sample HAC lag-5 two-sided p = 0.022841, with 95% interval [−0.024770, −0.001848]. Lags 10 and 20 gave p = 0.024688 and 0.028827. These are existing unadjusted exploratory results, not fresh tests. Paired-window intervals all included zero across those lags; the research did not establish a winning lookback. [R2]')
    figure('reports/figures/momentum_001_window_sensitivity_2010_2016.png','Saved exploratory window comparisons; shared samples and yearly patterns are descriptive.')
    table(['Quantile','Mean 5D forward label','Valid dates'],[[x['quantile'],f"{float(x['mean_return'])*100:.4f}%",x['valid_dates']] for x in quant], 'Exploratory 5D Momentum quantiles; Q1 lowest, Q5 highest')
    p(f"Saved Q1−Q5 mean spread: {float(spread['mean_spread'])*100:.4f} percentage points; daily spread SD {float(spread['std_daily_spread'])*100:.4f} percentage points; positive fraction {float(spread['positive_spread_fraction'])*100:.2f}%. The means are not strictly monotonic, and annual spread was negative in 2012. No spread significance test or executable strategy return was calculated.")
    figure('reports/figures/momentum_001_quantiles_2010_2016.png','Saved quantile mean-return and annual-spread analysis. This is not a histogram or a portfolio equity curve.')
    section(5)
    p('Fixed L ∈ {5,20,60}, H ∈ {5,10,20,60}, entry lag 1. #001-B is explicitly post-validation exploration; 2017–2019 was already seen. The pooled 5D cumulative mean IC attenuates from −0.015404 at H=5 to −0.007776 at H=60. In 2017–2019, 60D Momentum has positive cumulative means across the fixed horizons, while 20D changes sign at H=60. No optimum is selected. Detailed saved summary statistics appear in the appendix. [R3]')
    figure('reports/figures/momentum_001B/mean_ic_heatmaps.png','Saved lookback–horizon mean Rank IC matrices: available and strict common samples; subperiod endpoints are independently bounded.')
    figure('reports/figures/momentum_001B/horizon_profiles.png','Saved cumulative horizon profiles. Repeated periods and sample variants are not independent confirmations.')
    section(6)
    table(['Interval relative to entry','Saved return-label definition'],[['Days 1–5','P[t+6] / P[t+1] − 1'],['Days 6–10','P[t+11] / P[t+6] − 1'],['Days 11–20','P[t+21] / P[t+11] − 1'],['Days 21–60','P[t+61] / P[t+21] − 1']])
    p('The pooled 5D days 21–60 IC is near zero and changes sign between available (−0.000262) and common (+0.000425) samples. In 2017–2019, 5D and 20D are negative in the first three intervals but positive in days 21–60; 60D is positive throughout. This supports horizon-dependent characterization, not a selected alternative test. Intervals are disjoint within a signal date but overlap across consecutive signals; correlations are not additive. [R4]')
    figure('data/research/momentum_001B_incremental/heatmaps.png','Saved incremental interval mean IC matrices; ending days 5, 10, 20 and 60 identify distinct future intervals.')
    figure('data/research/momentum_001B_incremental/comparison.png','Saved incremental versus cumulative common-sample profiles; no new outcomes or charts were computed for publication.')
    section(7)
    p('Realized volatility is the unannualized sample SD of complete trailing 20/60 daily simple returns ending on the signal date. Daily neutralization fits Momentum on sector dummies, separately with vol20, vol60 or both, before filtering future labels. Regressions of raw future returns on Momentum and controls use outcome-complete samples. No present-day capitalization was used. Conditional linear slopes and Spearman IC measure different relationships. [R5]')
    table(['Period','Common sample specification','Dates','Mean IC','SD','Positive fraction'],[[x['period'].replace('_','–'),x['series'].replace('common/',''),int(float(x['count'])),fmt(x['mean']),fmt(x['std']),fmt(x['positive_fraction'],4)] for x in risk if x['series'].startswith('common/')])
    figure('data/research/momentum_001C/adjusted_ic.png','Saved sector and volatility-adjusted IC comparison on identical paired samples. Persistence of a descriptive association is not proof of causality.')
    table(['Period','Regression controls','Dates','Mean slope','SD','Positive fraction'],[[x['period'].replace('_','–'),x['model'],x['count'],fmt(x['mean']),fmt(x['std']),fmt(x['positive_fraction'],4)] for x in coefficients])
    p('Joint-control annual means are negative in nine of ten separately bounded subperiod years; 2015 is positive (+0.002454). Both low/high volatility groups have negative subperiod mean ICs, with descriptively more negative values in high-volatility groups. Pooled Momentum–volatility mean rank correlations are small (+0.001889 and +0.003656), but daily dispersion is about 0.24. Small average exposure does not imply absent time-varying exposure.')
    figure('data/research/momentum_001C/annual_coefficients.png','Saved annual conditional Momentum slopes in raw decimal-return units; no regression significance claims are made.')
    section(8)
    p('The negative 5D hypothesis was selected after exploration. The 2017–2019 protocol was then frozen and executed once with no amendment. It required an eligible negative mean and one-sided lower-tail p &lt; 0.05, using HAC lag 5, Bartlett weights, n/(n−1) correction and asymptotic normal inference. Its recorded decision is <strong>Pass</strong>. [R1, R6]')
    primary_table(vp)
    secondary_table(validation, vq)
    p('The validation secondary result was descriptive and could not determine success. The later #001-B/#001-C reuse of these dates does not create new independent confirmation. The historical validation and pre-test assessment are preserved, not rewritten after the final test.')
    section(9)
    p('The frozen 2020–2025 protocol was executed exactly once. Its decision is <strong>Not Supported</strong>. All 159 preflight tests passed without failures, errors or skips. The exclusive marker was recorded before real final-outcome access; the original seal, source versions and data were preserved. [R7, R8]')
    primary_table(fp)
    PARTS.append('<div class="equation"><p>t = mean(IC) / SE<sub>HAC</sub> &nbsp;&nbsp; p = Φ(t)<br>Upper one-sided 95% bound = mean(IC) + Φ<sup>−1</sup>(0.95) × SE<sub>HAC</sub></p></div>')
    p('The frozen null is mean IC ≥ 0; the alternative is mean IC &lt; 0. Lag 5, Bartlett kernel and n/(n−1) correction are unchanged. The lower-tail p-value is 0.192328417 and the upper bound is +0.006516792. Secondary evidence cannot override the primary decision.')
    secondary_table(final, fq)
    p('There were 1,508 final-period rows, 1,502 valid IC observations and six endpoint exclusions. Exactly five warm-up rows were 2019-12-24, 2019-12-26, 2019-12-27, 2019-12-30 and 2019-12-31. All 300 columns were retained; FDXF and HONA had no observed final-period prices. Valid signal dates ran from 2020-01-02 through 2025-12-22.')
    section(10)
    p('<strong>Watchlist — Mixed Temporal Evidence; Research Status: Closed.</strong> The pre-test Alpha Candidate assessment remains an unchanged historical record. The final assessment is the current classification. The unmet frozen final threshold prevents calling this a confirmed robust predictive candidate, while non-rejection does not prove no relationship. [R8, R9]')
    table(['Evidence level','What this archive supports'],[['Predictive association','Negative sample mean IC in exploration, validation and final periods; the final test did not reject its null.'],['Incremental information','Descriptive residual association under limited sector/volatility controls on already-seen data.'],['Tradable Alpha','Not established; costs, execution, capacity and comprehensive risk-adjusted performance were not tested.']])
    p('The final quantile shape is not strictly monotonic. Any interpretation of nonlinearity or regime differences after the final result is a <strong>post-test observation, not confirmatory evidence</strong>. No new model, subgroup, horizon or replacement hypothesis is fitted. The original test must not be repeated or resealed. Closure authorizes no new factor study.')
    section(11)
    p('Current-constituent selection creates survivorship and selection bias; frozen sector labels are not historical point-in-time classifications. IPO availability, absent delisted histories, missing endpoints, vendor revisions and retrospective corporate-action adjustments remain limitations. Complete-case/common samples condition on availability, and no prices were filled. [R2–R9]')
    p('Overlapping labels, shared securities and persistent signals induce dependence. Lag-5 HAC is not a guarantee against longer dependence and was not automatically reused for longer horizons. Exploratory windows, sectors, regimes, groups, horizons and controls create multiple comparisons; reused samples are not independent replications. No new multiplicity correction or significance test is performed in this publication.')
    p('Historical beta, size, value, quality, liquidity and event exposures remain incompletely controlled. No turnover, bid-ask costs, financing, short availability, capacity or implementable portfolio constraints were evaluated. Positive quantile labels can include market exposure and cannot be compounded as overlapping strategy performance.')
    p('This publication reads saved summaries and embeds original figures; no market-price panel is parsed. Existing integrity routines hash original bytes and check pinned versions only. HTML and PDF are built from identical content. Embedded PNGs, CSS and native MathML require no network. See the accompanying README and publication_manifest.json for build commands, hashes and QA. The source records remain authoritative; publication rounding is presentation only.')
    section(12)
    p('The following tables reproduce saved descriptive statistics without recomputing outcomes. Means, SD and ICIR are unannualized; positive fractions are proportions. “Individual” is the saved available-sample label. Appendix tables carry complete 12-combination summaries for the horizon studies; annual detail is retained in the cited source reports. [R3–R5]')
    for label, dataset in [('Cumulative horizons', horizon), ('Incremental intervals', incremental)]:
        for period in ['2010_2019','2010_2016','2017_2019']:
            for sample in ['individual','common']:
                PARTS.append(f'<h3>{label} · {period.replace("_","–")} · {sample}</h3>')
                table(['L','H / end day','Dates','Mean IC','SD','ICIR','Positive fraction'], [[x['lookback'],x['horizon'],int(float(x['count'])),fmt(x['mean']),fmt(x['std']),fmt(x['icir']),fmt(x['positive_fraction'],4)] for x in dataset if x['period']==period and x['sample']==sample])
    PARTS.append('<h3>Risk groups and exposures</h3>')
    table(['Period','Series','Dates','Mean IC','SD','Mean pairs'],[[x['period'].replace('_','–'),x['series'],int(float(x['count'])),fmt(x['mean']),fmt(x['std']),fmt(x['mean_pairs'],2)] for x in risk if x['series'].startswith(('vol','exposure/'))])
    PARTS.append('<h3>Annual joint-control Momentum coefficients</h3>')
    table(['Period','Year','Dates','Mean slope','SD','Positive fraction'],[[x['period'].replace('_','–'),x['year'],x['count'],fmt(x['mean']),fmt(x['std']),fmt(x['positive_fraction'],4)] for x in annual if x['model']=='sector_both' and x['period']!='2010_2019'])
    PARTS.append('<h3>Final-test group counts</h3>')
    table(['Group','Dates','Membership total','Valid returns','Members min–max','Returns min–max'],[[x['quantile'],x['dates'],x['membership_total'],x['observations'],x['members_min']+'–'+x['members_max'],x['valid_returns_min']+'–'+x['valid_returns_max']] for x in fq])
    PARTS.append('<h3>Research references and chronology</h3>')
    for i,name in enumerate(SOURCES,1):
        p(f'<strong>[R{i}]</strong> {e(name)} <span class="source">Repository path: reports/{e(name)}</span>')
    p('R7 records the execution-time status “review pending”; R8 and R9 are the subsequent closure decision and supersede that status without modifying the execution record. Similarly, frozen protocol documents retain their historical pre-execution wording. The exclusive execution marker and saved result establish that the final test was executed once.')
    p('Original driver SHA-256: <code>989bbf51c0be199e09f6b387e62562b5231e091c79a9f974f3501be9a5547391</code>. Original final seal SHA-256: <code>5269706a0f52c5110eab81e45daaeff55443ce9f4c40f9ea53022215beb1e50d</code>. Detailed audits, membership counts and source snapshots reside in the separately backed-up, Git-ignored data archive. The publication is not a replacement seal.')


def primary_table(values):
    table(['Primary statistic','Saved value'], [[label, values[key] if key in ['decision','valid_ic_observations'] else fmt(values[key],9)] for label,key in [('Decision','decision'),('Valid observations','valid_ic_observations'),('Mean Rank IC','mean_rank_ic'),('HAC SE','hac_se'),('t-statistic','t_stat'),('Lower-tail p-value','one_sided_p'),('One-sided 95% upper bound','one_sided_upper_95')]])


def secondary_table(result, groups):
    x = result['secondary']
    table(['Q1 mean','Q2 mean','Q3 mean','Q4 mean','Q5 mean'],[[f"{float(g['mean_return'])*100:.6f}%" for g in groups]], 'Descriptive equally weighted mean forward labels')
    table(['Spread statistic','Saved value'],[['Mean Q1−Q5',f"{x['mean_spread']*100:.6f} percentage points"],['Daily spread SD',f"{x['std_spread']*100:.6f} percentage points"],['Positive fraction',f"{x['positive_fraction']*100:.4f}%"],['Valid dates',x['valid_dates']]])


CSS = '''
:root{color-scheme:light;--navy:#132f46;--teal:#16697a;--muted:#566775}
*{box-sizing:border-box}body{margin:0;background:#eaf0f3;color:#26343e;font:15px/1.6 Arial,Helvetica,sans-serif}
main{max-width:1080px;margin:30px auto;background:white;padding:65px 75px;box-shadow:0 4px 30px #19344818}
h1,h2,h3{color:var(--navy);line-height:1.22}h1{font:44px/1.2 Georgia,serif;max-width:800px;margin:50px 0 32px}
h2{font-size:26px;margin-top:60px;border-top:2px solid #dce5eb;padding-top:20px}h2 span{color:var(--teal);margin-right:8px}
h3{font-size:18px;margin-top:32px}p{margin:14px 0}a{color:var(--teal)}nav a{text-decoration:none}nav li{padding:5px}
.cover{padding:45px 0 100px}.eyebrow{font-size:12px;letter-spacing:2px;color:var(--teal);font-weight:700}.cover-rule{width:90px;border-top:5px solid var(--teal);margin:32px 0}.classification{font:28px/1.4 Georgia,serif;color:var(--navy)}.cover-meta{margin-top:30px;color:var(--muted)}.cover-status{display:flex;gap:24px;margin:40px 0;padding:20px 0;border-top:1px solid #cedae1;border-bottom:1px solid #cedae1}.cover-note{max-width:650px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:12px;line-height:1.45;margin:20px 0;table-layout:fixed}th{text-align:left;background:#e8f0f4;color:var(--navy);font-weight:700}td,th{padding:8px 9px;border-bottom:1px solid #dbe4e9;overflow-wrap:anywhere}tbody tr:nth-child(even){background:#f8fafb}caption{text-align:left;color:var(--muted);font-size:12px;padding:8px 0}figure{margin:30px 0;break-inside:avoid}figure img{width:100%;height:auto;display:block}figcaption{font-size:12px;color:var(--muted);line-height:1.5;padding-top:12px}.source{display:block;font-size:10px;overflow-wrap:anywhere;color:var(--muted)}.equation{background:#f4f8fa;border-left:3px solid var(--teal);padding:18px;text-align:center;font:18px Georgia,serif}.equation math{font-size:24px}code{font-size:10px;overflow-wrap:anywhere}
@page{size:A4;margin:18mm 16mm 20mm}
@media print{body{background:white;font-size:10pt;line-height:1.45}main{padding:0;margin:0;box-shadow:none;max-width:none}.cover{height:235mm;padding-top:15mm;break-after:page}h1{font-size:32pt;margin-top:25mm}.classification{font-size:22pt}.cover-status{display:block}.cover-status b{display:block;margin:8px 0}nav{break-after:page}nav h2{break-before:auto}h2{break-before:page;font-size:20pt;margin-top:0;padding-top:6mm}h3{font-size:12pt;break-after:avoid}p{orphans:3;widows:3}table{font-size:8.1pt;margin:12px 0}th,td{padding:5px 6px}thead{display:table-header-group}tr{break-inside:avoid}caption{font-size:8pt}figure{break-inside:avoid;margin:8mm 0}figure img{max-height:205mm;object-fit:contain}figcaption{font-size:8pt}.source{font-size:7pt}.equation{font-size:12pt}.equation math{font-size:20pt}a{color:inherit;text-decoration:none}}
'''


def render_pdf(browser):
    import websocket
    profile = HERE/'.venv/chrome-profile'
    profile.mkdir(parents=True, exist_ok=True)
    portfile = profile/'DevToolsActivePort'
    if portfile.exists():
        portfile.unlink()  # Publication browser scratch metadata only.
    process = subprocess.Popen([str(browser),'--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
                                '--remote-debugging-port=0','--remote-allow-origins=*','--user-data-dir='+str(profile),'about:blank'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:
        for _ in range(200):
            if portfile.exists(): break
            time.sleep(.1)
        port = portfile.read_text().splitlines()[0]
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        targets=json.load(opener.open(f'http://127.0.0.1:{port}/json'))
        ws=websocket.create_connection(next(t['webSocketDebuggerUrl'] for t in targets if t['type']=='page'),timeout=60,suppress_origin=True,http_proxy_host=None)
        serial=0
        def call(method,params=None):
            nonlocal serial
            serial+=1;ws.send(json.dumps(dict(id=serial,method=method,params=params or {})))
            while True:
                response=json.loads(ws.recv())
                if response.get('id')==serial:
                    if 'error' in response: raise RuntimeError(response['error'])
                    return response.get('result',{})
        version=call('Browser.getVersion')
        call('Page.enable');call('Network.enable');call('Network.setBlockedURLs',{'urls':['http://*','https://*']})
        call('Page.navigate',{'url':(HERE/'momentum_001.html').as_uri()})
        for _ in range(100):
            state=call('Runtime.evaluate',{'expression':'document.readyState','returnByValue':True})
            if state['result'].get('value')=='complete':break
            time.sleep(.1)
        call('Runtime.evaluate',{'expression':'Promise.all([document.fonts.ready,...Array.from(document.images).map(i=>i.decode())])','awaitPromise':True})
        qa=call('Runtime.evaluate',{'expression':'''JSON.stringify({images:document.images.length,brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length,math:document.querySelectorAll('math').length,externalResources:[...document.querySelectorAll('[src],link[href]')].filter(x=>/^(https?:)?\\/\\//.test(x.src||x.href)).length,missingAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.querySelector(a.getAttribute('href'))).length})''','returnByValue':True})
        dom=json.loads(qa['result']['value']);assert dom['brokenImages']==0 and dom['externalResources']==0 and dom['missingAnchors']==0
        pdf=call('Page.printToPDF',{'printBackground':True,'preferCSSPageSize':True,'displayHeaderFooter':True,
                                  'headerTemplate':'<span></span>', 'footerTemplate':'<div style="font-size:8px;color:#566775;width:100%;padding:0 16mm;display:flex;justify-content:space-between"><span>FACTOR RESEARCH · MOMENTUM 001 · CLOSED</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'})
        (HERE/'momentum_001.pdf').write_bytes(base64.b64decode(pdf['data']))
        call('Emulation.setDeviceMetricsOverride',{'width':1200,'height':1600,'deviceScaleFactor':1,'mobile':False})
        shot=call('Page.captureScreenshot',{'format':'png'})
        (HERE/'.venv/html_preview.png').write_bytes(base64.b64decode(shot['data']))
        ws.close()
        return dict(browser=version,html_checks=dom)
    finally:
        process.terminate()
        process.wait(timeout=20)


def inspect_pdf():
    sys.path.insert(0,str(HERE/'.venv/qa'))
    import pymupdf
    doc=pymupdf.open(HERE/'momentum_001.pdf')
    texts=[page.get_text() for page in doc]
    text='\n'.join(texts)
    for required in ['Watchlist','Mixed Temporal Evidence','Not Supported','0.192328417','0.008403280','0.006516792']:
        assert required in text, required
    for title in HEADINGS:
        assert title in text, title
    overflow=[]; images=0; missing_fonts=[]
    for i,page in enumerate(doc):
        assert abs(page.rect.width-595.28)<2 and abs(page.rect.height-841.89)<2
        assert f'{i+1} / {len(doc)}' in texts[i], ('pagination',i)
        assert '\ufffd' not in texts[i]
        for word in page.get_text('words'):
            if word[0]<0 or word[1]<0 or word[2]>page.rect.width+.5 or word[3]>page.rect.height+.5:overflow.append((i+1,word[4]))
        images+=len(page.get_images())
        for font in page.get_fonts():
            if font[1]=='n/a': missing_fonts.append((i+1,font[3]))
    assert not overflow,overflow
    assert not missing_fonts,missing_fonts
    assert images>=len(FIGURES)
    from PIL import Image,ImageOps,ImageDraw
    thumbs=[]
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=pymupdf.Matrix(.35,.35),alpha=False)
        img=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
        canvas=Image.new('RGB',(230,320),'#dce4e8');canvas.paste(img,((230-img.width)//2,5));ImageDraw.Draw(canvas).text((10,303),f'Page {i+1}',fill='black');thumbs.append(canvas)
    for offset in range(0,len(thumbs),12):
        sheet=Image.new('RGB',(920,320*((len(thumbs[offset:offset+12])+3)//4)),'white')
        for j,img in enumerate(thumbs[offset:offset+12]):sheet.paste(img,((j%4)*230,(j//4)*320))
        sheet.save(HERE/f'.venv/contact_{offset//12+1}.png')
    return dict(pages=len(doc),page_size='A4',text_bounds_errors=overflow,missing_font_entries=missing_fonts,image_occurrences=images,all_page_numbers_present=True,required_text_present=True)


def main():
    before=verify_originals()
    content()
    output='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(TITLE)+'</title><style>'+CSS+'\n@media print {.table-wrap {break-inside:avoid}}</style></head><body><main>'+''.join(PARTS)+'</main></body></html>'
    (HERE/'momentum_001.html').write_text(output,encoding='utf-8')
    browser=Path(os.environ.get('PUBLICATION_CHROME','C:/Program Files/Google/Chrome/Application/chrome.exe'))
    checks=render_pdf(browser)
    checks['pdf_checks']=inspect_pdf()
    after=verify_originals()
    for path,sha in USED.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
    manifest=dict(publication_date=DATE,title=TITLE,mode='Saved-evidence presentation only; no new outcomes',source_sha256=USED,
                  build_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),integrity_before=before,integrity_after=after,
                  checks=checks,output_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['momentum_001.html','momentum_001.pdf']},
                  notes=['Legacy verifier status is preparation wording, not current execution status.','Original execution marker/result record the single completed final test.'])
    (HERE/'publication_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(checks,indent=2))


if __name__=='__main__':main()
