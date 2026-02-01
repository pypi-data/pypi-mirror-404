"""
Props data transformation functions.
Handles fetching and processing event-specific odds/props data.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import json
from commonv2 import get_logger

from ..extract.api import fetch_event_odds_data

logger = get_logger(__name__)

def get_props_data(
    sport_key: str,
    event_id: Optional[str] = None,
    markets: Optional[List[str]] = None
) -> pd.DataFrame:
    """Fetch and transform event-specific odds/props data
    
    Args:
        sport_key: Sport key to fetch props for (should be passed from CLI)
        event_id: Specific event ID to fetch props for
        markets: Optional list of market types to filter
        
    Returns:
        DataFrame with props data matching the props table schema
    """
    
    if event_id is None:
        logger.warning("No event_id provided for props data")
        return pd.DataFrame()
    
    logger.info(f"Fetching props data for event {event_id}...")
    data = fetch_event_odds_data(sport_key, event_id, markets)
    
    # Transform to match props table schema
    records: List[Dict[str, Any]] = []
    
    # Handle both single event and list of events
    events = data if isinstance(data, list) else [data]
    
    for event in events:
        if not isinstance(event, dict) or 'bookmakers' not in event:
            continue
        
        event_dict: Dict[str, Any] = event
        for bookmaker in event_dict.get('bookmakers', []):
            if not isinstance(bookmaker, dict):
                continue
            bookmaker_dict: Dict[str, Any] = bookmaker
            
            for market in bookmaker_dict.get('markets', []):
                if not isinstance(market, dict):
                    continue
                market_dict: Dict[str, Any] = market
                
                record = {
                    'event_id': event_dict.get('id'),
                    'sport_key': event_dict.get('sport_key'),
                    'bookmaker_key': bookmaker_dict.get('key'),
                    'market_key': market_dict.get('key'),
                    'market_data': json.dumps(market_dict),  # Store full market as JSON
                    'last_update': market_dict.get('last_update')  # Get last_update from market, not bookmaker
                }
                records.append(record)
    
    df = pd.DataFrame(records)
    
    # Convert last_update to datetime if present and not all null
    if 'last_update' in df.columns and not df['last_update'].isna().all():
        df['last_update'] = pd.to_datetime(df['last_update'], utc=True).dt.tz_convert('America/New_York')
    
    logger.info(f"Processed {len(df)} prop markets for event {event_id}")
    return df
