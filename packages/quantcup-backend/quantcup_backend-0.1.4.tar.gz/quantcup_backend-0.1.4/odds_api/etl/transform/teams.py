"""
Teams data transformation functions.
Handles fetching and processing teams/participants data.
"""

from typing import List, Dict, Any, cast
import pandas as pd
from commonv2 import get_logger

from ..extract.api import fetch_participants_data

logger = get_logger(__name__)

def get_teams_data(sport_key: str) -> pd.DataFrame:
    """
    Fetch and transform teams/participants data.
    
    Args:
        sport_key: Sport identifier (e.g., 'americanfootball_nfl', 'basketball_nba')
    
    Returns:
        DataFrame with columns: participant_id, sport_key, full_name
    """
    
    logger.info(f"Fetching teams/participants data for {sport_key}...")
    # fetch_participants_data returns OddsData (Dict[str, Any]) but API returns a list
    data = cast(List[Dict[str, Any]], fetch_participants_data(sport_key))
    
    # Debug: log the structure of the first participant
    if data and len(data) > 0:
        logger.info(f"Sample participant structure: {data[0]}")
    
    # Transform to match teams table schema
    records: List[Dict[str, Any]] = []
    for participant in data:
        # Handle different possible field names for participant name
        name = (
            participant.get('name') or
            participant.get('title') or
            participant.get('full_name') or
            str(participant.get('id', 'Unknown'))
        )
        
        record: Dict[str, Any] = {
            'participant_id': participant['id'],
            'sport_key': sport_key,
            'full_name': name
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"Processed {len(df)} teams/participants for {sport_key}")
    return df
