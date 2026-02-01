"""
Bucket Adapter Wrapper for nflfastRv3

This module maintains backward compatibility for nflfastRv3 while
delegating core bucket operations to commonv2.persistence.bucket_adapter.

Pattern: Legacy Wrapper / Bridge
"""

from typing import Optional
import pandas as pd
from commonv2.persistence.bucket_adapter import (
    BucketAdapter,
    get_bucket_adapter,
    normalize_timestamp,
    extract_date_part
)
from commonv2 import get_logger

_logger = get_logger('nflfastRv3.bucket')


def read_table_environment_aware(table_name: str, schema: str = 'raw_nflfastr',
                                 query: Optional[str] = None,
                                 bucket_adapter=None, db_router=None, logger=None) -> pd.DataFrame:
    """
    Read table data with environment-aware bucket-first approach.
    
    Routing Logic:
    - Production: Read from bucket (primary storage for ML/Analytics)
    - Local/Testing: Read from database (for development/testing)
    
    Pattern: Module-level function with DI fallback
    """
    from commonv2.core.config import Environment
    
    # Module-level logger with DI fallback
    logger = logger or _logger
    
    if Environment.is_production():
        # Production: Read from bucket (primary storage)
        logger.debug(f"Production environment - reading {table_name} from bucket")
        bucket = bucket_adapter or BucketAdapter(logger=logger)
        df = bucket.read_data(table_name, schema)
        
        if df.empty:
            logger.warning(
                f"⚠️ No data in bucket for {table_name} - "
                f"this shouldn't happen in production!"
            )
        else:
            logger.info(f"✓ Read {len(df):,} rows from bucket: {schema}/{table_name}")
        
        return df
    else:
        # Local/Testing: Read from database
        logger.debug(f"Local environment - reading {table_name} from database")
        
        from nflfastRv3.shared.database_router import get_database_router
        router = db_router or get_database_router(logger=logger)
        engine = router._get_engine_for_database(router.default_database)
        
        if engine is None:
            logger.error(f"Failed to get database engine for {table_name}")
            return pd.DataFrame()
        
        try:
            if query:
                # Use custom query if provided
                df = pd.read_sql(query, engine)
            else:
                # Simple table read
                df = pd.read_sql(f"SELECT * FROM {schema}.{table_name}", engine)
            
            logger.info(f"✓ Read {len(df):,} rows from database: {schema}.{table_name}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to read {table_name} from database: {e}")
            return pd.DataFrame()


__all__ = ['BucketAdapter', 'get_bucket_adapter', 'read_table_environment_aware', 'normalize_timestamp', 'extract_date_part']
