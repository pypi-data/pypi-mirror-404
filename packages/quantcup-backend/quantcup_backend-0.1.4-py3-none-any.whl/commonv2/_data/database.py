"""
Clean database facade for quantcup projects.
Follows pragmatic principles: simple, testable, and maintainable.

This module provides a clean facade that delegates to adapters for actual implementation.
"""

from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import pandas as pd
from sqlalchemy import create_engine, text, Engine

from ..core.logging import get_logger
from ..core.config import DatabaseConfig, ConfigError

# Module-level logger for simple utilities
_logger = get_logger('commonv2.data.database')

def create_db_engine_from_env(database_name: str, logger=None, **engine_kwargs) -> Engine:
    """
    Create database engine from environment variables using database name.

    Args:
        database_name: Database name (e.g., 'NFLFASTR_DB', 'SEVALLA_QUANTCUP_DB')
        logger: Optional logger instance
        **engine_kwargs: Additional SQLAlchemy engine parameters

    Returns:
        SQLAlchemy Engine instance

    Raises:
        ConfigError: If configuration is invalid or connection fails
    """
    logger = logger or _logger
    
    try:
        config = DatabaseConfig.load_from_env(database_name)
        logger.info(f"Creating database engine for {database_name}: {config.masked_url}")
        
        # Default engine settings
        default_kwargs = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'echo': False
        }
        default_kwargs.update(engine_kwargs)
        
        engine = create_engine(config.connection_url, **default_kwargs)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info(f"✓ Database connection established successfully for {database_name}")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine for {database_name}: {e}")
        raise ConfigError(f"Database connection failed for {database_name}: {e}")

def get_table_row_count(engine: Engine, table_name: str, schema: str = 'public', logger=None) -> int:
    """
    Get the current row count for a table.
    
    Simple facade function that delegates to DatabaseAdapter.
    
    Args:
        engine: SQLAlchemy engine
        table_name: Table name
        schema: Database schema
        logger: Optional logger instance
        
    Returns:
        Number of rows in the table
    """
    from .adapters import DatabaseAdapter
    
    logger = logger or _logger
    db_adapter = DatabaseAdapter(engine, logger)
    return db_adapter.get_table_row_count(table_name, schema)

def get_all_table_row_counts(
    engine: Engine, 
    schema: str = 'public', 
    table_list: Optional[List[str]] = None,
    logger=None
) -> Dict[str, int]:
    """
    Get row counts for multiple tables in a schema.
    
    Simple facade function that delegates to DatabaseAdapter.
    
    Args:
        engine: SQLAlchemy engine
        schema: Database schema to query
        table_list: Optional list of specific tables to check
        logger: Optional logger instance
        
    Returns:
        Dictionary mapping table names to row counts
    """
    from .adapters import DatabaseAdapter
    
    logger = logger or _logger
    db_adapter = DatabaseAdapter(engine, logger)
    return db_adapter.get_all_table_row_counts(schema, table_list)

def table_exists(engine: Engine, table_name: str, schema: str = "public", logger=None) -> bool:
    """
    Check if a table exists in the database.
    
    Simple facade function that delegates to DatabaseAdapter.
    
    Args:
        engine: SQLAlchemy engine
        table_name: Table name to check
        schema: Database schema
        logger: Optional logger instance
        
    Returns:
        True if table exists, False otherwise
    """
    from .adapters import DatabaseAdapter
    
    logger = logger or _logger
    db_adapter = DatabaseAdapter(engine, logger)
    return db_adapter.check_table_exists(table_name, schema)

def drop_table(engine: Engine, table_name: str, schema: str, logger=None):
    """
    Drop a table if it exists.
    
    Simple facade function that delegates to DatabaseAdapter.
    
    Args:
        engine: SQLAlchemy engine
        table_name: Table name to drop
        schema: Database schema
        logger: Optional logger instance
    """
    from .adapters import DatabaseAdapter
    
    logger = logger or _logger
    db_adapter = DatabaseAdapter(engine, logger)
    return db_adapter.drop_table(table_name, schema)

def execute_incremental_load(
    df: pd.DataFrame,
    engine: Engine,
    table_name: str,
    schema: str = "public",
    table_config: Optional[Dict[str, Any]] = None,
    current_year: Optional[int] = None,
    chunk_size: int = 1000,
    logger=None
) -> bool:
    """
    Execute incremental loading with sophisticated strategy.

    Facade function that creates LoadingStrategyService internally and
    delegates to the incremental loading logic.

    Args:
        df: DataFrame to load
        engine: SQLAlchemy engine
        table_name: Target table name
        schema: Database schema
        table_config: Optional table configuration
        current_year: Optional current year
        chunk_size: Chunk size for operations
        logger: Optional logger instance

    Returns:
        True if successful, False otherwise
    """
    from .loading_strategies import LoadingStrategyService

    logger = logger or _logger

    # Create default table config if not provided
    if table_config is None:
        table_config = {
            'table': table_name,
            'schema': schema,
            'unique_keys': [],  # Will be auto-detected
            'chunksize': chunk_size
        }

    # Create strategy service and execute
    strategy_service = LoadingStrategyService(engine, logger)
    return strategy_service.execute_incremental_load(
        df, table_config, engine, current_year
    )

def execute_full_refresh(
    df: pd.DataFrame,
    engine: Engine,
    table_name: str,
    schema: str = "public",
    table_config: Optional[Dict[str, Any]] = None,
    schema_changes: Optional[Dict[str, Any]] = None,
    chunk_size: int = 1000,
    logger=None
) -> bool:
    """
    Execute full refresh loading with sophisticated strategy.
    
    CENTRALIZED ARCHITECTURE: Can accept pre-analyzed schema changes to eliminate
    redundant schema detection across multiple database targets.
    
    Args:
        df: DataFrame to load
        engine: SQLAlchemy engine
        table_name: Target table name
        schema: Database schema
        table_config: Optional table configuration
        schema_changes: Optional pre-analyzed schema changes (for multi-database routing)
        chunk_size: Chunk size for operations
        logger: Optional logger instance
        
    Returns:
        True if successful, False otherwise
    """
    from .loading_strategies import LoadingStrategyService
    from .schema_detector import SchemaDetector
    
    logger = logger or _logger
    
    # Create default table config if not provided
    if table_config is None:
        table_config = {
            'table': table_name,
            'schema': schema,
            'unique_keys': [],  # Will be auto-detected
            'chunksize': chunk_size
        }
    
    # Create strategy service once
    strategy_service = LoadingStrategyService(engine, logger)
    
    if schema_changes is not None:
        # OPTIMIZED PATH: Use pre-analyzed schema changes (multi-database routing)
        logger.debug(f"Using pre-analyzed schema changes for {schema}.{table_name}")
        return strategy_service.execute_full_refresh_with_schema(
            df, table_config, engine, schema_changes
        )
    else:
        # SINGLE DATABASE PATH: Perform schema analysis once
        logger.debug(f"Performing schema analysis for {schema}.{table_name}")
        from .schema_detector import SchemaDetector
        schema_detector = SchemaDetector(logger)
        schema_changes = schema_detector.detect_schema_changes(
            df, table_name, schema, engine
        )
        return strategy_service.execute_full_refresh_with_schema(
            df, table_config, engine, schema_changes
        )

@contextmanager
def db_session(engine: Engine, logger=None):
    """
    Provide a transactional scope for database operations.
    
    Args:
        engine: SQLAlchemy engine
        logger: Optional logger instance
    """
    logger = logger or _logger
    logger.info("Creating database session...")
    try:
        yield engine
    finally:
        engine.dispose()
        logger.info("Database connection closed.")


