"""
Pipeline Components Package

Extracted components from implementation.py (Phase 1 Refactoring)
Provides focused, testable components for data pipeline operations.

Components:
- DataFetcher: Handles R integration and data fetching
- DataCleaner: Handles data cleaning with schema detection
- DataStorage: Handles bucket-first storage with database routing
- SourceProcessor: Orchestrates fetch → clean → store for single source
"""

from .data_fetcher import DataFetcher
from .data_cleaner import DataCleaner
from .data_storage import DataStorage
from .source_processor import SourceProcessor

__all__ = [
    'DataFetcher',
    'DataCleaner',
    'DataStorage',
    'SourceProcessor'
]
