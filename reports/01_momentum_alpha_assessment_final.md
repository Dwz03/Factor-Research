# Momentum Factor #001: Final Research Assessment

Closed on 2026-11-14 (Asia/Shanghai).

**Final classification: Watchlist — Mixed Temporal Evidence. Research status: Closed.**

This is a new post-test archival interpretation of existing records. It preserves the dated [pre-test Alpha Candidate assessment](01_momentum_alpha_assessment.md), all prior research and the exact final-test decision **Not Supported**. Research completion does not imply statistical validation success. No hypothesis was revised and no test was repeated.

## Definition and investigated orientation

The original unchanged Momentum implementation is M_L(t)=P[t]/P[t-L]-1, using adjusted Close without filling missing values; its original default was 20D. The investigated candidate and frozen validation/final test use L=5: P[t]/P[t-5]-1. The proposed negative orientation S=-M_5 describes short-horizon reversal: recent relative losers receive higher scores. It is not a changed frozen factor or a newly validated signal. The frozen tests retain raw Momentum and the alternative mean Rank IC < 0.

The target is P[t+6]/P[t+1]-1, five observed trading rows with entry lag one. The original frozen 300-security universe and market snapshot are preserved. At least 100 paired assets per date are required. Signals use available close-time information; forward endpoints must remain inside the named analysis period.

## Evidence chronology

| Stage | Period | Mean raw 5D Rank IC | Valid dates | Evidence status |
|---|---|---:|---:|---|
| Exploration | 2010-2016 | -0.013475 | 1,751 | Selected negative 5D hypothesis after exploration |
| Frozen validation | 2017-2019 | -0.019493 | 748 | Pass |
| Single frozen final held-out test | 2020-2025 | -0.007305375 | 1,502 | Not Supported |

Exploratory common-sample two-sided HAC lag-5 p=0.022841 was unadjusted and affected by research selection. The frozen validation passed its lower-tail test (p=0.024333390; upper one-sided 95% bound=-0.003229654). Neither is erased by the final result. Conversely, their favorable outcomes do not override the final protocol. #001-B and #001-C reused 2010-2019 after validation; they are not additional independent validations.

Sources: [exploration close-out](01_momentum_exploration_summary.md), [original research and validation](01_momentum.md), [final execution report](01_momentum_final_test_results.md).

## Final primary outcome, unchanged

| Metric | Recorded value |
|---|---:|
| Valid IC observations | 1502 |
| Mean Rank IC | -0.007305374754399302 |
| HAC standard error | 0.008403280409157152 |
| t-statistic | -0.8693479687335616 |
| One-sided lower-tail p-value | 0.19232841654620408 |
| One-sided 95% upper confidence bound | 0.00651679150489309 |
| Frozen decision | Not Supported |

HAC lag 5, Bartlett weights, n/(n-1) covariance correction and asymptotic normal lower-tail inference were fixed in advance. H0: mean IC >= 0; H1: mean IC < 0; alpha=0.05. The p-value exceeds 0.05 and the upper bound exceeds zero. The predefined evidence standard for retaining this as a robust predictive candidate was not met. Failure to reject the null does not prove a zero effect, establish equivalence, or prove that the relationship reversed. The mean remains negative, with material uncertainty. No new inference is performed here.

Exactly five pre-2020 rows supplied factor warm-up. There were 1,508 final-period price rows and six terminal endpoint exclusions. Valid signal dates ran from 2020-01-02 through 2025-12-22. All 300 columns remained; FDXF and HONA lacked final-period observations.

## Secondary quantile evidence

Final mean forward labels for Q1 through Q5 were 0.480656%, 0.305817%, 0.292038%, 0.299589% and 0.380504%. Q1 is lowest raw Momentum. Q1 minus Q5 averaged **0.100152 percentage points**; daily spread SD was **2.909320 percentage points**; positive fraction was **49.8668%**, across 1,502 dates. These are descriptive overlapping forward labels, not executable portfolio returns. The profile is not strictly monotonic. Any interpretation of this shape as nonlinearity is a **post-test observation, not confirmatory evidence**; no nonlinear specification is proposed or fitted.

Earlier mean Q1-Q5 spreads were 0.1386 percentage points in exploration and 0.1703 percentage points in validation. Their positive direction does not rescue the failed final primary threshold. No spread significance inference was conducted or borrowed from IC tests.

## Horizon dependence and limited-control evidence

[The horizon study](01B_momentum_horizon.md) and [incremental supplement](01B_momentum_incremental.md) describe shorter-lived negative 5D associations in the already-seen sample. Pooled 2010-2019 incremental days 21-60 were near zero (-0.000262 available, +0.000425 common), while early intervals remained negative. In 2017-2019, 5D incremental days 21-60 were positive (+0.007287). Longer lookbacks had different signs. These findings do not establish an optimal window or authorize a replacement hypothesis.

[The risk-control study](01C_momentum_risk.md) found common-sample sector-plus-vol20/vol60-adjusted mean IC of -0.011909 in 2010-2016 and -0.017188 in 2017-2019. Joint-control conditional linear Momentum slopes averaged -0.013939 and -0.026410; annual means were negative in nine of ten years, with 2015 positive. These descriptive associations suggest residual information relative to those controls only. Conditional linear slopes and Spearman IC answer different questions; neither establishes independence from omitted risk exposures or causality.

Earlier 20D Bull/Bear descriptions had unequal sample counts and no regime-effect inference. Any attribution of the final outcome to changing regimes, nonlinearity or exposure shifts would now be a **post-test interpretation**, not confirmatory evidence. No new regime, horizon, control or subgroup analysis was run for closure.

## Uncertainty and limits

Exploratory window choices, correlated tests, repeated sample examination, regimes, sectors, quantiles, horizons and controls create multiple-comparison and selection concerns. The predeclared final test is not retroactively adjusted or replaced. Serial dependence from overlapping labels, persistent features and shared securities makes consecutive observations non-independent; lag-5 HAC does not guarantee protection against longer dependence.

The universe uses current constituents rather than historical membership: survivorship, selection bias, IPO availability and missing delisted histories remain. Frozen sector labels are present-day classifications, not point-in-time sectors. Vendor revisions, corporate-action adjustments, missing-data selection and absent pre-2010 warm-up also limit interpretation. Historical beta, size, value, quality, liquidity and event exposures were not comprehensively controlled. No present-day capitalization was introduced as a historical control.

Predictive association is not synonymous with incremental information, and neither is tradable Alpha. Execution, turnover, transaction costs, capacity, liquidity, short availability, financing and implementable portfolio risk were not tested. No return series was compounded as a strategy.

## Closure decision and preservation

**Watchlist — Mixed Temporal Evidence** retains the historical evidence and unresolved possibility of an effect without treating the predefined final evidence standard as satisfied. The pre-test Alpha Candidate classification remains an unchanged historical record; this separate dated decision is the current library classification. **Closed** describes completion of the authorized research sequence, not success at every statistical gate. No confirmed independent Alpha or deployment readiness is claimed.

The original final test is closed to reruns, tuning or resealing. Any future work would require a separate explicit scope and must disclose that 2020-2025 is now seen; this archive authorizes none and does not start Factor #002.

See the [Factor Library](FACTOR_LIBRARY.md), [machine-readable record](../config/factor_library/001_momentum.json) and [archive verification receipt](archive/momentum_001/closure_integrity.json). All source references and original execution hashes are retained in the record/receipt. Local data artifacts remain Git-ignored and must be retained for full verification.

Verification uses hashes, saved records and existing integrity checks only. The historical verifier prints a hardcoded preparation-status phrase saying the final test is not executed; that phrase is not current execution status. The unchanged exclusive execution marker and saved result are authoritative: the test was executed once. The original verification code and seals are preserved rather than rewritten to change that wording.
