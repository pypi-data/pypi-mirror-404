"""
Results data transformation functions.
Handles fetching and processing scores/results data.
"""

import pandas as pd
from typing import List, Optional, Any, Dict
from commonv2 import get_logger

from .core import fix_commence_time
from ..extract.api import fetch_scores_data
from odds_api.core.types import SportKey

logger = get_logger(__name__)

def get_results_data(sport_key: SportKey, days_from: Optional[int] = None) -> pd.DataFrame:
    """
    Fetch and transform scores/results data.
    
    Args:
        sport_key: Sport identifier (e.g., 'americanfootball_nfl'). Provided by pipeline/CLI.
        days_from: Optional number of days to look back for results (1-3).
    
    Returns:
        DataFrame with results data ready for database insert.
    """
    
    logger.info(f"Fetching results data for {sport_key}...")
    raw_data = fetch_scores_data(sport_key, days_from)
    # API returns List[Dict[str, Any]] for scores endpoint
    data: List[Dict[str, Any]] = raw_data if isinstance(raw_data, list) else [raw_data]
    
    # Transform to match results table schema
    records = []
    for event in data:
        event_id = event['id']
        # Extract scores from nested structure
        home_score = None
        away_score = None
        if 'scores' in event and event['scores']:
            for score in event['scores']:
                if score['name'] == event['home_team']:
                    home_score = score.get('score')
                elif score['name'] == event['away_team']:
                    away_score = score.get('score')
        
        logger.info(f"  Processing Result Event ID: {event_id} - {event['away_team']} ({away_score}) @ {event['home_team']} ({home_score})")
        
        record = {
            'event_id': event_id,
            'sport_key': event['sport_key'],
            'sport_title': event['sport_title'],
            'commence_time': event['commence_time'],
            'completed': event.get('completed', False),
            'home_team': event['home_team'],
            'away_team': event['away_team'],
            'home_score': home_score,
            'away_score': away_score,
            'last_update': event.get('last_update')
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    df = fix_commence_time(df)  # Apply timezone conversion
    
    # Convert last_update to datetime if present
    if 'last_update' in df.columns and not df['last_update'].isna().all():
        df['last_update'] = pd.to_datetime(df['last_update'], utc=True).dt.tz_convert('America/New_York')
    
    logger.info(f"Processed {len(df)} results for {sport_key}")
    return df
