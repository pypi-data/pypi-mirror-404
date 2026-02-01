"""
Pre-validate proposed interaction features against collinearity threshold.

Run this BEFORE implementing features to predict if they'll survive Gauntlet Stage 2.

Usage:
    python scripts/diagnostics/validate_feature_nonlinearity.py

Example Test Formulas:
    test_formulas = {
        'epa_dome_poly': '(rolling_8g_epa_offense_diff * is_dome) ** 2',
        'simple_multiply': 'rolling_4g_point_diff_diff * is_conference_game',
    }
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from commonv2.persistence.bucket_adapter import get_bucket_adapter

def test_feature_formulas(
    formulas: Dict[str, str],
    test_season: int = 2024,
    correlation_threshold: float = 0.90
) -> Dict[str, Dict]:
    """
    Test proposed feature formulas against existing features.
    
    Args:
        formulas: Dict of {feature_name: python_formula_string}
        test_season: Season to test on
        correlation_threshold: Gauntlet filter threshold (0.90 = will be dropped)
    
    Returns:
        Dict of {feature_name: {'max_corr': float, 'corr_with': str, 'status': str}}
    """
    bucket = get_bucket_adapter()
    
    # Load game-level data with all existing features
    filters = [('season', '==', test_season)]
    
    print(f"\n{'='*70}")
    print(f"LOADING DATA: Season {test_season}")
    print(f"{'='*70}\n")
    
    # Load rolling metrics (team-level)
    rolling_df = bucket.read_data('rolling_metrics_v1', 'features', filters=filters)
    print(f"✓ Loaded rolling metrics: {len(rolling_df)} rows")
    
    # Load contextual features (game-level)
    contextual_df = bucket.read_data('contextual_features_v1', 'features', filters=filters)
    print(f"✓ Loaded contextual features: {len(contextual_df)} rows")
    
    # Load dim_game for game structure
    dim_game = bucket.read_data('dim_game', 'warehouse', filters=filters)
    print(f"✓ Loaded dim_game: {len(dim_game)} games")
    
    # Merge to create game-level dataset (simplified version of prepare_data)
    game_df = dim_game[['game_id', 'season', 'week', 'home_team', 'away_team']].copy()
    
    # Merge rolling metrics for home team
    home_rolling = rolling_df.rename(columns={
        col: f'home_{col}' for col in rolling_df.columns
        if col not in ['game_id', 'season', 'week', 'team']
    })
    game_df = game_df.merge(
        home_rolling,
        left_on=['game_id', 'season', 'week', 'home_team'],
        right_on=['game_id', 'season', 'week', 'team'],
        how='inner'
    ).drop(columns=['team'], errors='ignore')
    
    # Merge rolling metrics for away team
    away_rolling = rolling_df.rename(columns={
        col: f'away_{col}' for col in rolling_df.columns
        if col not in ['game_id', 'season', 'week', 'team']
    })
    game_df = game_df.merge(
        away_rolling,
        left_on=['game_id', 'season', 'week', 'away_team'],
        right_on=['game_id', 'season', 'week', 'team'],
        how='inner'
    ).drop(columns=['team'], errors='ignore')
    
    # Merge contextual features
    game_df = game_df.merge(contextual_df, on=['game_id', 'season', 'week'], how='left')
    
    print(f"✓ Merged dataset: {len(game_df)} games, {len(game_df.columns)} columns")
    
    # Create differentials (needed for formulas)
    diff_features = [
        'rolling_4g_epa_offense', 'rolling_4g_point_diff', 
        'rolling_8g_epa_offense', 'rolling_8g_epa_offense_std',
        'rolling_4g_epa_defense_std', 'recent_4g_win_rate'
    ]
    for feat in diff_features:
        if f'home_{feat}' in game_df.columns and f'away_{feat}' in game_df.columns:
            game_df[f'{feat}_diff'] = game_df[f'home_{feat}'] - game_df[f'away_{feat}']
    
    # Get list of all existing features (for correlation check)
    existing_features = [
        col for col in game_df.columns
        if col.endswith('_diff') or col.startswith('is_') or col.startswith('stadium_')
           or col.startswith('rolling_') or col.startswith('rest_')
    ]
    
    print(f"\n{'='*70}")
    print(f"PRE-VALIDATION: Testing {len(formulas)} proposed features")
    print(f"Dataset: {test_season} season, {len(game_df)} games")
    print(f"Existing features to check against: {len(existing_features)}")
    print(f"Gauntlet threshold: correlation >{correlation_threshold} = FILTERED")
    print(f"{'='*70}\n")
    
    results = {}
    
    for feature_name, formula in formulas.items():
        try:
            # Create the feature using eval (SAFE: controlled environment, known vars)
            game_df[feature_name] = eval(formula, {"np": np}, game_df.to_dict('series'))
            
            # Calculate variance
            std = game_df[feature_name].std()
            
            # Calculate correlation with ALL existing features
            max_corr = 0.0
            max_corr_with = None
            
            for existing_feat in existing_features:
                if existing_feat in game_df.columns and existing_feat != feature_name:
                    corr = abs(game_df[[feature_name, existing_feat]].corr().iloc[0, 1])
                    if corr > abs(max_corr):
                        max_corr = corr
                        max_corr_with = existing_feat
            
            # Determine status
            if max_corr >= correlation_threshold:
                status = "❌ FAIL - Will be filtered"
                risk_level = "HIGH RISK"
            elif 0.85 <= max_corr < correlation_threshold:
                status = "🟡 RISKY - Might survive"
                risk_level = "MEDIUM RISK"
            else:
                status = "✅ PASS - Will survive"
                risk_level = "LOW RISK"
            
            results[feature_name] = {
                'max_corr': max_corr,
                'corr_with': max_corr_with,
                'std': std,
                'status': status,
                'risk_level': risk_level
            }
            
            # Print result
            print(f"{feature_name}:")
            print(f"  Formula: {formula}")
            print(f"  Std Dev: {std:.4f}")
            print(f"  Max Correlation: {max_corr:.3f} (with {max_corr_with})")
            print(f"  Status: {status}")
            print(f"  Risk: {risk_level}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR testing {feature_name}:")
            print(f"   {str(e)}")
            print()
            results[feature_name] = {
                'max_corr': None,
                'corr_with': None,
                'std': None,
                'status': f"ERROR: {str(e)}",
                'risk_level': 'UNKNOWN'
            }
    
    # Summary
    pass_count = sum(1 for r in results.values() if r['status'].startswith('✅'))
    risky_count = sum(1 for r in results.values() if r['status'].startswith('🟡'))
    fail_count = sum(1 for r in results.values() if r['status'].startswith('❌'))
    
    print(f"\n{'='*70}")
    print(f"SUMMARY:")
    print(f"  ✅ PASS (corr <0.85): {pass_count}/{len(formulas)} - Safe to implement")
    print(f"  🟡 RISKY (0.85-0.90): {risky_count}/{len(formulas)} - Test carefully")
    print(f"  ❌ FAIL (corr >0.90): {fail_count}/{len(formulas)} - Will be filtered")
    print(f"{'='*70}\n")
    
    print("DECISION GUIDE:")
    print("  ✅ PASS: Proceed with implementation")
    print("  🟡 RISKY: Consider stronger transforms (higher polynomial, different threshold)")
    print("  ❌ FAIL: Revise formula - use polynomial/log/threshold transforms")
    print()
    
    return results


# Example usage
if __name__ == "__main__":
    # Test the formulas from Phase 2
    test_formulas = {
        # Phase 2 formulas (revised with non-linear transforms) - SHOULD PASS
        'epa_dome_poly_interaction': '(rolling_8g_epa_offense_diff * is_dome) ** 2',
        'conference_threshold_intensity': '((rolling_4g_point_diff_diff > 3).astype(float) * is_conference_game)',
        'rest_performance_ratio': 'rest_days_diff / (home_rolling_4g_epa_offense_std + home_rolling_4g_epa_defense_std + 0.01)',
        'stadium_form_log_synergy': '(np.log(stadium_home_win_rate * 100 + 1) * recent_4g_win_rate_diff)',
        
        # COUNTER-EXAMPLE: Simple multiplication (known to fail) - SHOULD FAIL
        'simple_epa_dome': 'rolling_8g_epa_offense_diff * is_dome',
        
        # NEW: Additional test formulas
        'epa_cubed': 'rolling_8g_epa_offense_diff ** 3',  # Should pass (strong non-linearity)
        'binary_and': '(is_dome.astype(float) * is_conference_game.astype(float))',  # Should pass (interaction of两 binaries)
    }
    
    print("\n" + "="*70)
    print("FEATURE NON-LINEARITY PRE-VALIDATION")
    print("="*70)
    
    results = test_feature_formulas(test_formulas, test_season=2024)
    
    # Print actionable recommendations
    print("\nACTIONABLE RECOMMENDATIONS:")
    print("-" * 70)
    
    for fname, result in results.items():
        if result['status'].startswith('❌'):
            print(f"\n{fname}:")
            print(f"  ❌ Will be filtered (corr={result['max_corr']:.3f})")
            print(f"  💡 Try: Add polynomial transform (^2 or ^3)")
            print(f"  💡 Try: Add threshold condition (>cutoff)")
            print(f"  💡 Try: Use log/exp transformation")
        elif result['status'].startswith('✅'):
            print(f"\n{fname}:")
            print(f"  ✅ Safe to implement (corr={result['max_corr']:.3f})")