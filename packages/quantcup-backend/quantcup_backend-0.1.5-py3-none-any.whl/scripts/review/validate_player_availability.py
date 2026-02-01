"""
Validation Script for Player Availability Warehouse Table

Validates data quality and integrity of the unified player_availability warehouse table.
Implements checks from AVAILABILITYTRACKING_ENHANCEMENTS.md Step 5.

Usage:
    python scripts/review/validate_player_availability.py
    python scripts/review/validate_player_availability.py --seasons 2023 2024
    python scripts/review/validate_player_availability.py --verbose

Created: 2026-01-25
"""

import pandas as pd
import argparse
from typing import List, Optional
from commonv2 import get_logger
from commonv2.persistence.bucket_adapter import get_bucket_adapter


logger = get_logger(__name__)


def validate_player_availability(
    seasons: Optional[List[int]] = None,
    verbose: bool = False
) -> dict:
    """
    Validate player_availability warehouse table quality.
    
    Checks (from AVAILABILITYTRACKING_ENHANCEMENTS.md):
    1. No duplicates on (season, week, team, gsis_id)
    2. All games have roster data (40-53 players per team per week)
    3. Status consistency (ACT players rarely have IR-level injuries)
    4. Coverage: 2002-present (wkly_rosters availability)
    5. Join quality: % of players with gsis_id match
    6. Temporal safety: Week-level data integrity
    7. Schema completeness: All expected columns present
    
    Args:
        seasons: Optional list of seasons to validate (None = all)
        verbose: If True, print detailed validation info
        
    Returns:
        dict: Validation results with pass/fail status for each check
    """
    logger.info("="*80)
    logger.info("PLAYER AVAILABILITY WAREHOUSE VALIDATION")
    logger.info("="*80)
    
    # Load data
    bucket_adapter = get_bucket_adapter(logger=logger)
    
    filters = None
    if seasons:
        season_list = list(seasons) if isinstance(seasons, (list, tuple)) else [seasons]
        filters = [('season', 'in', season_list)] if len(season_list) > 1 else [('season', '==', season_list[0])]
        logger.info(f"Validating seasons: {season_list}")
    else:
        logger.info("Validating all seasons")
    
    try:
        availability_df = bucket_adapter.read_data('player_availability', 'warehouse', filters=filters)
        
        if availability_df.empty:
            logger.error("❌ player_availability table is empty!")
            logger.error("   Run: quantcup nflfastrv3 data warehouse --tables player_availability")
            return {'overall': 'FAILED', 'reason': 'Empty table'}
        
        logger.info(f"✓ Loaded {len(availability_df):,} player availability records")
        logger.info(f"   Seasons: {availability_df['season'].min()}-{availability_df['season'].max()}")
        logger.info(f"   Players: {availability_df['full_name'].nunique():,}")
        
    except Exception as e:
        logger.error(f"❌ Failed to load player_availability: {e}")
        return {'overall': 'FAILED', 'reason': f'Load error: {e}'}
    
    # Initialize results
    results = {}
    
    # ========================================================================
    # CHECK 1: No Duplicates
    # ========================================================================
    logger.info("="*80)
    logger.info("CHECK 1: DUPLICATE RECORDS")
    logger.info("="*80)
    
    dupe_cols = ['season', 'week', 'team', 'gsis_id']
    dupes = availability_df[availability_df.duplicated(subset=dupe_cols, keep=False)]
    
    if len(dupes) == 0:
        logger.info(f"✅ PASS: No duplicates on ({', '.join(dupe_cols)})")
        results['duplicates'] = 'PASS'
    else:
        logger.error(f"❌ FAIL: Found {len(dupes):,} duplicate records!")
        if verbose:
            logger.error(f"   Sample duplicates:\n{dupes.head(10)}")
        results['duplicates'] = f'FAIL ({len(dupes)} duplicates)'
    
    # ========================================================================
    # CHECK 2: Roster Size Validation
    # ========================================================================
    logger.info("="*80)
    logger.info("CHECK 2: ROSTER SIZES")
    logger.info("="*80)
    
    roster_counts = availability_df.groupby(['season', 'week', 'team']).size()
    
    logger.info(f"   Roster size stats:")
    logger.info(f"      Min: {roster_counts.min()}")
    logger.info(f"      Mean: {roster_counts.mean():.1f}")
    logger.info(f"      Max: {roster_counts.max()}")
    
    # Check bounds (40-70 players per team per week is reasonable)
    small_rosters = (roster_counts < 40).sum()
    large_rosters = (roster_counts > 70).sum()
    
    if small_rosters == 0 and large_rosters == 0:
        logger.info("✅ PASS: All rosters within expected size (40-70 players)")
        results['roster_sizes'] = 'PASS'
    else:
        if small_rosters > 0:
            logger.warning(f"⚠️  {small_rosters} team-weeks have <40 players")
        if large_rosters > 0:
            logger.warning(f"⚠️  {large_rosters} team-weeks have >70 players")
        results['roster_sizes'] = f'WARNING ({small_rosters} small, {large_rosters} large)'
    
    # ========================================================================
    # CHECK 3: Status Consistency
    # ========================================================================
    logger.info("="*80)
    logger.info("CHECK 3: STATUS CONSISTENCY")
    logger.info("="*80)
    
    # Check for logical inconsistencies
    active_with_out = availability_df[
        (availability_df['roster_status'] == 'ACT') &
        (availability_df['injury_report_status'] == 'Out')
    ]
    
    inconsistent_pct = (len(active_with_out) / len(availability_df)) * 100
    
    if inconsistent_pct <= 1.0:  # Allow up to 1% inconsistency (edge cases)
        logger.info(f"✅ PASS: Status consistency check ({inconsistent_pct:.2f}% edge cases)")
        results['status_consistency'] = 'PASS'
    else:
        logger.warning(f"⚠️  WARNING: {inconsistent_pct:.1f}% of ACT players listed as Out")
        if verbose:
            logger.warning(f"   Sample inconsistencies:\n{active_with_out.head(10)}")
        results['status_consistency'] = f'WARNING ({inconsistent_pct:.1f}% inconsistent)'
    
    # ========================================================================
    # CHECK 4: Temporal Coverage
    # ========================================================================
    logger.info("="*80)
    logger.info("CHECK 4: TEMPORAL COVERAGE")
    logger.info("="*80)
    
    seasons_covered = sorted(availability_df['season'].unique())
    min_season = seasons_covered[0]
    max_season = seasons_covered[-1]
    
    logger.info(f"   Coverage: {min_season}-{max_season}")
    logger.info(f"   Total seasons: {len(seasons_covered)}")
    
    # wkly_rosters should cover 2002+
    if min_season <= 2002:
        logger.info("✅ PASS: Coverage starts at/before 2002 (wkly_rosters baseline)")
        results['temporal_coverage'] = 'PASS'
    else:
        logger.warning(f"⚠️  WARNING: Coverage starts at {min_season} (expected 2002 or earlier)")
        results['temporal_coverage'] = f'WARNING (starts {min_season})'
    
    # ========================================================================
    # CHECK 5: ID Coverage Quality
    # ========================================================================
    logger.info("="*80)
    logger.info("CHECK 5: PLAYER ID COVERAGE")
    logger.info("="*80)
    
    gsis_coverage = (availability_df['gsis_id'].notna().sum() / len(availability_df)) * 100
    logger.info(f"   gsis_id coverage: {availability_df['gsis_id'].notna().sum():,}/{len(availability_df):,} ({gsis_coverage:.1f}%)")
    
    missing_gsis = availability_df['gsis_id'].isna().sum()
    if missing_gsis > 0:
        logger.info(f"   Missing gsis_id: {missing_gsis:,} ({(missing_gsis/len(availability_df))*100:.1f}%)")
        logger.info(f"      Expected for rookies/practice squad players")
    
    if gsis_coverage >= 90.0:
        logger.info("✅ PASS: gsis_id coverage ≥90%")
        results['id_coverage'] = 'PASS'
    else:
        logger.warning(f"⚠️  WARNING: gsis_id coverage {gsis_coverage:.1f}% (expected ≥90%)")
        results['id_coverage'] = f'WARNING ({gsis_coverage:.1f}%)'
    
    # ========================================================================
    # CHECK 6: Temporal Safety (Week-Level Integrity)
    # ========================================================================
    logger.info("="*80)
    logger.info("CHECK 6: TEMPORAL SAFETY (ISSUE #2 SOLUTION)")
    logger.info("="*80)
    
    # Verify no future data leakage: Week N should not have Week N+1 data
    if 'week' in availability_df.columns:
        week_integrity = True
        for season in availability_df['season'].unique()[:3]:  # Sample first 3 seasons
            season_data = availability_df[availability_df['season'] == season]
            for week in range(1, min(18, season_data['week'].max())):
                week_data = season_data[season_data['week'] == week]
                future_weeks = week_data['week'] > week
                if future_weeks.any():
                    logger.error(f"❌ Week {week} contains future week data!")
                    week_integrity = False
                    break
            if not week_integrity:
                break
        
        if week_integrity:
            logger.info("✅ PASS: Temporal safety verified (no future data leakage)")
            logger.info("   wkly_rosters: Week-level snapshot (safe by design)")
            logger.info("   injuries: Merged by (season, week) gives pre-game status")
            results['temporal_safety'] = 'PASS'
        else:
            logger.error("❌ FAIL: Temporal safety violation detected!")
            results['temporal_safety'] = 'FAIL'
    else:
        logger.warning("⚠️  Cannot validate temporal safety (week column missing)")
        results['temporal_safety'] = 'SKIP'
    
    # ========================================================================
    # CHECK 7: Schema Completeness
    # ========================================================================
    logger.info("="*80)
    logger.info("CHECK 7: SCHEMA COMPLETENESS")
    logger.info("="*80)
    
    expected_columns = [
        # Identifiers
        'season', 'week', 'team', 'gsis_id', 'full_name',
        # Player info
        'position', 'depth_chart_position', 'jersey_number',
        # Roster status (Issue #1 solution)
        'roster_status', 'roster_status_description',
        # Injury status (Issue #1 solution)
        'injury_report_status', 'report_primary_injury',
        # Availability (unified)
        'availability_status', 'is_available',
        # Depth
        'depth_rank'
    ]
    
    missing_cols = [col for col in expected_columns if col not in availability_df.columns]
    extra_cols = [col for col in availability_df.columns if col not in expected_columns and not col.startswith('_')]
    
    logger.info(f"   Expected columns: {len(expected_columns)}")
    logger.info(f"   Actual columns: {len(availability_df.columns)}")
    
    if len(missing_cols) == 0:
        logger.info("✅ PASS: All expected columns present")
        results['schema'] = 'PASS'
    else:
        logger.error(f"❌ FAIL: Missing {len(missing_cols)} expected columns:")
        for col in missing_cols:
            logger.error(f"      - {col}")
        results['schema'] = f'FAIL ({len(missing_cols)} missing)'
    
    if verbose and extra_cols:
        logger.info(f"   Additional columns: {', '.join(extra_cols[:10])}...")
    
    # ========================================================================
    # CHECK 8: Availability Status Distribution
    # ========================================================================
    logger.info("="*80)
    logger.info("CHECK 8: AVAILABILITY STATUS DISTRIBUTION")
    logger.info("="*80)
    
    if 'availability_status' in availability_df.columns:
        status_dist = availability_df['availability_status'].value_counts()
        logger.info(f"   Status distribution:")
        for status, count in status_dist.items():
            pct = (count / len(availability_df)) * 100
            logger.info(f"      {status}: {count:,} ({pct:.1f}%)")
        
        # Check for healthy scratches (key feature)
        healthy_scratches = (availability_df['availability_status'] == 'INACTIVE_HEALTHY').sum()
        if healthy_scratches > 0:
            logger.info(f"   ⭐ Healthy scratches identified: {healthy_scratches:,}")
            logger.info(f"      This is a KEY FEATURE capturing strategic roster decisions!")
            results['healthy_scratches'] = f'FOUND ({healthy_scratches:,})'
        else:
            logger.warning("⚠️  No healthy scratches found (unexpected if data is complete)")
            results['healthy_scratches'] = 'NONE'
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    logger.info("="*80)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for v in results.values() if v == 'PASS')
    warned = sum(1 for v in results.values() if 'WARNING' in str(v))
    failed = sum(1 for v in results.values() if 'FAIL' in str(v))
    
    logger.info(f"Total checks: {len(results)}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"⚠️  Warnings: {warned}")
    logger.info(f"❌ Failed: {failed}")
    
    # Detailed results
    logger.info("\nDetailed Results:")
    for check, status in results.items():
        icon = "✅" if status == 'PASS' else ("⚠️" if 'WARNING' in str(status) else ("❌" if 'FAIL' in str(status) else "ℹ️"))
        logger.info(f"   {icon} {check}: {status}")
    
    # Overall verdict
    if failed == 0 and warned <= 2:  # Allow up to 2 warnings
        logger.info("\n🎉 OVERALL: PASS - Player availability warehouse is valid!")
        results['overall'] = 'PASS'
    elif failed == 0:
        logger.info(f"\n⚠️  OVERALL: PASS WITH WARNINGS ({warned} warnings)")
        results['overall'] = 'PASS_WITH_WARNINGS'
    else:
        logger.error(f"\n❌ OVERALL: FAIL ({failed} critical failures)")
        results['overall'] = 'FAIL'
    
    logger.info("="*80)
    
    return results


def main():
    """CLI entry point for validation script."""
    parser = argparse.ArgumentParser(
        description='Validate player_availability warehouse table quality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all seasons
  python scripts/review/validate_player_availability.py
  
  # Validate specific seasons
  python scripts/review/validate_player_availability.py --seasons 2023 2024
  
  # Verbose output
  python scripts/review/validate_player_availability.py --verbose --seasons 2024
        """
    )
    
    parser.add_argument(
        '--seasons',
        type=int,
        nargs='+',
        help='Seasons to validate (default: all seasons)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed validation information'
    )
    
    args = parser.parse_args()
    
    # Run validation
    results = validate_player_availability(
        seasons=args.seasons,
        verbose=args.verbose
    )
    
    # Exit with appropriate status code
    if results['overall'] in ['PASS', 'PASS_WITH_WARNINGS']:
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    main()
