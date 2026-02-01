"""
Build unified injuries warehouse table from multi-source raw data.

Architecture:
- Unions: raw_nflfastr/injuries (historical) + raw_nflcom_{YYYY}/injuries (current season)
- Deduplicates by (season, week, team, full_name), keeping most recent
- Outputs: warehouse/injuries (single source of truth)

Pattern: Warehouse transformation (matches dim_game, dim_player signature).
Complexity: 3 points (Multi-source + Union + Deduplication)

⚠️ TEMPORAL LEAKAGE WARNING:
This warehouse provides date_modified timestamps. ML feature builders MUST filter:
    injuries_df[injuries_df['date_modified'] < game_datetime]
to prevent using mid-game or post-game injury report updates.
See: TemporalValidator for week-level filtering (complementary).
"""

import pandas as pd
from typing import Optional, List, Any
from datetime import datetime
import logging
from nflfastRv3.shared.bucket_adapter import get_bucket_adapter


def build_warehouse_injuries(
    engine: Any,
    logger: logging.Logger,
    seasons: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Build unified injuries warehouse table from multiple raw sources.
    
    Data Sources:
    1. raw_nflfastr/injuries (historical through last completed season) - nflverse
    2. raw_nflcom_{YYYY}/injuries (current season) - NFL.com scraping
    3. (Future) raw_apisports/injuries - daily updates
    
    Deduplication Strategy:
    - Sort by source priority (nflverse > apisports > nflcom_scrape)
    - Then by date_modified (most recent first)
    - Keep first record per (season, week, team, full_name)
    
    ⚠️ TEMPORAL LEAKAGE WARNING:
    The date_modified field can be AFTER game start times. ML features must filter:
        safe_injuries = injuries_df[injuries_df['date_modified'] < game_datetime]
    This complements TemporalValidator's week-level filtering.
    
    Args:
        engine: SQLAlchemy engine or DataFrameEngine (ignored - uses bucket)
        logger: Logger instance (created via commonv2.get_logger by warehouse builder)
        seasons: Optional list of seasons to include (None = all)
        
    Returns:
        DataFrame with unified injuries data
    """
    logger.info("="*80)
    logger.info("BUILDING INJURIES WAREHOUSE TABLE")
    logger.info("="*80)
    
    bucket_adapter = get_bucket_adapter(logger=logger)
    all_injuries = []
    
    # Build filters
    filters = _build_season_filters(seasons)
    
    # 1. Load nflverse (2009-2024+)
    logger.info("📦 Loading nflverse injuries (2009-present)...")
    nflverse_df = None
    try:
        nflverse_df = bucket_adapter.read_data('injuries', 'raw_nflfastr', filters=filters)
        
        if not nflverse_df.empty:
            # Normalize timestamps BEFORE adding to list
            if 'date_modified' in nflverse_df.columns:
                nflverse_df['date_modified'] = pd.to_datetime(nflverse_df['date_modified'], utc=True).dt.tz_localize(None)
            
            nflverse_df['source'] = 'nflverse'
            all_injuries.append(nflverse_df)
            logger.info(f"✓ nflverse: {len(nflverse_df):,} rows")
            logger.info(f"   Seasons: {nflverse_df['season'].min()}-{nflverse_df['season'].max()}")
        else:
            logger.warning("⚠️  No nflverse data loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load nflverse: {e}")
        # Continue - try NFL.com data
    
    # 2. Load scraped source for current season (if needed)
    current_season = _get_current_season()
    scraped_bucket = f'raw_nflcom_{current_season}'
    
    if _should_load_scraped_source(nflverse_df, current_season, seasons):
        logger.info(f"📦 Loading {scraped_bucket}/injuries (bridge data)...")
        try:
            scraped_df = bucket_adapter.read_data('injuries', scraped_bucket)
            
            if not scraped_df.empty:
                # Normalize timestamps BEFORE adding to list
                if 'date_modified' in scraped_df.columns:
                    scraped_df['date_modified'] = pd.to_datetime(scraped_df['date_modified'], utc=True).dt.tz_localize(None)
                
                scraped_df['source'] = 'nflcom_scrape'
                all_injuries.append(scraped_df)
                logger.info(f"✓ Scraped: {len(scraped_df):,} rows")
                logger.info(f"   Weeks: {scraped_df['week'].min()}-{scraped_df['week'].max()}")
            else:
                logger.warning(f"⚠️  {scraped_bucket} returned empty data")
        except Exception as e:
            logger.warning(f"⚠️  {scraped_bucket} unavailable: {e}")
            logger.warning(f"   Expected if nflverse has {current_season} or bucket not created")
    else:
        logger.info(f"✓ Skipping {scraped_bucket} (not needed)")
    
    # 3. Union all sources
    if not all_injuries:
        logger.error("❌ No injury data loaded from any source!")
        return pd.DataFrame()
    
    logger.info("🔄 Unioning all sources...")
    unified_df = pd.concat(all_injuries, ignore_index=True)
    logger.info(f"   Combined: {len(unified_df):,} rows from {len(all_injuries)} sources")
    
    # Ensure schema consistency: convert null columns to proper nullable string types
    # Uses pandas 'string' dtype (StringDtype) for proper Parquet schema handling
    # This ensures schema compatibility when appending to existing Parquet files
    nullable_string_columns = [
        'gsis_id', 'first_name', 'last_name',
        'report_secondary_injury', 'practice_primary_injury', 'practice_secondary_injury'
    ]
    for col in nullable_string_columns:
        if col in unified_df.columns:
            # Use pandas nullable 'string' dtype (not 'str') for consistent Parquet schema
            # 'string' dtype properly handles None/NA values and creates string type in Parquet
            unified_df[col] = unified_df[col].astype('string')
    
    # 4. Deduplicate with source priority
    if 'date_modified' in unified_df.columns:
        original_count = len(unified_df)
        
        # Timestamps already normalized per-source before concat
        # Add source priority for deduplication
        SOURCE_PRIORITY = {
            'nflverse': 1,      # Official, vetted, complete historical data
            'apisports': 2,     # Real-time during season, reliable API
            'nflcom_scrape': 3  # Temporary bridge, scraped data
        }
        unified_df['_source_priority'] = unified_df['source'].map(SOURCE_PRIORITY)
        
        # Sort by priority first, then by recency
        unified_df = unified_df.sort_values(
            ['_source_priority', 'date_modified'],
            ascending=[True, False]  # Lower priority number = better source, newer date first
        )
        
        # Deduplicate, keeping first (best source + most recent)
        unified_df = unified_df.drop_duplicates(
            subset=['season', 'week', 'team', 'full_name'],
            keep='first'
        ).drop(columns=['_source_priority']).reset_index(drop=True)
        
        dedup_count = original_count - len(unified_df)
        if dedup_count > 0:
            logger.info(f"✓ Deduplicated: removed {dedup_count:,} duplicate records (source priority + recency)")
    
    # 5. Summary
    logger.info("="*80)
    logger.info("✅ INJURIES WAREHOUSE BUILD COMPLETE")
    logger.info("="*80)
    logger.info(f"Total records: {len(unified_df):,}")
    logger.info(f"Seasons: {unified_df['season'].min()}-{unified_df['season'].max()}")
    logger.info(f"Teams: {unified_df['team'].nunique()}")
    logger.info(f"Unique players: {unified_df['full_name'].nunique()}")
    
    # Log source distribution
    if 'source' in unified_df.columns:
        source_dist = unified_df['source'].value_counts().to_dict()
        logger.info(f"Sources: {source_dist}")
    
    logger.info(f"Output: warehouse/injuries")
    logger.info("="*80)
    
    return unified_df


def _get_current_season() -> int:
    """
    Get current NFL season based on date.
    Matches ScheduleDataProvider logic.
    
    NFL season runs from September to February:
    - Sep-Dec: Current year is the season
    - Jan-Feb: Previous year is the season (playoffs)
    - Mar-Aug: Previous year is the season (off-season)
    
    Returns:
        int: Current season year
    """
    # TODO: Update using actual season schedule
    now = datetime.now()
    # NFL season runs from September to February
    return now.year if now.month >= 9 else now.year - 1


def _should_load_scraped_source(
    nflverse_df: Optional[pd.DataFrame],
    current_season: int,
    seasons_filter: Optional[List[int]]
) -> bool:
    """
    Determine if temporary scraped source is needed for current season.
    
    Logic:
    - Skip if current season not in request
    - Skip if nflverse already has complete current season (5k+ records)
    - Load otherwise (nflverse hasn't caught up yet)
    
    Args:
        nflverse_df: DataFrame from raw_nflfastr, None if failed to load
        current_season: Current NFL season year
        seasons_filter: Optional season filter from request
        
    Returns:
        bool: True if scraped source should be loaded
    """
    # If filtering by seasons and current season not requested, skip
    if seasons_filter is not None and current_season not in seasons_filter:
        return False
    
    # If nflverse not loaded or empty, we need scraped source
    if nflverse_df is None or nflverse_df.empty:
        return True
    
    # Check if nflverse has complete current season coverage
    # 5000+ records indicates full season coverage
    nflverse_has_current = (
        current_season in nflverse_df['season'].unique() and
        len(nflverse_df[nflverse_df['season'] == current_season]) >= 5000
    )
    
    return not nflverse_has_current  # Load scraped if nflverse incomplete


def _build_season_filters(seasons: Optional[List[int]]) -> Optional[List[tuple]]:
    """
    Build season filters for bucket queries.
    
    Args:
        seasons: Optional list of seasons to filter by
        
    Returns:
        List of filter tuples for bucket adapter, or None for no filter
    """
    if seasons:
        season_list = list(seasons) if isinstance(seasons, (list, tuple)) else [seasons]
        if len(season_list) > 0:
            return [('season', 'in', season_list)] if len(season_list) > 1 else [('season', '==', season_list[0])]
    return None


__all__ = ['build_warehouse_injuries']
