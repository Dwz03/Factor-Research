# Factor Research

Reusable Python infrastructure for quantitative factor research. Factor hypotheses,
mathematical definitions, and interpretation belong to the researcher. This project
does not implement a trading strategy. The existing Momentum implementation is
unchanged: `prices.pct_change(periods=window, fill_method=None)`.

## Layout

```text
src/data/         Yahoo ingestion, validation, cleaning, and caching
src/evaluation/   Forward labels, IC, quantiles, and factor correlation
factors/          Individual factor construction (existing momentum.py)
research/         Individual notebooks; existing notebook and outputs retained
reports/          Report template and generated research reports
tests/            Offline automated tests, including original tests
config/           Explicit research configuration examples
data/raw/         Ignored vendor responses
data/processed/   Ignored Close-price panels and cache metadata
```

## Setup

Use Python 3.12 (the tested local interpreter), create a virtual environment, then
run `python -m pip install -r requirements.txt` from the repository root.
`requirements.txt` lists the runtime, test, and notebook dependencies used by the
repository, pinned to the existing environment. Unused plotting and machine-learning
dependencies and the redundant full environment snapshot have been removed;
installed packages in the local virtual environment are unchanged.
Dependency installation in a fresh environment has not been verified.

Run `python -m pytest -q`. All tests use synthetic data and block live Yahoo
downloads. If an existing `.pytest_cache` is inaccessible, use
`python -m pytest -q -p no:cacheprovider`.

Use `from src.data import download_prices, clean_prices`; the redundant top-level
compatibility wrappers have been removed and repository imports migrated.
The original notebook keeps its
saved results and now discovers the repository root when launched from the root
or a subdirectory. No notebooks are automatically executed.

## Data contract

```python
from src.data import download_prices, clean_prices

# Explicit network action; only run when you intend to download:
# prices = download_prices(tickers, start, end, auto_adjust=True)
```

Yahoo daily `Close` is selected; `auto_adjust=True` preserves the original behavior.
With `False`, the selected field is unadjusted Close, not Adj Close. Start is
inclusive and end exclusive. Explicit dates are required. Returned panels have
sorted, unique, timezone-naive dates as rows and canonical uppercase ticker names
as columns. Relative cache paths always resolve against the repository root,
regardless of the notebook working directory.

The loader rejects empty responses, missing or wholly missing assets, duplicate
dates, unsorted timestamps, infinities, nonnumeric values, and nonpositive prices
before caching. Partial missing observations generate a warning and remain NaN.
The separate `clean_prices` utility copies and sorts a panel, rejects duplicates,
and converts nonnumeric, infinite, and nonpositive observations to NaN. It never
forward-fills. Generic indexes are accepted by this legacy cleaning API only;
ingestion and evaluation require a DatetimeIndex. Neither module invents missing
trading sessions, nor can it infer whether an absent endpoint is a holiday or a
vendor omission. Inspect coverage before research.

Cache filenames hash a versioned specification including sorted universe, date
range, source, daily interval, selected field, and adjustment setting. Raw vendor
fields and processed Close panels are stored separately. Metadata records the
request, UTC retrieval time, yfinance version, and both file checksums. Cache reads
verify metadata, checksums, and panel validity. Partial writes cannot pass those
checks. Concurrent writers to the same cache are not supported; use separate cache
directories for concurrent jobs. CSVs and metadata are local artifacts, not a
point-in-time market database.

Legacy `cache_path` still selects a processed CSV location, but it now requires
matching metadata. Incompatible, damaged, or unversioned caches raise `CacheError`;
choose a new path or explicitly use `refresh=True` to replace the requested cache.
Existing `research/data/raw/prices.csv` is preserved and is not silently reused.
Default new caches use root `data/`. No data migration or download ran during this
refactor. A valid cache is reused until explicitly refreshed.

Keep Hiddify proxy settings in `HTTPS_PROXY` (or `https_proxy`) in the process
environment or root `.env`. The root `.env` is loaded without overriding process
variables, and the proxy is passed to yfinance's network configuration. No proxy
address or credentials belong in code, reports, or configurations. `.env`, virtual
environments, and datasets (including notebook-relative data) are ignored by Git.

### Yahoo Finance limitations

Yahoo snapshots are not guaranteed point-in-time data. Historical adjustments and
vendor corrections can revise earlier observations. Corporate-action adjustments
must be inspected; adjusted prices alone do not establish executable returns.
Current ticker lists introduce survivorship/selection bias and may omit delisted
securities. Symbol changes, incomplete histories, differing exchange calendars,
timezone conventions, outages, and partial responses require researcher review.
The loader validates structure and observed values, not completeness or economic
correctness. Retain retrieval metadata and independently verify data for rigorous
historical research. There is no built-in historical universe or publication-time
database.

## Evaluation conventions

All evaluation inputs are numeric wide panels: unique sorted timezone-naive dates
by unique asset labels. NaNs are allowed; infinities are rejected. Functions do not
mutate inputs, fill prices, or implicitly shift signals. Factors at date t must be
available at the researcher's stated signal time.

```python
from factors.momentum import calculate_momentum
from src.evaluation import (
    forward_returns, pearson_ic, rank_ic, ic_summary,
    quantile_returns, factor_correlations,
)

# Given an already loaded and validated prices panel:
# factor = calculate_momentum(prices, window=20)
# labels = forward_returns(prices, horizon=5, entry_lag=1)
# ic = pearson_ic(factor, labels)
# rank = rank_ic(factor, labels)
# stats = ic_summary(ic)
# by_date, summary = quantile_returns(factor, labels, quantiles=5)
```

Forward labels at t are `P[t + entry_lag + horizon] / P[t + entry_lag] - 1`.
Horizon and lag count observed panel rows, not calendar days. Default lag 1 places
the entry observation after a close-time signal; explicit lag 0 is a same-close
descriptive convention. Missing endpoints and insufficient future rows produce
NaN; intermediate missing observations do not change an endpoint return.

Pearson IC and Spearman Rank IC align labels by date and asset to the factor panel,
exclude missing pairs, and retain factor dates. No shared dates or assets is an
error. Sections with fewer than `min_assets` (default 3), or zero variance in either
variable, yield NaN. Spearman ranks the paired sample using average ranks for ties.
`ic_summary` excludes NaNs and returns count, mean, sample standard deviation,
positive fraction, and unannualized ICIR = mean / sample standard deviation.
Undefined ICIR is NaN. No iid significance or annualized inference is implied.

Quantile membership uses only same-date factor values. Average-rank percentile
midpoints assign bins from low (1) to high (Q). Ties stay together, so bins can be
empty; constant sections or fewer than Q observations are unassigned. Missing
labels do not change membership. `quantile_returns` returns date/bin means with
valid-label and membership counts, then equally averages valid date means. These
are descriptive forward outcomes, not executable portfolio returns: overlapping
labels must not be compounded into performance, and create serial dependence.

`factor_correlations` accepts a mapping of factor names to panels and returns
per-date pairwise cross-sectional correlations and an equal-date average matrix.
Default method is Spearman; Pearson is available. Missing pairs, minimum counts,
and zero variance use the same rules as IC. It does not pool observations across
time or alter factor timing.

## Reports

Copy `reports/TEMPLATE.md` for each study. Fill the hypothesis, mathematical
construction, methodology, IC/Rank IC, quantile analysis, limitations, and conclusion
yourself. Record the cache identity, configuration, timing choices, coverage, and
software versions. The framework produces no research interpretation automatically.
