"""
Domain helper functions for common patterns.

Consolidates repeated patterns found across domain facade functions
to reduce duplication and improve maintainability.
"""

import pandas as pd
from typing import Optional, List
from ..core.logging import get_logger
from ..domain.models import GameDataFrame

# Module-level logger
_logger = get_logger('commonv2.utils.helpers')


def standardize_team_columns_in_dataframe(
    df: GameDataFrame, 
    standardizer=None, 
    logger=None,
    output_format: str = 'abbr'
) -> GameDataFrame:
    """
    Apply team standardization to home_team/away_team columns automatically.
    
    Eliminates the repeated pattern found in:
    - get_upcoming_games()
    - get_games_by_week() 
    - get_schedule_for_seasons()
    
    Args:
        df: DataFrame with potential home_team/away_team columns
        standardizer: Team name standardizer (optional, for dependency injection)
        logger: Logger instance (optional, for dependency injection)
        output_format: Format for team names ('abbr' or 'full')
        
    Returns:
        DataFrame with standardized team columns
    """
    logger = logger or _logger
    
    if df.empty:
        return df
    
    # Create standardizer if not provided
    if standardizer is None:
        from ..domain.adapters import TeamNameStandardizer
        standardizer = TeamNameStandardizer()
    
    df_standardized = df.copy()
    columns_standardized = []
    
    # Standardize home_team column if present
    if 'home_team' in df_standardized.columns:
        df_standardized = standardizer.standardize_dataframe_column(
            df_standardized, 'home_team', output_format=output_format
        )
        columns_standardized.append('home_team')
    
    # Standardize away_team column if present
    if 'away_team' in df_standardized.columns:
        df_standardized = standardizer.standardize_dataframe_column(
            df_standardized, 'away_team', output_format=output_format
        )
        columns_standardized.append('away_team')
    
    if columns_standardized:
        logger.debug(f"Standardized team columns: {columns_standardized} to {output_format} format")
    else:
        logger.debug("No team columns found to standardize")
    
    return df_standardized


def filter_upcoming_games(
    schedule: GameDataFrame,
    weeks_ahead: float = 4.0,
    days_ahead: Optional[int] = None,
    logger=None
) -> GameDataFrame:
    """
    Filter schedule DataFrame to upcoming games.
    
    Extracts the filtering logic that was repeated in schedule functions.
    Supports both week-based and day-based filtering for flexibility.
    
    Args:
        schedule: Schedule DataFrame with 'gameday' column
        weeks_ahead: Number of weeks ahead to include (can be fractional)
        days_ahead: Number of days ahead to include (takes precedence if provided)
        logger: Logger instance (optional, for dependency injection)
        
    Returns:
        Filtered DataFrame with upcoming games
    """
    logger = logger or _logger
    
    if schedule.empty:
        return schedule
    
    if 'gameday' not in schedule.columns:
        logger.warning("No 'gameday' column found in schedule data")
        return schedule
    
    # Ensure gameday is datetime and normalized
    schedule_filtered = schedule.copy()
    schedule_filtered['gameday'] = pd.to_datetime(schedule_filtered['gameday']).dt.normalize()
    
    # Calculate time delta based on parameter priority
    if days_ahead is not None:
        time_delta = pd.Timedelta(days=days_ahead)
        logger.debug(f"Using days_ahead={days_ahead} for filtering")
    else:
        time_delta = pd.Timedelta(weeks=weeks_ahead)
        logger.debug(f"Using weeks_ahead={weeks_ahead} (~{weeks_ahead * 7:.1f} days) for filtering")
    
    # Calculate date range
    today = pd.Timestamp.today().normalize()
    future_cutoff = today + time_delta
    
    # Apply filters
    upcoming = schedule_filtered[
        (schedule_filtered['gameday'] >= today) &
        (schedule_filtered['gameday'] <= future_cutoff)
    ].copy()
    
    logger.debug(f"Filtered to {len(upcoming)} upcoming games from {len(schedule)} total games")
    return upcoming.sort_values('gameday')


def filter_games_by_week(
    schedule: GameDataFrame, 
    week: int, 
    logger=None
) -> GameDataFrame:
    """
    Filter schedule DataFrame to specific week.
    
    Extracts the filtering logic from get_games_by_week().
    
    Args:
        schedule: Schedule DataFrame with 'week' column
        week: NFL week number to filter to
        logger: Logger instance (optional, for dependency injection)
        
    Returns:
        Filtered DataFrame with games for the specified week
    """
    logger = logger or _logger
    
    if schedule.empty:
        return schedule
    
    if 'week' not in schedule.columns:
        logger.warning("No 'week' column found in schedule data")
        return schedule
    
    week_games = schedule[schedule['week'] == week].copy()
    logger.debug(f"Filtered to {len(week_games)} games for week {week} from {len(schedule)} total games")
    return week_games


def process_game_times(schedule: GameDataFrame, logger=None) -> GameDataFrame:
    """
    Process game time data to create proper datetime fields.
    
    Combines gameday and gametime columns to create timezone-aware game_time field.
    
    Args:
        schedule: Raw schedule DataFrame
        logger: Logger instance (optional, for dependency injection)
        
    Returns:
        DataFrame with processed time fields including game_time column
    """
    logger = logger or _logger
    
    if schedule.empty:
        return schedule
    
    try:
        processed = schedule.copy()
        
        # Check what time-related columns exist
        time_columns = [col for col in processed.columns if 'time' in col.lower() or 'day' in col.lower()]
        logger.debug(f"Found time-related columns: {time_columns}")
        
        # Process gameday if it exists
        if 'gameday' in processed.columns:
            processed['gameday'] = pd.to_datetime(processed['gameday']).dt.normalize()
        
        # Try to create game_time from gameday + gametime
        if 'gameday' in processed.columns and 'gametime' in processed.columns:
            logger.debug("Creating game_time from gameday + gametime")
            
            def combine_datetime(row):
                try:
                    if pd.isna(row['gameday']) or pd.isna(row['gametime']):
                        return None
                    
                    game_date = pd.to_datetime(row['gameday']).date()
                    time_str = str(row['gametime']).strip()
                    
                    # Parse time string (e.g., "1:00PM", "8:20 PM", etc.)
                    if time_str and time_str.lower() != 'nan':
                        # Clean up the time string
                        time_str = time_str.replace(' ', '').upper()
                        
                        # Try to parse the time
                        try:
                            time_obj = pd.to_datetime(time_str, format='%I:%M%p').time()
                        except:
                            try:
                                time_obj = pd.to_datetime(time_str, format='%H:%M').time()
                            except:
                                logger.warning(f"Could not parse time: {time_str}")
                                return None
                        
                        # Combine date and time - nflfastR times are in ET
                        from datetime import datetime
                        import pytz
                        naive_dt = datetime.combine(game_date, time_obj)
                        # Localize to Eastern Time first (nflfastR uses ET)
                        et_tz = pytz.timezone('America/New_York')
                        et_dt = et_tz.localize(naive_dt)
                        # Convert to UTC for storage
                        return et_dt.astimezone(pytz.utc)
                    
                    return None
                except Exception as e:
                    logger.warning(f"Error combining datetime for row: {e}")
                    return None
            
            game_times = []
            for _, row in processed.iterrows():
                game_times.append(combine_datetime(row))
            processed['game_time'] = game_times
            
            # Log success rate
            valid_times = processed['game_time'].notna().sum()
            total_games = len(processed)
            logger.info(f"Successfully created game_time for {valid_times}/{total_games} games")
        
        elif 'gameday' in processed.columns:
            # If no gametime, just use gameday as game_time
            logger.debug("Using gameday as game_time (no gametime column)")
            processed['game_time'] = processed['gameday']
        
        return processed
        
    except Exception as e:
        logger.error(f"Error processing game times: {e}")
        return schedule


def validate_season_range(seasons: List[int], logger=None) -> List[int]:
    """
    Validate and clean a list of season years.
    
    Extracts validation logic that could be reused across season operations.
    
    Args:
        seasons: List of season years to validate
        logger: Logger instance (optional, for dependency injection)
        
    Returns:
        List of valid, sorted, deduplicated season years
        
    Raises:
        ValueError: If no valid seasons found
    """
    logger = logger or _logger
    
    if not seasons:
        return []
    
    valid_seasons = []
    invalid_seasons = []
    
    for season in seasons:
        if isinstance(season, int) and 1920 <= season <= 2050:
            valid_seasons.append(season)
        else:
            invalid_seasons.append(season)
    
    if invalid_seasons:
        logger.warning(f"Invalid seasons filtered out: {invalid_seasons}")
    
    if not valid_seasons and seasons:
        raise ValueError(f"No valid seasons found in: {seasons}")
    
    # Return sorted and deduplicated
    result = sorted(set(valid_seasons))
    logger.debug(f"Validated {len(result)} seasons: {result}")
    return result
