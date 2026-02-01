"""
Transform NFL.com scraped injuries (current season) to unified schema and upload to bucket.

Dynamically detects current season and uses appropriate bucket name.

Input: data/nfl_injuries_backfill/nfl_injuries_{season}_combined_*.csv
Output: Bucket path raw_nflcom_{season}/injuries/data.parquet
Schema: Matches nflverse injuries schema with 'source' = 'nflcom_scrape'
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from nflfastRv3.shared.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger
from commonv2.domain.adapters import TeamNameStandardizer


def _get_current_season() -> int:
    """
    Get current NFL season based on date.
    Matches ScheduleDataProvider logic.
    
    Returns:
        int: Current season year
    """
    now = datetime.now()
    # NFL season runs from September to February
    return now.year if now.month >= 9 else now.year - 1


def main() -> int:
    """
    Transform NFL.com injuries CSV to unified schema and upload to bucket.
    Dynamically detects current season for bucket naming.
    
    Returns:
        Exit code: 0 for success, 1 for failure
    """
    logger = get_logger('scripts.transform_nflcom_injuries')
    
    try:
        bucket_adapter = get_bucket_adapter(logger=logger)
        team_standardizer = TeamNameStandardizer()
        
        # Get current season
        current_season = _get_current_season()
        scraped_bucket = f'raw_nflcom_{current_season}'
        
        logger.info("="*80)
        logger.info(f"NFL.COM INJURIES MIGRATION TO BUCKET ({current_season})")
        logger.info("="*80)
        logger.info(f"Target bucket: {scraped_bucket}")
        
        # Find latest combined CSV for current season
        csv_dir = Path("data/nfl_injuries_backfill")
        csv_files = list(csv_dir.glob(f"nfl_injuries_{current_season}_combined_*.csv"))
        
        if not csv_files:
            logger.error(f"❌ No NFL.com combined CSV found for {current_season}!")
            logger.info(f"   Expected: data/nfl_injuries_backfill/nfl_injuries_{current_season}_combined_*.csv")
            return 1
        
        csv_file = sorted(csv_files)[-1]
        logger.info(f"📂 Loading: {csv_file}")
        raw_df = pd.read_csv(csv_file)
        logger.info(f"   Raw records: {len(raw_df):,}")
        
        # Pre-validate team names before transformation using TeamNameStandardizer
        logger.info("🔍 Validating team names...")
        unique_teams = set(raw_df['team'].unique())
        unknown_teams = []
        
        for team in unique_teams:
            standardized = team_standardizer.standardize_team_name(team)
            # If standardizer returns original name, it wasn't recognized
            if standardized == team and team not in team_standardizer.get_all_abbreviations():
                unknown_teams.append(team)
        
        if unknown_teams:
            logger.error(f"❌ Unknown team names found: {unknown_teams}")
            logger.error("   These teams are not recognized by TeamNameStandardizer")
            logger.error("   Update TeamNameStandardizer.TEAM_NAME_ALIASES in commonv2/domain/adapters.py")
            return 1
        
        logger.info(f"✓ All {len(unique_teams)} teams validated")
        
        # Handle date_modified: use column if exists, otherwise file timestamp
        if 'data_pull_end_time' in raw_df.columns:
            date_modified = pd.to_datetime(raw_df['data_pull_end_time'])
            logger.info("✓ Using data_pull_end_time column for date_modified")
        else:
            # Fallback: use file modification time
            file_mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
            date_modified = file_mtime
            logger.warning(f"⚠️  Column 'data_pull_end_time' not found")
            logger.warning(f"   Using file modification time: {file_mtime}")
        
        # Transform to unified schema using TeamNameStandardizer
        logger.info("🔄 Transforming to unified schema...")
        unified_df = pd.DataFrame({
            'season': raw_df['season'],
            'week': raw_df['week'],
            'game_type': raw_df['game_type'],
            'team': raw_df['team'].apply(team_standardizer.standardize_team_name),  # Use standardizer
            'full_name': raw_df['player_name'],
            'position': raw_df['position'],
            'report_primary_injury': raw_df['injury'],
            'report_status': raw_df['game_status'],
            'practice_status': raw_df['practice_status'],
            'date_modified': date_modified,
            'source': 'nflcom_scrape'
        })
        
        # Data quality checks
        logger.info("🔍 Running data quality checks...")
        quality_checks = {
            'null_teams': unified_df['team'].isnull().sum(),
            'null_players': unified_df['full_name'].isnull().sum(),
            'invalid_weeks': ((unified_df['week'] < 1) | (unified_df['week'] > 22)).sum(),
            'missing_positions': unified_df['position'].isnull().sum()
        }
        
        has_errors = False
        for check, count in quality_checks.items():
            if count > 0:
                logger.error(f"❌ Quality issue: {check} = {count}")
                has_errors = True
            else:
                logger.info(f"✓ {check}: OK")
        
        if has_errors:
            logger.error("❌ Data quality validation failed")
            logger.error("   Review data and fix issues before upload")
            return 1
        
        # Upload to bucket (dynamic bucket name based on season)
        logger.info(f"📦 Uploading to bucket: {scraped_bucket}/injuries")
        success = bucket_adapter.store_data(
            df=unified_df,
            table_name='injuries',
            schema=scraped_bucket
        )
        
        if success:
            logger.info("="*80)
            logger.info("✅ MIGRATION COMPLETE")
            logger.info("="*80)
            logger.info(f"Records uploaded: {len(unified_df):,}")
            logger.info(f"Season: {unified_df['season'].unique()}")
            logger.info(f"Weeks: {unified_df['week'].min()}-{unified_df['week'].max()}")
            logger.info(f"Teams: {unified_df['team'].nunique()}")
            logger.info(f"Unique players: {unified_df['full_name'].nunique()}")
            logger.info(f"Output: {scraped_bucket}/injuries")
            logger.info("="*80)
            return 0
        else:
            logger.error("❌ Upload failed")
            return 1
            
    except Exception as e:
        logger.exception(f"❌ Migration failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
