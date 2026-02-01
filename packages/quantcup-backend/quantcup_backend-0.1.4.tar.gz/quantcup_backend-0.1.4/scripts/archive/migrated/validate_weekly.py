"""
Week-by-Week Validation Script for NFL Seasons

Tests model trained on historical data against each week of a test season
individually to measure variance and identify unstable predictions.

This script addresses the critical finding from Phase 6-7 analysis that
full-season testing (285 games) masks extreme week-by-week variance.

Usage:
    1. Edit the configuration section below to set TEST_YEAR
    2. Run: python scripts/validate_weekly.py

Output:
    - Console: Detailed variance analysis
    - File: reports/{TEST_YEAR}_weekly_validation_{timestamp}_report.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
import time
import platform
from typing import Optional, Dict, List, Any, Tuple

# ============================================================================
# CONFIGURATION - Edit these values to validate different years
# ============================================================================
TEST_YEAR = 2025        # Year to validate
BASELINE_YEAR = 2000    # Starting year for training data
MAX_WEEK = 11           # Maximum week to validate
# ============================================================================


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
    results: List[Dict[str, Any]],
    logger
) -> Optional[Dict[str, Dict[str, float]]]:
    """
    Analyze correlation between feature values and game outcomes.
    
    This measures actual predictive power, separate from XGBoost importance.
    
    Args:
        results: List of weekly validation results containing feature_correlations
        logger: Logger instance
    
    Returns:
        Dict mapping feature names to correlation statistics:
        {
            'feature_name': {
                'mean_correlation': float,  # Average correlation across weeks
                'std_correlation': float,   # Std dev of correlation
                'min_correlation': float,   # Weakest correlation
                'max_correlation': float,   # Strongest correlation
                'weeks_significant': int,   # Weeks with |r| > 0.1
                'predictive_power': str     # STRONG/MODERATE/WEAK/NONE
            }
        }
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
        logger.warning("No correlation data found in results")
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
    
    logger.info(f"✓ Analyzed correlations for {len(correlation_stats)} features across {len(results)} weeks")
    
    return correlation_stats


def analyze_misses(
    results: List[Dict[str, Any]],
    logger
) -> Optional[pd.DataFrame]:
    """
    Analyze incorrect predictions to identify patterns in model failures.
    
    Args:
        results: List of weekly validation results containing 'misses'
        logger: Logger instance
        
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
        
    miss_df = pd.DataFrame(all_misses)
    
    logger.info(f"✓ Analyzed {len(miss_df)} incorrect predictions")
    return miss_df


def validate_weekly() -> Optional[pd.DataFrame]:
    """
    Run week-by-week validation for configured season.
    
    Configuration is set via module-level constants:
    - TEST_YEAR: Season year to validate
    - BASELINE_YEAR: Starting year for training data
    - MAX_WEEK: Maximum week number to validate
    
    Trains model on BASELINE_YEAR to (TEST_YEAR-1) data, then tests on each
    week of TEST_YEAR individually using walk-forward validation.
    
    Returns:
        DataFrame with validation results, or None if validation fails
    """
    from nflfastRv3.features.ml_pipeline.orchestrators.model_trainer import create_model_trainer
    from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeModel
    from commonv2.core.logging import get_logger
    
    logger = get_logger(__name__)
    
    # Validate configuration
    if TEST_YEAR <= BASELINE_YEAR:
        raise ValueError(
            f"TEST_YEAR ({TEST_YEAR}) must be greater than BASELINE_YEAR ({BASELINE_YEAR})"
        )
    
    # Calculate training seasons from config
    train_end_year = TEST_YEAR - 1
    train_seasons = f'{BASELINE_YEAR}-{train_end_year}'
    training_years = train_end_year - BASELINE_YEAR + 1
    
    # Add timestamp tracking
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info("="*80)
    logger.info(f"{TEST_YEAR} SEASON WEEK-BY-WEEK VALIDATION")
    logger.info("="*80)
    logger.info(f"Run Date: {run_date}")
    logger.info(f"Run ID: {timestamp}")
    logger.info("")
    logger.info("Purpose: Measure model variance across individual weeks")
    logger.info(f"Training: {train_seasons} ({training_years} seasons)")
    logger.info(f"Testing: {TEST_YEAR} Weeks 1-{MAX_WEEK} (individual weeks)")
    logger.info("")
    logger.info("Model Configuration:")
    logger.info("  Type: XGBoost with Increased Regularization (v2)")
    logger.info("  Feature Count: 30 features")
    logger.info("  Random State: 42")
    logger.info("")
    
    # Initialize trainer using factory function
    logger.info("Initializing model trainer...")
    trainer = create_model_trainer(logger=logger)
    
    # Track cumulative training data for walk-forward validation
    cumulative_test_weeks = []
    results = []
    
    logger.info("🔍 Starting walk-forward validation...")
    logger.info(f"   Week 1: Baseline ({train_seasons} only)")
    logger.info(f"   Week 2+: Incremental learning (adding completed {TEST_YEAR} weeks)")
    logger.info("")
    
    for week in range(1, MAX_WEEK + 1):
        logger.info(f"📊 Progress: Week {week}/{MAX_WEEK} ({week/MAX_WEEK*100:.0f}%)")
        
        # Build cumulative training specification
        if week == 1:
            # Week 1: Only historical data (baseline)
            train_seasons_str = train_seasons
            train_weeks = None
            logger.info(f"Week {week}: Training on {train_seasons} only")
        else:
            # Week 2+: Historical + completed test year weeks
            train_seasons_str = f'{train_seasons},{TEST_YEAR}'
            train_weeks = {TEST_YEAR: cumulative_test_weeks.copy()}
            logger.info(f"Week {week}: Training on {train_seasons} + {TEST_YEAR} Weeks {cumulative_test_weeks}")
        
        try:
            # Train with cumulative data
            result = trainer.train_model(
                model_class=GameOutcomeModel,
                train_seasons=train_seasons_str,
                train_weeks=train_weeks,
                test_seasons=str(TEST_YEAR),
                test_week=week,
                save_model=False,
                random_state=42,
                return_correlations=True,
                return_predictions=True  # Request predictions for miss analysis
            )
            
            if result['status'] != 'success':
                logger.warning(f"⚠️  Week {week}: Training failed - {result.get('message', 'Unknown error')}")
                continue
            
            # Verify walk-forward is working
            actual_train_size = result['train_size']
            if week > 1:
                baseline_size = results[0]['train_size'] if results else 6160
                growth = actual_train_size - baseline_size
                logger.info(f"✓ Training size: {actual_train_size:,} games (+{growth} from baseline)")
            
            logger.info(f"✓ Week {week}: Training successful")
            
            # Add current week to cumulative list for next iteration
            cumulative_test_weeks.append(week)
            
            # Collect metrics with enhanced tracking
            metrics = result['metrics']
            results.append({
                'week': week,
                'train_size': actual_train_size,  # Track growing training set
                'train_weeks_used': len(cumulative_test_weeks) - 1,  # Weeks used in training
                'test_size': result['test_size'],
                'accuracy': metrics['accuracy'],
                'auc': metrics['auc'],
                'actual_home_win_rate': metrics['actual_home_win_rate'],
                'predicted_home_win_rate': metrics['predicted_home_win_rate'],
                'home_win_bias': metrics['home_win_bias'],
                'beats_always_home': metrics['accuracy'] > metrics['actual_home_win_rate'],
                'beats_random': metrics['beats_random'],
                'improvement_over_home': metrics['improvement_over_home'],
                'feature_importance': metrics.get('feature_importance', []),
                'feature_correlations': metrics.get('feature_correlations', {}),
                'misses': [] # Placeholder for miss analysis
            })
            
            # Extract misses if predictions are available
            if 'predictions' in result:
                preds = result['predictions']
                # Identify incorrect predictions
                # Assuming preds has 'game_id', 'home_team_won', 'prediction', 'home_win_prob'
                # and feature columns
                
                # Get feature importance for weighting
                feat_imp = {item['feature']: item['importance'] for item in metrics.get('feature_importance', [])}
                
                misses = []
                for _, row in preds.iterrows():
                    actual = row['home_team_won']
                    predicted = row['prediction']
                    
                    if actual != predicted:
                        # Calculate top contributing features for this specific miss
                        # Contribution = Feature Value * Global Importance
                        contributions = {}
                        for feat, importance in feat_imp.items():
                            if feat in row:
                                val = row[feat]
                                # Normalize contribution magnitude
                                contributions[feat] = val * importance
                        
                        # Sort by absolute contribution
                        top_contributors = sorted(
                            contributions.items(),
                            key=lambda x: abs(x[1]),
                            reverse=True
                        )[:3]
                        
                        misses.append({
                            'game_id': row.get('game_id', 'unknown'),
                            'home_team': row.get('home_team', 'unknown'),
                            'away_team': row.get('away_team', 'unknown'),
                            'actual_winner': 'Home' if actual == 1 else 'Away',
                            'predicted_winner': 'Home' if predicted == 1 else 'Away',
                            'confidence': row.get('confidence', 0.0),
                            'home_win_prob': row.get('home_win_prob', 0.0),
                            'top_factor_1': f"{top_contributors[0][0]} ({top_contributors[0][1]:.3f})" if len(top_contributors) > 0 else "N/A",
                            'top_factor_2': f"{top_contributors[1][0]} ({top_contributors[1][1]:.3f})" if len(top_contributors) > 1 else "N/A",
                            'top_factor_3': f"{top_contributors[2][0]} ({top_contributors[2][1]:.3f})" if len(top_contributors) > 2 else "N/A"
                        })
                
                results[-1]['misses'] = misses
            
            logger.info(
                f"Week {week:2d}: {result['test_size']:2d} games | "
                f"Train: {actual_train_size:,} | "
                f"Acc: {metrics['accuracy']:.1%} | "
                f"AUC: {metrics['auc']:.3f} | "
                f"Bias: {metrics['home_win_bias']:+.1%} | "
                f"{'✓' if metrics['accuracy'] > metrics['actual_home_win_rate'] else '✗'} Beats Home"
            )
            
        except Exception as e:
            logger.error(f"Week {week}: Error - {e}", exc_info=True)
            continue
    
    if not results:
        logger.error("No results collected. Validation failed.")
        return None
    
    # Calculate variance statistics
    results_df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    # Accuracy variance
    acc_min = results_df['accuracy'].min()
    acc_max = results_df['accuracy'].max()
    acc_range = acc_max - acc_min
    acc_mean = results_df['accuracy'].mean()
    acc_std = results_df['accuracy'].std()
    
    # Calculate Theoretical Standard Deviation (Binomial Noise)
    # Sigma_theo = sqrt(p(1-p)/n)
    avg_games = results_df['test_size'].mean()
    theoretical_std = np.sqrt((acc_mean * (1 - acc_mean)) / avg_games)
    stability_ratio = acc_std / theoretical_std if theoretical_std > 0 else 0
    
    print(f"\nAccuracy Statistics:")
    print(f"  Range: {acc_min:.1%} - {acc_max:.1%}")
    print(f"  Accuracy Range: {acc_range * 100:.1f} pp")
    print(f"  Mean: {acc_mean:.1%}")
    print(f"  Std Dev (Observed): {acc_std:.1%}")
    print(f"  Std Dev (Theoretical): {theoretical_std:.1%} (expected from n={avg_games:.1f})")
    print(f"  Stability Ratio: {stability_ratio:.2f}x (Observed / Theoretical)")
    
    # AUC variance
    auc_min = results_df['auc'].min()
    auc_max = results_df['auc'].max()
    weeks_below_random = (results_df['auc'] < 0.5).sum()
    
    print(f"\nAUC-ROC Statistics:")
    print(f"  Range: {auc_min:.3f} - {auc_max:.3f}")
    print(f"  Mean: {results_df['auc'].mean():.3f}")
    print(f"  Weeks with AUC < 0.5 (anti-predictive): {weeks_below_random}")
    
    # Home win bias
    bias_min = results_df['home_win_bias'].min()
    bias_max = results_df['home_win_bias'].max()
    bias_range = bias_max - bias_min
    
    print(f"\nHome Win Bias Statistics:")
    print(f"  Range: {bias_min:+.1%} - {bias_max:+.1%}")
    print(f"  Swing: {bias_range * 100:.1f} percentage points")
    print(f"  Mean: {results_df['home_win_bias'].mean():+.1%}")
    
    # Baseline performance
    weeks_beating_home = results_df['beats_always_home'].sum()
    weeks_beating_random = results_df['beats_random'].sum()
    
    print(f"\nBaseline Performance:")
    print(f"  Weeks Beating 'Always Home': {weeks_beating_home}/{len(results_df)} ({weeks_beating_home/len(results_df):.1%})")
    print(f"  Weeks Beating Random: {weeks_beating_random}/{len(results_df)} ({weeks_beating_random/len(results_df):.1%})")
    
    # Statistical significance test
    print(f"\nStatistical Tests:")
    
    # Test if accuracy is significantly different from 0.5 (random)
    t_stat_result = stats.ttest_1samp(results_df['accuracy'], 0.5)
    t_stat: float = float(t_stat_result.statistic)  # type: ignore[attr-defined]
    p_value: float = float(t_stat_result.pvalue)  # type: ignore[attr-defined]
    print(f"  Accuracy vs Random (0.5): t={t_stat:.3f}, p={p_value:.4f}")
    if p_value < 0.05:
        print(f"    → Significantly {'better' if acc_mean > 0.5 else 'worse'} than random (p < 0.05)")
    else:
        print(f"    → Not significantly different from random (p ≥ 0.05)")
    
    # Test if accuracy is significantly different from always home baseline
    home_baseline = results_df['actual_home_win_rate'].mean()
    t_stat_result = stats.ttest_1samp(results_df['accuracy'], home_baseline)
    t_stat = float(t_stat_result.statistic)  # type: ignore[attr-defined]
    p_value = float(t_stat_result.pvalue)  # type: ignore[attr-defined]
    print(f"  Accuracy vs Always Home ({home_baseline:.3f}): t={t_stat:.3f}, p={p_value:.4f}")
    if p_value < 0.05:
        print(f"    → Significantly {'better' if acc_mean > home_baseline else 'worse'} than baseline (p < 0.05)")
    else:
        print(f"    → Not significantly different from baseline (p ≥ 0.05)")
    
    # Training Size Progression Analysis (Walk-Forward Validation)
    if 'train_size' in results_df.columns:
        print("\n" + "="*80)
        print("TRAINING SIZE PROGRESSION (Walk-Forward Validation)")
        print("="*80)
        
        print(f"\nTraining Set Growth:")
        print(f"  Week 1 (baseline): {results_df.iloc[0]['train_size']:,} games")
        print(f"  Week 18 (final): {results_df.iloc[-1]['train_size']:,} games")
        print(f"  Total growth: {results_df.iloc[-1]['train_size'] - results_df.iloc[0]['train_size']:,} games")
        print(f"  Average per week: {(results_df.iloc[-1]['train_size'] - results_df.iloc[0]['train_size']) / 17:.1f} games")
        
        # Verify linear growth (should be ~16 games per week)
        weeks = results_df['week'].values
        train_sizes = results_df['train_size'].values
        growth_per_week = float(np.diff(np.array(train_sizes)).mean())
        print(f"  Actual growth per week: {growth_per_week:.1f} games")
        
        # Check correlation (should be ~1.0 for proper walk-forward)
        from scipy.stats import pearsonr
        corr_result = pearsonr(weeks, train_sizes)
        corr: float = float(corr_result.statistic)  # type: ignore[attr-defined]
        p_value_corr: float = float(corr_result.pvalue)  # type: ignore[attr-defined]
        print(f"  Growth correlation: {corr:.4f} (p={p_value_corr:.4f})")
        
        if corr > 0.99:
            print("  ✓ EXCELLENT: Linear growth confirmed (walk-forward working)")
        elif corr > 0.95:
            print("  ⚠️  GOOD: Mostly linear growth")
        else:
            print("  ❌ WARNING: Non-linear growth detected (check implementation)")
    
    # Feature Importance Analysis
    print("\n" + "="*80)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("="*80)
    
    # Extract feature importance from results
    feature_importance_by_week = {}
    feature_stats = None
    for r in results:
        if 'feature_importance' in r and r['feature_importance']:
            # Convert list of dicts to dict for easier processing
            week_dict = {item['feature']: item['importance'] for item in r['feature_importance']}
            feature_importance_by_week[r['week']] = week_dict
    
    if feature_importance_by_week:
        # Calculate average importance across weeks
        all_features = set()
        for week_features in feature_importance_by_week.values():
            all_features.update(week_features.keys())
        
        feature_stats = {}
        for feature in all_features:
            importances = [
                week_features.get(feature, 0)
                for week_features in feature_importance_by_week.values()
            ]
            feature_stats[feature] = {
                'mean': np.mean(importances),
                'std': np.std(importances),
                'min': np.min(importances),
                'max': np.max(importances),
                'cv': np.std(importances) / np.mean(importances) if np.mean(importances) > 0 else 0
            }
        
        # Sort by mean importance
        sorted_features = sorted(
            feature_stats.items(),
            key=lambda x: x[1]['mean'],
            reverse=True
        )
        
        print("\nTop 5 Most Important Features:")
        for i, (feature, feat_stats) in enumerate(sorted_features[:5], 1):
            print(f"  {i}. {feature}: {feat_stats['mean']:.4f} (±{feat_stats['std']:.4f})")
        
        # Feature Stability Summary
        stable_features = [f for f, feat_s in feature_stats.items() if feat_s['cv'] < 0.3]
        unstable_features_list = [f for f, feat_s in feature_stats.items() if feat_s['cv'] >= 0.5]
        
        print(f"\nFeature Stability: {len(stable_features)} stable, {len(unstable_features_list)} unstable")
    else:
        print("\n⚠️  Feature importance data not available")
    
    # Feature Correlation Analysis
    print("\n" + "="*80)
    print("FEATURE CORRELATION ANALYSIS")
    print("="*80)
    
    correlation_stats = analyze_feature_correlations(results, logger)
    
    if correlation_stats:
        # Sort by absolute mean correlation
        sorted_corrs = sorted(
            correlation_stats.items(),
            key=lambda x: abs(x[1]['mean_correlation']),
            reverse=True
        )
        
        print("\nTop 10 Features by Correlation with Outcomes:")
        for i, (feature, corr_stats) in enumerate(sorted_corrs[:10], 1):
            power = corr_stats['predictive_power']
            power_symbol = "✓" if power in ["STRONG", "MODERATE"] else "⚠️" if power == "WEAK" else "✗"
            print(f"  {i}. {feature}: {corr_stats['mean_correlation']:+.3f} (±{corr_stats['std_correlation']:.3f}) {power_symbol} {power}")
        
        # Identify injury features
        injury_features = [f for f in correlation_stats.keys() if 'injury' in f.lower() or 'qb_available' in f.lower()]
        if injury_features:
            print("\nInjury Feature Performance:")
            for feature in injury_features:
                corr_stats = correlation_stats[feature]
                print(f"  {feature}: {corr_stats['mean_correlation']:+.3f} ({corr_stats['predictive_power']})")
        
        # Count by power level
        power_counts = {}
        for corr_stat_dict in correlation_stats.values():
            power = corr_stat_dict['predictive_power']
            power_counts[power] = power_counts.get(power, 0) + 1
        
        print(f"\nPredictive Power Distribution:")
        for power in ["STRONG", "MODERATE", "WEAK", "NONE"]:
            count = power_counts.get(power, 0)
            pct = count / len(correlation_stats) * 100 if correlation_stats else 0
            print(f"  {power}: {count} features ({pct:.1f}%)")
    else:
        print("\n⚠️  Correlation data not available")
        correlation_stats = None
    
    
    # Prepare metadata for markdown report
    metadata = {
        'run_id': timestamp,
        'run_date': run_date,
        'duration_seconds': time.time() - start_time,
        'model_type': 'XGBoost',
        'model_version': 'v2_increased_regularization',
        'training_seasons': train_seasons,
        'test_season': TEST_YEAR,
        'baseline_year': BASELINE_YEAR,
        'max_week': MAX_WEEK,
        'training_years': training_years,
        'training_size': results_df.iloc[0]['train_size'] if len(results_df) > 0 else None,
        'feature_count': 30,
        'random_state': 42,
        'python_version': sys.version,
        'platform': platform.platform(),
        'weeks_tested': len(results_df),
        'mean_accuracy': results_df['accuracy'].mean(),
        'accuracy_variance': results_df['accuracy'].std(),
    }
    
    # Enhanced comprehensive assessment
    print("\n" + "="*80)
    print("COMPREHENSIVE ASSESSMENT")
    print("="*80)
    
    # Stability Assessment (Stability Ratio)
    # Ratio ~ 1.0 means variance is purely due to sample size (perfect stability)
    # Ratio > 1.0 means model has extra volatility
    print("\n📊 Stability Assessment (Observed vs Theoretical Variance):")
    if stability_ratio < 1.10:
        print(f"  ✓ EXCELLENT: Ratio {stability_ratio:.2f}x (Variance consistent with random sampling)")
        stability_grade = "A"
    elif stability_ratio < 1.25:
        print(f"  ✓ GOOD: Ratio {stability_ratio:.2f}x (Slight excess variance)")
        stability_grade = "B"
    elif stability_ratio < 1.50:
        print(f"  ⚠️  MODERATE: Ratio {stability_ratio:.2f}x (Moderate excess variance)")
        stability_grade = "C"
    else:
        print(f"  ❌ UNSTABLE: Ratio {stability_ratio:.2f}x (High excess variance)")
        stability_grade = "F"
    
    # Reliability Assessment (Anti-Predictive Weeks)
    print("\n🎯 Reliability Assessment:")
    if weeks_below_random == 0:
        print("  ✓ No anti-predictive weeks")
        reliability_grade = "A"
    elif weeks_below_random <= 1:
        print(f"  ⚠️  {weeks_below_random} anti-predictive week")
        reliability_grade = "B"
    else:
        print(f"  ❌ {weeks_below_random} anti-predictive weeks")
        reliability_grade = "F"
    
    # Baseline Performance
    print("\n📈 Baseline Performance:")
    baseline_pct = weeks_beating_home / len(results_df)
    if baseline_pct >= 0.9:
        print(f"  ✓ EXCELLENT: Beats baseline {baseline_pct:.1%} of weeks")
        baseline_grade = "A"
    elif baseline_pct >= 0.75:
        print(f"  ⚠️  GOOD: Beats baseline {baseline_pct:.1%} of weeks")
        baseline_grade = "B"
    else:
        print(f"  ❌ POOR: Beats baseline {baseline_pct:.1%} of weeks")
        baseline_grade = "F"
    
    # Overall Grade
    grades = [stability_grade, reliability_grade, baseline_grade]
    if all(g == "A" for g in grades):
        overall = "✓ PRODUCTION READY"
    elif "F" in grades:
        overall = "❌ NOT PRODUCTION READY"
    else:
        overall = "⚠️  NEEDS MONITORING"
    
    print(f"\n🏆 Overall Assessment: {overall}")
    print(f"   Stability: {stability_grade} | Reliability: {reliability_grade} | Baseline: {baseline_grade}")
    
    print("="*80)
    
    # Create comprehensive markdown report
    def create_markdown_report(
        results_df: pd.DataFrame,
        metadata: Dict[str, Any],
        timestamp: str,
        feature_stats: Optional[Dict[str, Dict[str, float]]] = None,
        correlation_stats: Optional[Dict[str, Dict[str, float]]] = None,
        stability_grade: str = "N/A",
        reliability_grade: str = "N/A",
        baseline_grade: str = "N/A",
        overall_assessment: str = "N/A",
        weeks_below_random: int = 0,
        weeks_beating_home: int = 0,
        acc_range: float = 0.0,
        acc_mean: float = 0.0,
        acc_std: float = 0.0,
        stability_ratio: float = 0.0,
        auc_min: float = 0.0,
        auc_max: float = 0.0,
        bias_min: float = 0.0,
        bias_max: float = 0.0,
        bias_range: float = 0.0,
        unstable_count: int = 0,
        miss_df: Optional[pd.DataFrame] = None
    ) -> Path:
        """Create comprehensive markdown report with enhanced feature analysis.
        
        Args:
            results_df: DataFrame containing weekly validation results
            metadata: Dictionary containing run metadata
            timestamp: Timestamp string for file naming
            feature_stats: Optional dictionary of feature statistics
            correlation_stats: Optional dictionary of feature correlation statistics
            variance_grade: Grade for variance assessment
            stability_grade: Grade for stability assessment
            baseline_grade: Grade for baseline performance
            overall_assessment: Overall assessment string
            weeks_below_random: Number of weeks with AUC < 0.5
            weeks_beating_home: Number of weeks beating home baseline
            acc_range: Accuracy range
            acc_mean: Mean accuracy
            acc_std: Standard deviation of accuracy
            auc_min: Minimum AUC
            auc_max: Maximum AUC
            bias_min: Minimum home win bias
            bias_max: Maximum home win bias
            bias_range: Range of home win bias
            unstable_count: Number of unstable features (CV >= 0.5)
            
        Returns:
            Path to the created markdown report file
        """
        # Use domain-based subfolder for organization
        # TODO: If generating multiple artifact types (CSV + MD + JSON), consider using
        # timestamped subfolders: Path("reports/weekly_validation") / f"{TEST_YEAR}_{timestamp}"
        # This groups related artifacts together (see scripts/analyze_pbp_odds_data_v4.py)
        domain_folder = Path("reports") / "weekly_validation"
        domain_folder.mkdir(parents=True, exist_ok=True)
        report_path = domain_folder / f"{TEST_YEAR}_weekly_validation_{timestamp}_report.md"
        
        with open(report_path, 'w') as f:
            # Header
            f.write(f"# {TEST_YEAR} Season Week-by-Week Validation Report\n\n")
            f.write(f"**Run Date:** {metadata['run_date']}  \n")
            f.write(f"**Run ID:** {metadata['run_id']}  \n")
            f.write(f"**Duration:** {metadata['duration_seconds']:.1f}s ({metadata['duration_seconds']/60:.1f} minutes)  \n")
            f.write(f"**Model:** {metadata['model_type']} {metadata['model_version']}  \n")
            f.write(f"**Training:** {metadata['training_seasons']} ({metadata['training_years']} seasons)  \n")
            f.write(f"**Testing:** {TEST_YEAR} Weeks 1-{MAX_WEEK}\n\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write("| Metric | Value | Grade |\n")
            f.write("|--------|-------|-------|\n")
            f.write(f"| **Mean Accuracy** | {acc_mean:.1%} | - |\n")
            f.write(f"| **Stability Ratio** | {stability_ratio:.2f}x | {stability_grade} |\n")
            f.write(f"| **Reliability (AUC)** | {results_df['auc'].mean():.3f} | {reliability_grade} |\n")
            f.write(f"| **Weeks Beating Baseline** | {weeks_beating_home}/{len(results_df)} ({weeks_beating_home/len(results_df):.1%}) | {baseline_grade} |\n")
            f.write(f"| **Overall Assessment** | {overall_assessment} | - |\n\n")
            
            # Key Findings
            f.write("### Key Findings\n")
            weeks_beating_random = (results_df['beats_random']).sum()
            f.write(f"- {'✓' if weeks_beating_random == len(results_df) else '⚠️'} Model beats random baseline in {weeks_beating_random}/{len(results_df)} weeks ({weeks_beating_random/len(results_df):.1%})\n")
            
            if stability_ratio < 1.25:
                f.write(f"- ✓ High stability detected (Ratio: {stability_ratio:.2f}x)\n")
            elif stability_ratio < 1.50:
                f.write(f"- ⚠️ Moderate stability detected (Ratio: {stability_ratio:.2f}x)\n")
            else:
                f.write(f"- ❌ Low stability detected (Ratio: {stability_ratio:.2f}x)\n")
            
            f.write(f"- {'✓' if weeks_below_random == 0 else '❌'} {weeks_below_random if weeks_below_random > 0 else 'No'} anti-predictive weeks (AUC < 0.5)\n")
            f.write(f"- {'⚠️' if abs(bias_range) > 0.15 else '✓'} Home win bias ranges from {bias_min:+.1%} to {bias_max:+.1%}\n\n")
            f.write("---\n\n")
            
            # Week-by-Week Performance
            f.write("## Week-by-Week Performance\n\n")
            f.write("| Week | Train Size | Test Size | Accuracy | AUC | Home Bias | Beats Home | Improvement |\n")
            f.write("|------|-----------|-----------|----------|-----|-----------|------------|-------------|\n")
            
            for _, row in results_df.iterrows():
                beats_home_symbol = "✓" if row['beats_always_home'] else "✗"
                f.write(f"| {int(row['week'])} | {int(row['train_size']):,} | {int(row['test_size'])} | "
                       f"{row['accuracy']:.1%} | {row['auc']:.3f} | {row['home_win_bias']:+.1%} | "
                       f"{beats_home_symbol} | {row['improvement_over_home']:+.1%} |\n")
            
            # Training Size Progression
            if len(results_df) > 1:
                f.write(f"\n**Training Size Progression:**\n")
                f.write(f"- Week 1 (baseline): {int(results_df.iloc[0]['train_size']):,} games\n")
                f.write(f"- Week {MAX_WEEK} (final): {int(results_df.iloc[-1]['train_size']):,} games  \n")
                total_growth = int(results_df.iloc[-1]['train_size'] - results_df.iloc[0]['train_size'])
                f.write(f"- Total growth: {total_growth:,} games\n")
                
                if len(results_df) > 1:
                    growth_per_week = total_growth / (len(results_df) - 1)
                    f.write(f"- Growth per week: {growth_per_week:.1f} games")
                    
                    # Check correlation
                    from scipy.stats import pearsonr
                    weeks = results_df['week'].values
                    train_sizes = results_df['train_size'].values
                    corr_result = pearsonr(weeks, train_sizes)
                    corr = float(corr_result.statistic)  # type: ignore
                    
                    if corr > 0.99:
                        f.write(f" (✓ Linear growth confirmed, r={corr:.4f})\n")
                    else:
                        f.write(f" (⚠️ r={corr:.4f})\n")
            
            f.write("\n---\n\n")
            
            # Statistical Analysis
            f.write("## Statistical Analysis\n\n")
            
            f.write("### Accuracy Statistics\n")
            f.write(f"- **Range:** {results_df['accuracy'].min():.1%} - {results_df['accuracy'].max():.1%}\n")
            f.write(f"- **Mean:** {acc_mean:.1%}\n")
            f.write(f"- **Std Dev (Observed):** {acc_std:.1%}\n")
            f.write(f"- **Stability Ratio:** {stability_ratio:.2f}x (Observed / Theoretical)\n")
            f.write(f"- **Coefficient of Variation:** {(acc_std / acc_mean):.2%}\n\n")
            
            # Statistical tests
            t_stat_result = stats.ttest_1samp(results_df['accuracy'], 0.5)
            t_stat = float(t_stat_result.statistic)  # type: ignore
            p_value = float(t_stat_result.pvalue)  # type: ignore
            
            f.write("**Statistical Tests:**\n")
            f.write(f"- Accuracy vs Random (50%): t={t_stat:.3f}, p={p_value:.4f}")
            if p_value < 0.05:
                f.write(f" → {'✓ Significantly better' if acc_mean > 0.5 else '❌ Significantly worse'} than random\n")
            else:
                f.write(f" → Not significantly different from random\n")
            
            home_baseline = results_df['actual_home_win_rate'].mean()
            t_stat_result = stats.ttest_1samp(results_df['accuracy'], home_baseline)
            t_stat = float(t_stat_result.statistic)  # type: ignore
            p_value = float(t_stat_result.pvalue)  # type: ignore
            
            f.write(f"- Accuracy vs Always Home ({home_baseline:.1%}): t={t_stat:.3f}, p={p_value:.4f}")
            if p_value < 0.05:
                f.write(f" → {'✓ Significantly better' if acc_mean > home_baseline else '❌ Significantly worse'} than baseline\n")
            else:
                f.write(f" → Not significantly different from baseline\n")
            
            f.write("\n### AUC-ROC Statistics\n")
            f.write(f"- **Range:** {auc_min:.3f} - {auc_max:.3f}\n")
            f.write(f"- **Mean:** {results_df['auc'].mean():.3f}\n")
            f.write(f"- **Weeks with AUC < 0.5:** {weeks_below_random} ({weeks_below_random/len(results_df):.1%})\n\n")
            
            f.write("### Home Win Bias\n")
            f.write(f"- **Range:** {bias_min:+.1%} to {bias_max:+.1%}\n")
            f.write(f"- **Swing:** {bias_range * 100:.1f} percentage points\n")
            f.write(f"- **Mean:** {results_df['home_win_bias'].mean():+.1%}\n\n")
            
            f.write("---\n\n")
            
            # Feature Importance Analysis
            if feature_stats:
                f.write("## Feature Importance Analysis\n\n")
                
                # Sort features by mean importance
                sorted_features = sorted(
                    feature_stats.items(),
                    key=lambda x: x[1]['mean'],
                    reverse=True
                )
                
                # Top 15 Features
                f.write("### Top 15 Most Important Features\n\n")
                f.write("| Rank | Feature | Mean | Std Dev | Min | Max | CV | Status |\n")
                f.write("|------|---------|------|---------|-----|-----|----|--------|\n")
                
                for i, (feature, feat_stats) in enumerate(sorted_features[:15], 1):
                    cv = feat_stats['cv']
                    status = "FROZEN" if cv < 0.01 else "STABLE" if cv < 0.3 else "VARIABLE" if cv < 0.5 else "UNSTABLE"
                    f.write(f"| {i} | {feature} | {feat_stats['mean']:.4f} | {feat_stats['std']:.4f} | "
                           f"{feat_stats['min']:.4f} | {feat_stats['max']:.4f} | {cv:.2f} | {status} |\n")
                
                # Bottom 15 Features
                f.write("\n### Bottom 15 Least Important Features\n\n")
                f.write("| Rank | Feature | Mean | Std Dev | Min | Max | CV | Status |\n")
                f.write("|------|---------|------|---------|-----|-----|----|--------|\n")
                
                total_features = len(sorted_features)
                start_rank = max(16, total_features - 14)
                
                for i, (feature, feat_stats) in enumerate(sorted_features[-15:], start_rank):
                    cv = feat_stats['cv']
                    status = "FROZEN" if cv < 0.01 else "STABLE" if cv < 0.3 else "VARIABLE" if cv < 0.5 else "UNSTABLE"
                    f.write(f"| {i} | {feature} | {feat_stats['mean']:.4f} | {feat_stats['std']:.4f} | "
                           f"{feat_stats['min']:.4f} | {feat_stats['max']:.4f} | {cv:.2f} | {status} |\n")
                
                f.write("\n---\n\n")
                
                # Feature Stability Assessment
                f.write("## Feature Stability Assessment\n\n")
                f.write("### Stability Distribution\n\n")
                
                frozen_count = sum(1 for _, feat_s in feature_stats.items() if feat_s['cv'] < 0.01)
                stable_count = sum(1 for _, feat_s in feature_stats.items() if 0.01 <= feat_s['cv'] < 0.3)
                variable_count = sum(1 for _, feat_s in feature_stats.items() if 0.3 <= feat_s['cv'] < 0.5)
                unstable_count = sum(1 for _, feat_s in feature_stats.items() if feat_s['cv'] >= 0.5)
                total = len(feature_stats)
                
                f.write("| Category | Count | Percentage | Description |\n")
                f.write("|----------|-------|------------|-------------|\n")
                f.write(f"| **FROZEN** (CV < 0.01) | {frozen_count} | {frozen_count/total:.1%} | ❌ Indicates overfitting |\n")
                f.write(f"| **STABLE** (0.01-0.3) | {stable_count} | {stable_count/total:.1%} | ✓ Healthy variation |\n")
                f.write(f"| **VARIABLE** (0.3-0.5) | {variable_count} | {variable_count/total:.1%} | ⚠️ High variation |\n")
                f.write(f"| **UNSTABLE** (CV ≥ 0.5) | {unstable_count} | {unstable_count/total:.1%} | ❌ Too unstable |\n\n")
                
                if frozen_count == 0:
                    f.write("**Assessment:** ✓ No frozen features - walk-forward validation working correctly!\n\n")
                else:
                    f.write(f"**Assessment:** ⚠️ {frozen_count} frozen features detected - may indicate overfitting\n\n")
                
                # Unstable features requiring review
                if unstable_count > 0:
                    f.write("### Unstable Features Requiring Review\n\n")
                    f.write("The following features show high variance (CV ≥ 0.5) and may need refinement:\n\n")
                    
                    unstable_features = [(feat, feat_stats) for feat, feat_stats in sorted_features if feat_stats['cv'] >= 0.5]
                    for i, (feature, feat_stats) in enumerate(unstable_features[:10], 1):
                        f.write(f"{i}. **{feature}** (CV={feat_stats['cv']:.2f}) - Range: [{feat_stats['min']:.4f}, {feat_stats['max']:.4f}]\n")
                    
                    f.write("\n**Recommendations:**\n")
                    f.write("- Week-specific patterns not generalizable\n")
                    f.write("- Small sample size effects\n")
                    f.write("- Consider feature engineering improvements or removal\n\n")
                
                f.write("---\n\n")
                
                # Feature Variance Analysis
                f.write("## Feature Variance Analysis\n\n")
                f.write("| Feature | Variance Across Weeks | Interpretation |\n")
                f.write("|---------|----------------------|----------------|\n")
                
                # Show top 10 by variance
                variance_sorted = sorted(
                    feature_stats.items(),
                    key=lambda x: x[1]['std']**2,
                    reverse=True
                )[:10]
                
                for feature, feat_stats in variance_sorted:
                    variance = feat_stats['std'] ** 2
                    interpretation = "Very high - unreliable" if variance > 0.001 else "High - week-dependent" if variance > 0.0005 else "Low - consistent importance"
                    f.write(f"| {feature} | {variance:.5f} | {interpretation} |\n")
                
                f.write("\n---\n\n")
                
                # Feature Correlation Analysis Section
                if correlation_stats:
                    f.write("## Feature Correlation Analysis\n\n")
                    f.write("### Correlation with Game Outcomes\n\n")
                    f.write("Measures actual predictive power (separate from XGBoost importance).\n\n")
                    
                    # Sort by absolute mean correlation
                    sorted_corrs = sorted(
                        correlation_stats.items(),
                        key=lambda x: abs(x[1]['mean_correlation']),
                        reverse=True
                    )
                    
                    f.write("| Rank | Feature | Mean Corr | Std Dev | Range | Weeks Sig | Power |\n")
                    f.write("|------|---------|-----------|---------|-------|-----------|-------|\n")
                    
                    for i, (feature, corr_stats) in enumerate(sorted_corrs[:20], 1):
                        f.write(
                            f"| {i} | {feature} | {corr_stats['mean_correlation']:+.3f} | "
                            f"{corr_stats['std_correlation']:.3f} | "
                            f"[{corr_stats['min_correlation']:+.3f}, {corr_stats['max_correlation']:+.3f}] | "
                            f"{corr_stats['weeks_significant']}/{len(results_df)} | "
                            f"{corr_stats['predictive_power']} |\n"
                        )
                    
                    f.write("\n**Interpretation:**\n")
                    f.write("- **Mean Corr**: Average correlation with home wins (higher = more predictive)\n")
                    f.write("- **Std Dev**: Consistency across weeks (lower = more stable)\n")
                    f.write("- **Weeks Sig**: Weeks with |correlation| > 0.1 (meaningful signal)\n")
                    f.write("- **Power**: STRONG (>0.15), MODERATE (0.08-0.15), WEAK (0.05-0.08), NONE (<0.05)\n\n")
                    
                    # Correlation vs Importance Comparison
                    if feature_stats:
                        f.write("### Correlation vs Importance Comparison\n\n")
                        f.write("Features with HIGH importance but LOW correlation may indicate:\n")
                        f.write("- Interaction effects (feature works in combination with others)\n")
                        f.write("- Non-linear relationships\n")
                        f.write("- Overfitting to training data\n\n")
                        
                        f.write("| Feature | XGBoost Importance | Correlation | Discrepancy |\n")
                        f.write("|---------|-------------------|-------------|-------------|\n")
                        
                        # Find features with high importance but low correlation
                        discrepancies = []
                        for feature in feature_stats.keys():
                            if feature in correlation_stats:
                                importance = feature_stats[feature]['mean']
                                correlation = abs(correlation_stats[feature]['mean_correlation'])
                                
                                # High importance (>0.02) but low correlation (<0.08)
                                if importance > 0.02 and correlation < 0.08:
                                    discrepancies.append((feature, importance, correlation_stats[feature]['mean_correlation']))
                        
                        # Sort by importance
                        discrepancies.sort(key=lambda x: x[1], reverse=True)
                        
                        for feature, importance, correlation in discrepancies[:10]:
                            status = "⚠️ HIGH IMPORTANCE, LOW CORRELATION" if importance > 0.04 else "⚠️ Moderate discrepancy"
                            f.write(f"| {feature} | {importance:.4f} | {correlation:+.3f} | {status} |\n")
                        
                        if not discrepancies:
                            f.write("| *No significant discrepancies found* | - | - | ✓ Good alignment |\n")
                        
                        f.write("\n")
                    
                    # Injury Feature Specific Analysis
                    injury_features = [f for f in correlation_stats.keys()
                                     if 'injury' in f.lower() or 'qb_available' in f.lower()]
                    
                    if injury_features:
                        f.write("### Injury Feature Performance\n\n")
                        f.write("| Feature | Mean Corr | Importance | Status | Recommendation |\n")
                        f.write("|---------|-----------|------------|--------|----------------|\n")
                        
                        for feature in injury_features:
                            corr_stats = correlation_stats[feature]
                            importance = feature_stats.get(feature, {}).get('mean', 0.0) if feature_stats else 0.0
                            power = corr_stats['predictive_power']
                            
                            if power == "NONE":
                                recommendation = "❌ REMOVE"
                            elif power == "WEAK":
                                recommendation = "⚠️ INVESTIGATE"
                            else:
                                recommendation = "✓ KEEP"
                            
                            f.write(
                                f"| {feature} | {corr_stats['mean_correlation']:+.3f} | "
                                f"{importance:.4f} | {power} | {recommendation} |\n"
                            )
                        
                        f.write("\n**Assessment:**\n")
                        none_count = sum(1 for f in injury_features
                                       if correlation_stats[f]['predictive_power'] == "NONE")
                        if none_count == len(injury_features):
                            f.write("- ❌ ALL injury features show ZERO predictive power\n")
                            f.write("- Model ignores these features in favor of rolling performance metrics\n")
                            f.write("- **Recommendation: Remove all injury features from feature set**\n")
                        elif none_count > 0:
                            f.write(f"- ⚠️ {none_count}/{len(injury_features)} injury features show no predictive power\n")
                            f.write("- Consider removing low-performing injury features\n")
                        else:
                            f.write("- ✓ Injury features show some predictive power\n")
                        
                        f.write("\n")
                    
                    f.write("---\n\n")
                else:
                    f.write("## Feature Correlation Analysis\n\n")
                    f.write("*Correlation data not available for this run.*\n\n")
                    f.write("---\n\n")
            
            # Miss Analysis
            if miss_df is not None and not miss_df.empty:
                f.write("## Miss Analysis\n\n")
                f.write("Analysis of incorrect predictions to identify patterns in model failures.\n\n")
                
                f.write(f"**Total Misses:** {len(miss_df)}\n")
                f.write(f"**Average Confidence on Misses:** {miss_df['confidence'].mean():.1%}\n\n")
                
                # High confidence misses
                high_conf_misses = miss_df[miss_df['confidence'] > 0.7]
                if not high_conf_misses.empty:
                    f.write(f"### ⚠️ High Confidence Misses (>70%)\n\n")
                    f.write("| Week | Game | Pred | Actual | Conf | Top Factor |\n")
                    f.write("|------|------|------|--------|------|------------|\n")
                    
                    for _, row in high_conf_misses.sort_values('confidence', ascending=False).head(10).iterrows():
                        game_str = f"{row['away_team']} @ {row['home_team']}"
                        f.write(f"| {row['week']} | {game_str} | {row['predicted_winner']} | {row['actual_winner']} | {row['confidence']:.1%} | {row['top_factor_1']} |\n")
                    
                    f.write("\n")
                
                f.write("---\n\n")

            # Comparison to Historical Performance
            f.write("## Comparison to Historical Performance\n\n")
            f.write("| Metric | Historical (2023) | Current ({}) | Change |\n".format(TEST_YEAR))
            f.write("|--------|-------------------|--------------|--------|\n")
            f.write(f"| Mean Accuracy | 63.8% | {acc_mean:.1%} | {(acc_mean - 0.638):+.1%} {'✓' if acc_mean > 0.638 else '⚠️'} |\n")
            f.write(f"| Accuracy Range | 37.1 pp | {acc_range * 100:.1f} pp | {(acc_range * 100 - 37.1):+.1f} pp {'✓' if acc_range < 0.371 else '⚠️'} |\n")
            f.write(f"| Weeks Beating Home | 66.7% | {weeks_beating_home/len(results_df):.1%} | {(weeks_beating_home/len(results_df) - 0.667):+.1%} {'✓' if weeks_beating_home/len(results_df) > 0.667 else '⚠️'} |\n")
            f.write(f"| Mean AUC | 0.638 | {results_df['auc'].mean():.3f} | {(results_df['auc'].mean() - 0.638):+.3f} {'✓' if results_df['auc'].mean() > 0.638 else '⚠️'} |\n\n")
            
            if acc_range < 0.371:
                f.write("**Assessment:** ✓ IMPROVED - Stability improved compared to historical baseline\n\n")
            else:
                f.write("**Assessment:** ⚠️ SIMILAR - Stability comparable to historical baseline\n\n")
            
            f.write("---\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            f.write("### Immediate Actions\n")
            
            if overall_assessment == "✓ PRODUCTION READY":
                f.write("1. ✓ **Deploy to Production** - Model shows excellent performance\n")
            elif overall_assessment == "⚠️ NEEDS MONITORING":
                f.write("1. ⚠️ **Deploy with Monitoring** - Model shows acceptable performance but requires monitoring\n")
            else:
                f.write("1. ❌ **Do Not Deploy** - Model requires improvements before production\n")
            
            if unstable_count > 0:
                f.write(f"2. ⚠️ **Monitor Unstable Features** - Track {unstable_count} high-variance features weekly\n")
            
            f.write("3. ⚠️ **Review Feature Correlations** - Consider removing redundant features\n\n")
            
            f.write("### Future Improvements\n")
            if unstable_count > 0:
                f.write(f"1. Investigate unstable features (CV ≥ 0.5) for potential removal\n")
            f.write("2. Add feature interaction terms for top 5 features\n")
            f.write("3. Implement ensemble methods to reduce variance\n")
            f.write("4. Collect more data for low-sample features\n\n")
            
            f.write("---\n\n")
            f.write(f"*Generated by validate_weekly.py on {metadata['run_date']}*\n")
        
        return report_path
    
    # Note: Previous run comparison has been removed since we no longer save
    # intermediate CSV/JSON files. Historical comparison can be added to the
    # markdown report if needed by parsing previous markdown reports.
    
    # Calculate unstable_count for markdown report
    unstable_count = 0
    if feature_stats:
        unstable_count = sum(1 for _, s in feature_stats.items() if s['cv'] >= 0.5)
    
    # Generate markdown report
    report_path = create_markdown_report(
        results_df=results_df,
        metadata=metadata,
        timestamp=timestamp,
        feature_stats=feature_stats if feature_importance_by_week else None,
        correlation_stats=correlation_stats,
        stability_grade=stability_grade,
        reliability_grade=reliability_grade,
        baseline_grade=baseline_grade,
        overall_assessment=overall,
        weeks_below_random=weeks_below_random,
        weeks_beating_home=weeks_beating_home,
        acc_range=acc_range,
        acc_mean=acc_mean,
        acc_std=acc_std,
        stability_ratio=stability_ratio,
        auc_min=auc_min,
        auc_max=auc_max,
        bias_min=bias_min,
        bias_max=bias_max,
        bias_range=bias_range,
        unstable_count=unstable_count,
        miss_df=analyze_misses(results, logger)
    )
    logger.info(f"✓ Markdown report saved to: {report_path}")
    
    # Add execution summary
    duration = time.time() - start_time
    logger.info("")
    logger.info("="*80)
    logger.info("EXECUTION SUMMARY")
    logger.info("="*80)
    logger.info(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    logger.info(f"📁 Report: {report_path}")
    logger.info(f"🆔 Run ID: {timestamp}")
    logger.info("="*80)
    
    return results_df


if __name__ == "__main__":
    validate_weekly()