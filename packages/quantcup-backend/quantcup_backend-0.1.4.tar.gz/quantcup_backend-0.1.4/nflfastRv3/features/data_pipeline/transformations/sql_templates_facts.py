"""
SQL templates for fact table transformations.

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
    "sql_templates_facts module is deprecated. "
    "Use DataFrameEngine with bucket-first architecture instead. "
    "See warehouse_bucket_implementation_plan_hybird.md for migration details.",
    DeprecationWarning,
    stacklevel=2
)


def get_fact_play_sql(engine):
    """
    Generate adaptive SQL for fact_play with V2's sophisticated column detection.
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    
    Preserves V2 features:
    - Dynamic column detection (40+ potential columns)
    - Intelligent fallbacks for missing columns
    - Complex drive_key construction logic
    
    Args:
        engine: SQLAlchemy database engine
        
    Returns:
        text: SQL query with adaptive column detection
        
    Raises:
        ValueError: If required columns are missing
    """
    warnings.warn(
        "get_fact_play_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    available_cols = _get_available_columns(engine, 'raw_nflfastr', 'play_by_play')
    
    # Required columns (cannot build without these)
    required = ['play_id', 'game_id']
    missing_required = [col for col in required if col not in available_cols]
    if missing_required:
        raise ValueError(f"Cannot build fact_play: missing required columns {missing_required}")
    
    select_parts = ['play_id', 'game_id']
    
    # Core context columns with fallbacks (V2 logic preserved)
    context_mapping = {
        'game_date': 'game_date',
        'drive': 'drive', 
        'posteam': 'posteam',
        'defteam': 'defteam',
        'down': 'down',
        'ydstogo': 'ydstogo',
        'yardline_100': 'yardline_100',
        'quarter_seconds_remaining': 'quarter_seconds_remaining',
        'half_seconds_remaining': 'half_seconds_remaining',
        'game_seconds_remaining': 'game_seconds_remaining',
        'game_half': 'game_half'
    }
    
    for col, select_expr in context_mapping.items():
        if col in available_cols:
            select_parts.append(select_expr)
        else:
            select_parts.append(f"NULL as {col}")
    
    # Drive key construction (V2 logic preserved)
    if 'drive' in available_cols:
        select_parts.append("CONCAT(game_id, '-', COALESCE(drive, 0)) as drive_key")
    else:
        select_parts.append("CONCAT(game_id, '-', play_id) as drive_key")
    
    # Performance metrics with fallbacks (V2 sophistication preserved)
    metrics_mapping = {
        'play_type': "'unknown'",
        'yards_gained': "0",
        'touchdown': "false", 
        'first_down': "false",
        'epa': "NULL",
        'wpa': "NULL",
        'ep': "NULL",
        'wp': "NULL",
        'rush_attempt': "false",
        'pass_attempt': "false",
        'penalty': "false",
        'timeout': "false",
        'special_teams_play': "false",
        'posteam_score': "0",
        'defteam_score': "0",
        'score_differential': "0",
        'no_score_prob': "NULL",
        'opp_fg_prob': "NULL",
        'opp_safety_prob': "NULL",
        'opp_td_prob': "NULL",
        'fg_prob': "NULL",
        'safety_prob': "NULL",
        'td_prob': "NULL",
        'posteam_timeouts_remaining': "NULL",
        'defteam_timeouts_remaining': "NULL"
    }
    
    for col, fallback in metrics_mapping.items():
        if col in available_cols:
            select_parts.append(col)
        else:
            select_parts.append(f"{fallback} as {col}")
    
    return text(f"""
    SELECT {', '.join(select_parts)}
    FROM raw_nflfastr.play_by_play
    WHERE play_id IS NOT NULL AND game_id IS NOT NULL
    ORDER BY game_id, play_id
    """)


def get_fact_player_stats_sql():
    """
    Generate SQL for fact_player_stats with snap counts integration.
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    
    Preserves V2 features:
    - Multi-table joins (player_stats + snap_counts)
    - Comprehensive performance metrics
    
    Returns:
        text: SQL query for player stats with snap counts
    """
    warnings.warn(
        "get_fact_player_stats_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    return text("""
    SELECT 
        ps.player_id, ps.player_name, ps.player_display_name,
        ps.position, ps.position_group, ps.recent_team,
        ps.season, ps.week, ps.season_type, ps.opponent_team,
        
        -- Passing stats (V2 comprehensive set)
        ps.completions, ps.attempts, ps.passing_yards, ps.passing_tds,
        ps.interceptions, ps.sacks, ps.sack_yards, ps.sack_fumbles,
        ps.sack_fumbles_lost, ps.passing_air_yards, ps.passing_yards_after_catch,
        ps.passing_first_downs, ps.passing_epa, ps.passing_2pt_conversions,
        ps.pacr, ps.dakota,
        
        -- Rushing stats
        ps.carries, ps.rushing_yards, ps.rushing_tds, ps.rushing_fumbles,
        ps.rushing_fumbles_lost, ps.rushing_first_downs, ps.rushing_epa,
        ps.rushing_2pt_conversions,
        
        -- Receiving stats  
        ps.receptions, ps.targets, ps.receiving_yards, ps.receiving_tds,
        ps.receiving_fumbles, ps.receiving_fumbles_lost, ps.receiving_air_yards,
        ps.receiving_yards_after_catch, ps.receiving_first_downs, ps.receiving_epa,
        ps.receiving_2pt_conversions, ps.racr, ps.target_share, ps.air_yards_share,
        ps.wopr,
        
        -- Special teams and fantasy
        ps.special_teams_tds, ps.fantasy_points, ps.fantasy_points_ppr,
        
        -- Snap counts integration (V2 feature)
        sc.offense_snaps, sc.offense_pct, sc.defense_snaps, sc.defense_pct,
        sc.st_snaps, sc.st_pct
        
    FROM raw_nflfastr.player_stats ps
    LEFT JOIN raw_nflfastr.snap_counts sc ON (
        ps.player_id = sc.pfr_player_id 
        AND ps.season = sc.season 
        AND ps.week = sc.week
        AND ps.recent_team = sc.team
    )
    WHERE ps.player_id IS NOT NULL
    ORDER BY ps.season, ps.week, ps.player_id
    """)


def get_fact_player_play_sql():
    """
    Generate SQL for fact_player_play with individual performance attribution.
    
    ⚠️ DEPRECATED: Use DataFrameEngine with bucket storage instead.
    
    Preserves V2 features:
    - Player involvement detection
    - Position-specific performance metrics
    - EPA and opportunity attribution
    
    Returns:
        text: SQL query for player-play facts
    """
    warnings.warn(
        "get_fact_player_play_sql() is deprecated. Use DataFrameEngine with bucket-first mode.",
        DeprecationWarning,
        stacklevel=2
    )
    return text("""
    SELECT 
        p.play_id,
        p.game_id,
        p.drive,
        p.play_type,
        p.posteam,
        p.defteam,
        p.down,
        p.ydstogo,
        p.yardline_100,
        p.yards_gained,
        p.epa,
        
        -- Quarterback involvement
        p.passer_id as player_id,
        p.passer as player_name,
        'QB' as involvement_type,
        'offense' as side_of_ball,
        p.passing_yards as stat_value,
        p.pass_attempt::int as opportunity_count,
        CASE WHEN p.pass_attempt = true THEN p.epa ELSE 0 END as attributed_epa
        
    FROM raw_nflfastr.play_by_play p
    WHERE p.passer_id IS NOT NULL
        AND p.pass_attempt = true
    
    UNION ALL
    
    SELECT 
        p.play_id, p.game_id, p.drive, p.play_type, p.posteam, p.defteam,
        p.down, p.ydstogo, p.yardline_100, p.yards_gained, p.epa,
        
        -- Rusher involvement  
        p.rusher_id as player_id,
        p.rusher as player_name,
        'RB' as involvement_type,
        'offense' as side_of_ball,
        p.rushing_yards as stat_value,
        p.rush_attempt::int as opportunity_count,
        CASE WHEN p.rush_attempt = true THEN p.epa ELSE 0 END as attributed_epa
        
    FROM raw_nflfastr.play_by_play p
    WHERE p.rusher_id IS NOT NULL
        AND p.rush_attempt = true
    
    UNION ALL
    
    SELECT 
        p.play_id, p.game_id, p.drive, p.play_type, p.posteam, p.defteam,
        p.down, p.ydstogo, p.yardline_100, p.yards_gained, p.epa,
        
        -- Receiver involvement
        p.receiver_id as player_id,
        p.receiver as player_name,
        'WR' as involvement_type,  
        'offense' as side_of_ball,
        p.receiving_yards as stat_value,
        1 as opportunity_count,  -- Each target is an opportunity
        CASE WHEN p.complete_pass = true THEN p.epa ELSE 0 END as attributed_epa
        
    FROM raw_nflfastr.play_by_play p
    WHERE p.receiver_id IS NOT NULL
        AND p.pass_attempt = true
    
    ORDER BY game_id, play_id, player_id
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
