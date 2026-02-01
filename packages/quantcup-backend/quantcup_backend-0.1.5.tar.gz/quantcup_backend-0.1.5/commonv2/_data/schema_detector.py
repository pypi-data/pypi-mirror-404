"""
Generic schema detection service for commonv2.

Provides schema change detection and compatibility analysis for any table.
Extracted and generalized from nflfastRv2 for ecosystem-wide use.

Following commonv2 patterns:
- Simple dependency injection
- Module-level logger with DI fallback
- Generic interface (no project-specific dependencies)
- Reusable across quantcup ecosystem
"""

import pandas as pd
from typing import Dict, Any
from sqlalchemy import MetaData, Table

from ..core.logging import get_logger

# Module-level logger with DI fallback
_logger = get_logger('commonv2.schema_detector')


class SchemaDetector:
    """
    Generic schema detection and analysis service.
    
    Analyzes schema changes between incoming DataFrames and existing database tables.
    Provides recommendations for loading strategies based on schema compatibility.
    
    Key Features:
    - Breaking change detection
    - Schema compatibility analysis
    - Loading strategy recommendations
    - Database-agnostic implementation
    
    Example Usage:
        detector = SchemaDetector(logger)
        changes = detector.detect_schema_changes(df, 'teams', 'raw_nflfastr', engine)
        if changes['requires_drop']:
            # Use drop/recreate strategy
        else:
            # Use truncate/upsert strategy
    """
    
    def __init__(self, logger=None):
        """
        Initialize schema detector.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or _logger
    
    def detect_schema_changes(
        self, 
        df: pd.DataFrame, 
        table_name: str, 
        schema: str, 
        engine
    ) -> Dict[str, Any]:
        """
        Compare incoming DataFrame schema with existing table schema.
        
        Args:
            df: Incoming DataFrame
            table_name: Target table name
            schema: Database schema
            engine: Database engine
            
        Returns:
            Dict with schema change analysis:
            {
                'table_exists': bool,
                'requires_drop': bool,
                'breaking_changes': List[str],
                'new_columns': List[str],
                'missing_columns': List[str],
                'type_changes': List[Dict],
                'existing_columns': List[str],
                'incoming_columns': List[str]
            }
        """
        self.logger.debug(f"Analyzing schema changes for {schema}.{table_name}")
        
        try:
            # Try to reflect existing table
            metadata = MetaData()
            existing_table = Table(table_name, metadata,
                                 autoload_with=engine, schema=schema)
            existing_columns = {col.name: str(col.type) for col in existing_table.columns}
            
            self.logger.debug(f"Found existing table {schema}.{table_name} with {len(existing_columns)} columns")
            
        except Exception as e:
            # Table doesn't exist or can't be reflected
            self.logger.debug(f"Could not reflect existing table {schema}.{table_name}: {e}")
            return {
                'table_exists': False,
                'requires_drop': False,
                'breaking_changes': [],
                'new_columns': list(df.columns),
                'missing_columns': [],
                'type_changes': [],
                'existing_columns': [],
                'incoming_columns': list(df.columns)
            }

        # Compare schemas
        incoming_columns = {col: str(df[col].dtype) for col in df.columns}

        new_columns = set(incoming_columns.keys()) - set(existing_columns.keys())
        missing_columns = set(existing_columns.keys()) - set(incoming_columns.keys())

        # Check for type changes in common columns
        type_changes = []
        for col in set(incoming_columns.keys()) & set(existing_columns.keys()):
            if incoming_columns[col] != existing_columns[col]:
                type_changes.append({
                    'column': col,
                    'old_type': existing_columns[col],
                    'new_type': incoming_columns[col]
                })

        # Determine if breaking changes require drop/recreate
        breaking_changes = []
        requires_drop = False

        if missing_columns:
            breaking_changes.append(f"Missing columns: {list(missing_columns)}")
            requires_drop = True

        if len(new_columns) > len(missing_columns):  # Net addition of columns
            breaking_changes.append(f"New columns added: {list(new_columns)}")

        if type_changes:
            type_change_details = []
            for tc in type_changes:
                type_change_details.append(f"{tc['column']}: {tc['old_type']} -> {tc['new_type']}")
            breaking_changes.append(f"Data type changes: {type_change_details}")
            requires_drop = True

        # Major schema overhaul
        if len(missing_columns) > len(existing_columns) * 0.5:  # More than 50% of columns missing
            breaking_changes.append("Major schema overhaul detected")
            requires_drop = True

        result = {
            'table_exists': True,
            'requires_drop': requires_drop,
            'breaking_changes': breaking_changes,
            'new_columns': list(new_columns),
            'missing_columns': list(missing_columns),
            'type_changes': type_changes,
            'existing_columns': list(existing_columns.keys()),
            'incoming_columns': list(incoming_columns.keys())
        }
        
        self.logger.debug(f"Schema analysis complete for {schema}.{table_name}: "
                         f"requires_drop={requires_drop}, "
                         f"breaking_changes={len(breaking_changes)}, "
                         f"new_columns={len(new_columns)}, "
                         f"missing_columns={len(missing_columns)}")
        
        return result


__all__ = ['SchemaDetector']
