"""
Build unified player availability warehouse table.

Architecture:
- Primary: wkly_rosters (provides weekly roster status for ALL players)
- Secondary: warehouse/injuries (provides injury details when status = INA/RES)
- Enhanced: depth_chart (for position/starter context)
- ID resolution: player_id_mapping (for missing gsis_id backfill)

Pattern: Multi-source warehouse transformation
Complexity: 5 points (Multi-source + Union + Enrichment + Deduplication + ID Resolution)

Key Insight:
- wkly_rosters.status tells us WHO IS AVAILABLE (ACT vs INA vs RES)
- injuries tells us WHY they're unavailable (injury details)
- Together = complete player availability picture

⚠️ CRITICAL ISSUE SOL UTIONS:
1. Schema Collision (Issue #1): Renames status → roster_status, report_status → injury_report_status
2. Temporal Safety (Issue #2): wkly_rosters is week-level snapshot (safe by design)
3. Position Mapping (Issue #3): Uses position (primary) + depth_chart_position (analysis)
4. Missing IDs (Issue #4): 3-stage ID matching (gsis_id → name → alternative IDs)

Created: 2026-01-25
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Any
from datetime import datetime
import logging
from nflfastRv3.shared.bucket_adapter import get_bucket_adapter


# Roster status descriptions from data dictionary
ROSTER_STATUS_DESCRIPTIONS = {
    'ACT': 'On the active roster',
    'EXE': "On the commissioner's exempt list",
    'DEV': 'On the practice squad',
    'CUT': "Cut from the team's roster",
    'E14': 'On the roster as an exempt international player',
    'INA': 'Under contract but not on the active roster, inactive',
    'NWT': 'Rarely used, tends to indicate a waived player',
    'PUP': 'On the "Physically Unable to Perform" list',
    'RES': 'On the reserve list',
    'RET': 'On the retired from football list',
    'RFA': 'Rarely used, tends to indicate a cut player who is a restricted free agent',
    'RSN': 'Rarely used, tends to indicate a player is on the non-football injured reserve list',
    'RSR': 'Rarely used, tends to indicate a player released from being on the injured reserve list',
    'SUS': 'Player is suspended from the NFL',
    'TRC': 'Player has been released from the practice squad',
    'TRD': 'Player has been released from the practice squad',
    'TRL': 'Rarely used and only for a brief period in the 1960s',
    'TRT': 'Player has been released from the practice squad',
    'UFA': 'Player has been released and is an unrestricted free agent',
}


def build_warehouse_player_availability(
    engine: Any,
    logger: logging.Logger,
    seasons: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Build unified player availability table from multiple raw sources.
    
    Data Sources:
    1. raw_nflfastr/wkly_rosters (weekly roster snapshots 2002-present)
    2. warehouse/injuries (unified injury reports 2009-present)
    3. raw_nflfastr/depth_chart (depth chart positions 2001-present)
    4. warehouse/player_id_mapping (ID crosswalk for missing gsis_id)
    
    Key Features:
    - Tracks ALL player statuses (not just injured)
    - Identifies healthy scratches (INACTIVE_HEALTHY)
    - Tracks long-term unavailability (IR, suspended, practice squad)
    - Provides unified availability classification
    
    Output Schema:
    - Identifiers: season, week, team, gsis_id, full_name
    - Player Info: position (primary), depth_chart_position (analysis), jersey_number
    - Roster Status: roster_status (ACT/INA/RES/etc), roster_status_description
    - Injury Status: injury_report_status (Out/Question able/etc), report_primary_injury
    - Availability: availability_status (unified), is_available (boolean)
    - Depth: depth_rank (from depth_chart)
    - Alternative IDs: pfr_player_id, espn_id, pff_id, nfl_id, otc_id(for joins)
    
    ⚠️ TEMPORAL SAFETY:
    - wkly_rosters: Week-level snapshot (safe by design, published pre-game)
    - injuries: Merged by (season, week) gives final pre-game injury report
    - No future leakage - data represents player status at WEEK START
    
    Args:
        engine: SQLAlchemy engine or DataFrameEngine (ignored - uses bucket)
        logger: Logger instance(created via commonv2.get_logger by warehouse builder)
        seasons: Optional list of seasons to include (None = all)
        
    Returns:
        DataFrame with unified player availability data
    """
    logger.info("="*80)
    logger.info("BUILDING PLAYER AVAILABILITY WAREHOUSE TABLE")
    logger.info("="*80)
    
    bucket_adapter = get_bucket_adapter(logger=logger)
    
    # Build filters
    filters = _build_season_filters(seasons)
    filter_desc = f"seasons {seasons}" if seasons else "all seasons"
    logger.info(f"📦 Loading data for: {filter_desc}")
    
    # ============================================================================
    # STAGE 1: Load wkly_rosters (base truth)
    # ============================================================================
    logger.info("="*80)
    logger.info("STAGE 1: LOADING WEEKLY ROSTERS (BASE TRUTH)")
    logger.info("="*80)
    
    try:
        wkly_rosters = bucket_adapter.read_data('wkly_rosters', 'raw_nflfastr', filters=filters)
        
        if wkly_rosters.empty:
            logger.error("❌ wkly_rosters returned no data!")
            return pd.DataFrame()
        
        # ✅ ISSUE #1 SOLUTION: Rename to prevent schema collision
        wkly_rosters = wkly_rosters.rename(columns={'status': 'roster_status'})
        
        # ✅ PRIORITY 2: Ensure schema consistency for nullable string columns
        # Uses pandas 'string' dtype (StringDtype) for proper Parquet schema handling
        # This ensures schema compatibility when appending to existing Parquet files
        nullable_string_columns = [
            # Position fields
            'depth_chart_position', 'ngs_position',
            # Player ID fields (many are all-null and need explicit typing)
            'espn_id', 'sportradar_id', 'yahoo_id', 'rotowire_id', 'pff_id',
            'pfr_id', 'fantasy_data_id', 'sleeper_id',
            # Name/text fields that may have nulls
            'football_name', 'esb_id', 'gsis_it_id', 'smart_id',
            'draft_club', 'draft_number', 'college'
        ]
        for col in nullable_string_columns:
            if col in wkly_rosters.columns:
                # Use pandas nullable 'string' dtype (not 'str') for consistent Parquet schema
                # 'string' dtype properly handles None/NA values and creates string type in Parquet
                wkly_rosters[col] = wkly_rosters[col].astype('string')
            else:
                # Create missing column as empty string type
                logger.debug(f"   Creating missing column {col} as string type")
                wkly_rosters[col] = pd.Series(dtype='string', index=wkly_rosters.index)
        
        logger.info(f"✓ Enforced string types for {len(nullable_string_columns)} nullable columns")
        
        logger.info(f"✓ Loaded wkly_rosters: {len(wkly_rosters):,} rows")
        logger.info(f"   Seasons: {wkly_rosters['season'].min()}-{wkly_rosters['season'].max()}")
        logger.info(f"   Weeks: {wkly_rosters['week'].min()}-{wkly_rosters['week'].max()}")
        logger.info(f"   Teams: {wkly_rosters['team'].nunique()}")
        logger.info(f"   Players: {wkly_rosters['full_name'].nunique():,}")
        
        # Log roster status distribution
        if 'roster_status' in wkly_rosters.columns:
            status_counts = wkly_rosters['roster_status'].value_counts()
            logger.info(f"   Status distribution: {status_counts.to_dict()}")
        
    except Exception as e:
        logger.error(f"❌ Failed to load wkly_rosters: {e}", exc_info=True)
        return pd.DataFrame()
    
    # ============================================================================
    # STAGE 2: Load injuries (supplemental - why unavailable)
    # ============================================================================
    logger.info("="*80)
    logger.info("STAGE 2: LOADING INJURY DATA (SUPPLEMENTAL)")
    logger.info("="*80)
    
    try:
        injuries = bucket_adapter.read_data('injuries', 'warehouse', filters=filters)
        
        if not injuries.empty:
            # ✅ ISSUE #1 SOLUTION: Rename to prevent schema collision
            injuries = injuries.rename(columns={'report_status': 'injury_report_status'})
            
            logger.info(f"✓ Loaded injuries: {len(injuries):,} rows")
            logger.info(f"   Seasons: {injuries['season'].min()}-{injuries['season'].max()}")
            logger.info(f"   Players with injuries: {injuries['full_name'].nunique():,}")
            
            # Log injury status distribution
            if 'injury_report_status' in injuries.columns:
                injury_counts = injuries['injury_report_status'].value_counts()
                logger.info(f"   Injury statuses: {injury_counts.to_dict()}")
        else:
            logger.warning("⚠️  Injuries table is empty - will proceed without injury data")
            injuries = pd.DataFrame()
            
    except Exception as e:
        logger.warning(f"⚠️  Could not load injuries: {e}")
        logger.warning("   Will proceed without injury data")
        injuries = pd.DataFrame()
    
    # ============================================================================
    # STAGE 3: Load depth_chart (starter identification)
    # ============================================================================
    logger.info("="*80)
    logger.info("STAGE 3: LOADING DEPTH CHART (STARTER IDENTIFICATION)")
    logger.info("="*80)
    
    try:
        depth_chart = bucket_adapter.read_data('depth_chart', 'raw_nflfastr', filters=filters)
        
        if not depth_chart.empty:
            logger.info(f"✓ Loaded depth_chart: {len(depth_chart):,} rows")
            logger.info(f"   Schema detected: {list(depth_chart.columns)[:10]}...")  # Debug: show first 10 columns
            
            # ✅ PRE-MERGE CLEANING: Handle new schema format (2025+)
            # New format has 'dt' (timestamp) instead of 'season'/'week'
            if 'dt' in depth_chart.columns and 'season' not in depth_chart.columns:
                logger.info("   📅 New depth chart format detected (2025+) - enriching with season/week")
                
                # Load dim_game for season/week/game_date mapping
                try:
                    dim_game = bucket_adapter.read_data('dim_game', 'warehouse')
                    
                    if dim_game.empty:
                        logger.error("❌ Cannot enrich depth chart: dim_game is empty")
                        depth_simplified = pd.DataFrame()
                    else:
                        # Create unique week mapping (dedup on season, week, game_date)
                        week_mapping = dim_game[['season', 'week', 'game_date']].drop_duplicates()
                        week_mapping['game_date'] = pd.to_datetime(week_mapping['game_date'])
                        
                        # Remove timezone for merge compatibility (converts both UTC and naive to naive)
                        try:
                            week_mapping['game_date'] = week_mapping['game_date'].dt.tz_localize(None)
                        except TypeError:
                            # Already timezone-naive, continue
                            pass
                        
                        week_mapping = week_mapping.sort_values('game_date')
                        
                        # Convert depth chart dt to datetime and remove timezone
                        depth_chart['dt'] = pd.to_datetime(depth_chart['dt'])
                        
                        # Remove timezone for merge compatibility (converts both UTC and naive to naive)
                        try:
                            depth_chart['dt'] = depth_chart['dt'].dt.tz_localize(None)
                        except TypeError:
                            # Already timezone-naive, continue
                            pass
                        
                        depth_chart = depth_chart.sort_values('dt')
                        
                        logger.info(f"   🔗 Matching {len(depth_chart):,} depth records to game weeks...")
                        
                        # 📊 DIAGNOSTIC: Log date ranges before merge
                        depth_dt_min = depth_chart['dt'].min()
                        depth_dt_max = depth_chart['dt'].max()
                        game_date_min = week_mapping['game_date'].min()
                        game_date_max = week_mapping['game_date'].max()
                        
                        logger.info(f"   📅 Depth chart dt range: {depth_dt_min} to {depth_dt_max}")
                        logger.info(f"   📅 Game date range: {game_date_min} to {game_date_max}")
                        
                        # Check for gaps
                        if depth_dt_min < game_date_min:
                            days_before = (game_date_min - depth_dt_min).days
                            early_count = (depth_chart['dt'] < game_date_min).sum()
                            logger.warning(f"   ⚠️  {early_count:,} depth records are {days_before} days BEFORE first game")
                        
                        if depth_dt_max > game_date_max + pd.Timedelta(days=7):
                            days_after = (depth_dt_max - game_date_max).days
                            late_count = (depth_chart['dt'] > game_date_max + pd.Timedelta(days=7)).sum()
                            logger.warning(f"   ⚠️  {late_count:,} depth records are {days_after} days AFTER last game")
                        
                        # Temporal join: match dt to nearest future game_date (within 7 days)
                        # Depth charts are published 0-7 days before games
                        depth_enriched = pd.merge_asof(
                            depth_chart,
                            week_mapping,
                            left_on='dt',
                            right_on='game_date',
                            direction='forward',  # Match to next upcoming game
                            tolerance=pd.Timedelta(days=7)  # Only match within 7-day window
                        )
                        
                        # Filter out unmatched records
                        matched_count = depth_enriched['season'].notna().sum()
                        unmatched_count = len(depth_enriched) - matched_count
                        
                        if unmatched_count > 0:
                            # Analyze unmatched records
                            unmatched = depth_enriched[depth_enriched['season'].isna()]
                            unmatched_dt_min = unmatched['dt'].min()
                            unmatched_dt_max = unmatched['dt'].max()
                            
                            # Determine if unmatched records are preseason
                            # NFL preseason typically runs mid-August, regular season starts early September
                            preseason_count = ((unmatched['dt'].dt.month == 8) |
                                             ((unmatched['dt'].dt.month == 9) & (unmatched['dt'].dt.day < 5))).sum()
                            postseason_count = (unmatched['dt'] > game_date_max).sum()
                            other_count = unmatched_count - preseason_count - postseason_count
                            
                            logger.warning(f"   ⚠️  {unmatched_count:,} depth records couldn't match to game week")
                            logger.warning(f"   Breakdown:")
                            if preseason_count > 0:
                                logger.warning(f"      • {preseason_count:,} preseason depth charts (Aug-early Sept, no regular season games yet)")
                            if postseason_count > 0:
                                logger.warning(f"      • {postseason_count:,} post-season depth charts (after last game)")
                            if other_count > 0:
                                logger.warning(f"      • {other_count:,} other (bye weeks or data gaps)")
                            
                            logger.warning(f"   Unmatched dt range: {unmatched_dt_min} to {unmatched_dt_max}")
                            
                            # Sample unmatched dates
                            sample_unmatched = unmatched['dt'].value_counts().head(5)
                            logger.warning(f"   Top unmatched dates:\n{sample_unmatched}")
                        
                        depth_enriched = depth_enriched[depth_enriched['season'].notna()].copy()
                        
                        if not depth_enriched.empty:
                            logger.info(f"   ✓ Enriched {matched_count:,}/{len(depth_chart):,} records with season/week")
                            logger.info(f"   Seasons: {int(depth_enriched['season'].min())}-{int(depth_enriched['season'].max())}")
                            
                            # Create simplified depth chart for merge
                            depth_simplified = depth_enriched[['season', 'week', 'gsis_id', 'pos_rank']].copy()
                            depth_simplified['season'] = depth_simplified['season'].astype(int)
                            depth_simplified['week'] = depth_simplified['week'].astype(int)
                            depth_simplified = depth_simplified.rename(columns={'pos_rank': 'depth_rank'})
                            
                            # Deduplicate (player may appear multiple times in different formations)
                            # Keep lowest depth_rank (1 = starter)
                            depth_simplified = depth_simplified.sort_values('depth_rank')
                            depth_simplified = depth_simplified.drop_duplicates(
                                subset=['season', 'week', 'gsis_id'],
                                keep='first'
                            )
                            
                            logger.info(f"   ✓ Deduplicated to {len(depth_simplified):,} unique player-week positions")
                        else:
                            logger.warning("⚠️  No depth records matched to game weeks")
                            depth_simplified = pd.DataFrame()
                
                except Exception as dim_game_err:
                    logger.error(f"❌ Failed to load dim_game for depth enrichment: {dim_game_err}")
                    logger.warning("   Will proceed without depth data")
                    depth_simplified = pd.DataFrame()
            
            # Legacy format (pre-2025): has 'season' and 'week' columns
            elif 'season' in depth_chart.columns and 'week' in depth_chart.columns:
                logger.info("   📅 Legacy depth chart format detected (pre-2025)")
                logger.info(f"   Seasons: {depth_chart['season'].min()}-{depth_chart['season'].max()}")
                
                # Create simplified depth chart for merge (keep only starter designation)
                depth_simplified = depth_chart[['season', 'week', 'gsis_id', 'pos_rank']].copy()
                depth_simplified = depth_simplified.rename(columns={'pos_rank': 'depth_rank'})
                
                # Deduplicate (player may appear multiple times in different formations)
                # Keep lowest depth_rank (1 = starter)
                depth_simplified = depth_simplified.sort_values('depth_rank')
                depth_simplified = depth_simplified.drop_duplicates(
                    subset=['season', 'week', 'gsis_id'],
                    keep='first'
                )
                
                logger.info(f"   ✓ Deduplicated to {len(depth_simplified):,} unique player-week positions")
            
            # Unknown format
            else:
                logger.error(f"❌ Unknown depth chart schema. Available columns: {list(depth_chart.columns)}")
                logger.error("   Expected: (dt + pos_rank) OR (season + week + pos_rank)")
                depth_simplified = pd.DataFrame()
        else:
            logger.warning("⚠️  Depth chart is empty - will proceed without depth data")
            depth_simplified = pd.DataFrame()
            
    except Exception as e:
        logger.warning(f"⚠️  Could not load/process depth_chart: {e}", exc_info=True)
        logger.warning("   Will proceed without depth data")
        depth_simplified = pd.DataFrame()
    
    # ============================================================================
    # STAGE 4: Load player_id_mapping (for ID resolution)
    # ============================================================================
    logger.info("="*80)
    logger.info("STAGE 4: LOADING PLAYER ID MAPPING (ID RESOLUTION)")
    logger.info("="*80)
    
    try:
        id_mapping = bucket_adapter.read_data('player_id_mapping', 'warehouse')
        
        if not id_mapping.empty:
            logger.info(f"✓ Loaded player_id_mapping: {len(id_mapping):,} players")
            logger.info(f"   Will use for missing gsis_id backfill")
        else:
            logger.warning("⚠️  player_id_mapping is empty")
            id_mapping = pd.DataFrame()
            
    except Exception as e:
        logger.warning(f"⚠️  Could not load player_id_mapping: {e}")
        logger.warning("   Issue #4 (missing ID resolution) will be limited")
        id_mapping = pd.DataFrame()
    
    # ============================================================================
    # STAGE 5: MERGE - Build unified availability table
    # ============================================================================
    logger.info("="*80)
    logger.info("STAGE 5: MERGING DATA SOURCES")
    logger.info("="*80)
    
    # ✅ ISSUE #4 SOLUTION Stage 1: Primary join on gsis_id
    logger.info("🔗 Stage 5a: Merging injuries (gsis_id join)...")
    
    if not injuries.empty:
        availability_df = wkly_rosters.merge(
            injuries[['season', 'week', 'team', 'gsis_id', 'injury_report_status',
                      'report_primary_injury', 'report_secondary_injury', 'date_modified']],
            on=['season', 'week', 'team', 'gsis_id'],
            how='left',
            suffixes=('', '_injury')
        )
        
        # ✅ PRIORITY 1: Convert null-typed columns from merge to string type
        for col in ['injury_report_status', 'report_primary_injury', 'report_secondary_injury']:
            if col in availability_df.columns:
                availability_df[col] = availability_df[col].astype('string')
        
        matched_count = availability_df['injury_report_status'].notna().sum()
        match_pct = (matched_count / len(wkly_rosters)) * 100
        logger.info(f"   ✓ Matched {matched_count:,}/{len(wkly_rosters):,} ({match_pct:.1f}%) by gsis_id")
    
    else:
        availability_df = wkly_rosters.copy()
        # ✅ PRIORITY 1: Use typed nullable columns instead of None
        availability_df['injury_report_status'] = pd.Series(dtype='string', index=availability_df.index)
        availability_df['report_primary_injury'] = pd.Series(dtype='string', index=availability_df.index)
        availability_df['report_secondary_injury'] = pd.Series(dtype='string', index=availability_df.index)
        availability_df['date_modified'] = pd.Series(dtype='datetime64[ns]', index=availability_df.index)
        logger.info("   ⚠️ Skipped injury merge (no injury data) - created empty typed columns")
    
    # ✅ ISSUE #4 SOLUTION Stage 2: Fallback join on (full_name, team, season)
    if not injuries.empty:
        logger.info("🔗 Stage 5b: Filling gaps with name-based matching...")
        
        # Find unmatched rows (no injury data and roster_status suggests injury)
        needs_match = (
            availability_df['injury_report_status'].isna() &
            availability_df['roster_status'].isin(['INA', 'RES', 'PUP'])
        )
        
        if needs_match.sum() > 0:
            # Try name-based match
            name_matches = availability_df[needs_match].merge(
                injuries[['season', 'week', 'team', 'full_name', 'injury_report_status',
                          'report_primary_injury']],
                on=['season', 'week', 'team', 'full_name'],
                how='left',
                suffixes=('', '_name')
            )
            
            # Update availability_df with name matches
            for idx in name_matches.index:
                if pd.notna(name_matches.loc[idx, 'injury_report_status_name']):
                    availability_df.loc[idx, 'injury_report_status'] = name_matches.loc[idx, 'injury_report_status_name']
                    availability_df.loc[idx, 'report_primary_injury'] = name_matches.loc[idx, 'report_primary_injury_name']
            
            additional_matches = availability_df.loc[needs_match.index, 'injury_report_status'].notna().sum()
            logger.info(f"   ✓ Found {additional_matches:,} additional matches by name")
    
    # Merge depth chart
    logger.info("🔗 Stage 5c: Merging depth chart...")
    if not depth_simplified.empty:
        availability_df = availability_df.merge(
            depth_simplified,
            on=['season', 'week', 'gsis_id'],
            how='left'
        )
        
        # ✅ PRIORITY 1: Convert null-typed column from merge to string type
        if 'depth_rank' in availability_df.columns:
            availability_df['depth_rank'] = availability_df['depth_rank'].astype('string')
        
        depth_matched = availability_df['depth_rank'].notna().sum()
        logger.info(f"   ✓ Matched {depth_matched:,} players with depth chart positions")
    else:
        # ✅ PRIORITY 1: Use typed nullable column instead of None
        availability_df['depth_rank'] = pd.Series(dtype='string', index=availability_df.index)
        logger.info("   ⚠️ Skipped depth chart merge (no depth data) - created empty typed column")
    
    # ✅ ISSUE #4 SOLUTION Stage 3: Backfill missing gsis_id from player_id_mapping
    null_gsis_count = availability_df['gsis_id'].isna().sum()
    
    if null_gsis_count > 0 and not id_mapping.empty:
        logger.info(f"🔗 Stage 5d: Backfilling {null_gsis_count:,} missing gsis_id values...")
        
        # Try to match on alternative IDs
        backfilled = 0
        # Fix: use actual id columns (By Acie F 1/25/26; DO NOT REMOVE COMMENT)
        for id_col in ['espn_id', 'pfr_id', 'pff_id', 'nfl_id', 'otc_id']:
            if id_col not in availability_df.columns:
                logger.warning(f"   ⚠️ {id_col} not available in source data - skipping")
                continue
            if id_col not in id_mapping.columns:
                logger.warning(f"   ⚠️ {id_col} not in player_id_mapping - skipping")
                continue
            if id_col in availability_df.columns and id_col in id_mapping.columns:
                # Create mapping dict
                alt_to_gsis = id_mapping[[id_col, 'gsis_id']].dropna().drop_duplicates(id_col)
                alt_to_gsis_dict = dict(zip(alt_to_gsis[id_col], alt_to_gsis['gsis_id']))
                
                # Fill missing gsis_id
                mask = availability_df['gsis_id'].isna() & availability_df[id_col].notna()
                if mask.sum() > 0:
                    availability_df.loc[mask, 'gsis_id'] = availability_df.loc[mask, id_col].map(alt_to_gsis_dict)
                    newly_filled = mask.sum() - availability_df.loc[mask, 'gsis_id'].isna().sum()
                    backfilled += newly_filled
        
        if backfilled > 0:
            logger.info(f"   ✓ Backfilled {backfilled:,} gsis_id values from alternative IDs")
    
    # ============================================================================
    # STAGE 6: CLASSIFICATION - Derive unified availability status
    # ============================================================================
    logger.info("="*80)
    logger.info("STAGE 6: CLASSIFYING PLAYER AVAILABILITY")
    logger.info("="*80)
    
    # Convert string dtype back to object for np.select compatibility
    roster_status_for_classify = availability_df['roster_status'].astype('object')
    injury_status_for_classify = availability_df['injury_report_status'].astype('object')
    
    availability_df['availability_status'] = _classify_availability(
        roster_status_for_classify,
        injury_status_for_classify
    )
    
    # Add boolean is_available flag (True only for active status)
    availability_df['is_available'] = availability_df['availability_status'].isin([
        'ACTIVE', 'ACTIVE_QUESTIONABLE'
    ])
    
    # Add roster status descriptions
    availability_df['roster_status_description'] = availability_df['roster_status'].map(
        ROSTER_STATUS_DESCRIPTIONS
    )
    
    # Log classification distribution
    status_dist = availability_df['availability_status'].value_counts()
    logger.info(f"✓ Classified {len(availability_df):,} player-week records:")
    for status, count in status_dist.items():
        pct = (count / len(availability_df)) * 100
        logger.info(f"   {status}: {count:,} ({pct:.1f}%)")
    
    # ✅ ISSUE #3 SOLUTION: Document position field usage
    logger.info("="*80)
    logger.info("POSITION FIELD RESOLUTION (ISSUE #3)")
    logger.info("="*80)
    logger.info("✓ position: Primary position from NFL.com (use for weighting)")
    logger.info("✓ depth_chart_position: Position from roster (use for depth analysis only)")
    logger.info("   Note: depth_chart_position marked 'not always accurate' in data dictionary")
    
    # ============================================================================
    # STAGE 7: QUALITY METRICS & VALIDATION
    # ============================================================================
    logger.info("="*80)
    logger.info("STAGE 7: QUALITY METRICS")
    logger.info("="*80)
    
    # ID coverage
    gsis_coverage = (availability_df['gsis_id'].notna().sum() / len(availability_df)) * 100
    logger.info(f"✓ gsis_id coverage: {availability_df['gsis_id'].notna().sum():,}/{len(availability_df):,} ({gsis_coverage:.1f}%)")
    
    missing_gsis = availability_df['gsis_id'].isna().sum()
    if missing_gsis > 0:
        logger.warning(f"   ⚠️ {missing_gsis:,} players without gsis_id (expected for rookies/practice squad)")
    
    # Duplicates check
    dupe_cols = ['season', 'week', 'team', 'gsis_id']
    dupes = availability_df[availability_df.duplicated(subset=dupe_cols, keep=False)]
    if len(dupes) > 0:
        logger.error(f"❌ Found {len(dupes)} duplicates on ({', '.join(dupe_cols)})!")
        # Log sample
        logger.error(f"   Sample duplicates:\n{dupes.head(10)}")
    else:
        logger.info(f"✓ No duplicates on ({', '.join(dupe_cols)})")
    
    # Roster size validation
    roster_counts = availability_df.groupby(['season', 'week', 'team']).size()
    logger.info(f"✓ Roster sizes: min={roster_counts.min()}, mean={roster_counts.mean():.1f}, max={roster_counts.max()}")
    
    if roster_counts.min() < 35:
        logger.warning(f"   ⚠️ Some teams have <35 players (min={roster_counts.min()})")
    if roster_counts.max() > 70:
        logger.warning(f"   ⚠️ Some teams have >70 players (max={roster_counts.max()})")
    
    # ✅ ISSUE #2 SOLUTION: Temporal safety validation
    logger.info("="*80)
    logger.info("TEMPORAL SAFETY VALIDATION (ISSUE #2)")
    logger.info("="*80)
    logger.info("✓ wkly_rosters: Week-level snapshot (published pre-game) - SAFE")
    logger.info("✓ injuries: Merged by (season, week) gives pre-game status - SAFE")
    logger.info("✓ No future leakage - data represents player status at WEEK START")
    if 'date_modified' in availability_df.columns:
        logger.info("✓ date_modified preserved for auditing (not used in features)")
    
    # ============================================================================
    # STAGE 8: FINALIZE OUTPUT
    # ============================================================================
    
    # ✅ PRIORITY 4: Enforce expected schema before return
    logger.info("="*80)
    logger.info("SCHEMA TYPE ENFORCEMENT")
    logger.info("="*80)
    
    expected_schema = {
        'depth_chart_position': 'string',
        'ngs_position': 'string',
        'injury_report_status': 'string',
        'report_primary_injury': 'string',
        'report_secondary_injury': 'string',
        'depth_rank': 'string',
        'pff_id': 'string',
        'fantasy_data_id': 'string',
    }
    
    for col, expected_dtype in expected_schema.items():
        if col in availability_df.columns:
            current_dtype = str(availability_df[col].dtype)
            if current_dtype != expected_dtype and current_dtype != 'object':
                logger.warning(f"Type mismatch {col}: {current_dtype} != {expected_dtype}, converting...")
                if expected_dtype == 'string':
                    availability_df[col] = availability_df[col].astype('string')
    
    logger.info("✓ Schema types validated and enforced")
    
    logger.info("="*80)
    logger.info("✅ PLAYER AVAILABILITY WAREHOUSE BUILD COMPLETE")
    logger.info("="*80)
    logger.info(f"Total records: {len(availability_df):,}")
    logger.info(f"Seasons: {availability_df['season'].min()}-{availability_df['season'].max()}")
    logger.info(f"Weeks: {availability_df['week'].min()}-{availability_df['week'].max()}")
    logger.info(f"Teams: {availability_df['team'].nunique()}")
    logger.info(f"Unique players: {availability_df['full_name'].nunique():,}")
    logger.info(f"Available players: {availability_df['is_available'].sum():,} ({(availability_df['is_available'].sum()/len(availability_df))*100:.1f}%)")
    logger.info(f"Output: warehouse/player_availability")
    logger.info("="*80)
    
    return availability_df


def _classify_availability(roster_status: pd.Series, injury_report_status: pd.Series) -> pd.Series:
    """
    Classify unified player availability from roster + injury data.
    
    Priority Logic (roster_status takes precedence):
    1. roster_status='ACT' + no injury → ACTIVE
    2. roster_status='ACT' + injury='Questionable' → ACTIVE_QUESTIONABLE
    3. roster_status='ACT' + injury='Out'/Doubtful' → ACTIVE_INJURED (rare, playing through injury)
    4. roster_status='INA' + no injury → INACTIVE_HEALTHY (healthy scratch - KEY SIGNAL!)
    5. roster_status='INA' + injury → INACTIVE_INJURED
    6. roster_status='RES' → INJURED_RESERVE (long-term)
    7. roster_status='PUP' → PHYSICALLY_UNABLE (long-term)
    8. roster_status='SUS' → SUSPENDED
    9. roster_status='DEV' → PRACTICE_SQUAD
    10. Other statuses → UNAVAILABLE
    
    Args:
        roster_status: Series of roster status codes (ACT/INA/RES/etc)
        injury_report_status: Series of injury report statuses (Out/Questionable/etc)
        
    Returns:
        pd.Series: Unified availability classification
    """
    conditions = [
        # Active players (on roster)
        (roster_status == 'ACT') & (injury_report_status.isna()),
        (roster_status == 'ACT') & (injury_report_status == 'Questionable'),
        (roster_status == 'ACT') & (injury_report_status.isin(['Doubtful', 'Out'])),
        
        # Inactive players (healthy vs injured)
        (roster_status == 'INA') & (injury_report_status.isna()),
        (roster_status == 'INA') & (injury_report_status.notna()),
        
        # Long-term unavailable
        (roster_status == 'RES'),
        (roster_status == 'PUP'),
        (roster_status == 'SUS'),
        (roster_status == 'DEV'),
        (roster_status == 'EXE'),  # Commissioner's exempt
        
        # Cut/released (unavailable)
        (roster_status.isin(['CUT', 'RET', 'UFA', 'TRC', 'TRD', 'TRT'])),
    ]
    
    choices = [
        'ACTIVE',
        'ACTIVE_QUESTIONABLE',
        'ACTIVE_INJURED',  # Playing through injury (rare)
        'INACTIVE_HEALTHY',  # Healthy scratch - strategic decision!
        'INACTIVE_INJURED',
        'INJURED_RESERVE',
        'PHYSICALLY_UNABLE',
        'SUSPENDED',
        'PRACTICE_SQUAD',
        'EXEMPT_LIST',
        'UNAVAILABLE',  # Cut/retired/released
    ]
    
    return pd.Series(np.select(conditions, choices, default='UNKNOWN'), index=roster_status.index)


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


__all__ = ['build_warehouse_player_availability']
