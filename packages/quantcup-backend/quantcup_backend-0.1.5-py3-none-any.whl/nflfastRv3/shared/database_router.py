"""
Database Router for Table-Driven Routing

Simplified router following REFACTORING_SPECS.md constraints:
- Maximum 2 complexity points (DI + routing logic)
- Config-driven database routing
- Clean separation of concerns

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 3 (Infrastructure)

Refactored to comply with REFACTORING_SPECS.md constraints.
Router uses CommonV2 directly, no dependency on NFLfastRDatabase.
"""

import os
import time
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert
import sqlalchemy as sa
from commonv2 import get_logger
from commonv2.core.config import Environment, DatabaseConfig, DatabasePrefixes
from commonv2._data.database import create_db_engine_from_env
from commonv2._data.adapters import DatabaseAdapter, DataCleaningService

# Retry configuration
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    RETRY_AVAILABLE = True
except ImportError:
    RETRY_AVAILABLE = False

# Configurable timeouts from environment
DB_CONNECTION_TIMEOUT = int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
DB_RETRY_ATTEMPTS = int(os.getenv('DB_RETRY_ATTEMPTS', '3'))


class DatabaseRouter:
    """
    Simplified table-driven database routing.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    - Config-driven routing (1 point)
    - Simple strategy selection (1 point)
    
    Refactored to comply with REFACTORING_SPECS.md constraints.
    Uses CommonV2 directly for all database access.
    """
    
    def __init__(self, logger=None):
        """
        Initialize database router with environment-aware default database.
        
        Environment-aware routing:
        - Local/Testing: Uses NFLFASTR_DB (local PostgreSQL)
        - Production: Uses SEVALLA_QUANTCUP_DB (Sevalla remote database)
        
        Args:
            logger: Optional logger instance (uses module logger if not provided)
        """
        self.logger = logger or get_logger('nflfastRv3.router')
        self._engines = {}  # Cache for database engines
        
        # Environment-aware default database selection
        if Environment.is_local() or Environment.is_testing():
            self.default_database = 'NFLFASTR_DB'
        else:  # Production
            self.default_database = 'SEVALLA_QUANTCUP_DB'
        
        self.logger.info(
            f"DatabaseRouter initialized: "
            f"environment={Environment.get_current()}, "
            f"default_database={self.default_database}"
        )

    def route_to_databases(self, df: pd.DataFrame, config) -> bool:
        """
        Route DataFrame to configured databases with environment-aware filtering.
        
        Bucket-First Architecture:
        - Production: Only write to production databases (API_PRODUCTION), filter out local databases
        - Local/Testing: Write to all configured databases
        - Bucket-only tables: Empty databases list = intentionally no DB routing (bucket is primary storage)
        
        This ensures most tables are bucket-only in production, while API tables
        (schedules, teams) that explicitly configure API_PRODUCTION still get written.
        
        Args:
            df: DataFrame to route
            config: DataSourceConfig with routing information and strategy
            
        Returns:
            bool: True if routing completed successfully or table is bucket-only
                  False only if routing was attempted but all databases failed
        """
        if df.empty:
            self.logger.info(f"Skipping routing for {config.table} - no data")
            return True
        
        # Check if table is explicitly bucket-only (empty databases list)
        configured_databases = config.databases if config.databases is not None else [DatabasePrefixes.LOCAL_DEV]
        
        if not configured_databases:
            # Bucket-only table: no database routing needed
            self.logger.info(f"✓ {config.table} is bucket-only (no database routing configured)")
            return True
        
        # Environment-aware filtering for bucket-first architecture
        if Environment.is_production():
            # Production: Only keep production databases (filter out local)
            # This makes most tables bucket-only, while API tables still write to production DB
            target_databases = [db for db in configured_databases if db == DatabasePrefixes.API_PRODUCTION]
        else:
            # Local/Testing: Use all configured databases
            target_databases = configured_databases
        
        # Check if environment filtering resulted in no target databases
        if not target_databases:
            self.logger.info(
                f"✓ {config.table} is bucket-only in {Environment.get_current()} environment "
                f"(configured databases: {configured_databases})"
            )
            return True
        
        success_count = 0
        
        self.logger.info(f"🗄️  Routing {config.table} with strategy '{config.strategy}' to {len(target_databases)} databases: {target_databases}")
        
        for database in target_databases:
            try:
                # Apply simple transforms
                transformed_df = self._apply_transforms(df, config, database)
                
                # Get engine
                engine = self._get_engine_for_database(database)
                if engine is None:
                    self.logger.warning(f"Skipping {database} - engine unavailable")
                    continue
                
                # Simple strategy selection (2 options only)
                rows_written = 0
                if config.strategy == 'incremental':
                    rows_written = self._execute_incremental_load(transformed_df, config, engine)
                elif config.strategy == 'full_refresh':
                    rows_written = self._execute_full_refresh(transformed_df, config, engine)
                else:
                    self.logger.error(f"Unknown strategy '{config.strategy}' for {config.table}")
                    continue
                
                if rows_written > 0:
                    self.logger.info(f"✓ Routed {rows_written:,} rows to {database}: {config.table}")
                    success_count += 1
                else:
                    self.logger.warning(f"No rows written to {database} for {config.table}")
                
            except Exception as e:
                self.logger.error(f"Failed to route {config.table} to {database}: {e}")
                continue
        
        # Only report error if we actually attempted routing but all failed
        if success_count == 0:
            self.logger.error(f"❌ Failed to route {config.table} to any database (attempted: {target_databases})")
            return False
        elif success_count < len(target_databases):
            self.logger.warning(f"⚠️  Partial routing success for {config.table}: {success_count}/{len(target_databases)}")
        
        return success_count > 0

    def _execute_incremental_load(self, df: pd.DataFrame, config, engine) -> int:
        """Execute incremental load using CommonV2."""
        try:
            from commonv2._data.database import execute_incremental_load
            
            table_config = {
                'table': config.table,
                'schema': config.schema,
                'unique_keys': config.unique_keys,
                'chunksize': getattr(config, 'chunksize', None) or 1000
            }
            
            success = execute_incremental_load(
                df=df,
                engine=engine,
                table_name=config.table,
                schema=config.schema,
                table_config=table_config,
                logger=self.logger
            )
            return len(df) if success else 0
            
        except Exception as e:
            self.logger.warning(f"CommonV2 incremental load failed: {e}")
            # Fallback to DatabaseAdapter
            try:
                # Clean the data first
                cleaning_service = DataCleaningService(self.logger)
                clean_df = cleaning_service.clean_for_database(df, table_name=config.table)
                
                # Use DatabaseAdapter for upsert
                db_adapter = DatabaseAdapter(engine, self.logger)
                rows_affected = db_adapter.execute_upsert(
                    clean_df, config.table, config.schema,
                    chunk_size=getattr(config, 'chunksize', None) or 1000
                )
                
                self.logger.info(f"✓ DatabaseAdapter fallback upsert complete: {rows_affected:,} rows affected")
                return rows_affected
            except Exception as fallback_error:
                self.logger.error(f"DatabaseAdapter fallback also failed: {fallback_error}")
                return 0

    def _execute_full_refresh(self, df: pd.DataFrame, config, engine) -> int:
        """Execute full refresh using CommonV2."""
        try:
            from commonv2._data.database import execute_full_refresh
            
            table_config = {
                'table': config.table,
                'schema': config.schema,
                'unique_keys': config.unique_keys,
                'chunksize': getattr(config, 'chunksize', None) or 10000
            }
            
            success = execute_full_refresh(
                df=df,
                engine=engine,
                table_name=config.table,
                schema=config.schema,
                table_config=table_config,
                schema_changes=None,  # Let CommonV2 handle schema detection
                logger=self.logger
            )
            return len(df) if success else 0
            
        except Exception as e:
            self.logger.warning(f"CommonV2 full refresh failed: {e}")
            # Fallback to DatabaseAdapter
            try:
                # Clean the data first
                cleaning_service = DataCleaningService(self.logger)
                clean_df = cleaning_service.clean_for_database(df, table_name=config.table)
                
                # Use DatabaseAdapter for upsert
                db_adapter = DatabaseAdapter(engine, self.logger)
                rows_affected = db_adapter.execute_upsert(
                    clean_df, config.table, config.schema,
                    chunk_size=getattr(config, 'chunksize', None) or 10000
                )
                
                self.logger.info(f"✓ DatabaseAdapter fallback upsert complete: {rows_affected:,} rows affected")
                return rows_affected
            except Exception as fallback_error:
                self.logger.error(f"DatabaseAdapter fallback also failed: {fallback_error}")
                return 0

    def write_streaming(self, df: pd.DataFrame, table_fq: str, pk_cols: List[str],
                       chunk_rows: int = 50_000, memory_monitor=None,
                       conflict_strategy: str = "do_nothing") -> int:
        """
        Write DataFrame to database in chunks with UPSERT (dedupe guard).
        
        This method chunks the DataFrame and uses PostgreSQL upsert to handle duplicates,
        preventing memory spikes from large DataFrame operations.
        
        Args:
            df: DataFrame to write
            table_fq: Fully qualified table name (schema.table)
            pk_cols: Primary key columns for upsert conflict resolution
            chunk_rows: Number of rows per chunk
            memory_monitor: Optional memory monitor for cleanup
            conflict_strategy: Strategy for handling conflicts ("do_nothing" or "do_update")
            
        Returns:
            int: Number of rows written
        """
        if df.empty:
            return 0
        
        try:
            schema, table = table_fq.split('.', 1)
        except ValueError:
            raise ValueError(f"Invalid table format '{table_fq}'. Expected 'schema.table'")
        
        # Get the primary database engine (NFLFASTR_DB)
        engine = self._get_engine_for_database('NFLFASTR_DB')
        if engine is None:
            self.logger.error("Failed to get NFLFASTR_DB engine for streaming write")
            return 0
        
        try:
            # Get table metadata for upsert
            meta = MetaData()
            table_obj = Table(table, meta, schema=schema, autoload_with=engine)
            
            total_rows = len(df)
            written_rows = 0
            
            self.logger.debug(f"Streaming {total_rows:,} rows to {table_fq} in chunks of {chunk_rows:,}")
            
            with engine.begin() as conn:
                for start in range(0, total_rows, chunk_rows):
                    end = min(start + chunk_rows, total_rows)
                    chunk_df = df.iloc[start:end].copy()
                    
                    # Downcast numeric types before shipping to database
                    chunk_df = self._downcast_dtypes(chunk_df)
                    
                    # CRITICAL: replace pandas <NA> / NA scalars with None for DB drivers
                    # This handles pd.NA from nullable Int64/boolean AND Arrow-backed frames.
                    import pandas as pd
                    chunk_df = chunk_df.where(pd.notna(chunk_df), None)
                    
                    # Convert to records for bulk insert
                    rows = chunk_df.to_dict(orient='records')
                    
                    # Create upsert statement
                    stmt = pg_insert(table_obj).values(rows)
                    
                    # Handle conflicts based on strategy
                    if conflict_strategy == "do_update":
                        # "Last write wins" - update existing records
                        update_dict = {c.name: stmt.excluded[c.name] for c in table_obj.columns if c.name not in pk_cols}
                        stmt = stmt.on_conflict_do_update(
                            index_elements=pk_cols,
                            set_=update_dict
                        )
                    else:
                        # Default: do nothing on conflict (pure backfill mode)
                        stmt = stmt.on_conflict_do_nothing(index_elements=pk_cols)
                    
                    # Execute the chunk
                    conn.execute(stmt)
                    written_rows += len(rows)
                    
                    # Clean up chunk from memory
                    del chunk_df, rows
                    
                    # Optional memory cleanup
                    if memory_monitor:
                        memory_monitor.cleanup_memory()
                    
                    self.logger.debug(f"Written chunk {start:,}-{end:,} to {table_fq}")
            
            self.logger.info(f"Streaming write completed: {written_rows:,} rows → {table_fq}")
            return written_rows
            
        except Exception as e:
            self.logger.error(f"Failed to stream write to {table_fq}: {e}")
            return 0

    def _downcast_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Downcast DataFrame dtypes to reduce memory usage before database write.
        
        Args:
            df: DataFrame to downcast
            
        Returns:
            DataFrame with downcasted dtypes
        """
        df_downcasted = df.copy()
        
        # Downcast float64 to float32
        for col in df_downcasted.select_dtypes(include=['float64']).columns:
            df_downcasted[col] = df_downcasted[col].astype('float32')
        
        # Downcast int64 to int32 where safe
        for col in df_downcasted.select_dtypes(include=['int64']).columns:
            col_max = df_downcasted[col].max()
            col_min = df_downcasted[col].min()
            
            # Check if values fit in int32 range
            if col_max <= 2_147_483_647 and col_min >= -2_147_483_648:
                df_downcasted[col] = df_downcasted[col].astype('int32')
        
        return df_downcasted

    def get_engine(self, database: Optional[str] = None):
        """
        Get SQLAlchemy engine for specified database.
        
        Public API method for accessing database engines.
        
        Args:
            database: Database prefix (uses default_database if None)
            
        Returns:
            SQLAlchemy Engine instance
            
        Raises:
            ValueError: If database prefix not found
        """
        db_name = database or self.default_database
        return self._get_engine_for_database(db_name)
    
    def _get_engine_for_database(self, database_prefix: str):
        """
        Get database engine using config-driven approach.
        
        Simplified to use commonv2 configuration directly.
        
        Args:
            database_prefix: Database prefix from DatabasePrefixes constants
            
        Returns:
            SQLAlchemy engine for the specified database
            
        Raises:
            ValueError: If database prefix not found
        """
        # Check cache first
        if database_prefix in self._engines:
            return self._engines[database_prefix]
        
        try:
            # Validate database prefix
            available_databases = DatabasePrefixes.get_all()
            if database_prefix not in available_databases:
                raise ValueError(f"Unknown database prefix: {database_prefix}. Available: {available_databases}")
            
            # Create engine based on database prefix
            if database_prefix == DatabasePrefixes.LOCAL_DEV:
                # Local database - use CommonV2 directly
                engine = create_db_engine_from_env(database_prefix, logger=self.logger)
                self.logger.info(f"✓ Local development database connection successful")
                
            elif database_prefix in [DatabasePrefixes.API_PRODUCTION, DatabasePrefixes.ANALYTICS]:
                # Remote database - use DatabaseConfig
                try:
                    config = DatabaseConfig.load_from_env(database_prefix)
                    
                    # Create engine with structured configuration
                    engine = create_engine(
                        config.connection_url,
                        connect_args={'connect_timeout': 10},
                        pool_pre_ping=True,
                        pool_recycle=3600
                    )
                    
                    # Test connection
                    with engine.connect() as conn:
                        conn.execute(sa.text("SELECT 1"))
                    
                    db_name = "Sevalla QuantCup" if database_prefix == DatabasePrefixes.API_PRODUCTION else "Analytics"
                    self.logger.info(f"✓ {db_name} database connection successful: {config.masked_url}")
                    
                except Exception as e:
                    db_name = "Sevalla QuantCup" if database_prefix == DatabasePrefixes.API_PRODUCTION else "Analytics"
                    self.logger.warning(f"⚠️ {db_name} database connection failed: {e}")
                    return None
            else:
                raise ValueError(f"Unknown database prefix: {database_prefix}")
            
            # Cache the engine only if successfully created
            if engine is not None:
                self._engines[database_prefix] = engine
            return engine
            
        except Exception as e:
            available_databases = DatabasePrefixes.get_all()
            raise ValueError(f"Failed to create engine for {database_prefix}. Available: {available_databases}") from e

    def _apply_transforms(self, df: pd.DataFrame, config, database: str) -> pd.DataFrame:
        """
        Apply simple database-specific transforms.
        
        Simplified transform logic with basic if/else instead of complex patterns.
        
        Args:
            df: Source DataFrame
            config: DataSourceConfig with transform information
            database: Target database identifier
            
        Returns:
            DataFrame: Transformed DataFrame
        """
        transforms = config.transforms.get(database, [])
        
        if not transforms:
            return df.copy()
        
        self.logger.debug(f"Applying {len(transforms)} transforms to {config.table} -> {database}")
        
        transformed_df = df.copy()
        
        for transform_name in transforms:
            try:
                # Simple transform logic (team standardization removed - now handled in cleaning phase)
                if transform_name in ['PARSE_DATES', 'parse_dates']:
                    transformed_df = self._parse_dates_simple(transformed_df)
                elif transform_name in ['ADD_METADATA', 'add_metadata']:
                    transformed_df = self._add_metadata_simple(transformed_df)
                else:
                    self.logger.warning(f"Unknown transform: {transform_name}")
                    
            except Exception as e:
                self.logger.error(f"Failed to apply transform '{transform_name}': {e}")
                continue
        
        return transformed_df

    def _parse_dates_simple(self, df: pd.DataFrame) -> pd.DataFrame:
        """Simple date parsing."""
        df_transformed = df.copy()
        date_columns = ['game_date', 'gameday', 'date', 'birth_date', 'loaded_at']
        
        for col in date_columns:
            if col in df_transformed.columns:
                try:
                    df_transformed[col] = pd.to_datetime(df_transformed[col], errors='coerce')
                except Exception as e:
                    self.logger.warning(f"Failed to parse dates in column {col}: {e}")
        
        return df_transformed

    def _add_metadata_simple(self, df: pd.DataFrame) -> pd.DataFrame:
        """Simple metadata addition."""
        from datetime import datetime
        df_transformed = df.copy()
        
        if 'loaded_at' not in df_transformed.columns:
            df_transformed['loaded_at'] = datetime.now()
        if 'processed_by' not in df_transformed.columns:
            df_transformed['processed_by'] = 'nflfastRv3'
        
        return df_transformed


def get_database_router(logger=None) -> DatabaseRouter:
    """
    Factory function to create database router.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        DatabaseRouter instance
    """
    return DatabaseRouter(logger=logger)


__all__ = ['DatabaseRouter', 'get_database_router']
