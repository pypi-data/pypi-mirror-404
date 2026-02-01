"""
Optimization Report Section Generators

Exports section generators for window optimization reports.
"""

from .summary import SummarySectionGenerator
from .window_comparison import WindowComparisonSectionGenerator
from .recommendations import RecommendationsSectionGenerator

__all__ = [
    'SummarySectionGenerator',
    'WindowComparisonSectionGenerator',
    'RecommendationsSectionGenerator',
]
