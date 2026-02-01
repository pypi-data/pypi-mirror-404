"""
Weather Module for QuantCup

Unified weather data integration combining:
- Forecasts: NOAA National Weather Service forecasts for upcoming games
- Historical: NCEI historical weather data and climatology

Usage:
    # Forecasts for upcoming games
    from weather.forecasts import get_game_weather, WeatherProcessor
    
    # Historical data and climatology
    from weather.historical import NCEIClient, climatology_forecast

CLI Access:
    quantcup weather forecast week 20
    quantcup weather historical --date 2024-09-01
"""

# Re-export key components for convenience
from .forecasts import (
    NOAAWeatherClient,
    StadiumRegistry,
    NFL_STADIUMS,
    WeatherProcessor,
    WeatherNLPParser,
    GameWeather,
    get_game_weather
)

from .historical import (
    NCEIClient,
    climatology_forecast
)

__all__ = [
    # Forecasts
    'NOAAWeatherClient',
    'StadiumRegistry',
    'NFL_STADIUMS',
    'WeatherProcessor',
    'WeatherNLPParser',
    'GameWeather',
    'get_game_weather',
    
    # Historical
    'NCEIClient',
    'climatology_forecast'
]

__version__ = "1.0.0"
