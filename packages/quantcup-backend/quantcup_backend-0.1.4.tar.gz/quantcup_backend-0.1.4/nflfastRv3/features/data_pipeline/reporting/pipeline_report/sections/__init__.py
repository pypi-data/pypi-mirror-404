"""
Pipeline Report Section Generators

Specialized generators for different sections of pipeline ingestion reports.
Each section focuses on a specific aspect of the pipeline process.

Phase 5 Enhancement: Added PerformanceSectionGenerator and DataLineageSectionGenerator
"""

from .summary import SummarySectionGenerator
from .source_details import SourceDetailsSectionGenerator
from .quality import QualitySectionGenerator
from .failures import FailuresSectionGenerator
from .storage import PipelineStorageHealthSectionGenerator
from .performance import PerformanceSectionGenerator  # NEW - Phase 5
from .lineage import DataLineageSectionGenerator  # NEW - Phase 5

__all__ = [
    'SummarySectionGenerator',
    'SourceDetailsSectionGenerator',
    'QualitySectionGenerator',
    'FailuresSectionGenerator',
    'PipelineStorageHealthSectionGenerator',
    'PerformanceSectionGenerator',  # NEW - Phase 5
    'DataLineageSectionGenerator',  # NEW - Phase 5
]
