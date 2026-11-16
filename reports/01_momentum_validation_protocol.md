# Momentum Research #001 — Frozen Validation Protocol v1.0.0

Frozen 2026-11-13, Asia/Shanghai. **Status: frozen, not executed.** Machine-readable
authority: `config/momentum_001_validation.json`. Integrity seal:
`config/momentum_001_validation.lock.json`. Exploration close-out:
[01_momentum_exploration_summary.md](01_momentum_exploration_summary.md).

## Selection provenance and boundaries

The 5D negative-IC hypothesis was selected from the completed 2010–2016
exploration, including window comparisons. It was NOT independently pre-specified
before exploration. This protocol fixes one subsequent temporal validation test;
it does not retroactively turn exploratory p-values into confirmatory evidence.
No 2017–2019 IC/quantile results were inspected to create it. No 2017–2025 factor
evaluation is authorized or performed by this freeze task.

- Validation signal dates: 2017-01-01 through 2019-12-31 inclusive.
- Held out: 2020-01-01 through 2025-12-31, untouched; do not load/evaluate its
  outcomes or use its prices to complete validation labels.
- Use the existing frozen 300-security universe and adjusted Yahoo price snapshot.
  Keep all universe columns, including wholly missing histories; no replacements,
  current reconstitution, refresh, or availability-based universe selection.
- Freeze source bytes by SHA-256. Hashing the full existing price file is a
  byte-integrity operation only; it does not inspect or evaluate later outcomes.

## Timing and missing-data contract

On later authorized execution, select only price rows in validation plus the
**five immediately preceding observed trading rows** before 2017-01-01 from the
same frozen matrix. These pre-validation rows are factor-price warm-up only:
no returns, ICs or quantile outcomes from them enter validation summaries.
Compute the factor over this bounded panel and then select validation signal
dates. Do not drop missing rows before shifts, invent sessions or import 2020
prices. Sorted unique naive dates and unique ticker labels are required.

Factor: existing `calculate_momentum(prices, window=5)`, P[t]/P[t-5]-1,
fill_method=None. Target: `forward_returns(prices, horizon=5, entry_lag=1)`,
P[t+6]/P[t+1]-1. Units are observed trading rows, not calendar days. Both entry
and exit must be within validation; exclude the final six signal rows if their
endpoints exceed the boundary. The current close is available at the signal
close, and entry is the next row. No sector neutralization or market-regime filter.

Missing endpoints give missing factors/labels; never forward-fill. Endpoint
formulas do not require intermediate prices to be present. Observed prices must
be positive and finite. Reject structural/price validation failures rather than
silently cleaning or altering the frozen data. Record missingness, counts and all
excluded signal dates with reasons.

## Primary outcome and inference

Primary metric: equally weighted mean of daily cross-sectional Spearman Rank IC.
Use `rank_ic` with min_assets=100 and pairwise observed factors/labels. Average
ranks handle ties. Fewer than 100 pairs or zero variance yields missing IC.
There is only one window, so the earlier three-window common-sample intersection
is NOT imposed. Use every eligible validation date under these fixed conventions.

H0: mean Rank IC >= 0; H1: mean Rank IC < 0. Test the boundary null of zero.
Primary HAC lag: **5**, Bartlett weights w[j]=1-j/6 for j=1..5. Use the frozen
`hac_mean` covariance and t-ratio, with correction n/(n-1) for intercept-only
OLS. For demeaned residuals u:

`Var(mean) = [sum(u²) + 2 sum(j=1..5) w[j] sum(t=j+1..n) u[t]u[t-j]] / n² * n/(n-1)`.

Inference is asymptotic standard normal. **One-sided lower-tail p = norm.cdf(t)**,
where t = mean/HAC_SE. The existing `hac_mean` returns a TWO-SIDED p-value;
do not use it directly for this protocol, and do not blindly divide it by two.
At positive t the lower-tail p exceeds 0.5. Report a 95% one-sided upper bound
`mean + norm.ppf(0.95)*HAC_SE`; a two-sided 95% interval may be included for
context but does not determine the primary decision.

HAC lags refer to consecutive retained trading rows. Jointly trim only leading
and trailing undefined-IC rows; if any undefined IC occurs inside the remaining
sample, **stop and classify the run as inconclusive due to data/inference
ineligibility**. Do not compress gaps, impute IC, reduce min_assets or choose a
different lag. Require n>5, finite positive HAC_SE and a finite valid p-value.
Failure of any check is inconclusive, never a pass or an automatic rejection of
the economic hypothesis. Record all trimming and the resulting sample length.

## Decision rules fixed before execution

1. Verify the seal, source/implementation hashes and recorded package versions.
   A mismatch blocks evaluation; never regenerate the seal automatically.
2. If any structural, eligibility or covariance check fails, record an inconclusive
   validation run with diagnostics and stop. Do not inspect held-out outcomes.
3. Otherwise, primary directional validation passes only if mean IC < 0 AND
   lower-tail p < 0.05. At p=0.05 it does not pass. Equivalently the one-sided
   95% upper bound is below zero (allow only numerical roundoff consistency).
4. Any other eligible result is “primary hypothesis not supported at the frozen
   0.05 level,” not proof that the effect is zero or reversed.
5. Report effect size, count, HAC SE, t-ratio, lower-tail p, upper bound and coverage
   regardless of outcome. No optional stopping or repeated tests on revised data.
6. No lag/window/regime/sector searches, adaptive universe changes, or alternative
   primary metrics. No additional validation tests or HAC bandwidth sensitivities
   are part of this protocol. The secondary result cannot rescue or overturn the
   primary decision. Passing does not authorize a held-out test or live strategy.

## Secondary descriptive outcome

Mean Q1 minus Q5 forward-return spread with five groups from the existing
`quantile_groups`/`quantile_returns`. Q1 is lowest 5D Momentum, Q5 highest.
Membership uses signal-date factor values before observing future labels;
average-rank percentile midpoints keep ties together. Fewer than five observed
factors or constant cross sections are unassigned. A group requires at least one
valid return; an empty group has NaN, not zero. No new group-size cutoff.

Equal-weight valid labels within each preassigned group, then equal-weight dates.
Q1 minus Q5 requires both means on the same date. Use all eligible spread dates;
do not force the IC-specific 100-asset threshold or IC-valid-date filter onto this
secondary descriptive sample. Report both sample counts, membership and valid
return counts, mean spread, sample std and positive fraction. No secondary
p-value or success criterion is registered, and it cannot determine primary success.
Do not compound overlapping labels or call them executable portfolio returns.

## Reproducibility and amendment policy

The JSON records the protocol ID, Git HEAD, working-tree status, Python/package
versions and SHA-256 hashes of the data, universe, existing implementations and
exploratory evidence. Git HEAD alone is insufficient because relevant work is
uncommitted. A local byte-for-byte source snapshot under
`data/protocols/momentum_001_validation_v1/` preserves the exact implementations.
The lock manifest seals both the JSON and this document, plus the close-out summary.
This is a local integrity seal, not a third-party timestamp or immutable storage.

Verify offline using `python -B scripts/verify_momentum_001_validation.py`.
The verifier hashes files and checks environment versions only; it imports no
factor/evaluation code and computes no research outcomes. A validation execution
driver is intentionally not created in this task. A later authorized driver must
wire the frozen primitives exactly as above and pass synthetic timing and tail
tests before observing validation results; record its code hash in the execution
record without rewriting this protocol or its original seal.

Preserve this v1.0.0 snapshot. Any necessary amendment needs a new version with
reason and timing recorded before evaluation; no outcome-driven amendment counts
as the original frozen test. Retain original inputs, results and both versions.

## Research limitations

HAC handles weighted serial covariance, not survivorship, vendor revisions,
changing availability, nonstationarity, or arbitrary long dependence. The frozen
current-constituent universe was selected in 2026 and is not a point-in-time
historical universe. Temporal validation therefore remains subject to selection
bias even when outcomes are uninspected. The negative direction and 5D window
are post-exploration choices; multiplicity in exploration is not erased. The
one primary test has no adjustment for additional primary hypotheses because
none are authorized. Secondary descriptions are not separate confirmatory claims.
No portfolio backtesting, tradable-return claims or Alpha claims are part of this protocol.
