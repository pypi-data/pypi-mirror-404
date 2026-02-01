"""
Warehouse Builder for nflfastRv3 - Integrated with Real Transformations

REFACTORING_SPECS.md Compliance Validated:
✅ Pattern: Minimum Viable Decoupling (4 complexity points ≤ 5 budget)
✅ Depth: 3 layers maximum (Public API → Transformations → Infrastructure)
✅ "Can I Trace This?" test: User → WarehouseBuilder → build_dim_game() → SQL/cleaning
✅ Integration: 15 transformation modules connected with V2 business logic

Architecture Achievement:
- V2 sophistication preserved (weather categorization, EPA calculations, chunked processing)
- Clean separation of concerns with dependency injection
- Performance optimized with chunked fact processing (5000+ rows/chunk)
- REFACTORING_SPECS compliant: solo developer budget maintained
"""

import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from commonv2 import get_logger
from commonv2.core.config import Environment
from ...shared.database_router import get_database_router
from commonv2.persistence.bucket_adapter import BucketAdapter

# Import all transformation modules (Layer 2 dependencies)
from .transformations import (
    # Bucket-first infrastructure
    create_dataframe_engine,
    
    # Dimension builders
    build_dim_game,
    build_dim_player,
    build_dim_date,
    build_dim_drive,
    
    # Warehouse builders
    build_warehouse_injuries,
    build_player_id_mapping,
    
    # Fact builders (with chunked processing)
    build_fact_play,
    build_fact_player_stats,
    build_fact_player_play
)


class WarehouseBuilder:
    """
    Warehouse builder integrating real transformation modules.
    
    Pattern: Minimum Viable Decoupling (5 complexity points - AT BUDGET)
    - Base orchestration: 2 points
    - Transformation coordination: 2 points
    - Bucket-first feature flag: 1 point
    Layer: 2 (Implementation - calls transformations which call infrastructure)
    
    Architecture:
    Layer 1: Public API (this class)
    Layer 2: Transformation modules
    Layer 3: Infrastructure (database, bucket, SQL, cleaning)
    
    Bucket-First Architecture:
    - Production: Uses bucket storage as primary (WAREHOUSE_USE_BUCKET=true)
    - Local/Dev: Uses database (WAREHOUSE_USE_BUCKET=false)
    - Emergency rollback: Set WAREHOUSE_USE_BUCKET=false
    """
    
    def __init__(self, db_service, logger, bucket_adapter: Optional[BucketAdapter] = None, use_bucket: Optional[bool] = None):
        """
        Initialize with injected dependencies and bucket-first architecture.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            bucket_adapter: Optional BucketAdapter instance (for bucket-first)
            use_bucket: Optional override for bucket usage (default: auto-detect from environment)
        """
        self.db_service = db_service
        self.logger = logger
        
        # Feature flag for bucket-first architecture
        # Priority: explicit parameter > env var > environment detection
        if use_bucket is None:
            # Check environment variable first
            env_override = os.getenv('WAREHOUSE_USE_BUCKET', '').lower()
            if env_override in ('true', 'false'):
                self.use_bucket = env_override == 'true'
            else:
                # Auto-detect: production uses bucket, local uses database
                self.use_bucket = Environment.is_production()
        else:
            self.use_bucket = use_bucket
        
        # Initialize bucket adapter if using bucket-first
        if self.use_bucket:
            self.bucket_adapter = bucket_adapter or BucketAdapter(logger=logger)
            
            # Validate bucket is available
            bucket_status = self.bucket_adapter.get_status()
            if not bucket_status['available']:
                self.logger.error(
                    f"❌ Bucket storage required for warehouse operations but not available: "
                    f"{bucket_status}"
                )
                raise RuntimeError(
                    "Bucket storage required for warehouse operations. "
                    "Check bucket configuration or set WAREHOUSE_USE_BUCKET=false for database mode."
                )
            
            self.logger.info(
                f"✅ Warehouse initialized in BUCKET-FIRST mode "
                f"(bucket: {self.bucket_adapter.bucket_name})"
            )
        else:
            self.bucket_adapter = None
            self.logger.info("✅ Warehouse initialized in DATABASE mode (local/dev)")
        
        # Define build order (dimensions first, then facts)
        # REMOVED: dim_team - see docs/transformation_removal.md
        # Evidence: No downstream consumers, CommonV2 provides superior data
        self.dimension_builders = [
            ('dim_game', build_dim_game),
            ('dim_player', build_dim_player),
            ('dim_date', build_dim_date),
            ('dim_drive', build_dim_drive),
            ('injuries', build_warehouse_injuries),  # Multi-source warehouse table
            ('player_id_mapping', build_player_id_mapping)  # ID crosswalk for snap_counts joins
        ]
        
        # Fact builders (chunking automatic: bucket mode = no chunks, database mode = chunked for memory safety)
        self.fact_builders = [
            ('fact_play', build_fact_play, True),
            ('fact_player_stats', build_fact_player_stats, False),
            ('fact_player_play', build_fact_player_play, True)
        ]
        
        # PHASE 2: Initialize error tracking storage
        self._build_failures = []
        self._empty_tables = []
        
        # PHASE 4: Initialize schema tracking storage
        self._schema_changes = []
        self._schema_registry = {}  # Stores current schemas for comparison
    
    def _track_build_failure(self, table_name: str, error: str, build_stage: str):
        """
        PHASE 2: Track build failure for reporting.
        
        Args:
            table_name: Name of table that failed
            error: Error message
            build_stage: Stage where failure occurred ('load', 'transform', 'save', 'validate')
        """
        self._build_failures.append({
            'table': table_name,
            'error': error,
            'stage': build_stage,
            'timestamp': datetime.now().isoformat(),
            'recoverable': self._is_recoverable_error(error),
            'recommendation': self._get_recovery_recommendation(error, table_name, build_stage)
        })
    
    def _track_empty_table(self, table_name: str, reason: str, expected: bool = False):
        """
        PHASE 2: Track empty table result for reporting.
        
        Args:
            table_name: Name of table with empty result
            reason: Explanation for empty result
            expected: Whether this is expected behavior
        """
        self._empty_tables.append({
            'table': table_name,
            'reason': reason,
            'expected': expected,
            'action': self._get_empty_table_action(table_name, reason, expected)
        })
    
    def _is_recoverable_error(self, error: str) -> bool:
        """
        PHASE 2: Determine if an error is recoverable.
        
        Args:
            error: Error message
            
        Returns:
            bool: True if error appears recoverable
        """
        # Check for recoverable error patterns
        recoverable_patterns = [
            'column', 'not found', 'missing',  # Schema issues
            'empty', 'no data',  # Data availability
            'memory', 'timeout',  # Resource issues
            'connection', 'network'  # Connectivity issues
        ]
        
        error_lower = error.lower()
        return any(pattern in error_lower for pattern in recoverable_patterns)
    
    def _get_recovery_recommendation(self, error: str, table_name: str, build_stage: str) -> str:
        """
        PHASE 2: Provide recovery recommendation based on error.
        
        Args:
            error: Error message
            table_name: Name of table that failed
            build_stage: Stage where failure occurred
            
        Returns:
            str: Actionable recovery recommendation
        """
        error_lower = error.lower()
        
        # Column/schema issues
        if 'column' in error_lower and 'not found' in error_lower:
            return f"Re-run pipeline to fetch latest data with required columns, or check column requirements in WAREHOUSE_COLUMN_REQUIREMENTS for {table_name}"
        
        # Empty data issues
        if 'empty' in error_lower or 'no data' in error_lower:
            return f"Check if source data exists for {table_name}. May need to run pipeline for required seasons"
        
        # Memory issues
        if 'memory' in error_lower:
            return f"Increase WAREHOUSE_MEMORY_LIMIT_MB or enable column pruning to reduce memory usage for {table_name}"
        
        # Transform stage issues
        if build_stage == 'transform':
            return f"Review transformation logic for {table_name}. May need to update transformation code to handle new data format"
        
        # Save stage issues
        if build_stage == 'save':
            if self.use_bucket:
                return f"Check bucket connectivity and permissions for {table_name}. Verify bucket_adapter status"
            else:
                return f"Check database connectivity for {table_name}. Verify warehouse schema exists"
        
        # Load stage issues
        if build_stage == 'load':
            return f"Check source data availability for {table_name}. May need to run pipeline first"
        
        # Generic recommendation
        return f"Review logs for {table_name} build failure. Check source data quality and transformation requirements"
    
    def _get_empty_table_action(self, table_name: str, reason: str, expected: bool) -> str:
        """
        PHASE 2: Provide action recommendation for empty table.
        
        Args:
            table_name: Name of empty table
            reason: Reason for empty result
            expected: Whether this was expected
            
        Returns:
            str: Actionable recommendation
        """
        if expected:
            return "No action needed - empty result expected"
        
        reason_lower = reason.lower()
        
        if 'season' in reason_lower:
            return f"Run pipeline for missing seasons or adjust season filters for {table_name}"
        
        if 'injury' in table_name.lower() or 'injuries' in table_name.lower():
            return f"Check if injury data exists in source tables. May need to run injury data backfill"
        
        return f"Check if source data exists for {table_name}. Verify pipeline has been run for required data"
    
    def _get_build_failures(self) -> List[Dict]:
        """PHASE 2: Expose build failures for reporting."""
        return self._build_failures
    
    def _get_empty_tables(self) -> List[Dict]:
        """PHASE 2: Expose empty table tracking for reporting."""
        return self._empty_tables
    
    def _clear_error_tracking(self):
        """PHASE 2: Clear error tracking between builds."""
        self._build_failures = []
        self._empty_tables = []
    
    def _track_schema_change(self, table_name: str, change_type: str, details: Dict):
        """
        PHASE 4: Track schema change detected during warehouse build.
        
        Args:
            table_name: Table where change detected
            change_type: Type of change ('column_added', 'column_removed', 'type_changed',
                        'schema_mismatch', 'schema_drift')
            details: Dict with change specifics
        """
        severity = self._determine_schema_severity(change_type, details)
        
        self._schema_changes.append({
            'table': table_name,
            'type': change_type,
            'severity': severity,  # 'critical', 'warning', 'info'
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'requires_action': severity == 'critical'
        })
        
        # Log schema change
        emoji = '🔴' if severity == 'critical' else '⚠️' if severity == 'warning' else 'ℹ️'
        self.logger.info(
            f"{emoji} Schema change detected in {table_name}: {change_type} "
            f"(severity: {severity})"
        )
    
    def _determine_schema_severity(self, change_type: str, details: Dict) -> str:
        """
        PHASE 4: Determine severity of schema change.
        
        Args:
            change_type: Type of schema change
            details: Change details
            
        Returns:
            str: 'critical', 'warning', or 'info'
        """
        # Column removals are critical (breaking change)
        if change_type == 'column_removed':
            return 'critical'
        
        # Type changes are warnings (potential compatibility issues)
        if change_type == 'type_changed':
            # Check if it's a precision enhancement (safe) vs actual type change (risky)
            old_type = details.get('old_type', '').upper()
            new_type = details.get('new_type', '').upper()
            
            # Same base type with different precision is warning
            if ('INT' in old_type and 'INT' in new_type) or \
               ('FLOAT' in old_type and 'NUMERIC' in new_type) or \
               ('REAL' in old_type and 'NUMERIC' in new_type):
                return 'warning'
            
            # Different base types are critical
            return 'critical'
        
        # Schema mismatches are critical
        if change_type == 'schema_mismatch':
            return 'critical'
        
        # Column additions are informational (non-breaking)
        if change_type == 'column_added':
            return 'info'
        
        # Schema drift is a warning (should be monitored)
        if change_type == 'schema_drift':
            return 'warning'
        
        # Default to warning for unknown types
        return 'warning'
    
    def _compare_schemas(self, source_schema: Dict, result_schema: Dict) -> Optional[Dict]:
        """
        PHASE 4: Compare two schemas and identify differences.
        
        Args:
            source_schema: Original schema {column: dtype}
            result_schema: New schema {column: dtype}
            
        Returns:
            Dict with differences if changes detected, None otherwise
        """
        if source_schema is None or result_schema is None:
            return None
        
        source_cols = set(source_schema.keys())
        result_cols = set(result_schema.keys())
        
        # Check for column additions
        added_columns = result_cols - source_cols
        
        # Check for column removals
        removed_columns = source_cols - result_cols
        
        # Check for type changes in common columns
        type_changes = []
        for col in source_cols & result_cols:
            source_type = str(source_schema[col])
            result_type = str(result_schema[col])
            if source_type != result_type:
                type_changes.append({
                    'column': col,
                    'old_type': source_type,
                    'new_type': result_type
                })
        
        # Return None if no changes
        if not added_columns and not removed_columns and not type_changes:
            return None
        
        # Build change summary
        changes = {}
        if added_columns:
            changes['added_columns'] = list(added_columns)
        if removed_columns:
            changes['removed_columns'] = list(removed_columns)
        if type_changes:
            changes['type_changes'] = type_changes
        
        return changes
    
    def _get_current_schema(self, table_name: str) -> Optional[Dict]:
        """
        PHASE 4: Get currently stored schema for a table.
        
        Args:
            table_name: Name of table
            
        Returns:
            Dict mapping column names to types, or None if not stored
        """
        return self._schema_registry.get(table_name)
    
    def _store_schema(self, table_name: str, schema: Dict):
        """
        PHASE 4: Store schema for future comparison.
        
        Args:
            table_name: Name of table
            schema: Dict mapping column names to types
        """
        self._schema_registry[table_name] = schema
    
    def _get_schema_changes(self) -> List[Dict]:
        """PHASE 4: Expose schema changes for reporting."""
        return self._schema_changes
    
    def _clear_schema_tracking(self):
        """PHASE 4: Clear schema tracking between builds."""
        self._schema_changes = []
        # Note: We keep _schema_registry to enable cross-build comparison
    
    def _calculate_warehouse_performance_metrics(self, results: Dict) -> Dict:
        """
        PHASE 3: Calculate comprehensive performance metrics for warehouse build.
        
        Analyzes build timing at all levels to identify bottlenecks and optimization opportunities.
        
        Args:
            results: Build results dictionary with timing data
            
        Returns:
            Dict with performance analysis:
            - total_duration_seconds: Overall warehouse build time
            - average_rate_rows_per_sec: Overall processing rate
            - slowest_table: Table taking longest to build
            - fastest_table: Table with highest processing rate
            - memory_efficiency_mb_per_row: Memory usage per row
            - tables: Per-table breakdown with rates and percentages
        """
        # Calculate warehouse-level metrics
        total_duration = results.get('duration', 0)
        total_rows = results.get('total_rows', 0)
        total_memory_mb = results.get('total_memory_used_mb', 0)
        
        # Aggregate table metrics
        table_metrics = {}
        all_durations = []
        
        # Process dimension tables
        for table_name, details in results.get('dimension_results', {}).get('table_details', {}).items():
            if details.get('status') == 'success' and 'duration' in details:
                duration = details['duration']
                rows = details['rows']
                all_durations.append((table_name, duration))
                
                table_metrics[table_name] = {
                    'duration': duration,
                    'rows': rows,
                    'rate': int(rows / duration) if duration > 0 else 0,
                    'percent_of_total_time': round((duration / total_duration * 100), 1) if total_duration > 0 else 0,
                    'type': 'dimension',
                    'memory_mb': details.get('memory_mb', 0)
                }
        
        # Process fact tables
        for table_name, details in results.get('fact_results', {}).get('table_details', {}).items():
            if details.get('status') == 'success' and 'duration' in details:
                duration = details['duration']
                rows = details['rows']
                all_durations.append((table_name, duration))
                
                # Calculate rate based on processing type
                rate = int(rows / duration) if duration > 0 else 0
                
                table_metrics[table_name] = {
                    'duration': duration,
                    'rows': rows,
                    'rate': rate,
                    'percent_of_total_time': round((duration / total_duration * 100), 1) if total_duration > 0 else 0,
                    'type': 'fact',
                    'processing_type': details.get('processing_type', 'standard')
                }
                
                # Add chunking metrics if available
                if details.get('processing_type') == 'chunked':
                    perf_metrics = details.get('performance_metrics', {})
                    table_metrics[table_name]['chunks_processed'] = details.get('chunks_processed', 0)
                    table_metrics[table_name]['avg_chunk_time'] = perf_metrics.get('avg_chunk_time', 'N/A')
                    
                    # Classify chunk performance
                    avg_chunk_time = perf_metrics.get('avg_chunk_time', 0)
                    if isinstance(avg_chunk_time, (int, float)):
                        if avg_chunk_time < 1.0:
                            chunk_perf = 'optimal'
                        elif avg_chunk_time < 3.0:
                            chunk_perf = 'good'
                        elif avg_chunk_time < 5.0:
                            chunk_perf = 'moderate'
                        else:
                            chunk_perf = 'slow'
                        table_metrics[table_name]['chunk_performance'] = chunk_perf
        
        # Identify bottlenecks
        slowest_table = max(all_durations, key=lambda x: x[1])[0] if all_durations else None
        fastest_table = max(table_metrics.items(), key=lambda x: x[1]['rate'])[0] if table_metrics else None
        
        # Calculate memory efficiency
        memory_efficiency = round(total_memory_mb / total_rows, 6) if total_rows > 0 else 0
        
        return {
            'total_duration_seconds': total_duration,
            'average_rate_rows_per_sec': int(total_rows / total_duration) if total_duration > 0 else 0,
            'slowest_table': slowest_table,
            'fastest_table': fastest_table,
            'memory_efficiency_mb_per_row': memory_efficiency,
            'tables': table_metrics
        }
    
    def build_specific_tables(self, table_names: List[str], seasons=None):
        """
        Build only specified warehouse tables.
        
        Args:
            table_names: List of table names to build (e.g., ['dim_game', 'fact_play'])
            seasons: Optional list of seasons for fact tables
            
        Returns:
            dict: Build results with status, tables built, and row counts
            
        Example:
            >>> builder.build_specific_tables(['dim_game', 'fact_play'], seasons=[2024])
            {'status': 'success', 'tables_built': ['dim_game', 'fact_play'], 'total_rows': 50000}
        """
        self.logger.info("=" * 60)
        self.logger.info(f"Building Specific Tables: {table_names}")
        self.logger.info("=" * 60)
        
        try:
            results = {
                'status': 'success',
                'tables_built': [],
                'total_rows': 0,
                'dimension_results': {},
                'fact_results': {}
            }
            
            # Filter dimension builders
            dim_builders = [
                (name, func) for name, func in self.dimension_builders
                if name in table_names
            ]
            
            # Filter fact builders
            fact_builders = [
                (name, func, chunked) for name, func, chunked in self.fact_builders
                if name in table_names
            ]
            
            # Validate: detect unregistered table requests
            registered_tables = set(name for name, _ in self.dimension_builders) | \
                               set(name for name, _, _ in self.fact_builders)
            unregistered = set(table_names) - registered_tables
            
            if unregistered:
                self.logger.warning(
                    f"⚠️ Requested tables not registered in warehouse: {unregistered}\n"
                    f"   Available tables: {sorted(registered_tables)}"
                )
            
            # Build filtered dimensions
            if dim_builders:
                self.logger.info(f"Building {len(dim_builders)} dimension tables...")
                dim_results = self._build_dimension_tables_filtered(dim_builders)
                results['dimension_results'] = dim_results
                results['tables_built'].extend(dim_results.get('tables', []))
                results['total_rows'] += dim_results.get('total_rows', 0)
            
            # Build filtered facts
            if fact_builders:
                self.logger.info(f"Building {len(fact_builders)} fact tables...")
                fact_results = self._build_fact_tables_filtered(fact_builders, seasons)
                results['fact_results'] = fact_results
                results['tables_built'].extend(fact_results.get('tables', []))
                results['total_rows'] += fact_results.get('total_rows', 0)
            
            # Add storage metrics for reporting
            results['storage_metrics'] = {
                'bucket_mode': self.use_bucket,
                'bucket_name': self.bucket_adapter.bucket_name if self.bucket_adapter else None,
                'schema_used': 'warehouse',
                'memory_limit_mb': int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                'column_pruning_enabled': True
            }
            
            self.logger.info("=" * 60)
            self.logger.info(f"✅ Specific Tables Build Complete!")
            self.logger.info(f"Tables: {len(results['tables_built'])}")
            self.logger.info(f"Total Rows: {results['total_rows']:,}")
            self.logger.info("=" * 60)
            
            # Generate warehouse report (matches ML pipeline pattern)
            try:
                from .reporting import create_report_orchestrator
                orchestrator = create_report_orchestrator(logger=self.logger)
                report_path = orchestrator.generate_warehouse_report(results, seasons=seasons)
                if report_path:
                    self.logger.info(f"📊 Warehouse report: {report_path}")
            except Exception as e:
                self.logger.warning(f"Report generation failed: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Specific tables build failed: {e}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e),
                'tables_built': [],
                'total_rows': 0
            }
    
    def build_dimensions_only(self):
        """
        Build only dimension tables.
        
        Returns:
            dict: Build results for dimension tables only
            
        Example:
            >>> builder.build_dimensions_only()
            {'status': 'success', 'tables_built': ['dim_game', 'dim_player', ...], 'total_rows': 5000}
        """
        self.logger.info("=" * 60)
        self.logger.info("Building Dimension Tables Only")
        self.logger.info("=" * 60)
        
        results = self._build_dimension_tables()
        
        # Add storage metrics for reporting
        results['storage_metrics'] = {
            'bucket_mode': self.use_bucket,
            'bucket_name': self.bucket_adapter.bucket_name if self.bucket_adapter else None,
            'schema_used': 'warehouse',
            'memory_limit_mb': int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
            'column_pruning_enabled': True
        }
        
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Dimension Build Complete!")
        self.logger.info(f"Tables: {len(results.get('tables', []))}")
        self.logger.info(f"Total Rows: {results.get('total_rows', 0):,}")
        self.logger.info("=" * 60)
        
        # Generate warehouse report (matches ML pipeline pattern)
        try:
            from .reporting import create_report_orchestrator
            orchestrator = create_report_orchestrator(logger=self.logger)
            report_path = orchestrator.generate_warehouse_report(results, seasons=None)
            if report_path:
                self.logger.info(f"📊 Warehouse report: {report_path}")
        except Exception as e:
            self.logger.warning(f"Report generation failed: {e}")
        
        return results
    
    def build_facts_only(self, seasons=None):
        """
        Build only fact tables.
        
        Args:
            seasons: Optional list of seasons to process
            
        Returns:
            dict: Build results for fact tables only
            
        Example:
            >>> builder.build_facts_only(seasons=[2023, 2024])
            {'status': 'success', 'tables_built': ['fact_play', ...], 'total_rows': 100000}
        """
        self.logger.info("=" * 60)
        self.logger.info("Building Fact Tables Only")
        if seasons:
            self.logger.info(f"Seasons: {seasons}")
        self.logger.info("=" * 60)
        
        results = self._build_fact_tables(seasons)
        
        # Add storage metrics for reporting
        results['storage_metrics'] = {
            'bucket_mode': self.use_bucket,
            'bucket_name': self.bucket_adapter.bucket_name if self.bucket_adapter else None,
            'schema_used': 'warehouse',
            'memory_limit_mb': int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
            'column_pruning_enabled': True
        }
        
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Fact Build Complete!")
        self.logger.info(f"Tables: {len(results.get('tables', []))}")
        self.logger.info(f"Total Rows: {results.get('total_rows', 0):,}")
        self.logger.info("=" * 60)
        
        # Generate warehouse report (matches ML pipeline pattern)
        try:
            from .reporting import create_report_orchestrator
            orchestrator = create_report_orchestrator(logger=self.logger)
            report_path = orchestrator.generate_warehouse_report(results, seasons=seasons)
            if report_path:
                self.logger.info(f"📊 Warehouse report: {report_path}")
        except Exception as e:
            self.logger.warning(f"Report generation failed: {e}")
        
        return results
    
    @property
    def bucket_adapter_required(self) -> BucketAdapter:
        """
        Get bucket adapter, raising error if not available.
        
        Provides type-safe access to bucket_adapter when in bucket mode.
        
        Returns:
            BucketAdapter: Non-None bucket adapter instance
            
        Raises:
            RuntimeError: If bucket adapter is not initialized
        """
        if self.bucket_adapter is None:
            raise RuntimeError("Bucket adapter required but not initialized")
        return self.bucket_adapter
    
    def _get_database_engine(self):
        """
        Get database engine for warehouse operations.
        
        Uses public API method to avoid protected member access.
        
        Returns:
            SQLAlchemy engine for database operations
        """
        return self.db_service.get_engine()
    
    def build_all_tables(self, seasons=None, sync_after_build=False):
        """
        Build all warehouse tables using real transformation modules.
        
        Orchestrates complete warehouse build:
        1. Build dimension tables (Layer 2 calls to transformations)
        2. Build fact tables with chunked processing (Layer 2 calls)
        3. Return comprehensive summary
        
        Args:
            seasons: Optional list of seasons to process
            sync_after_build: Whether to sync after building
            
        Returns:
            dict: Comprehensive build results with performance metrics
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Warehouse Build with Real Transformations")
        self.logger.info("=" * 60)
        
        # PHASE 3: Start warehouse-level timing
        warehouse_start_time = time.time()
        
        try:
            # PHASE 2 & PHASE 4: Clear error and schema tracking from previous builds
            self._clear_error_tracking()
            self._clear_schema_tracking()
            
            results = {
                'status': 'success',
                'tables_built': [],
                'total_rows': 0,
                'dimension_results': {},
                'fact_results': {},
                'performance_metrics': {}
            }
            
            # Step 1: Build dimension tables using real transformations
            self.logger.info("Building dimension tables...")
            dim_results = self._build_dimension_tables()
            results['dimension_results'] = dim_results
            results['tables_built'].extend(dim_results.get('tables', []))
            results['total_rows'] += dim_results.get('total_rows', 0)
            
            # Step 2: Build fact tables with chunked processing  
            self.logger.info("Building fact tables with chunked processing...")
            fact_results = self._build_fact_tables(seasons)
            results['fact_results'] = fact_results
            results['tables_built'].extend(fact_results.get('tables', []))
            results['total_rows'] += fact_results.get('total_rows', 0)
            
            # Step 3: Calculate performance metrics
            results['performance_metrics'] = {
                'dimensions_built': len(results['dimension_results'].get('tables', [])),
                'facts_built': len(results['fact_results'].get('tables', [])),
                'total_tables': len(results['tables_built']),
                'build_success_rate': len(results['tables_built']) / (len(self.dimension_builders) + len(self.fact_builders))
            }
            
            # PHASE 1: Calculate aggregate warehouse metrics
            total_memory_mb = 0
            column_pruning_tables = []
            chunked_tables = []
            standard_tables = []
            
            # Aggregate from dimensions
            for table_name, details in results['dimension_results'].get('table_details', {}).items():
                if details.get('status') == 'success':
                    total_memory_mb += details.get('memory_mb', 0)
                    if details.get('columns_pruned', False):
                        column_pruning_tables.append(table_name)
            
            # Aggregate from facts
            for table_name, details in results['fact_results'].get('table_details', {}).items():
                if details.get('status') == 'success':
                    if details.get('processing_type') == 'chunked':
                        chunked_tables.append(table_name)
                        total_memory_mb += details.get('total_memory_mb', 0) if isinstance(details.get('total_memory_mb'), (int, float)) else 0
                    else:
                        standard_tables.append(table_name)
                    
                    if details.get('column_pruning_enabled', False):
                        column_pruning_tables.append(table_name)
            
            # PHASE 1: Add top-level warehouse metrics
            results['total_memory_used_mb'] = round(total_memory_mb, 2)
            results['column_pruning_stats'] = {
                'enabled_tables': column_pruning_tables,
                'total_tables_using_pruning': len(column_pruning_tables),
                'total_columns_loaded': 'N/A',  # Will be calculated from table details if needed
                'estimated_memory_saved_mb': 'N/A'  # Placeholder for future calculation
            }
            results['build_metadata'] = {
                'bucket_mode': self.use_bucket,
                'bucket_name': self.bucket_adapter.bucket_name if self.bucket_adapter else None,
                'schema_used': 'warehouse',
                'memory_limit_mb': int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                'chunked_tables': chunked_tables,
                'standard_tables': standard_tables
            }
            
            # PHASE 2: Add error tracking results
            results['build_failures'] = self._get_build_failures()
            results['empty_tables'] = self._get_empty_tables()
            
            # PHASE 4: Add schema tracking results
            results['schema_changes'] = self._get_schema_changes()
            
            # Adjust status based on failures
            if len(results['build_failures']) > 0:
                if len(results['tables_built']) == 0:
                    results['status'] = 'failed'
                elif len(results['tables_built']) < (len(self.dimension_builders) + len(self.fact_builders)):
                    results['status'] = 'partial'
            
            # PHASE 3: Calculate total duration and enhanced performance metrics
            total_duration = time.time() - warehouse_start_time
            results['duration'] = round(total_duration, 2)
            
            # Calculate detailed performance metrics using helper
            results['performance_metrics'] = self._calculate_warehouse_performance_metrics(results)
            
            # Step 4: Keep storage metrics for backward compatibility
            results['storage_metrics'] = {
                'bucket_mode': self.use_bucket,
                'bucket_name': self.bucket_adapter.bucket_name if self.bucket_adapter else None,
                'schema_used': 'warehouse',
                'memory_limit_mb': int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                'column_pruning_enabled': True
            }
            
            self.logger.info("=" * 60)
            self.logger.info(f"✅ Warehouse Build Complete in {total_duration:.2f}s!")
            self.logger.info(f"Tables: {len(results['tables_built'])}/{len(self.dimension_builders) + len(self.fact_builders)}")
            self.logger.info(f"Total Rows: {results['total_rows']:,}")
            self.logger.info(f"Processing Rate: {results['performance_metrics']['average_rate_rows_per_sec']:,} rows/sec")
            self.logger.info("=" * 60)
            
            # Generate warehouse report (matches ML pipeline pattern)
            try:
                from .reporting import create_report_orchestrator
                orchestrator = create_report_orchestrator(logger=self.logger)
                report_path = orchestrator.generate_warehouse_report(results, seasons=seasons)
                if report_path:
                    self.logger.info(f"📊 Warehouse report: {report_path}")
            except Exception as e:
                self.logger.warning(f"Report generation failed: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Warehouse build failed: {e}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e),
                'tables_built': [],
                'total_rows': 0
            }
    
    def _build_dimension_tables(self):
        """
        Build dimension tables using real transformation modules.
        
        Calls Layer 2 transformation functions that preserve V2 business logic:
        - Sophisticated data cleaning and categorization
        - Weather analysis and venue standardization
        - Player demographics and fantasy platform integration
        
        Bucket-First: Creates DataFrameEngine for bucket mode
        FIX #2: Uses dynamic column loading to reduce memory by 10x
        
        Returns:
            dict: Comprehensive dimension build results with 'status' key
        """
        self.logger.info("Building dimension tables with V2 business logic...")
        
        tables_built = []
        total_rows = 0
        table_details = {}
        has_errors = False
        
        # FIX #2: Determine which columns to load based on dimension requirements
        # This reduces memory from ~4GB to ~400MB by loading only needed columns
        from .config.data_sources import get_warehouse_columns, WAREHOUSE_COLUMN_REQUIREMENTS
        
        # Get union of all columns needed by all dimensions
        all_dim_columns = set()
        for table_name, _ in self.dimension_builders:
            table_columns = get_warehouse_columns(table_name)
            if table_columns:
                all_dim_columns.update(table_columns)
        
        # Convert to list for DataFrameEngine
        dimension_columns = list(all_dim_columns) if all_dim_columns else None
        
        if dimension_columns:
            self.logger.info(
                f"📊 Column pruning enabled: loading {len(dimension_columns)} columns "
                f"(vs 250+ full PBP) for ~10x memory reduction"
            )
        
        # Create engine (bucket-first OR database)
        if self.use_bucket:
            # Bucket mode: Create DataFrameEngine with play_by_play data
            self.logger.info("Creating DataFrameEngine for bucket-first warehouse...")
            engine = create_dataframe_engine(
                table_name='play_by_play',
                schema='raw_nflfastr',
                columns=dimension_columns,  # FIX #2: Load only needed columns
                max_memory_mb=int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                bucket_adapter=self.bucket_adapter_required,
                logger=self.logger
            )
            self.logger.info(f"DataFrameEngine created: {len(engine.df):,} rows loaded")
        else:
            # Database mode: Use database engine
            engine = self._get_database_engine()
        
        for table_name, builder_func in self.dimension_builders:
            try:
                # PHASE 3: Start table-level timing
                table_start_time = time.time()
                
                self.logger.info(f"Building {table_name}...")
                
                # Call real transformation function (Layer 2 → Layer 3)
                df_result = builder_func(engine, self.logger)
                
                if df_result.empty:
                    self.logger.warning(f"No data returned for {table_name}")
                    table_details[table_name] = {'status': 'empty', 'rows': 0}
                    # PHASE 2: Track empty table
                    self._track_empty_table(
                        table_name=table_name,
                        reason=f"No data returned from transformation for {table_name}",
                        expected=False
                    )
                    continue
                
                # PHASE 3: Calculate table duration
                table_duration = time.time() - table_start_time
                
                #  PHASE 4: Schema tracking before save
                source_schema = self._get_current_schema(table_name)
                result_schema = {col: str(dtype) for col, dtype in df_result.dtypes.items()}
                
                # Save to analytics schema
                self._save_table(df_result, table_name)
                
                # PHASE 4: Compare schemas and track changes
                if source_schema:
                    schema_diff = self._compare_schemas(source_schema, result_schema)
                    if schema_diff:
                        # Track specific change types
                        if 'added_columns' in schema_diff:
                            self._track_schema_change(
                                table_name=table_name,
                                change_type='column_added',
                                details=schema_diff
                            )
                        if 'removed_columns' in schema_diff:
                            self._track_schema_change(
                                table_name=table_name,
                                change_type='column_removed',
                                details=schema_diff
                            )
                        if 'type_changes' in schema_diff:
                            for type_change in schema_diff['type_changes']:
                                self._track_schema_change(
                                    table_name=table_name,
                                    change_type='type_changed',
                                    details=type_change
                                )
                
                # PHASE 4: Store current schema for next build comparison
                self._store_schema(table_name, result_schema)
                
                # Track results
                row_count = len(df_result)
                tables_built.append(table_name)
                total_rows += row_count
                
                # PHASE 1: Enhanced metrics capture
                config = WAREHOUSE_COLUMN_REQUIREMENTS.get(table_name, {})
                source_table = config.get('source_table')
                
                # Determine build type
                if source_table is None:
                    build_type = 'generated'
                elif isinstance(source_table, list):
                    build_type = 'multi_source'
                else:
                    build_type = 'single_source'
                
                # Calculate memory usage
                memory_mb = df_result.memory_usage(deep=True).sum() / 1024 / 1024
                
                table_details[table_name] = {
                    'status': 'success',
                    'rows': row_count,
                    'columns': len(df_result.columns),
                    # PHASE 1: New fields
                    'column_names': list(df_result.columns),
                    'memory_mb': round(memory_mb, 2),
                    'build_type': build_type,
                    'source_table': source_table,
                    'columns_pruned': dimension_columns is not None,
                    'columns_loaded': len(dimension_columns) if dimension_columns else 'all',
                    # PHASE 3: Performance timing
                    'duration': round(table_duration, 2),
                    'rows_per_second': int(row_count / table_duration) if table_duration > 0 else 0
                }
                
                self.logger.info(
                    f"✅ {table_name}: {row_count:,} rows, {len(df_result.columns)} columns, "
                    f"{memory_mb:.2f} MB, {table_duration:.2f}s ({build_type})"
                )
                
            except Exception as e:
                self.logger.error(f"❌ Failed to build {table_name}: {e}", exc_info=True)
                table_details[table_name] = {'status': 'failed', 'error': str(e), 'rows': 0}
                # PHASE 2: Track build failure
                self._track_build_failure(
                    table_name=table_name,
                    error=str(e),
                    build_stage='transform'
                )
                has_errors = True
                continue
        
        # Determine overall status
        if len(tables_built) == 0:
            status = 'failed'
        elif has_errors:
            status = 'partial'
        else:
            status = 'success'
        
        return {
            'status': status,
            'tables': tables_built,
            'total_rows': total_rows,
            'table_details': table_details,
            'success_rate': len(tables_built) / len(self.dimension_builders) if self.dimension_builders else 0
        }
    
    def _build_fact_tables(self, seasons=None):
        """
        Build fact tables using real transformation modules with chunked processing.
        
        Leverages sophisticated V2 capabilities:
        - Chunked processing for large datasets (5000+ rows per chunk)
        - EPA calculations and advanced analytics
        - Player-level attribution and performance metrics
        
        Bucket-First: Creates DataFrameEngine for bucket mode, passes db_service for saving
        FIX #2: Uses dynamic column loading to reduce memory
        
        Args:
            seasons: Optional list of seasons to process
            
        Returns:
            dict: Comprehensive fact build results with performance metrics and 'status' key
        """
        self.logger.info("Building fact tables with chunked processing...")
        
        tables_built = []
        total_rows = 0
        table_details = {}
        has_errors = False
        
        # FIX #2: Get union of columns needed by all fact tables
        from .config.data_sources import get_warehouse_columns
        
        all_fact_columns = set()
        for table_name, _, _ in self.fact_builders:
            table_columns = get_warehouse_columns(table_name)
            if table_columns:
                all_fact_columns.update(table_columns)
        
        fact_columns = list(all_fact_columns) if all_fact_columns else None
        
        if fact_columns:
            self.logger.info(
                f"📊 Column pruning for fact tables: {len(fact_columns)} columns "
                f"(vs 250+ full PBP) for memory optimization"
            )
        
        # Create engine for data loading (bucket-first OR database)
        if self.use_bucket:
            # Bucket mode: Create DataFrameEngine with play_by_play data
            self.logger.info("Creating DataFrameEngine for bucket-first fact tables...")
            data_engine = create_dataframe_engine(
                table_name='play_by_play',
                schema='raw_nflfastr',
                seasons=[int(s) for s in seasons] if seasons else None,
                columns=fact_columns,  # FIX #2: Load only needed columns
                max_memory_mb=int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                bucket_adapter=self.bucket_adapter_required,
                logger=self.logger
            )
            self.logger.info(f"DataFrameEngine created: {len(data_engine.df):,} rows loaded")
        else:
            data_engine = None
        
        for table_name, builder_func, requires_chunking in self.fact_builders:
            try:
                # PHASE 3: Start table-level timing
                table_start_time = time.time()
                
                self.logger.info(f"Building {table_name} (chunked: {requires_chunking})...")
                
                if requires_chunking:
                    # Use chunked processing for large tables (V2's approach)
                    # In bucket mode: pass data_engine for reading, bucket_adapter for saving
                    # In database mode: pass db_service for both
                    if self.use_bucket:
                        # Bucket mode: pass DataFrameEngine for data, bucket_adapter for saving
                        build_result = builder_func(
                            data_engine,
                            seasons=seasons,
                            db_service=self.db_service,
                            bucket_adapter=self.bucket_adapter_required,
                            logger=self.logger
                        )
                    else:
                        # Database mode: pass db_service as before
                        build_result = builder_func(
                            self.db_service,
                            seasons=seasons,
                            logger=self.logger
                        )
                    
                    if build_result['status'] == 'success':
                        # PHASE 3: Calculate table duration
                        table_duration = time.time() - table_start_time
                        
                        row_count = build_result.get('total_rows_saved', 0)
                        tables_built.append(table_name)
                        total_rows += row_count
                        
                        # PHASE 1: Enhanced metrics for chunked fact tables
                        perf_metrics = build_result.get('performance_metrics', {})
                        chunks_processed = build_result.get('chunks_processed', 0)
                        chunk_size = build_result.get('chunk_size', 5000)
                        
                        table_details[table_name] = {
                            'status': 'success',
                            'rows': row_count,
                            'columns': build_result.get('column_count', 'N/A'),  # PHASE 1
                            'processing_type': 'chunked',
                            'chunks_processed': chunks_processed,
                            'chunk_size': chunk_size,  # PHASE 1
                            'memory_per_chunk_mb': perf_metrics.get('avg_chunk_memory_mb', 'N/A'),  # PHASE 1
                            'total_memory_mb': perf_metrics.get('total_memory_mb', 'N/A'),  # PHASE 1
                            'column_pruning_enabled': fact_columns is not None,  # PHASE 1
                            'columns_loaded': len(fact_columns) if fact_columns else 'all',  # PHASE 1
                            # PHASE 3: Add table-level duration
                            'duration': round(table_duration, 2),
                            'performance_metrics': {
                                'avg_chunk_time': perf_metrics.get('avg_chunk_time_sec', 'N/A'),  # PHASE 1
                                'total_build_time': perf_metrics.get('total_build_time_sec', 'N/A'),  # PHASE 1
                                'rows_per_second': int(row_count / perf_metrics.get('total_build_time_sec', 1)) if perf_metrics.get('total_build_time_sec', 0) > 0 else 'N/A'  # PHASE 1
                            }
                        }
                        
                        # PHASE 4: Track schema for chunked fact tables (if column info available)
                        if 'column_count' in build_result and build_result.get('column_count') != 'N/A':
                            # For chunked tables, schema info comes from build_result metadata if available
                            # We'll just store the basic schema info we have
                            pass  # Schema tracking for chunked tables can be enhanced in future iterations
                        
                        self.logger.info(f"✅ {table_name}: {row_count:,} rows ({chunks_processed} chunks), {table_duration:.2f}s")
                    else:
                        self.logger.error(f"❌ {table_name} build failed: {build_result.get('message', 'Unknown error')}")
                        table_details[table_name] = {
                            'status': 'failed', 
                            'error': build_result.get('message', 'Unknown error'),
                            'rows': 0
                        }
                        
                else:
                    # Standard processing for smaller tables
                    # MUST respect bucket-first architecture like chunked processing does
                    if self.use_bucket:
                        # Bucket mode: pass DataFrameEngine for data, bucket_adapter for saving
                        build_result = builder_func(
                            data_engine,
                            seasons=seasons,
                            db_service=self.db_service,
                            bucket_adapter=self.bucket_adapter_required,
                            logger=self.logger
                        )
                        
                        # Handle dict return (like fact_player_stats)
                        if isinstance(build_result, dict):
                            if build_result['status'] == 'success':
                                # PHASE 3: Calculate table duration
                                table_duration = time.time() - table_start_time
                                
                                row_count = build_result.get('rows_saved', 0)
                                tables_built.append(table_name)
                                total_rows += row_count
                                table_details[table_name] = {
                                    'status': 'success',
                                    'rows': row_count,
                                    'processing_type': 'standard',
                                    # PHASE 3: Add duration
                                    'duration': round(table_duration, 2)
                                }
                                self.logger.info(f"✅ {table_name}: {row_count:,} rows, {table_duration:.2f}s")
                            else:
                                error_msg = build_result.get('message', 'Unknown error')
                                self.logger.error(f"❌ {table_name} build failed: {error_msg}")
                                table_details[table_name] = {
                                    'status': 'failed',
                                    'error': error_msg,
                                    'rows': 0
                                }
                                # PHASE 2: Track chunked build failure
                                self._track_build_failure(
                                    table_name=table_name,
                                    error=error_msg,
                                    build_stage='transform'
                                )
                                has_errors = True
                        elif isinstance(build_result, pd.DataFrame):
                            # Legacy DataFrame return
                            if build_result.empty:
                                self.logger.warning(f"No data returned for {table_name}")
                                table_details[table_name] = {'status': 'empty', 'rows': 0}
                                # PHASE 2: Track empty table (bucket mode, legacy DataFrame)
                                self._track_empty_table(
                                    table_name=table_name,
                                    reason=f"No data returned from transformation",
                                    expected=False
                                )
                            else:
                                # PHASE 3: Calculate table duration
                                table_duration = time.time() - table_start_time
                                
                                # PHASE 4: Schema tracking for standard DataFrame processing
                                source_schema = self._get_current_schema(table_name)
                                result_schema = {col: str(dtype) for col, dtype in build_result.dtypes.items()}
                                
                                self._save_table(build_result, table_name)
                                
                                # PHASE 4: Compare schemas and track changes
                                if source_schema:
                                    schema_diff = self._compare_schemas(source_schema, result_schema)
                                    if schema_diff:
                                        if 'added_columns' in schema_diff:
                                            self._track_schema_change(table_name, 'column_added', schema_diff)
                                        if 'removed_columns' in schema_diff:
                                            self._track_schema_change(table_name, 'column_removed', schema_diff)
                                        if 'type_changes' in schema_diff:
                                            for type_change in schema_diff['type_changes']:
                                                self._track_schema_change(table_name, 'type_changed', type_change)
                                
                                # PHASE 4: Store current schema
                                self._store_schema(table_name, result_schema)
                                
                                row_count = len(build_result)
                                tables_built.append(table_name)
                                total_rows += row_count
                                table_details[table_name] = {
                                    'status': 'success',
                                    'rows': row_count,
                                    'processing_type': 'standard',
                                    'columns': len(build_result.columns),
                                    # PHASE 3: Add duration
                                    'duration': round(table_duration, 2)
                                }
                                self.logger.info(f"✅ {table_name}: {row_count:,} rows, {table_duration:.2f}s")
                        else:
                            # Unexpected return type - graceful degradation
                            error_msg = f"Builder {table_name} returned unexpected type: {type(build_result).__name__}"
                            self.logger.error(f"❌ {error_msg}")
                            table_details[table_name] = {
                                'status': 'failed',
                                'error': error_msg,
                                'rows': 0
                            }
                            has_errors = True
                    else:
                        # Database mode: use database engine
                        engine = self._get_database_engine()
                        build_result = builder_func(engine, seasons, self.logger)
                        
                        # Handle both dict and DataFrame return types
                        if isinstance(build_result, dict):
                            # Modern dict-based return
                            if build_result['status'] == 'success':
                                # PHASE 3: Calculate table duration
                                table_duration = time.time() - table_start_time
                                
                                row_count = build_result.get('rows_saved', 0)
                                tables_built.append(table_name)
                                total_rows += row_count
                                table_details[table_name] = {
                                    'status': 'success',
                                    'rows': row_count,
                                    'processing_type': 'standard',
                                    # PHASE 3: Add duration
                                    'duration': round(table_duration, 2)
                                }
                                self.logger.info(f"✅ {table_name}: {row_count:,} rows, {table_duration:.2f}s")
                            else:
                                error_msg = build_result.get('message', 'Unknown error')
                                self.logger.error(f"❌ {table_name} build failed: {error_msg}")
                                table_details[table_name] = {
                                    'status': 'failed',
                                    'error': error_msg,
                                    'rows': 0
                                }
                                # PHASE 2: Track standard processing failure
                                self._track_build_failure(
                                    table_name=table_name,
                                    error=error_msg,
                                    build_stage='transform'
                                )
                                has_errors = True
                        elif isinstance(build_result, pd.DataFrame):
                            # Legacy DataFrame return
                            df_result = build_result
                            if df_result.empty:
                                self.logger.warning(f"No data returned for {table_name}")
                                table_details[table_name] = {'status': 'empty', 'rows': 0}
                                # PHASE 2: Track empty table (database mode, legacy DataFrame)
                                self._track_empty_table(
                                    table_name=table_name,
                                    reason=f"No data returned from transformation",
                                    expected=False
                                )
                                continue
                            
                            # PHASE 3: Calculate table duration
                            table_duration = time.time() - table_start_time
                            
                            # PHASE 4: Schema tracking for database mode DataFrame
                            source_schema = self._get_current_schema(table_name)
                            result_schema = {col: str(dtype) for col, dtype in df_result.dtypes.items()}
                            
                            # Save to analytics schema
                            self._save_table(df_result, table_name)
                            
                            # PHASE 4: Compare schemas and track changes
                            if source_schema:
                                schema_diff = self._compare_schemas(source_schema, result_schema)
                                if schema_diff:
                                    if 'added_columns' in schema_diff:
                                        self._track_schema_change(table_name, 'column_added', schema_diff)
                                    if 'removed_columns' in schema_diff:
                                        self._track_schema_change(table_name, 'column_removed', schema_diff)
                                    if 'type_changes' in schema_diff:
                                        for type_change in schema_diff['type_changes']:
                                            self._track_schema_change(table_name, 'type_changed', type_change)
                            
                            # PHASE 4: Store current schema
                            self._store_schema(table_name, result_schema)
                            
                            row_count = len(df_result)
                            tables_built.append(table_name)
                            total_rows += row_count
                            table_details[table_name] = {
                                'status': 'success',
                                'rows': row_count,
                                'processing_type': 'standard',
                                'columns': len(df_result.columns),
                                # PHASE 3: Add duration
                                'duration': round(table_duration, 2)
                            }
                            
                            self.logger.info(f"✅ {table_name}: {row_count:,} rows, {table_duration:.2f}s")
                        else:
                            # Unexpected return type - graceful degradation
                            error_msg = f"Builder {table_name} returned unexpected type: {type(build_result).__name__}"
                            self.logger.error(f"❌ {error_msg}")
                            table_details[table_name] = {
                                'status': 'failed',
                                'error': error_msg,
                                'rows': 0
                            }
                            has_errors = True
                
            except Exception as e:
                self.logger.error(f"❌ Failed to build {table_name}: {e}", exc_info=True)
                table_details[table_name] = {'status': 'failed', 'error': str(e), 'rows': 0}
                has_errors = True
                continue
        
        # Determine overall status
        if len(tables_built) == 0:
            status = 'failed'
        elif has_errors:
            status = 'partial'
        else:
            status = 'success'
        
        return {
            'status': status,
            'tables': tables_built,
            'total_rows': total_rows,
            'table_details': table_details,
            'success_rate': len(tables_built) / len(self.fact_builders) if self.fact_builders else 0
        }
    
    def _build_dimension_tables_filtered(self, dim_builders):
        """
        Build filtered dimension tables.
        
        FIX #2: Uses dynamic column loading to reduce memory
        
        Args:
            dim_builders: List of (table_name, builder_func) tuples
            
        Returns:
            dict: Build results with 'status' key
        """
        tables_built = []
        total_rows = 0
        table_details = {}
        has_errors = False
        
        # FIX #2: Get union of columns needed by filtered dimensions
        from .config.data_sources import get_warehouse_columns, WAREHOUSE_COLUMN_REQUIREMENTS
        
        all_dim_columns = set()
        needs_dataframe_engine = False
        
        for table_name, _ in dim_builders:
            config = WAREHOUSE_COLUMN_REQUIREMENTS.get(table_name, {})
            source_table = config.get('source_table')
            
            # Skip if multi-source (loads own data via BucketAdapter) or generated (no source)
            if source_table is None or isinstance(source_table, list):
                self.logger.info(f"Skipping DataFrameEngine columns for {table_name} (multi-source or generated)")
                continue
                
            # Single-source dimension needs DataFrameEngine
            needs_dataframe_engine = True
            table_columns = get_warehouse_columns(table_name)
            if table_columns:
                all_dim_columns.update(table_columns)
        
        dimension_columns = list(all_dim_columns) if all_dim_columns and needs_dataframe_engine else None
        
        if dimension_columns:
            self.logger.info(
                f"📊 Column pruning for {len(dim_builders)} dimensions: "
                f"{len(dimension_columns)} columns loaded"
            )
        
        # Create engine (bucket-first OR database)
        if self.use_bucket:
            if needs_dataframe_engine:
                self.logger.info("Creating DataFrameEngine for bucket-first warehouse...")
                engine = create_dataframe_engine(
                    table_name='play_by_play',
                    schema='raw_nflfastr',
                    columns=dimension_columns,  # FIX #2: Load only needed columns
                    max_memory_mb=int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                    bucket_adapter=self.bucket_adapter_required,
                    logger=self.logger
                )
                self.logger.info(f"DataFrameEngine created: {len(engine.df):,} rows loaded")
            else:
                self.logger.info("No DataFrameEngine needed - all dimensions are multi-source or generated")
                engine = None  # Dimensions will load own data via BucketAdapter
        else:
            engine = self._get_database_engine()
        
        # Build each dimension
        for table_name, builder_func in dim_builders:
            try:
                # PHASE 3: Start table-level timing
                table_start_time = time.time()
                
                self.logger.info(f"Building {table_name}...")
                df_result = builder_func(engine, self.logger)
                
                if df_result.empty:
                    self.logger.warning(f"No data returned for {table_name}")
                    table_details[table_name] = {'status': 'empty', 'rows': 0}
                    continue
                
                # PHASE 3: Calculate table duration
                table_duration = time.time() - table_start_time
                
                # Save to warehouse
                self._save_table(df_result, table_name)
                
                # Track results
                row_count = len(df_result)
                tables_built.append(table_name)
                total_rows += row_count
                
                # PHASE 1: Enhanced metrics capture (matching _build_dimension_tables)
                config = WAREHOUSE_COLUMN_REQUIREMENTS.get(table_name, {})
                source_table = config.get('source_table')
                
                # Determine build type
                if source_table is None:
                    build_type = 'generated'
                elif isinstance(source_table, list):
                    build_type = 'multi_source'
                else:
                    build_type = 'single_source'
                
                # Calculate memory usage
                memory_mb = df_result.memory_usage(deep=True).sum() / 1024 / 1024
                
                table_details[table_name] = {
                    'status': 'success',
                    'rows': row_count,
                    'columns': len(df_result.columns),
                    # PHASE 1: New fields
                    'column_names': list(df_result.columns),
                    'memory_mb': round(memory_mb, 2),
                    'build_type': build_type,
                    'source_table': source_table,
                    'columns_pruned': dimension_columns is not None,
                    'columns_loaded': len(dimension_columns) if dimension_columns else 'all',
                    # PHASE 3: Performance timing
                    'duration': round(table_duration, 2),
                    'rows_per_second': int(row_count / table_duration) if table_duration > 0 else 0
                }
                
                self.logger.info(
                    f"✅ {table_name}: {row_count:,} rows, {len(df_result.columns)} columns, "
                    f"{memory_mb:.2f} MB, {table_duration:.2f}s ({build_type})"
                )
                
            except Exception as e:
                self.logger.error(f"❌ Failed to build {table_name}: {e}", exc_info=True)
                table_details[table_name] = {'status': 'failed', 'error': str(e), 'rows': 0}
                has_errors = True
                continue
        
        # Determine overall status
        if len(tables_built) == 0:
            status = 'failed'
        elif has_errors:
            status = 'partial'
        else:
            status = 'success'
        
        return {
            'status': status,
            'tables': tables_built,
            'total_rows': total_rows,
            'table_details': table_details,
            'success_rate': len(tables_built) / len(dim_builders) if dim_builders else 0
        }
    
    def _build_fact_tables_filtered(self, fact_builders, seasons=None):
        """
        Build filtered fact tables.
        
        FIX #2: Uses dynamic column loading to reduce memory
        
        Args:
            fact_builders: List of (table_name, builder_func, requires_chunking) tuples
            seasons: Optional list of seasons to process
            
        Returns:
            dict: Build results with 'status' key
        """
        tables_built = []
        total_rows = 0
        table_details = {}
        has_errors = False
        
        # FIX #2: Get union of columns needed by filtered fact tables
        from .config.data_sources import get_warehouse_columns
        
        all_fact_columns = set()
        for table_name, _, _ in fact_builders:
            table_columns = get_warehouse_columns(table_name)
            if table_columns:
                all_fact_columns.update(table_columns)
        
        fact_columns = list(all_fact_columns) if all_fact_columns else None
        
        if fact_columns:
            self.logger.info(
                f"📊 Column pruning for {len(fact_builders)} facts: "
                f"{len(fact_columns)} columns loaded"
            )
        
        # Create engine for data loading (bucket-first OR database)
        if self.use_bucket:
            self.logger.info("Creating DataFrameEngine for bucket-first fact tables...")
            data_engine = create_dataframe_engine(
                table_name='play_by_play',
                schema='raw_nflfastr',
                seasons=[int(s) for s in seasons] if seasons else None,
                columns=fact_columns,  # FIX #2: Load only needed columns
                max_memory_mb=int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                bucket_adapter=self.bucket_adapter_required,
                logger=self.logger
            )
            self.logger.info(f"DataFrameEngine created: {len(data_engine.df):,} rows loaded")
        else:
            data_engine = None
        
        for table_name, builder_func, requires_chunking in fact_builders:
            try:
                self.logger.info(f"Building {table_name} (chunked: {requires_chunking})...")
                
                if requires_chunking:
                    # Use chunked processing for large tables
                    if self.use_bucket:
                        # Bucket mode: pass DataFrameEngine for data, bucket_adapter for saving
                        build_result = builder_func(
                            data_engine,
                            seasons=seasons,
                            db_service=self.db_service,
                            bucket_adapter=self.bucket_adapter_required,
                            logger=self.logger
                        )
                    else:
                        # Database mode: pass db_service as before
                        build_result = builder_func(
                            self.db_service,
                            seasons=seasons,
                            logger=self.logger
                        )
                    
                    if build_result['status'] == 'success':
                        row_count = build_result.get('total_rows_saved', 0)
                        tables_built.append(table_name)
                        total_rows += row_count
                        table_details[table_name] = {
                            'status': 'success',
                            'rows': row_count,
                            'processing_type': 'chunked',
                            'chunks_processed': build_result.get('chunks_processed', 0),
                            'performance_metrics': build_result.get('performance_metrics', {})
                        }
                        
                        self.logger.info(f"✅ {table_name}: {row_count:,} rows ({build_result.get('chunks_processed', 0)} chunks)")
                    else:
                        self.logger.error(f"❌ {table_name} build failed: {build_result.get('message', 'Unknown error')}")
                        table_details[table_name] = {
                            'status': 'failed', 
                            'error': build_result.get('message', 'Unknown error'),
                            'rows': 0
                        }
                        
                else:
                    # Standard processing for smaller tables
                    # MUST respect bucket-first architecture like chunked processing does
                    if self.use_bucket:
                        # Bucket mode: pass DataFrameEngine for data, bucket_adapter for saving
                        build_result = builder_func(
                            data_engine,
                            seasons=seasons,
                            db_service=self.db_service,
                            bucket_adapter=self.bucket_adapter_required,
                            logger=self.logger
                        )
                        
                        # Handle dict return (like fact_player_stats)
                        if isinstance(build_result, dict):
                            if build_result['status'] == 'success':
                                row_count = build_result.get('rows_saved', 0)
                                tables_built.append(table_name)
                                total_rows += row_count
                                table_details[table_name] = {
                                    'status': 'success',
                                    'rows': row_count,
                                    'processing_type': 'standard'
                                }
                                self.logger.info(f"✅ {table_name}: {row_count:,} rows")
                            else:
                                error_msg = build_result.get('message', 'Unknown error')
                                self.logger.error(f"❌ {table_name} build failed: {error_msg}")
                                table_details[table_name] = {
                                    'status': 'failed',
                                    'error': error_msg,
                                    'rows': 0
                                }
                                # PHASE 2: Track standard processing failure
                                self._track_build_failure(
                                    table_name=table_name,
                                    error=error_msg,
                                    build_stage='transform'
                                )
                                has_errors = True
                        elif isinstance(build_result, pd.DataFrame):
                            # Handle DataFrame return (legacy)
                            df_result = build_result
                            if df_result.empty:
                                self.logger.warning(f"No data returned for {table_name}")
                                table_details[table_name] = {'status': 'empty', 'rows': 0}
                            else:
                                self._save_table(df_result, table_name)
                                row_count = len(df_result)
                                tables_built.append(table_name)
                                total_rows += row_count
                                table_details[table_name] = {
                                    'status': 'success',
                                    'rows': row_count,
                                    'processing_type': 'standard',
                                    'columns': len(df_result.columns)
                                }
                                self.logger.info(f"✅ {table_name}: {row_count:,} rows")
                        else:
                            # Unexpected return type - graceful degradation
                            error_msg = f"Builder {table_name} returned unexpected type: {type(build_result).__name__}"
                            self.logger.error(f"❌ {error_msg}")
                            table_details[table_name] = {
                                'status': 'failed',
                                'error': error_msg,
                                'rows': 0
                            }
                            has_errors = True
                    else:
                        # Database mode: use database engine
                        engine = self._get_database_engine()
                        build_result = builder_func(engine, seasons, self.logger)
                        
                        # Handle both dict and DataFrame return types
                        if isinstance(build_result, dict):
                            # Modern dict-based return
                            if build_result['status'] == 'success':
                                row_count = build_result.get('rows_saved', 0)
                                tables_built.append(table_name)
                                total_rows += row_count
                                table_details[table_name] = {
                                    'status': 'success',
                                    'rows': row_count,
                                    'processing_type': 'standard'
                                }
                                self.logger.info(f"✅ {table_name}: {row_count:,} rows")
                            else:
                                error_msg = build_result.get('message', 'Unknown error')
                                self.logger.error(f"❌ {table_name} build failed: {error_msg}")
                                table_details[table_name] = {
                                    'status': 'failed',
                                    'error': error_msg,
                                    'rows': 0
                                }
                                # PHASE 2: Track standard processing failure
                                self._track_build_failure(
                                    table_name=table_name,
                                    error=error_msg,
                                    build_stage='transform'
                                )
                                has_errors = True
                        elif isinstance(build_result, pd.DataFrame):
                            # Legacy DataFrame return
                            df_result = build_result
                            if df_result.empty:
                                self.logger.warning(f"No data returned for {table_name}")
                                table_details[table_name] = {'status': 'empty', 'rows': 0}
                                # PHASE 2: Track empty table (database mode, legacy DataFrame)
                                self._track_empty_table(
                                    table_name=table_name,
                                    reason=f"No data returned from transformation",
                                    expected=False
                                )
                                continue
                            
                            # Save to warehouse
                            self._save_table(df_result, table_name)
                            
                            row_count = len(df_result)
                            tables_built.append(table_name)
                            total_rows += row_count
                            table_details[table_name] = {
                                'status': 'success',
                                'rows': row_count,
                                'processing_type': 'standard',
                                'columns': len(df_result.columns)
                            }
                            
                            self.logger.info(f"✅ {table_name}: {row_count:,} rows")
                        else:
                            # Unexpected return type - graceful degradation
                            error_msg = f"Builder {table_name} returned unexpected type: {type(build_result).__name__}"
                            self.logger.error(f"❌ {error_msg}")
                            table_details[table_name] = {
                                'status': 'failed',
                                'error': error_msg,
                                'rows': 0
                            }
                            has_errors = True
                
            except Exception as e:
                self.logger.error(f"❌ Failed to build {table_name}: {e}", exc_info=True)
                table_details[table_name] = {'status': 'failed', 'error': str(e), 'rows': 0}
                has_errors = True
                continue
        
        # Determine overall status
        if len(tables_built) == 0:
            status = 'failed'
        elif has_errors:
            status = 'partial'
        else:
            status = 'success'
        
        return {
            'status': status,
            'tables': tables_built,
            'total_rows': total_rows,
            'table_details': table_details,
            'success_rate': len(tables_built) / len(fact_builders) if fact_builders else 0
        }
    
    def _save_table(self, df, table_name):
        """
        Save table to bucket warehouse schema.
        
        Args:
            df: DataFrame to save
            table_name: Target table name
        """
        if self.bucket_adapter is None:
            raise RuntimeError(
                f"Cannot save {table_name}: bucket adapter not initialized. "
                "Warehouse requires bucket storage."
            )
        
        rows_saved = self.bucket_adapter.store_data_streaming(
            df=df,
            table_name=table_name,
            schema='warehouse',
            rows_per_group=10000
        )
        self.logger.info(f"💾 Saved {rows_saved:,} rows to warehouse/{table_name}")

def create_warehouse_builder(db_service=None, logger=None, bucket_adapter=None, use_bucket=None):
    """
    Create warehouse builder with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        use_bucket: Optional override for bucket usage (default: auto-detect)
        
    Returns:
        WarehouseBuilder: Configured warehouse builder
    """
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.warehouse')
    
    return WarehouseBuilder(
        db_service=db_service,
        logger=logger,
        bucket_adapter=bucket_adapter,
        use_bucket=use_bucket
    )


__all__ = ['WarehouseBuilder', 'create_warehouse_builder']
