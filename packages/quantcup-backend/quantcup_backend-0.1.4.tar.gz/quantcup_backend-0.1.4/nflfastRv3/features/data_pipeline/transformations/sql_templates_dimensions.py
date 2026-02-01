"""
SQL template helpers for dimensional transformations.

⚠️ DEPRECATED: These SQL templates are deprecated in favor of bucket-first architecture.
   - Production: Use DataFrameEngine with bucket storage (bucket-first mode)
   - Local/Dev: Database mode still supported as fallback
   - Migration: See warehouse_bucket_implementation_plan_hybird.md

Pattern: Enhanced template functions (4 complexity points)
- Adaptive query building: 2 points
- Column detection logic: +1 point
- Complex field mapping: +1 point

Following REFACTORING_SPECS.md: Stay within complexity budget while preserving V2 sophistication.
"""

import warnings
from sqlalchemy import text
from typing import List, Dict


# Deprecation warning for module
warnings.warn(
    "sql_templates_dimensions module is deprecated. "
    "Use DataFrameEngine with bucket-first architecture instead. "
    "See warehouse_bucket_implementation_plan_hybird.md for migration details.",
    DeprecationWarning,
    stacklevel=2
)


def get_play_data_sql(engine):
    """
    Generate adaptive SQL for game dimension based on available columns.
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    
    Preserves V2's sophisticated column detection while simplifying structure.
    
    Args:
        engine: SQLAlchemy database engine
        
    Returns:
        text: SQL query with adaptive column detection
        
    Raises:
        ValueError: If required columns are missing
    """
    warnings.warn(
        "get_play_data_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    available_cols = _get_available_columns(engine, 'raw_nflfastr', 'play_by_play')
    
    # Required columns (fail if missing)
    required = ['game_id', 'season', 'game_date', 'week', 'home_team', 'away_team']
    missing_required = [col for col in required if col not in available_cols]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")
    
    # Optional columns with smart fallbacks
    optional_cols = {
        'season_type': "'REG'",
        'stadium': "'Unknown'", 
        'roof': "'Unknown'",
        'surface': "'Unknown'",
        'weather': "'Unknown'",
        'temp': 'NULL',
        'wind': 'NULL',
        'div_game': 'false',
        'result': 'NULL',
        'total': 'NULL',
        'spread_line': 'NULL',
        'total_line': 'NULL',
        'home_coach': "'Unknown'",
        'away_coach': "'Unknown'",
        'stadium_id': "'Unknown'",
        'game_stadium': "'Unknown'",
        'location': "'Unknown'"
    }
    
    # Build SELECT clause
    select_parts = []
    for col in required:
        select_parts.append(f"COALESCE({col}, 'Unknown') as {col}")
    
    for col, fallback in optional_cols.items():
        if col in available_cols:
            select_parts.append(col)
        else:
            select_parts.append(f"{fallback} as {col}")
    
    return text(f"""
    SELECT DISTINCT 
        {', '.join(select_parts)}
    FROM raw_nflfastr.play_by_play
    WHERE game_id IS NOT NULL
    ORDER BY game_date, game_id
    """)


def get_team_base_sql():
    """
    Get comprehensive team data from teams table.
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    """
    warnings.warn(
        "get_team_base_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    return text("""
    SELECT 
        team_abbr,
        COALESCE(team_name, team_abbr) as team_name,
        COALESCE(team_id, team_abbr) as team_id,
        COALESCE(team_nick, team_abbr) as team_nick,
        COALESCE(team_conf, 'Unknown') as team_conf,
        COALESCE(team_division, 'Unknown') as team_division,
        COALESCE(team_color, '#000000') as team_color,
        COALESCE(team_color2, '#FFFFFF') as team_color2,
        COALESCE(team_color3, '#000000') as team_color3,
        COALESCE(team_color4, '#FFFFFF') as team_color4,
        team_logo_wikipedia,
        team_logo_espn,
        team_wordmark,
        team_conference_logo,
        team_league_logo,
        team_logo_squared
    FROM raw_nflfastr.teams
    """)


def get_team_stadium_sql(engine):
    """
    Get stadium data with adaptive column detection (V2 feature preserved).
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    
    Args:
        engine: SQLAlchemy database engine
        
    Returns:
        text: SQL query for stadium data with fallbacks
        
    Raises:
        ValueError: If home_team column is missing
    """
    warnings.warn(
        "get_team_stadium_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    available_cols = _get_available_columns(engine, 'raw_nflfastr', 'schedules')
    
    # Required column
    if 'home_team' not in available_cols:
        raise ValueError("home_team column missing from schedules - cannot build stadium mapping")
    
    select_parts = ["home_team as team_abbr"]
    
    # Optional stadium columns with fallbacks
    stadium_cols = {
        'stadium': "'Unknown'",
        'roof': "'Unknown'", 
        'surface': "'Unknown'"
    }
    
    for col, fallback in stadium_cols.items():
        if col in available_cols:
            select_parts.append(f"COALESCE({col}, 'Unknown') as {col}")
        else:
            select_parts.append(f"{fallback} as {col}")
    
    return text(f"""
    SELECT DISTINCT {', '.join(select_parts)}
    FROM raw_nflfastr.schedules
    WHERE home_team IS NOT NULL
    """)


def get_player_base_sql():
    """
    Get comprehensive player data from players table.
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    """
    warnings.warn(
        "get_player_base_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    return text("""
    SELECT DISTINCT
        gsis_id,
        display_name, first_name, last_name, football_name, short_name,
        suffix,
        birth_date, college_name, position, position_group,
        jersey_number, height, weight, years_of_experience, rookie_year,
        draft_club, draft_number, draft_round, college_conference,
        status, esb_id, smart_id, headshot,
        team_abbr as latest_team, season as last_season
    FROM raw_nflfastr.players
    WHERE gsis_id IS NOT NULL
    """)


def get_player_current_team_sql():
    """
    Get current team assignment from most recent roster data.
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    """
    warnings.warn(
        "get_player_current_team_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    return text("""
    WITH latest_roster AS (
        SELECT gsis_id, team, season, week,
               ROW_NUMBER() OVER (PARTITION BY gsis_id ORDER BY season DESC, week DESC) as rn
        FROM raw_nflfastr.rosters
        WHERE gsis_id IS NOT NULL AND team IS NOT NULL
    )
    SELECT gsis_id, team as current_team, season as current_season, week as current_week
    FROM latest_roster WHERE rn = 1
    """)


def get_player_fantasy_ids_sql():
    """
    Get fantasy platform ID mappings.
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    """
    warnings.warn(
        "get_player_fantasy_ids_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    return text("""
    SELECT DISTINCT gsis_id, mfl_id, sportradar_id, fantasypros_id, pff_id,
           sleeper_id, nfl_id, espn_id, yahoo_id, fleaflicker_id, cbs_id,
           pfr_id, cfbref_id, rotowire_id, rotoworld_id, ktc_id, stats_id,
           stats_global_id, fantasy_data_id, swish_id,
           draft_year, draft_round, draft_pick, draft_ovr
    FROM raw_nflfastr.ff_playerids
    WHERE gsis_id IS NOT NULL
    """)


def _get_available_columns(engine, schema: str, table: str) -> List[str]:
    """
    Helper to detect available columns in a table.
    
    Args:
        engine: SQLAlchemy database engine
        schema: Database schema name
        table: Table name
        
    Returns:
        List[str]: Available column names
    """
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = '{schema}' AND table_name = '{table}'
        """))
        return [row[0] for row in result.fetchall()]
