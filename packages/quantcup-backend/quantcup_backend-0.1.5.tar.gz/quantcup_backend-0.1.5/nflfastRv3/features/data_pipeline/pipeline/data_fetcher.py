"""
Data Fetcher Component for nflfastRv3 Pipeline

Extracted from implementation.py lines 461-618 (Phase 1 Refactoring)
Handles R integration and data fetching with progress tracking.

Pattern: Focused Component (2 complexity points)
Complexity: 2 points (DI + business logic)
Responsibilities: R integration, validation, progress tracking, circuit breaker tracking
"""

from typing import Optional, List
import pandas as pd
from commonv2 import get_logger
from ....shared.r_integration import get_r_service, execute_real_r_call, current_nfl_season
from ....shared.models import ValidationResult
from ....shared.progress_tracker import ProgressTracker
from nflfastRv3.features.data_pipeline.config.data_sources import DataSourceConfig


class DataFetcher:
    """Handles R integration and data fetching with progress tracking."""
    
    def __init__(self, logger):
        """
        Initialize DataFetcher.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.r_service = get_r_service()
        self._fetch_failures = {}  # Circuit breaker tracking
    
    def fetch_from_r(self, config: DataSourceConfig, seasons: Optional[List[int]]) -> pd.DataFrame:
        """
        Fetch data using strategy-based temporal control.

        Strategy-based season handling:
        - Incremental tables: Load current season data only
        - Full refresh tables: Load all available historical data
        - No manual season parameter substitution needed

        Args:
            config: Data source configuration with R call specification
            seasons: Seasons to load (ignored - strategy determines temporal scope)

        Returns:
            DataFrame with fetched data

        Raises:
            RuntimeError: If R integration fails or data cannot be loaded
        """
        # 2. Data fetching progress tracking (tracking rows)
        fetch_progress = ProgressTracker(
            table_name=f"fetching_{config.table}",
            tracking_unit="rows",
            logger=self.logger
        )
        fetch_progress.start()

        # Strategy-based R call preparation
        r_call = self._prepare_strategy_based_r_call(config)

        self.logger.info(f"📡 Fetching {config.table} data using R call: {r_call}")
        self.logger.info(f"Using strategy: {config.strategy}")

        try:
            # Get the enhanced R service
            if not self.r_service.is_healthy:
                self.logger.warning("R service not healthy, attempting to continue")

            # Execute using the working string approach
            df = execute_real_r_call(r_call, config.table)

            if df.empty:
                self.logger.warning(f"No data returned for {config.table}")
                fetch_progress.finish()
                return pd.DataFrame()

            # BUG-004 FIX: Enhanced data loss logging - Log initial fetch count
            initial_row_count = len(df)
            self.logger.info(f"📊 DATA FETCH: {config.table} - Initial R fetch: {initial_row_count:,} rows")

            # Update progress with fetched data
            fetch_progress.update(len(df), force_report=True)

            # Validate the fetched data
            validation = self._validate_fetched_data(df, config)
            if not validation.is_valid:
                self.logger.warning(f"Data validation issues for {config.table}: {validation.errors}")

            # Finish fetch progress
            fetch_progress.finish()
            return df

        except Exception as e:
            self.logger.error(f"Failed to fetch data for {config.table}: {e}")
            fetch_progress.finish()
            
            # Circuit breaker pattern - track failures
            self._record_fetch_failure(config.table, str(e))
            return pd.DataFrame()
    
    def _prepare_strategy_based_r_call(self, config: DataSourceConfig) -> str:
        """
        Prepare R call based on loading strategy without parameter substitution.

        Strategy-based approach:
        - Incremental tables: Add current season parameter to R call
        - Full refresh tables: Use R call as-is (loads all available data)

        Args:
            config: Data source configuration

        Returns:
            str: Prepared R call string
        """
        r_call = config.r_call
        
        if config.strategy == 'incremental':
            # For incremental tables, add current season parameter
            current_season = current_nfl_season()
            
            # Add season parameter based on function signature
            if 'load_pbp(' in r_call:
                r_call = r_call.replace('load_pbp(', f'load_pbp(seasons = {current_season}, ')
            elif 'load_rosters(' in r_call:
                r_call = r_call.replace('load_rosters(', f'load_rosters(seasons = {current_season}, ')
            elif 'load_player_stats(' in r_call:
                r_call = r_call.replace('load_player_stats(', f'load_player_stats(seasons = {current_season}, ')
            elif 'load_participation(' in r_call:
                r_call = r_call.replace('load_participation(', f'load_participation(seasons = {current_season}, ')
            elif 'load_nextgen_stats(' in r_call:
                r_call = r_call.replace('load_nextgen_stats(', f'load_nextgen_stats({current_season}, ')
            elif 'load_snap_counts(' in r_call:
                r_call = r_call.replace('load_snap_counts(', f'load_snap_counts({current_season}, ')
            elif 'load_pfr_advstats(' in r_call:
                r_call = r_call.replace('load_pfr_advstats(', f'load_pfr_advstats({current_season}, ')
            elif 'load_ftn_charting(' in r_call:
                r_call = r_call.replace('load_ftn_charting(', f'load_ftn_charting(seasons = {current_season}')
            elif 'load_espn_qbr(' in r_call:
                r_call = r_call.replace('load_espn_qbr(', f'load_espn_qbr(seasons = {current_season}, ')
            elif 'load_rosters_weekly(' in r_call:
                r_call = r_call.replace('load_rosters_weekly(', f'load_rosters_weekly({current_season}, ')
            
            self.logger.info(f"Incremental strategy: Added current season {current_season} to R call")
        else:
            # For full refresh tables, use R call as-is
            self.logger.info(f"Full refresh strategy: Using R call as-is to load all available data")
        
        return r_call
    
    def _validate_fetched_data(self, df: pd.DataFrame, config: DataSourceConfig) -> ValidationResult:
        """
        Validate fetched data against configuration expectations.
        
        Args:
            df: Fetched DataFrame
            config: Data source configuration
            
        Returns:
            ValidationResult with validation status and issues
        """
        validation = ValidationResult(True)
        validation.record_count = len(df)
        
        # Check if data is empty
        if df.empty:
            validation.add_error("No data fetched")
            return validation
        
        # Check for expected columns based on unique keys
        if config.unique_keys:
            missing_keys = [key for key in config.unique_keys if key not in df.columns]
            if missing_keys:
                validation.add_error(f"Missing expected columns: {missing_keys}")
        
        # Check for reasonable data volume
        if len(df) < 10 and config.table not in ['teams', 'officials']:  # Some tables are naturally small
            validation.add_warning(f"Low row count: {len(df)} rows")
        
        # Check data types for numeric columns if specified
        if hasattr(config, 'numeric_cols') and config.numeric_cols:
            for col in config.numeric_cols:
                if col in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        validation.add_warning(f"Column {col} expected to be numeric but isn't")
        
        return validation
    
    def _record_fetch_failure(self, table_name: str, error_message: str):
        """
        Record data fetch failure for circuit breaker pattern.
        
        Args:
            table_name: Table that failed to fetch
            error_message: Error message from the failure
        """
        if table_name not in self._fetch_failures:
            self._fetch_failures[table_name] = []
        
        from datetime import datetime
        self._fetch_failures[table_name].append({
            'timestamp': datetime.now(),
            'error': error_message
        })
        
        # Keep only last 10 failures per table
        self._fetch_failures[table_name] = self._fetch_failures[table_name][-10:]
        
        # Check if we should trigger circuit breaker
        recent_failures = len(self._fetch_failures[table_name])
        if recent_failures >= 3:
            self.logger.error(f"🚨 CIRCUIT_BREAKER: {table_name} has {recent_failures} recent failures - consider manual intervention")
    
    def get_fetch_failures(self) -> dict:
        """
        Get current fetch failures for monitoring.
        
        Returns:
            Dictionary of fetch failures by table name
        """
        return self._fetch_failures


__all__ = ['DataFetcher']
