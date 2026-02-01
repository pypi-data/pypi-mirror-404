"""
Schedule domain facade for CommonV2.

Clean facade functions that use existing adapters and domain services.
Following Phase 1 patterns: simple dependency injection, thin facades.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from ..core.logging import get_logger
from .models import GameDataFrame, Season

# Module-level logger for simple utilities (following database.py pattern)
_logger = get_logger('commonv2.domain.schedules')


class SeasonParser:
    """Pure domain service for season parsing with data-driven logic."""
    
    @staticmethod
    def get_current_season(logger=None) -> int:
        """Determine current NFL season from actual schedule data with fallback."""
        logger = logger or _logger
        
        try:
            # Use nfl_data_wrapper to get actual schedule data
            from nfl_data_wrapper import import_schedules
            
            current_year = datetime.now().year
            potential_seasons = [current_year - 1, current_year, current_year + 1]
            
            schedule_df = import_schedules(potential_seasons)
            if not schedule_df.empty and 'season' in schedule_df.columns:
                max_season = int(schedule_df['season'].max())
                
                # Check if current season is over (after Super Bowl)
                current_date = datetime.now()
                first_sunday_feb = SeasonParser._get_first_sunday_of_february(max_season + 1)
                
                if current_date > first_sunday_feb:
                    # Season is over, return next season
                    logger.info(f"Season {max_season} is over (past Super Bowl), returning {max_season + 1}")
                    return max_season + 1
                else:
                    logger.info(f"Current season determined from schedule data: {max_season}")
                    return max_season
            
        except Exception as e:
            logger.warning(f"Failed to get current season from schedule API: {e}, using date-based fallback")
        
        # Fallback to date-based logic
        current_date = datetime.now()
        fallback_season = current_date.year if current_date.month >= 9 else current_date.year - 1
        logger.info(f"Using date-based fallback for current season: {fallback_season}")
        return fallback_season
    
    @staticmethod
    def _get_first_sunday_of_february(year: int) -> datetime:
        """Get the first Sunday of February for Super Bowl timing."""
        feb_first = datetime(year, 2, 1)
        days_until_sunday = (6 - feb_first.weekday()) % 7
        return feb_first + timedelta(days=days_until_sunday)
    
    @staticmethod
    def parse_season_expr(expr: str) -> List[int]:
        """Parse season expressions like '2024', '2020-2024', 'current'."""
        expr = (expr or "").strip().lower()
        
        if not expr:
            return []
        
        if expr == "current":
            return [SeasonParser.get_current_season()]
        
        if "-" in expr:
            parts = expr.split("-", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid range format: {expr}")
            
            start_year = int(parts[0].strip())
            end_year = int(parts[1].strip())
            min_year, max_year = min(start_year, end_year), max(start_year, end_year)
            
            if max_year - min_year > 50:
                raise ValueError(f"Season range too large: {expr}")
            
            return list(range(min_year, max_year + 1))
        
        # Single year
        year = int(expr)
        if not (1920 <= year <= 2050):
            raise ValueError(f"Season year out of range: {year}")
        
        return [year]


class WeekParser:
    """Pure domain service for week parsing with data-driven logic."""
    
    @staticmethod
    def get_current_week(season: Optional[int] = None, logger=None) -> int:
        """Get current week - always the upcoming week, never finished week."""
        logger = logger or _logger
        
        try:
            # Use nfl_data_wrapper to get actual schedule data
            from nfl_data_wrapper import import_schedules
            
            if season is None:
                season = SeasonParser.get_current_season(logger)
            
            schedule_df = import_schedules([season])
            if not schedule_df.empty and 'week' in schedule_df.columns and 'gameday' in schedule_df.columns:
                today = pd.Timestamp.today().normalize()
                schedule_df['gameday'] = pd.to_datetime(schedule_df['gameday']).dt.normalize()
                
                # Find upcoming games (games today or in the future)
                upcoming_games = schedule_df[schedule_df['gameday'] >= today]
                
                if not upcoming_games.empty:
                    current_week = int(upcoming_games['week'].min())
                    logger.info(f"Current week determined from schedule data: Week {current_week}")
                    return current_week
                else:
                    # No upcoming games, season is over - return week 1 of next season
                    logger.info(f"No upcoming games in season {season}, returning Week 1")
                    return 1
            
        except Exception as e:
            logger.warning(f"Failed to get current week from schedule API: {e}, using fallback")
        
        # Fallback to week 1
        logger.info("Using fallback for current week: Week 1")
        return 1
    
    @staticmethod
    def parse_week_expr(expr: str, season: Optional[int] = None) -> List[int]:
        """Parse week expressions like 'current', '5', '1-4', 'playoffs'."""
        expr = (expr or "").strip().lower()
        
        if not expr:
            return []
        
        if expr == "current":
            return [WeekParser.get_current_week(season)]
        
        if expr == "playoffs":
            return list(range(19, 23))  # Weeks 19-22
        
        if "-" in expr:
            parts = expr.split("-", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid week range format: {expr}")
            
            start_week = int(parts[0].strip())
            end_week = int(parts[1].strip())
            min_week, max_week = min(start_week, end_week), max(start_week, end_week)
            
            if max_week - min_week > 22:
                raise ValueError(f"Week range too large: {expr}")
            
            return list(range(min_week, max_week + 1))
        
        # Single week
        week = int(expr)
        if not (1 <= week <= 22):
            raise ValueError(f"Week number out of range: {week}")
        
        return [week]


def get_upcoming_games(weeks_ahead: float = 4.0, current_season: Optional[int] = None,
                      logger=None, schedule_provider=None, team_standardizer=None) -> GameDataFrame:
    """
    Get upcoming NFL games with standardized team names.
    
    Clean facade with direct dependency creation (simplified from DependencyFactory).
    Supports fractional weeks for flexible day-based filtering.
    
    Args:
        weeks_ahead: Number of weeks ahead to include (can be fractional, e.g., 1.5 weeks = 10.5 days)
        current_season: Season year (if None, determines current season)
        logger: Logger instance (optional, for dependency injection)
        schedule_provider: Schedule provider (optional, for dependency injection)
        team_standardizer: Team standardizer (optional, for dependency injection)
        
    Returns:
        pd.DataFrame: Upcoming games with standardized team names
    """
    from .adapters import NFLDataScheduleProvider, TeamNameStandardizer
    from ..utils.helpers import standardize_team_columns_in_dataframe, filter_upcoming_games, process_game_times
    
    # Create dependencies directly
    logger = logger or _logger
    
    if schedule_provider is None:
        schedule_provider = NFLDataScheduleProvider(logger)
    
    if team_standardizer is None:
        team_standardizer = TeamNameStandardizer()
    
    # Use domain service for season logic
    season = current_season or SeasonParser.get_current_season()
    
    # Use adapter to get raw data
    schedule = schedule_provider.get_schedule_data([season])
    if schedule.empty:
        logger.warning(f"No schedule data found for {season}")
        return pd.DataFrame()
    
    # Use helper function to standardize team columns (eliminates duplication)
    schedule = standardize_team_columns_in_dataframe(schedule, team_standardizer, logger)
    
    # Process game times to create proper datetime fields
    schedule = process_game_times(schedule, logger)
    
    # Use helper function for filtering logic (eliminates duplication)
    upcoming = filter_upcoming_games(schedule, weeks_ahead=weeks_ahead, logger=logger)
    
    logger.info(f"Found {len(upcoming)} upcoming games in next {weeks_ahead} weeks")
    return upcoming


def get_games_by_week(week: int, season: Optional[int] = None, logger=None, 
                     schedule_provider=None, team_standardizer=None) -> GameDataFrame:
    """
    Get games for a specific week and season.
    
    Clean facade with direct dependency creation (simplified from DependencyFactory).
    
    Args:
        week: NFL week number
        season: Season year (if None, determines current season)
        logger: Logger instance (optional, for dependency injection)
        schedule_provider: Schedule provider (optional, for dependency injection)
        team_standardizer: Team standardizer (optional, for dependency injection)
        
    Returns:
        pd.DataFrame: Games for the specified week/season
    """
    from .adapters import NFLDataScheduleProvider, TeamNameStandardizer
    from ..utils.helpers import standardize_team_columns_in_dataframe, filter_games_by_week, process_game_times
    
    # Create dependencies directly
    logger = logger or _logger
    
    if schedule_provider is None:
        schedule_provider = NFLDataScheduleProvider(logger)
    
    if team_standardizer is None:
        team_standardizer = TeamNameStandardizer()
    
    # Use domain service for season logic
    season = season or SeasonParser.get_current_season()
    
    # Use adapter to get raw data
    schedule = schedule_provider.get_schedule_data([season])
    if schedule.empty:
        logger.warning(f"No schedule data found for {season}")
        return pd.DataFrame()
    
    # Use helper function to standardize team columns (eliminates duplication)
    schedule = standardize_team_columns_in_dataframe(schedule, team_standardizer, logger)
    
    # Process game times to create proper datetime fields
    schedule = process_game_times(schedule, logger)
    
    # Use helper function for filtering logic (eliminates duplication)
    week_games = filter_games_by_week(schedule, week, logger)
    
    logger.info(f"Found {len(week_games)} games for Week {week}, {season}")
    return week_games


def get_schedule_for_seasons(seasons: List[int], logger=None, schedule_provider=None, 
                           team_standardizer=None) -> GameDataFrame:
    """
    Get schedule data for multiple seasons with standardized team names.
    
    Clean facade with direct dependency creation (simplified from DependencyFactory).
    
    Args:
        seasons: List of season years to fetch
        logger: Logger instance (optional, for dependency injection)
        schedule_provider: Schedule provider (optional, for dependency injection)
        team_standardizer: Team standardizer (optional, for dependency injection)
        
    Returns:
        pd.DataFrame: Schedule data for all requested seasons
    """
    from .adapters import NFLDataScheduleProvider, TeamNameStandardizer
    from ..utils.helpers import standardize_team_columns_in_dataframe, validate_season_range, process_game_times
    
    # Create dependencies directly
    logger = logger or _logger
    
    if schedule_provider is None:
        schedule_provider = NFLDataScheduleProvider(logger)
    
    if team_standardizer is None:
        team_standardizer = TeamNameStandardizer()
    
    # Use helper function to validate seasons
    validated_seasons = validate_season_range(seasons, logger)
    
    # Use adapter to get raw data
    schedule = schedule_provider.get_schedule_data(validated_seasons)
    if schedule.empty:
        logger.warning(f"No schedule data found for seasons: {validated_seasons}")
        return pd.DataFrame()
    
    # Use helper function to standardize team columns (eliminates duplication)
    schedule = standardize_team_columns_in_dataframe(schedule, team_standardizer, logger)
    
    # Process game times to create proper datetime fields
    schedule = process_game_times(schedule, logger)
    
    logger.info(f"Retrieved {len(schedule)} games across {len(validated_seasons)} seasons")
    return schedule


def validate_schedule_data(df: GameDataFrame, logger=None) -> bool:
    """
    Validate schedule DataFrame has required columns.
    
    Uses centralized UnifiedDataValidator to reduce duplication.
    """
    from ..utils.validation.core import UnifiedDataValidator
    
    validator = UnifiedDataValidator(logger)
    return validator.validate_schedule_dataframe(df)
