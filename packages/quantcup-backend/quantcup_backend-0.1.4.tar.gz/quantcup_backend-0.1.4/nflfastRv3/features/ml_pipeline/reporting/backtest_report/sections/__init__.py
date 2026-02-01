"""
Backtest Report Section Generators

Modular section generators for backtest reports.
"""

from .summary import SummarySectionGenerator
from .results import ResultsSectionGenerator
from .trends import TrendsSectionGenerator
from .stability import StabilitySectionGenerator
from .statistics import StatisticsSectionGenerator
from .recommendations import RecommendationsSectionGenerator

__all__ = [
    'SummarySectionGenerator',
    'ResultsSectionGenerator',
    'TrendsSectionGenerator',
    'StabilitySectionGenerator',
    'StatisticsSectionGenerator',
    'RecommendationsSectionGenerator',
]
