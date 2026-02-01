"""
Schema Tracker Component

Extracted from warehouse.py (lines 284-436).
Handles schema change detection, comparison, and tracking.

Pattern: Single Responsibility (2 complexity points)
- Base functionality: 1 point  
- Schema comparison logic: 1 point
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class SchemaTracker:
    """
    Tracks schema changes and drift across warehouse builds.
    
    Pattern: Single Responsibility (2 complexity points)
    Complexity: 2 points (base + schema comparison)
    
    Responsibilities:
    - Schema change detection and tracking
    - Severity assessment (critical, warning, info)
    - Schema comparison logic
    - Schema registry management
    """
    
    def __init__(self, logger):
        """
        Initialize schema tracker.
        
        Args:
            logger: Logger instance for tracking messages
        """
        self.logger = logger
        self._schema_changes = []
        self._schema_registry = {}  # Stores current schemas for comparison
    
    def track_change(self, table_name: str, change_type: str, details: Dict):
        """
        Track schema change detected during warehouse build.
        
        Extracted from warehouse.py lines 284-310.
        
        Args:
            table_name: Table where change detected
            change_type: Type of change ('column_added', 'column_removed', 'type_changed',
                        'schema_mismatch', 'schema_drift')
            details: Dict with change specifics
        """
        severity = self.determine_severity(change_type, details)
        
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
    
    def determine_severity(self, change_type: str, details: Dict) -> str:
        """
        Determine severity of schema change.
        
        Extracted from warehouse.py lines 312-355.
        
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
    
    def compare_schemas(self, source_schema: Dict, result_schema: Dict) -> Optional[Dict]:
        """
        Compare two schemas and identify differences.
        
        Extracted from warehouse.py lines 357-405.
        
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
    
    def get_current_schema(self, table_name: str) -> Optional[Dict]:
        """
        Get currently stored schema for a table.
        
        Extracted from warehouse.py lines 407-417.
        
        Args:
            table_name: Name of table
            
        Returns:
            Dict mapping column names to types, or None if not stored
        """
        return self._schema_registry.get(table_name)
    
    def store_schema(self, table_name: str, schema: Dict):
        """
        Store schema for future comparison.
        
        Extracted from warehouse.py lines 419-427.
        
        Args:
            table_name: Name of table
            schema: Dict mapping column names to types
        """
        self._schema_registry[table_name] = schema
    
    def get_schema_changes(self) -> List[Dict]:
        """
        Get all schema changes tracked.
        
        Extracted from warehouse.py lines 429-431.
        
        Returns:
            List of schema change dictionaries
        """
        return self._schema_changes
    
    def clear_tracking(self):
        """
        Clear schema tracking between builds.
        
        Extracted from warehouse.py lines 433-436.
        
        Note: We keep _schema_registry to enable cross-build comparison
        """
        self._schema_changes = []
        # Note: We keep _schema_registry to enable cross-build comparison


__all__ = ['SchemaTracker']
