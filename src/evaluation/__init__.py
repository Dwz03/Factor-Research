"""Date-by-asset descriptive factor evaluation; no portfolio simulation."""
from .regimes import market_trend_regime
from .inference import hac_mean
from .core import (
    forward_returns, cross_sectional_ic, pearson_ic, rank_ic, ic_summary,
    quantile_groups, quantile_returns, factor_correlations,
)

__all__ = ['forward_returns', 'cross_sectional_ic', 'pearson_ic', 'rank_ic',
           'ic_summary', 'quantile_groups', 'quantile_returns', 'factor_correlations',
           'market_trend_regime', 'hac_mean']
