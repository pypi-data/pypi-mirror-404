"""
Warehouse Component Package

Extracted components from warehouse.py for better separation of concerns.

Components:
- DimensionOrchestrator: Builds dimension tables with column pruning
- FactOrchestrator: Builds fact tables with chunking support
- SchemaTracker: Tracks schema changes and drift
- PerformanceCalculator: Calculates warehouse performance metrics
"""

from .dimension_orchestrator import DimensionOrchestrator
from .fact_orchestrator import FactOrchestrator
from .schema_tracker import SchemaTracker
from .performance_calculator import PerformanceCalculator

__all__ = [
    'DimensionOrchestrator',
    'FactOrchestrator',
    'SchemaTracker',
    'PerformanceCalculator'
]
