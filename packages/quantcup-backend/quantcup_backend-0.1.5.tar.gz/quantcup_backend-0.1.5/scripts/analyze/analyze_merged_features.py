"""
Merged Feature Correlation Analysis

Analyzes correlations between features and game outcomes using the MERGED dataset
(rolling_metrics + contextual features) exactly as the model sees it.

This addresses the concern that contextual features showed weak individual correlations.
The real test is whether they improve predictions when combined with team performance.

Usage:
    python scripts/analyze_merged_features.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from commonv2.core.logging import get_logger


def analyze_merged_features():
    """
    Analyze correlations using the merged dataset (rolling_metrics + contextual).
    
    This mimics how game_outcome.py:prepare_data() merges the features,
    allowing us to see if contextual features add predictive power when
    combined with team performance metrics.
    """
    logger = get_logger(__name__)
    
    logger.info("="*80)
    logger.info("MERGED FEATURES CORRELATION ANALYSIS")
    logger.info("="*80)
    logger.info("")
    logger.info("Purpose: Analyze contextual features in combination with rolling_metrics")
    logger.info("Method: Merge datasets exactly as game_outcome.py does, then analyze")
    logger.info("")
    
    # Load data from bucket
    from commonv2.persistence.bucket_adapter import get_bucket_adapter
    
    bucket_adapter = get_bucket_adapter(logger=logger)
    
    # Step 1: Load rolling metrics (team-level)
    logger.info("📊 Step 1: Loading rolling_metrics (team-level)...")
    rolling_df = bucket_adapter.read_data('rolling_metrics_v1', 'features')
    logger.info(f"✓ Loaded {len(rolling_df):,} team-games")
    logger.info(f"   Columns: {len(rolling_df.columns)}")
    logger.info(f"   Seasons: {rolling_df['season'].min()} - {rolling_df['season'].max()}")
    logger.info("")
    
    # Step 2: Load contextual features (game-level)
    logger.info("📊 Step 2: Loading contextual_features (game-level)...")
    contextual_df = bucket_adapter.read_data('contextual_features_v1', 'features')
    logger.info(f"✓ Loaded {len(contextual_df):,} games")
    logger.info(f"   Columns: {len(contextual_df.columns)}")
    logger.info(f"   Seasons: {contextual_df['season'].min()} - {contextual_df['season'].max()}")
    logger.info("")
    
    # Step 3: Load dim_game for target variable
    logger.info("📊 Step 3: Loading dim_game for target...")
    dim_game = bucket_adapter.read_data('dim_game', 'warehouse')
    
    # Filter to completed games
    dim_game = dim_game[
        (dim_game['home_score'].notna()) &
        (dim_game['away_score'].notna())
    ].copy()
    
    dim_game['home_team_won'] = (dim_game['home_score'] > dim_game['away_score']).astype(int)
    
    logger.info(f"✓ Loaded {len(dim_game):,} completed games")
    logger.info(f"   Home win rate: {dim_game['home_team_won'].mean():.1%}")
    logger.info("")
    
    # Step 4: Merge exactly as game_outcome.py does
    logger.info("📊 Step 4: Merging datasets (following game_outcome.py pattern)...")
    logger.info("")
    
    # 4a. Merge home team rolling metrics
    logger.info("   4a. Merging home team rolling metrics...")
    home_features = rolling_df.rename(columns={
        col: f'home_{col}' for col in rolling_df.columns
        if col not in ['game_id', 'season', 'week', 'team']
    })
    
    game_df = dim_game.merge(
        home_features,
        left_on=['game_id', 'season', 'week', 'home_team'],
        right_on=['game_id', 'season', 'week', 'team'],
        how='inner'
    ).drop(columns=['team'], errors='ignore')
    
    logger.info(f"      After home merge: {len(game_df):,} games")
    
    # 4b. Merge away team rolling metrics
    logger.info("   4b. Merging away team rolling metrics...")
    away_features = rolling_df.rename(columns={
        col: f'away_{col}' for col in rolling_df.columns
        if col not in ['game_id', 'season', 'week', 'team']
    })
    
    game_df = game_df.merge(
        away_features,
        left_on=['game_id', 'season', 'week', 'away_team'],
        right_on=['game_id', 'season', 'week', 'team'],
        how='inner'
    ).drop(columns=['team'], errors='ignore')
    
    logger.info(f"      After away merge: {len(game_df):,} games")
    
    # 4c. Merge contextual features (game-level)
    logger.info("   4c. Merging contextual features...")
    game_df = game_df.merge(
        contextual_df,
        on=['game_id', 'season', 'week'],
        how='left'
    )
    
    logger.info(f"      After contextual merge: {len(game_df):,} games")
    logger.info(f"      Total columns: {len(game_df.columns)}")
    logger.info("")
    
    # Step 5: Engineer differential features (as game_outcome.py does)
    logger.info("📊 Step 5: Engineering differential features...")
    
    from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeModel
    game_df = GameOutcomeModel.engineer_features(game_df, logger=logger)
    logger.info("")

    # Step 5b: Engineer Interaction Terms (Experimental)
    logger.info("📊 Step 5b: Engineering experimental interaction terms...")
    
    # 1. Power x Rest
    if 'rolling_16g_point_diff_diff' in game_df.columns and 'rest_days_diff' in game_df.columns:
        game_df['interaction_power_rest'] = game_df['rolling_16g_point_diff_diff'] * game_df['rest_days_diff']
        logger.info("   + Created interaction_power_rest")

    # 2. Recent Form x Home Field
    if 'recent_4g_epa_trend_diff' in game_df.columns and 'stadium_home_win_rate' in game_df.columns:
        game_df['interaction_form_home'] = game_df['recent_4g_epa_trend_diff'] * game_df['stadium_home_win_rate']
        logger.info("   + Created interaction_form_home")

    # 3. Power x Motivation (Division Game)
    if 'rolling_16g_point_diff_diff' in game_df.columns and 'is_division_game' in game_df.columns:
        game_df['interaction_power_division'] = game_df['rolling_16g_point_diff_diff'] * game_df['is_division_game']
        logger.info("   + Created interaction_power_division")
        
    # 4. Power x Late Season
    if 'rolling_16g_point_diff_diff' in game_df.columns and 'is_late_season' in game_df.columns:
        game_df['interaction_power_late'] = game_df['rolling_16g_point_diff_diff'] * game_df['is_late_season']
        logger.info("   + Created interaction_power_late")

    # 5. Momentum x Rest
    if 'momentum_advantage' in game_df.columns and 'rest_days_diff' in game_df.columns:
        game_df['interaction_momentum_rest'] = game_df['momentum_advantage'] * game_df['rest_days_diff']
        logger.info("   + Created interaction_momentum_rest")

    # 6. Trend x Division
    if 'recent_4g_epa_trend_diff' in game_df.columns and 'is_division_game' in game_df.columns:
        game_df['interaction_trend_division'] = game_df['recent_4g_epa_trend_diff'] * game_df['is_division_game']
        logger.info("   + Created interaction_trend_division")

    # 7. Offense x Weather (Precipitation)
    if 'rolling_16g_epa_offense_diff' in game_df.columns and 'is_precipitation' in game_df.columns:
        # Logic: High offense matters LESS in rain, so we expect a negative interaction or dampening effect
        game_df['interaction_offense_rain'] = game_df['rolling_16g_epa_offense_diff'] * game_df['is_precipitation']
        logger.info("   + Created interaction_offense_rain")

    # 8. EPA Advantage x Home Field
    if 'epa_advantage_8game' in game_df.columns and 'stadium_home_win_rate' in game_df.columns:
        game_df['interaction_epa_home'] = game_df['epa_advantage_8game'] * game_df['stadium_home_win_rate']
        logger.info("   + Created interaction_epa_home")

    # 9. Point Diff x Home Field
    if 'rolling_16g_point_diff_diff' in game_df.columns and 'stadium_home_win_rate' in game_df.columns:
        game_df['interaction_diff_home'] = game_df['rolling_16g_point_diff_diff'] * game_df['stadium_home_win_rate']
        logger.info("   + Created interaction_diff_home")

    logger.info("")
    
    # Step 6: Analyze correlations with home_team_won
    logger.info("="*80)
    logger.info("CORRELATION ANALYSIS: MERGED DATASET")
    logger.info("="*80)
    logger.info("")
    
    # Get all differential and contextual features
    diff_features = [col for col in game_df.columns if col.endswith('_diff')]
    
    contextual_features = [
        'rest_days_diff', 'home_short_rest', 'away_short_rest',
        'home_long_rest', 'away_long_rest',
        'is_division_game', 'is_conference_game',
        'stadium_home_win_rate', 'stadium_scoring_rate',
        'is_high_altitude', 'is_dome',
        'temp_diff_from_normal', 'is_precipitation', 'high_wind',
        'weather_passing_impact',
        'games_remaining', 'is_late_season'
    ]
    
    composite_features = ['epa_advantage_4game', 'epa_advantage_8game', 
                         'win_rate_advantage', 'momentum_advantage']
    
    interaction_features = [col for col in game_df.columns if col.startswith('interaction_')]

    # Filter to available features
    available_diff = [f for f in diff_features if f in game_df.columns]
    available_contextual = [f for f in contextual_features if f in game_df.columns]
    available_composite = [f for f in composite_features if f in game_df.columns]
    available_interaction = [f for f in interaction_features if f in game_df.columns]
    
    all_features = available_diff + available_contextual + available_composite + available_interaction
    
    logger.info(f"Analyzing {len(all_features)} features:")
    logger.info(f"  - {len(available_diff)} differential features (rolling_metrics)")
    logger.info(f"  - {len(available_contextual)} contextual features")
    logger.info(f"  - {len(available_composite)} composite features")
    logger.info(f"  - {len(available_interaction)} interaction features")
    logger.info("")
    
    # Calculate correlations
    correlations = game_df[all_features].corrwith(game_df['home_team_won']).sort_values(ascending=False)
    
    # 1. TOP FEATURES
    logger.info("="*80)
    logger.info("1. TOP 20 MOST PREDICTIVE FEATURES")
    logger.info("="*80)
    logger.info("")
    
    for i, (feat, corr) in enumerate(correlations.head(20).items(), 1):
        strength = "STRONG" if abs(corr) > 0.15 else "MODERATE" if abs(corr) > 0.08 else "WEAK"
        if feat in available_contextual: feat_type = "CONTEXTUAL"
        elif feat in available_diff: feat_type = "DIFFERENTIAL"
        elif feat in available_composite: feat_type = "COMPOSITE"
        elif feat in available_interaction: feat_type = "INTERACTION"
        else: feat_type = "UNKNOWN"
        logger.info(f"  {i:2d}. {feat:45s}: {corr:+.4f} ({strength}) [{feat_type}]")
    
    # 2. CONTEXTUAL FEATURES RANKING
    logger.info("")
    logger.info("="*80)
    logger.info("2. CONTEXTUAL FEATURES RANKING (in merged dataset)")
    logger.info("="*80)
    logger.info("")
    
    contextual_corr = correlations[correlations.index.isin(available_contextual)].sort_values(ascending=False)
    
    logger.info(f"Contextual features ranked by correlation:")
    for i, (feat, corr) in enumerate(contextual_corr.items(), 1):
        strength = "STRONG" if abs(corr) > 0.15 else "MODERATE" if abs(corr) > 0.08 else "WEAK" if abs(corr) > 0.05 else "VERY WEAK"
        
        # Find rank among all features
        overall_rank = list(correlations.index).index(feat) + 1
        
        logger.info(f"  {i:2d}. {feat:35s}: {corr:+.4f} ({strength}) [Overall rank: {overall_rank}/{len(all_features)}]")
    
    # 3. CORRELATION STRENGTH DISTRIBUTION
    logger.info("")
    logger.info("="*80)
    logger.info("3. CORRELATION STRENGTH DISTRIBUTION")
    logger.info("="*80)
    logger.info("")
    
    # Count by feature type and strength
    def categorize_strength(corr):
        abs_corr = abs(corr)
        if abs_corr > 0.15:
            return 'STRONG'
        elif abs_corr > 0.08:
            return 'MODERATE'
        elif abs_corr > 0.05:
            return 'WEAK'
        else:
            return 'VERY WEAK'
    
    # Analyze by feature type
    for feat_type, feat_list in [
        ('Differential (rolling_metrics)', available_diff),
        ('Contextual (Phase 1 & 2)', available_contextual),
        ('Composite', available_composite)
    ]:
        type_corr = correlations[correlations.index.isin(feat_list)]
        
        strong = sum(abs(type_corr) > 0.15)
        moderate = sum((abs(type_corr) > 0.08) & (abs(type_corr) <= 0.15))
        weak = sum((abs(type_corr) > 0.05) & (abs(type_corr) <= 0.08))
        very_weak = sum(abs(type_corr) <= 0.05)
        
        logger.info(f"{feat_type}:")
        logger.info(f"  STRONG (>0.15):       {strong:2d} / {len(feat_list):2d} ({strong/len(feat_list)*100:.1f}%)")
        logger.info(f"  MODERATE (0.08-0.15): {moderate:2d} / {len(feat_list):2d} ({moderate/len(feat_list)*100:.1f}%)")
        logger.info(f"  WEAK (0.05-0.08):     {weak:2d} / {len(feat_list):2d} ({weak/len(feat_list)*100:.1f}%)")
        logger.info(f"  VERY WEAK (<0.05):    {very_weak:2d} / {len(feat_list):2d} ({very_weak/len(feat_list)*100:.1f}%)")
        logger.info("")
    
    # 4. KEY INSIGHTS
    logger.info("="*80)
    logger.info("4. KEY INSIGHTS")
    logger.info("="*80)
    logger.info("")
    
    # How many contextual features are in top 20?
    top_20_features = correlations.head(20).index.tolist()
    contextual_in_top_20 = [f for f in top_20_features if f in available_contextual]
    
    logger.info(f"Contextual features in top 20: {len(contextual_in_top_20)}")
    if contextual_in_top_20:
        for feat in contextual_in_top_20:
            rank = top_20_features.index(feat) + 1
            corr = correlations[feat]
            logger.info(f"  - {feat}: rank #{rank}, r={corr:+.4f}")
    else:
        logger.info("  None - all contextual features ranked below top 20")
    
    logger.info("")
    
    # Compare contextual vs differential average correlation
    diff_avg_corr = abs(correlations[correlations.index.isin(available_diff)]).mean()
    contextual_avg_corr = abs(correlations[correlations.index.isin(available_contextual)]).mean()
    
    logger.info(f"Average absolute correlation:")
    logger.info(f"  Differential features: {diff_avg_corr:.4f}")
    logger.info(f"  Contextual features:   {contextual_avg_corr:.4f}")
    logger.info(f"  Ratio: {contextual_avg_corr/diff_avg_corr:.2f}x")
    logger.info("")
    
    # 5. RECOMMENDATION
    logger.info("="*80)
    logger.info("5. RECOMMENDATION")
    logger.info("="*80)
    logger.info("")
    
    # Count useful contextual features
    useful_contextual = sum(abs(correlations[correlations.index.isin(available_contextual)]) > 0.08)
    
    if useful_contextual == 0:
        logger.warning("⚠️  NO contextual features show moderate-to-strong correlation (>0.08)")
        logger.warning("")
        logger.warning("This suggests contextual features may not add predictive power.")
        logger.warning("However, they may still:")
        logger.warning("  1. Reduce variance through interaction effects")
        logger.warning("  2. Improve calibration (reduce home bias)")
        logger.warning("  3. Help in specific scenarios (weather, rest, etc.)")
        logger.warning("")
        logger.warning("📋 NEXT STEP: Train model and measure variance reduction")
        logger.warning("   - Baseline: 43.8 pp range (rolling_metrics only)")
        logger.warning("   - Target: 20-25 pp range (with contextual)")
        logger.warning("   - If variance doesn't improve: Consider removing weak features")
    elif useful_contextual < len(available_contextual) / 2:
        logger.info(f"⚠️  Only {useful_contextual}/{len(available_contextual)} contextual features are useful")
        logger.info("")
        logger.info("📋 RECOMMENDATION:")
        logger.info("   1. Train model with all features")
        logger.info("   2. Measure variance reduction")
        logger.info("   3. Consider removing very weak features (<0.05 correlation)")
    else:
        logger.info(f"✓ {useful_contextual}/{len(available_contextual)} contextual features show good correlation")
        logger.info("")
        logger.info("📋 RECOMMENDATION:")
        logger.info("   Proceed with model training - features look promising!")
    
    logger.info("")
    logger.info("="*80)
    
    # Save correlation analysis
    output_path = Path.cwd() / "data" / "merged_features_correlation_analysis.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    correlation_df = pd.DataFrame({
        'feature': correlations.index,
        'correlation': correlations.values,
        'abs_correlation': np.abs(correlations.values.astype(float)),
        'feature_type': [
            'CONTEXTUAL' if f in available_contextual else 'DIFFERENTIAL' if f in available_diff else 'COMPOSITE' if f in available_composite else 'INTERACTION'
            for f in correlations.index
        ],
        'strength': [
            'STRONG' if abs(c) > 0.15 else 'MODERATE' if abs(c) > 0.08 else 'WEAK' if abs(c) > 0.05 else 'VERY WEAK'
            for c in correlations.values
        ]
    })
    
    correlation_df.to_csv(output_path, index=False)
    logger.info(f"✓ Correlation analysis saved to: {output_path}")
    logger.info("")
    
    # Summary statistics
    logger.info("="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info("")
    logger.info(f"Dataset: {len(game_df):,} games")
    logger.info(f"Features analyzed: {len(all_features)}")
    logger.info(f"  - Differential: {len(available_diff)}")
    logger.info(f"  - Contextual: {len(available_contextual)}")
    logger.info(f"  - Composite: {len(available_composite)}")
    logger.info("")
    logger.info(f"Correlation strength:")
    logger.info(f"  STRONG (>0.15):       {sum(abs(correlations) > 0.15):2d} features")
    logger.info(f"  MODERATE (0.08-0.15): {sum((abs(correlations) > 0.08) & (abs(correlations) <= 0.15)):2d} features")
    logger.info(f"  WEAK (0.05-0.08):     {sum((abs(correlations) > 0.05) & (abs(correlations) <= 0.08)):2d} features")
    logger.info(f"  VERY WEAK (<0.05):    {sum(abs(correlations) <= 0.05):2d} features")
    logger.info("")
    logger.info("="*80)
    
    return correlation_df


if __name__ == "__main__":
    analyze_merged_features()