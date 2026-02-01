"""
Unified validation module for commonv2.
Consolidates general validation (from shared/) with domain-specific validation.

Following REFACTORING_SPECS.md: Maximum 5 complexity points, 3 layers depth.
"""

# General validation (from shared/data_validation.py)
from .core import (
    UnifiedDataValidator, 
    DataQualityError,
    validate_dataframe, 
    apply_cleaning, 
    standardize_dtypes_for_postgres
)

# Configuration (from shared/validation_config.py)
from .config import (
    TABLE_SPECIFIC_TYPE_RULES, 
    QUALITY_THRESHOLDS, 
    NFL_SCHEMAS
)

# Export everything for backward compatibility
__all__ = [
    # General validation
    'UnifiedDataValidator', 'DataQualityError',
    'validate_dataframe', 'apply_cleaning', 'standardize_dtypes_for_postgres',
    
    # Configuration
    'TABLE_SPECIFIC_TYPE_RULES', 'QUALITY_THRESHOLDS', 'NFL_SCHEMAS',
]