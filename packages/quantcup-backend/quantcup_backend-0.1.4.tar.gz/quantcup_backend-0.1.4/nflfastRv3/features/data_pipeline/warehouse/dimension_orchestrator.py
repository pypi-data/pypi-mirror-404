"""
Dimension Orchestrator Component

Extracted from warehouse.py (lines 918-1103 + helper methods).
Orchestrates dimension table building with column pruning.

Pattern: Orchestration with Memory Optimization (3 complexity points)
- Base orchestration: 1 point
- Column pruning logic: 1 point
- Build type detection: 1 point
"""

import os
import io
import time
from typing import Dict, Any, List, Tuple, Callable, Optional
import pandas as pd
from commonv2.persistence.bucket_adapter import BucketAdapter
from botocore.exceptions import ClientError

# Import for schema validation
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


class DimensionOrchestrator:
    """
    Orchestrates dimension table building with column pruning.
    
    Pattern: Orchestration with Memory Optimization (3 complexity points)
    Complexity: 3 points (base + column pruning + build type detection)
    
    Responsibilities:
    - DataFrameEngine creation with column pruning
    - Dimension table building loop
    - Memory optimization tracking
    - Build type detection (single_source vs multi_source vs generated)
    - Schema change tracking coordination
    """
    
    def __init__(self, bucket_adapter: Optional[BucketAdapter], db_service, logger, schema_tracker=None, source_table: str = 'play_by_play', source_schema: str = 'raw_nflfastr'):
        """
        Initialize dimension orchestrator.
        
        Args:
            bucket_adapter: Optional bucket adapter for storage (None for database mode)
            db_service: Database service for fallback/database mode
            logger: Logger instance
            schema_tracker: Optional schema tracker instance for change detection
            source_table: Source table name for dimension builds (default: 'play_by_play')
            source_schema: Source schema name for dimension builds (default: 'raw_nflfastr')
        """
        self.bucket_adapter = bucket_adapter
        self.db_service = db_service
        self.logger = logger
        self.schema_tracker = schema_tracker
        self.source_table = source_table
        self.source_schema = source_schema
    
    def build_all(self, dimension_builders: List[Tuple[str, Callable]], use_bucket: bool) -> Dict[str, Any]:
        """
        Build all dimension tables with memory optimization.
        
        Extracted from warehouse.py lines 918-1103.
        
        Args:
            dimension_builders: List of (table_name, builder_func) tuples
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
        self.logger.info("Building dimension tables with V2 business logic...")
        
        tables_built = []
        total_rows = 0
        table_details = {}
        has_errors = False
        
        # FIX: Check if any dimension actually needs DataFrameEngine
        needs_engine, dimension_columns = self._analyze_dimension_requirements(dimension_builders)
        
        if not needs_engine and use_bucket:
            self.logger.info("📊 No DataFrameEngine needed - all dimensions are multi-source/generated")
            engine = None
        else:
            if dimension_columns:
                self.logger.info(
                    f"📊 Column pruning enabled: loading {len(dimension_columns)} columns "
                    f"(vs 250+ full PBP) for ~10x memory reduction"
                )
            
            # Create engine (bucket-first OR database)
            engine = self._create_engine_for_dimensions(dimension_columns, use_bucket)
        
        # Build each dimension table
        for table_name, builder_func in dimension_builders:
            try:
                table_start_time = time.time()
                
                self.logger.info(f"Building {table_name}...")
                
                # Call real transformation function (Layer 2 → Layer 3)
                df_result = builder_func(engine, self.logger)
                
                if df_result.empty:
                    self.logger.warning(f"No data returned for {table_name}")
                    table_details[table_name] = {'status': 'empty', 'rows': 0}
                    continue
                
                table_duration = time.time() - table_start_time
                
                # Schema tracking before save (if tracker provided)
                if self.schema_tracker:
                    source_schema = self.schema_tracker.get_current_schema(table_name)
                    result_schema = {col: str(dtype) for col, dtype in df_result.dtypes.items()}
                
                # Save to analytics schema
                self._save_table(df_result, table_name, use_bucket)
                
                # Schema tracking after save
                if self.schema_tracker and source_schema:
                    result_schema = {col: str(dtype) for col, dtype in df_result.dtypes.items()}
                    schema_diff = self.schema_tracker.compare_schemas(source_schema, result_schema)
                    if schema_diff:
                        # Track specific change types
                        if 'added_columns' in schema_diff:
                            self.schema_tracker.track_change(
                                table_name=table_name,
                                change_type='column_added',
                                details=schema_diff
                            )
                        if 'removed_columns' in schema_diff:
                            self.schema_tracker.track_change(
                                table_name=table_name,
                                change_type='column_removed',
                                details=schema_diff
                            )
                        if 'type_changes' in schema_diff:
                            for type_change in schema_diff['type_changes']:
                                self.schema_tracker.track_change(
                                    table_name=table_name,
                                    change_type='type_changed',
                                    details=type_change
                                )
                
                # Store current schema for next build comparison
                if self.schema_tracker:
                    result_schema = {col: str(dtype) for col, dtype in df_result.dtypes.items()}
                    self.schema_tracker.store_schema(table_name, result_schema)
                
                # Track results
                row_count = len(df_result)
                tables_built.append(table_name)
                total_rows += row_count
                
                # Enhanced metrics capture
                build_type, source_table = self._determine_build_type(table_name)
                memory_mb = df_result.memory_usage(deep=True).sum() / 1024 / 1024
                
                table_details[table_name] = {
                    'status': 'success',
                    'rows': row_count,
                    'columns': len(df_result.columns),
                    'column_names': list(df_result.columns),
                    'memory_mb': round(memory_mb, 2),
                    'build_type': build_type,
                    'source_table': source_table,
                    'columns_pruned': dimension_columns is not None,
                    'columns_loaded': len(dimension_columns) if dimension_columns else 'all',
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
            'success_rate': len(tables_built) / len(dimension_builders) if dimension_builders else 0
        }
    
    def _analyze_dimension_requirements(self, dimension_builders: List[Tuple[str, Callable]]) -> Tuple[bool, Optional[List[str]]]:
        """
        Analyze dimension requirements to determine if DataFrameEngine is needed.
        
        This function implements the critical optimization that prevents unnecessary
        loading of play_by_play data (1.2M+ rows, ~1.5GB, 2+ minutes).
        
        ⚠️ CRITICAL LOGIC:
        ------------------
        The 'source_table' field type determines the build strategy:
        
        1. source_table = None:
           → Generated dimension (e.g., dim_date)
           → NO DataFrameEngine created
           → Memory: Minimal
           → Example: dim_date generates from date range
        
        2. source_table = ['table1', 'table2', ...]:
           → Multi-source dimension (LIST type)
           → NO DataFrameEngine created
           → Transformation loads its own data via BucketAdapter
           → Memory: Only what transformation needs (<50MB typically)
           → Examples: dim_player, injuries, dim_game_weather
        
        3. source_table = 'play_by_play':
           → Single-source dimension (STRING type)
           → CREATES DataFrameEngine with play_by_play
           → Memory: ~1.5GB for 27 seasons
           → Time: ~2 minutes with spilling/checkpointing
           → Examples: dim_game, dim_drive, fact_play
        
        ⚠️ COMMON BUG SCENARIO:
        If source_table is incorrectly set as string instead of list for
        warehouse-sourced tables (e.g., 'dim_game' instead of ['dim_game']),
        this function will incorrectly create a DataFrameEngine, wasting
        2+ minutes and 1.5GB memory loading data the transformation doesn't use.
        
        See data_sources.py WAREHOUSE_COLUMN_REQUIREMENTS header for config rules.
        
        Args:
            dimension_builders: List of (table_name, builder_func) tuples
            
        Returns:
            Tuple of (needs_engine, columns_list)
            - needs_engine: True if any single-source dimension found
            - columns_list: Union of columns needed, or None
        """
        from ..config.data_sources import get_warehouse_columns, WAREHOUSE_COLUMN_REQUIREMENTS
        
        needs_engine = False
        all_dim_columns = set()
        
        for table_name, _ in dimension_builders:
            config = WAREHOUSE_COLUMN_REQUIREMENTS.get(table_name, {})
            source_table = config.get('source_table')
            
            # Check build type
            if source_table is None:
                # Generated dimension (e.g., dim_date) - no engine needed
                self.logger.debug(f"  {table_name}: generated dimension (no source)")
                continue
            elif isinstance(source_table, list):
                # Multi-source dimension (e.g., injuries, player_id_mapping)
                # These load their own data via BucketAdapter
                self.logger.debug(f"  {table_name}: multi-source dimension (loads own data)")
                continue
            else:
                # Single-source dimension (e.g., dim_game, dim_player)
                # These need DataFrameEngine with play_by_play
                self.logger.debug(f"  {table_name}: single-source dimension (needs engine)")
                needs_engine = True
                
                # Collect columns for this dimension
                table_columns = get_warehouse_columns(table_name)
                if table_columns:
                    all_dim_columns.update(table_columns)
        
        # Convert to list for DataFrameEngine
        columns_list = list(all_dim_columns) if all_dim_columns else None
        
        return needs_engine, columns_list
    
    def _determine_columns_to_load(self, dimension_builders: List[Tuple[str, Callable]]) -> Optional[List[str]]:
        """
        Determine union of columns needed by all dimensions.
        
        DEPRECATED: Use _analyze_dimension_requirements instead.
        Kept for backward compatibility.
        
        Args:
            dimension_builders: List of (table_name, builder_func) tuples
            
        Returns:
            List of column names to load, or None for all columns
        """
        _, columns = self._analyze_dimension_requirements(dimension_builders)
        return columns
    
    def _create_engine_for_dimensions(self, dimension_columns, use_bucket):
        """
        Create appropriate engine (DataFrameEngine or database).
        
        Extracted from warehouse.py lines 961-975.
        
        Args:
            dimension_columns: List of columns to load (None for all)
            use_bucket: Whether to use bucket-first architecture
            
        Returns:
            Engine instance (DataFrameEngine or database engine)
        """
        if use_bucket:
            # Bucket mode: Create DataFrameEngine with configured source table
            from ..transformations import create_dataframe_engine
            
            self.logger.info(f"Creating DataFrameEngine for bucket-first warehouse from {self.source_schema}.{self.source_table}...")
            engine = create_dataframe_engine(
                table_name=self.source_table,
                schema=self.source_schema,
                columns=dimension_columns,
                max_memory_mb=int(os.getenv('WAREHOUSE_MEMORY_LIMIT_MB', '1536')),
                bucket_adapter=self.bucket_adapter,
                logger=self.logger
            )
            self.logger.info(f"DataFrameEngine created: {len(engine.df):,} rows loaded from {self.source_schema}.{self.source_table}")
            return engine
        else:
            # Database mode: Use database engine
            return self.db_service.get_engine()
    
    def _determine_build_type(self, table_name: str) -> Tuple[str, Any]:
        """
        Determine build type and source table for a dimension.
        
        Args:
            table_name: Name of dimension table
            
        Returns:
            Tuple of (build_type, source_table)
            build_type: 'generated', 'multi_source', or 'single_source'
        """
        from ..config.data_sources import WAREHOUSE_COLUMN_REQUIREMENTS
        
        config = WAREHOUSE_COLUMN_REQUIREMENTS.get(table_name, {})
        source_table = config.get('source_table')
        
        if source_table is None:
            return 'generated', None
        elif isinstance(source_table, list):
            return 'multi_source', source_table
        else:
            return 'single_source', source_table
    
    def _validate_schema_compatibility(self, df: pd.DataFrame, table_name: str, schema: str) -> bool:
        """
        Check if DataFrame schema is compatible with existing table in bucket.
        
        ✅ PRIORITY 3: Schema validation before write to prevent PyArrow errors
        
        Args:
            df: DataFrame to validate
            table_name: Target table name
            schema: Target schema (e.g., 'warehouse')
            
        Returns:
            True if compatible or no existing table, raises exception otherwise
        """
        if not HAS_PYARROW:
            return True  # Skip validation without pyarrow
            
        try:
            key = f"{schema}/{table_name}/data.parquet"
            
            # Try to get existing schema
            assert self.bucket_adapter is not None
            assert self.bucket_adapter.s3_client is not None
            assert self.bucket_adapter.bucket_name is not None
            
            response = self.bucket_adapter.s3_client.get_object(
                Bucket=self.bucket_adapter.bucket_name,
                Key=key
            )
            
            # Read just metadata (first few KB)
            partial_bytes = response['Body'].read(8192)
            existing_file = pq.ParquetFile(io.BytesIO(partial_bytes))
            existing_schema = existing_file.schema_arrow
            
            # Get new schema
            new_table = pa.Table.from_pandas(df, preserve_index=False)
            new_schema = new_table.schema
            
            # Check for incompatibilities
            for field in new_schema:
                if field.name in existing_schema.names:
                    existing_field = existing_schema.field(field.name)
                    if field.type != existing_field.type:
                        self.logger.error(
                            f"Schema mismatch for {table_name}.{field.name}: "
                            f"existing={existing_field.type}, new={field.type}"
                        )
                        raise ValueError(
                            f"Schema incompatibility in {table_name}: "
                            f"Column '{field.name}' type mismatch "
                            f"(existing: {existing_field.type}, new: {field.type})"
                        )
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # New table - no validation needed
                self.logger.debug(f"No existing table for {table_name} - skipping schema validation")
                return True
            else:
                self.logger.warning(f"Could not validate schema for {table_name}: {e}")
                return True  # Don't block on validation errors
        except Exception as e:
            self.logger.warning(f"Schema validation failed for {table_name}: {e}")
            return True  # Don't block on validation errors
    
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
        
        # ✅ PRIORITY 3: Validate schema compatibility before write
        self._validate_schema_compatibility(df, table_name, 'warehouse')
        
        rows_saved = self.bucket_adapter.store_data_streaming(
            df=df,
            table_name=table_name,
            schema='warehouse',
            rows_per_group=10000
        )
        self.logger.info(f"💾 Saved {rows_saved:,} rows to bucket: warehouse/{table_name}")


__all__ = ['DimensionOrchestrator']
