"""
Leagues data transformation functions.
Handles fetching and processing sports/leagues data.
"""

from typing import Any, Dict, List, Union, cast
import pandas as pd
from commonv2 import get_logger

from ..extract.api import fetch_sports_data

logger = get_logger(__name__)

def get_leagues_data() -> pd.DataFrame:
    """Fetch and transform sports/leagues data"""
    
    logger.info("Fetching sports/leagues data...")
    raw_data = fetch_sports_data()
    
    # fetch_sports_data returns List[Dict], cast to ensure type safety
    data = cast(List[Dict[str, Any]], raw_data)
    
    # Transform to match leagues table schema
    records: List[Dict[str, Any]] = []
    for sport in data:
        record: Dict[str, Any] = {
            'sport_key': sport['key'],
            'group_name': sport['group'],
            'title': sport['title'],
            'description': sport.get('description', ''),
            'active': sport['active'],
            'has_outrights': sport.get('has_outrights', False)
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"Processed {len(df)} sports/leagues")
    return df
