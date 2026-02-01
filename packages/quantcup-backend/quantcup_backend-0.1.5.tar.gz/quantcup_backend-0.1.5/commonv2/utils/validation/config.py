"""
Shared Validation Configuration

Consolidates duplicated configuration from:
- nflfastRv3/features/data_pipeline/quality_checks.py (TABLE_SPECIFIC_TYPE_RULES)
- commonv2/_data/adapters.py (_get_table_specific_rules)

Pattern: Simple configuration module (1 complexity point)
"""

# Consolidated table-specific type rules (single source of truth)
TABLE_SPECIFIC_TYPE_RULES = {
    'ff_playerids': {
        'draft_pick': 'Int64',
        'draft_round': 'Int64',
        'height': 'Int64',
        'weight': 'Int64',
        'draft_year': 'Int64',
        'db_season': 'Int64'
    },
    'ff_opportunity': {
        'week': 'Int64',
        'pass_touchdown': 'Int64',
        'rec_air_yards': 'Int64',
        'rec_yards_gained': 'Int64',
        'rush_yards_gained': 'Int64',
        'pass_completions': 'Int64',
        'receptions': 'Int64',
        'pass_attempt': 'Int64',
        'rec_attempt': 'Int64',
        'rush_attempt': 'Int64',
        'pass_air_yards': 'Int64',
        'pass_first_down': 'Int64',
        'rec_first_down': 'Int64',
        'rush_first_down': 'Int64',
        'pass_interception': 'Int64',
        'rec_interception': 'Int64',
        'rec_fumble_lost': 'Int64',
        'rush_fumble_lost': 'Int64',
        'total_yards_gained': 'Int64',
        'total_touchdown': 'Int64',
        'total_first_down': 'Int64',
        'pass_two_point_conv': 'Int64',
        'rec_two_point_conv': 'Int64',
        'rush_two_point_conv': 'Int64',
        'rec_touchdown': 'Int64',
        'rush_touchdown': 'Int64'
    },
    'ff_rankings': {
        'rank': 'Int64',
        'ecr': 'Int64'
    },
    'play_by_play': {
        # Core integer columns that may contain NaN must be nullable Int64
        'play_id': 'Int64', 'season': 'Int64', 'week': 'Int64', 'qtr': 'Int64',
        'down': 'Int64', 'ydstogo': 'Int64', 'drive': 'Int64', 'drive_play_id_ended': 'Int64',
        'home_score': 'Int64', 'away_score': 'Int64', 'home_timeouts_remaining': 'Int64',
        'away_timeouts_remaining': 'Int64', 'yardline_100': 'Int64', 'goal_to_go': 'Int64',
        'quarter_seconds_remaining': 'Int64', 'half_seconds_remaining': 'Int64',
        'game_seconds_remaining': 'Int64', 'quarter_end': 'Int64', 'sp': 'Int64',
        
        # Additional integer fields that often arrive as float due to NaNs
        'yards_gained': 'Int64', 'ydsnet': 'Int64', 'air_yards': 'Int64',
        'yards_after_catch': 'Int64', 'kick_distance': 'Int64',
        
        # Boolean columns as nullable boolean
        'qb_kneel': 'boolean', 'qb_spike': 'boolean', 'shotgun': 'boolean',
        'no_huddle': 'boolean', 'qb_dropback': 'boolean', 'qb_scramble': 'boolean',
        'timeout': 'boolean', 'aborted_play': 'boolean', 'pass': 'boolean',
        'rush': 'boolean', 'special': 'boolean', 'play': 'boolean',
        'out_of_bounds': 'boolean', 'home_opening_kickoff': 'boolean',
        
        # EPA/XYAC/XPass columns - force to Float64 for true decimals
        'epa': 'Float64', 'wpa': 'Float64', 'wp': 'Float64', 'def_wp': 'Float64',
        'home_wp': 'Float64', 'away_wp': 'Float64', 'vegas_wp': 'Float64',
        'qb_epa': 'Float64', 'xyac_epa': 'Float64', 'xyac_mean_yardage': 'Float64',
        'xyac_median_yardage': 'Float64', 'xpass': 'Float64', 'pass_oe': 'Float64',
    }
}

# Quality thresholds (from quality_checks.py)
QUALITY_THRESHOLDS = {
    'data_loss_warning': 1.0,
    'data_loss_critical': 5.0,
    'null_percentage_warning': 15.0,
    'null_percentage_critical': 25.0,
    'type_conversion_failure_threshold': 0.1,
    'schema_change_major_threshold': 20
}

# NFL table schemas (from nflfastRv3/shared/validation.py)
NFL_SCHEMAS = {
    'play_by_play': [
        'game_id', 'play_id', 'season', 'week', 'posteam', 'defteam',
        'down', 'ydstogo', 'yardline_100', 'play_type'
    ],
    'schedules': [
        'game_id', 'season', 'week', 'home_team', 'away_team', 'gameday'
    ],
    'rosters': [
        'season', 'team', 'position', 'player_name', 'player_id'
    ]
}