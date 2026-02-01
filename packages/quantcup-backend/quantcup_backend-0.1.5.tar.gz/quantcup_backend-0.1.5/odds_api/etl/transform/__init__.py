"""
Transform package for odds_api.
Re-exports all transformation functions for backward compatibility.
"""

# Import core utilities
from .core import american_to_decimal, enrich_odds_metrics, fix_commence_time, write_to_csv

# Import endpoint-specific functions
from .odds import get_odds, normalize_odds_df
from .leagues import get_leagues_data
from .teams import get_teams_data
from .schedule import get_schedule_data
from .results import get_results_data
from .props import get_props_data

# Maintain backward compatibility - export everything that was in the original transform.py
__all__ = [
    'get_odds',
    'normalize_odds_df', 
    'enrich_odds_metrics',
    'write_to_csv',
    'american_to_decimal',
    'fix_commence_time',
    'get_leagues_data',
    'get_teams_data',
    'get_schedule_data',
    'get_results_data',
    'get_props_data'
]
