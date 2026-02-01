"""
Shared utilities for warehouse transformations.

Pattern: Simple utility functions (5 complexity points total)
- Table save function: 1 point
- Validation function: 1 point
- Empty dataframe handler: 0.5 points
- Season filter: 0.5 points
- Bucket/DB save: 1 point
- Efficiency calc: 0.5 points
- Season logging: 0.5 points

Following REFACTORING_SPECS.md: Stay within complexity budget while providing essential utilities.
"""

import pandas as pd
from commonv2 import get_logger
from typing import Dict, Any, Optional, List


def ensure_warehouse_schema_exists(engine, schema: str = 'warehouse', logger=None) -> bool:
    """
    Ensure warehouse schema exists in database.
    
    Creates schema if it doesn't exist (idempotent operation).
    
    Args:
        engine: SQLAlchemy database engine
        schema: Schema name to create (default: 'warehouse')
        logger: Optional logger instance
        
    Returns:
        bool: True if schema exists or was created successfully
    """
    logger = logger or get_logger('nflfastRv3.warehouse_utils')
    
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            # Create schema if not exists (idempotent)
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        logger.debug(f"✓ Schema '{schema}' exists or was created")
        return True
    except Exception as e:
        logger.error(f"Failed to ensure schema '{schema}' exists: {e}")
        return False

def save_table_to_db(df: pd.DataFrame, table_name: str, engine, chunk_size: int = 10000, logger=None) -> bool:
    """
    Save DataFrame to warehouse schema with chunked writes to avoid memory spikes.
    
    Pattern: Simple save function with chunking (1 complexity point)
    
    MEMORY FIX: Writes data in chunks to prevent memory doubling during to_sql()
    - First chunk: replaces table
    - Subsequent chunks: append to table
    - Default chunk size: 10,000 rows
    
    Args:
        df: DataFrame to save
        table_name: Target table name in warehouse schema
        engine: SQLAlchemy database engine
        chunk_size: Number of rows per chunk (default: 10000)
        logger: Optional logger instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger = logger or get_logger('nflfastRv3.warehouse_utils')
    
    try:
        if df.empty:
            logger.warning(f"Cannot save empty DataFrame to {table_name}")
            return False
        
        # Ensure warehouse schema exists
        ensure_warehouse_schema_exists(engine, 'warehouse', logger)
        
        total_rows = len(df)
        logger.info(f"Saving {total_rows:,} rows to warehouse.{table_name} in chunks of {chunk_size:,}...")
        
        # Write in chunks to avoid memory spikes
        num_chunks = (total_rows + chunk_size - 1) // chunk_size
        
        for i in range(0, total_rows, chunk_size):
            chunk_num = (i // chunk_size) + 1
            chunk = df.iloc[i:i+chunk_size]
            
            if i == 0:
                # First chunk: replace table
                if_exists_mode = 'replace'
                logger.info(f"Writing chunk 1/{num_chunks} ({len(chunk):,} rows) - replacing table...")
            else:
                # Subsequent chunks: append
                if_exists_mode = 'append'
                logger.info(f"Writing chunk {chunk_num}/{num_chunks} ({len(chunk):,} rows) - appending...")
            
            with engine.begin() as conn:
                chunk.to_sql(
                    name=table_name,
                    con=conn,
                    schema='warehouse',
                    if_exists=if_exists_mode,
                    index=False,
                    method='multi'
                )
        
        logger.info(f"✓ Successfully saved warehouse.{table_name} ({num_chunks} chunks, {total_rows:,} total rows)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save {table_name}: {e}")
        return False

def validate_table_data(df: pd.DataFrame, table_name: str, 
                       required_columns: Optional[list] = None, logger=None) -> Dict[str, Any]:
    """
    Validate DataFrame meets basic quality requirements.
    
    Pattern: Simple validation function (1 complexity point)
    
    Args:
        df: DataFrame to validate
        table_name: Table name for logging
        required_columns: List of required column names
        logger: Optional logger instance
        
    Returns:
        Dict: Validation results with status and details
    """
    logger = logger or get_logger('nflfastRv3.warehouse_utils')
    required_columns = required_columns or []
    
    validation_result = {
        'table_name': table_name,
        'status': 'success',
        'row_count': len(df),
        'column_count': len(df.columns),
        'issues': []
    }
    
    # Check if DataFrame is empty
    if df.empty:
        validation_result['status'] = 'warning'
        validation_result['issues'].append('DataFrame is empty')
        logger.warning(f"{table_name}: DataFrame is empty")
        return validation_result
    
    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        validation_result['status'] = 'error'
        validation_result['issues'].append(f'Missing required columns: {missing_columns}')
        logger.error(f"{table_name}: Missing required columns: {missing_columns}")
    
    # Check for completely null columns
    null_columns = [col for col in df.columns if df[col].isnull().all()]
    if null_columns:
        validation_result['status'] = 'warning'
        validation_result['issues'].append(f'Completely null columns: {null_columns}')
        logger.warning(f"{table_name}: Completely null columns: {null_columns}")
    
    # Check for duplicate rows
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        validation_result['status'] = 'warning'
        validation_result['issues'].append(f'Found {duplicate_count} duplicate rows')
        logger.warning(f"{table_name}: Found {duplicate_count} duplicate rows")
    
    logger.info(f"{table_name}: Validation complete - {validation_result['status']}")
    return validation_result

def create_table_summary(df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
    """
    Create summary statistics for a warehouse table.
    
    Args:
        df: DataFrame to summarize
        table_name: Table name for reference
        
    Returns:
        Dict: Summary statistics
    """
    if df.empty:
        return {
            'table_name': table_name,
            'row_count': 0,
            'column_count': 0,
            'memory_usage_mb': 0
        }
    
    return {
        'table_name': table_name,
        'row_count': len(df),
        'column_count': len(df.columns),
        'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        'data_types': df.dtypes.value_counts().to_dict(),
        'null_percentages': (df.isnull().sum() / len(df) * 100).round(2).to_dict()
    }

def handle_empty_dataframe(logger, message: str = "No data to process") -> Dict[str, Any]:
    """
    Return standard empty result dictionary for fact builders.
    
    Pattern: Simple utility function (0.5 complexity points)
    
    Args:
        logger: Logger instance
        message: Custom message for the warning
        
    Returns:
        Dict: Standard empty result structure
    """
    logger.warning(message)
    return {
        'status': 'success',
        'total_rows_processed': 0,
        'total_rows_saved': 0,
        'chunks_processed': 0,
        'message': message
    }

def filter_dataframe_by_seasons(df: pd.DataFrame, seasons: Optional[List[str]], 
                                logger) -> Optional[pd.DataFrame]:
    """
    Filter DataFrame by seasons with empty check.
    
    Pattern: Simple utility function (0.5 complexity points)
    
    Args:
        df: DataFrame to filter
        seasons: List of season strings to filter by
        logger: Logger instance
        
    Returns:
        Filtered DataFrame or None if empty after filtering
    """
    if seasons and 'season' in df.columns:
        season_ints = [int(s) for s in seasons]
        df = df[df['season'].isin(season_ints)]
        logger.info(f"Filtered to {len(df):,} rows for seasons {seasons}")
        
        if df.empty:
            logger.warning(f"No data found for seasons {seasons}")
            return None
    return df

def calculate_processing_efficiency(rows_saved: int, rows_processed: int) -> Dict[str, float]:
    """
    Calculate processing efficiency metrics.
    
    Pattern: Simple calculation function (0.5 complexity points)
    
    Args:
        rows_saved: Number of rows saved
        rows_processed: Number of rows processed
        
    Returns:
        Dict with processing efficiency metric
    """
    return {
        'processing_efficiency': rows_saved / rows_processed if rows_processed > 0 else 0
    }

def log_season_processing(seasons: Optional[List[str]], logger) -> int:
    """
    Log season processing information.
    
    Pattern: Simple logging function (0.5 complexity points)
    
    Args:
        seasons: Optional list of seasons to process
        logger: Logger instance
        
    Returns:
        Number of seasons being processed (0 if all seasons)
    """
    if seasons:
        logger.info(f"Processing filtered seasons: {seasons}")
        return len(seasons)
    else:
        logger.info("Processing all available seasons")
        return 0
