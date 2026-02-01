"""
Debug Rest Days Calculation

Investigates the rest_days_diff bug where range is [-294, 288] days.
This is clearly wrong - teams don't have 294 days between games.

Expected range: [-14, 14] days (max difference is bye week vs short week)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from commonv2.core.logging import get_logger


def debug_rest_days():
    """Debug the rest_days_diff calculation to find the bug."""
    logger = get_logger(__name__)
    
    logger.info("="*80)
    logger.info("REST DAYS DIFFERENTIAL DEBUG")
    logger.info("="*80)
    logger.info("")
    
    # Load contextual features
    from commonv2.persistence.bucket_adapter import get_bucket_adapter
    
    bucket_adapter = get_bucket_adapter(logger=logger)
    
    logger.info("📊 Loading contextual features...")
    df = bucket_adapter.read_data('contextual_features_v1', 'features')
    logger.info(f"✓ Loaded {len(df):,} games")
    logger.info("")
    
    # Analyze rest_days_diff
    logger.info("="*80)
    logger.info("REST DAYS DIFFERENTIAL ANALYSIS")
    logger.info("="*80)
    logger.info("")
    
    logger.info(f"Statistics:")
    logger.info(f"  Mean: {df['rest_days_diff'].mean():.2f} days")
    logger.info(f"  Median: {df['rest_days_diff'].median():.2f} days")
    logger.info(f"  Std: {df['rest_days_diff'].std():.2f} days")
    logger.info(f"  Min: {df['rest_days_diff'].min():.0f} days")
    logger.info(f"  Max: {df['rest_days_diff'].max():.0f} days")
    logger.info(f"  Range: [{df['rest_days_diff'].min():.0f}, {df['rest_days_diff'].max():.0f}]")
    logger.info("")
    
    # Find extreme values
    logger.info("🔍 Finding extreme values...")
    logger.info("")
    
    # Most negative (away team had way more rest)
    logger.info("Top 5 MOST NEGATIVE rest_days_diff (away team had much more rest):")
    extreme_negative = df.nsmallest(5, 'rest_days_diff')[
        ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team', 
         'home_rest_days', 'away_rest_days', 'rest_days_diff']
    ]
    logger.info(f"\n{extreme_negative.to_string()}")
    logger.info("")
    
    # Most positive (home team had way more rest)
    logger.info("Top 5 MOST POSITIVE rest_days_diff (home team had much more rest):")
    extreme_positive = df.nlargest(5, 'rest_days_diff')[
        ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team',
         'home_rest_days', 'away_rest_days', 'rest_days_diff']
    ]
    logger.info(f"\n{extreme_positive.to_string()}")
    logger.info("")
    
    # Analyze home_rest_days and away_rest_days separately
    logger.info("="*80)
    logger.info("HOME REST DAYS ANALYSIS")
    logger.info("="*80)
    logger.info("")
    logger.info(f"Statistics:")
    logger.info(f"  Mean: {df['home_rest_days'].mean():.2f} days")
    logger.info(f"  Median: {df['home_rest_days'].median():.2f} days")
    logger.info(f"  Min: {df['home_rest_days'].min():.0f} days")
    logger.info(f"  Max: {df['home_rest_days'].max():.0f} days")
    logger.info("")
    
    logger.info("Top 5 longest home rest periods:")
    longest_home = df.nlargest(5, 'home_rest_days')[
        ['game_id', 'season', 'week', 'game_date', 'home_team', 'home_last_game', 'home_rest_days']
    ]
    logger.info(f"\n{longest_home.to_string()}")
    logger.info("")
    
    logger.info("="*80)
    logger.info("AWAY REST DAYS ANALYSIS")
    logger.info("="*80)
    logger.info("")
    logger.info(f"Statistics:")
    logger.info(f"  Mean: {df['away_rest_days'].mean():.2f} days")
    logger.info(f"  Median: {df['away_rest_days'].median():.2f} days")
    logger.info(f"  Min: {df['away_rest_days'].min():.0f} days")
    logger.info(f"  Max: {df['away_rest_days'].max():.0f} days")
    logger.info("")
    
    logger.info("Top 5 longest away rest periods:")
    longest_away = df.nlargest(5, 'away_rest_days')[
        ['game_id', 'season', 'week', 'game_date', 'away_team', 'away_last_game', 'away_rest_days']
    ]
    logger.info(f"\n{longest_away.to_string()}")
    logger.info("")
    
    # Check for cross-season contamination
    logger.info("="*80)
    logger.info("CROSS-SEASON CONTAMINATION CHECK")
    logger.info("="*80)
    logger.info("")
    
    # Find games where rest_days > 100 (likely cross-season)
    long_rest = df[df['rest_days_diff'].abs() > 100].copy()
    
    if len(long_rest) > 0:
        logger.warning(f"⚠️  Found {len(long_rest)} games with |rest_days_diff| > 100 days")
        logger.warning("   This suggests cross-season contamination!")
        logger.warning("")
        logger.warning("Sample of problematic games:")
        sample = long_rest.head(10)[
            ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team',
             'home_last_game', 'away_last_game', 'home_rest_days', 'away_rest_days', 'rest_days_diff']
        ]
        logger.warning(f"\n{sample.to_string()}")
        logger.warning("")
        logger.warning("🐛 BUG IDENTIFIED:")
        logger.warning("   The groupby('home_team') and groupby('away_team') calculations")
        logger.warning("   are NOT grouped by season, causing cross-season contamination.")
        logger.warning("")
        logger.warning("   For example, if a team's last game in 2023 was Week 18,")
        logger.warning("   and their first game in 2024 is Week 1, the calculation")
        logger.warning("   treats this as ~240 days rest instead of resetting.")
        logger.warning("")
        logger.warning("FIX:")
        logger.warning("   Change groupby('home_team') → groupby(['home_team', 'season'])")
        logger.warning("   Change groupby('away_team') → groupby(['away_team', 'season'])")
    else:
        logger.info("✓ No extreme rest days found - calculation looks correct")
    
    logger.info("")
    logger.info("="*80)
    logger.info("DIAGNOSIS COMPLETE")
    logger.info("="*80)
    
    return df


if __name__ == "__main__":
    debug_rest_days()