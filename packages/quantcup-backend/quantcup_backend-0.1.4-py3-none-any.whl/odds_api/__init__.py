"""
Odds API Data Pipeline

A production-ready system for fetching, processing, and storing sports betting odds data.
Built with the "skinny-but-useful" philosophy - minimal dependencies, maximum functionality.
"""

__version__ = "1.0.0"

# Make key functions available at package level
from .etl.transform.odds import get_odds
from .etl.extract.api import fetch_odds_data

__all__ = [
    'get_odds',
    'fetch_odds_data', 
]
