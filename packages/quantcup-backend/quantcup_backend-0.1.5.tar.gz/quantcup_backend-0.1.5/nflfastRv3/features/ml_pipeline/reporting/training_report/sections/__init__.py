"""
Training Report Section Generators

Modular section generators following Single Responsibility Principle.

**Refactoring Note**: Split from monolithic TrainingReportGenerator (852 lines)
into focused, testable section generators.
"""

from .summary import SummarySectionGenerator
from .metrics import MetricsSectionGenerator
from .features import FeaturesSectionGenerator
from .diagnostics import DiagnosticsSectionGenerator

__all__ = [
    'SummarySectionGenerator',
    'MetricsSectionGenerator',
    'FeaturesSectionGenerator',
    'DiagnosticsSectionGenerator',
]
