"""
Sophisticated loading strategies for database operations.

Provides intelligent loading strategies:
- Incremental loading with year-based data management
- Full refresh with schema change detection
- Drop/recreate for breaking schema changes
- Truncate/upsert for compatible schemas

Following commonv2 patterns:
- Simple dependency injection
- Module-level logger with DI fallback
- Table-config driven (no db_prefix parameters)
- Reusable across quantcup ecosystem
"""

import pandas as pd
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from datetime import datetime

from ..core.logging import get_logger
from .adapters import DatabaseAdapter, DataCleaningService

# Module-level logger with DI fallback
_logger = get_logger('commonv2.loading_strategies')


class LoadingStrategyService:
    """
    Service for sophisticated database loading strategies.
    
    Provides intelligent loading approaches based on data characteristics:
    - Incremental: Delete existing year data → upsert new data
    - Full refresh: Schema detection → drop/recreate OR truncate/upsert
    
    Key Features:
    - Year-based incremental loading
    - Schema change detection integration
    - Automatic strategy selection
    - Table-config driven (no db_prefix parameters)
    - Multi-database support
    
    Example Usage:
        strategy_service = LoadingStrategyService(db_adapter, logger)
        table_config = {
            'table': 'teams',
            'schema': 'raw_nflfastr',
            'databases': ['NFLFASTR_DB', 'SEVALLA_QUANTCUP_DB'],
            'transforms': {'SEVALLA_QUANTCUP_DB': ['standardize_team_names']},
            'unique_keys': ['team_abbr'],
            'chunksize': 1000
        }
        engines = {'NFLFASTR_DB': engine1, 'SEVALLA_QUANTCUP_DB': engine2}
        success = strategy_service.execute_incremental_load(df, table_config, engines)
    """
    
    def __init__(self, db_adapter_or_engine, logger=None):
        """
        Initialize loading strategy service.
        
        Args:
            db_adapter_or_engine: DatabaseAdapter (legacy) or SQLAlchemy Engine (new pattern)
            logger: Optional logger instance
        """
        # Support both old (DatabaseAdapter) and new (Engine) patterns for backward compatibility
        if hasattr(db_adapter_or_engine, 'execute_upsert'):
            # Old pattern: DatabaseAdapter passed
            self.db_adapter = db_adapter_or_engine
            self._engine = db_adapter_or_engine._engine
        else:
            # New pattern: Engine passed directly
            self._engine = db_adapter_or_engine
            self.db_adapter = None  # Create as needed
        
        self.logger = logger or _logger
    
    def _get_db_adapter(self):
        """Get DatabaseAdapter, creating if needed."""
        if self.db_adapter is None:
            from .adapters import DatabaseAdapter
            self.db_adapter = DatabaseAdapter(self._engine, self.logger)
        return self.db_adapter
    
    def execute_incremental_load(
        self, 
        df: pd.DataFrame, 
        table_config: Dict[str, Any], 
        engine,
        current_year: Optional[int] = None
    ) -> bool:
        """
        Execute incremental loading strategy for a single database.
        
        Process:
        1. Detect year column in DataFrame
        2. Filter to current year (if year column exists)
        3. Delete existing data for current year
        4. Upsert new data
        
        Args:
            df: DataFrame to load (already transformed)
            table_config: Table configuration dict with keys:
                - table: Table name
                - schema: Database schema
                - unique_keys: List of unique key columns
                - chunksize: Chunk size for operations
            engine: Database engine for this specific database
            current_year: Optional current year (auto-detected if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        table_name = table_config['table']
        schema = table_config['schema']
        
        self.logger.info(f"Starting incremental load for {schema}.{table_name}")
        
        if df.empty:
            self.logger.warning(f"Empty DataFrame for {schema}.{table_name}")
            return True
        
        # Get current year and detect year column
        if current_year is None:
            try:
                from ..domain.schedules import SeasonParser
                current_year = SeasonParser.get_current_season(self.logger)
            except ImportError:
                # Fallback to current year
                current_year = datetime.now().year
        
        year_col = self.detect_year_column(df)
        
        # Filter to current year if year column exists and no seasons placeholder
        r_call = table_config.get('r_call', '')
        if year_col and '{seasons}' not in r_call:
            original_rows = len(df)
            df_filtered = df[df[year_col].astype(str) == str(current_year)]
            if df_filtered.empty:
                self.logger.info(f"No data for {schema}.{table_name} in {current_year}")
                return True
            
            filtered_rows = len(df_filtered)
            if filtered_rows < original_rows:
                self.logger.info(f"Filtered {original_rows} rows to {filtered_rows} rows for current year {current_year}")
            
            df = df_filtered
        
        try:
            # Delete existing data for this year if year column exists
            if year_col:
                self.delete_existing_data(table_name, schema, year_col, current_year, engine)
            
            # Handle tables without unique keys (simple append)
            unique_keys = table_config.get('unique_keys', [])
            if not unique_keys:
                self.logger.warning(f"No unique keys for '{table_name}'. Using simple append.")
                df.to_sql(
                    table_name,
                    engine,
                    schema=schema,
                    if_exists='append',
                    index=False,
                    chunksize=table_config.get('chunksize', 1000)
                )
                rows = len(df)
                self.logger.info(f"✓ {schema}.{table_name}: Appended {rows:,} new rows ({current_year}).")
                return True
            
            # Upsert new data using DatabaseAdapter
            cleaning_service = DataCleaningService(self.logger)
            clean_df = cleaning_service.clean_for_database(df)
            
            # Use adapter for upsert operations
            adapter = self._get_db_adapter()
            rows_affected = adapter.execute_upsert(
                clean_df, table_name, schema, table_config.get('chunksize', 1000)
            )
            
            self.logger.info(f"✓ {schema}.{table_name}: Upserted {rows_affected:,} rows ({current_year}).")
            return True
            
        except Exception as e:
            self.logger.error(f"Incremental load failed for {schema}.{table_name}: {e}")
            return False
    
    def execute_full_refresh_with_schema(
        self,
        df: pd.DataFrame,
        table_config: Dict[str, Any],
        engine,
        schema_changes: Dict[str, Any]
    ) -> bool:
        """
        Execute full refresh using pre-analyzed schema changes.
        
        OPTIMIZED PATH: Uses centralized schema analysis to eliminate redundant
        schema detection across multiple database targets.
        
        Args:
            df: DataFrame to load (already transformed)
            table_config: Table configuration dict
            engine: Database engine for this specific database
            schema_changes: Pre-analyzed schema changes from centralized detection
            
        Returns:
            True if successful, False otherwise
        """
        table_name = table_config['table']
        schema = table_config['schema']
        
        self.logger.info(f"Starting full refresh for {schema}.{table_name}")
        
        if df.empty:
            self.logger.warning(f"Empty DataFrame for {schema}.{table_name}")
            return True
        
        try:
            # Log strategy decision reasoning with pre-analyzed schema changes
            self.logger.info(f"🎯 STRATEGY_DECISION: {schema}.{table_name} | "
                           f"requires_drop={schema_changes['requires_drop']} | "
                           f"unique_keys={bool(table_config.get('unique_keys'))} | "
                           f"breaking_changes={len(schema_changes['breaking_changes'])}")
            
            # Log schema change warnings if any
            if schema_changes['breaking_changes']:
                self.logger.warning(f"🚨 SCHEMA CHANGES DETECTED in {schema}.{table_name}")
                self.logger.warning("Downstream processes may be affected!")
                for change in schema_changes['breaking_changes']:
                    self.logger.warning(f"  - {change}")
            
            # Choose strategy based on pre-analyzed schema compatibility
            if schema_changes['requires_drop'] or not table_config.get('unique_keys'):
                # Drop and recreate for breaking changes or tables without unique keys
                success = self.drop_and_recreate(df, table_config, engine, schema_changes)
            else:
                # Truncate and upsert for compatible schemas with safety check
                success = self.truncate_and_upsert_with_fallback(df, table_config, engine)
            
            if success:
                self.logger.info(f"✓ Full refresh successful for {schema}.{table_name}")
            else:
                self.logger.error(f"✗ Full refresh failed for {schema}.{table_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Full refresh failed for {schema}.{table_name}: {e}")
            return False

    def execute_full_refresh(
        self,
        df: pd.DataFrame,
        table_config: Dict[str, Any],
        engine,
        schema_changes: Dict[str, Any]
    ) -> bool:
        """
        Execute full refresh loading strategy using pre-analyzed schema changes.
        
        CENTRALIZED ARCHITECTURE: Always requires pre-analyzed schema changes
        to ensure consistent strategy selection across multiple database targets.
        
        Args:
            df: DataFrame to load (already transformed)
            table_config: Table configuration dict
            engine: Database engine for this specific database
            schema_changes: Pre-analyzed schema changes from centralized detection
            
        Returns:
            True if successful, False otherwise
        """
        # Delegate to optimized method - no redundant logic
        return self.execute_full_refresh_with_schema(df, table_config, engine, schema_changes)
    
    def drop_and_recreate(
        self, 
        df: pd.DataFrame, 
        table_config: Dict[str, Any], 
        engine,
        schema_changes: Dict[str, Any]
    ) -> bool:
        """
        Drop table and recreate with new schema using nflfastR proven patterns.
        
        Uses automatic transaction management to prevent hanging issues.
        Based on working nflfastR implementation.
        
        Args:
            df: DataFrame to load
            table_config: Table configuration dict
            engine: Database engine
            schema_changes: Schema change analysis from SchemaDetector
            
        Returns:
            True if successful, False otherwise
        """
        table_name = table_config['table']
        schema = table_config['schema']
        
        self.logger.info(f"🔄 Drop and recreate strategy for {schema}.{table_name}")
        if schema_changes['requires_drop']:
            self.logger.warning("Schema incompatibility requires table recreation")
        
        try:
            # ENSURE SCHEMA EXISTS FIRST (pandas should auto-create, but explicitly ensure it)
            with engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
            self.logger.debug(f"✓ Schema '{schema}' ensured to exist")
            
            # Use nflfastR proven pattern: simple DROP IF EXISTS with automatic transaction management
            self.logger.info(f"Dropping table '{schema}.{table_name}'...")
            with engine.begin() as conn:
                conn.execute(text(f'DROP TABLE IF EXISTS "{schema}"."{table_name}"'))
                self.logger.info(f"Successfully dropped table '{schema}.{table_name}'")
            
            # Create table with proper error handling and verification
            self.logger.info(f"Creating new table with {len(df):,} rows...")
            try:
                # Use smaller chunks for large datasets to prevent timeouts
                chunk_size = min(table_config.get('chunksize', 1000), 5000)
                if len(df) > 10000:
                    chunk_size = 1000  # Use smaller chunks for very large datasets
                    
                self.logger.info(f"Using chunk size of {chunk_size} for table creation...")
                
                # Create the table with proper error handling
                df.to_sql(
                    table_name,
                    engine,
                    schema=schema,
                    if_exists='fail',  # Use 'fail' since we just dropped the table
                    index=False,
                    chunksize=chunk_size
                )
                
                # Verify table was created successfully
                adapter = self._get_db_adapter()
                if not adapter.check_table_exists(table_name, schema):
                    raise Exception(f"Table {schema}.{table_name} was not created successfully")
                
                # Verify row count
                actual_rows = adapter.get_table_row_count(table_name, schema)
                expected_rows = len(df)
                
                if actual_rows != expected_rows:
                    self.logger.warning(f"Row count mismatch: expected {expected_rows}, got {actual_rows}")
                
                self.logger.info(f"✓ {schema}.{table_name}: Recreated table with {actual_rows:,} rows (drop/recreate).")
                
                # Log the new schema for reference
                self.logger.info(f"New table schema: {list(df.columns)}")
                return True
                
            except Exception as create_error:
                self.logger.error(f"Table creation failed: {create_error}")
                # Try to diagnose the issue
                try:
                    adapter = self._get_db_adapter()
                    exists = adapter.check_table_exists(table_name, schema)
                    self.logger.info(f"Table exists after failed creation: {exists}")
                    if exists:
                        row_count = adapter.get_table_row_count(table_name, schema)
                        self.logger.info(f"Partial table has {row_count} rows")
                except Exception as diag_error:
                    self.logger.warning(f"Could not diagnose table creation failure: {diag_error}")
                
                raise create_error
            
        except Exception as e:
            self.logger.error(f"Failed to drop/recreate {schema}.{table_name}: {e}")
            # Connection automatically rolled back by engine.begin() context manager
            return False
    
    def truncate_and_upsert_with_fallback(
        self,
        df: pd.DataFrame,
        table_config: Dict[str, Any],
        engine
    ) -> bool:
        """
        Truncate and upsert with automatic fallback to drop/recreate.
        
        SAFETY NET: Checks if table exists before attempting TRUNCATE.
        If table doesn't exist, automatically falls back to drop/recreate strategy.
        This fixes the "relation does not exist" error in multi-database scenarios.
        
        Args:
            df: DataFrame to load
            table_config: Table configuration dict
            engine: Database engine
            
        Returns:
            True if successful, False otherwise
        """
        table_name = table_config['table']
        schema = table_config['schema']
        
        self.logger.info(f"🔄 Truncate and upsert strategy for {schema}.{table_name}")
        
        # SAFETY CHECK: Verify table exists before TRUNCATE
        adapter = self._get_db_adapter()
        if not adapter.check_table_exists(table_name, schema):
            self.logger.warning(f"🔄 FALLBACK: Table {schema}.{table_name} doesn't exist, "
                               f"switching to drop/recreate strategy")
            return self.drop_and_recreate(
                df, table_config, engine,
                {'requires_drop': True, 'breaking_changes': ['Table does not exist']}
            )
        
        # Proceed with truncate/upsert
        return self.truncate_and_upsert(df, table_config, engine)

    def truncate_and_upsert(
        self,
        df: pd.DataFrame,
        table_config: Dict[str, Any],
        engine
    ) -> bool:
        """
        Truncate table and upsert all data.
        
        Used for schema-compatible full refresh operations.
        
        Args:
            df: DataFrame to load
            table_config: Table configuration dict
            engine: Database engine
            
        Returns:
            True if successful, False otherwise
        """
        table_name = table_config['table']
        schema = table_config['schema']
        
        self.logger.info(f"🔄 Truncate and upsert strategy for {schema}.{table_name}")
        
        try:
            # Truncate table
            with engine.begin() as conn:
                conn.execute(text(f'TRUNCATE "{schema}"."{table_name}"'))
            
            # Upsert all data using DatabaseAdapter
            cleaning_service = DataCleaningService(self.logger)
            clean_df = cleaning_service.clean_for_database(df)
            
            # Use adapter for upsert operations
            adapter = self._get_db_adapter()
            rows_affected = adapter.execute_upsert(
                clean_df, table_name, schema, table_config.get('chunksize', 1000)
            )
            
            self.logger.info(f"✓ {schema}.{table_name}: Replaced table with {rows_affected:,} rows (truncate/upsert).")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to truncate/upsert {schema}.{table_name}: {e}")
            return False
    
    def detect_year_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Detect year column in DataFrame.
        
        Searches for common year column names: 'season', 'year', 'game_year'
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Name of year column if found, None otherwise
        """
        year_candidates = ['season', 'year', 'game_year']
        for col in year_candidates:
            if col in df.columns:
                self.logger.debug(f"Detected year column: {col}")
                return col
        
        self.logger.debug("No year column detected")
        return None
    
    def delete_existing_data(
        self, 
        table: str, 
        schema: str, 
        year_col: str, 
        year: int,
        engine
    ) -> int:
        """
        Delete existing data for incremental loading.
        
        Args:
            table: Table name
            schema: Schema name
            year_col: Year column name
            year: Year value to delete
            engine: Database engine
            
        Returns:
            Number of rows deleted
        """
        delete_sql = text(f'DELETE FROM "{schema}"."{table}" WHERE "{year_col}" = :year_val')
        
        try:
            with engine.connect() as conn:
                result = conn.execute(delete_sql, {'year_val': year})
                conn.commit()
                rows_deleted = result.rowcount
                self.logger.info(f"Deleted {rows_deleted} existing rows from {schema}.{table} for {year_col} = {year}")
                return rows_deleted
        except Exception as e:
            self.logger.error(f"Failed to delete existing data: {e}")
            return 0
    
    


__all__ = ['LoadingStrategyService']
