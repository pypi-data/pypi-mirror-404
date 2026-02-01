"""
Load package - data persistence operations.

Provides bucket storage for odds data with clean abstractions over
the nflfastRv3 BucketAdapter.
"""

from .bucket import (
    get_odds_bucket_adapter,
    store_odds_data,
    read_odds_data,
    list_odds_files,
    table_exists,
    normalize_timestamp,
    extract_date_part
)

__all__ = [
    'get_odds_bucket_adapter',
    'store_odds_data',
    'read_odds_data',
    'list_odds_files',
    'table_exists',
    'normalize_timestamp',
    'extract_date_part'
]
