"""
Early-Season Shrinkage Framework

Applies Bayesian shrinkage to stabilize metrics with small sample sizes.
Used across all NextGen features for Weeks 1-3.
"""

import numpy as np
import pandas as pd
from typing import Union, Optional


def apply_shrinkage(
    value: Union[float, pd.Series],
    prior: float,
    n_samples: Union[int, pd.Series],
    confidence: float = 0.3
) -> Union[float, pd.Series]:
    """
    Apply Bayesian shrinkage to pull small-sample metrics toward prior.
    
    Formula: weighted_value = (n / (n + k)) * value + (k / (n + k)) * prior
    
    Where k = confidence * league_avg_samples
    
    Args:
        value: Observed metric value(s)
        prior: Prior belief (e.g., league average)
        n_samples: Number of observations
        confidence: Shrinkage strength (higher = more shrinkage)
                   0.3 = pull toward prior when n < 30% of league avg
    
    Returns:
        Shrunk value(s)
    
    Examples:
        >>> # Week 1: 2 games, pull heavily toward prior
        >>> apply_shrinkage(value=0.15, prior=0.05, n_samples=2, confidence=0.3)
        0.067  # Heavily shrunk toward 0.05
        
        >>> # Week 8: 8 games, less shrinkage
        >>> apply_shrinkage(value=0.15, prior=0.05, n_samples=8, confidence=0.3)
        0.12  # Lightly shrunk
    """
    # League average sample size (e.g., 16 games for full season)
    league_avg_samples = 16
    
    # Calculate shrinkage weight
    k = confidence * league_avg_samples
    weight = n_samples / (n_samples + k)
    
    # Apply shrinkage
    return weight * value + (1 - weight) * prior


def get_league_prior(
    metric_name: str,
    season: Optional[int] = None
) -> float:
    """
    Get league-average prior for a given metric.
    
    Args:
        metric_name: Name of metric (e.g., 'qb_epa_per_db')
        season: Optional season for time-varying priors
    
    Returns:
        Prior value (league average)
    """
    # Default priors (can be updated from historical data)
    PRIORS = {
        # Rolling metrics
        'rolling_4g_epa_offense': 0.05,
        'rolling_8g_epa_offense': 0.05,
        'rolling_16g_epa_offense': 0.05,
        'rolling_4g_epa_defense': 0.00,
        'rolling_8g_epa_defense': 0.00,
        'rolling_16g_epa_defense': 0.00,
        'rolling_4g_point_diff': 0.0,
        'rolling_8g_point_diff': 0.0,
        'rolling_16g_point_diff': 0.0,
        'rolling_4g_win_rate': 0.50,
        'rolling_8g_win_rate': 0.50,
        'rolling_16g_win_rate': 0.50,
        
        # NextGen metrics
        'qb_epa_per_db': 0.05,
        'qb_epa_clean_per_db': 0.10,
        'qb_epa_pressured_per_db': -0.15,
        'explosive_pass_rate': 0.12,
        'explosive_pass_epa': 0.50,
        'pbwr_pass': 0.50,
        'run_stop_win_rate': 0.50,
    }
    
    return PRIORS.get(metric_name, 0.0)


def apply_shrinkage_to_dataframe(
    df: pd.DataFrame,
    metric_cols: list,
    n_samples_col: str,
    confidence: float = 0.3
) -> pd.DataFrame:
    """
    Apply shrinkage to multiple metrics in a DataFrame.
    
    Args:
        df: DataFrame with metrics
        metric_cols: List of column names to shrink
        n_samples_col: Column name with sample sizes
        confidence: Shrinkage strength
    
    Returns:
        DataFrame with shrunk metrics
    """
    df = df.copy()
    
    for col in metric_cols:
        if col in df.columns:
            prior = get_league_prior(col)
            df[col] = apply_shrinkage(
                value=df[col],
                prior=prior,
                n_samples=df[n_samples_col],
                confidence=confidence
            )
    
    return df