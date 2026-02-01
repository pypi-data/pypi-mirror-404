"""
Diagnostic analysis logic for Analytics Suite.
Extracts mathematical and statistical logic from validate_weekly.py.
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

def classify_power(mean_corr: float) -> str:
    """Classify predictive power based on correlation magnitude."""
    abs_corr = abs(mean_corr)
    if abs_corr > 0.15:
        return "STRONG"
    elif abs_corr > 0.08:
        return "MODERATE"
    elif abs_corr > 0.05:
        return "WEAK"
    else:
        return "NONE"

def analyze_feature_correlations(
    results: List[Dict[str, Any]]
) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Analyze correlation between feature values and game outcomes.
    
    Args:
        results: List of weekly validation results containing feature_correlations
    
    Returns:
        Dict mapping feature names to correlation statistics
    """
    feature_correlations = {}
    
    # Collect correlations from each week
    for week_result in results:
        if 'feature_correlations' not in week_result:
            continue
        
        week_corrs = week_result['feature_correlations']
        for feature, corr in week_corrs.items():
            if feature not in feature_correlations:
                feature_correlations[feature] = []
            feature_correlations[feature].append(corr)
    
    if not feature_correlations:
        return None
    
    # Aggregate statistics across weeks
    correlation_stats = {}
    for feature, corr_list in feature_correlations.items():
        if not corr_list:
            continue
        
        mean_corr = np.mean(corr_list)
        correlation_stats[feature] = {
            'mean_correlation': float(mean_corr),
            'std_correlation': float(np.std(corr_list)),
            'min_correlation': float(np.min(corr_list)),
            'max_correlation': float(np.max(corr_list)),
            'weeks_significant': int(sum(abs(c) > 0.1 for c in corr_list)),
            'predictive_power': classify_power(mean_corr)
        }
    
    return correlation_stats

def analyze_misses(
    results: List[Dict[str, Any]]
) -> Optional[pd.DataFrame]:
    """
    Analyze incorrect predictions to identify patterns in model failures.
    
    Args:
        results: List of weekly validation results containing 'misses'
        
    Returns:
        DataFrame containing detailed miss analysis
    """
    all_misses = []
    
    for week_result in results:
        if 'misses' in week_result:
            for miss in week_result['misses']:
                miss['week'] = week_result['week']
                all_misses.append(miss)
    
    if not all_misses:
        return None
        
    return pd.DataFrame(all_misses)

def calculate_stability_ratio(
    accuracy_mean: float,
    accuracy_std: float,
    avg_sample_size: float
) -> float:
    """
    Calculate Stability Ratio (Observed vs Theoretical Std Dev).
    
    Sigma_theo = sqrt(p(1-p)/n)
    Ratio = Sigma_obs / Sigma_theo
    
    Args:
        accuracy_mean: Mean accuracy across weeks
        accuracy_std: Observed standard deviation of accuracy
        avg_sample_size: Average number of games per week
        
    Returns:
        Stability ratio (1.0 = perfect stability consistent with random sampling)
    """
    if avg_sample_size <= 0:
        return 0.0
        
    theoretical_std = np.sqrt((accuracy_mean * (1 - accuracy_mean)) / avg_sample_size)
    
    if theoretical_std <= 0:
        return 0.0
        
    return accuracy_std / theoretical_std

def perform_statistical_tests(
    accuracies: List[float],
    baseline_accuracy: float = 0.5
) -> Dict[str, float]:
    """
    Perform T-tests against baseline.
    
    Args:
        accuracies: List of weekly accuracy scores
        baseline_accuracy: Baseline to test against (0.5 for random, or home win rate)
        
    Returns:
        Dictionary with t-statistic and p-value
    """
    if not accuracies or len(accuracies) < 2:
        return {'t_stat': 0.0, 'p_value': 1.0}
        
    t_stat_result = stats.ttest_1samp(accuracies, baseline_accuracy)
    
    # Handle potential numpy types
    t_stat = float(t_stat_result.statistic) if hasattr(t_stat_result, 'statistic') else 0.0
    p_value = float(t_stat_result.pvalue) if hasattr(t_stat_result, 'pvalue') else 1.0
    
    return {
        't_stat': t_stat,
        'p_value': p_value
    }

def check_training_growth_linearity(
    weeks: List[int],
    train_sizes: List[int]
) -> Dict[str, Any]:
    """
    Verify linear growth of training set (Walk-Forward Validation check).
    
    Args:
        weeks: List of week numbers
        train_sizes: List of training set sizes
        
    Returns:
        Dictionary with correlation and growth metrics
    """
    if len(weeks) < 2 or len(weeks) != len(train_sizes):
        return {'correlation': 0.0, 'growth_per_week': 0.0, 'is_linear': False}
        
    # Calculate growth per week
    growth_per_week = float(np.diff(np.array(train_sizes)).mean())
    
    # Check correlation
    corr_result = stats.pearsonr(weeks, train_sizes)
    corr = float(corr_result.statistic)
    
    return {
        'correlation': corr,
        'growth_per_week': growth_per_week,
        'is_linear': corr > 0.99
    }