"""
Memory Management Utilities for Large Dataset Processing

Provides proactive memory management to prevent OOM kills when processing
large datasets. Designed for production environments with limited resources.

Pattern: Reusable Infrastructure (2 complexity points)
- DI with fallback (1 point)
- Business logic (1 point)

Usage:
    from commonv2.utils.memory import MemoryManager
    
    # Initialize with conservative limit (75% of available RAM)
    memory = MemoryManager(max_memory_mb=1536, logger=logger)  # For 2GB instance
    
    # Pre-flight check before loading
    estimated_mb = memory.estimate_parquet_memory(file_size_bytes)
    if memory.can_load(estimated_mb):
        df = load_full_partition()
    else:
        df = load_chunked_partition()
"""

from .manager import MemoryManager
from .estimator import ParquetMemoryEstimator

__all__ = ['MemoryManager', 'ParquetMemoryEstimator']