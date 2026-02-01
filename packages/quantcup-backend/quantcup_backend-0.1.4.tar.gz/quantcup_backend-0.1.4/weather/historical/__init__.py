"""
Historical Weather Data Module

NCEI (National Centers for Environmental Information) integration for:
- Historical weather observations
- Climatology normals (30-year averages)
- Station discovery and data retrieval

Components:
- ncei_client.py: Thread-safe, rate-limited client for NCEI Access Data API
- climatologyforecast.py: Climatology baseline forecasting
- test_climatologyforecast.py: Integration tests

Usage:
    from weather.historical import NCEIClient, climatology_forecast
    
    client = NCEIClient()
    forecast = climatology_forecast(
        client=client,
        date="2025-09-07",
        lat=35.2271,
        lon=-80.8431
    )
"""

from .ncei_client import NCEIClient
from .climatologyforecast import climatology_forecast, format_forecast

__all__ = [
    'NCEIClient',
    'climatology_forecast',
    'format_forecast'
]
