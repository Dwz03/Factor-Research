# Momentum Factor #001: Alpha Signal Assessment

Assessment date: 2026-11-14 (Asia/Shanghai). **Provisional classification: Alpha Candidate**, specifically a short-horizon reversal candidate represented by negative 5D Momentum. Retain for further research; **not confirmed independent Alpha** and not approved for deployment.

This is a synthesis of existing verified evidence only. No new parameter search, statistical test, portfolio backtest, price analysis or held-out evaluation was performed. #001-A's frozen Final Held-Out Test Protocol v1.0.0 remains unchanged and unexecuted. This assessment does not authorize its execution.

## 1. Factor definition and economic hypotheses

The unchanged implementation is `factors.momentum.calculate_momentum`: M_L(t)=P[t]/P[t-L]-1, using adjusted Close and observed trading rows, without filling. The original implementation defaults to L=20; research subsequently examined fixed L=5,20,60. The retained candidate uses the already selected L=5, not a new formula or newly optimized window. Its evaluated target is R(t)=P[t+6]/P[t+1]-1: five trading-row returns with entry lag one after the signal-date close. Minimum cross-sectional paired assets: 100. The universe is the original frozen 300 securities.

Continuation is the natural directional hypothesis for raw Momentum: recent relative winners continue outperforming. Short-horizon reversal is the competing interpretation consistent with the observed negative relationship: recent relative losers subsequently outperform winners. Temporary price pressure, liquidity provision or overreaction are possible economic explanations, not mechanisms identified by this research. These explanations are assessment-level interpretations, not a claim that a causal mechanism was pre-specified or tested. The evidence does not support generalizing one direction to every lookback and horizon.

## 2. Direction and proposed signal orientation

For further research, orient the score as S(t)=-M_5(t), so higher scores favor recent losers. This is a proposed deterministic sign convention, not an implemented new factor or a portfolio rule. Reversing the sign reverses Spearman IC on the same sample and creates no additional evidence. Do not retrospectively replace stored raw-Momentum results, change frozen test hypotheses, or relabel the original negative-IC validation as a new positive-IC experiment. The original final protocol continues to test raw 5D Momentum mean Rank IC < 0.

## 3. Exploration and frozen temporal validation

| Evidence | Period | Mean raw Rank IC | Valid dates | Status |
|---|---|---:|---:|---|
| Original 20D analysis | 2010-2016 | -0.009835 | 1,736 | Exploration |
| Selected 5D analysis | 2010-2016 | -0.013475 | 1,751 | Exploration |
| Frozen 5D validation | 2017-2019 | -0.019493 | 748 | Recorded Pass |

The 5D negative hypothesis was selected after exploration, not independently pre-specified before it. The frozen validation's one-sided lower-tail HAC test used lag 5, Bartlett weights, n/(n-1) correction and asymptotic normal inference. Saved HAC SE=0.009887328, t=-1.971499421, p=0.024333390 and one-sided 95% upper bound=-0.003229654. It passed its fixed mean<0 and p<0.05 rule. This is meaningful evidence under that protocol and sample, not a universal or risk-adjusted Alpha certificate.

The #001-B and #001-C studies subsequently reused 2010-2019. Their 2017-2019 findings are post-validation exploration, not additional independent validations. Pooled evidence overlaps both subperiods and is not a third replication. Historical close-out documents describe the status at their own creation dates; the later saved validation record supplies the current status.

Sources: [exploration close-out](01_momentum_exploration_summary.md), [original report and validation record](01_momentum.md), [validation protocol](01_momentum_validation_protocol.md).

## 4. Lookback, horizon and stability characteristics

The fixed 5D/20D/60D exploration common-sample means at H=5 were -0.013309, -0.010709 and -0.003273. Existing paired HAC comparisons did not establish differences between these windows; 5D must not be called statistically superior or optimal.

In #001-B, available-sample 5D mean IC attenuated from -0.015404 at cumulative H=5 to -0.007776 at H=60 over 2010-2019. Incremental days 21-60 were approximately zero (-0.000262 available; +0.000425 common), although early intervals remained negative. In 2017-2019 the incremental 5D means were -0.019493, -0.005592, -0.010340 and +0.007287 for days 1-5, 6-10, 11-20 and 21-60. This is more consistent with a short-horizon association than a persistent negative effect across every future interval.

Longer lookbacks behave differently: in 2017-2019 60D Momentum had positive cumulative means at all four horizons; 20D changed sign at H=60. Such differences discourage interpreting all Momentum definitions as the same signal. Incremental and cumulative rank correlations are not additive.

Original 20D regime means were negative in both Bull (-0.007281; 1,474 dates) and Bear (-0.024208; 262 dates), with unequal samples and no regime-effect inference. Within-sector means had mixed signs. These describe heterogeneity, not permission to select sectors or regimes.

Sources: [horizon study](01B_momentum_horizon.md), [incremental supplement](01B_momentum_incremental.md), [original report](01_momentum.md).

## 5. Sector and historical volatility controls

#001-C fits transformations separately on each signal date using feature-complete stocks before future-return filtering. Realized volatility is the unannualized sample SD of complete trailing 20/60 daily simple returns. No present-day capitalization was used. Common samples recompute ranks on identical paired stocks and dates.

| Common-sample mean IC | 2010-2016 | 2017-2019 |
|---|---:|---:|
| Raw 5D | -0.013309 | -0.019328 |
| Sector-neutral | -0.014609 | -0.014901 |
| Sector + vol20 | -0.012791 | -0.016819 |
| Sector + vol60 | -0.011728 | -0.016686 |
| Sector + both | -0.011909 | -0.017188 |

Negative adjusted means remain under these specified controls. Joint-control daily raw-unit Momentum regression slopes average -0.013939 (SD 0.118943) and -0.026410 (SD 0.142629). Annual joint-control means were negative in nine of ten years; 2015 was positive (+0.002454). Both low- and high-volatility groups had negative subperiod mean ICs, descriptively more negative in the high-volatility groups.

This supports retaining a hypothesis of residual predictive information relative to these limited controls. It does not statistically establish incremental information: #001-C is descriptive, controls are incomplete, and neutralized Spearman IC and conditional linear regression coefficients measure different relationships. Regression specifications also have different complete-case samples. Small average Momentum-volatility correlations do not rule out large or time-varying exposure.

Source: [risk exposure study](01C_momentum_risk.md).

## 6. Quantile forward-return evidence

| Saved descriptive result | 2010-2016 | 2017-2019 |
|---|---:|---:|
| Valid dates | 1,751 | 748 |
| Q1 mean 5D label | 0.4479% | 0.4448% |
| Q5 mean 5D label | 0.3093% | 0.2745% |
| Q1 minus Q5 mean | 0.1386 percentage points | 0.1703 percentage points |
| Daily spread SD | 1.3689 percentage points | 1.4299 percentage points |
| Positive spread fraction | 55.11% | 54.55% |

Q1 contains lowest raw Momentum and Q5 highest. Membership precedes future-label deletion. The exploration quantile pattern is not strictly monotonic; annual spreads were negative in 2012. No spread significance test was performed, and IC inference cannot be transferred to spreads. These overlapping, equally weighted forward labels are neither executable long-short P&L nor cumulative performance. Positive individual quantile returns can reflect market exposure. Secondary validation evidence did not determine the primary Pass.

Source: [original quantile and validation sections](01_momentum.md).

## 7. Statistical uncertainty and research selection

The exploratory common-sample 5D two-sided HAC lag-5 p-value was 0.022841, with 95% interval [-0.024770,-0.001848]; lags 10/20 gave p=0.024688/0.028827. These are existing, unadjusted exploratory results. Eighteen correlated HAC comparisons, window exploration, sectors, regimes, quantiles, horizons, controls and repeated sample examination create multiplicity and selection concerns. No multiplicity-adjusted claim or new combined p-value is made here.

The single frozen validation Pass has stronger procedural separation than exploration, but retains universe/data biases and finite-sample approximation limits. Overlapping labels, persistent signals and shared stocks make consecutive daily observations dependent; lag-5 HAC is not a guarantee against longer dependence and was not automatically applied to longer horizons. Effect dispersion and yearly sign changes remain substantial. Reusing the same outcomes in #001-B/#001-C must not be counted as fresh corroboration with independent error rates.

## 8. Missing controls, data and implementation limits

Unmodeled historical exposures include market beta, size, value, profitability/quality, investment, liquidity, trading activity, idiosyncratic risk, industry detail and event/earnings effects. The evidence does not isolate these alternatives. Point-in-time historical data would be needed to evaluate them properly; present-day capitalization is not a substitute and was not added.

The frozen universe was selected from current constituents, not reconstructed historical membership. Survivorship and selection bias remain, as do missing delisted histories, IPO availability, retrospective corporate-action adjustments and vendor revisions. Sector labels are frozen current labels, not point-in-time historical classifications. No missing observations were filled; common samples nevertheless condition on availability. Price coverage is 87.91% in 2010-2016 and 92.85% in 2017-2019. #001-C common samples contain 1,696 and 748 dates, averaging 263.27 and 277.94 paired assets. Pre-2010 warm-up is absent from the snapshot; initial lookbacks remain undefined.

Transaction costs, bid-ask effects, turnover, execution delay, liquidity/capacity, short availability, borrow/financing and implementable portfolio risk constraints remain unassessed. A short-horizon association may be especially sensitive to these frictions, but their magnitude has not been measured here.

## 9. Evidence levels and provisional classification

| Claim | Assessment |
|---|---|
| Predictive association | Negative raw 5D Rank IC in exploration and the frozen validation; descriptive quantile evidence has consistent direction. |
| Incremental information | Residual negative association under sector and historical-volatility controls; limited descriptive support, not established independence from all risk exposures. |
| Tradable Alpha | Not established: no executable, cost-adjusted or comprehensive risk-adjusted performance evidence. |

**Decision: Alpha Candidate.** Retain the negatively oriented 5D signal for further research because the saved frozen validation passed, quantile evidence is directionally consistent, and descriptive associations remain under specified controls. This classification is a research-priority judgment, not an estimated probability of success, new test result or deployment recommendation. A Watchlist classification would understate the existing validation evidence; Reject is not supported by the current record. Neither comparison excuses the unresolved biases and uncertainty.

The candidate is short-horizon reversal, not a claim that conventional positive Momentum or any other window is superior. Do not choose a new interval, neutralization or subgroup based on this assessment. Future work would need a separately authorized, documented scope addressing risk/data quality and implementation feasibility. The already frozen [Final Test Protocol v1.0.0](01_momentum_final_test_protocol.md) must remain unchanged; its execution is outside this task. Any future assessment should preserve this dated record and explain changes rather than rewrite historical decisions.

## 10. Provenance and verification

This document was created from the linked reports and existing verified outputs only. Before and after writing, checks covered 136 final-freeze hash checks and 122 validation-lineage checks, the #001-B source/artifact manifest, its incremental supplement manifest, and all 47 #001-C manifest entries. The authorized historical validation report append is checked through its saved full-report hash and archived original prefix; no original seal was regenerated.

Raw market bytes may be hashed by integrity verification, but no 2020-2025 prices or outcomes were parsed or evaluated. No existing report, implementation, data file, protocol or manifest was modified. The prior recorded full suite passed 154 tests; no new computational code was introduced and this documentation-only task did not rerun research or statistical tests.
