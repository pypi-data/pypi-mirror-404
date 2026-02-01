"""
Consolidated Data Validation Module

Single source of truth for all data validation across nflfastRv3 and commonv2.
Following REFACTORING_SPECS.md: 5 complexity points max, 3 layers depth max.

Pattern: Minimum Viable Decoupling (2 complexity points)
Complexity: 5 points total
Depth: 2 layers maximum
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from ...core.logging import get_logger
from .config import TABLE_SPECIFIC_TYPE_RULES, QUALITY_THRESHOLDS


class DataQualityError(Exception):
    """Data quality validation error."""
    pass


class UnifiedDataValidator:
    """
    Consolidated data validator combining functionality from:
    - nflfastRv3/features/data_pipeline/quality_checks.py
    - nflfastRv3/shared/validation.py  
    - commonv2/utils/validation.py
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + business logic)
    Depth: 1 layer (calls utilities directly)
    """
    
    def __init__(self, logger=None):
        """Initialize with dependency injection."""
        self._logger = logger or get_logger('commonv2.utils.validation')
    
    def validate_dataframe(self, df, table_name, min_rows=1, required_columns=None):
        """
        Unified DataFrame validation combining all 3 implementations.
        
        Args:
            df: DataFrame to validate
            table_name: Table name for logging
            min_rows: Minimum required rows
            required_columns: List of required column names
            
        Returns:
            dict: Validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'row_count': len(df) if df is not None else 0
        }
        
        # Basic validations
        if df is None:
            results['valid'] = False
            results['errors'].append(f"{table_name}: DataFrame is None")
            return results
        
        if df.empty:
            results['valid'] = False
            results['errors'].append(f"{table_name}: DataFrame is empty")
            return results
        
        if len(df) < min_rows:
            results['valid'] = False
            results['errors'].append(f"{table_name}: Only {len(df)} rows, minimum {min_rows} required")
            return results
        
        # Required columns validation
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                results['valid'] = False
                results['errors'].append(f"{table_name}: Missing required columns: {missing_columns}")
        
        # Check for duplicate columns
        duplicate_cols = df.columns[df.columns.duplicated()].tolist()
        if duplicate_cols:
            results['warnings'].append(f"{table_name}: Duplicate columns: {duplicate_cols}")
        
        # Check for completely null columns
        null_cols = df.columns[df.isnull().all()].tolist()
        if null_cols:
            results['warnings'].append(f"{table_name}: Completely null columns: {null_cols}")
        
        self._logger.info(f"Validated {table_name}: {len(df):,} rows, {results['valid']}")
        return results
    
    def standardize_dtypes_for_postgres(self, df, table_name=None, type_hints=None):
        """
        Unified PostgreSQL type standardization with shared rules.
        
        Args:
            df: DataFrame to standardize
            table_name: Optional table name for table-specific rules
            type_hints: Optional explicit type mappings
            
        Returns:
            DataFrame with standardized dtypes for PostgreSQL compatibility
        """
        if df.empty:
            return df
        
        self._logger.debug(f"🔧 Standardizing dtypes for PostgreSQL: {table_name or 'unknown'} table")
        
        df_standardized = df.copy()
        
        try:
            # Step 1: Apply generic PostgreSQL mappings
            df_standardized = self._apply_simple_postgres_mappings(df_standardized)
            
            # Step 2: Apply table-specific rules if available
            if table_name and table_name in TABLE_SPECIFIC_TYPE_RULES:
                df_standardized = self._apply_table_specific_rules(df_standardized, table_name)
            
            # Step 3: Apply explicit type hints (highest priority)
            if type_hints:
                df_standardized = self._apply_type_hints(df_standardized, type_hints)
            
            self._logger.debug(f"✓ PostgreSQL dtype standardization complete for {table_name}")
            return df_standardized
            
        except Exception as e:
            self._logger.error(f"Failed to standardize dtypes for {table_name}: {e}")
            raise DataQualityError(f"Dtype standardization failed: {e}")
    
    def apply_cleaning(self, df, table_name, config, logger=None):
        """
        Unified data cleaning and validation.
        
        Args:
            df: DataFrame to clean
            table_name: Table name for specific cleaning
            config: Configuration with cleaning parameters
            logger: Optional logger override
            
        Returns:
            Cleaned and validated DataFrame
        """
        logger = logger or self._logger
        initial_count = len(df)
        
        # Step 1: Basic data cleaning
        # Normalize all null-like values. pandas/Arrow nullable dtypes use <NA>, not np.nan.
        df = df.where(df.notna(), None)
        df = df.replace({np.nan: None})
        df = df.replace(['NA_character_', 'NA', '<NA>', 'nan'], None)
        df = df.replace(-2147483648, None)  # R integer sentinel
        
        # Step 2: Apply PostgreSQL dtype standardization
        df = self.standardize_dtypes_for_postgres(
            df, 
            table_name=table_name, 
            type_hints=config.get('type_hints')
        )
        
        # Step 3: Team standardization if enabled and team columns present
        if config.get('standardize_teams', True):  # Default to True
            team_columns = ['home_team', 'away_team', 'team', 'team_abbr', 'posteam', 'defteam']
            if any(col in df.columns for col in team_columns):
                try:
                    from ...domain.adapters import TeamNameStandardizer
                    standardizer = TeamNameStandardizer()
                    standardized_cols = []
                    for col in team_columns:
                        if col in df.columns:
                            df = standardizer.standardize_dataframe_column(df, col, output_format='abbr')
                            standardized_cols.append(col)
                    if standardized_cols:
                        logger.debug(f"Team standardization applied to {table_name}: {standardized_cols}")
                except ImportError:
                    logger.warning("TeamNameStandardizer not available - skipping team standardization")
                except Exception as e:
                    logger.error(f"Team standardization failed for {table_name}: {e}")
        
        # Step 4: Table-specific cleaning
        if table_name in ['rosters', 'wkly_rosters'] and 'gsis_id' in df.columns:
            df = df.dropna(subset=['gsis_id'])
        elif table_name == 'ff_opportunity':
            required_cols = ['player_id', 'full_name']
            if all(col in df.columns for col in required_cols):
                df = df.dropna(subset=required_cols)
        
        # Step 5: Unique key validation
        unique_keys = config.get('unique_keys', [])
        if unique_keys:
            df = self.validate_unique_key_integrity(df, unique_keys, table_name, logger)
            df = self.validate_unique_key_duplicates(df, unique_keys, table_name, logger)
        
        # Final validation
        if len(df) < 1:
            raise DataQualityError(f"{table_name} has no rows after cleaning and validation")
        
        # Summary logging
        final_count = len(df)
        total_loss = initial_count - final_count
        if total_loss > 0:
            loss_percentage = (total_loss / initial_count) * 100
            logger.info(f"📊 CLEANING: {table_name} - {initial_count:,} → {final_count:,} rows ({loss_percentage:.1f}% loss)")
            if loss_percentage > QUALITY_THRESHOLDS['data_loss_critical']:
                logger.warning(f"⚠️ DATA_LOSS_ALERT: {table_name} lost {loss_percentage:.1f}% of data")
        
        logger.info(f"✓ Data cleaning complete for {table_name}: {len(df):,} rows")
        return df
    
    def validate_required_columns(self, df, columns, context=""):
        """
        Unified required columns validation.
        
        Args:
            df: DataFrame to validate
            columns: List of required column names
            context: Context string for error messages
            
        Returns:
            True if valid, False otherwise
        """
        if df.empty:
            self._logger.warning(f"{context} DataFrame is empty")
            return False
        
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            self._logger.error(f"Missing required columns in {context}: {missing_columns}")
            return False
        
        # Check for null values in critical columns
        for col in columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                self._logger.warning(f"Found {null_count} null values in column '{col}' ({context})")
        
        self._logger.debug(f"Required columns validation passed for {context}: {len(df)} rows")
        return True
    
    def validate_row_count(self, df, expected=None, max_rows=None, context=""):
        """
        Unified row count validation.
        
        Args:
            df: DataFrame to validate
            expected: Expected exact number of rows (optional)
            max_rows: Maximum allowed rows (optional)
            context: Context string for error messages
            
        Returns:
            True if valid, raises exception for max_rows violation
        """
        if df.empty:
            self._logger.warning(f"{context} DataFrame is empty")
            return True
        
        # Check expected count
        if expected is not None and len(df) != expected:
            self._logger.warning(f"Expected {expected} rows in {context}, found {len(df)}")
        
        # Check maximum count (hard limit)
        if max_rows is not None and len(df) > max_rows:
            raise ValueError(f"{context} has {len(df)} rows, maximum allowed is {max_rows}")
        
        self._logger.debug(f"Row count validation passed for {context}: {len(df)} rows")
        return True
    
    def validate_unique_key_integrity(self, df, unique_keys, table_name, logger=None):
        """
        Simple validation for null values in unique key columns.
        
        Args:
            df: DataFrame to validate
            unique_keys: List of unique key column names
            table_name: Table name for logging
            logger: Optional logger instance
            
        Returns:
            DataFrame with null unique keys removed
        """
        logger = logger or self._logger
        
        if not unique_keys:
            return df
        
        # Check for missing columns
        for key in unique_keys:
            if key not in df.columns:
                raise DataQualityError(f"Unique key '{key}' missing from {table_name}")
        
        # Remove rows with null unique keys
        initial_count = len(df)
        df_validated = df.dropna(subset=unique_keys)
        final_count = len(df_validated)
        
        if final_count == 0:
            raise DataQualityError(f"{table_name} has no rows after unique key validation")
        
        # Log results
        rows_lost = initial_count - final_count
        if rows_lost > 0:
            logger.info(f"🔧 UNIQUE KEY: Removed {rows_lost:,} rows with null keys from {table_name}")
        
        return df_validated
    
    def validate_unique_key_duplicates(self, df, unique_keys, table_name, logger=None):
        """
        Simple duplicate validation for unique key combinations.
        
        Args:
            df: DataFrame to validate
            unique_keys: List of unique key column names
            table_name: Table name for logging
            logger: Optional logger instance
            
        Returns:
            DataFrame with duplicates removed
        """
        logger = logger or self._logger
        
        if not unique_keys:
            return df
        
        # Remove duplicates and log
        initial_count = len(df)
        df_validated = df.drop_duplicates(subset=unique_keys, keep='first')
        final_count = len(df_validated)
        removed_count = initial_count - final_count
        
        if removed_count > 0:
            logger.info(f"🔧 DEDUPLICATION: Removed {removed_count:,} duplicate rows from {table_name}")
        else:
            logger.debug(f"✓ No duplicates found in {table_name}")
        
        return df_validated
    
    def _apply_simple_postgres_mappings(self, df):
        """Apply simple PostgreSQL dtype mappings."""
        df_mapped = df.copy()
        
        for col in df_mapped.columns:
            # Integer columns: Convert to nullable Int64 for PostgreSQL BIGINT compatibility
            if df_mapped[col].dtype in ['int64', 'int32', 'int16', 'int8']:
                df_mapped[col] = df_mapped[col].astype('Int64')
            
            # Float columns: Ensure consistent float64 for PostgreSQL DOUBLE PRECISION
            elif df_mapped[col].dtype in ['float32', 'float16']:
                df_mapped[col] = df_mapped[col].astype('float64')
            
            # Boolean columns: Convert to nullable boolean for PostgreSQL BOOLEAN
            elif df_mapped[col].dtype == 'bool':
                df_mapped[col] = df_mapped[col].astype('boolean')
            
            # Category columns: Convert to object for PostgreSQL TEXT
            elif hasattr(df_mapped[col].dtype, 'categories'):
                df_mapped[col] = df_mapped[col].astype('object')
        
        return df_mapped
    
    def _apply_table_specific_rules(self, df, table_name):
        """Apply table-specific type conversion rules."""
        df_processed = df.copy()
        table_rules = TABLE_SPECIFIC_TYPE_RULES[table_name]
        
        for col, target_type in table_rules.items():
            if col in df_processed.columns:
                try:
                    if target_type == 'Int64':
                        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').astype('Int64')
                    elif target_type == 'boolean':
                        df_processed[col] = df_processed[col].astype('boolean')
                    else:
                        df_processed[col] = df_processed[col].astype(target_type)
                except (ValueError, TypeError) as e:
                    self._logger.warning(f"Failed to convert {col} to {target_type}: {e}")
        
        return df_processed
    
    def _apply_type_hints(self, df, type_hints):
        """Apply explicit type hints to DataFrame."""
        df_processed = df.copy()
        
        for col, target_type in type_hints.items():
            if col in df_processed.columns:
                try:
                    if target_type == 'Int64':
                        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').astype('Int64')
                    elif target_type == 'boolean':
                        df_processed[col] = df_processed[col].astype('boolean')
                    else:
                        df_processed[col] = df_processed[col].astype(target_type)
                except (ValueError, TypeError) as e:
                    self._logger.warning(f"Failed to apply type hint {col} → {target_type}: {e}")
        
        return df_processed
    
    def validate_team_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Team-specific validation rules.
        
        Consolidates validation logic from teams.py validate_team_data().
        
        Args:
            df: Team DataFrame to validate
            
        Returns:
            True if valid, False otherwise
        """
        context = "team data"
        
        # Required columns check
        if not self.validate_required_columns(df, ['team_abbr', 'team_name'], context):
            return False
        
        # Expected team count check
        self.validate_row_count(df, expected=32, context=context)
        
        self._logger.info(f"Team validation passed: {len(df)} teams with required columns")
        return True
    
    def validate_schedule_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Schedule-specific validation rules.
        
        Consolidates validation logic from schedules.py validate_schedule_data().
        
        Args:
            df: Schedule DataFrame to validate
            
        Returns:
            True if valid, False otherwise
        """
        context = "schedule data"
        
        # Required columns check
        if not self.validate_required_columns(df, ['home_team', 'away_team'], context):
            return False
        
        self._logger.info(f"Schedule validation passed: {len(df)} games")
        return True


# Convenience functions for backward compatibility
def validate_dataframe(df, table_name, min_rows=1, logger=None):
    """Convenience function maintaining existing API."""
    validator = UnifiedDataValidator(logger)
    return validator.validate_dataframe(df, table_name, min_rows)


def apply_cleaning(df, table_name, config, logger=None):
    """Convenience function maintaining existing API."""
    validator = UnifiedDataValidator(logger)
    return validator.apply_cleaning(df, table_name, config, logger)


def standardize_dtypes_for_postgres(df, table_name=None, type_hints=None, logger=None):
    """Convenience function maintaining existing API."""
    validator = UnifiedDataValidator(logger)
    return validator.standardize_dtypes_for_postgres(df, table_name, type_hints)


# detect_schema_changes removed - use commonv2._data.schema_detector.SchemaDetector instead