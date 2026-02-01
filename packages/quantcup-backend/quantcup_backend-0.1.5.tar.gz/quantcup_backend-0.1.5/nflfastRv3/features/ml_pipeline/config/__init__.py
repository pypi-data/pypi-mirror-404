"""
ML Pipeline Configuration Package

Lightweight configuration metadata only - no business logic.
"""

from .training_modes import (
    TRAINING_MODES,
    VALIDATION_CONSTRAINTS,
    MODE_PRIORITY,
    get_mode_info,
    get_all_modes,
    get_validation_constraint
)

__all__ = [
    'TRAINING_MODES',
    'VALIDATION_CONSTRAINTS',
    'MODE_PRIORITY',
    'get_mode_info',
    'get_all_modes',
    'get_validation_constraint'
]