"""
Schedule data transformation functions.
Handles fetching and processing events/schedule data.
"""

from typing import List, Dict, Any, cast
import pandas as pd
from commonv2 import get_logger

from .core import fix_commence_time
from ..extract.api import fetch_events_data
from odds_api.core.types import SportKey

logger = get_logger(__name__)

def get_schedule_data(sport_key: SportKey) -> pd.DataFrame:
    """Fetch and transform events/schedule data"""
    
    logger.info(f"Fetching schedule data for {sport_key}...")
    data = fetch_events_data(sport_key)
    
    # Cast to List for type checking (API returns list for events endpoint)
    events: List[Dict[str, Any]] = cast(List[Dict[str, Any]], data)
    
    # Transform to match schedule table schema
    records: List[Dict[str, Any]] = []
    for event in events:
        event_id: str = event['id']
        record: Dict[str, Any] = {
            'event_id': event_id,
            'sport_key': event['sport_key'],
            'sport_title': event['sport_title'],
            'commence_time': event['commence_time'],
            'home_team': event['home_team'],
            'away_team': event['away_team']
        }
        records.append(record)
        logger.info(f"  Processing Event ID: {event_id} - {event['away_team']} @ {event['home_team']}")
    
    df = pd.DataFrame(records)
    df = fix_commence_time(df)  # Apply timezone conversion
    logger.info(f"Processed {len(df)} events for {sport_key}")
    return df
