"""
Common Metrics Calculations

Shared metric calculation functions used across reporting modules.
"""

import numpy as np
from .config import ROI_BREAKEVEN_ACCURACY, ROI_PAYOUT_MULTIPLIER_110


def calculate_roi(accuracy: float, odds: str = "-110") -> float:
    """
    Calculate estimated ROI for betting at given odds.
    
    Formula for -110 odds: ROI = (accuracy * 1.909 - 1)
    Where 1.909 comes from winning $100 on $110 bet (100/110 * 2 + 10/110)
    
    Args:
        accuracy: Win rate (0.0 to 1.0)
        odds: Betting odds format (currently only "-110" supported)
        
    Returns:
        float: Estimated ROI as decimal (e.g., 0.12 = 12% ROI)
        
    Example:
        >>> calculate_roi(0.60)  # 60% accuracy
        0.09  # 9% ROI
        
        >>> calculate_roi(0.524)  # Break-even accuracy
        0.0  # 0% ROI
        
        >>> calculate_roi(0.50)   # 50% accuracy
        -0.048  # -4.8% ROI (losing)
    """
    if odds != "-110":
        raise ValueError(f"Only -110 odds currently supported, got: {odds}")
    
    if accuracy < ROI_BREAKEVEN_ACCURACY:
        # Below break-even - approximate loss rate
        return (accuracy - ROI_BREAKEVEN_ACCURACY) * 2
    else:
        # Simplified ROI calculation for -110 odds
        # More accurate: ((wins * 0.909) - losses) / total_bets
        wins_per_100 = accuracy * 100
        losses_per_100 = (1 - accuracy) * 100
        profit = (wins_per_100 * 0.909) - losses_per_100
        return profit / 100


def calculate_coefficient_of_variation(values: np.ndarray) -> float:
    """
    Calculate coefficient of variation (CV = std_dev / mean).
    
    Used to measure relative variability, especially useful for
    comparing stability across features with different scales.
    
    Args:
        values: Array of values
        
    Returns:
        float: Coefficient of variation (0.0 to inf)
        
    Example:
        >>> calculate_coefficient_of_variation(np.array([0.10, 0.12, 0.11]))
        0.091  # 9.1% variation
    """
    mean_val = np.mean(values)
    if mean_val <= 0.001:
        return 0.0  # Avoid division by zero for very small means
    
    std_val = np.std(values)
    return float(std_val / mean_val)


__all__ = [
    'calculate_roi',
    'calculate_coefficient_of_variation',
]
