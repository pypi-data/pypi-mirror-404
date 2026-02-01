"""
Data operations module for CommonV2.

Clean, testable data operations following Phase 1 patterns:
- Simple dependency injection via parameters
- Thin adapters for external dependencies
- Stable facade API - internal changes won't break consumers
- Clear separation between primary, advanced, and legacy APIs
"""

# Primary API - Most users should use these stable facade functions
from .database import (
    create_db_engine_from_env,
    get_table_row_count,
    get_all_table_row_counts,
    table_exists,
    drop_table,
    db_session,
    DatabaseConfig,
    # NEW: Strategy-aware functions
    execute_incremental_load,
    execute_full_refresh
)

# Advanced API - For dependency injection and testing
from .adapters import (
    DatabaseAdapter,
    DataCleaningService
)

# NEW: Loading strategy services
from .loading_strategies import LoadingStrategyService
from .schema_detector import SchemaDetector


__all__ = [
    # Primary API - Enhanced facade functions
    'create_db_engine_from_env',
    'get_table_row_count',
    'get_all_table_row_counts',
    'table_exists',
    'drop_table',
    'db_session',
    'DatabaseConfig',
    'execute_incremental_load',      # NEW
    'execute_full_refresh',          # NEW
    
    # Advanced API - Enhanced adapters
    'DatabaseAdapter',
    'DataCleaningService',
    'LoadingStrategyService',        # NEW
    'SchemaDetector',                # NEW
]
