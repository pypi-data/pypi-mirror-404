"""
Utility functions for safe correlation calculations.

Prevents NumPy division warnings when calculating correlations
on constant series (zero variance) or insufficient data pairs.
"""

import pandas as pd
import numpy as np
from typing import Optional
from logging import Logger


def safe_correlation(
    series1: pd.Series, 
    series2: pd.Series, 
    logger: Optional[Logger] = None
) -> float:
    """
    Calculate correlation with protection against constant series.
    
    This function prevents "invalid value encountered in divide" warnings
    that occur when numpy.corrcoef encounters zero-variance series.
    
    Args:
        series1: First series for correlation
        series2: Second series for correlation
        logger: Optional logger for diagnostic messages
    
    Returns:
        float: Pearson correlation coefficient or np.nan if calculation invalid
    
    Examples:
        >>> s1 = pd.Series([1, 2, 3, 4, 5])
        >>> s2 = pd.Series([2, 4, 6, 8, 10])
        >>> safe_correlation(s1, s2)
        1.0
        
        >>> # Constant series returns nan instead of warning
        >>> s_const = pd.Series([5, 5, 5, 5, 5])
        >>> safe_correlation(s1, s_const)
        nan
    """
    # Filter to rows with both values present
    mask = series1.notna() & series2.notna()
    s1, s2 = series1[mask], series2[mask]
    
    # Need at least 2 pairs for correlation
    if len(s1) < 2:
        if logger:
            logger.warning(f"Insufficient data pairs for correlation: {len(s1)}")
        return np.nan
    
    # Check for constant series (zero variance)
    # Using nunique() is more efficient than std() for this check
    if s1.nunique() <= 1:
        if logger:
            logger.debug(f"Skipped correlation calculation (constant series1)")
        return np.nan
    
    if s2.nunique() <= 1:
        if logger:
            logger.debug(f"Skipped correlation calculation (constant series2)")
        return np.nan
    
    # Safe to calculate correlation
    try:
        return s1.corr(s2)
    except Exception as e:
        if logger:
            logger.warning(f"Unexpected error in correlation calculation: {e}")
        return np.nan


def safe_corrwith(
    dataframe: pd.DataFrame,
    target: pd.Series,
    logger: Optional[Logger] = None
) -> pd.Series:
    """
    Calculate correlations for all columns with protection against constant series.
    
    Similar to pd.DataFrame.corrwith() but filters out constant columns
    before calculation to prevent division warnings.
    
    Args:
        dataframe: DataFrame with features to correlate
        target: Target series to correlate against
        logger: Optional logger for diagnostic messages
    
    Returns:
        pd.Series: Correlation coefficients (np.nan for constant columns)
    """
    # Filter to numeric columns only
    numeric_cols = dataframe.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        if logger:
            logger.warning("No numeric columns found for correlation calculation")
        return pd.Series(dtype=float)
    
    # Identify constant columns (zero variance)
    constant_cols = []
    non_constant_cols = []
    
    for col in numeric_cols:
        if dataframe[col].nunique() <= 1:
            constant_cols.append(col)
        else:
            non_constant_cols.append(col)
    
    if constant_cols and logger:
        logger.debug(f"Skipping {len(constant_cols)} constant columns in correlation calculation")
    
    # Calculate correlations for non-constant columns
    if non_constant_cols:
        try:
            correlations = dataframe[non_constant_cols].corrwith(target)
        except Exception as e:
            if logger:
                logger.warning(f"Error in corrwith calculation: {e}")
            correlations = pd.Series({col: np.nan for col in non_constant_cols})
    else:
        correlations = pd.Series(dtype=float)
    
    # Add NaN entries for constant columns
    for col in constant_cols:
        correlations[col] = np.nan
    
    # Preserve original column order
    return correlations.reindex(numeric_cols)


def safe_corr_matrix(
    dataframe: pd.DataFrame,
    logger: Optional[Logger] = None
) -> pd.DataFrame:
    """
    Calculate correlation matrix with protection against constant series.
    
    Filters out constant columns before calculating correlation matrix
    to prevent division warnings.
    
    Args:
        dataframe: DataFrame with features to correlate
        logger: Optional logger for diagnostic messages
    
    Returns:
        pd.DataFrame: Correlation matrix (excluding constant columns)
    """
    # Filter to numeric columns only
    numeric_cols = dataframe.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        if logger:
            logger.warning("No numeric columns found for correlation matrix")
        return pd.DataFrame()
    
    # Filter out constant columns
    non_constant = [col for col in numeric_cols if dataframe[col].nunique() > 1]
    
    if len(non_constant) < 2:
        if logger:
            logger.warning(f"Insufficient non-constant columns for correlation matrix: {len(non_constant)}")
        return pd.DataFrame()
    
    dropped_count = len(numeric_cols) - len(non_constant)
    if dropped_count > 0 and logger:
        logger.debug(f"Dropped {dropped_count} constant columns before correlation matrix calculation")
    
    try:
        return dataframe[non_constant].corr()
    except Exception as e:
        if logger:
            logger.warning(f"Error in correlation matrix calculation: {e}")
        return pd.DataFrame()


__all__ = ['safe_correlation', 'safe_corrwith', 'safe_corr_matrix']
