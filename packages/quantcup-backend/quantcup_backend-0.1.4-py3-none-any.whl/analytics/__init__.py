"""
AnalyticsV2 - Solo Developer Pattern Implementation

Simplified analytics module following the Solo Developer pattern from REFACTORING_SPECS.md.
Eliminates cognitive overhead while maintaining functionality.
"""

from .points_per_drive import generate_points_per_drive_analysis
from .success_rate import generate_success_rate_analysis

__all__ = [
    'generate_points_per_drive_analysis',
    'generate_success_rate_analysis'
]
