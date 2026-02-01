"""
Simplified Data Source Configuration for nflfastRv3

Following REFACTORING_SPECS.md:
- Simple data structures (no complex patterns)
- Maximum 5 complexity points per module
- Easy to understand and maintain

Migrated from nflfastRv2 with architectural simplification.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from commonv2 import get_logger
from commonv2.core.config import DatabasePrefixes, TransformNames, SchemaNames, DatabaseConfig

# Module-level logger following REFACTORING_SPECS.md pattern
_logger = get_logger('nflfastRv3.features.data_pipeline.config.data_sources')



@dataclass
class DataSourceConfig:
    """
    Enhanced data source configuration with V2 bucket-first + routing parity.
    
    Pattern: Enhanced dataclass (3 complexity points)
    Provides complete V2 functional equivalence with bucket-first architecture.
    
    Bucket-First Architecture:
    - bucket: All tables go to S3/Sevalla bucket FIRST (primary storage)
    - databases: List of target databases (secondary storage)
    - transforms: Per-database transforms for production data
    """
    r_call: str
    table: str
    schema: str = SchemaNames.RAW_NFLFASTR
    unique_keys: List[str] = field(default_factory=list)
    strategy: str = 'incremental'  # 'incremental' or 'full_refresh'
    
    # V2 parity fields for complete functional equivalence
    min_year: Optional[int] = None
    numeric_cols: List[str] = field(default_factory=list)
    non_numeric_cols: List[str] = field(default_factory=list)
    history_table: Optional[str] = None
    chunksize: Optional[int] = None
    
    # NEW: Bucket-first + table-driven routing (from V2)
    databases: List[str] = field(default_factory=lambda: [DatabasePrefixes.LOCAL_DEV])
    bucket: bool = True  # All data goes to bucket FIRST
    transforms: Dict[str, List[str]] = field(default_factory=dict)  # Per-database transforms
    
    # Team standardization control
    standardize_teams: bool = True  # Default to True for backward compatibility
    
    # Bucket partitioning strategy (for large tables like play_by_play)
    partition_by_year: bool = False  # Default: single file (backward compatible)
    
    def __post_init__(self):
        """Simple validation on creation."""
        _logger.debug(f"Creating DataSourceConfig for table '{self.table}' with R call: {self.r_call}")
        if not self.r_call or not self.table:
            _logger.error(f"Invalid DataSourceConfig: r_call='{self.r_call}', table='{self.table}' - both are required")
            raise ValueError("r_call and table are required")
        _logger.debug(f"DataSourceConfig validated successfully: {self.table} -> {len(self.databases)} database(s)")


# Core NFL data sources with V2 parity fields
NFL_DATA_SOURCES = {
    'play_by_play': DataSourceConfig(
        r_call='load_pbp(file_type = "parquet")',
        table='play_by_play',
        unique_keys=['game_id', 'play_id'],
        strategy='incremental',
        min_year=1999,
        history_table='nflfastr_pbp_hist',
        chunksize=1000,  # Large table with 372 columns
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={},
        standardize_teams=True,  # Has home_team, away_team, posteam, defteam columns
        partition_by_year=True,  # Enable year partitioning to match backfill structure
        # Key numeric columns only (subset of V2 for simplicity)
        numeric_cols=[
            'play_id', 'week', 'yardline_100', 'quarter_seconds_remaining',
            'down', 'ydstogo', 'yards_gained', 'air_yards', 'yards_after_catch',
            'total_home_score', 'total_away_score', 'ep', 'epa', 'wp', 'wpa',
            'season', 'passing_yards', 'receiving_yards', 'rushing_yards'
        ]
    ),
    'rosters': DataSourceConfig(
        r_call='load_rosters(file_type = "parquet")',
        table='rosters',
        unique_keys=[],  # V2 has empty unique_keys due to near-duplicates
        strategy='incremental',
        min_year=1999,
        history_table='nflfastr_rosters_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={},
        standardize_teams=True,  # Has team column
        numeric_cols=['height', 'weight', 'years_exp', 'draft_number', 'jersey_number']
    ),
    'players': DataSourceConfig(
        r_call='load_players(file_type = "parquet")',
        table='players',
        unique_keys=['gsis_id'],
        strategy='full_refresh',
        history_table='nflfastr_players_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={},
        standardize_teams=False  # No team columns to standardize
    ),
    'player_stats': DataSourceConfig(
        r_call='load_player_stats(stat_type = c("offense", "defense", "kicking"), file_type = "parquet")',
        table='player_stats',
        unique_keys=['player_id', 'season', 'week'],
        strategy='incremental',
        min_year=1999,
        history_table='nflfastr_player_stats_hist',
        chunksize=5000,
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={},
        standardize_teams=True,  # Has recent_team column
        non_numeric_cols=[
            'player_id', 'player_name', 'player_display_name', 'position',
            'position_group', 'recent_team', 'season', 'week', 'season_type'
        ]
    ),
    
    # Missing NFL sources from V2 - Batch 1: Advanced Analytics
    'participation': DataSourceConfig(
        # NOTE: PARTICIPATION DATA LOADING ISSUE (2025-10-25)
        # - R call works fine in isolation: load_participation(seasons = TRUE, file_type = "parquet")
        #   * Test results: 433,805 rows in 4.13 seconds, 86.1 MB memory
        #   * All individual year calls work: 2024 (45,919 rows), 2023 (46,168 rows), etc.
        # - Pipeline process gets killed when loading through data pipeline
        # - Root cause investigation completed:
        #   * Removed Universal List-Column Sanitizer from R integration (memory optimization)
        #   * Optimized data cleaning for large datasets (>200K rows)
        #   * Added chunked processing for quality checks
        #   * Strategy='full_refresh' works correctly (doesn't add seasons = 2025)
        # - Use test_r_calls.py to verify R call functionality
        # - Pipeline optimizations implemented but may need further memory tuning
        # - Consider loading participation data in smaller year ranges if issues persist
        r_call='load_participation(seasons = TRUE, file_type = "parquet")',
        table='participation',
        unique_keys=['nflverse_game_id', 'play_id'],
        strategy='full_refresh',
        min_year=2016,
        history_table='nflfastr_participation_hist',
        chunksize=5000,
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={}
    ),
    'nextgen': DataSourceConfig(
        r_call='load_nextgen_stats(stat_type = c("passing", "receiving", "rushing"), file_type = "parquet")',
        table='nextgen',
        unique_keys=['player_gsis_id', 'season', 'week'],
        strategy='full_refresh',
        min_year=2016,
        history_table='nflfastr_nextgen_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={}
    ),
    'snap_counts': DataSourceConfig(
        r_call='load_snap_counts(seasons = TRUE, file_type = "parquet")',
        table='snap_counts',
        unique_keys=['pfr_game_id', 'pfr_player_id'],
        strategy='full_refresh',
        min_year=2012,
        history_table='nflfastr_snap_counts_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={}
    ),
    'pfr_adv_stats': DataSourceConfig(
        r_call='load_pfr_advstats()',
        table='pfr_adv_stats',
        unique_keys=['pfr_game_id', 'pfr_player_id'],
        strategy='incremental',
        min_year=2018,
        history_table='nflfastr_pfr_adv_stats_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={},
        non_numeric_cols=[
            'game_id', 'pfr_game_id', 'game_type', 'team',
            'opponent', 'pfr_player_name', 'pfr_player_id'
        ]
    ),
    'officials': DataSourceConfig(
        r_call='load_officials(seasons = TRUE, file_type = "parquet")',
        table='officials',
        unique_keys=['game_id', 'official_id'],
        strategy='full_refresh',
        history_table='nflfastr_officials_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={}
    ),
    'trades': DataSourceConfig(
        r_call='load_trades(seasons = TRUE)',
        table='trades',
        unique_keys=[],  # V2 has empty unique_keys
        strategy='full_refresh',
        history_table='nflfastr_trades_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={}
    ),
    'ftn_chart': DataSourceConfig(
        r_call='load_ftn_charting()',
        table='ftn_chart',
        unique_keys=['nflverse_game_id', 'nflverse_play_id'],
        strategy='incremental',
        min_year=2022,
        history_table='nflfastr_ftn_chart_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={}
    ),
    'espn_qbr_season': DataSourceConfig(
        # NOTE: ESPN QBR functions REQUIRE explicit 'seasons' parameter
        # - Without 'seasons = TRUE': returns 0 rows (tested 2025-10-25)
        # - With 'seasons = TRUE': returns 1,363 rows (all seasons 2006-2023)
        # - Must use 'full_refresh' strategy to preserve explicit seasons parameter
        r_call='load_espn_qbr(seasons = TRUE, summary_type = "season")',
        table='espn_qbr_season',
        unique_keys=['player_id', 'season', 'season_type'],
        strategy='full_refresh',
        min_year=2006,
        history_table='nflfastr_espn_qbr_season_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={}
    ),
    'espn_qbr_wk': DataSourceConfig(
        # NOTE: ESPN QBR functions REQUIRE explicit 'seasons' parameter
        # - Without 'seasons = TRUE': returns 0 rows (tested 2025-10-25)
        # - With 'seasons = TRUE': returns 9,570 rows (all seasons 2006-2023)
        # - Must use 'full_refresh' strategy to preserve explicit seasons parameter
        r_call='load_espn_qbr(seasons = TRUE, summary_type = "weekly")',
        table='espn_qbr_wk',
        unique_keys=['player_id', 'season', 'game_week', 'season_type'],
        strategy='full_refresh',
        min_year=2006,
        history_table='nflfastr_espn_qbr_wk_hist',
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={}
    ),
    # use seasons = TRUE, on weekly rosters to 
    # pull all data and backfill switching 
    # strategy to 'full_refresh'
    'wkly_rosters': DataSourceConfig(
        r_call='load_rosters_weekly( file_type = "parquet")',
        table='wkly_rosters',
        unique_keys=['season', 'week', 'team', 'gsis_id'],
        strategy='incremental',
        min_year=2002,
        history_table='nflfastr_wkly_rosters_hist',
        chunksize=7500,
        databases=[DatabasePrefixes.LOCAL_DEV],
        bucket=True,
        transforms={},
        standardize_teams=True,  # Has team column
        numeric_cols=['height', 'weight', 'years_exp', 'draft_number', 'jersey_number']
    )
}

# Fantasy football data sources with V2 parity fields
# NOTE: Fantasy tables are bucket-only (no database routing in production)
# Raw data is stored in cloud storage; warehouse/API tables query from bucket
FANTASY_DATA_SOURCES = {
    'ff_playerids': DataSourceConfig(
        r_call='load_ff_playerids()',
        table='ff_playerids',
        unique_keys=['mfl_id'],
        strategy='full_refresh',
        history_table='nflfastr_ff_playerids_hist',
        databases=[],  # Bucket-only: no database routing
        bucket=True,
        transforms={}
    ),
    'ff_opportunity': DataSourceConfig(
        r_call='load_ff_opportunity(seasons = TRUE, stat_type = c("weekly", "pbp_pass", "pbp_rush"), model_version = c("latest", "v1.0.0"))',
        table='ff_opportunity',
        unique_keys=['player_id', 'full_name', 'season', 'week'],  # V2 uses full_name too
        strategy='full_refresh',
        history_table='nflfastr_ff_opportunity_hist',
        chunksize=2000,
        databases=[],  # Bucket-only: no database routing
        bucket=True,
        transforms={}
    ),
    
    # Missing Fantasy source from V2 - Batch 2
    'ff_rankings': DataSourceConfig(
        r_call='load_ff_rankings(type = c("draft", "week", "all"))',
        table='ff_rankings',
        unique_keys=['id', 'pos', 'ecr_type', 'page_type'],
        strategy='full_refresh',
        history_table='nflfastr_ff_rankings_hist',
        databases=[],  # Bucket-only: no database routing
        bucket=True,
        transforms={}
    )
}

# Draft and combine data with V2 parity fields
# NOTE: Draft tables are bucket-only (no database routing in production)
# Raw data is stored in cloud storage; warehouse/API tables query from bucket
DRAFT_DATA_SOURCES = {
    'draft_picks': DataSourceConfig(
        r_call='load_draft_picks(seasons = TRUE, file_type = "parquet")',
        table='draft_picks',
        unique_keys=['season', 'round', 'pick'],
        strategy='full_refresh',
        history_table='nflfastr_draft_picks_hist',
        databases=[],  # Bucket-only: no database routing
        bucket=True,
        transforms={}
    ),
    'combine': DataSourceConfig(
        r_call='load_combine(seasons = TRUE)',
        table='combine',
        unique_keys=['season', 'player_name', 'pos', 'school'],
        strategy='full_refresh',
        history_table='nflfastr_combine_hist',
        databases=[],  # Bucket-only: no database routing
        bucket=True,
        transforms={}
    )
}

# Health and injury data with V2 parity fields
# NOTE: Health tables are bucket-only (no database routing in production)
# Raw data is stored in cloud storage; warehouse/API tables query from bucket
HEALTH_DATA_SOURCES = {
    'injuries': DataSourceConfig(
        # NOTE: Critical R call configuration for injury data
        # - MUST use 'seasons = TRUE' to load all historical data (2009-2024)
        # - DO NOT use 'file_type = "parquet"' as it causes 0 rows (current season parquet files may not exist)
        # - This loads ~84k rows of historical injury data from nflreadr package
        # - Tested 2025-10-25: 'seasons = TRUE' returns 84,684 rows vs 'file_type = "parquet"' returns 0 rows
        r_call='load_injuries(seasons = TRUE)',
        table='injuries',
        unique_keys=['season', 'week', 'team', 'full_name'],
        strategy='full_refresh',
        min_year=2009,
        history_table='nflfastr_injuries_hist',
        databases=[],  # Bucket-only: no database routing
        bucket=True,
        transforms={}
    )
}

# Teams data sources with V2 parity fields - Batch 3: Missing Teams Sources
# NOTE: Most team tables are bucket-only, EXCEPT schedules and teams which need production DB for API access
TEAMS_DATA_SOURCES = {
    'contracts': DataSourceConfig(
        r_call='nflreadr::load_contracts()',
        table='contracts',
        unique_keys=['player', 'team', 'year_signed', 'value', 'years'],
        strategy='full_refresh',
        history_table='nflfastr_contracts_hist',
        databases=[],  # Bucket-only: no database routing
        bucket=True,
        transforms={}
    ),
    'schedules': DataSourceConfig(
        r_call='nflfastR::fast_scraper_schedules()',
        table='schedules',
        unique_keys=['game_id'],
        strategy='full_refresh',
        history_table='nflfastr_schedules_hist',
        databases=[DatabasePrefixes.LOCAL_DEV, DatabasePrefixes.API_PRODUCTION],  # API table - needs production DB
        bucket=True,
        transforms={DatabasePrefixes.API_PRODUCTION: [TransformNames.PARSE_DATES]},  # Removed STANDARDIZE_TEAMS
        standardize_teams=True,  # Has home_team, away_team columns
        numeric_cols=[
            'season', 'week', 'away_score', 'home_score', 'total', 'overtime',
            'away_rest', 'home_rest', 'away_moneyline', 'home_moneyline',
            'spread_line', 'away_spread_odds', 'home_spread_odds', 'total_line',
            'under_odds', 'over_odds', 'div_game', 'temp', 'wind'
        ]
    ),
    'teams': DataSourceConfig(
        r_call='nflreadr::load_teams()',
        table='teams',
        unique_keys=['team_abbr'],
        strategy='full_refresh',
        history_table='nflfastr_teams_hist',
        databases=[DatabasePrefixes.LOCAL_DEV, DatabasePrefixes.API_PRODUCTION],  # API table - needs production DB
        bucket=True,
        transforms={},  # Removed STANDARDIZE_TEAMS transform
        standardize_teams=True  # Has team_abbr column
    ),
    'depth_chart': DataSourceConfig(
        r_call='nflreadr::load_depth_charts()',
        table='depth_chart',
        unique_keys=[],  # V2 has empty unique_keys due to schema changes and duplicates
        strategy='full_refresh',  # V2 changed from incremental due to schema incompatibility
        min_year=2001,
        history_table='nflfastr_depth_chart_hist',
        databases=[],  # Bucket-only: no database routing
        bucket=True,
        transforms={}
    )
}

# Grouped data sources - Complete V2 parity with 26 total sources
DATA_SOURCE_GROUPS = {
    'nfl_data': NFL_DATA_SOURCES,
    'fantasy': FANTASY_DATA_SOURCES,
    'draft': DRAFT_DATA_SOURCES,
    'health': HEALTH_DATA_SOURCES,
    'teams': TEAMS_DATA_SOURCES
}

def log_datasource_stats():
    """Log data source configuration statistics."""
    total_sources = sum(len(group) for group in DATA_SOURCE_GROUPS.values())
    incremental_count = sum(1 for group in DATA_SOURCE_GROUPS.values()
                            for config in group.values() if config.strategy == 'incremental')
    full_refresh_count = total_sources - incremental_count

    _logger.info(f"Data source configuration loaded: {total_sources} total sources across {len(DATA_SOURCE_GROUPS)} groups")
    _logger.info(f"Strategy distribution: {incremental_count} incremental, {full_refresh_count} full_refresh")

    # Log group statistics
    for group_name, group_sources in DATA_SOURCE_GROUPS.items():
        _logger.debug(f"Group '{group_name}': {len(group_sources)} sources")


# ============================================================================
# WAREHOUSE COLUMN REQUIREMENTS
# ============================================================================
# Defines minimal column sets needed for each warehouse table to reduce memory usage.
# Used by dimension_orchestrator.py to determine if DataFrameEngine is needed.
#
# ⚠️ CRITICAL CONFIGURATION RULES:
# ---------------------------------
# The 'source_table' field determines warehouse build strategy and memory usage:
#
# 1. SINGLE-SOURCE (String Value):
#    source_table: 'play_by_play'
#    → Creates DataFrameEngine loading ALL seasons of play_by_play
#    → High memory: ~1.5GB for 27 seasons
#    → Use ONLY when transformation actually uses play_by_play data
#    Example: dim_game, dim_drive, fact_play
#
# 2. MULTI-SOURCE (List of Strings):
#    source_table: ['players', 'wkly_rosters']
#    → NO DataFrameEngine created - transformation loads its own data
#    → Low memory: only loads what it needs via BucketAdapter
#    → Use when transformation reads from multiple bucket tables
#    Example: dim_player, injuries, player_availability
#
# 3. GENERATED (None):
#    source_table: None
#    → NO DataFrameEngine created - transformation generates data
#    → Minimal memory: transformation creates from scratch
#    → Use for date ranges, lookups, etc.
#    Example: dim_date
#
# 4. WAREHOUSE-SOURCED (List with 'dim_*' or 'fact_*'):
#    source_table: ['dim_game']  ← MUST BE A LIST!
#    → NO DataFrameEngine created - transformation reads from warehouse bucket
#    → Low memory: only loads upstream warehouse table
#    → Use when transformation enriches existing warehouse table
#    Example: dim_game_weather (reads dim_game, adds weather parsing)
#
# ⚠️ COMMON BUG: Using string instead of list for warehouse-sourced tables
#    ❌ WRONG: source_table: 'dim_game'  (treated as single-source, loads PBP!)
#    ✅ RIGHT: source_table: ['dim_game']  (multi-source, skips PBP)
#
# Memory Impact:
# - Full PBP: 250+ columns = ~4 GB for 27 seasons (~2 minutes to load)
# - With column pruning: 5-35 columns = ~400 MB for 27 seasons
# - Multi-source/Generated: <50 MB (no PBP loading, <3 seconds)
#
# Pattern: Analyzed from actual transformation code usage
# - dim_game: From dimensions_core.py + cleaning_dimensions.py
# - dim_player: From dimensions_player.py + cleaning_dimensions.py
# - dim_drive: From dimensions_calendar.py
# - fact_play: From sql_templates_facts.py + cleaning_facts.py
# - fact_player_play: From sql_templates_facts.py + cleaning_facts.py
# ============================================================================

WAREHOUSE_COLUMN_REQUIREMENTS = {
    'dim_game': {
        'source_table': 'play_by_play',
        'required': [
            # Core identifiers (from dimension_game.py)
            'game_id', 'season', 'game_date', 'week', 'home_team', 'away_team',
            # Game scores (required for ML feature engineering)
            'total_home_score', 'total_away_score',
            # Game Metadata
            'weather',
            # Play statistics for aggregation (from dimension_game.py:50-77)
            'yards_gained', 'touchdown', 'interception', 'fumble_lost',
            'field_goal_attempt', 'punt_attempt', 'penalty', 'penalty_yards'
        ],
        'optional': [
            # Game context (from dimension_game.py:40-58)
            'season_type', 'stadium', 'roof', 'surface', 'weather', 'temp', 'wind',
            # Game type indicators
            'div_game', 'result', 'total', 'spread_line', 'total_line',
            # Additional context
            'home_coach', 'away_coach', 'stadium_id', 'game_stadium', 'location'
        ],
        'memory_reduction': '88%',  # 31 cols vs 250+ (added 8 stat columns for aggregation)
        'notes': 'Aggregates play_by_play to game-level. Requires play stats for SUM aggregation.'
    },
    # 'dim_team': REMOVED - see docs/transformation_removal.md
    # Use commonv2.domain.teams.get_all_teams() for team data instead
    'dim_player': {
        'source_table': ['players', 'wkly_rosters'],  # Multi-source: loads from bucket via BucketAdapter
        'required': [],
        'optional': [],
        'memory_reduction': '100%',  # Doesn't use play_by_play
        'notes': 'Multi-source dimension: loads players + wkly_rosters from bucket using BucketAdapter. Does not use play_by_play DataFrameEngine.'
    },
    'dim_date': {
        'source_table': None,  # Generated from date range
        'required': [],
        'optional': [],
        'memory_reduction': '100%',  # Doesn't use PBP at all
        'notes': 'Generated from date range (1999-present), no PBP data needed'
    },
    'injuries': {
        'source_table': ['raw_nflfastr/injuries', 'raw_nflcom_YYYY/injuries'],  # Multi-source: loads from bucket via BucketAdapter
        'required': [],
        'optional': [],
        'memory_reduction': '100%',  # Doesn't use play_by_play
        'notes': 'Multi-source warehouse: loads from raw_nflfastr + raw_nflcom buckets using BucketAdapter. Does not use play_by_play DataFrameEngine.'
    },
    'player_id_mapping': {
        'source_table': ['players'],  # Multi-source loads from bucket via BucketAdapter
        'required': [],
        'optional': [],
        'memory_reduction': '100%',  # Doesn't use play_by_play
        'notes': 'ID crosswalk table: extracts pfr_player_id ↔ gsis_id mapping from players table for joining snap_counts with injury/depth data. Does not use play_by_play DataFrameEngine.'
    },
    'player_availability': {
        'source_table': ['wkly_rosters', 'injuries', 'depth_chart', 'player_id_mapping'],  # Multi-source: loads from bucket via BucketAdapter
        'required': [],
        'optional': [],
        'memory_reduction': '100%',  # Doesn't use play_by_play
        'notes': 'Unified player availability warehouse: merges wkly_rosters (roster status) + injuries (injury details) + depth_chart (starter designation) + player_id_mapping (ID resolution). Provides comprehensive player status tracking including healthy scratches, IR, suspended, and practice squad. Does not use play_by_play DataFrameEngine.'
    },
    'dim_game_weather': {
        # ✅ CRITICAL: Must be a LIST to avoid loading play_by_play!
        # This table reads dim_game from warehouse bucket (not a raw source),
        # so it's multi-source and should NOT trigger DataFrameEngine creation.
        # See WAREHOUSE COLUMN REQUIREMENTS header for detailed explanation.
        # Performance: ~2-3 seconds vs ~2+ minutes if misconfigured as string
        'source_table': ['dim_game'],  # ← List format = multi-source
        'required': [],
        'optional': [],
        'memory_reduction': '100%',  # Doesn't use play_by_play
        'notes': 'Weather enrichment dimension: loads dim_game from warehouse bucket, parses weather strings to backfill temp/wind, filters for model eligibility (excludes indoor/closed roofs), adds provenance tracking. Does not use play_by_play DataFrameEngine.'
    },
    'dim_drive': {
        'source_table': 'play_by_play',
        'required': [
            # Drive aggregation (from dimensions_calendar.py:120-135)
            'game_id', 'drive', 'posteam', 'defteam', 'play_id', 'yardline_100', 'yards_gained'
        ],
        'optional': [
            # Drive outcomes (from dimensions_calendar.py:130-134)
            'touchdown', 'field_goal_attempt', 'field_goal_result', 'punt_attempt', 'epa'
        ],
        'memory_reduction': '95%',  # 12 cols vs 250+
        'notes': 'Aggregates play_by_play by (game_id, drive) to create drive-level metrics'
    },
    'fact_play': {
        'source_table': 'play_by_play',
        'required': [
            # Core identifiers (from sql_templates_facts.py:60-65)
            'play_id', 'game_id', 'season', 'week',
            # Context (from sql_templates_facts.py:68-80)
            'game_date', 'drive', 'posteam', 'defteam', 'down', 'ydstogo', 'yardline_100',
            # Play details (from sql_templates_facts.py:95-121)
            'play_type', 'yards_gained',
            # Outcomes (critical for ML feature engineering)
            'touchdown', 'first_down', 'interception',
            # Turnovers (critical for ML feature engineering)
            'fumble_lost',
            # Third down conversions (critical for ML feature engineering)
            'third_down_converted', 'third_down_failed'
        ],
        'optional': [
            # Time context (from sql_templates_facts.py:76-79)
            'quarter_seconds_remaining', 'half_seconds_remaining', 'game_seconds_remaining', 'game_half',
            # Analytics (from sql_templates_facts.py:100-103)
            'epa', 'wpa', 'ep', 'wp',
            # Play types (from sql_templates_facts.py:104-108)
            'rush_attempt', 'pass_attempt', 'penalty', 'timeout', 'special_teams_play',
            # Scoring (from sql_templates_facts.py:109-111)
            'posteam_score', 'defteam_score', 'score_differential',
            # Win probability components (from sql_templates_facts.py:112-120)
            'no_score_prob', 'opp_fg_prob', 'opp_safety_prob', 'opp_td_prob',
            'fg_prob', 'safety_prob', 'td_prob',
            'posteam_timeouts_remaining', 'defteam_timeouts_remaining'
        ],
        'memory_reduction': '84%',  # 41 cols vs 250+ (added 6 critical ML columns)
        'notes': 'Full play-by-play with EPA and analytics metrics. Added fumble_lost, third_down_converted/failed for ML feature engineering.'
    },
    'fact_player_play': {
        'source_table': 'play_by_play',
        'required': [
            # Play context (from sql_templates_facts.py:219-230)
            'play_id', 'game_id', 'season', 'drive', 'play_type', 'posteam', 'defteam',
            'down', 'ydstogo', 'yardline_100', 'yards_gained', 'epa',
            # QB involvement (from sql_templates_facts.py:233-239)
            'passer_id', 'passer', 'passing_yards', 'pass_attempt',
            # RB involvement (from sql_templates_facts.py:252-258)
            'rusher_id', 'rusher', 'rushing_yards', 'rush_attempt',
            # WR involvement (from sql_templates_facts.py:271-277)
            'receiver_id', 'receiver', 'receiving_yards', 'complete_pass'
        ],
        'optional': [],
        'memory_reduction': '91%',  # 24 cols vs 250+
        'notes': 'Player-level attribution with passer/rusher/receiver involvement'
    },
    'fact_player_stats': {
        'source_table': 'play_by_play',
        'required': [
            # Core identifiers
            'game_id', 'season', 'week',
            # Player identification
            'passer_player_id', 'passer_player_name',
            'rusher_player_id', 'rusher_player_name',
            'receiver_player_id', 'receiver_player_name'
        ],
        'optional': [
            # Passing stats
            'passing_yards', 'pass_attempt', 'complete_pass', 'interception',
            # Rushing stats
            'rushing_yards', 'rush_attempt',
            # Receiving stats
            'receiving_yards', 'complete_pass',
            # Team context
            'posteam', 'defteam'
        ],
        'memory_reduction': '95%',  # ~15 cols vs 250+
        'notes': 'Player statistics aggregated from play-by-play data'
    }
}


def get_warehouse_columns(table_name: str) -> Optional[List[str]]:
    """
    Get required columns for a warehouse table to enable column pruning.
    
    Args:
        table_name: Warehouse table name (e.g., 'dim_game', 'fact_play')
        
    Returns:
        List of column names to load, or None to load all columns
        
    Example:
        >>> cols = get_warehouse_columns('dim_game')
        >>> # Returns: ['game_id', 'season', 'game_date', 'week', 'home_team', 'away_team', ...]
        >>> engine = create_dataframe_engine('play_by_play', columns=cols)
    """
    if table_name not in WAREHOUSE_COLUMN_REQUIREMENTS:
        _logger.warning(f"No column requirements defined for '{table_name}', will load all columns")
        return None
    
    config = WAREHOUSE_COLUMN_REQUIREMENTS[table_name]
    
    # dim_date doesn't use PBP
    if config['source_table'] is None:
        return None
    
    # Combine required + optional columns
    columns = config['required'] + config['optional']
    
    _logger.debug(
        f"Column pruning for {table_name}: {len(columns)} columns "
        f"(memory reduction: {config['memory_reduction']})"
    )
    
    return columns if columns else None


def list_all_sources() -> List[str]:
    """
    List all available data sources across all groups.
    
    Returns:
        List of all data source names
    """
    _logger.debug("Listing all available data sources across groups")
    all_sources = []
    for group_name, group in DATA_SOURCE_GROUPS.items():
        group_sources = list(group.keys())
        all_sources.extend(group_sources)
        _logger.debug(f"Group '{group_name}': {len(group_sources)} sources - {group_sources}")
    
    _logger.info(f"Total data sources available: {len(all_sources)}")
    return all_sources


def get_sources_by_strategy(strategy: str) -> Dict[str, DataSourceConfig]:
    """
    Get all data sources using a specific loading strategy.
    
    Args:
        strategy: Loading strategy ('incremental' or 'full_refresh')
        
    Returns:
        Dictionary of source names to configurations
    """
    _logger.debug(f"Filtering data sources by strategy: '{strategy}'")
    matching_sources = {}
    
    for group_name, group in DATA_SOURCE_GROUPS.items():
        group_matches = 0
        for source_name, config in group.items():
            if config.strategy == strategy:
                matching_sources[source_name] = config
                group_matches += 1
        
        if group_matches > 0:
            _logger.debug(f"Group '{group_name}': {group_matches} sources match strategy '{strategy}'")
    
    _logger.info(f"Found {len(matching_sources)} data sources with strategy '{strategy}': {list(matching_sources.keys())}")
    return matching_sources


__all__ = [
    'DataSourceConfig',
    'DATA_SOURCE_GROUPS',
    'NFL_DATA_SOURCES',
    'FANTASY_DATA_SOURCES',
    'DRAFT_DATA_SOURCES',
    'HEALTH_DATA_SOURCES',
    'TEAMS_DATA_SOURCES',
    'WAREHOUSE_COLUMN_REQUIREMENTS',
    'list_all_sources',
    'get_sources_by_strategy',
    'get_warehouse_columns',
]
