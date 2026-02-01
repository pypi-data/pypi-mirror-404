"""
Data Storage Component for nflfastRv3 Pipeline

Extracted from implementation.py lines 869-999 (Phase 1 Refactoring)
Handles bucket-first storage with database routing.

Pattern: Focused Component (2 complexity points)
Complexity: 2 points (DI + bucket-first logic)
Responsibilities: Bucket storage, database routing, storage failure tracking, progress tracking
"""

from typing import Any, Dict, List
import pandas as pd
from commonv2.persistence.bucket_adapter import BucketAdapter
from nflfastRv3.shared.database_router import DatabaseRouter
from nflfastRv3.features.data_pipeline.config.data_sources import DataSourceConfig
from nflfastRv3.shared.progress_tracker import ProgressTracker


class DataStorage:
    """Handles bucket-first storage with database routing."""
    
    def __init__(self, bucket_adapter: BucketAdapter, database_router: DatabaseRouter, logger):
        """
        Initialize DataStorage.
        
        Args:
            bucket_adapter: Bucket adapter instance
            database_router: Database router instance
            logger: Logger instance
        """
        self.bucket_adapter = bucket_adapter
        self.database_router = database_router
        self.logger = logger
        self._storage_failures = {}
    
    def store_with_tracking(self, df: pd.DataFrame, config: DataSourceConfig) -> tuple:
        """
        Store data using bucket-first architecture with detailed status tracking.
        
        PHASE 1 ENHANCEMENT: Return storage status for comprehensive reporting
        
        Args:
            df: Cleaned DataFrame
            config: Data source configuration
            
        Returns:
            Tuple of (bucket_success, database_success, rows_written)
        """
        if df.empty:
            self.logger.info(f"No data to store for {config.table}")
            return (False, False, 0)
        
        # 3. Storage progress tracking (tracking rows)
        storage_progress = ProgressTracker(
            total_expected=len(df),
            table_name=f"storing_{config.table}",
            tracking_unit="rows",
            logger=self.logger
        )
        storage_progress.start()
        
        # Step 1: Store in bucket FIRST (primary storage)
        bucket_success = False
        if config.bucket:
            self.logger.info(f"☁️  Storing {len(df):,} rows in bucket: {config.table}")
            
            # Pass partition_by_year flag from config (enables year partitioning for play_by_play)
            partition_by_year = getattr(config, 'partition_by_year', False)
            bucket_success = self.bucket_adapter.store_data(
                df,
                config.table,
                config.schema,
                partition_by_year=partition_by_year
            )
            
            if not bucket_success:
                # BUG-009 FIX: Standardized storage reporting - Complete failure
                self.logger.error(f"❌ STORAGE FAILED: {config.table} - {len(df):,} rows → Bucket: ✗ Database: ✗")
                storage_progress.finish()
                return (False, False, 0)
            
            # Update progress for bucket storage
            storage_progress.update(len(df), force_report=True)
        else:
            self.logger.debug(f"Bucket storage disabled for {config.table}")
            storage_progress.update(len(df), force_report=True)
            bucket_success = True  # Consider it successful if disabled
        
        # Step 2: Route to databases (secondary storage)
        database_success = False
        try:
            # Check if table is intentionally bucket-only
            is_bucket_only = not config.databases or len(config.databases) == 0
            
            if not is_bucket_only:
                self.logger.info(f"🗄️  Configured databases: {config.databases} (environment filtering will be applied)")
            
            database_success = self.database_router.route_to_databases(df, config)
            
            # BUG-009 FIX: Standardized storage reporting - Single consolidated message
            if bucket_success and database_success:
                self.logger.info(f"✅ STORAGE SUCCESS: {config.table} - {len(df):,} rows → Bucket: ✓ Database: ✓")
            elif bucket_success and not database_success:
                if is_bucket_only:
                    # Bucket-only table: this is expected behavior
                    self.logger.info(f"✅ STORAGE SUCCESS: {config.table} - {len(df):,} rows → Bucket: ✓ (bucket-only table)")
                else:
                    # Database routing was configured but failed
                    self.logger.warning(f"⚠️ STORAGE PARTIAL: {config.table} - {len(df):,} rows → Bucket: ✓ Database: ✗ (data safe in bucket)")
            else:
                self.logger.error(f"❌ STORAGE FAILED: {config.table} - {len(df):,} rows → Bucket: ✗ Database: ✗")
            
            # Finish storage progress
            storage_progress.finish()
            return (bucket_success, database_success, len(df))
            
        except Exception as e:
            self.logger.error(f"Failed to route {config.table} to databases: {e}")
            
            # PHASE 1 ENHANCEMENT: Enhanced error recovery with detailed logging
            if bucket_success:
                self.logger.warning(f"⚠️ STORAGE_PARTIAL: {config.table} - {len(df):,} rows → Bucket: ✓ Database: ✗ (data safe in bucket)")
                self.logger.info(f"💡 RECOVERY_SUGGESTION: Data for {config.table} is safely stored in bucket and can be reprocessed to database")
            else:
                self.logger.error(f"❌ STORAGE_FAILED: {config.table} - {len(df):,} rows → Bucket: ✗ Database: ✗")
                self.logger.error(f"🚨 DATA_LOSS_RISK: {config.table} data may be lost - manual intervention required")
            
            # Record storage failure for monitoring
            self._record_storage_failure(config.table, str(e), bucket_success)
            
            storage_progress.finish()
            return (bucket_success, False, len(df) if bucket_success else 0)
    
    def _record_storage_failure(self, table_name: str, error_message: str, bucket_success: bool):
        """
        Record storage failure for monitoring and recovery planning.
        
        PHASE 1 ENHANCEMENT: Storage failure tracking
        
        Args:
            table_name: Table that failed to store
            error_message: Error message from the failure
            bucket_success: Whether bucket storage succeeded
        """
        if table_name not in self._storage_failures:
            self._storage_failures[table_name] = []
        
        from datetime import datetime
        self._storage_failures[table_name].append({
            'timestamp': datetime.now(),
            'error': error_message,
            'bucket_success': bucket_success,
            'recovery_needed': not bucket_success
        })
        
        # Keep only last 5 storage failures per table
        self._storage_failures[table_name] = self._storage_failures[table_name][-5:]
        
        # Alert on repeated storage failures
        recent_failures = len(self._storage_failures[table_name])
        if recent_failures >= 2:
            self.logger.error(f"🚨 REPEATED_STORAGE_FAILURES: {table_name} has {recent_failures} recent storage failures")
    
    def get_storage_failures(self) -> List[Dict[str, Any]]:
        """
        Get storage failures for reporting.
        
        PHASE 2 ENHANCEMENT: Expose storage failure tracking to reports
        
        Returns:
            List of dictionaries containing storage failure details
        """
        failures = []
        for table, failure_list in self._storage_failures.items():
            # Get most recent failure for this table
            if failure_list:
                recent_failure = failure_list[-1]
                failures.append({
                    'table': table,
                    'bucket_success': recent_failure['bucket_success'],
                    'database_success': False,  # If it's in failures, DB failed
                    'error': recent_failure['error'],
                    'recovery_needed': recent_failure['recovery_needed'],
                    'timestamp': recent_failure['timestamp'].isoformat()
                })
        
        return failures


__all__ = ['DataStorage']
