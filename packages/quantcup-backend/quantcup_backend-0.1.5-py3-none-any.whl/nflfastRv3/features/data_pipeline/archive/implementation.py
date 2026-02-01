"""
Data Pipeline Implementation for nflfastRv3

Migrates proven DataLoader business logic from nflfastRv2 into clean architecture.
Following REFACTORING_SPECS.md: Maximum 5 complexity points, 3 layers depth.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Implementation - calls infrastructure directly)
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import time
from commonv2 import get_logger
from ...shared.database_router import get_database_router
from ...shared.r_integration import get_r_service, execute_real_r_call, current_nfl_season
from ...shared.models import ValidationResult
from commonv2.persistence.bucket_adapter import BucketAdapter
from ...shared.database_router import DatabaseRouter
from .config.data_sources import DATA_SOURCE_GROUPS, DataSourceConfig
from commonv2 import apply_cleaning
from commonv2._data.schema_detector import SchemaDetector
from ...shared.progress_tracker import ProgressTracker


def _calculate_data_loss_percentage(rows_before: int, rows_after: int) -> float:
    """
    Calculate data loss percentage during cleaning.
    
    PHASE 1 ENHANCEMENT: Helper for data loss tracking
    
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


class DataPipeline:
    """
    Core data pipeline business logic.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + business logic)
    Depth: 1 layer (calls infrastructure directly)
    
    Migrated from nflfastRv2.DataLoader with architectural simplification.
    """
    
    def __init__(self, db_service, logger):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        
        # NEW: Initialize bucket-first architecture services (Layer 3)
        self.bucket_adapter = BucketAdapter(logger=logger)
        self.database_router = DatabaseRouter(logger=logger)
    
    def process(self, groups=None, tables=None, seasons=None):
        """
        Execute data pipeline workflow.

        V1-style processing: either groups OR tables (mutually exclusive)
        1. Load data from R (Layer 3 call)
        2. Process each data source group (Layer 3 calls)
        3. Return summary

        Args:
            groups: Data source groups to load (mutually exclusive with tables)
            tables: Specific tables to load with auto-discovery (mutually exclusive with groups)
            seasons: Seasons to load

        Returns:
            dict: Processing summary
        """
        # PHASE 3: Start timing the entire pipeline
        pipeline_start_time = time.time()
        
        # V1-style: Default to nfl_data if nothing specified
        if not groups and not tables:
            groups = ['nfl_data']
        
        self.logger.info(f"Starting data pipeline: groups={groups}, tables={tables}, seasons={seasons}")
        
        try:
            # V1-style processing: either groups OR tables
            groups_to_process = self._resolve_data_sources(groups, tables)
            
            if not groups_to_process:
                return {
                    'status': 'warning',
                    'message': 'No valid groups specified',
                    'tables': [],
                    'total_rows': 0
                }
            
            # Process each group
            total_rows = 0
            total_rows_fetched = 0
            all_tables = []
            group_results = {}
            
            for group_name, data_sources in groups_to_process.items():
                self.logger.info(f"Processing group: {group_name}")
                
                try:
                    # PHASE 1: Get enhanced metrics from processing
                    rows_processed, source_details = self._process_data_sources(group_name, data_sources, seasons)
                    
                    # Aggregate fetched rows from source details
                    group_rows_fetched = sum(details.get('rows_fetched', 0) for details in source_details.values())
                    
                    group_results[group_name] = {
                        'status': 'success',
                        'rows': rows_processed,
                        'source_details': source_details  # PHASE 1: Add source-level details
                    }
                    total_rows += rows_processed
                    total_rows_fetched += group_rows_fetched
                    all_tables.extend(data_sources.keys())
                    
                except Exception as e:
                    self.logger.error(f"Group {group_name} failed: {e}")
                    group_results[group_name] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    continue
            
            # PHASE 3: Calculate pipeline duration
            pipeline_duration = time.time() - pipeline_start_time
            
            self.logger.info(f"Pipeline complete: {total_rows:,} total rows processed")
            self.logger.info(f"Pipeline complete: {total_rows_fetched:,} total rows fetched")
            self.logger.info(f"Pipeline duration: {pipeline_duration:.2f} seconds")
            
            # PHASE 2: Add circuit breaker and storage failure tracking
            circuit_breaker_activations = self._get_circuit_breaker_status()
            storage_failures = self._get_storage_failures()
            
            # PHASE 3: Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                group_results,
                total_rows,
                pipeline_duration
            )
            
            # PHASE 4: Get schema issues detected during processing
            schema_issues = self._get_schema_issues()
            
            # Determine overall status: success if all groups succeeded, partial if some failed
            failed_groups = [g for g, r in group_results.items() if r.get('status') == 'failed']
            overall_status = 'partial' if failed_groups else 'success'
            
            if overall_status == 'partial':
                self.logger.warning(f"⚠️ Pipeline completed with failures in {len(failed_groups)} groups: {', '.join(failed_groups)}")
            
            result = {
                'status': overall_status,
                'tables': all_tables,
                'total_rows': total_rows,
                'total_rows_fetched': total_rows_fetched,  # PHASE 1: Add total fetched count
                'group_results': group_results,
                'circuit_breaker_activations': circuit_breaker_activations,  # PHASE 2: Circuit breaker status
                'storage_failures': storage_failures,  # PHASE 2: Storage failure tracking
                'duration': pipeline_duration,  # PHASE 3: Total pipeline duration
                'performance_metrics': performance_metrics,  # PHASE 3: Performance analysis
                'schema_issues': schema_issues  # PHASE 4: Schema drift detection
            }
            
            # Generate pipeline report (matches ML pipeline pattern)
            self.logger.info("🔄 Attempting to generate pipeline report...")
            try:
                self.logger.debug(f"Report result status: {result.get('status')}")
                self.logger.debug(f"Report result groups: {list(result.get('group_results', {}).keys())}")
                
                from .reporting import create_report_orchestrator
                self.logger.debug("Report orchestrator imported successfully")
                
                orchestrator = create_report_orchestrator(logger=self.logger)
                self.logger.debug("Report orchestrator created successfully")
                
                # Pass logger directly to static method
                report_path = orchestrator.generate_pipeline_report(result, logger=self.logger)
                
                if report_path:
                    self.logger.info(f"📊 Pipeline report generated: {report_path}")
                else:
                    self.logger.warning("📊 Report generation returned None - no report created")
            except Exception as e:
                self.logger.error(f"❌ Report generation failed: {e}", exc_info=True)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Data pipeline failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'tables': [],
                'total_rows': 0
            }
    
    def _resolve_data_sources(self, groups: Optional[List[str]] = None, tables: Optional[List[str]] = None) -> Dict[str, Dict[str, DataSourceConfig]]:
        """
        V1-style processing: either groups OR tables, not both.
        
        Args:
            groups: List of group names (mutually exclusive with tables)
            tables: List of table names with auto-discovery (mutually exclusive with groups)
            
        Returns:
            Dictionary of valid groups with their data sources
        """
        
        if tables:
            # V1-style table auto-discovery
            groups_to_process = {}
            for table_name in tables:
                # Find which group contains this table
                found_group = None
                for group_name, sources in DATA_SOURCE_GROUPS.items():
                    if table_name in sources:
                        found_group = group_name
                        break
                
                if not found_group:
                    available_tables = [t for sources in DATA_SOURCE_GROUPS.values() for t in sources.keys()]
                    raise ValueError(f"Unknown table: {table_name}. Available: {available_tables}")
                
                # Add to single_tables group (v1 pattern)
                if "single_tables" not in groups_to_process:
                    groups_to_process["single_tables"] = {}
                groups_to_process["single_tables"][table_name] = DATA_SOURCE_GROUPS[found_group][table_name]
            
            self.logger.info(f"📊 Auto-discovered tables: {list(tables)}")
            return groups_to_process
        
        elif groups:
            # Standard group processing
            groups_to_process = {}
            for group_name in groups:
                if group_name not in DATA_SOURCE_GROUPS:
                    raise ValueError(f"Unknown group: {group_name}. Available: {list(DATA_SOURCE_GROUPS.keys())}")
                groups_to_process[group_name] = DATA_SOURCE_GROUPS[group_name]
            
            self.logger.info(f"📊 Processing groups: {list(groups)}")
            return groups_to_process
        
        else:
            # Default: nfl_data group
            self.logger.info("📊 Processing default group: nfl_data")
            return {"nfl_data": DATA_SOURCE_GROUPS["nfl_data"]}
    
    def _process_data_sources(self, group_name: str, data_sources: Dict[str, DataSourceConfig], seasons: Optional[List[int]]) -> tuple:
        """
        Process all data sources in a group.
        
        V1-style: No default seasons - each data source determines its own seasons
        based on loading strategy (incremental vs full refresh).
        
        PHASE 1 ENHANCEMENT: Return source-level details for comprehensive reporting
        
        Args:
            group_name: Name of the data source group
            data_sources: Dictionary of data source configs
            seasons: Seasons to load (None = let each source determine its own)
            
        Returns:
            Tuple of (total_rows_processed, source_details_dict)
        """
        total_processed = 0
        total_sources = len(data_sources)
        source_details = {}
        
        # 1. Pipeline-level progress tracking (tracking data sources, not rows)
        pipeline_progress = ProgressTracker(
            total_expected=total_sources,
            table_name=f"{group_name}_sources",
            tracking_unit="sources",
            logger=self.logger
        )
        pipeline_progress.start()
        
        for idx, (source_name, config) in enumerate(data_sources.items(), 1):
            self.logger.info(f"🔄 Processing {idx}/{total_sources} data sources: {source_name}")
            
            try:
                # Get detailed metrics from source processing
                source_metrics = self._process_source(source_name, config, seasons)
                total_processed += source_metrics['rows_written']
                
                # PHASE 1: Capture per-source details for reporting
                # PHASE 3: Include timing metrics
                source_details[source_name] = {
                    'rows': source_metrics['rows_written'],
                    'rows_fetched': source_metrics['rows_fetched'],
                    'rows_after_cleaning': source_metrics['rows_after_cleaning'],
                    'rows_lost': source_metrics['rows_lost'],
                    'data_loss_pct': source_metrics['data_loss_pct'],
                    'bucket_success': source_metrics['bucket_success'],
                    'database_success': source_metrics['database_success'],
                    'status': source_metrics['status'],
                    'loading_strategy': source_metrics['strategy'],
                    'duration': source_metrics['duration'],  # PHASE 3
                    'fetch_duration': source_metrics['fetch_duration'],  # PHASE 3
                    'cleaning_duration': source_metrics['cleaning_duration'],  # PHASE 3
                    'storage_duration': source_metrics['storage_duration']  # PHASE 3
                }
                
                # Update pipeline progress (1 source completed)
                pipeline_progress.update(1, force_report=True, step_name=source_name)
                self.logger.info(f"✅ {source_name}: {source_metrics['rows_written']:,} rows processed")
                
            except Exception as e:
                self.logger.error(f"Failed to process {source_name}: {e}")
                
                # PHASE 1: Record failure in source details
                source_details[source_name] = {
                    'rows': 0,
                    'rows_fetched': 0,
                    'rows_after_cleaning': 0,
                    'rows_lost': 0,
                    'data_loss_pct': 0.0,
                    'bucket_success': False,
                    'database_success': False,
                    'status': 'failed',
                    'error': str(e),
                    'loading_strategy': config.strategy
                }
                
                pipeline_progress.update(1, force_report=True, step_name=f"{source_name} (failed)")
                continue
        
        # Finish pipeline progress
        pipeline_progress.finish()
        return (total_processed, source_details)
    
    def _process_source(self, source_name: str, config: DataSourceConfig, seasons: Optional[List[int]]) -> Dict[str, Any]:
        """
        Process single data source: fetch → clean → store.
        
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
        df = self._fetch_data(config, seasons)
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
        
        # Get engine for schema matching (use local database engine)
        try:
            engine = self.db_service.engine
        except:
            engine = None
        df = self._clean_data(df, config, engine)
        
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
        bucket_success, database_success, rows_written = self._store_data_with_status(df, config)
        
        metrics['storage_duration'] = round(time.time() - storage_start, 2)
        metrics['rows_written'] = rows_written
        metrics['bucket_success'] = bucket_success
        metrics['database_success'] = database_success

        # PHASE 3: Calculate total duration
        metrics['duration'] = round(time.time() - source_start_time, 2)

        return metrics
    
    def _fetch_data(self, config: DataSourceConfig, seasons: Optional[List[int]]) -> pd.DataFrame:
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
            r_service = get_r_service()

            if not r_service.is_healthy:
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

    def _record_fetch_failure(self, table_name: str, error_message: str):
        """
        Record data fetch failure for circuit breaker pattern.
        
        PHASE 1 ENHANCEMENT: Circuit breaker pattern implementation
        
        Args:
            table_name: Table that failed to fetch
            error_message: Error message from the failure
        """
        # Simple failure tracking - could be enhanced with persistent storage
        if not hasattr(self, '_fetch_failures'):
            self._fetch_failures = {}
        
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
    
    def _get_circuit_breaker_status(self) -> List[Dict[str, Any]]:
        """
        Get current circuit breaker activation status for reporting.
        
        PHASE 2 ENHANCEMENT: Expose circuit breaker tracking to reports
        
        Returns:
            List of dictionaries containing circuit breaker activation details
        """
        if not hasattr(self, '_fetch_failures'):
            return []
        
        activations = []
        for source, failures in self._fetch_failures.items():
            if len(failures) >= 3:  # Circuit breaker threshold
                activations.append({
                    'source': source,
                    'failure_count': len(failures),
                    'last_error': failures[-1]['error'],
                    'activated_at': failures[-1]['timestamp'].isoformat(),
                    'status': 'open'
                })
        
        return activations
    
    def _get_storage_failures(self) -> List[Dict[str, Any]]:
        """
        Get storage failures for reporting.
        
        PHASE 2 ENHANCEMENT: Expose storage failure tracking to reports
        
        Returns:
            List of dictionaries containing storage failure details
        """
        if not hasattr(self, '_storage_failures'):
            return []
        
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
    
    def _get_schema_issues(self) -> List[Dict[str, Any]]:
        """
        Get schema issues detected during processing for reporting.
        
        PHASE 4 ENHANCEMENT: Expose schema drift tracking to reports
        
        Returns:
            List of dictionaries containing schema issue details
        """
        if not hasattr(self, '_schema_issues'):
            return []
        
        return self._schema_issues
    
    def _track_schema_issue(self, table: str, schema_analysis: Dict[str, Any]):
        """
        Track schema drift issue for reporting.
        
        PHASE 4 ENHANCEMENT: Schema drift tracking
        
        Args:
            table: Table name where schema drift was detected
            schema_analysis: Schema analysis results from SchemaDetector
        """
        if not hasattr(self, '_schema_issues'):
            self._schema_issues = []
        
        # Extract relevant information from schema analysis
        issue = {
            'table': table,
            'requires_drop': schema_analysis.get('requires_drop', False),
            'breaking_changes': schema_analysis.get('breaking_changes', []),
            'missing_columns': schema_analysis.get('missing_columns', []),
            'severity': 'critical' if schema_analysis.get('requires_drop', False) else 'warning',
            'type': 'schema_drift'
        }
        
        # Add descriptive message
        if issue['requires_drop']:
            issue['message'] = f"Table requires drop/recreate due to breaking schema changes"
        elif issue['missing_columns']:
            issue['message'] = f"Missing columns in database: {', '.join(issue['missing_columns'])}"
        elif issue['breaking_changes']:
            issue['message'] = f"Breaking changes detected: {', '.join(issue['breaking_changes'])}"
        else:
            issue['message'] = "Schema drift detected"
        
        self._schema_issues.append(issue)
    
    def _calculate_performance_metrics(self, group_results: Dict[str, Any], total_rows: int, pipeline_duration: float) -> Dict[str, Any]:
        """
        Calculate performance metrics for the pipeline.
        
        PHASE 3 ENHANCEMENT: Analyze processing rates and identify bottlenecks
        
        Args:
            group_results: Dictionary of group processing results
            total_rows: Total number of rows processed
            pipeline_duration: Total pipeline execution time in seconds
            
        Returns:
            Dictionary with performance analysis:
            - total_duration_seconds: Total pipeline duration
            - average_rate_rows_per_sec: Average processing rate
            - peak_rate: Highest processing rate among sources
            - slowest_source: Name of the slowest processing source
            - sources: Per-source performance breakdown
        """
        if pipeline_duration == 0:
            pipeline_duration = 0.001  # Avoid division by zero
        
        # Calculate overall average rate
        average_rate = round(total_rows / pipeline_duration, 2) if total_rows > 0 else 0
        
        # Collect per-source metrics
        source_metrics = {}
        peak_rate = 0
        slowest_source = None
        slowest_duration = 0
        
        for group_name, group_data in group_results.items():
            if group_data.get('status') == 'success' and 'source_details' in group_data:
                for source_name, source_data in group_data['source_details'].items():
                    duration = source_data.get('duration', 0)
                    rows = source_data.get('rows', 0)
                    
                    # Calculate processing rate (rows per second)
                    rate = round(rows / duration, 2) if duration > 0 and rows > 0 else 0
                    
                    # Calculate percent of total time
                    percent_of_total = round((duration / pipeline_duration) * 100, 1) if pipeline_duration > 0 else 0
                    
                    # Track peak rate
                    if rate > peak_rate:
                        peak_rate = rate
                    
                    # Track slowest source
                    if duration > slowest_duration:
                        slowest_duration = duration
                        slowest_source = source_name
                    
                    # Store performance metrics for this source
                    source_metrics[source_name] = {
                        'duration': duration,
                        'rate': rate,
                        'percent_of_total': percent_of_total,
                        'fetch_duration': source_data.get('fetch_duration', 0),
                        'cleaning_duration': source_data.get('cleaning_duration', 0),
                        'storage_duration': source_data.get('storage_duration', 0)
                    }
        
        return {
            'total_duration_seconds': round(pipeline_duration, 2),
            'average_rate_rows_per_sec': average_rate,
            'peak_rate': peak_rate,
            'slowest_source': slowest_source,
            'sources': source_metrics
        }
    
    def _clean_data(self, df: Any, config: DataSourceConfig, engine=None) -> Any:
        """
        Clean data using quality checks with enhanced schema matching.
        
        ENHANCED: Phase 1 - Schema change detection integration
        ENHANCED: Phase 4 - Track schema issues for reporting
        
        Args:
            df: Raw DataFrame
            config: Data source configuration
            engine: Optional SQLAlchemy engine for schema matching
            
        Returns:
            Cleaned DataFrame
        """
        # ENHANCED: Detect schema changes before cleaning using real SchemaDetector
        if engine:
            schema_detector = SchemaDetector(self.logger)
            schema_analysis = schema_detector.detect_schema_changes(df, config.table, config.schema, engine)
            
            if schema_analysis['requires_drop']:
                self.logger.warning(f"🚨 SCHEMA_DRIFT_DETECTED: {config.table} requires drop/recreate")
                
                if schema_analysis['breaking_changes']:
                    for change in schema_analysis['breaking_changes']:
                        self.logger.warning(f"⚠️ BREAKING_CHANGE: {change}")
                
                if schema_analysis['missing_columns']:
                    self.logger.error(f"❌ CRITICAL: Missing columns will cause failures: {schema_analysis['missing_columns']}")
                
                # PHASE 4: Track schema issue for reporting
                self._track_schema_issue(config.table, schema_analysis)
        
        # Convert config to dict for apply_cleaning with engine for schema matching
        config_dict = {
            'table': config.table,
            'schema': config.schema,
            'numeric_cols': config.numeric_cols,
            'non_numeric_cols': config.non_numeric_cols,
            'unique_keys': config.unique_keys,
            'engine': engine  # Pass engine for schema matching
        }
        
        # Layer 3 call to quality checks with enhanced schema matching
        return apply_cleaning(df, config.table, config_dict, self.logger)
    
    def _store_data_with_status(self, df: Any, config: DataSourceConfig) -> tuple:
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
        if not hasattr(self, '_storage_failures'):
            self._storage_failures = {}
        
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


def create_data_pipeline(db_service=None, logger=None):
    """
    Create data pipeline with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        
    Returns:
        DataPipeline: Configured data pipeline
    """
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.data_pipeline')
    
    return DataPipeline(db_service, logger)


__all__ = ['DataPipeline', 'create_data_pipeline']
