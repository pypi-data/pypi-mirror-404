"""
Storage Report Section Generators

Specialized generators for each storage health monitoring section:
- BucketHealthSection: S3/Sevalla bucket connectivity and content analysis
- DatabaseHealthSection: Database accessibility and table validation  
- SyncStatusSection: Storage sync comparison and recommendations

Pattern: Single Responsibility Principle
Each section generator handles one specific aspect of storage monitoring.
"""

from .bucket import BucketHealthSectionGenerator
from .database import DatabaseHealthSectionGenerator
from .sync import SyncStatusSectionGenerator

__all__ = [
    'BucketHealthSectionGenerator',
    'DatabaseHealthSectionGenerator',
    'SyncStatusSectionGenerator'
]
