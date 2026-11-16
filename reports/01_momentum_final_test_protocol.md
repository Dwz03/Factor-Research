# Momentum Research #001 — Final Held-Out Test Protocol v1.0.0

Frozen on 2026-11-13 (Asia/Shanghai). **Frozen, not executed.** Authority:
`config/momentum_001_final_test.json`; integrity seal:
`config/momentum_001_final_test.lock.json`. No final-period market outcomes were
inspected or calculated to prepare this protocol. Byte hashing of the existing
price file is an integrity operation, not inspection of its outcomes.

## Transition from exploration and validation

The negative 5D hypothesis was selected after 2010–2016 exploration, not
independently pre-specified before it. The single frozen 2017–2019 validation
subsequently passed: 748 IC observations, mean -0.019492862, HAC SE 0.009887328,
t=-1.971499421, lower-tail p=0.024333390, upper one-sided 95% bound -0.003229654.
These are the existing saved results, not a new evaluation. Secondary spreads
did not determine validation success. The transition now freezes a final temporal
test of the same directional hypothesis without changing any parameters.

The original validation JSON, seal, execution marker, preflight evidence, driver
snapshot and every result artifact are preserved. The validation report append
is accounted for by its recorded full-report hash and its exact archived original
report/prefix. The original verifier and original integrity seal are not amended.
The separate final-test verifier checks this recorded lineage explicitly.

## Fixed sample, factor and label

- Final test signal dates: **2020-01-01 through 2025-12-31 inclusive**.
- Original frozen 300-security universe and original adjusted Yahoo Close matrix;
  require exact hashes. No refresh, ticker substitutions, universe reconstitution,
  removal of wholly missing columns or ex-post eligibility-based universe selection.
- Factor: existing `calculate_momentum(prices, window=5)`, P[t]/P[t-5]-1,
  fill_method=None. No neutralization, inversion or regime filtering.
- Target: existing `forward_returns(..., horizon=5, entry_lag=1)`,
  P[t+6]/P[t+1]-1, using observed trading rows, not calendar days.
- Primary outcome: equally weighted mean daily cross-sectional Spearman Rank IC;
  at least **100** observed factor/return pairs per date, average ranks for ties.
  No three-window common-sample restriction.

For a later authorized run, retain **exactly the last five observed price rows
before 2020-01-01** from the same frozen panel, plus final-period rows through
2025-12-31. These five rows are factor-price warm-up only. Compute factors using
the bounded panel, then select final-test signal dates. Construct labels on the
final-period price panel only. Both entry and exit dates must lie within the
final period. The final six rows cannot enter endpoint-valid summaries. Do not
load 2026 prices to complete labels. Signal values are known after the signal
close and entry is the next observed row.

Preserve the observed row grid before shifts; do not invent sessions or remove
missing rows. Missing endpoints produce missing factors/labels. Never forward-fill
or interpolate. The original endpoint formulas do not require every intermediate
price to exist. Reject invalid observed prices (nonpositive/nonfinite) and invalid
index structure rather than silently cleaning frozen inputs. Record per-date
pair counts, coverage and every exclusion reason; retain all 300 columns.

## Primary inference and decisions fixed before outcomes

H0: mean IC >= 0. H1: mean IC < 0. One-sided lower-tail Newey–West HAC with
**lag 5**, Bartlett weights w[j]=1-j/6 for j=1..5 and the **n/(n-1)** correction
for intercept-only OLS. Demean residuals; autocovariance products use denominator
n, not n-j. No automatic bandwidth, annualization or additional lag sensitivity.

`Var(mean) = [sum(u²) + 2 sum(j=1..5) w[j] sum(t=j+1..n) u[t]u[t-j]] / n² * n/(n-1)`.

Reuse `hac_mean` for covariance, HAC SE and t=mean/SE. The reference distribution
is asymptotic standard normal, not an exact finite-sample Student-t distribution.
The primary p-value is **norm.cdf(t)**, not the function's existing two-sided
p-value and not always half of it. Report the one-sided 95% upper bound
mean + norm.ppf(0.95)*SE. Any two-sided interval is context only.

1. Verify the new seal, data, source and environment versions, validation lineage,
   and a newly tested execution driver before loading real final-test values.
   If verification fails, stop without outcomes; never regenerate a lock automatically.
2. Require n>5 and finite positive HAC SE, finite t/p/bound. Leading/trailing
   undefined IC rows may be trimmed and recorded. **Any interior undefined IC
   makes the run Inconclusive**; no gap compression, imputation or lag changes.
3. **Pass:** eligible result with mean IC < 0 AND lower-tail p < 0.05. Equivalently,
   the one-sided 95% upper bound is below zero, subject only to numerical roundoff.
4. **Not Supported:** eligible result not meeting that conjunction. At p=0.05 it
   does not pass. This does not prove a zero effect or the opposite hypothesis.
5. **Inconclusive:** any integrity, structural, sample-eligibility, internal-gap,
   n<=5 or nonpositive/nonfinite covariance/inference failure. Stop rather than
   modifying the specification. Do not evaluate secondary outcomes after a
   primary eligibility failure.

The outcome must be reported regardless of direction. No sequential peeking,
optional stopping, outcome-driven reruns, window/lag/threshold tuning, sector
subtests or alternative primary outcomes. The final run is a single fixed test;
passing does not authorize portfolio deployment, backtesting or a new search.

## Secondary description, with no override of the primary outcome

Five cross-sectional groups using the existing `quantile_groups` and
`quantile_returns`: Q1 lowest 5D Momentum, Q5 highest. Fixed grouping formula:
floor((average_rank-0.5)/observed_factor_count*5)+1. Ties stay together; constant
cross sections or fewer than five observed factors remain unassigned. Determine
membership before excluding missing future labels. No alternative grouping rule.

Group means equally weight observed returns within preassigned members. At least
one valid return per group is required; empty groups yield NaN, not zero.
Q1 minus Q5 uses only dates with both means. Equally weight these daily spreads.
Do not impose primary IC eligibility or min_assets=100 on this descriptive sample.
Report group means, sample counts, membership/valid-return counts, mean spread,
sample standard deviation (ddof=1), and strictly positive-spread fraction.
No secondary significance test, success rule or power to rescue/overturn the
primary decision. Never compound overlapping labels into cumulative performance.

## Implementations, test conditions and execution boundary

The frozen primitives and validation pure computation helpers are reused without
modifying their originals. `execute_momentum_001_validation.py` helpers accept a
configuration argument but read its historical `periods.validation` slot. A later
final-test driver may map `periods.final_test` to that slot **in an in-memory copy
only** and call `load_bounded_prices`, `evaluate`, `assess_ic` and `decision`.
The final JSON and original validation JSON must never be changed by that adapter.
Do not call the original validation `execute()`/`preflight()` wrappers; they own
the validation paths and single-use marker. New final execution paths and a new
exclusive marker are required, and the new driver must record its own hash.

No final execution driver or real final-period outcome artifacts are created by
this preparation task. New synthetic tests exercise timing, exact five-row
warm-up, no post-boundary endpoints, missing-data behavior, rank alignment,
lower-tail HAC and Pass/Not Supported/Inconclusive rules with generated prices
only. Existing regression tests are also required. Before a later real run,
rerun the full offline suite, require zero failures/errors/skips, verify the
tested driver hash, then claim a single-use execution marker before any real
outcomes. A failed/partial attempt retains its marker and requires explicit review,
not automatic retry. No test or verifier in this task reads real final IC/quantiles.

The JSON records source hashes, Python/package versions, Git HEAD plus dirty-tree
status, implementation-manifest hash, original data/universe hashes, and validation
transition references. A separate local source snapshot and preparation test
evidence live under `data/protocols/momentum_001_final_test_v1/`. The seal hashes
the JSON, this document and preparation test evidence. This is a local integrity
seal, not a trusted external timestamp. It must not be silently regenerated.

Verify using `python -B scripts/verify_momentum_001_final_test.py`. This command
checks bytes, versions and saved validation provenance only; it cannot execute
factor evaluation. Preparation does not authorize final execution: wait for a
separate explicit request. Preserve v1.0.0; any necessary pre-outcome amendment
must be a separately documented version, never a retroactive rewrite.

## Interpretation limits

This final test assesses persistence of the same negative cross-sectional
relationship over a later period. The window and direction were selected during
exploration and retained after successful validation. No new hypothesis family
or multiple-look procedure is introduced; there is one registered final primary
test and a descriptive secondary outcome. Exploration's multiple comparisons
are not erased by this freeze.

Overlapping labels and shared securities induce dependence; lag-5 HAC is not a
guarantee under longer memory or structural breaks. Current 2026 constituents
were used to construct the universe, so historical survivorship/selection bias
persists even though final outcomes have not been inspected. Retrospective
adjustments, vendor revisions, changing availability and missing endpoints remain.
No costs, execution, liquidity, financing, risk adjustment or portfolio returns
are modeled. A Pass would not by itself establish tradable Alpha.
