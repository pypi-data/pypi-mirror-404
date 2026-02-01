"""
Feature Report Section Generators

Section-specific report generation modules.
"""

from .header import HeaderSectionGenerator
from .summary import SummarySectionGenerator
from .overview import OverviewSectionGenerator
from .statistics import StatisticsSectionGenerator
from .quality import QualitySectionGenerator
from .recommendations import RecommendationsSectionGenerator


__all__ = [
    'HeaderSectionGenerator',
    'SummarySectionGenerator',
    'OverviewSectionGenerator',
    'StatisticsSectionGenerator',
    'QualitySectionGenerator',
    'RecommendationsSectionGenerator',
]
