"""
Data Pipeline Reporting Configuration

Centralized configuration for data pipeline benchmarks, thresholds,
and status indicators used across reporting modules.
"""

from typing import NamedTuple, List, Tuple


# Report output directory
REPORT_OUTPUT_DIR = 'reports/data_pipeline'


# Status indicators (emojis for markdown reports)
STATUS_INDICATORS = {
    'success': '✅',
    'warning': '⚠️',
    'error': '❌',
    'info': 'ℹ️',
    'running': '🔄',
    'stopped': '⏸️',
    'complete': '🎯',
    'partial': '📊',
}


class DataLossThreshold(NamedTuple):
    """Data loss threshold for quality assessment."""
    min_loss: float
    max_loss: float
    rating: str
    emoji: str
    level: str


# Data Loss Thresholds (percentage of rows lost during processing)
DATA_LOSS_THRESHOLDS: List[DataLossThreshold] = [
    DataLossThreshold(
        min_loss=0.0,
        max_loss=0.01,
        rating="Excellent",
        emoji="🟢",
        level="Minimal data loss - high quality pipeline"
    ),
    DataLossThreshold(
        min_loss=0.01,
        max_loss=0.05,
        rating="Good",
        emoji="🟡",
        level="Acceptable data loss - normal cleaning"
    ),
    DataLossThreshold(
        min_loss=0.05,
        max_loss=0.10,
        rating="Fair",
        emoji="🟠",
        level="Moderate data loss - review cleaning rules"
    ),
    DataLossThreshold(
        min_loss=0.10,
        max_loss=1.0,
        rating="Poor",
        emoji="🔴",
        level="High data loss - investigate quality issues"
    ),
]


class StorageEfficiencyThreshold(NamedTuple):
    """Storage efficiency threshold for memory optimization."""
    min_efficiency: float
    max_efficiency: float
    rating: str
    emoji: str
    level: str


# Storage Efficiency Thresholds (memory saved through optimization)
STORAGE_EFFICIENCY_THRESHOLDS: List[StorageEfficiencyThreshold] = [
    StorageEfficiencyThreshold(
        min_efficiency=0.50,
        max_efficiency=1.0,
        rating="Excellent",
        emoji="🟢",
        level="Outstanding memory optimization"
    ),
    StorageEfficiencyThreshold(
        min_efficiency=0.30,
        max_efficiency=0.50,
        rating="Good",
        emoji="🟡",
        level="Solid memory savings achieved"
    ),
    StorageEfficiencyThreshold(
        min_efficiency=0.10,
        max_efficiency=0.30,
        rating="Fair",
        emoji="🟠",
        level="Moderate optimization benefits"
    ),
    StorageEfficiencyThreshold(
        min_efficiency=0.0,
        max_efficiency=0.10,
        rating="Poor",
        emoji="🔴",
        level="Limited optimization impact"
    ),
]


class SuccessRateThreshold(NamedTuple):
    """Success rate threshold for reliability assessment."""
    min_rate: float
    max_rate: float
    rating: str
    emoji: str
    level: str


# Success Rate Thresholds (percentage of successful operations)
SUCCESS_RATE_THRESHOLDS: List[SuccessRateThreshold] = [
    SuccessRateThreshold(
        min_rate=0.99,
        max_rate=1.0,
        rating="Excellent",
        emoji="🟢",
        level="Nearly perfect reliability"
    ),
    SuccessRateThreshold(
        min_rate=0.95,
        max_rate=0.99,
        rating="Good",
        emoji="🟡",
        level="High reliability - minor issues"
    ),
    SuccessRateThreshold(
        min_rate=0.90,
        max_rate=0.95,
        rating="Fair",
        emoji="🟠",
        level="Moderate reliability - review failures"
    ),
    SuccessRateThreshold(
        min_rate=0.0,
        max_rate=0.90,
        rating="Poor",
        emoji="🔴",
        level="Low reliability - investigate systematically"
    ),
]


def get_status_indicator(status: str) -> str:
    """
    Get status indicator emoji for a given status.
    
    Args:
        status: Status string (success, warning, error, etc.)
        
    Returns:
        str: Emoji indicator
        
    Example:
        >>> get_status_indicator('success')
        '✅'
        >>> get_status_indicator('error')
        '❌'
    """
    return STATUS_INDICATORS.get(status.lower(), STATUS_INDICATORS['info'])


def get_data_loss_rating(loss_percentage: float) -> Tuple[str, str, str]:
    """
    Get data loss rating based on percentage of rows lost.
    
    Args:
        loss_percentage: Percentage of data lost (0.0 to 1.0)
        
    Returns:
        Tuple of (rating, emoji, level)
        
    Example:
        >>> rating, emoji, level = get_data_loss_rating(0.03)
        >>> print(f"{emoji} {rating} - {level}")
        🟡 Good - Acceptable data loss - normal cleaning
    """
    for threshold in DATA_LOSS_THRESHOLDS:
        if threshold.min_loss <= loss_percentage < threshold.max_loss:
            return (threshold.rating, threshold.emoji, threshold.level)
    
    # Fallback
    return ("Unknown", "⚪", "Could not determine data loss level")


def get_storage_efficiency_rating(efficiency: float) -> Tuple[str, str, str]:
    """
    Get storage efficiency rating based on memory saved.
    
    Args:
        efficiency: Efficiency ratio (0.0 to 1.0), where 0.5 = 50% memory saved
        
    Returns:
        Tuple of (rating, emoji, level)
        
    Example:
        >>> rating, emoji, level = get_storage_efficiency_rating(0.45)
        >>> print(f"{emoji} {rating} - {level}")
        🟡 Good - Solid memory savings achieved
    """
    for threshold in STORAGE_EFFICIENCY_THRESHOLDS:
        if threshold.min_efficiency <= efficiency < threshold.max_efficiency:
            return (threshold.rating, threshold.emoji, threshold.level)
    
    # Fallback
    return ("Unknown", "⚪", "Could not determine efficiency level")


def get_success_rate_rating(success_rate: float) -> Tuple[str, str, str]:
    """
    Get success rate rating based on percentage of successful operations.
    
    Args:
        success_rate: Success rate (0.0 to 1.0)
        
    Returns:
        Tuple of (rating, emoji, level)
        
    Example:
        >>> rating, emoji, level = get_success_rate_rating(0.98)
        >>> print(f"{emoji} {rating} - {level}")
        🟡 Good - High reliability - minor issues
    """
    for threshold in SUCCESS_RATE_THRESHOLDS:
        if threshold.min_rate <= success_rate < threshold.max_rate:
            return (threshold.rating, threshold.emoji, threshold.level)
    
    # Fallback
    return ("Unknown", "⚪", "Could not determine success rate level")


__all__ = [
    'REPORT_OUTPUT_DIR',
    'STATUS_INDICATORS',
    'DATA_LOSS_THRESHOLDS',
    'STORAGE_EFFICIENCY_THRESHOLDS',
    'SUCCESS_RATE_THRESHOLDS',
    'get_status_indicator',
    'get_data_loss_rating',
    'get_storage_efficiency_rating',
    'get_success_rate_rating',
]
