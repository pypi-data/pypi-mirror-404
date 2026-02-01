"""
NOAA Weather API Integration Module for QuantCup Edge Detection System

This module provides integration with NOAA Weather API to replace mock weather
data with live meteorological conditions for accurate weather-based edge calculations.

Components:
- noaa_client.py: Main API client for NOAA Weather API
- models.py: Data models for weather data
- stadium_registry.py: NFL stadium coordinates and roof type mappings
- weather_processor.py: Weather processing, NLP parsing, and impact assessment
- nlp_parser.py: Natural language processing for forecast text analysis
"""

from .noaa_client import NOAAWeatherClient
from ..utils.stadium_registry import StadiumRegistry, NFL_STADIUMS
from .weather_processor import WeatherProcessor
from .nlp_parser import WeatherNLPParser
from .models import GameWeather

def get_game_weather(home_team, away_team, game_time=None):
    """
    Convenience function to get processed weather for a specific game
    
    This is the recommended way to get weather data for most use cases.
    For advanced usage or batch processing, use WeatherProcessor directly.
    
    Args:
        home_team (str): Home team code (e.g., 'KC', 'NO', 'GB')
        away_team (str): Away team code  
        game_time (datetime, optional): Game start time for forecast period matching
        
    Returns:
        GameWeather: Processed weather data with impact assessment, or None if unavailable
        
    Example:
        >>> from quantcup.data_sources.weather import get_game_weather
        >>> weather = get_game_weather('KC', 'BUF')
        >>> print(f"Impact: {weather.impact_level}, Score: {weather.impact_score}")
    """
    processor = WeatherProcessor()
    return processor.process_game_weather(home_team, away_team, game_time=game_time)

__all__ = [
    'NOAAWeatherClient',
    'StadiumRegistry',
    'NFL_STADIUMS',
    'WeatherProcessor',
    'WeatherNLPParser',
    'GameWeather',
    'get_game_weather'
]
