"""
Game Weather Module

Handles schedule integration for weather analysis across multiple games.
"""

from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

from commonv2 import get_games_by_week, get_schedule_for_seasons
from commonv2.domain.schedules import SeasonParser
from .weather_processor import WeatherProcessor


class GameWeatherService:
    """
    Service for getting weather data for scheduled games
    """
    
    def __init__(self, db_connection=None, logger=None):
        self.db = db_connection
        self.logger = logger
        self.weather_processor = WeatherProcessor(db_connection, logger)
    
    
    def get_weather_for_week(self, week: int, season: Optional[int] = None, include_domes: bool = False) -> tuple[List[Dict], Dict]:
        """
        Get weather for all games in a specific week
        
        Args:
            week: Week number
            season: Season year (defaults to current year)
            include_domes: Whether to include dome games
            
        Returns:
            Tuple of (rows, meta) where:
            - rows: list of dict rows for display (including placeholders)
            - meta: {"scheduled_count", "returned_count", "unavailable_count"}
        """
        try:
            if season is None:
                season = datetime.now().year
            
            # Get games for the week
            games_df = get_games_by_week(week, season)
            
            if games_df.empty:
                if self.logger:
                    self.logger.info(f"No games found for week {week}, season {season}")
                return [], {"scheduled_count": 0, "returned_count": 0, "unavailable_count": 0}
            
            # Deduplicate games by game_id to prevent duplicate table rows
            if 'game_id' in games_df.columns:
                original_count = len(games_df)
                games_df = games_df.drop_duplicates(['game_id'])
                if self.logger and len(games_df) < original_count:
                    self.logger.info(f"Removed {original_count - len(games_df)} duplicate games")
            
            # Process weather for each game
            results = []
            scheduled_count = len(games_df)
            unavailable_count = 0
            
            for _, game in games_df.iterrows():
                weather_result = self._process_game_weather_from_schedule(game, include_domes)
                if weather_result is None:
                    # Shouldn't happen now, but keep defensive guard
                    unavailable_count += 1
                    continue
                if weather_result.get('game_weather') is None:
                    unavailable_count += 1
                results.append(weather_result)
            
            if self.logger:
                self.logger.info(f"Processed weather for {len(results)} games in week {week} (scheduled={scheduled_count}, unavailable={unavailable_count})")
            
            meta = {
                "scheduled_count": scheduled_count,
                "returned_count": len(results),
                "unavailable_count": unavailable_count,
            }
            return results, meta
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting weather for week {week}: {e}")
            return [], {"scheduled_count": 0, "returned_count": 0, "unavailable_count": 0}
    
    def get_weather_for_day(self, date: datetime, include_domes: bool = False) -> List[Dict]:
        """
        Get weather for all games on a specific day
        
        Args:
            date: Date to get games for
            include_domes: Whether to include dome games
            
        Returns:
            List of game weather data
        """
        try:
            # Get games for the day - filter from current season schedule
            current_season = SeasonParser.get_current_season()
            all_games = get_schedule_for_seasons([current_season])
            
            if not all_games.empty and 'gameday' in all_games.columns:
                all_games['gameday'] = pd.to_datetime(all_games['gameday']).dt.normalize()
                target_date = pd.to_datetime(date).normalize()
                games_df = all_games[all_games['gameday'] == target_date].copy()
            else:
                games_df = pd.DataFrame()
            
            if games_df.empty:
                if self.logger:
                    self.logger.info(f"No games found for {date.strftime('%Y-%m-%d')}")
                return []
            
            # Process weather for each game
            results = []
            for _, game in games_df.iterrows():
                weather_result = self._process_game_weather_from_schedule(game, include_domes)
                if weather_result:
                    results.append(weather_result)
            
            if self.logger:
                self.logger.info(f"Processed weather for {len(results)} games on {date.strftime('%Y-%m-%d')}")
            
            return results
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting weather for date {date}: {e}")
            return []
    
    def _process_game_weather_from_schedule(self, game_row: pd.Series, include_domes: bool) -> Optional[Dict]:
        """
        Process weather for a single game from schedule data
        
        Args:
            game_row: Pandas Series with game data
            include_domes: Whether to include dome games
            
        Returns:
            Dict with game and weather data or None
        """
        try:
            home_team = game_row.get('home_team')
            away_team = game_row.get('away_team')
            game_id = game_row.get('game_id', 'unknown')
            
            # Enhanced validation and logging
            if not home_team or not away_team:
                if self.logger:
                    self.logger.warning(f"Missing team data for game {game_id}: home={home_team}, away={away_team}")
                return None
            
            # Log game being processed
            if self.logger:
                self.logger.info(f"Processing weather for {away_team} @ {home_team} (Game: {game_id})")
            
            # Get stadium registry for validation and dome checking
            from ..utils.stadium_registry import StadiumRegistry
            registry = StadiumRegistry(self.db)
            
            # Validate stadium registry entry
            if not registry.validate_team(home_team):
                if self.logger:
                    self.logger.error(f"Home team {home_team} not found in stadium registry")
                return None
            
            # Skip dome games if not included
            if not include_domes:
                stadium_info = registry.get_stadium_info(home_team)
                if stadium_info and stadium_info.get('roof_type') == 'fixed_dome':
                    if self.logger:
                        self.logger.info(f"Skipping dome game: {away_team} @ {home_team} (fixed dome)")
                    return None
            
            # Get weather for the game
            game_weather = self.weather_processor.process_game_weather(
                home_team=home_team,
                away_team=away_team,
                game_id=game_id,
                game_time=game_row.get('game_time'),
                season=game_row.get('season'),
                week=game_row.get('week')
            )
            
            # Get stadium info for enhanced data
            stadium_info = registry.get_stadium_info(home_team)
            
            if not game_weather:
                # Return a placeholder so the display layer renders:
                # "Forecast not available (game too far in future)"
                return {
                    'game_id': game_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'game_time': game_row.get('game_time'),
                    'gameday': game_row.get('gameday'),
                    'gametime': game_row.get('gametime'),
                    'season': game_row.get('season'),
                    'week': game_row.get('week'),
                    'stadium_info': stadium_info,
                    # Explicit (optional) reason flag for friendlier UI copy
                    'forecast_status': 'unavailable-too-far',
                    'game_weather': None,
                }
            
            # Combine game info with weather data
            result = {
                'game_id': game_id,
                'home_team': home_team,
                'away_team': away_team,
                'game_time': game_row.get('game_time'),
                'gameday': game_row.get('gameday'),
                'gametime': game_row.get('gametime'),
                'season': game_row.get('season'),
                'week': game_row.get('week'),
                'stadium_info': stadium_info,
                'weather': self.weather_processor.get_weather_summary(game_weather),
                'game_weather': game_weather
            }
            
            if self.logger:
                self.logger.info(f"Successfully processed weather for {away_team} @ {home_team}")
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing weather for game {game_row.get('game_id', 'unknown')}: {e}")
            return None
