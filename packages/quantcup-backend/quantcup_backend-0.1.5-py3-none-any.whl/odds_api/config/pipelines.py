"""
Pipeline registry configuration.

This module defines the registry of available data pipelines for the Odds API ETL system.
Each pipeline specifies how to fetch, transform, and load a specific type of data.

Usage:
    from odds_api.config.pipelines import PIPELINES
    
    # Get a specific pipeline config
    leagues_config = PIPELINES['leagues']
    
    # Execute a pipeline's fetch function
    df = leagues_config['fetch_fn']()
    
    # Access pipeline metadata
    print(f"Updates every {leagues_config['update_interval']} seconds")
    print(f"Uses quota: {leagues_config['uses_quota']}")

Adding a New Pipeline:
    1. Create your fetch function in odds_api/etl/transform/
    2. Ensure it accepts **kwargs and returns a pd.DataFrame
    3. Add an entry to PIPELINES dict below
    4. Run validate_pipelines() to ensure correctness

Notes:
    - All fetch functions must accept **kwargs for a consistent interface
    - Common kwargs: sport_key, event_id, markets, days_from
    - update_interval is in seconds (use interval constants)
    - uses_quota=True means the pipeline consumes API rate limits
"""

from typing import Dict
from datetime import timedelta
from functools import partial

from odds_api.core.types import PipelineConfig
from odds_api.etl.transform.leagues import get_leagues_data
from odds_api.etl.transform.teams import get_teams_data
from odds_api.etl.transform.schedule import get_schedule_data
from odds_api.etl.transform.results import get_results_data
from odds_api.etl.transform.props import get_props_data
from odds_api.etl.transform.odds import get_odds


# Update interval constants (in seconds)
INTERVAL_DAILY = int(timedelta(days=1).total_seconds())      # 86400
INTERVAL_HOURLY = int(timedelta(hours=1).total_seconds())    # 3600
INTERVAL_MINUTE = int(timedelta(minutes=1).total_seconds())  # 60
INTERVAL_MANUAL = 0  # Only runs when explicitly triggered


# Pipeline registry - maps endpoint keys to their configuration
PIPELINES: Dict[str, PipelineConfig] = {
    'leagues': {
        'fetch_fn': get_leagues_data,
        'required_cols': ['sport_key', 'title', 'active'],
        'table': 'dim_leagues',
        'uses_quota': False,
        'update_interval': INTERVAL_DAILY,
        'description': 'Sports/leagues dimension data'
    },
    'teams': {
        'fetch_fn': get_teams_data,
        'required_cols': ['participant_id', 'sport_key', 'full_name'],
        'table': 'dim_teams',  # Pluralized for consistency
        'uses_quota': False,
        'update_interval': INTERVAL_DAILY,
        'description': 'Teams/participants dimension data'
    },
    'schedule': {
        'fetch_fn': get_schedule_data,
        'required_cols': ['event_id', 'sport_key', 'commence_time', 'home_team', 'away_team'],
        'table': 'dim_oddapi_game',
        'uses_quota': False,
        'update_interval': INTERVAL_HOURLY,
        'description': 'Schedule/events dimension data'
    },
    'results': {
        'fetch_fn': partial(get_results_data, days_from=7),  # Default lookback of 7 days
        'required_cols': ['event_id', 'sport_key', 'commence_time', 'home_team', 'away_team'],
        'table': 'dim_results',
        'uses_quota': True,
        'update_interval': INTERVAL_HOURLY,
        'description': 'Game results/scores dimension data'
    },
    'props': {
        'fetch_fn': get_props_data,
        'required_cols': ['event_id', 'sport_key', 'bookmaker_key', 'market_key'],
        'table': 'fact_props',
        'uses_quota': True,
        'update_interval': INTERVAL_MINUTE,
        'description': 'Player props and event-specific odds fact data'
    },
    'odds': {
        'fetch_fn': get_odds,
        'required_cols': ['event_id', 'sport_key', 'bookmaker_key', 'market_key'],  # Changed game_id to event_id
        'table': 'fact_odds_raw',
        'uses_quota': True,
        'update_interval': INTERVAL_MINUTE,
        'description': 'Betting odds fact data'
    },
    'backfill': {
        'fetch_fn': None,  # Handled by BackfillPipeline class
        'required_cols': [],
        'table': 'backfill_summary',
        'uses_quota': True,
        'update_interval': INTERVAL_MANUAL,
        'description': 'Historical odds backfill (special pipeline)'
    }
}


def validate_pipelines() -> None:
    """
    Validate all pipeline configurations at module import or startup.
    
    Checks:
        - Required fields are present
        - fetch_fn is callable or explicitly None (backfill special case)
        - update_interval is non-negative
        - table name is non-empty
        - required_cols is a list
    
    Raises:
        AssertionError: If any validation check fails
        
    Example:
        >>> validate_pipelines()  # Runs successfully if all configs are valid
    """
    for name, config in PIPELINES.items():
        # Check required fields
        assert 'fetch_fn' in config, f"Pipeline '{name}' missing 'fetch_fn'"
        assert 'table' in config, f"Pipeline '{name}' missing 'table'"
        assert 'uses_quota' in config, f"Pipeline '{name}' missing 'uses_quota'"
        assert 'update_interval' in config, f"Pipeline '{name}' missing 'update_interval'"
        assert 'required_cols' in config, f"Pipeline '{name}' missing 'required_cols'"
        
        # Validate field types and values
        fetch_fn = config['fetch_fn']
        assert fetch_fn is None or callable(fetch_fn), \
            f"Pipeline '{name}' fetch_fn must be callable or None"
        
        # Special case: backfill can have None fetch_fn
        if name != 'backfill':
            assert fetch_fn is not None, \
                f"Pipeline '{name}' fetch_fn cannot be None (only 'backfill' allowed)"
        
        assert isinstance(config['table'], str) and config['table'], \
            f"Pipeline '{name}' table must be non-empty string"
        
        assert isinstance(config['uses_quota'], bool), \
            f"Pipeline '{name}' uses_quota must be boolean"
        
        assert isinstance(config['update_interval'], int) and config['update_interval'] >= 0, \
            f"Pipeline '{name}' update_interval must be non-negative integer"
        
        assert isinstance(config['required_cols'], list), \
            f"Pipeline '{name}' required_cols must be a list"


# Validate configurations on module import
validate_pipelines()


__all__ = [
    'PIPELINES',
    'INTERVAL_DAILY',
    'INTERVAL_HOURLY',
    'INTERVAL_MINUTE',
    'INTERVAL_MANUAL',
    'validate_pipelines'
]
