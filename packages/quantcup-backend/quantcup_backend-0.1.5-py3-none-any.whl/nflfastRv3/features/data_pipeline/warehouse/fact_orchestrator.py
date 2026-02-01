"""
Fact Orchestrator Component

Extracted from warehouse.py (lines 1105-1464).
Orchestrates fact table building with chunked processing support.

Pattern: Orchestration with Chunking (4 complexity points)
- Base orchestration: 1 point
- Column pruning logic: 1 point
- Chunking support: 1 point
- Return type flexibility: 1 point
"""

import os
import time
from typing import Dict, Any, List, Tuple, Callable, Optional
import pandas as pd
from commonv2.persistence.bucket_adapter import BucketAdapter


class FactOrchestrator:
    """
    Orchestrates fact table building with chunked processing.
    
    Pattern: Orchestration with Chunking (4 complexity points)
    Complexity: 4 points (base + column pruning + chunking + type handling)
    
    Responsibilities:
    - DataFrameEngine creation with column pruning
    - Fact table building with chunking support
    - Handling both chunked and standard processing
    - Return type flexibility (dict vs DataFrame)
    - Schema change tracking coordination
    """
    
    def __init__(self, bucket_adapter: Optional[BucketAdapter], db_service, logger, schema_tracker=None, source_table: str = 'play_by_play', source_schema: str = 'raw_nflfastr'):
        """
        Initialize fact orchestrator.
        
        Args:
            bucket_adapter: Optional bucket adapter for storage (None for database mode)
            db_service: Database service for fallback/database mode
            logger: Logger instance
            schema_tracker: Optional schema tracker instance for change detection
            source_table: Source table name for fact builds (default: 'play_by_play')
            source_schema: Source schema name for fact builds (default: 'raw_nflfastr')
        """
        self.bucket_adapter = bucket_adapter
        self.db_service = db_service
        self.logger = logger
        self.schema_tracker = schema_tracker
        self.source_table = source_table
        self.source_schema = source_schema
    
    def build_all(self, fact_builders: List[Tuple[str, Callable, bool]], seasons: Optional[List[int]], use_bucket: bool) -> Dict[str, Any]:
        """
        Build all fact tables with chunking support.
        
        Extracted from warehouse.py lines 1105-1464.
        
        Args:
            fact_builders: List of (table_name, builder_func, requires_chunking) tuples
            seasons: Optional season filter
            use_bucket: Whether to use bucket-first architecture
            
        Returns:
            {
                'status': 'success' | 'partial' | 'failed',
                'tables': List[str],
                'total_rows': int,
                'table_details': Dict[str, Dict],
                'success_rate': float
            }
        """
        self.logger.info("Building fact tables with chunked processing...")
        
        tables_built = []
        total_rows = 0
        table_details = {}
        has_errors = False
        
        # Get union of columns needed by all fact tables
        fact_columns = self._determine_fact_columns(fact_builders)
        
        if fact_columns:
            self.logger.info(
                f"📊 Column pruning for fact tables: {len(fact_columns)} columns "
                f"(vs 250+ full PBP) for memory optimization"
            )
        
        # Create engine for data loading (bucket-first OR database)
        data_engine = self._create_engine_for_facts(fact_columns, seasons, use_bucket)
        
        # Build each fact table
        for table_name, builder_func, requires_chunking in fact_builders:
            try:
                table_start_time = time.time()
                
                self.logger.info(f"Building {table_name} (chunked: {requires_chunking})...")
                
                if requires_chunking:
                    # Use chunked processing for large tables
                    build_result = self._build_chunked_fact(
                        table_name, builder_func, data_engine, seasons, use_bucket
                    )
                    
                    if build_result['status'] == 'success':
                        table_duration = time.time() - table_start_time
                        
                        row_count = build_result.get('total_rows_saved', 0)
                        tables_built.append(table_name)
                        total_rows += row_count
                        
                        # Enhanced metrics for chunked fact tables
                        perf_metrics = build_result.get('performance_metrics', {})
                        chunks_processed = build_result.get('chunks_processed', 0)
                        chunk_size = build_result.get('chunk_size', 5000)
                        
                        table_details[table_name] = {
                            'status': 'success',
                            'rows': row_count,
                            'columns': build_result.get('column_count', 'N/A'),
                            'processing_type': 'chunked',
                            'chunks_processed': chunks_processed,
                            'chunk_size': chunk_size,
                            'memory_per_chunk_mb': perf_metrics.get('avg_chunk_memory_mb', 'N/A'),
                            'total_memory_mb': perf_metrics.get('total_memory_mb', 'N/A'),
                            'column_pruning_enabled': fact_columns is not None,
                            'columns_loaded': len(fact_columns) if fact_columns else 'all',
                            'duration': round(table_duration, 2),
                            'performance_metrics': {
                                'avg_chunk_time': perf_metrics.get('avg_chunk_time_sec', 'N/A'),
                                'total_build_time': perf_metrics.get('total_build_time_sec', 'N/A'),
                                'rows_per_second': int(row_count / perf_metrics.get('total_build_time_sec', 1)) if perf_metrics.get('total_build_time_sec', 0) > 0 else 'N/A'
                            }
                        }
                        
                        self.logger.info(f"✅ {table_name}: {row_count:,} rows ({chunks_processed} chunks), {table_duration:.2f}s")
                    else:
                        self.logger.error(f"❌ {table_name} build failed: {build_result.get('message', 'Unknown error')}")
                        table_details[table_name] = {
                            'status': 'failed', 
                            'error': build_result.get('message', 'Unknown error'),
                            'rows': 0
                        }
                        has_errors = True
                        
                else:
                    # Standard processing for smaller tables
                    build_result = self._build_standard_fact(
                        table_name, builder_func, data_engine, seasons, use_bucket
                    )
                    
                    # Handle dict return (like fact_player_stats)
                    if isinstance(build_result, dict):
                        if build_result['status'] == 'success':
                            table_duration = time.time() - table_start_time
                            
                            row_count = build_result.get('rows_saved', 0)
                            tables_built.append(table_name)
                            total_rows += row_count
                            table_details[table_name] = {
                                'status': 'success',
                                'rows': row_count,
                                'processing_type': 'standard',
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
                            has_errors = True
                    elif isinstance(build_result, pd.DataFrame):
                        # Legacy DataFrame return
                        if build_result.empty:
                            self.logger.warning(f"No data returned for {table_name}")
                            table_details[table_name] = {'status': 'empty', 'rows': 0}
                        else:
                            table_duration = time.time() - table_start_time
                            
                            # Schema tracking for standard DataFrame processing
                            if self.schema_tracker:
                                source_schema = self.schema_tracker.get_current_schema(table_name)
                                result_schema = {col: str(dtype) for col, dtype in build_result.dtypes.items()}
                            
                            self._save_table(build_result, table_name, use_bucket)
                            
                            # Schema tracking after save
                            if self.schema_tracker and source_schema:
                                result_schema = {col: str(dtype) for col, dtype in build_result.dtypes.items()}
                                schema_diff = self.schema_tracker.compare_schemas(source_schema, result_schema)
                                if schema_diff:
                                    if 'added_columns' in schema_diff:
                                        self.schema_tracker.track_change(table_name, 'column_added', schema_diff)
                                    if 'removed_columns' in schema_diff:
                                        self.schema_tracker.track_change(table_name, 'column_removed', schema_diff)
                                    if 'type_changes' in schema_diff:
                                        for type_change in schema_diff['type_changes']:
                                            self.schema_tracker.track_change(table_name, 'type_changed', type_change)
                            
                            # Store current schema
                            if self.schema_tracker:
                                result_schema = {col: str(dtype) for col, dtype in build_result.dtypes.items()}
                                self.schema_tracker.store_schema(table_name, result_schema)
                            
                            row_count = len(build_result)
                            tables_built.append(table_name)
                            total_rows += row_count
                            table_details[table_name] = {
                                'status': 'success',
                                'rows': row_count,
                                'processing_type': 'standard',
                                'columns': len(build_result.columns),
                                'duration': round(table_duration, 2)
                            }
                            self.logger.info(f"✅ {table_name}: {row_count:,} rows, {table_duration:.2f}s")
                    else:
                        # Unexpected return type
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
    
    def _determine_fact_columns(self, fact_builders: List[Tuple[str, Callable, bool]]) -> Optional[List[str]]:
        """
        Determine union of columns needed by all facts.
        
        Extracted from warehouse.py lines 1130-1145.
        
        Args:
            fact_builders: List of (table_name, builder_func, requires_chunking) tuples
            
        Returns:
            List of column names, or None for all columns
        """
        from ..config.data_sources import get_warehouse_columns
        
        all_fact_columns = set()
        for table_name, _, _ in fact_builders:
            table_columns = get_warehouse_columns(table_name)
            if table_columns:
                all_fact_columns.update(table_columns)
        
        return list(all_fact_columns) if all_fact_columns else None
    
    def _create_engine_for_facts(self, fact_columns: Optional[List[str]], seasons: Optional[List[int]], use_bucket: bool):
        """
        Create appropriate engine with season filtering.
        
        Extracted from warehouse.py lines 1148-1162.
        
        Args:
            fact_columns: List of columns to load (None for all)
            seasons: Optional season filter
            use_bucket: Whether to use bucket-first architecture
            
        Returns:
            Engine instance (DataFrameEngine or None for database mode)
        """
        if use_bucket:
            # Bucket mode: Create DataFrameEngine with configured source table
            from ..transformations import create_dataframe_engine
            
            self.logger.info(f"Creating DataFrameEngine for bucket-first fact tables from {self.source_schema}.{self.source_table}...")
            data_engine = create_dataframe_engine(
                table_name=self.source_table,
                schema=self.source_schema,
                seasons=[int(s) for s in seasons] if seasons else None,
                columns=fact_columns,
                max_memory_mb=int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                bucket_adapter=self.bucket_adapter,
                logger=self.logger
            )
            self.logger.info(f"DataFrameEngine created: {len(data_engine.df):,} rows loaded from {self.source_schema}.{self.source_table}")
            return data_engine
        else:
            return None
    
    def _build_chunked_fact(self, table_name: str, builder_func: Callable, data_engine, seasons: Optional[List[int]], use_bucket: bool) -> Dict:
        """
        Build fact table using chunked processing.
        
        Args:
            table_name: Name of fact table
            builder_func: Builder function
            data_engine: Data engine (DataFrameEngine or None)
            seasons: Optional season filter
            use_bucket: Whether to use bucket-first architecture
            
        Returns:
            Dict with build results
        """
        if use_bucket:
            # Bucket mode: pass DataFrameEngine for data, bucket_adapter for saving
            return builder_func(
                data_engine,
                seasons=seasons,
                db_service=self.db_service,
                bucket_adapter=self.bucket_adapter,
                logger=self.logger
            )
        else:
            # Database mode: pass db_service
            return builder_func(
                self.db_service,
                seasons=seasons,
                logger=self.logger
            )
    
    def _build_standard_fact(self, table_name: str, builder_func: Callable, data_engine, seasons: Optional[List[int]], use_bucket: bool):
        """
        Build fact table using standard processing.
        
        Args:
            table_name: Name of fact table
            builder_func: Builder function
            data_engine: Data engine (DataFrameEngine or None)
            seasons: Optional season filter
            use_bucket: Whether to use bucket-first architecture
            
        Returns:
            Build result (dict or DataFrame)
        """
        if use_bucket:
            # Bucket mode: pass DataFrameEngine for data, bucket_adapter for saving
            return builder_func(
                data_engine,
                seasons=seasons,
                db_service=self.db_service,
                bucket_adapter=self.bucket_adapter,
                logger=self.logger
            )
        else:
            # Database mode: use database engine
            engine = self.db_service.get_engine()
            return builder_func(engine, seasons, self.logger)
    
    def _save_table(self, df: pd.DataFrame, table_name: str, use_bucket: bool):
        """
        Save table to warehouse schema.
        
        Args:
            df: DataFrame to save
            table_name: Target table name
            use_bucket: Whether to use bucket storage
        """
        if not use_bucket:
            # Database mode - use db_service
            # This is handled by the transformation functions themselves
            return
        
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
        self.logger.info(f"💾 Saved {rows_saved:,} rows to bucket: warehouse/{table_name}")


__all__ = ['FactOrchestrator']
