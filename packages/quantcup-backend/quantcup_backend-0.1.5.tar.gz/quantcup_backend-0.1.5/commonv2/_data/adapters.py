"""
Thin adapters for external dependencies in the data layer.

Following Phase 1 patterns: simple wrappers that isolate external dependencies
and provide clean interfaces with dependency injection.
"""

import pandas as pd
import sqlalchemy as sa
from typing import List, Optional, Dict, Any
from ..core.logging import get_logger
from ..core.errors import DataValidationError
from .sql_queries import (
    GET_TABLES_IN_SCHEMA,
    CHECK_TABLE_EXISTS,
    DROP_TABLE_IF_EXISTS,
    table_exists_params,
    schema_tables_params
)


class DatabaseAdapter:
    """
    Thin adapter for database operations with simple dependency injection.
    
    Isolates database concerns and provides clean interface for testing.
    Follows Phase 1 patterns: simple parameter injection, focused responsibilities.
    """
    
    def __init__(self, engine, logger=None):
        """Simple dependency injection via constructor."""
        self._engine = engine
        self._logger = logger or get_logger('commonv2.data.adapters')
    
    def execute_upsert(self, df: pd.DataFrame, table_name: str, schema: str = "public", 
                      chunk_size: int = 1000) -> int:
        """
        Execute pure database upsert operation - expects clean DataFrame.
        
        This adapter focuses solely on database operations. Data cleaning
        should be handled by the facade layer or DataCleaningService.
        
        Args:
            df: Clean DataFrame ready for database insertion
            table_name: Target table name
            schema: Database schema
            chunk_size: Number of rows per chunk
            
        Returns:
            Number of rows affected
            
        Raises:
            DataValidationError: If table has no unique constraints or other validation issues
        """
        if df.empty:
            self._logger.info(f"No data to upsert into {schema}.{table_name}")
            return 0
        
        # Validate table exists
        if not self.check_table_exists(table_name, schema):
            raise DataValidationError(f"Table {schema}.{table_name} does not exist")
        
        # Get table metadata and constraints
        try:
            metadata = sa.MetaData(schema=schema)
            metadata.reflect(bind=self._engine, only=[table_name])
            table = metadata.tables[f"{schema}.{table_name}"]
        except Exception as e:
            raise DataValidationError(f"Failed to reflect table {schema}.{table_name}: {e}")
        
        # Get primary key or unique constraint columns
        pk_cols = [c.name for c in table.primary_key.columns]
        if not pk_cols:
            # Check for unique constraints as fallback
            unique_cols = []
            for constraint in table.constraints:
                if constraint.__class__.__name__ == 'UniqueConstraint':
                    columns = getattr(constraint, 'columns', None)
                    if columns:
                        unique_cols.extend([c.name for c in columns])
            
            if not unique_cols:
                # Try to auto-create constraints if we have DataFrame columns that match common patterns
                potential_unique_keys = self._detect_potential_unique_keys(df, table_name)
                if potential_unique_keys:
                    self._logger.info(f"🔧 AUTO-CONSTRAINT: Attempting to create unique constraint for {schema}.{table_name}")
                    if self.ensure_table_constraints(table_name, schema, potential_unique_keys):
                        # Re-reflect table to get new constraints
                        metadata = sa.MetaData(schema=schema)
                        metadata.reflect(bind=self._engine, only=[table_name])
                        table = metadata.tables[f"{schema}.{table_name}"]
                        
                        # Get the newly created constraint columns
                        for constraint in table.constraints:
                            if constraint.__class__.__name__ == 'UniqueConstraint':
                                columns = getattr(constraint, 'columns', None)
                                if columns:
                                    pk_cols = [c.name for c in columns]
                                    break
                    else:
                        raise DataValidationError(
                            f"Table {schema}.{table_name} has no PRIMARY KEY or UNIQUE constraints. "
                            "Upsert operations require unique constraints for conflict resolution."
                        )
                else:
                    raise DataValidationError(
                        f"Table {schema}.{table_name} has no PRIMARY KEY or UNIQUE constraints. "
                        "Upsert operations require unique constraints for conflict resolution."
                    )
            else:
                pk_cols = unique_cols
        
        # Validate DataFrame has required columns
        missing_cols = [col for col in pk_cols if col not in df.columns]
        if missing_cols:
            raise DataValidationError(f"DataFrame missing required columns: {missing_cols}")
        
        # Get non-primary key columns for updates
        non_pk = [c for c in df.columns if c not in pk_cols]
        
        self._logger.info(f"Upserting {len(df)} rows into {schema}.{table_name} using conflict keys: {pk_cols}")
        
        # Process in chunks
        total_rows_affected = 0
        
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            rows_affected = self._upsert_chunk(chunk, table, pk_cols, non_pk)
            total_rows_affected += rows_affected
            
            if len(df) > chunk_size:
                chunk_num = i // chunk_size + 1
                total_chunks = (len(df) - 1) // chunk_size + 1
                self._logger.debug(f"Processed chunk {chunk_num}/{total_chunks} ({len(chunk)} rows)")
        
        self._logger.info(f"✓ Upsert complete. {total_rows_affected} rows affected in {schema}.{table_name}")
        return total_rows_affected
    
    def get_table_row_count(self, table_name: str, schema: str = 'public') -> int:
        """Get the current row count for a table."""
        query = sa.text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
        
        with self._engine.connect() as conn:
            result = conn.execute(query).scalar()
            count = result if result is not None else 0
            self._logger.debug(f"Table {schema}.{table_name} has {count:,} rows")
            return count
    
    def get_all_table_row_counts(self, schema: str = 'public', 
                                table_list: Optional[List[str]] = None) -> Dict[str, int]:
        """Get row counts for multiple tables in a schema."""
        counts = {}
        
        # Get table list if not provided
        if table_list is None:
            with self._engine.connect() as conn:
                result = conn.execute(sa.text(GET_TABLES_IN_SCHEMA), schema_tables_params(schema))
                table_list = [row[0] for row in result]
        
        # Get row count for each table
        for table in table_list:
            try:
                counts[table] = self.get_table_row_count(table, schema)
            except Exception as e:
                self._logger.warning(f"Could not get row count for {schema}.{table}: {e}")
                counts[table] = 0
        
        self._logger.info(f"Retrieved row counts for {len(counts)} tables in schema '{schema}'")
        return counts
    
    def check_table_exists(self, table_name: str, schema: str = "public") -> bool:
        """Check if a table exists in the database."""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(sa.text(CHECK_TABLE_EXISTS), table_exists_params(schema, table_name))
                exists = result.scalar()
                exists_bool = bool(exists) if exists is not None else False
                self._logger.debug(f"Table {schema}.{table_name} exists: {exists_bool}")
                return exists_bool
        except Exception as e:
            self._logger.error(f"Failed to check if table exists {schema}.{table_name}: {e}")
            return False
    
    def drop_table(self, table_name: str, schema: str):
        """Drop a table if it exists using nflfastR proven pattern."""
        try:
            self._logger.info(f"Dropping table '{schema}.{table_name}'...")
            
            # Use nflfastR proven pattern: automatic transaction management with engine.begin()
            with self._engine.begin() as conn:
                conn.execute(sa.text(f'DROP TABLE IF EXISTS "{schema}"."{table_name}"'))
            
            self._logger.info(f"Successfully dropped table '{schema}.{table_name}'")
        except Exception as e:
            self._logger.warning(f"Could not drop table '{schema}.{table_name}': {e}")
            # Connection automatically rolled back by engine.begin() context manager
    
    def _upsert_chunk(self, chunk: pd.DataFrame, table: sa.Table, 
                     pk_cols: List[str], non_pk_cols: List[str]) -> int:
        """Upsert a single chunk of data."""
        try:
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            
            # Prepare data
            payload = chunk.to_dict(orient="records")
            
            # Create upsert statement
            insert_stmt = pg_insert(table).values(payload)
            update_stmt = {col: insert_stmt.excluded[col] for col in non_pk_cols}
            
            on_conflict_stmt = insert_stmt.on_conflict_do_update(
                index_elements=pk_cols,
                set_=update_stmt
            )
            
            # Execute
            with self._engine.begin() as conn:
                result = conn.execute(on_conflict_stmt)
                return result.rowcount
                
        except Exception as e:
            self._logger.error(f"Failed to upsert chunk: {e}")
            raise DataValidationError(f"Upsert operation failed: {e}")
    
    def ensure_table_constraints(self, table_name: str, schema: str, unique_keys: List[str]) -> bool:
        """
        Dynamically ensure table has required constraints for upsert operations.
        
        Args:
            table_name: Target table name
            schema: Database schema
            unique_keys: List of columns that should form unique constraint
            
        Returns:
            True if constraints exist or were created successfully
        """
        if not unique_keys:
            self._logger.debug(f"No unique keys specified for {schema}.{table_name}")
            return False
        
        try:
            # Check if table exists first
            if not self.check_table_exists(table_name, schema):
                self._logger.debug(f"Table {schema}.{table_name} doesn't exist yet")
                return False
            
            # Check if constraints already exist
            metadata = sa.MetaData(schema=schema)
            metadata.reflect(bind=self._engine, only=[table_name])
            table = metadata.tables[f"{schema}.{table_name}"]
            
            # Check primary key
            pk_cols = [c.name for c in table.primary_key.columns]
            if pk_cols:
                self._logger.debug(f"✓ Table {schema}.{table_name} already has PRIMARY KEY: {pk_cols}")
                return True
            
            # Check unique constraints
            for constraint in table.constraints:
                if constraint.__class__.__name__ == 'UniqueConstraint':
                    columns = getattr(constraint, 'columns', None)
                    if columns:
                        existing_cols = [c.name for c in columns]
                        if set(existing_cols) == set(unique_keys):
                            self._logger.debug(f"✓ Table {schema}.{table_name} already has matching UNIQUE constraint: {existing_cols}")
                            return True
            
            # Create unique constraint
            constraint_name = f"uk_{table_name}"
            columns_str = ", ".join(f'"{col}"' for col in unique_keys)
            
            create_constraint_sql = sa.text(
                f'ALTER TABLE "{schema}"."{table_name}" '
                f'ADD CONSTRAINT "{constraint_name}" UNIQUE ({columns_str})'
            )
            
            with self._engine.begin() as conn:
                conn.execute(create_constraint_sql)
            
            self._logger.info(f"✓ Created unique constraint {constraint_name} on {schema}.{table_name} ({unique_keys})")
            return True
            
        except Exception as e:
            self._logger.warning(f"Failed to ensure constraints for {schema}.{table_name}: {e}")
            return False
    
    def _detect_potential_unique_keys(self, df: pd.DataFrame, table_name: str) -> List[str]:
        """
        Detect potential unique key columns based on table name and data patterns.
        
        Args:
            df: DataFrame to analyze
            table_name: Table name for pattern matching
            
        Returns:
            List of column names that could form a unique constraint
        """
        # Known unique key patterns for NFL tables
        table_patterns = {
            'play_by_play': ['game_id', 'play_id'],
            'wkly_rosters': ['season', 'week', 'team', 'gsis_id'],
            'nextgen': ['player_gsis_id', 'season', 'week'],
            'snap_counts': ['pfr_game_id', 'pfr_player_id'],
            'pfr_adv_stats': ['pfr_game_id', 'pfr_player_id'],
            'officials': ['game_id', 'official_id'],
            'player_stats': ['player_id', 'season', 'week'],
            'participation': ['nflverse_game_id', 'play_id', 'gsis_id'],
            'espn_qbr_season': ['player_id', 'season', 'season_type'],
            'espn_qbr_wk': ['player_id', 'season', 'game_week', 'season_type'],
            'ftn_chart': ['nflverse_game_id', 'nflverse_play_id']
        }
        
        # Check if we have a known pattern for this table
        if table_name in table_patterns:
            potential_keys = table_patterns[table_name]
            # Verify all columns exist in DataFrame
            if all(col in df.columns for col in potential_keys):
                self._logger.debug(f"Found known unique key pattern for {table_name}: {potential_keys}")
                return potential_keys
        
        # Fallback: look for common ID patterns
        id_columns = [col for col in df.columns if col.endswith('_id') or col == 'id']
        if id_columns:
            self._logger.debug(f"Found potential ID columns for {table_name}: {id_columns}")
            return id_columns[:2]  # Use first 2 ID columns as composite key
        
        self._logger.debug(f"No potential unique keys detected for {table_name}")
        return []


class DataCleaningService:
    """
    Domain service for data cleaning with no external dependencies.
    
    Pure business logic for data transformation and validation.
    """
    
    def __init__(self, logger=None):
        """Simple dependency injection via constructor."""
        self._logger = logger or get_logger('commonv2.data.adapters')
    
    def clean_for_database(self, df: pd.DataFrame, column_types: Optional[Dict[str, List[str]]] = None,
                          datetime_policy: str = 'convert_to_none', table_name: Optional[str] = None) -> pd.DataFrame:
        """
        Clean DataFrame for database insertion.
        
        Focused cleaning operation with configurable policies.
        
        Args:
            df: DataFrame to clean
            column_types: Dict mapping type names to column lists
            datetime_policy: How to handle datetime columns
            table_name: Optional table name for table-specific rules
            
        Returns:
            Cleaned DataFrame ready for database insertion
        """
        if df.empty:
            return df
        
        self._logger.debug(f"Cleaning DataFrame with {len(df)} rows, {len(df.columns)} columns")
        
        df_clean = df.copy()
        column_types = column_types or {}
        
        # Auto-detect datetime columns by name patterns
        datetime_columns = column_types.get('datetime', [])
        auto_detected_datetime = self._auto_detect_datetime_columns(df_clean)
        datetime_columns.extend(auto_detected_datetime)
        
        # Handle datetime columns (including auto-detected ones)
        if datetime_columns:
            df_clean = self._handle_datetime_columns(df_clean, datetime_columns, datetime_policy)
        
        # Handle odds columns with validation
        odds_columns = column_types.get('odds', [])
        if odds_columns:
            df_clean = self._coerce_american_odds(df_clean, odds_columns)
        
        self._logger.info(f"DataFrame cleaning complete: {len(df_clean)} rows, {len(df_clean.columns)} columns")
        return df_clean

    def _handle_datetime_columns(self, df: pd.DataFrame, datetime_columns: List[str],
                                policy: str) -> pd.DataFrame:
        """Handle datetime columns with configurable policies."""
        for col in datetime_columns:
            if col in df.columns:
                original_dtype = str(df[col].dtype)
                nat_count_before = df[col].isna().sum()
                
                # Convert to datetime with optimized format detection
                df[col] = self._convert_to_datetime_optimized(df[col])
                nat_count_after = df[col].isna().sum()
                
                if policy == 'convert_to_none':
                    # Cast to object dtype so it can hold None
                    df[col] = df[col].astype('object')
                    # Replace NaT with None for PostgreSQL compatibility
                    df[col] = df[col].where(df[col].notna(), None)
                    
                    if nat_count_after > 0:
                        self._logger.info(f"🔧 DATETIME_CLEANING: {col} - Converted {nat_count_after} NaT values to None (PostgreSQL NULL)")
                    
                    if original_dtype != 'datetime64[ns]':
                        self._logger.debug(f"Converted {col}: {original_dtype} → datetime64[ns] → object (with None)")
                    else:
                        self._logger.debug(f"Converted {col} datetime NaT values to None")
                        
                elif policy == 'raise_on_nat':
                    if df[col].isna().any():
                        raise ValueError(f"Column {col} contains {nat_count_after} NaT values")
                # For 'keep_nat', do nothing - leave as datetime with NaT
        
        return df
    
    def _convert_to_datetime_optimized(self, series: pd.Series) -> pd.Series:
        """
        Convert series to datetime using format-specific parsing for better performance.
        
        Args:
            series: Pandas series to convert
            
        Returns:
            Series converted to datetime
        """
        if series.empty or series.isna().all():
            return pd.to_datetime(series, errors='coerce')
        
        # Get sample of non-null values for format detection
        sample_values = series.dropna().head(10)
        if len(sample_values) == 0:
            return pd.to_datetime(series, errors='coerce')
        
        # Common datetime formats in NFL data
        common_formats = [
            '%Y-%m-%d',           # 2024-10-25
            '%Y-%m-%d %H:%M:%S',  # 2024-10-25 14:01:02
            '%m/%d/%Y',           # 10/25/2024
            '%Y-%m-%dT%H:%M:%S',  # 2024-10-25T14:01:02
            '%Y-%m-%d %H:%M:%S.%f', # 2024-10-25 14:01:02.123456
            '%Y-%m-%dT%H:%M:%S.%f', # 2024-10-25T14:01:02.123456
            '%Y-%m-%dT%H:%M:%S%z'   # 2024-10-25T14:01:02-04:00
        ]
        
        # Try format-specific parsing first
        for fmt in common_formats:
            try:
                parsed_sample = pd.to_datetime(sample_values, format=fmt, errors='coerce')
                success_rate = parsed_sample.notna().sum() / len(sample_values)
                if success_rate >= 0.8:  # 80% success rate
                    # Apply this format to the entire series
                    return pd.to_datetime(series, format=fmt, errors='coerce')
            except (ValueError, TypeError):
                continue
        
        # Fallback with warning suppression to eliminate pandas UserWarning
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return pd.to_datetime(series, errors='coerce')
    
    def _auto_detect_datetime_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Auto-detect datetime columns by name patterns and data types.
        
        FIXED: Much more restrictive detection to prevent false positives
        that were causing massive performance issues with NFL data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            List of column names that appear to be datetime columns
        """
        datetime_columns = []
        
        # RESTRICTIVE: Only very specific datetime column name patterns
        datetime_patterns = [
            'birth_date', 'game_date', 'created_at', 'updated_at', 'date_pulled',
            'start_time', 'end_time', 'time_of_day', 'end_clock_time',
            'drive_real_start_time', 'trade_date'
        ]
        
        # EXPANDED: Exclude NFL numeric columns that were incorrectly detected as datetime
        numeric_exclusions = [
            # Time-related but numeric
            'avg_time_to_throw', 'time_to_throw', 'avg_time', 'time_remaining',
            'seconds_remaining', 'minutes_remaining', 'timeout', 'timeouts',
            'times_blitzed', 'times_hurried', 'times_hit',
            
            # NFL-specific numeric columns that contain misleading keywords
            'drive', 'time', 'ydsnet', 'qb_dropback', 'kick_distance',
            'posteam_score', 'defteam_score', 'score_differential',
            'posteam_score_post', 'defteam_score_post', 'score_differential_post',
            'air_epa', 'yac_epa', 'comp_air_epa', 'comp_yac_epa', 'def_wp',
            'vegas_wpa', 'vegas_home_wpa', 'home_wp_post', 'away_wp_post', 'vegas_wp',
            'air_wpa', 'yac_wpa', 'comp_air_wpa', 'comp_yac_wpa',
            
            # Boolean/binary NFL columns
            'punt_blocked', 'first_down_rush', 'first_down_pass', 'first_down_penalty',
            'third_down_converted', 'third_down_failed', 'fourth_down_converted',
            'fourth_down_failed', 'incomplete_pass', 'interception', 'punt_inside_twenty',
            'punt_in_endzone', 'punt_out_of_bounds', 'punt_downed', 'punt_fair_catch',
            'kickoff_inside_twenty', 'kickoff_in_endzone', 'kickoff_out_of_bounds',
            'kickoff_downed', 'kickoff_fair_catch', 'fumble_forced', 'fumble_not_forced',
            'fumble_out_of_bounds', 'solo_tackle', 'safety', 'penalty', 'tackled_for_loss',
            'fumble_lost', 'own_kickoff_recovery', 'own_kickoff_recovery_td', 'qb_hit',
            'rush_attempt', 'pass_attempt', 'sack', 'touchdown', 'pass_touchdown',
            'rush_touchdown', 'return_touchdown', 'extra_point_attempt', 'two_point_attempt',
            'field_goal_attempt', 'kickoff_attempt', 'punt_attempt', 'fumble', 'complete_pass',
            'assist_tackle', 'lateral_reception', 'lateral_rush', 'lateral_return',
            'lateral_recovery', 'tackle_with_assist', 'defensive_two_point_attempt',
            'defensive_two_point_conv', 'defensive_extra_point_attempt', 'defensive_extra_point_conv',
            'success', 'first_down', 'qb_epa', 'xyac_epa', 'xyac_mean_yardage', 'xyac_success',
            'xyac_fd', 'xpass', 'pass_oe',
            
            # Numeric yard/distance columns
            'lateral_receiving_yards', 'lateral_rushing_yards', 'fumble_recovery_1_yards',
            'fumble_recovery_2_yards', 'return_yards', 'penalty_yards',
            
            # Drive statistics (numeric)
            'drive_play_count', 'drive_time_of_possession', 'drive_first_downs',
            'drive_inside20', 'drive_ended_with_score', 'drive_quarter_start',
            'drive_quarter_end', 'drive_yards_penalized', 'drive_game_clock_start',
            'drive_game_clock_end', 'drive_play_id_started', 'drive_play_id_ended',
            
            # Completion probability metrics
            'cp', 'cpoe'
        ]
        
        for col in df.columns:
            col_lower = col.lower()
            
            # FIRST: Skip columns that are explicitly known to be numeric (NFL-specific)
            if col in numeric_exclusions or col_lower in [exc.lower() for exc in numeric_exclusions]:
                self._logger.debug(f"Skipping known numeric column: {col}")
                continue
            
            # SECOND: Skip if column is already numeric (float/int) - these shouldn't be datetime
            if pd.api.types.is_numeric_dtype(df[col]):
                self._logger.debug(f"Skipping numeric column: {col}")
                continue
            
            # THIRD: Only detect columns with EXACT datetime name matches (whitelist approach)
            if col in datetime_patterns or col_lower in [pat.lower() for pat in datetime_patterns]:
                datetime_columns.append(col)
                self._logger.debug(f"Auto-detected datetime column by exact name match: {col}")
                continue
            
            # FOURTH: Check if column is already datetime type
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                datetime_columns.append(col)
                self._logger.debug(f"Auto-detected datetime column by dtype: {col}")
                continue
            
            # REMOVED: Content-based datetime detection for object columns
            # This was causing false positives where numeric data was being detected as datetime
            # Only rely on explicit name patterns and existing datetime dtypes
            pass
        
        if datetime_columns:
            self._logger.info(f"Auto-detected {len(datetime_columns)} datetime columns: {datetime_columns}")
        
        return datetime_columns
    
    def _coerce_american_odds(self, df: pd.DataFrame, odds_columns: List[str]) -> pd.DataFrame:
        """Validate and convert American odds columns to nullable Int64."""
        for col in odds_columns:
            if col in df.columns:
                # Skip type check if column is all-NaN
                if df[col].notna().any():
                    # Check if any non-null value has decimals (indicates decimal odds)
                    bad_vals = df[col].dropna().mod(1).ne(0).any()
                    if bad_vals:
                        raise ValueError(f"{col} contains non-integer odds (looks like decimal odds).")
                
                # Cast to nullable integer so NaNs don't up-cast the whole column
                try:
                    df[col] = df[col].round().astype("Int64")
                    self._logger.debug(f"Converted {col} to nullable Int64")
                except (ValueError, TypeError):
                    # Handle edge case where all values are NaN
                    df[col] = df[col].astype("Int64")
        
        return df

