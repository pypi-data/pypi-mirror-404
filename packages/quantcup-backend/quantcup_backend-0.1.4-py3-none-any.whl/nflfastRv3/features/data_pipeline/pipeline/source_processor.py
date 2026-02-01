"""
Source Processor Component for nflfastRv3 Pipeline

Extracted from implementation.py lines 351-459 (Phase 1 Refactoring)
Processes individual data sources through fetch → clean → store pipeline.

Pattern: Orchestration Component (3 complexity points)
Complexity: 3 points (DI + orchestration + metrics)
Responsibilities: Single source orchestration, comprehensive metrics, timing, data loss calculation
"""

from typing import Dict, Any, Optional, List
import time
from nflfastRv3.features.data_pipeline.config.data_sources import DataSourceConfig
from .data_fetcher import DataFetcher
from .data_cleaner import DataCleaner
from .data_storage import DataStorage


def _calculate_data_loss_percentage(rows_before: int, rows_after: int) -> float:
    """
    Calculate data loss percentage during cleaning.
    
    Args:
        rows_before: Number of rows before cleaning
        rows_after: Number of rows after cleaning
        
    Returns:
        Percentage of data lost (0-100)
    """
    if rows_before == 0:
        return 0.0
    rows_lost = rows_before - rows_after
    return round((rows_lost / rows_before) * 100, 2)


class SourceProcessor:
    """Processes individual data sources through fetch → clean → store pipeline."""
    
    def __init__(self, fetcher: DataFetcher, cleaner: DataCleaner, storage: DataStorage, engine_provider, logger):
        """
        Initialize SourceProcessor.
        
        Args:
            fetcher: DataFetcher instance
            cleaner: DataCleaner instance
            storage: DataStorage instance
            engine_provider: Callable that returns database engine for schema matching
            logger: Logger instance
        """
        self.fetcher = fetcher
        self.cleaner = cleaner
        self.storage = storage
        self.engine_provider = engine_provider
        self.logger = logger
    
    def process(self, source_name: str, config: DataSourceConfig, seasons: Optional[List[int]]) -> Dict[str, Any]:
        """
        Process single data source with comprehensive metrics.
        
        V1-style: Each source determines its own seasons based on strategy.
        
        PHASE 1 ENHANCEMENT: Return comprehensive metrics dictionary instead of just row count
        PHASE 3 ENHANCEMENT: Add timing metrics for performance analysis
        
        Args:
            source_name: Name of the data source
            config: Data source configuration
            seasons: Seasons to load (None = let source determine based on strategy)
            
        Returns:
            Dictionary with detailed processing metrics:
            - rows_written: Final row count written to storage
            - rows_fetched: Initial rows fetched from R
            - rows_after_cleaning: Rows after cleaning/validation
            - rows_lost: Number of rows lost during cleaning
            - data_loss_pct: Percentage of data lost
            - bucket_success: Whether bucket storage succeeded
            - database_success: Whether database storage succeeded
            - status: Processing status ('success' or 'failed')
            - strategy: Loading strategy used
            - duration: Total processing time for this source (PHASE 3)
            - fetch_duration: Time spent fetching data (PHASE 3)
            - cleaning_duration: Time spent cleaning data (PHASE 3)
            - storage_duration: Time spent storing data (PHASE 3)
        """
        # PHASE 3: Start timing this source
        source_start_time = time.time()
        
        self.logger.debug(f"Processing data source: {source_name}")
        
        # Initialize metrics with defaults
        metrics = {
            'rows_written': 0,
            'rows_fetched': 0,
            'rows_after_cleaning': 0,
            'rows_lost': 0,
            'data_loss_pct': 0.0,
            'bucket_success': False,
            'database_success': False,
            'status': 'success',
            'strategy': config.strategy,
            'duration': 0.0,  # PHASE 3
            'fetch_duration': 0.0,  # PHASE 3
            'cleaning_duration': 0.0,  # PHASE 3
            'storage_duration': 0.0  # PHASE 3
        }
        
        # Step 1: Fetch data from R (Layer 3 call)
        # PHASE 3: Time the fetch operation
        fetch_start = time.time()
        df = self.fetcher.fetch_from_r(config, seasons)
        metrics['fetch_duration'] = round(time.time() - fetch_start, 2)
        
        if df.empty:
            self.logger.info(f"No data for {source_name}")
            metrics['duration'] = round(time.time() - source_start_time, 2)
            return metrics

        # BUG-004 FIX: Enhanced data loss logging - Track cleaning impact
        pre_cleaning_count = len(df)
        metrics['rows_fetched'] = pre_cleaning_count
        self.logger.info(f"📊 DATA CLEANING: {source_name} - Before cleaning: {pre_cleaning_count:,} rows")

        # Step 2: Clean data with schema matching (Layer 3 call)
        # PHASE 3: Time the cleaning operation
        cleaning_start = time.time()
        
        # Get engine for schema matching
        try:
            engine = self.engine_provider()
        except:
            engine = None
        df = self.cleaner.clean(df, config, engine)
        
        metrics['cleaning_duration'] = round(time.time() - cleaning_start, 2)

        # BUG-004 FIX: Calculate and log data loss from cleaning
        post_cleaning_count = len(df)
        metrics['rows_after_cleaning'] = post_cleaning_count
        metrics['rows_lost'] = pre_cleaning_count - post_cleaning_count
        metrics['data_loss_pct'] = _calculate_data_loss_percentage(pre_cleaning_count, post_cleaning_count)
        
        if metrics['rows_lost'] > 0:
            self.logger.warning(f"⚠️  DATA LOSS: {source_name} - Lost {metrics['rows_lost']:,} rows during cleaning ({metrics['data_loss_pct']:.1f}%)")
            self.logger.info(f"📊 DATA CLEANING: {source_name} - After cleaning: {post_cleaning_count:,} rows")
        else:
            self.logger.info(f"📊 DATA CLEANING: {source_name} - After cleaning: {post_cleaning_count:,} rows (no loss)")

        # Step 3: Store in database (Layer 3 call)
        # PHASE 3: Time the storage operation
        storage_start = time.time()
        
        # Track storage success status
        bucket_success, database_success, rows_written = self.storage.store_with_tracking(df, config)
        
        metrics['storage_duration'] = round(time.time() - storage_start, 2)
        metrics['rows_written'] = rows_written
        metrics['bucket_success'] = bucket_success
        metrics['database_success'] = database_success

        # PHASE 3: Calculate total duration
        metrics['duration'] = round(time.time() - source_start_time, 2)

        return metrics


__all__ = ['SourceProcessor']
