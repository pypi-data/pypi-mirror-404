"""
Warehouse Report Section Generators

Modular section generators for warehouse build reports.
Each generator is responsible for a specific aspect of the build process.

Pattern: Single Responsibility Principle
Architecture: Composition-based design
"""

from .summary import SummarySectionGenerator
from .dimensions import DimensionsSectionGenerator
from .facts import FactsSectionGenerator
from .performance import PerformanceSectionGenerator
from .storage import StorageHealthSectionGenerator
from .schema_evolution import SchemaEvolutionSectionGenerator
from .transformations import TransformationDetailsSectionGenerator  # PHASE 5
from .lineage import DataLineageSectionGenerator  # PHASE 5

__all__ = [
    'SummarySectionGenerator',
    'DimensionsSectionGenerator',
    'FactsSectionGenerator',
    'PerformanceSectionGenerator',
    'StorageHealthSectionGenerator',
    'SchemaEvolutionSectionGenerator',
    'TransformationDetailsSectionGenerator',  # PHASE 5
    'DataLineageSectionGenerator'  # PHASE 5
]
