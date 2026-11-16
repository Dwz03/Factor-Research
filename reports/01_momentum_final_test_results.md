# Momentum #001-A: Final Held-Out Test v1.0.0 Results

Single execution of the unchanged frozen 2020-2025 protocol. This is final-test evidence, distinct from exploration and 2017-2019 validation. No Factor Library classification is finalized here; review is pending.

## Primary

| index | value |
| --- | --- |
| decision | Not Supported |
| reason | Frozen primary lower-tail rule applied |
| valid_ic_observations | 1502 |
| mean_rank_ic | -0.007305375 |
| hac_se | 0.008403280 |
| t_stat | -0.869347969 |
| one_sided_p | 0.192328417 |
| one_sided_upper_95 | 0.006516792 |
| leading_trim | 0 |
| trailing_trim | 6 |
| first_signal | 2020-01-02 |
| last_signal | 2025-12-22 |

HAC lag 5, Bartlett kernel, n/(n-1) correction, asymptotic standard normal lower tail; p=norm.cdf(mean/SE), upper95=mean+norm.ppf(.95)*SE. Pass requires eligible mean<0 and p<.05. Secondary results cannot override this decision.

## Secondary descriptive results

| index | value |
| --- | --- |
| valid_dates | 1502.000000000 |
| mean_spread | 0.001001520 |
| std_spread | 0.029093199 |
| positive_fraction | 0.498668442 |

| quantile | mean_return | dates | observations | membership_total | members_min | members_mean | members_max | valid_returns_min | valid_returns_mean | valid_returns_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.004806556 | 1502 | 87375 | 87375 | 56 | 58.172436751 | 60 | 56 | 58.172436751 | 60 |
| 2 | 0.003058170 | 1502 | 87627 | 87627 | 56 | 58.340213049 | 60 | 56 | 58.340213049 | 60 |
| 3 | 0.002920379 | 1502 | 87751 | 87751 | 57 | 58.422769640 | 60 | 57 | 58.422769640 | 60 |
| 4 | 0.002995887 | 1502 | 87626 | 87626 | 56 | 58.339547270 | 60 | 56 | 58.339547270 | 60 |
| 5 | 0.003805036 | 1502 | 87376 | 87376 | 57 | 58.173102530 | 60 | 57 | 58.173102530 | 60 |

All returns are decimal fractions. Q1 is lowest raw Momentum; Q5 highest. Membership uses factor values before label exclusions. Full daily membership and valid-return counts are saved. No spread inference or portfolio performance is claimed.

## Execution and limitations

Coverage: `{"warmup_dates": ["2019-12-24", "2019-12-26", "2019-12-27", "2019-12-30", "2019-12-31"], "securities": 300, "final_period_rows": 1508, "last_price_date": "2025-12-31", "entirely_missing_symbols": ["FDXF", "HONA"], "exclusions": {"": 1502, "forward_endpoint_outside_final_test": 6}}`. Tests: `{"tests": 159, "failures": 0, "errors": 0, "skipped": 0}`. Driver SHA-256: `989bbf51c0be199e09f6b387e62562b5231e091c79a9f974f3501be9a5547391`.

Exactly five preceding observed rows warm factors; endpoints stay within the final period. Exclusive started.json, tested driver snapshot, preflight evidence, result and audit tables are retained under data/final_test/momentum_001_v1. Original reports, protocols, seals and pre-test assessment remain unchanged. No reruns or tuning are permitted. Current-constituent survivorship bias, current sector labels, vendor adjustments, missing history and serial dependence remain limitations. Lag-5 HAC does not guarantee protection against longer dependence. No costs, liquidity, implementation, portfolio backtest or comprehensive risk-adjusted Alpha is modeled. The final classification awaits review.
