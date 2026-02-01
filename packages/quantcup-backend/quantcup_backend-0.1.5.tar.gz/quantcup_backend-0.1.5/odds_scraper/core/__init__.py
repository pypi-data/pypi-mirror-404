"""Sportsbook core infrastructure components."""
from odds_scraper.core.browser import BrowserEngine
from odds_scraper.core.processor import OddsDataProcessor

__all__ = [
    "BrowserEngine",
    "OddsDataProcessor",
]
