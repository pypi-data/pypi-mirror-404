"""
Domain module for CommonV2.

Clean, testable business logic following Phase 1 patterns:
- Domain models for type safety
- Thin adapters for external dependencies
- Pure domain services for business logic
- Simple dependency injection via parameters
"""

# Domain models
from .models import Team, Game, Season, TeamDataFrame, GameDataFrame

# Adapters and services
from .adapters import (
    DatabaseTeamRepository, 
    NFLDataScheduleProvider, 
    TeamNameStandardizer
)

# Public facade functions
from .teams import (
    get_all_teams, 
    validate_team_data,
    standardize_team_name, 
    standardize_team_column,
    get_team_abbreviation,
    get_team_full_name,
    validate_team_names,
    get_all_team_abbreviations,
    get_all_team_names
)
from .schedules import (
    get_upcoming_games,
    get_games_by_week,
    get_schedule_for_seasons,
    validate_schedule_data,
    SeasonParser,
    WeekParser
)

__all__ = [
    # Domain models
    'Team', 
    'Game', 
    'Season', 
    'TeamDataFrame', 
    'GameDataFrame',
    
    # Adapters and services
    'DatabaseTeamRepository', 
    'NFLDataScheduleProvider', 
    'TeamNameStandardizer',
    'SeasonParser',
    'WeekParser',
    
    # Teams facade
    'get_all_teams', 
    'validate_team_data',
    'standardize_team_name', 
    'standardize_team_column',
    'get_team_abbreviation',
    'get_team_full_name',
    'validate_team_names',
    'get_all_team_abbreviations',
    'get_all_team_names',
    
    # Schedules facade
    'get_upcoming_games',
    'get_games_by_week',
    'get_schedule_for_seasons',
    'validate_schedule_data'
]
