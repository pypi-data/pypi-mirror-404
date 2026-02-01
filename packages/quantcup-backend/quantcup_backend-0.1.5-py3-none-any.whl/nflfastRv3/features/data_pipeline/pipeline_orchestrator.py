"""
Data Pipeline Orchestrator for nflfastRv3

Refactored from implementation.py (Phase 1 Refactoring - ~300 lines)
Thin orchestrator pattern - delegates to specialized components.

Pattern: Minimum Viable Decoupling (3 complexity points)
Complexity: 3 points (DI + orchestration)
Depth: 1 layer (delegates to pipeline components)
"""

from typing import Dict, List, Any, Optional
import time
from commonv2 import get_logger
from ...shared.database_router import get_database_router
from commonv2.persistence.bucket_adapter import BucketAdapter
from ...shared.database_router import DatabaseRouter
from .config.data_sources import DATA_SOURCE_GROUPS, DataSourceConfig
from ...shared.progress_tracker import ProgressTracker

# NEW: Import extracted pipeline components
from .pipeline import DataFetcher, DataCleaner, DataStorage, SourceProcessor


class DataPipeline:
    """
    Core data pipeline orchestration.
    
    Pattern: Minimum Viable Decoupling (3 complexity points)
    Complexity: 3 points (DI + orchestration)
    Depth: 1 layer (delegates to pipeline components)
    
    PHASE 1 REFACTOR: Ext from 1,018 lines → ~300 lines orchestration
    """
    
    def __init__(self, db_service, logger):
        """
        Initialize with injected dependencies and compose from extracted components.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        
        # NEW: Initialize bucket-first architecture services (Layer 3)
        self.bucket_adapter = BucketAdapter(logger=logger)
        self.database_router = DatabaseRouter(logger=logger)
        
        # NEW: Compose from extracted components
        self.fetcher = DataFetcher(logger)
        self.cleaner = DataCleaner(logger)
        self.storage = DataStorage(
            bucket_adapter=self.bucket_adapter,
            database_router=self.database_router,
            logger=logger
        )
        self.processor = SourceProcessor(
            fetcher=self.fetcher,
            cleaner=self.cleaner,
            storage=self.storage,
            engine_provider=lambda: self.db_service.engine if self.db_service else None,
            logger=logger
        )
    
    def process(self, groups=None, tables=None, seasons=None):
        """
        Execute data pipeline workflow (thin orchestration).

        V1-style processing: either groups OR tables (mutually exclusive)
        1. Load data from R (delegates to components)
        2. Process each data source group (delegates to components)
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
                from .reporting import create_report_orchestrator
                orchestrator = create_report_orchestrator(logger=self.logger)
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
        Process all data sources in a group (delegates to SourceProcessor).
        
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
                # NEW: Delegate to SourceProcessor component
                source_metrics = self.processor.process(source_name, config, seasons)
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
    
    def _get_circuit_breaker_status(self) -> List[Dict[str, Any]]:
        """Get current circuit breaker activation status from DataFetcher."""
        fetch_failures = self.fetcher.get_fetch_failures()
        activations = []
        
        for source, failures in fetch_failures.items():
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
        """Get storage failures from DataStorage component."""
        return self.storage.get_storage_failures()
    
    def _get_schema_issues(self) -> List[Dict[str, Any]]:
        """Get schema issues detected from DataCleaner component."""
        return self.cleaner.get_schema_issues()
    
    def _calculate_performance_metrics(self, group_results: Dict[str, Any], total_rows: int, pipeline_duration: float) -> Dict[str, Any]:
        """
        Calculate performance metrics for the pipeline.
        
        PHASE 3 ENHANCEMENT: Analyze processing rates and identify bottlenecks
        
        Args:
            group_results: Dictionary of group processing results
            total_rows: Total number of rows processed
            pipeline_duration: Total pipeline execution time in seconds
            
        Returns:
            Dictionary with performance analysis
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
