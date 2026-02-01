"""
Configuration and schema definitions for odds_api.

This module contains all configuration-related code including
database schemas, API settings, and environment variables.
"""

from .schemas import (
    MARKET_MAP,
    SUPPORTED_SPORTS,
    get_market_columns,
    get_market_ddl,
    get_market_indexes,
    validate_sport_and_markets
)
from .settings import Settings, BackfillSettings, get_settings

__all__ = [
    # Schema definitions
    'MARKET_MAP',
    'SUPPORTED_SPORTS',
    'get_market_columns',
    'get_market_ddl',
    'get_market_indexes',
    'validate_sport_and_markets',
    # Settings
    'Settings',
    'BackfillSettings',
    'get_settings'
]