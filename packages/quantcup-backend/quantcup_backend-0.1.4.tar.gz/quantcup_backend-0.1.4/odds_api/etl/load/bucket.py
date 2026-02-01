"""
Bucket adapter wrapper for odds_api data persistence.

Provides odds-specific defaults while delegating to the mature
nflfastRv3 BucketAdapter implementation.

Pattern: Lightweight facade with dependency injection
Layer: Infrastructure (Data persistence)
"""
from typing import Optional, Any, Tuple, List
import pandas as pd
from commonv2.persistence.bucket_adapter import (
    BucketAdapter,
    get_bucket_adapter as _get_bucket_adapter,
    normalize_timestamp,
    extract_date_part
)
from commonv2 import get_logger
from odds_api.config.settings import get_settings

logger = get_logger(__name__)

# Singleton instance for BucketAdapter
_ODDS_BUCKET_ADAPTER: Optional[BucketAdapter] = None

def setup_bucket_adapter(cfg: Any) -> Tuple[Any, bool]:
    """Initialize bucket adapter if needed."""
    bucket = None
    save_to_bucket = cfg.save_to_bucket
    
    if save_to_bucket:
        try:
            bucket = get_odds_bucket_adapter()
            bucket_status = bucket.get_status()
            if not bucket_status['available']:
                logger.warning(f"⚠️  Bucket not available: {bucket_status}")
                logger.warning("   Falling back to CSV-only mode")
                save_to_bucket = False
            else:
                logger.info(f"✓ Bucket configured: {bucket_status['bucket_name']}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize BucketAdapter: {e}")
            logger.warning("   Falling back to CSV-only mode")
            save_to_bucket = False
    
    return bucket, save_to_bucket

def get_odds_bucket_adapter(config: Optional[dict] = None) -> BucketAdapter:
    """
    Get BucketAdapter configured for odds_api (Singleton).
    
    Args:
        config: Optional bucket configuration (uses env vars if None)
    
    Returns:
        BucketAdapter instance configured for odds data
        
    Example:
        >>> bucket = get_odds_bucket_adapter()
        >>> bucket.store_data(df, 'dim_team', schema='oddsapi')
    """
    global _ODDS_BUCKET_ADAPTER
    
    if _ODDS_BUCKET_ADAPTER is None or config is not None:
        adapter = _get_bucket_adapter(config=config, logger=logger)
        if config is None:
            _ODDS_BUCKET_ADAPTER = adapter
        return adapter
        
    return _ODDS_BUCKET_ADAPTER

def store_odds_data(
    df: pd.DataFrame,
    table_name: str,
    timestamp: Optional[str] = None,
    schema: Optional[str] = None,
    partition_by_year: bool = False
) -> bool:
    """
    Store odds data to bucket with sensible defaults.
    
    Args:
        df: DataFrame to store
        table_name: Table name (e.g., 'fact_odds_raw', 'dim_team')
        timestamp: Optional ISO-8601 timestamp for time-series partitioning
                  Creates structure: schema/table/date=YYYYMMDD/timestamp=ISO/data.parquet
        schema: Schema name (default: from settings.backfill.bucket_schema)
        partition_by_year: If True, partition by year (for large historical tables)
    
    Returns:
        bool: True if successful, False otherwise
        
    Examples:
        # Single-file dimension table
        >>> store_odds_data(df, 'dim_team')
        
        # Time-series fact table partitioned by game kickoff
        >>> store_odds_data(df, 'fact_odds_raw', timestamp='2025-09-05T20:00:00Z')
        
        # Year-partitioned table
        >>> store_odds_data(df, 'historical_odds', partition_by_year=True)
    """
    # Use configured schema if not provided
    if schema is None:
        settings = get_settings()
        schema = settings.backfill.bucket_schema
    
    bucket = get_odds_bucket_adapter()
    
    try:
        return bucket.store_data(
            df=df,
            table_name=table_name,
            schema=schema,
            timestamp=timestamp,
            partition_by_year=partition_by_year
        )
    except Exception as e:
        logger.error(f"Failed to store {table_name} to bucket: {e}", exc_info=True)
        return False

def read_odds_data(
    table_name: str,
    schema: Optional[str] = None,
    filters: Optional[list] = None,
    columns: Optional[list] = None
) -> pd.DataFrame:
    """
    Read odds data from bucket.
    
    Args:
        table_name: Table name to read
        schema: Schema name (default: from settings.backfill.bucket_schema)
        filters: Optional parquet filters for predicate pushdown
                Format: [('column', 'operator', value), ...]
                Operators: '==', '!=', '<', '<=', '>', '>=', 'in', 'not in'
        columns: Optional column subset to read (reduces memory usage)
    
    Returns:
        DataFrame (empty if not found)
        
    Examples:
        # Read entire dimension table
        >>> df = read_odds_data('dim_team')
        
        # Read with filters (predicate pushdown)
        >>> df = read_odds_data('dim_oddapi_game', 
        ...                      filters=[('season', '==', 2025)])
        
        # Read specific columns only
        >>> df = read_odds_data('fact_odds_raw',
        ...                      columns=['event_id', 'odds_price', 'bookmaker_key'])
    """
    # Use configured schema if not provided
    if schema is None:
        settings = get_settings()
        schema = settings.backfill.bucket_schema
    
    bucket = get_odds_bucket_adapter()
    
    try:
        return bucket.read_data(
            table_name=table_name,
            schema=schema,
            filters=filters,
            columns=columns
        )
    except Exception as e:
        logger.error(f"Failed to read {table_name} from bucket: {e}")
        return pd.DataFrame()

def list_odds_files(prefix: str = '', schema: Optional[str] = None) -> List[str]:
    """
    List all files in odds bucket with optional prefix.
    
    Args:
        prefix: Optional prefix to filter files (e.g., 'dim_team/')
        schema: Schema name (default: from settings.backfill.bucket_schema)
    
    Returns:
        List of file keys
        
    Example:
        # List all files for a table
        >>> files = list_odds_files(prefix='oddsapi/fact_odds_raw/')
        
        # Check if specific partition exists
        >>> files = list_odds_files(prefix='oddsapi/fact_odds_raw/date=20250905/')
        >>> exists = len(files) > 0
    """
    # Add schema prefix if provided
    if schema is None:
        settings = get_settings()
        schema = settings.backfill.bucket_schema
    
    # Prepend schema to prefix if not already present
    if prefix and not prefix.startswith(schema):
        prefix = f"{schema}/{prefix}"
    elif not prefix:
        prefix = f"{schema}/"
    
    bucket = get_odds_bucket_adapter()
    
    try:
        return bucket.list_files(prefix=prefix)
    except Exception as e:
        logger.error(f"Failed to list files with prefix '{prefix}': {e}")
        return []

def table_exists(table_name: str, schema: Optional[str] = None, 
                 check_partitioned: bool = True) -> bool:
    """
    Check if odds table exists in bucket.
    
    Args:
        table_name: Table name to check
        schema: Schema name (default: from settings.backfill.bucket_schema)
        check_partitioned: If True, also checks for timestamp-partitioned data
    
    Returns:
        bool: True if table exists (either single-file or partitioned)
        
    Example:
        >>> if table_exists('dim_team'):
        ...     df = read_odds_data('dim_team')
    """
    if schema is None:
        settings = get_settings()
        schema = settings.backfill.bucket_schema
    
    bucket = get_odds_bucket_adapter()
    
    try:
        return bucket.table_exists(
            table_name=table_name,
            schema=schema,
            check_partitioned=check_partitioned
        )
    except Exception as e:
        logger.error(f"Failed to check table existence for {table_name}: {e}")
        return False


# Re-export timestamp utilities for convenience
# These are needed by backfill scripts for timestamp partitioning
__all__ = [
    'get_odds_bucket_adapter',
    'store_odds_data',
    'read_odds_data',
    'list_odds_files',
    'table_exists',
    'normalize_timestamp',
    'extract_date_part'
]
