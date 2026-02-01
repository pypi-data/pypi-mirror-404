from typing import List, Dict, Any, Optional, Union, TypedDict, Callable
from datetime import datetime
import pandas as pd
try:
    from typing import NotRequired
except ImportError:
    # Python < 3.11
    from typing_extensions import NotRequired

# Type aliases for clarity
SportKey = str
MarketKey = str
EventID = str
BookmakerKey = str
OddsData = Dict[str, Any]
DataFrameOrNone = Optional[pd.DataFrame]
ISOTimestamp = str

# Phase 1: Core Type System Expansion
MarketList = List[MarketKey]
QuotaCost = int
RegionKey = str
ParticipantID = str
SelectionSide = str  # e.g., 'home', 'away', 'over', 'under'
SelectionType = str  # e.g., 'team', 'total', 'prop'

class PipelineConfig(TypedDict):
    """
    Configuration for a pipeline in the registry.
    
    All pipelines accept **kwargs for their fetch functions to provide
    a consistent interface. Common kwargs include:
    - sport_key: SportKey (required for most pipelines)
    - event_id: EventID (for event-specific data)
    - markets: MarketList (for filtering markets)
    - days_from: int (for historical data lookback)
    
    Fields:
        fetch_fn: Function that fetches and returns a DataFrame.
                  Should accept **kwargs. Can be None for special pipelines.
        required_cols: List of column names that must be present in the result.
        table: Database table name where data will be loaded.
        uses_quota: Whether this pipeline consumes API quota.
        update_interval: Seconds between updates (0 = manual trigger only).
        description: Human-readable description (optional).
    """
    fetch_fn: Optional[Callable[..., pd.DataFrame]]
    required_cols: List[str]
    table: str
    uses_quota: bool
    update_interval: int
    description: NotRequired[str]

__all__ = [
    'SportKey',
    'MarketKey',
    'EventID',
    'BookmakerKey',
    'OddsData',
    'DataFrameOrNone',
    'ISOTimestamp',
    'MarketList',
    'QuotaCost',
    'RegionKey',
    'ParticipantID',
    'SelectionSide',
    'SelectionType',
    'PipelineConfig'
]
