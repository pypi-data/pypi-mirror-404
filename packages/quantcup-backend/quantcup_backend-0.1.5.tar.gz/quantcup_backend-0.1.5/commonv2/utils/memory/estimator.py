"""
Parquet Memory Estimator

Estimates memory requirements for loading Parquet files based on file size
and compression characteristics.

Pattern: Utility Class (1 complexity point)
"""

from typing import Optional
from ...core.logging import get_logger

# Module-level logger
_logger = get_logger('commonv2.utils.memory.estimator')


class ParquetMemoryEstimator:
    """
    Estimates memory requirements for Parquet file operations.
    
    Parquet files are compressed on disk but expand in memory when loaded.
    This class provides conservative estimates to prevent OOM errors.
    
    Pattern: Utility Class (1 complexity point)
    """
    
    # Conservative expansion factors based on typical compression ratios
    DEFAULT_EXPANSION_FACTOR = 3.0  # Parquet typically compresses 3:1
    CONSERVATIVE_EXPANSION_FACTOR = 4.0  # Extra safety margin
    
    def __init__(self, logger=None):
        """
        Initialize estimator with optional logger.
        
        Args:
            logger: Optional logger instance (uses module logger if not provided)
        """
        self.logger = logger or _logger
    
    def estimate_parquet_memory(
        self, 
        file_size_bytes: int,
        expansion_factor: Optional[float] = None,
        include_overhead: bool = True
    ) -> float:
        """
        Estimate memory required to load a Parquet file.
        
        Args:
            file_size_bytes: Size of Parquet file on disk in bytes
            expansion_factor: Custom expansion factor (default: 3.0)
            include_overhead: Include pandas/pyarrow overhead (default: True)
            
        Returns:
            Estimated memory in MB
            
        Example:
            >>> estimator = ParquetMemoryEstimator()
            >>> file_size = 100 * 1024 * 1024  # 100MB file
            >>> estimated_mb = estimator.estimate_parquet_memory(file_size)
            >>> print(f"Estimated memory: {estimated_mb:.1f}MB")
            Estimated memory: 330.0MB
        """
        if file_size_bytes <= 0:
            return 0.0
        
        # Use provided factor or default
        factor = expansion_factor or self.DEFAULT_EXPANSION_FACTOR
        
        # Convert bytes to MB
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Apply expansion factor
        estimated_mb = file_size_mb * factor
        
        # Add overhead for pandas/pyarrow operations (10%)
        if include_overhead:
            estimated_mb *= 1.1
        
        self.logger.debug(
            f"Parquet memory estimate: {file_size_mb:.1f}MB file → "
            f"{estimated_mb:.1f}MB in memory (factor: {factor}x)"
        )
        
        return estimated_mb
    
    def estimate_with_column_pruning(
        self,
        file_size_bytes: int,
        total_columns: int,
        selected_columns: int,
        expansion_factor: Optional[float] = None
    ) -> float:
        """
        Estimate memory with column pruning optimization.
        
        When reading only a subset of columns from Parquet, memory usage
        is proportionally reduced.
        
        Args:
            file_size_bytes: Size of Parquet file on disk in bytes
            total_columns: Total number of columns in file
            selected_columns: Number of columns to read
            expansion_factor: Custom expansion factor (default: 3.0)
            
        Returns:
            Estimated memory in MB with column pruning
            
        Example:
            >>> estimator = ParquetMemoryEstimator()
            >>> # Reading 10 out of 100 columns
            >>> estimated_mb = estimator.estimate_with_column_pruning(
            ...     file_size_bytes=100 * 1024 * 1024,
            ...     total_columns=100,
            ...     selected_columns=10
            ... )
        """
        if total_columns <= 0 or selected_columns <= 0:
            return 0.0
        
        # Calculate base estimate
        base_estimate = self.estimate_parquet_memory(
            file_size_bytes,
            expansion_factor=expansion_factor,
            include_overhead=False
        )
        
        # Apply column pruning ratio
        column_ratio = selected_columns / total_columns
        pruned_estimate = base_estimate * column_ratio
        
        # Add overhead
        pruned_estimate *= 1.1
        
        self.logger.debug(
            f"Column pruning: {selected_columns}/{total_columns} columns → "
            f"{pruned_estimate:.1f}MB (vs {base_estimate * 1.1:.1f}MB full)"
        )
        
        return pruned_estimate
    
    def estimate_chunked_memory(
        self,
        file_size_bytes: int,
        chunk_size_rows: int,
        total_rows: int,
        expansion_factor: Optional[float] = None
    ) -> float:
        """
        Estimate memory for chunked processing.
        
        Args:
            file_size_bytes: Size of Parquet file on disk in bytes
            chunk_size_rows: Number of rows per chunk
            total_rows: Total number of rows in file
            expansion_factor: Custom expansion factor (default: 3.0)
            
        Returns:
            Estimated memory per chunk in MB
        """
        if total_rows <= 0 or chunk_size_rows <= 0:
            return 0.0
        
        # Calculate base estimate
        base_estimate = self.estimate_parquet_memory(
            file_size_bytes,
            expansion_factor=expansion_factor,
            include_overhead=False
        )
        
        # Apply chunk ratio
        chunk_ratio = chunk_size_rows / total_rows
        chunk_estimate = base_estimate * chunk_ratio
        
        # Add overhead
        chunk_estimate *= 1.1
        
        self.logger.debug(
            f"Chunked processing: {chunk_size_rows:,}/{total_rows:,} rows → "
            f"{chunk_estimate:.1f}MB per chunk"
        )
        
        return chunk_estimate


def estimate_parquet_memory(file_size_bytes: int, logger=None) -> float:
    """
    Convenience function for quick memory estimation.
    
    Args:
        file_size_bytes: Size of Parquet file on disk in bytes
        logger: Optional logger instance
        
    Returns:
        Estimated memory in MB
    """
    estimator = ParquetMemoryEstimator(logger=logger)
    return estimator.estimate_parquet_memory(file_size_bytes)


__all__ = ['ParquetMemoryEstimator', 'estimate_parquet_memory']