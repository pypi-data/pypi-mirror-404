"""
Common Metrics Calculations for Data Pipeline Reporting

Shared metric calculation functions used across reporting modules.
"""


def calculate_success_rate(successful: int, total: int) -> float:
    """
    Calculate success rate for operations.
    
    Args:
        successful: Number of successful operations
        total: Total number of operations attempted
        
    Returns:
        float: Success rate (0.0 to 1.0)
        
    Example:
        >>> calculate_success_rate(98, 100)
        0.98
        >>> calculate_success_rate(0, 0)
        0.0
    """
    if total == 0:
        return 0.0
    return successful / total


def calculate_data_loss_percentage(rows_in: int, rows_out: int) -> float:
    """
    Calculate percentage of data lost during processing.
    
    Args:
        rows_in: Number of rows going in
        rows_out: Number of rows coming out
        
    Returns:
        float: Data loss percentage (0.0 to 1.0)
        
    Example:
        >>> calculate_data_loss_percentage(1000, 950)
        0.05  # 5% data loss
        >>> calculate_data_loss_percentage(1000, 1000)
        0.0  # No data loss
    """
    if rows_in == 0:
        return 0.0
    
    loss = rows_in - rows_out
    return max(0.0, loss / rows_in)


def calculate_storage_efficiency(original_size: float, optimized_size: float) -> float:
    """
    Calculate storage efficiency (memory saved through optimization).
    
    Args:
        original_size: Original size in bytes (or any consistent unit)
        optimized_size: Optimized size in bytes (or any consistent unit)
        
    Returns:
        float: Efficiency ratio (0.0 to 1.0), where 0.5 = 50% memory saved
        
    Example:
        >>> calculate_storage_efficiency(1000, 500)
        0.5  # 50% memory saved
        >>> calculate_storage_efficiency(1000, 800)
        0.2  # 20% memory saved
    """
    if original_size == 0:
        return 0.0
    
    savings = original_size - optimized_size
    return max(0.0, savings / original_size)


def calculate_velocity(rows_processed: int, duration_seconds: float) -> float:
    """
    Calculate processing velocity (rows per second).
    
    Args:
        rows_processed: Number of rows processed
        duration_seconds: Duration in seconds
        
    Returns:
        float: Rows per second
        
    Example:
        >>> calculate_velocity(10000, 5.0)
        2000.0  # 2000 rows/sec
        >>> calculate_velocity(0, 5.0)
        0.0
    """
    if duration_seconds <= 0:
        return 0.0
    
    return rows_processed / duration_seconds


def calculate_memory_usage_mb(bytes_value: int) -> float:
    """
    Convert bytes to megabytes for reporting.
    
    Args:
        bytes_value: Size in bytes
        
    Returns:
        float: Size in megabytes
        
    Example:
        >>> calculate_memory_usage_mb(5242880)
        5.0  # 5 MB
        >>> calculate_memory_usage_mb(1048576)
        1.0  # 1 MB
    """
    if bytes_value < 0:
        return 0.0
    
    return bytes_value / (1024 * 1024)


def calculate_average(values: list) -> float:
    """
    Calculate average of a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        float: Average value
        
    Example:
        >>> calculate_average([10, 20, 30])
        20.0
        >>> calculate_average([])
        0.0
    """
    if not values:
        return 0.0
    
    return sum(values) / len(values)


def calculate_total(values: list) -> float:
    """
    Calculate total sum of a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        float: Total sum
        
    Example:
        >>> calculate_total([10, 20, 30])
        60
        >>> calculate_total([])
        0
    """
    return sum(values) if values else 0


def calculate_percentage_of_total(value: float, total: float) -> float:
    """
    Calculate what percentage a value is of a total.
    
    Args:
        value: The value to calculate percentage for
        total: The total value
        
    Returns:
        float: Percentage (0.0 to 1.0)
        
    Example:
        >>> calculate_percentage_of_total(25, 100)
        0.25  # 25%
        >>> calculate_percentage_of_total(50, 200)
        0.25  # 25%
    """
    if total == 0:
        return 0.0
    
    return value / total


__all__ = [
    'calculate_success_rate',
    'calculate_data_loss_percentage',
    'calculate_storage_efficiency',
    'calculate_velocity',
    'calculate_memory_usage_mb',
    'calculate_average',
    'calculate_total',
    'calculate_percentage_of_total',
]
