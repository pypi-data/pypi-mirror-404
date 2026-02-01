"""
Odds Scraper Data Source Module

Provides scraping and data collection functionality for sportsbook odds.

Architecture (3-Layer Clean Architecture):
    Layer 1 (CLI): cli.py - Command-line interface using Typer
    Layer 2 (Pipeline): pipeline.py - ETL orchestration
    Layer 3 (Infrastructure): core/* - Browser engine, data processor, config

Recommended Usage:
    CLI: `quantcup odds-scraper scrape-nfl`
    Python API: `from odds_scraper.pipeline import OddsScraperPipeline`

⚠️ DEPRECATED:
    scraper.OddsScraper - Use OddsScraperPipeline instead
    See odds_scraper/README.md for migration guide

Original source: sports-books/Dev_DKScraper_PRD.py
"""

# New clean architecture implementation (recommended)
from .pipeline import SportsbookPipeline

# Legacy implementation (deprecated - kept for backward compatibility)
from .scraper import SportsbookScraper

# Aliases for backward compatibility
OddsScraperPipeline = SportsbookPipeline
OddsScraper = SportsbookScraper

__all__ = [
    'SportsbookPipeline',  # ✅ Recommended
    'OddsScraperPipeline',  # ✅ Alias for backward compatibility
    'SportsbookScraper',   # ⚠️ Deprecated
    'OddsScraper',         # ⚠️ Deprecated alias
]
