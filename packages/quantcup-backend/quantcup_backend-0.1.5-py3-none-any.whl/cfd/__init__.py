"""College Football Data API wrapper."""

from .client import (
    # Games
    get_games,
    get_game_teams,
    get_game_players,
    get_game_media,
    get_calendar,
    get_scoreboard,
    
    # Teams
    get_teams,
    get_fbs_teams,
    get_roster,
    get_talent,
    get_team_matchup,
    
    # Conferences
    get_conferences,
    
    # Rankings
    get_rankings,
    
    # Betting
    get_lines,
    
    # Recruiting
    get_recruiting_players,
    get_recruiting_teams,
    
    # Ratings
    get_sp_ratings,
    get_srs_ratings,
    get_elo_ratings,
    get_fpi_ratings,
    
    # Stats
    get_player_season_stats,
    get_team_season_stats,
    get_advanced_team_season_stats,
    
    # Players
    get_player_search,
    get_player_usage,
    get_returning_production,
    
    # Drives
    get_drives,
    
    # Plays
    get_plays,
    get_play_types,
    get_play_stats,
    
    # Coaches
    get_coaches,
    
    # Venues
    get_venues,
)

__all__ = [
    'get_games',
    'get_game_teams',
    'get_game_players',
    'get_game_media',
    'get_calendar',
    'get_scoreboard',
    'get_teams',
    'get_fbs_teams',
    'get_roster',
    'get_talent',
    'get_team_matchup',
    'get_conferences',
    'get_rankings',
    'get_lines',
    'get_recruiting_players',
    'get_recruiting_teams',
    'get_sp_ratings',
    'get_srs_ratings',
    'get_elo_ratings',
    'get_fpi_ratings',
    'get_player_season_stats',
    'get_team_season_stats',
    'get_advanced_team_season_stats',
    'get_player_search',
    'get_player_usage',
    'get_returning_production',
    'get_drives',
    'get_plays',
    'get_play_types',
    'get_play_stats',
    'get_coaches',
    'get_venues',
]