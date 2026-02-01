"""
Schedule Integration with CommonV2 Provider

Pattern: Simple service class with DI support
Complexity: 2 points (data loading + validation)
Layer: 2 (Feature - domain-specific schedule operations)

Provides integration with CommonV2 schedule provider to load real
NFL schedule data for the ML pipeline and analytics.

================================================================================
USAGE GUIDE: schedules vs dim_date (as of 11/1/25)
================================================================================

CURRENT STATUS:
- schedules: Available via CommonV2 but NOT directly queried by ML pipeline
- ML Pipeline: Uses dim_game for game-specific data instead
- See docs/dim_date_vs_schedules_analysis.md for detailed comparison

DATA MODEL:
- ~7,263 rows: Only dates when actual NFL games occur
- No offseason dates (only game days included)
- Sparse time series (gaps between games)

FEATURES PROVIDED:
1. Game Context:
   - game_id, home_team, away_team, week, season
   
2. Venue Information:
   - stadium: Stadium name
   - roof: outdoors / dome / retractable
   - surface: grass / turf / fieldturf

3. Weather Conditions:
   - temperature: Game-time temperature
   - humidity: Humidity percentage
   - wind_speed: Wind speed in mph
   - conditions: Clear / Rain / Snow / etc.

4. Timing:
   - gameday: Game date (YYYY-MM-DD)
   - gametime: Game time (HH:MM)

WHEN TO USE schedules:
✅ Game-specific analysis (team matchups, actual game dates)
✅ Venue/weather context (stadium, roof type, surface)
✅ Rich game metadata (weather conditions, timing)
✅ Home/away splits analysis

WHEN NOT TO USE schedules:
❌ Continuous time series (use dim_date - has all dates including offseason)
❌ Calendar-based features (use dim_date - has day-of-week, holidays)
❌ Offseason analysis (use dim_date - schedules has no offseason dates)
❌ ML feature engineering (use dim_game - currently active approach)

COMPARISON WITH dim_date:
- schedules: ~7,263 game dates with venue/weather metadata
- dim_date: 10,227 continuous dates with calendar features
- They serve DIFFERENT purposes and are NOT interchangeable
- schedules CANNOT replace dim_date (missing 2,964 offseason dates + no calendar features)

See docs/dim_date_vs_schedules_analysis.md for complete comparison and examples.
================================================================================
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

from commonv2 import get_logger
from commonv2.domain.schedules import get_schedule_for_seasons, get_games_by_week, get_upcoming_games
from nflfastRv3.shared.models import GameSchedule, ValidationResult


class ScheduleDataProvider:
    """
    Schedule data provider using CommonV2 integration.
    
    Pattern: Simple service class
    Complexity: 2 points (data loading + validation)
    Depth: 1 layer (delegates to CommonV2)
    
    Features:
    - Load NFL schedule data from CommonV2
    - Convert to standardized GameSchedule format
    - Validate schedule data quality
    - Filter schedules by week, season, team
    """
    
    def __init__(self):
        """
        Initialize schedule data provider.
        """
        self.logger = get_logger('nflfastRv3.schedule_integration')
        
    def load_schedule(self, seasons: List[int]) -> List[GameSchedule]:
        """
        Load complete NFL schedule for specified seasons.
        
        Args:
            seasons: List of seasons to load
            
        Returns:
            List[GameSchedule]: Complete schedule data
        """
        self.logger.info(f"Loading schedule data for seasons: {seasons}")
        
        try:
            # Load schedule data from CommonV2 for all seasons at once
            schedule_data = get_schedule_for_seasons(seasons, logger=self.logger)
            
            # Convert to GameSchedule objects
            all_games = self._convert_to_game_schedule(schedule_data)
            
            self.logger.info(f"Loaded {len(all_games)} games for seasons: {seasons}")
            
        except Exception as e:
            self.logger.error(f"Failed to load schedule for seasons {seasons}: {e}")
            all_games = []
        
        # Validate loaded schedule
        validation = self.validate_schedule(all_games)
        if not validation.is_valid:
            self.logger.warning(f"Schedule validation issues: {validation.errors}")
        
        self.logger.info(f"Total games loaded: {len(all_games)}")
        return all_games
    
    def get_games_for_week(self, season: int, week: int) -> List[GameSchedule]:
        """
        Get games for a specific week and season.
        
        Args:
            season: NFL season
            week: Week number (1-22)
            
        Returns:
            List[GameSchedule]: Games for specified week
        """
        self.logger.info(f"Loading games for season {season}, week {week}")
        
        try:
            # Load week data from CommonV2
            week_data = get_games_by_week(week, season, logger=self.logger)
            
            # Convert to GameSchedule objects
            games = self._convert_to_game_schedule(week_data)
            
            self.logger.info(f"Loaded {len(games)} games for week {week}")
            return games
            
        except Exception as e:
            self.logger.error(f"Failed to load week {week} schedule: {e}")
            return []
    
    def get_upcoming_games(self, days_ahead: int = 7) -> List[GameSchedule]:
        """
        Get games scheduled in the next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List[GameSchedule]: Upcoming games
        """
        self.logger.info(f"Loading upcoming games for next {days_ahead} days")
        
        try:
            # Use CommonV2 to get upcoming games (convert days to weeks approximation)
            weeks_ahead = max(1, days_ahead // 7)
            upcoming_data = get_upcoming_games(weeks_ahead, logger=self.logger)
            
            # Convert to GameSchedule objects
            all_upcoming = self._convert_to_game_schedule(upcoming_data)
            
            # Further filter by exact day range if needed
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=days_ahead)
            
            upcoming = []
            for game in all_upcoming:
                game_date = game.game_date.date()
                if start_date <= game_date <= end_date:
                    upcoming.append(game)
            
            self.logger.info(f"Found {len(upcoming)} upcoming games")
            return upcoming
            
        except Exception as e:
            self.logger.error(f"Failed to load upcoming games: {e}")
            return []
    
    def _convert_to_game_schedule(self, schedule_data: pd.DataFrame) -> List[GameSchedule]:
        """
        Convert CommonV2 schedule data to GameSchedule objects.
        
        Args:
            schedule_data: Raw schedule DataFrame from CommonV2
            
        Returns:
            List[GameSchedule]: Converted game schedules
        """
        games = []
        
        if schedule_data.empty:
            return games
        
        for _, row in schedule_data.iterrows():
            try:
                # Parse game date - CommonV2 should provide standardized format
                game_date = self._parse_game_date(row.get('gameday'), row.get('gametime'))
                
                # Get season from the row data
                season = int(row.get('season', self._get_current_season()))
                
                # Create GameSchedule object
                game = GameSchedule(
                    game_id=str(row.get('game_id', '')),
                    home_team=str(row.get('home_team', '')),
                    away_team=str(row.get('away_team', '')),
                    game_date=game_date,
                    week=int(row.get('week', 0)),
                    season=season,
                    season_type=str(row.get('season_type', 'REG')),  # Preserve season_type from source data
                    stadium=row.get('stadium'),
                    weather=self._extract_weather_info(row)
                )
                
                games.append(game)
                
            except Exception as e:
                self.logger.warning(f"Failed to convert game row: {e}")
                continue
        
        return games
    
    def _parse_game_date(self, gameday: Any, gametime: Any) -> datetime:
        """
        Parse game date and time from CommonV2 format.
        
        Args:
            gameday: Game date (various formats)
            gametime: Game time (various formats)
            
        Returns:
            datetime: Parsed game datetime
        """
        try:
            # Handle different date formats from CommonV2
            if isinstance(gameday, str):
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y%m%d']:
                    try:
                        date_part = datetime.strptime(gameday, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    # Fallback to current date if parsing fails
                    date_part = datetime.now().date()
            else:
                # Handle pandas datetime or other formats
                date_part = pd.to_datetime(gameday).date()
            
            # Combine with time (default to noon if no time provided)
            if gametime and isinstance(gametime, str):
                try:
                    time_part = datetime.strptime(gametime, '%H:%M').time()
                except ValueError:
                    time_part = datetime.strptime('12:00', '%H:%M').time()
            else:
                time_part = datetime.strptime('12:00', '%H:%M').time()
            
            return datetime.combine(date_part, time_part)
            
        except Exception as e:
            self.logger.warning(f"Date parsing failed: {e}, using current datetime")
            return datetime.now()
    
    def _extract_weather_info(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Extract weather information from schedule row if available.
        
        Args:
            row: Schedule data row
            
        Returns:
            Optional[Dict[str, Any]]: Weather information
        """
        weather_fields = ['temperature', 'humidity', 'wind_speed', 'conditions']
        weather = {}
        
        for field in weather_fields:
            if field in row and pd.notna(row[field]):
                weather[field] = row[field]
        
        return weather if weather else None
    
    def _get_current_season(self) -> int:
        """
        Get current NFL season based on date.
        
        Returns:
            int: Current season year
        """
        now = datetime.now()
        # NFL season runs from September to February
        if now.month >= 9:
            return now.year
        else:
            return now.year - 1
    
    def validate_schedule(self, games: List[GameSchedule]) -> ValidationResult:
        """
        Validate schedule data quality and consistency.
        
        Args:
            games: List of games to validate
            
        Returns:
            ValidationResult: Validation results
        """
        validation = ValidationResult(True)
        validation.record_count = len(games)
        
        if not games:
            validation.add_error("No games provided for validation")
            return validation
        
        # Check for duplicate game IDs
        game_ids = [game.game_id for game in games]
        if len(game_ids) != len(set(game_ids)):
            validation.add_error("Duplicate game IDs found")
        
        # Check for missing required fields
        for i, game in enumerate(games):
            if not game.game_id:
                validation.add_error(f"Game {i}: Missing game_id")
            if not game.home_team or not game.away_team:
                validation.add_error(f"Game {game.game_id}: Missing team information")
            if game.week < 1 or game.week > 22:
                validation.add_error(f"Game {game.game_id}: Invalid week {game.week}")
        
        # Check for reasonable date ranges
        current_year = datetime.now().year
        for game in games:
            if game.season < 1999 or game.season > current_year + 1:
                validation.add_warning(f"Game {game.game_id}: Unusual season {game.season}")
        
        # Check team name consistency
        all_teams = set()
        for game in games:
            all_teams.add(game.home_team)
            all_teams.add(game.away_team)
        
        if len(all_teams) > 35:  # NFL has 32 teams plus some variation in naming
            validation.add_warning(f"Found {len(all_teams)} unique team names (expected ~32)")
        
        return validation


# Convenience functions for module-level access
def load_real_schedule_data(seasons: List[int]) -> List[GameSchedule]:
    """
    Load real NFL schedule data for specified seasons.
    
    Args:
        seasons: List of seasons to load
        
    Returns:
        List[GameSchedule]: Complete schedule data
    """
    provider = ScheduleDataProvider()
    return provider.load_schedule(seasons)


def get_games_for_current_week() -> List[GameSchedule]:
    """
    Get games for the current NFL week.
    
    Returns:
        List[GameSchedule]: Current week's games
    """
    provider = ScheduleDataProvider()
    now = datetime.now()
    
    # Determine current season and week (simplified logic)
    current_season = now.year if now.month >= 9 else now.year - 1
    
    # Get week number (this is simplified - real implementation would need better logic)
    if now.month >= 9:
        week = min((now - datetime(now.year, 9, 1)).days // 7 + 1, 18)
    else:
        week = min((now - datetime(now.year - 1, 9, 1)).days // 7 + 1, 22)
    
    return provider.get_games_for_week(current_season, max(1, week))
