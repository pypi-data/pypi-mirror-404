"""
Data Cleaner Component for nflfastRv3 Pipeline

Extracted from implementation.py lines 823-867 (Phase 1 Refactoring)
Handles data cleaning with schema matching and validation.

Pattern: Focused Component (2 complexity points)
Complexity: 2 points (DI + schema detection)
Responsibilities: Schema change detection, data quality checks, schema issue tracking
"""

from typing import Any, Dict, List
import pandas as pd
from commonv2 import apply_cleaning
from commonv2._data.schema_detector import SchemaDetector
from nflfastRv3.features.data_pipeline.config.data_sources import DataSourceConfig


class DataCleaner:
    """Handles data cleaning with schema matching and validation."""
    
    def __init__(self, logger):
        """
        Initialize DataCleaner.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.schema_detector = SchemaDetector(logger)
        self._schema_issues = []
    
    def clean(self, df: pd.DataFrame, config: DataSourceConfig, engine=None) -> pd.DataFrame:
        """
        Clean data using quality checks with enhanced schema matching.
        
        ENHANCED: Phase 1 - Schema change detection integration
        ENHANCED: Phase 4 - Track schema issues for reporting
        
        Args:
            df: Raw DataFrame
            config: Data source configuration
            engine: Optional SQLAlchemy engine for schema matching
            
        Returns:
            Cleaned DataFrame
        """
        # ENHANCED: Detect schema changes before cleaning using real SchemaDetector
        if engine:
            schema_analysis = self.schema_detector.detect_schema_changes(df, config.table, config.schema, engine)
            
            if schema_analysis['requires_drop']:
                self.logger.warning(f"🚨 SCHEMA_DRIFT_DETECTED: {config.table} requires drop/recreate")
                
                if schema_analysis['breaking_changes']:
                    for change in schema_analysis['breaking_changes']:
                        self.logger.warning(f"⚠️ BREAKING_CHANGE: {change}")
                
                if schema_analysis['missing_columns']:
                    self.logger.error(f"❌ CRITICAL: Missing columns will cause failures: {schema_analysis['missing_columns']}")
                
                # PHASE 4: Track schema issue for reporting
                self._track_schema_issue(config.table, schema_analysis)
        
        # Convert config to dict for apply_cleaning with engine for schema matching
        config_dict = {
            'table': config.table,
            'schema': config.schema,
            'numeric_cols': config.numeric_cols,
            'non_numeric_cols': config.non_numeric_cols,
            'unique_keys': config.unique_keys,
            'engine': engine  # Pass engine for schema matching
        }
        
        # Layer 3 call to quality checks with enhanced schema matching
        return apply_cleaning(df, config.table, config_dict, self.logger)
    
    def _track_schema_issue(self, table: str, schema_analysis: Dict[str, Any]):
        """
        Track schema drift issue for reporting.
        
        PHASE 4 ENHANCEMENT: Schema drift tracking
        
        Args:
            table: Table name where schema drift was detected
            schema_analysis: Schema analysis results from SchemaDetector
        """
        # Extract relevant information from schema analysis
        issue = {
            'table': table,
            'requires_drop': schema_analysis.get('requires_drop', False),
            'breaking_changes': schema_analysis.get('breaking_changes', []),
            'missing_columns': schema_analysis.get('missing_columns', []),
            'severity': 'critical' if schema_analysis.get('requires_drop', False) else 'warning',
            'type': 'schema_drift'
        }
        
        # Add descriptive message
        if issue['requires_drop']:
            issue['message'] = f"Table requires drop/recreate due to breaking schema changes"
        elif issue['missing_columns']:
            issue['message'] = f"Missing columns in database: {', '.join(issue['missing_columns'])}"
        elif issue['breaking_changes']:
            issue['message'] = f"Breaking changes detected: {', '.join(issue['breaking_changes'])}"
        else:
            issue['message'] = "Schema drift detected"
        
        self._schema_issues.append(issue)
    
    def get_schema_issues(self) -> List[Dict[str, Any]]:
        """
        Get all schema issues detected during cleaning.
        
        Returns:
            List of dictionaries containing schema issue details
        """
        return self._schema_issues


__all__ = ['DataCleaner']
