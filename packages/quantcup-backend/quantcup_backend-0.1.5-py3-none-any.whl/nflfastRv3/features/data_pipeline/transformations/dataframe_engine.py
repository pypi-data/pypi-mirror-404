"""
DataFrame Engine for Bucket-First Warehouse

Makes SQL-based transformations work with bucket DataFrames by providing
an adapter pattern that integrates memory management, checkpointing, and
schema validation.

Pattern: Adapter Pattern (2 complexity points)
- Adapter logic: 1 point
- Integration with utilities: 1 point

Usage:
    from .dataframe_engine import create_dataframe_engine
    
    # Create engine with production safeguards
    engine = create_dataframe_engine(
        table_name='play_by_play',
        schema='raw_nflfastr',
        seasons=[2020, 2021, 2022],
        max_memory_mb=1536,  # Conservative for S2 instance
        logger=logger
    )
    
    # Use in transformations
    if isinstance(engine, DataFrameEngine):
        raw_data = engine.df  # Bucket data already loaded & validated
    else:
        # Fallback: Database mode
        raw_data = pd.read_sql(sql, engine)
"""

import os
import gc
import io
from typing import List, Optional
import pandas as pd
from uuid import uuid4
from commonv2 import get_logger
from commonv2.utils.memory import MemoryManager
from commonv2.utils.checkpointing import CheckpointManager
from commonv2.utils.validation import UnifiedDataValidator
from commonv2.persistence.bucket_adapter import BucketAdapter

# Spill configuration for memory management (configurable via environment or arguments)
SPILL_MIN_FREE_MB = int(os.getenv('SPILL_MIN_FREE_MB', '200'))  # Spill when <200MB free headroom
SPILL_MAX_ROWS = int(os.getenv('SPILL_MAX_ROWS', '1000000'))  # Spill when >1M rows accumulated
MEMORY_SPILL_THRESHOLD_PCT = float(os.getenv('MEMORY_SPILL_THRESHOLD_PCT', '0.85'))  # Spill at 85%
GC_FREQUENCY = os.getenv('GC_FREQUENCY', 'major_only')  # 'always', 'major_only', or 'never'

# Module-level logger
_logger = get_logger('nflfastRv3.transformations.dataframe_engine')


def _maybe_gc(frequency: str = GC_FREQUENCY) -> None:
    """
    Conditionally run garbage collection based on configured frequency.
    
    Args:
        frequency: 'always', 'major_only', or 'never'
    """
    if frequency == 'always':
        gc.collect()
    elif frequency == 'major_only':
        # Only run GC after major operations (default)
        pass  # Caller controls when to call this for major ops
    # 'never' does nothing


class DataFrameEngine:
    """
    Adapter that makes bucket DataFrames work with SQL-based transformations.
    
    Wraps a DataFrame to provide an engine-like interface that transformation
    functions can use interchangeably with database engines.
    
    Pattern: Adapter Pattern (2 complexity points)
    - Adapter logic: 1 point
    - Integration with utilities: 1 point
    
    Attributes:
        df: The loaded and validated DataFrame
        schema: Schema name (e.g., 'raw_nflfastr')
        table_name: Table name (e.g., 'play_by_play')
        metadata: Additional metadata about the data
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        schema: str = 'raw_nflfastr',
        table_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Initialize DataFrame engine.
        
        Args:
            df: The DataFrame to wrap
            schema: Schema name
            table_name: Table name
            metadata: Additional metadata
        """
        self.df = df
        self.schema = schema
        self.table_name = table_name
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DataFrameEngine(table={self.table_name}, "
            f"schema={self.schema}, "
            f"rows={len(self.df):,}, "
            f"columns={len(self.df.columns)})"
        )


def create_dataframe_engine(
    table_name: str,
    schema: str = 'raw_nflfastr',
    seasons: Optional[List[int]] = None,
    columns: Optional[List[str]] = None,
    max_memory_mb: int = 1536,  # Conservative for S2 instance (75% of 2GB)
    bucket_adapter: Optional[BucketAdapter] = None,
    logger=None
) -> DataFrameEngine:
    """
    Create DataFrameEngine with production safeguards.
    
    Integrates commonv2 utilities:
    - MemoryManager: Prevents OOM kills with proactive checks
    - CheckpointManager: Enables resume capability (S3 storage)
    - UnifiedDataValidator: Schema validation
    
    Args:
        table_name: Name of the table to load
        schema: Schema name (default: 'raw_nflfastr')
        seasons: Optional list of seasons to load (default: all available)
        columns: Optional list of columns to load (default: all)
        max_memory_mb: Maximum memory to use in MB (default: 1536 for S2)
        bucket_adapter: Optional BucketAdapter instance
        logger: Optional logger instance
        
    Returns:
        DataFrameEngine with loaded and validated data
        
    Example:
        >>> engine = create_dataframe_engine(
        ...     table_name='play_by_play',
        ...     seasons=[2020, 2021, 2022],
        ...     max_memory_mb=1536
        ... )
        >>> print(f"Loaded {len(engine.df):,} rows")
    """
    logger = logger or _logger
    bucket = bucket_adapter or BucketAdapter(logger=logger)
    
    # Initialize commonv2 utilities
    memory_manager = MemoryManager(max_memory_mb=max_memory_mb, logger=logger)
    checkpoint_manager = CheckpointManager(
        storage_backend='s3',
        bucket_adapter=bucket,
        max_checkpoints=5
    )
    validator = UnifiedDataValidator(logger=logger)
    
    logger.info(f"Creating DataFrameEngine for {schema}.{table_name}")
    memory_manager.log_status()
    
    # Try to resume from checkpoint
    operation_id = f"warehouse_{table_name}"
    partial_df, remaining_seasons = checkpoint_manager.resume(operation_id)
    
    # Discover seasons to load
    if seasons is None:
        all_seasons = _discover_season_partitions(bucket, schema, table_name, logger)
    else:
        all_seasons = seasons
    
    # FIX: Retrieve orphaned spill files from previous checkpoint
    # These contain data that was already processed but spilled to bucket
    checkpoint_spill_keys = []
    if partial_df is not None:
        # Try to retrieve checkpoint metadata using new method
        checkpoint_metadata = checkpoint_manager.get_metadata(operation_id)
        if checkpoint_metadata and 'spill_keys' in checkpoint_metadata:
            checkpoint_spill_keys = checkpoint_metadata['spill_keys']
            logger.info(f"📦 Found {len(checkpoint_spill_keys)} orphaned spill files from previous checkpoint")
    
    # Determine which seasons to process
    if partial_df is not None and isinstance(partial_df, pd.DataFrame):
        completed_seasons = [s for s in all_seasons if s not in (remaining_seasons or [])]
        logger.info(
            f"🔄 Resuming from checkpoint: {len(partial_df):,} rows already processed, "
            f"{len(completed_seasons)}/{len(all_seasons)} seasons completed, "
            f"{len(remaining_seasons or [])} seasons remaining"
        )
        # Start with checkpoint data
        accumulated_df = partial_df
        seasons_to_load = remaining_seasons if remaining_seasons else []
        seasons_completed = completed_seasons
    else:
        # Start fresh
        accumulated_df = pd.DataFrame()
        seasons_to_load = all_seasons
        seasons_completed = []
    
    # INCREMENTAL PROCESSING: Load, validate, and accumulate one season at a time
    # This prevents memory accumulation by releasing each season's DataFrame after concat
    # NEW: Spill to bucket when memory is hot to prevent OOM kills
    # FIX: Track NEW spill files separately from checkpoint spills
    new_spill_keys = []  # Track NEW spill files for final stitching
    
    for i, season in enumerate(sorted(seasons_to_load)):
        season_key = f"{schema}/{table_name}/season={season}/{table_name}_{season}.parquet"
        
        try:
            # FIX #3: Hard stop gate - Force spill BEFORE loading if memory exhausted
            if memory_manager.get_available_mb() <= 0:
                logger.warning("💥 No headroom left: forcing spill before next load")
                
                if not accumulated_df.empty and bucket.s3_client is not None and bucket.bucket_name is not None:
                    spill_key = f"checkpoints/warehouse/{table_name}/spill_{uuid4().hex}.parquet"
                    
                    # Write spill file to bucket
                    buffer = io.BytesIO()
                    accumulated_df.to_parquet(buffer, engine='pyarrow', index=False)
                    buffer.seek(0)
                    
                    bucket.s3_client.put_object(
                        Bucket=bucket.bucket_name,
                        Key=spill_key,
                        Body=buffer.getvalue()
                    )
                    
                    logger.info(f"💾 Emergency spill: {len(accumulated_df):,} rows to {spill_key}")
                    new_spill_keys.append(spill_key)
                    accumulated_df = pd.DataFrame()
                    gc.collect()
                    memory_manager.log_status()
            
            # Pre-flight memory check
            try:
                if bucket.s3_client is not None and bucket.bucket_name is not None:
                    response = bucket.s3_client.head_object(
                        Bucket=bucket.bucket_name,
                        Key=season_key
                    )
                    file_size_bytes = response['ContentLength']
                else:
                    file_size_bytes = 0
            except Exception as e:
                logger.warning(f"Could not get file size for {season_key}: {e}")
                file_size_bytes = 0
            
            # Estimate memory requirement
            if file_size_bytes > 0:
                estimated_mb = memory_manager.estimate_parquet_memory(file_size_bytes)
                
                # Load based on memory availability
                if memory_manager.can_load(estimated_mb):
                    df_season = _load_partition_full(bucket, season_key, columns, logger)
                else:
                    logger.warning(
                        f"⚠️ Memory limit - using chunked processing for season {season}"
                    )
                    df_season = _load_partition_chunked(
                        bucket, season_key, columns, memory_manager, logger
                    )
            else:
                # No size info, try loading directly
                df_season = _load_partition_full(bucket, season_key, columns, logger)
            
            if df_season.empty:
                logger.warning(f"No data loaded for season {season}")
                continue
            
            # Validate schema using existing UnifiedDataValidator
            # FIX: play_id column added in 2000+ seasons - 1999 data doesn't have it
            # Only validate truly universal columns (game_id, season)
            # Individual transformations (dim_game, fact_play) handle their own requirements
            if table_name == 'play_by_play':
                # Core fields present in ALL seasons (including 1999)
                required_columns = ['game_id', 'season']
                # play_id is in unique_keys but not required (missing in 1999)
            else:
                # Other tables: no hardcoded validation (transformation-specific)
                required_columns = None
            
            result = validator.validate_dataframe(
                df_season,
                table_name=table_name,
                min_rows=1,
                required_columns=required_columns
            )
            
            if not result['valid']:
                error_msg = (
                    f"Schema validation failed for {table_name} season {season}:\n"
                    f"{chr(10).join(result['errors'])}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Standardize dtypes for PostgreSQL compatibility
            df_season = validator.standardize_dtypes_for_postgres(df_season, table_name)
            
            # MEMORY OPTIMIZATION: Concatenate immediately and release season DataFrame
            if accumulated_df.empty:
                accumulated_df = df_season
            else:
                accumulated_df = pd.concat([accumulated_df, df_season], ignore_index=True)
            
            # Explicitly delete season DataFrame (GC only when needed, not every iteration)
            del df_season
            
            seasons_completed.append(season)
            logger.info(f"✅ Loaded season {season}: {len(accumulated_df):,} total rows")
            memory_manager.log_status()
            
            # FIX #1: Spill to bucket when memory is hot
            if (memory_manager.get_available_mb() < SPILL_MIN_FREE_MB or len(accumulated_df) > SPILL_MAX_ROWS) and bucket.s3_client is not None and bucket.bucket_name is not None:
                spill_key = f"checkpoints/warehouse/{table_name}/spill_{uuid4().hex}.parquet"
                
                # Write spill file to bucket
                buffer = io.BytesIO()
                accumulated_df.to_parquet(buffer, engine='pyarrow', index=False)
                buffer.seek(0)
                
                bucket.s3_client.put_object(
                    Bucket=bucket.bucket_name,
                    Key=spill_key,
                    Body=buffer.getvalue()
                )
                
                logger.info(
                    f"💾 Spilled {len(accumulated_df):,} rows to {spill_key} and cleared RAM "
                    f"(free: {memory_manager.get_available_mb():.0f}MB, rows: {len(accumulated_df):,})"
                )
                new_spill_keys.append(spill_key)
                accumulated_df = pd.DataFrame()
                gc.collect()
                memory_manager.log_status()
            
            # Checkpoint every 5 seasons
            if (i + 1) % 5 == 0:
                checkpoint_manager.create_checkpoint(
                    operation_id=operation_id,
                    partial_data=accumulated_df,
                    items_completed=seasons_completed,
                    items_remaining=[s for s in seasons_to_load if s not in seasons_completed]
                )
                logger.info(f"📍 Checkpoint created: {len(seasons_completed)}/{len(all_seasons)} seasons")
        
        except Exception as e:
            # Save emergency checkpoint on failure (including spill if needed)
            if not accumulated_df.empty:
                # Emergency spill before checkpoint
                if len(accumulated_df) > 0 and bucket.s3_client is not None and bucket.bucket_name is not None:
                    spill_key = f"checkpoints/warehouse/{table_name}/emergency_spill_{uuid4().hex}.parquet"
                    
                    buffer = io.BytesIO()
                    accumulated_df.to_parquet(buffer, engine='pyarrow', index=False)
                    buffer.seek(0)
                    
                    bucket.s3_client.put_object(
                        Bucket=bucket.bucket_name,
                        Key=spill_key,
                        Body=buffer.getvalue()
                    )
                    
                    logger.info(f"💾 Emergency spill: {len(accumulated_df):,} rows to {spill_key}")
                    new_spill_keys.append(spill_key)
                
                # FIX: Include both old checkpoint spills and new spills
                all_spill_keys_emergency = checkpoint_spill_keys + new_spill_keys
                checkpoint_manager.create_checkpoint(
                    operation_id=operation_id,
                    partial_data=pd.DataFrame(),  # Empty, data is in spills
                    items_completed=seasons_completed,
                    items_remaining=[s for s in seasons_to_load if s not in seasons_completed],
                    metadata={'spill_keys': all_spill_keys_emergency}  # Track ALL spills in checkpoint
                )
                logger.info(f"📍 Emergency checkpoint saved before failure (with {len(all_spill_keys_emergency)} spills)")
            
            logger.error(f"Failed to load season {season}: {e}")
            raise
    
    # FIX: Merge checkpoint spills with new spills before stitching
    # This prevents data loss from checkpoint spills being orphaned
    all_spill_keys = checkpoint_spill_keys + new_spill_keys
    
    # FIX #1 & #2: Memory-safe incremental stitching of spill files
    if all_spill_keys and bucket.s3_client is not None and bucket.bucket_name is not None:
        logger.info(f"🔗 Stitching {len(all_spill_keys)} spill files incrementally (memory-safe)...")
        if checkpoint_spill_keys:
            logger.info(f"  ├─ {len(checkpoint_spill_keys)} from previous checkpoint")
        if new_spill_keys:
            logger.info(f"  └─ {len(new_spill_keys)} from current run")
        
        # PRE-STITCH VALIDATION: Track expected row counts
        expected_total_rows = len(accumulated_df) if not accumulated_df.empty else 0
        logger.info(f"📊 Pre-stitch row count tracking:")
        logger.info(f"  - Accumulator: {expected_total_rows:,} rows")
        
        for spill_key in all_spill_keys:
            try:
                # Get spill file metadata to track expected rows
                response = bucket.s3_client.head_object(
                    Bucket=bucket.bucket_name,
                    Key=spill_key
                )
                # Read parquet metadata to get exact row count
                spill_response = bucket.s3_client.get_object(
                    Bucket=bucket.bucket_name,
                    Key=spill_key
                )
                spill_bytes = spill_response['Body'].read()
                
                import pyarrow.parquet as pq
                parquet_file = pq.ParquetFile(io.BytesIO(spill_bytes))
                spill_rows = parquet_file.metadata.num_rows
                expected_total_rows += spill_rows
                logger.info(f"  - {os.path.basename(spill_key)}: {spill_rows:,} rows")
                
                # Clean up
                del spill_bytes, parquet_file
                _maybe_gc('major_only')
            except Exception as e:
                logger.warning(f"Could not pre-validate spill {spill_key}: {e}")
        
        logger.info(f"  - Expected total after stitching: {expected_total_rows:,} rows")
        
        # Check if we have enough memory for traditional stitching
        available_mb = memory_manager.get_available_mb()
        
        # If memory is critically low, use chunked stitching to avoid OOM
        if available_mb < 100:
            logger.warning(
                f"⚠️ Low memory ({available_mb:.1f}MB available) - using chunked stitching to prevent OOM"
            )
            df = _stitch_spills_chunked(
                bucket,
                all_spill_keys,
                accumulated_df,
                table_name,
                memory_manager,
                logger
            )
        else:
            # Traditional stitching: load each spill and concat
            # Start with final accumulator (already in memory)
            df = accumulated_df
            
            # Stitch each spill one at a time to avoid OOM
            for i, spill_key in enumerate(all_spill_keys):
                # Memory check before loading each spill
                if memory_manager.get_available_mb() < 50:
                    logger.warning(
                        f"⚠️ Memory running low during stitch {i+1}/{len(all_spill_keys)} - "
                        f"switching to chunked mode"
                    )
                    # Switch to chunked stitching for remaining spills
                    remaining_spills = all_spill_keys[i:]
                    df = _stitch_spills_chunked(
                        bucket,
                        remaining_spills,
                        df,
                        table_name,
                        memory_manager,
                        logger
                    )
                    break
                
                try:
                    # Read spill file from bucket
                    response = bucket.s3_client.get_object(
                        Bucket=bucket.bucket_name,
                        Key=spill_key
                    )
                    spill_bytes = response['Body'].read()
                    spill_df = pd.read_parquet(io.BytesIO(spill_bytes), engine='pyarrow')
                    
                    # Concatenate and immediately release spill
                    df = pd.concat([df, spill_df], ignore_index=True)
                    del spill_df
                    gc.collect()
                    
                    logger.info(f"  ✅ Stitched {i+1}/{len(all_spill_keys)}: {len(df):,} total rows")
                    memory_manager.log_status()
                except Exception as e:
                    logger.error(f"Failed to stitch spill file {spill_key}: {e}")
                    raise  # Don't silently continue - this is critical data
        
        logger.info(f"✅ Final stitched result: {len(df):,} rows from {len(all_spill_keys)} spills + accumulator")
        
        # POST-STITCH VALIDATION: Verify row counts match expected
        if len(df) != expected_total_rows:
            logger.error(
                f"❌ DATA LOSS DETECTED: Expected {expected_total_rows:,} rows after stitching, "
                f"but got {len(df):,} rows. Missing {expected_total_rows - len(df):,} rows!"
            )
            raise ValueError(
                f"Stitching resulted in data loss: expected {expected_total_rows:,} rows "
                f"but got {len(df):,} rows"
            )
        else:
            logger.info(f"✅ Row count validation passed: {len(df):,} rows match expected")
        
        # Clean up ALL spill files after successful stitching
        for spill_key in all_spill_keys:
            try:
                bucket.s3_client.delete_object(
                    Bucket=bucket.bucket_name,
                    Key=spill_key
                )
                logger.debug(f"  Deleted spill: {spill_key}")
            except Exception as e:
                logger.warning(f"Failed to delete spill file {spill_key}: {e}")
    else:
        # No spills - use accumulated_df directly
        df = accumulated_df
    
    # Final result validation
    if df.empty:
        logger.warning(f"No data loaded for {table_name}")
    else:
        logger.info(f"✅ Combined {len(seasons_completed)} seasons: {len(df):,} total rows")
    
    # Clear checkpoints on success
    checkpoint_manager.clear_checkpoints(operation_id)
    
    # Log final memory status
    memory_manager.log_status()
    
    return DataFrameEngine(
        df=df,
        schema=schema,
        table_name=table_name,
        metadata={
            'seasons_loaded': seasons_to_load,
            'total_rows': len(df),
            'total_columns': len(df.columns) if not df.empty else 0
        }
    )


def _discover_season_partitions(
    bucket: BucketAdapter,
    schema: str,
    table_name: str,
    logger
) -> List[int]:
    """
    Discover available season partitions in bucket.
    
    Args:
        bucket: BucketAdapter instance
        schema: Schema name
        table_name: Table name
        logger: Logger instance
        
    Returns:
        List of available season numbers
    """
    if bucket.s3_client is None or bucket.bucket_name is None:
        logger.error("Bucket client not available for discovering seasons")
        return []
    
    try:
        prefix = f"{schema}/{table_name}/season="
        response = bucket.s3_client.list_objects_v2(
            Bucket=bucket.bucket_name,
            Prefix=prefix,
            Delimiter='/'
        )
        
        seasons = []
        if 'CommonPrefixes' in response:
            for prefix_obj in response['CommonPrefixes']:
                # Extract season from prefix like "schema/table/season=2020/"
                prefix_path = prefix_obj['Prefix'].rstrip('/')
                season_str = prefix_path.split('=')[-1]
                try:
                    season = int(season_str)
                    seasons.append(season)
                except ValueError:
                    logger.warning(f"Could not parse season from: {prefix_path}")
        
        seasons.sort()
        logger.info(f"Discovered {len(seasons)} seasons for {table_name}: {seasons}")
        return seasons
        
    except Exception as e:
        logger.error(f"Failed to discover seasons for {table_name}: {e}")
        return []


def _load_partition_full(
    bucket: BucketAdapter,
    key: str,
    columns: Optional[List[str]],
    logger
) -> pd.DataFrame:
    """
    Load full partition from bucket.
    
    Args:
        bucket: BucketAdapter instance
        key: S3 key for the partition
        columns: Optional list of columns to load
        logger: Logger instance
        
    Returns:
        DataFrame with partition data
    """
    if bucket.s3_client is None or bucket.bucket_name is None:
        logger.error(f"Bucket client not available for loading partition {key}")
        return pd.DataFrame()
    
    try:
        response = bucket.s3_client.get_object(
            Bucket=bucket.bucket_name,
            Key=key
        )
        
        parquet_bytes = response['Body'].read()
        df = pd.read_parquet(
            io.BytesIO(parquet_bytes),
            engine='pyarrow',
            columns=columns
        )
        
        logger.debug(f"Loaded full partition: {key} ({len(df):,} rows)")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load partition {key}: {e}")
        return pd.DataFrame()


def _load_partition_chunked(
    bucket: BucketAdapter,
    key: str,
    columns: Optional[List[str]],
    memory_manager: MemoryManager,
    logger
) -> pd.DataFrame:
    """
    Load partition in chunks to manage memory.
    
    MEMORY OPTIMIZATION: Concatenates chunks incrementally and releases memory
    after each chunk to prevent accumulation.
    
    Args:
        bucket: BucketAdapter instance
        key: S3 key for the partition
        columns: Optional list of columns to load
        memory_manager: MemoryManager instance
        logger: Logger instance
        
    Returns:
        DataFrame with partition data
    """
    if bucket.s3_client is None or bucket.bucket_name is None:
        logger.error(f"Bucket client not available for chunked loading of {key}")
        return pd.DataFrame()
    
    try:
        import pyarrow.parquet as pq
        
        # Download to temporary location for chunked reading
        response = bucket.s3_client.get_object(
            Bucket=bucket.bucket_name,
            Key=key
        )
        
        parquet_bytes = response['Body'].read()
        parquet_file = pq.ParquetFile(io.BytesIO(parquet_bytes))
        
        # Calculate optimal chunk size
        total_rows = parquet_file.metadata.num_rows
        available_mb = memory_manager.get_available_mb() * 0.5  # Use 50% of available
        
        # Estimate rows per chunk based on available memory
        # Rough estimate: 1MB per 10,000 rows (adjust based on actual data)
        rows_per_mb = 10000
        chunk_size = int(available_mb * rows_per_mb)
        chunk_size = max(1000, min(chunk_size, total_rows))  # Between 1K and total
        
        logger.info(
            f"Chunked loading: {total_rows:,} rows in chunks of {chunk_size:,}"
        )
        
        # MEMORY OPTIMIZATION: Concatenate incrementally instead of accumulating
        accumulated_df = pd.DataFrame()
        chunk_count = 0
        
        for batch in parquet_file.iter_batches(batch_size=chunk_size, columns=columns):
            chunk_df = batch.to_pandas()
            chunk_count += 1
            
            # Concatenate immediately and release chunk
            if accumulated_df.empty:
                accumulated_df = chunk_df
            else:
                accumulated_df = pd.concat([accumulated_df, chunk_df], ignore_index=True)
            
            # Explicitly delete chunk and force garbage collection
            del chunk_df
            gc.collect()
        
        logger.debug(
            f"Loaded chunked partition: {key} ({len(accumulated_df):,} rows, {chunk_count} chunks)"
        )
        return accumulated_df
        
    except Exception as e:
        logger.error(f"Failed to load partition chunked {key}: {e}")
        # Fallback to full load
        return _load_partition_full(bucket, key, columns, logger)


def _stitch_spills_chunked(
    bucket: BucketAdapter,
    spill_keys: List[str],
    accumulated_df: pd.DataFrame,
    table_name: str,
    memory_manager: MemoryManager,
    logger
) -> pd.DataFrame:
    """
    Stitch spill files using chunked processing to avoid OOM.
    
    Instead of loading entire spills into memory, this function:
    1. Streams data from spills in small chunks
    2. Writes to a temporary aggregated parquet file
    3. Reads back the final result in chunks if needed
    
    This approach trades speed for memory safety - it's slower but won't OOM.
    
    Args:
        bucket: BucketAdapter instance
        spill_keys: List of spill file keys in S3
        accumulated_df: Current accumulated DataFrame in memory
        table_name: Name of the table (for temporary file naming)
        memory_manager: MemoryManager instance
        logger: Logger instance
        
    Returns:
        Final stitched DataFrame
    """
    import pyarrow as pa
    import pyarrow.parquet as pq
    
    logger.info(f"📦 Starting chunked stitching for {len(spill_keys)} spills (memory-constrained mode)")
    
    # Create a temporary output key for the stitched result
    output_key = f"checkpoints/warehouse/{table_name}/stitched_{uuid4().hex}.parquet"
    
    # Track expected vs actual row counts for validation
    expected_total_rows = len(accumulated_df) if not accumulated_df.empty else 0
    logger.info(f"  Initial accumulator: {expected_total_rows:,} rows")
    
    try:
        # Collect all tables/batches to write
        all_tables = []
        total_rows_tracked = 0
        
        # Step 1: Convert accumulator to Arrow table if not empty
        if not accumulated_df.empty:
            logger.info(f"  Adding accumulator ({len(accumulated_df):,} rows)...")
            table = pa.Table.from_pandas(accumulated_df)
            all_tables.append(table)
            total_rows_tracked += len(table)
            
            # Clear accumulator from memory
            del accumulated_df
            gc.collect()
            memory_manager.log_status()
        
        # Step 2: Process each spill file incrementally
        for i, spill_key in enumerate(spill_keys):
            logger.info(f"  Processing spill {i+1}/{len(spill_keys)}: {spill_key}")
            
            try:
                # Download spill file
                response = bucket.s3_client.get_object(
                    Bucket=bucket.bucket_name,
                    Key=spill_key
                )
                spill_bytes = response['Body'].read()
                
                # Open as parquet file
                parquet_file = pq.ParquetFile(io.BytesIO(spill_bytes))
                spill_rows = parquet_file.metadata.num_rows
                expected_total_rows += spill_rows  # Track expected rows
                
                # Check if we can load this spill into memory
                available_mb = memory_manager.get_available_mb()
                
                if available_mb > 50:
                    # Load entire spill as table
                    table = parquet_file.read()
                    all_tables.append(table)
                    total_rows_tracked += len(table)
                    logger.info(f"    ✅ Loaded {spill_rows:,} rows (cumulative: {total_rows_tracked:,})")
                else:
                    # Process in smaller batches
                    batch_size = max(1000, int((available_mb / 100) * 10000))
                    logger.info(
                        f"    Low memory - processing in batches of {batch_size:,}"
                    )
                    
                    batch_count = 0
                    batch_rows_total = 0
                    for batch in parquet_file.iter_batches(batch_size=batch_size):
                        all_tables.append(batch)
                        batch_rows = len(batch)
                        total_rows_tracked += batch_rows
                        batch_rows_total += batch_rows
                        batch_count += 1
                        
                        # Write intermediate result if tables accumulate
                        if len(all_tables) >= 10:
                            logger.info(f"      Writing intermediate result ({len(all_tables)} chunks)...")
                            _write_combined_table(
                                bucket, output_key, all_tables, logger
                            )
                            all_tables = []
                            gc.collect()
                    
                    logger.info(f"    ✅ Processed {batch_rows_total:,} rows in {batch_count} batches (cumulative: {total_rows_tracked:,})")
                
                # Clean up
                del spill_bytes
                gc.collect()
                
                # Write intermediate if we have many tables in memory
                if len(all_tables) >= 5:
                    logger.info(f"    Writing intermediate result ({len(all_tables)} chunks)...")
                    _write_combined_table(
                        bucket, output_key, all_tables, logger
                    )
                    all_tables = []
                    gc.collect()
                    memory_manager.log_status()
                
            except Exception as e:
                logger.error(f"Failed to process spill {spill_key}: {e}")
                raise
        
        # Step 3: Write final combined result if we have remaining tables
        if all_tables:
            logger.info(f"  Writing final result ({len(all_tables)} remaining chunks)...")
            _write_combined_table(
                bucket, output_key, all_tables, logger
            )
        
        # Step 4: Download final stitched result
        logger.info(f"  📥 Downloading final stitched result from {output_key}")
        final_response = bucket.s3_client.get_object(
            Bucket=bucket.bucket_name,
            Key=output_key
        )
        final_bytes = final_response['Body'].read()
        final_df = pd.read_parquet(io.BytesIO(final_bytes), engine='pyarrow')
        
        logger.info(f"✅ Chunked stitching complete: {len(final_df):,} total rows")
        
        # VALIDATION: Verify row counts
        logger.info(f"  Row count validation:")
        logger.info(f"    - Expected: {expected_total_rows:,} rows")
        logger.info(f"    - Tracked during processing: {total_rows_tracked:,} rows")
        logger.info(f"    - Final result: {len(final_df):,} rows")
        
        if len(final_df) != expected_total_rows:
            logger.error(
                f"❌ DATA LOSS in chunked stitching: Expected {expected_total_rows:,} rows, "
                f"got {len(final_df):,} rows. Missing {expected_total_rows - len(final_df):,} rows!"
            )
            raise ValueError(
                f"Chunked stitching lost data: expected {expected_total_rows:,} rows "
                f"but final result has {len(final_df):,} rows"
            )
        
        logger.info(f"  ✅ Row count validation passed")
        
        # Clean up temporary output file
        try:
            bucket.s3_client.delete_object(
                Bucket=bucket.bucket_name,
                Key=output_key
            )
            logger.debug(f"  Deleted temporary output: {output_key}")
        except Exception as e:
            logger.warning(f"Failed to delete temporary output {output_key}: {e}")
        
        return final_df
        
    except Exception as e:
        logger.error(f"Chunked stitching failed: {e}")
        # Try to clean up temporary file
        try:
            bucket.s3_client.delete_object(
                Bucket=bucket.bucket_name,
                Key=output_key
            )
        except:
            pass
        raise


def _write_combined_table(
    bucket: BucketAdapter,
    output_key: str,
    tables: list,
    logger
) -> None:
    """
    Write combined Arrow tables to S3.
    
    If output file already exists, appends to it. Otherwise creates new file.
    
    Args:
        bucket: BucketAdapter instance
        output_key: S3 key for output file
        tables: List of Arrow tables/batches to write
        logger: Logger instance
    """
    import pyarrow as pa
    import pyarrow.parquet as pq
    
    try:
        # Check if output already exists
        try:
            response = bucket.s3_client.head_object(
                Bucket=bucket.bucket_name,
                Key=output_key
            )
            file_exists = True
        except:
            file_exists = False
        
        # Combine new tables
        if len(tables) == 1:
            new_table = tables[0] if isinstance(tables[0], pa.Table) else pa.Table.from_batches([tables[0]])
        else:
            # Ensure all are tables
            arrow_tables = []
            for t in tables:
                if isinstance(t, pa.Table):
                    arrow_tables.append(t)
                else:
                    arrow_tables.append(pa.Table.from_batches([t]))
            new_table = pa.concat_tables(arrow_tables)
        
        if file_exists:
            # Download existing, append, re-upload
            existing_response = bucket.s3_client.get_object(
                Bucket=bucket.bucket_name,
                Key=output_key
            )
            existing_bytes = existing_response['Body'].read()
            existing_table = pq.read_table(io.BytesIO(existing_bytes))
            
            # Combine tables
            combined_table = pa.concat_tables([existing_table, new_table])
            
            # Clean up
            del existing_bytes, existing_table, new_table
            gc.collect()
        else:
            combined_table = new_table
        
        # Write to buffer and upload
        buffer = io.BytesIO()
        pq.write_table(combined_table, buffer)
        buffer.seek(0)
        
        bucket.s3_client.put_object(
            Bucket=bucket.bucket_name,
            Key=output_key,
            Body=buffer.getvalue()
        )
        
        logger.debug(f"    Wrote {len(combined_table):,} total rows to {output_key}")
        
        # Clean up
        del combined_table, buffer
        gc.collect()
        
    except Exception as e:
        logger.error(f"Failed to write combined table: {e}")
        raise


__all__ = ['DataFrameEngine', 'create_dataframe_engine']