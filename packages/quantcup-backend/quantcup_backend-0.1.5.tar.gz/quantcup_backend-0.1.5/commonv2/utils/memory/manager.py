"""
Memory Manager for Proactive Memory Management

Prevents OOM kills by checking memory availability BEFORE loading data.
Designed for production environments with limited resources.

Pattern: Utility Class with DI (2 complexity points)
"""

import os
import psutil
from typing import Optional, Dict, Any
from ...core.logging import get_logger
from .estimator import ParquetMemoryEstimator

# Module-level logger
_logger = get_logger('commonv2.utils.memory.manager')


class MemoryManager:
    """
    Proactive memory manager for large dataset processing.
    
    Prevents OOM kills by:
    1. Tracking current memory usage
    2. Estimating memory requirements before loading
    3. Recommending chunked processing when needed
    
    Pattern: Utility Class with DI (2 complexity points)
    - DI with fallback (1 point)
    - Business logic (1 point)
    
    Example:
        >>> memory = MemoryManager(max_memory_mb=1536)  # 75% of 2GB
        >>> estimated_mb = memory.estimate_parquet_memory(file_size_bytes)
        >>> if memory.can_load(estimated_mb):
        ...     df = load_full_partition()
        ... else:
        ...     df = load_chunked_partition()
    """
    
    def __init__(
        self,
        max_memory_mb: int = 1536,
        safety_margin_pct: float = 0.1,
        logger=None
    ):
        """
        Initialize memory manager with limits.
        
        Args:
            max_memory_mb: Maximum memory to use in MB (default: 1536 = 75% of 2GB)
            safety_margin_pct: Safety margin as percentage (default: 0.1 = 10%)
            logger: Optional logger instance (uses module logger if not provided)
        """
        self.max_memory_mb = max_memory_mb
        self.safety_margin_pct = safety_margin_pct
        self.logger = logger or _logger
        self.estimator = ParquetMemoryEstimator(logger=self.logger)
        
        # Log initialization
        self.logger.info(
            f"MemoryManager initialized: max={max_memory_mb}MB, "
            f"safety_margin={safety_margin_pct*100:.0f}%"
        )
        
        # Validate system has enough memory
        self._validate_system_memory()
    
    def _validate_system_memory(self):
        """Validate system has enough memory for configured limit."""
        try:
            system_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
            
            if self.max_memory_mb > system_memory_mb:
                self.logger.warning(
                    f"⚠️ Configured max_memory_mb ({self.max_memory_mb}MB) exceeds "
                    f"system memory ({system_memory_mb:.0f}MB). "
                    f"Adjusting to 75% of system memory."
                )
                self.max_memory_mb = int(system_memory_mb * 0.75)
            
            self.logger.debug(
                f"System memory: {system_memory_mb:.0f}MB, "
                f"Configured limit: {self.max_memory_mb}MB "
                f"({(self.max_memory_mb/system_memory_mb)*100:.0f}%)"
            )
        except Exception as e:
            self.logger.warning(f"Could not validate system memory: {e}")
    
    def get_current_usage_mb(self) -> float:
        """
        Get current process memory usage in MB.
        
        Returns:
            Current memory usage in MB
        """
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            usage_mb = memory_info.rss / (1024 * 1024)
            return usage_mb
        except Exception as e:
            self.logger.warning(f"Could not get memory usage: {e}")
            return 0.0
    
    def get_available_mb(self) -> float:
        """
        Get available memory for new operations in MB.
        
        Returns:
            Available memory in MB (max_memory - current_usage - safety_margin)
        """
        current_mb = self.get_current_usage_mb()
        safety_mb = self.max_memory_mb * self.safety_margin_pct
        available_mb = self.max_memory_mb - current_mb - safety_mb
        
        return max(0.0, available_mb)
    
    def can_load(self, estimated_mb: float) -> bool:
        """
        Check if we can safely load data of estimated size.
        
        Args:
            estimated_mb: Estimated memory requirement in MB
            
        Returns:
            True if we can safely load, False if chunking needed
        """
        available_mb = self.get_available_mb()
        can_load = estimated_mb <= available_mb
        
        if can_load:
            self.logger.debug(
                f"✓ Can load {estimated_mb:.1f}MB "
                f"(available: {available_mb:.1f}MB)"
            )
        else:
            self.logger.warning(
                f"⚠️ Cannot load {estimated_mb:.1f}MB "
                f"(available: {available_mb:.1f}MB) - chunking recommended"
            )
        
        return can_load
    
    def estimate_parquet_memory(
        self,
        file_size_bytes: int,
        expansion_factor: Optional[float] = None
    ) -> float:
        """
        Estimate memory required for Parquet file.
        
        Args:
            file_size_bytes: Size of Parquet file on disk in bytes
            expansion_factor: Custom expansion factor (default: 3.0)
            
        Returns:
            Estimated memory in MB
        """
        return self.estimator.estimate_parquet_memory(
            file_size_bytes,
            expansion_factor=expansion_factor
        )
    
    def estimate_with_column_pruning(
        self,
        file_size_bytes: int,
        total_columns: int,
        selected_columns: int
    ) -> float:
        """
        Estimate memory with column pruning.
        
        Args:
            file_size_bytes: Size of Parquet file on disk in bytes
            total_columns: Total number of columns in file
            selected_columns: Number of columns to read
            
        Returns:
            Estimated memory in MB with column pruning
        """
        return self.estimator.estimate_with_column_pruning(
            file_size_bytes,
            total_columns,
            selected_columns
        )
    
    def calculate_optimal_chunk_size(
        self,
        file_size_bytes: int,
        total_rows: int,
        target_memory_mb: Optional[float] = None
    ) -> int:
        """
        Calculate optimal chunk size for processing.
        
        Args:
            file_size_bytes: Size of Parquet file on disk in bytes
            total_rows: Total number of rows in file
            target_memory_mb: Target memory per chunk (default: 50% of available)
            
        Returns:
            Optimal number of rows per chunk
        """
        if total_rows <= 0:
            return 0
        
        # Use 50% of available memory as target if not specified
        if target_memory_mb is None:
            target_memory_mb = self.get_available_mb() * 0.5
        
        # Estimate full file memory
        full_memory_mb = self.estimate_parquet_memory(file_size_bytes)
        
        # Calculate chunk ratio
        chunk_ratio = target_memory_mb / full_memory_mb if full_memory_mb > 0 else 1.0
        chunk_ratio = min(1.0, max(0.01, chunk_ratio))  # Clamp between 1% and 100%
        
        # Calculate chunk size
        chunk_size = int(total_rows * chunk_ratio)
        chunk_size = max(1000, chunk_size)  # Minimum 1000 rows per chunk
        
        self.logger.info(
            f"📊 Optimal chunk size: {chunk_size:,} rows "
            f"({chunk_ratio*100:.1f}% of {total_rows:,} total rows) "
            f"for {target_memory_mb:.1f}MB target"
        )
        
        return chunk_size
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get memory manager status for debugging.
        
        Returns:
            Dict with status information
        """
        current_mb = self.get_current_usage_mb()
        available_mb = self.get_available_mb()
        
        try:
            system_memory = psutil.virtual_memory()
            system_total_mb = system_memory.total / (1024 * 1024)
            system_available_mb = system_memory.available / (1024 * 1024)
            system_percent = system_memory.percent
        except Exception:
            system_total_mb = 0
            system_available_mb = 0
            system_percent = 0
        
        return {
            'max_memory_mb': self.max_memory_mb,
            'current_usage_mb': round(current_mb, 1),
            'available_mb': round(available_mb, 1),
            'safety_margin_pct': self.safety_margin_pct,
            'usage_percent': round((current_mb / self.max_memory_mb) * 100, 1) if self.max_memory_mb > 0 else 0,
            'system_total_mb': round(system_total_mb, 1),
            'system_available_mb': round(system_available_mb, 1),
            'system_usage_percent': round(system_percent, 1)
        }
    
    def log_status(self):
        """Log current memory status."""
        status = self.get_status()
        self.logger.info(
            f"💾 Memory Status: "
            f"{status['current_usage_mb']:.1f}MB / {status['max_memory_mb']}MB "
            f"({status['usage_percent']:.1f}% used), "
            f"{status['available_mb']:.1f}MB available"
        )


def create_memory_manager(
    max_memory_mb: int = 1536,
    safety_margin_pct: float = 0.1,
    logger=None
) -> MemoryManager:
    """
    Factory function to create memory manager.
    
    Args:
        max_memory_mb: Maximum memory to use in MB (default: 1536 = 75% of 2GB)
        safety_margin_pct: Safety margin as percentage (default: 0.1 = 10%)
        logger: Optional logger instance
        
    Returns:
        MemoryManager instance
    """
    return MemoryManager(
        max_memory_mb=max_memory_mb,
        safety_margin_pct=safety_margin_pct,
        logger=logger
    )


__all__ = ['MemoryManager', 'create_memory_manager']