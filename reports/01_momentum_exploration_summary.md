# Momentum Research #001 — Exploration close-out

Closed on 2026-11-13 (Asia/Shanghai). This summarizes saved 2010–2016 outputs;
no analysis was rerun. Original notebook outputs and the full research report
remain unchanged. Validation and held-out outcomes have not been inspected here.

## Descriptive findings

Raw/sector results below use 20D Momentum and 5-day forward labels with entry lag
1. The notebook's final endpoint-filtered results are used, rather than its
earlier unfiltered intermediate output. Each series has 1,736 valid dates.

| Series | Mean Rank IC | Sample std | ICIR | Positive fraction |
|---|---:|---:|---:|---:|
| Raw 20D | -0.009835 | 0.157147 | -0.062588 | 0.466590 |
| Sector-neutral 20D | -0.012524 | 0.112791 | -0.111041 | 0.459677 |

Sector neutrality here subtracts each date's sector-average factor value before
cross-sectional ranking. It does not remove market risk or prove a causal effect.
Excluding 2016, the saved raw mean is -0.003771 across 1,490 dates, illustrating
time sensitivity without changing the frozen full exploration sample.

Within-sector analysis used at least five paired assets; all sectors had 1,736
valid dates. These are descriptions with no sector-specific inference:

| Sector | Mean Rank IC |
|---|---:|
| Real Estate | -0.039759 |
| Health Care | -0.035142 |
| Industrials | -0.023283 |
| Utilities | -0.021324 |
| Financials | -0.015630 |
| Consumer Staples | -0.011849 |
| Consumer Discretionary | -0.008665 |
| Materials | -0.008173 |
| Information Technology | -0.006197 |
| Communication Services | 0.014371 |
| Energy | 0.028911 |

SPY regimes used current-date adjusted Close against its trailing 200-row mean,
warmed up with pre-2010 SPY data. Bull: 1,474 dates, mean Rank IC -0.007281;
Bear: 262 dates, mean -0.024208. Unequal samples and serial dependence prevent
reading these descriptive differences as independent evidence of regime effects.

The fixed-window sensitivity study reported:

| Window | Available dates | Available mean Rank IC | Common dates | Common mean Rank IC |
|---|---:|---:|---:|---:|
| 5D | 1,751 | -0.013475 | 1,696 | -0.013309 |
| 20D | 1,736 | -0.009835 | 1,696 | -0.010709 |
| 60D | 1,696 | -0.003273 | 1,696 | -0.003273 |

Common comparison means identical signal dates AND ticker/return pairs, with
ranks recomputed on their intersection. Yearly means varied in sign and magnitude;
these comparisons did not establish a winning window.

## Exploratory statistical evidence

Two-sided Newey–West tests used the saved 1,696-date common sample, Bartlett
weights, n/(n-1) covariance correction and asymptotic normal inference. At the
primary exploratory lag 5, mean-IC p-values were 0.022841 (5D), 0.119045 (20D),
and 0.659158 (60D). The 5D 95% interval was [-0.024770, -0.001848]. For 5D,
lags 10 and 20 gave p=0.024688 and 0.028827. The nominal 0.05 threshold pattern
did not change across these three lag choices.

Paired daily differences were tested directly. Lag-5 p-values were 0.687849
(5D minus 20D), 0.204302 (5D minus 60D), and 0.219044 (20D minus 60D).
Every paired-difference interval included zero at all three lags; this does not
establish equivalence. All 126 numerical reference comparisons with statsmodels
passed. These are unadjusted exploratory p-values from 18 correlated tests and
an already investigated sample, not independent confirmatory evidence.

## Quantile forward-label description

The final experiment used 5D Momentum, five fixed framework quantiles, and
5-day labels with entry lag 1. All five groups had 1,751 valid signal dates:

| Quantile | Mean forward return |
|---|---:|
| Q1 (lowest Momentum) | 0.4479% |
| Q2 | 0.3934% |
| Q3 | 0.3450% |
| Q4 | 0.3082% |
| Q5 (highest Momentum) | 0.3093% |

Mean Q1 minus Q5 was 0.1386 percentage points per 5-day label; daily spread
std was 1.3689 percentage points and positive fraction 55.11%. Each group had
49–56 members/valid returns on included dates. Annual mean spreads were positive
in six years and negative in 2012. The means are not strictly monotonic across
all five groups. No spread significance test or cumulative strategy performance
was calculated, and the earlier IC HAC results do not supply spread inference.

## Exploration status and validation hand-off

These findings motivate a **post-exploration-selected** negative 5D Rank IC
hypothesis. It was not independently pre-specified before exploration and does
not supersede the original findings or prove that 5D is optimal. Multiple
comparisons, missing-history selection, a current-constituent universe, adjusted
price revisions and overlapping labels remain limitations. Positive label spreads
are not tradable returns or Alpha; costs, exposures and execution are unmodeled.

The next permissible experiment is the frozen 2017–2019 protocol in
[01_momentum_validation_protocol.md](01_momentum_validation_protocol.md), subject
to separate execution authorization. The 2020–2025 held-out period remains
untouched. No validation success or failure is claimed by this close-out.

Sources within the repository: `research/01_momentum.ipynb` (saved cells 5–12,
zero-based); [full report](01_momentum.md); and the saved `regime_2010_2016`,
`window_sensitivity_2010_2016`, `hac_2010_2016`, and `quantiles_2010_2016`
directories under `data/research/momentum_001/`. Numbers here are rounded summaries.
