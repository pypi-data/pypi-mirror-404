"""Sportsbook configuration module."""
from odds_scraper.config.settings import (
    BrowserConfig,
    SportsbookSettings,
    LocationConfig,
    ProxyConfig,
    get_odds_scraper_settings,
)

__all__ = [
    "BrowserConfig",
    "SportsbookSettings",
    "LocationConfig",
    "ProxyConfig",
    "get_odds_scraper_settings",
]
