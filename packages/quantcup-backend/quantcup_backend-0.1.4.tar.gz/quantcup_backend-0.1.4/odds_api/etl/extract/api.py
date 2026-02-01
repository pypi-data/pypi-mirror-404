"""
API interaction module for odds data fetching.
Handles HTTP requests, retry logic, and rate limiting.
"""

from typing import List, Optional, Union
from commonv2 import get_logger
from odds_api.core.types import SportKey, EventID, ISOTimestamp, OddsData, MarketList, QuotaCost

from .api_core import _api_get, get_session, close_session, BASE_URL

logger = get_logger(__name__)

__all__ = [
    'fetch_odds_data',
    'fetch_sports_data',
    'fetch_events_data',
    'fetch_scores_data',
    'fetch_participants_data',
    'fetch_event_odds_data',
    'fetch_historical_odds_data',
    'fetch_historical_events_data',
    'fetch_historical_event_odds_data'
]


def fetch_odds_data(sport_key: SportKey = 'americanfootball_nfl', markets: Optional[MarketList] = None, use_paid_key: bool = True) -> Union[OddsData, List[OddsData]]:
    """Fetch odds data with retry logic and rate limit handling (PAID endpoint)"""
    if markets is None:
        markets = ['h2h', 'spreads', 'totals']
    return _api_get(
        f"/v4/sports/{sport_key}/odds",
        use_paid_key=use_paid_key,
        regions="us",
        markets=",".join(markets),
        oddsFormat="american"
    )


def fetch_sports_data() -> Union[OddsData, List[OddsData]]:
    """Fetch sports list - GET /v4/sports (FREE - no quota cost)"""
    return _api_get("/v4/sports", use_paid_key=False)


def fetch_events_data(sport_key: SportKey = 'americanfootball_nfl') -> Union[OddsData, List[OddsData]]:
    """Fetch events list - GET /v4/sports/{sport}/events (FREE - no quota cost)"""
    return _api_get(f"/v4/sports/{sport_key}/events", use_paid_key=False)


def fetch_scores_data(sport_key: SportKey = 'americanfootball_nfl', days_from: Optional[int] = None, use_paid_key: bool = True) -> Union[OddsData, List[OddsData]]:
    """Fetch scores - GET /v4/sports/{sport}/scores (PAID endpoint)"""
    params = {}
    # Only add daysFrom if it's a valid integer 1-3
    if days_from and isinstance(days_from, int) and 1 <= days_from <= 3:
        params['daysFrom'] = str(days_from)
    return _api_get(f"/v4/sports/{sport_key}/scores", use_paid_key=use_paid_key, **params)


def fetch_participants_data(sport_key: SportKey) -> OddsData:
    """
    Fetch participants - GET /v4/sports/{sport}/participants (FREE - no quota cost)
    
    Args:
        sport_key: Sport identifier (e.g., 'americanfootball_nfl', 'basketball_nba')
    """
    return _api_get(f"/v4/sports/{sport_key}/participants", use_paid_key=False)


def fetch_event_odds_data(sport_key: SportKey, event_id: EventID, markets: Optional[MarketList] = None, use_paid_key: bool = True) -> OddsData:
    """Fetch event-specific odds - GET /v4/sports/{sport}/events/{eventId}/odds (PAID endpoint)"""
    params = {
        'use_paid_key': use_paid_key,
        'regions': 'us',
        'oddsFormat': 'american'
    }
    if markets:
        params['markets'] = ','.join(markets) if isinstance(markets, list) else markets
    return _api_get(f"/v4/sports/{sport_key}/events/{event_id}/odds", **params)



# ============================================================================
# HISTORICAL ODDS ENDPOINTS (PAID - uses 10x quota cost)
# ============================================================================

def fetch_historical_odds_data(sport_key: SportKey = 'americanfootball_nfl', date: Optional[ISOTimestamp] = None, markets: Optional[MarketList] = None, regions: str = 'us', use_paid_key: bool = True) -> OddsData:
    """
    Fetch historical odds snapshot at a specific timestamp.
    
    GET /v4/historical/sports/{sport}/odds (PAID - 10x quota cost)
    Cost: 10 x [number of markets] x [number of regions]
    
    Args:
        sport_key: Sport identifier (default: 'americanfootball_nfl')
        date: ISO8601 timestamp for snapshot (e.g., '2021-10-18T12:00:00Z')
        markets: List of market types or comma-separated string (default: ['h2h', 'spreads', 'totals'])
        regions: Regions for bookmakers (default: 'us')
        use_paid_key: Must use paid key (default: True)
    
    Returns:
        Dict with 'timestamp', 'previous_timestamp', 'next_timestamp', and 'data' keys
    """
    if markets is None:
        markets = ['h2h', 'spreads', 'totals']
    
    if not date:
        raise ValueError("date parameter is required for historical odds (ISO8601 format, e.g., '2021-10-18T12:00:00Z')")
    
    # Calculate actual quota cost: 10 × markets × regions
    num_markets = len(markets) if isinstance(markets, list) else len(markets.split(','))
    num_regions = len(regions.split(','))
    actual_quota_cost = 10 * num_markets * num_regions
    
    logger.debug(f"Historical odds quota cost: {actual_quota_cost} (10 × {num_markets} markets × {num_regions} regions)")
    
    params = {
        'use_paid_key': use_paid_key,
        'quota_cost': actual_quota_cost,
        'regions': regions,
        'markets': ','.join(markets) if isinstance(markets, list) else markets,
        'oddsFormat': 'american',
        'date': date
    }
    
    return _api_get(f"/v4/historical/sports/{sport_key}/odds", **params)


def fetch_historical_events_data(sport_key: SportKey = 'americanfootball_nfl', date: Optional[ISOTimestamp] = None, use_paid_key: bool = True) -> OddsData:
    """
    Fetch historical events list at a specific timestamp.
    
    GET /v4/historical/sports/{sport}/events (PAID - uses 1 quota)
    Returns event ids, teams, and commence times without odds.
    
    Args:
        sport_key: Sport identifier (default: 'americanfootball_nfl')
        date: ISO8601 timestamp for snapshot (e.g., '2021-10-18T12:00:00Z')
        use_paid_key: Must use paid key (default: True)
    
    Returns:
        Dict with 'timestamp', 'previous_timestamp', 'next_timestamp', and 'data' keys
    """
    if not date:
        raise ValueError("date parameter is required for historical events (ISO8601 format, e.g., '2021-10-18T12:00:00Z')")
    
    params = {
        'use_paid_key': use_paid_key,
        'quota_cost': 1,
        'date': date
    }
    
    return _api_get(f"/v4/historical/sports/{sport_key}/events", **params)


def fetch_historical_event_odds_data(sport_key: SportKey, event_id: EventID, date: Optional[ISOTimestamp] = None, markets: Optional[List[str]] = None, regions: str = 'us', use_paid_key: bool = True) -> OddsData:
    """
    Fetch historical odds for a single event at a specific timestamp.
    
    GET /v4/historical/sports/{sport}/events/{eventId}/odds (PAID - 10x quota cost)
    Cost: 10 x [number of unique markets returned] x [number of regions]
    
    Args:
        sport_key: Sport identifier (e.g., 'americanfootball_nfl')
        event_id: Event ID from historical events endpoint
        date: ISO8601 timestamp for snapshot (e.g., '2023-11-29T22:45:00Z')
        markets: List of market types or comma-separated string (default: ['h2h', 'spreads', 'totals'])
        regions: Regions for bookmakers (default: 'us')
        use_paid_key: Must use paid key (default: True)
    
    Returns:
        Dict with 'timestamp', 'previous_timestamp', 'next_timestamp', and 'data' keys
    """
    if markets is None:
        markets = ['h2h', 'spreads', 'totals']
    
    if not date:
        raise ValueError("date parameter is required for historical event odds (ISO8601 format, e.g., '2023-11-29T22:45:00Z')")
    
    # Calculate actual quota cost: 10 × markets × regions
    num_markets = len(markets) if isinstance(markets, list) else len(markets.split(','))
    num_regions = len(regions.split(','))
    actual_quota_cost = 10 * num_markets * num_regions
    
    logger.debug(f"Historical event odds quota cost: {actual_quota_cost} (10 × {num_markets} markets × {num_regions} regions)")
    
    params = {
        'use_paid_key': use_paid_key,
        'quota_cost': actual_quota_cost,
        'regions': regions,
        'markets': ','.join(markets) if isinstance(markets, list) else markets,
        'oddsFormat': 'american',
        'date': date
    }
    
    return _api_get(f"/v4/historical/sports/{sport_key}/events/{event_id}/odds", **params)
