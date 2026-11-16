# Market data coverage

Universe constructed: 2026-11-12 (Asia/Shanghai).

## Universe and methodology

503 current constituent securities; 300 selected using proportional sector quotas 
(largest remainder, alphabetical sector tie break), then the lowest SHA-256 hashes 
of `factor-research-universe-v1|source_ticker` within each sector. No price/history filter or substitutions.
Share classes are separate securities, not necessarily 300 distinct issuers.

Source: [Wikipedia-derived public CSV mirror](https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv). Direct Wikipedia access returned 403.
Snapshot and checksum: `data/universe/2026-11-12/`; selection metadata: `config/universe.json`.
Recent membership spot-check: [Okta replaces Kenvue, effective November 4](https://press.spglobal.com/2026-10-30-Okta-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600).
**Survivorship and selection bias:** this is current membership sampled after the historical period.
It does not represent historical S&P 500 membership; sector labels are current, too.

## Download and coverage

Yahoo daily Close, auto_adjust=True; 2010-01-01 inclusive through 2026-01-01 exclusive.
Existing loader and environment proxy retained. Initial batch 10; subsequent batches up to 25,
20 seconds apart, no application retries; stop on rate-limit indications.
Independent validated caches under root data/raw and data/processed. No forward filling.

Requested: 300; with observations: 298; 
matrix: 4024 dates × 300 tickers.
Observed range: 2010-01-04 00:00:00 through 2025-12-31 00:00:00.
Partial histories: 52; internal missing cells: 0.
Daily eligible count range: 246–298.

Eligibility here means a positive finite observed price on that date only; it does not imply
a sufficient factor lookback, future label, liquidity, or historical index membership.
Coverage ratios use the union of observed dates. No independent exchange calendar is used,
so an all-universe missing session cannot be detected. Missing values remain NaN.

| Sector | Requested | Downloaded |
|---|---:|---:|
| Communication Services | 13 | 13 |
| Consumer Discretionary | 28 | 28 |
| Consumer Staples | 20 | 20 |
| Energy | 13 | 13 |
| Financials | 45 | 45 |
| Health Care | 36 | 36 |
| Industrials | 50 | 48 |
| Information Technology | 45 | 45 |
| Materials | 14 | 14 |
| Real Estate | 18 | 18 |
| Utilities | 18 | 18 |

## Per-stock coverage

| Ticker | First date | Last date | Missing | Coverage | Internal gaps | Status |
|---|---|---|---:|---:|---:|---|
| ABBV | 2013-01-02 | 2025-12-31 | 754 | 81.26% | 0 | downloaded |
| ABNB | 2020-12-10 | 2025-12-31 | 2754 | 31.56% | 0 | downloaded |
| ABT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ACN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ADBE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ADI | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AEP | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AES | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AIG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AIZ | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AKAM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ALGN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ALLE | 2013-11-18 | 2025-12-31 | 976 | 75.75% | 0 | downloaded |
| AMAT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AMGN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AMP | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AMT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AMZN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ANET | 2014-06-06 | 2025-12-31 | 1113 | 72.34% | 0 | downloaded |
| APA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| APD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| APH | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| APP | 2021-04-15 | 2025-12-31 | 2839 | 29.45% | 0 | downloaded |
| APTV | 2011-11-17 | 2025-12-31 | 474 | 88.22% | 0 | downloaded |
| ATO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AVGO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| AVY | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BAX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BDX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BE | 2018-07-25 | 2025-12-31 | 2154 | 46.47% | 0 | downloaded |
| BEN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BF-B | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BIIB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BKNG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BSX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| BXP | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| C | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CARR | 2020-03-19 | 2025-12-31 | 2569 | 36.16% | 0 | downloaded |
| CASY | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CBOE | 2010-06-15 | 2025-12-31 | 112 | 97.22% | 0 | downloaded |
| CBRE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CCI | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CDNS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CDW | 2013-06-27 | 2025-12-31 | 876 | 78.23% | 0 | downloaded |
| CEG | 2022-01-19 | 2025-12-31 | 3032 | 24.65% | 0 | downloaded |
| CF | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CFG | 2014-09-24 | 2025-12-31 | 1189 | 70.45% | 0 | downloaded |
| CHD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CHRW | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CI | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CIEN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CLX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CMCSA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CMG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CMS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CNC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| COF | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| COHR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| COIN | 2021-04-14 | 2025-12-31 | 2838 | 29.47% | 0 | downloaded |
| COST | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CPAY | 2010-12-15 | 2025-12-31 | 240 | 94.04% | 0 | downloaded |
| CPRT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CPT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CRM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CRWD | 2019-06-12 | 2025-12-31 | 2375 | 40.98% | 0 | downloaded |
| CSCO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| CTSH | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| D | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DASH | 2020-12-09 | 2025-12-31 | 2753 | 31.59% | 0 | downloaded |
| DD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DGX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DHR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DIS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DLR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DOW | 2019-03-20 | 2025-12-31 | 2317 | 42.42% | 0 | downloaded |
| DPZ | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DUK | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DVA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| DVN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ECHO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| EFX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EIX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| ELV | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EMR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EOG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EQT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| ERIE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| ESS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EW | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EXC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EXPD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| EXPE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| F | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FAST | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FCX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FDS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FDX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FDXF | unavailable | unavailable | 4024 | 0.00% | 0 | no_observations |
| FE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FERG | 2010-01-05 | 2025-12-31 | 1 | 99.98% | 0 | downloaded_diagnostic |
| FFIV | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FICO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FISV | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FITB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| FIX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| FOX | 2019-03-13 | 2025-12-31 | 2312 | 42.54% | 0 | downloaded |
| FRT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| FSLR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| FTNT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GDDY | 2015-03-31 | 2025-12-31 | 1318 | 67.25% | 0 | downloaded |
| GE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GEHC | 2022-12-15 | 2025-12-31 | 3261 | 18.96% | 0 | downloaded |
| GEN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GEV | 2024-03-27 | 2025-12-31 | 3581 | 11.01% | 0 | downloaded |
| GILD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GIS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GM | 2010-11-18 | 2025-12-31 | 222 | 94.48% | 0 | downloaded |
| GNRC | 2010-02-11 | 2025-12-31 | 27 | 99.33% | 0 | downloaded |
| GPC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GPN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| GWW | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| HAS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| HBAN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| HCA | 2011-03-10 | 2025-12-31 | 298 | 92.59% | 0 | downloaded |
| HIG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| HLT | 2013-12-12 | 2025-12-31 | 993 | 75.32% | 0 | downloaded |
| HON | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| HONA | unavailable | unavailable | 4024 | 0.00% | 0 | no_observations |
| HOOD | 2021-07-29 | 2025-12-31 | 2912 | 27.63% | 0 | downloaded_diagnostic |
| HPQ | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| HUBB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| HUM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| HWM | 2016-11-01 | 2025-12-31 | 1720 | 57.26% | 0 | downloaded_diagnostic |
| IBKR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| IBM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| IEX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| IFF | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| INTC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| IP | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| IT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| ITW | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| IVZ | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| J | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| JCI | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| JKHY | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| KDP | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| KEY | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| KEYS | 2014-10-20 | 2025-12-31 | 1207 | 70.00% | 0 | downloaded_diagnostic |
| KHC | 2015-07-06 | 2025-12-31 | 1384 | 65.61% | 0 | downloaded_diagnostic |
| KKR | 2010-07-15 | 2025-12-31 | 133 | 96.69% | 0 | downloaded_diagnostic |
| KMB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded_diagnostic |
| KMI | 2011-02-11 | 2025-12-31 | 280 | 93.04% | 0 | downloaded_diagnostic |
| KR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| L | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| LH | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| LIN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| LLY | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| LMT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| LULU | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| LUV | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| LYB | 2010-04-28 | 2025-12-31 | 79 | 98.04% | 0 | downloaded |
| MA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MAA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MAR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MAS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MCD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MDLZ | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MET | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| META | 2012-05-18 | 2025-12-31 | 599 | 85.11% | 0 | downloaded |
| MGM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MLM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MMM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MNST | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MPC | 2011-06-24 | 2025-12-31 | 372 | 90.76% | 0 | downloaded |
| MRVL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MSFT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MTD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| MU | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NEM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NFLX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NI | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NKE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NOC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NRG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NSC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NTRS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| NWS | 2013-06-19 | 2025-12-31 | 870 | 78.38% | 0 | downloaded |
| NWSA | 2013-06-19 | 2025-12-31 | 870 | 78.38% | 0 | downloaded |
| O | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ODFL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| OKE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| OMC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ORCL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| OTIS | 2020-03-19 | 2025-12-31 | 2569 | 36.16% | 0 | downloaded |
| PANW | 2012-07-20 | 2025-12-31 | 642 | 84.05% | 0 | downloaded |
| PAYX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PCAR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PCG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PEG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PFE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PFG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PGR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PH | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PHM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PLD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PNC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PNW | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PPG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PRU | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PSA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PSX | 2012-04-12 | 2025-12-31 | 573 | 85.76% | 0 | downloaded |
| PTC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| PYPL | 2015-07-06 | 2025-12-31 | 1384 | 65.61% | 0 | downloaded |
| Q | 2025-10-27 | 2025-12-31 | 3978 | 1.14% | 0 | downloaded |
| RCL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| RDDT | 2024-03-21 | 2025-12-31 | 3577 | 11.11% | 0 | downloaded |
| REG | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| REGN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| RL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| RMD | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ROK | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ROL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ROP | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| RTX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| RVTY | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SBAC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SBUX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SCHW | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SHW | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SJM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SLB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SMCI | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SNA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SNDK | 2025-02-13 | 2025-12-31 | 3802 | 5.52% | 0 | downloaded |
| SNPS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SOLV | 2024-03-26 | 2025-12-31 | 3580 | 11.03% | 0 | downloaded |
| SPGI | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SRE | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| STT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| STX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| SYF | 2014-07-31 | 2025-12-31 | 1151 | 71.40% | 0 | downloaded |
| SYK | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TECH | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TEL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TGT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TJX | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TKO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TMO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TPL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TPR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TRMB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TSCO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TSLA | 2010-06-29 | 2025-12-31 | 122 | 96.97% | 0 | downloaded |
| TSN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TTWO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TWLO | 2016-06-23 | 2025-12-31 | 1629 | 59.52% | 0 | downloaded |
| TXN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| TYL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| UBER | 2019-05-10 | 2025-12-31 | 2353 | 41.53% | 0 | downloaded |
| UDR | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| UHS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| UNH | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| USB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| V | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| VICI | 2018-01-02 | 2025-12-31 | 2013 | 49.98% | 0 | downloaded |
| VLO | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| VLTO | 2023-10-04 | 2025-12-31 | 3461 | 13.99% | 0 | downloaded |
| VMC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| VRSK | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| VRT | 2018-08-02 | 2025-12-31 | 2160 | 46.32% | 0 | downloaded |
| VTRS | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WAB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WAT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WEC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WELL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WFC | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WMB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WMT | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WRB | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WSM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WST | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WTW | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WY | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| WYNN | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| XEL | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| XOM | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ZBH | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |
| ZBRA | 2010-01-04 | 2025-12-31 | 0 | 100.00% | 0 | downloaded |

## Failures and ticker changes

Unavailable symbols: FDXF, HONA.
Batch rejections do not prove every member failed at the vendor; such symbols are explicitly
marked batch_rejected and not substituted. Unattempted symbols remain in the matrix as NaN.
Dot share-class symbols are mapped to Yahoo hyphens; source symbols are retained.
Other ticker changes and predecessor histories are not inferred or stitched automatically.

## Structured outputs

Under `data/market/2026-11-12/`: `prices.csv`, `stock_coverage.csv`, `daily_coverage.csv`
(one eligible-count row per observed trading date), `sector_coverage.csv`,
`partial_symbols.csv`, `unavailable_symbols.csv`, `batches.json`, and `summary.json`.

## Limitations

IPOs, spin-offs, ticker changes and vendor gaps can explain short histories; first observation
is not verified IPO date. Missingness causes are not independently adjudicated. Delisted and
former constituents are absent from this current-universe design. Corporate-action adjustment
and historical prices can be revised; these are retrieval-time snapshots, not point-in-time data.
Adjusted Close does not establish executable returns. No factor, IC or portfolio analysis ran.

## Rejected-batch diagnostics

A single diagnostic request per rejected batch preserved the complete response separately.
Valid individual columns were retained after the same strict panel validation; failed symbols
remain NaN. Diagnostic raw/processed CSVs and request/checksum manifests are stored under
`data/market/2026-11-12/diagnostics/`, separate from loader-managed caches.
No diagnostic request was allowed after a recorded rate-limit stop. No identity rotation.
no_observations means no valid history was returned, not a verified delisting or IPO cause.

## Verified post-period spin-offs

- FDXF: standalone trading began 2026-06-01. FedEx Freight spin-off began trading after requested end; do not substitute parent FDX. [Company announcement](https://newsroom.fedexfreight.com/fedex-freight-completes-spin-off-and-begins-trading-on-the-new-york-stock-exchange).
- HONA: standalone trading began 2026-06-29. Honeywell Aerospace spin-off began trading after requested end; do not substitute parent HON. [Company announcement](https://www.honeywell.com/us/en/news/press-releases/2026/06/honeywell-technologies-launches-independent-pure-play-automation-company-following-honeywell-aerospace-spin-off).

These verified dates explain the two wholly unavailable histories; neither symbol was removed.
Other missing-history causes remain unverified. Structured notes: `symbol_notes.csv`.
