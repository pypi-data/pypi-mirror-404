"""
Direct imports from validation submodule.
Clean API without backward compatibility layer.
"""

# Import everything from the validation submodule
from .validation.core import (
    UnifiedDataValidator,
    DataQualityError,
    validate_dataframe,
    apply_cleaning,
    standardize_dtypes_for_postgres
)

from .validation.config import (
    TABLE_SPECIFIC_TYPE_RULES,
    QUALITY_THRESHOLDS,
    NFL_SCHEMAS
)

# Clean API exports
__all__ = [
    # General validation
    'UnifiedDataValidator', 'DataQualityError',
    'validate_dataframe', 'apply_cleaning', 'standardize_dtypes_for_postgres',
    
    # Configuration
    'TABLE_SPECIFIC_TYPE_RULES', 'QUALITY_THRESHOLDS', 'NFL_SCHEMAS'
]
