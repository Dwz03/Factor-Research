"""Date-by-asset descriptive factor evaluation; no portfolio simulation."""
from .core import (
    forward_returns, cross_sectional_ic, pearson_ic, rank_ic, ic_summary,
    quantile_groups, quantile_returns, factor_correlations,
)

__all__ = ['forward_returns', 'cross_sectional_ic', 'pearson_ic', 'rank_ic',
           'ic_summary', 'quantile_groups', 'quantile_returns', 'factor_correlations']
