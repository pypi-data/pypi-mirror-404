"""
Test script for player_availability_features.py

Demonstrates how to use the new PlayerAvailabilityFeatureCalculator
with the warehouse/player_availability table.

Usage:
    python scripts/test_player_availability_features.py

Expected Output:
    - QB availability features (home/away_qb_available)
    - Starter unavailability counts (by unit: offense/defense)
    - Position-weighted impact scores
    - Sample data showing Patrick Mahomes IR case (2025 weeks 16-18)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from nflfastRv3.features.ml_pipeline.feature_sets.player_availability_features import (
    PlayerAvailabilityFeatureCalculator
)
from nflfastRv3.shared.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger


def main():
    """Run test of player availability features."""
    logger = get_logger(__name__)
    
    logger.info("=" * 80)
    logger.info("TESTING PLAYER AVAILABILITY FEATURES")
    logger.info("=" * 80)
    
    # Initialize bucket adapter
    bucket_adapter = get_bucket_adapter(logger=logger)
    
    # Load warehouse/player_availability
    logger.info("\n📦 Loading warehouse/player_availability...")
    try:
        player_availability = bucket_adapter.read_data(
            'player_availability',
            'warehouse',
            filters=[('season', '==', 2025)]  # Test with 2025 season
        )
        logger.info(f"✓ Loaded {len(player_availability):,} player availability records")
        
        # Show schema
        logger.info(f"\n📋 Schema:")
        logger.info(f"   Columns: {player_availability.columns.tolist()}")
        logger.info(f"   Seasons: {player_availability['season'].unique()}")
        logger.info(f"   Weeks: {player_availability['week'].min()}-{player_availability['week'].max()}")
        
        # Show availability status distribution
        if 'availability_status' in player_availability.columns:
            status_dist = player_availability['availability_status'].value_counts()
            logger.info(f"\n   Availability status distribution:")
            for status, count in status_dist.head(10).items():
                logger.info(f"      {status}: {count:,}")
        
    except Exception as e:
        logger.error(f"❌ Failed to load player_availability: {e}")
        return
    
    # Load games (create sample if not in bucket)
    logger.info("\n📦 Loading games schedule...")
    try:
        games = bucket_adapter.read_data(
            'schedules',
            'raw_nflfastr',
            filters=[('season', '==', 2025), ('game_type', '==', 'REG')]
        )
        logger.info(f"✓ Loaded {len(games):,} games")
    except Exception as e:
        logger.warning(f"⚠️ Could not load schedules: {e}")
        logger.info("   Creating sample games DataFrame...")
        
        # Create sample games for testing
        games = pd.DataFrame({
            'game_id': [f'2025_{w:02d}_KC_{opp}' for w in range(1, 19) for opp in ['OPP']],
            'season': [2025] * 18,
            'week': list(range(1, 19)),
            'home_team': ['KC'] * 18,
            'away_team': ['OPP'] * 18
        })
        logger.info(f"   Created {len(games)} sample games")
    
    # Initialize calculator
    calculator = PlayerAvailabilityFeatureCalculator(logger=logger, debug=True)
    
    # Calculate features
    logger.info("\n🔧 Calculating availability features...")
    games_with_features = calculator.calculate_features(
        games_df=games,
        player_availability_df=player_availability
    )
    
    # Show results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    
    # Show KC games (Patrick Mahomes case)
    logger.info("\n🏈 KC GAMES (Patrick Mahomes IR case - weeks 16-18):")
    kc_games = games_with_features[games_with_features['home_team'] == 'KC'].copy()
    
    display_cols = [
        'week', 'home_qb_available', 'home_starter_unavailable',
        'home_offense_unavailable', 'home_defense_unavailable',
        'home_availability_impact'
    ]
    
    if all(col in kc_games.columns for col in display_cols):
        kc_sample = kc_games[display_cols].sort_values('week')
        logger.info(f"\n{kc_sample.to_string(index=False)}")
        
        # Highlight the issue
        weeks_16_18 = kc_sample[kc_sample['week'] >= 16]
        if len(weeks_16_18) > 0:
            qb_avail_16_18 = weeks_16_18['home_qb_available'].sum()
            if qb_avail_16_18 > 0:
                logger.warning("\n⚠️ ISSUE: QB showing as available in weeks 16-18 (Mahomes was on IR!)")
            else:
                logger.info("\n✅ CORRECT: QB unavailable in weeks 16-18 (Mahomes on IR)")
    
    # Show feature statistics
    logger.info("\n📊 FEATURE STATISTICS:")
    feature_cols = [col for col in games_with_features.columns 
                   if any(x in col for x in ['qb_available', 'unavailable', 'impact'])]
    
    for col in feature_cols:
        if col in games_with_features.columns:
            mean_val = games_with_features[col].mean()
            min_val = games_with_features[col].min()
            max_val = games_with_features[col].max()
            logger.info(f"   {col}:")
            logger.info(f"      mean={mean_val:.4f}, min={min_val:.4f}, max={max_val:.4f}")
    
    # Save results to CSV for inspection
    output_path = project_root / 'reports' / 'player_availability_test_results.csv'
    output_path.parent.mkdir(exist_ok=True, parents=True)
    games_with_features.to_csv(output_path, index=False)
    logger.info(f"\n💾 Results saved to: {output_path}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ TEST COMPLETE")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
