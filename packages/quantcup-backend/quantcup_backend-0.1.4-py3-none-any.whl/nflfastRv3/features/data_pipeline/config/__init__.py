"""
Data Pipeline Configuration

Simplified data source configurations for nflfastRv3.
Following REFACTORING_SPECS.md: Simple data structures, no complex patterns.
"""

__all__ = ['DATA_SOURCE_GROUPS', 'list_all_sources']

from .data_sources import DATA_SOURCE_GROUPS, list_all_sources
