"""
Odds data transformation functions.
Handles fetching, normalizing, and processing betting odds data.
"""

import pandas as pd
import json
import os
from commonv2 import get_logger

from typing import Any, Dict, List, Optional, Tuple
from .core import enrich_odds_metrics, fix_commence_time, output_dir
from ..extract.api import fetch_odds_data
from odds_api.core import get_team_registry
from odds_api.core.types import SportKey, MarketKey, EventID, OddsData, ISOTimestamp, MarketList, SelectionSide, SelectionType, ParticipantID

logger = get_logger(__name__)

# Initialize team registry for stable participant ID lookups
TEAM_REGISTRY = get_team_registry()

def _parse_selection_keys(market_key: MarketKey, outcome_name: Optional[str],
                          outcome_description: Optional[str],
                          home_team: Optional[str], away_team: Optional[str],
                          home_participant_id: Optional[str],
                          away_participant_id: Optional[ParticipantID]) -> Tuple[SelectionType, Optional[ParticipantID], Optional[SelectionSide]]:
    """
    Parse stable selection keys using Odds API participant IDs.
    
    Args:
        market_key: Market type (h2h, spreads, totals, player_*)
        outcome_name: Outcome name from API (team name or Over/Under)
        outcome_description: Additional description (player name for props)
        home_team: Home team name
        away_team: Away team name
        home_participant_id: Home team participant ID from registry
        away_participant_id: Away team participant ID from registry
    
    Returns:
        (selection_type, participant_id, side)
    """
    # Parse based on market type
    if market_key in ['h2h', 'spreads']:
        # Team-based markets - use participant IDs!
        outcome_participant_id = TEAM_REGISTRY.get_participant_id(outcome_name)
        
        if outcome_participant_id == home_participant_id:
            return ('team', home_participant_id, 'home')
        elif outcome_participant_id == away_participant_id:
            return ('team', away_participant_id, 'away')
        else:
            # Fallback if registry doesn't recognize the outcome name
            logger.warning(f"Team not matched: outcome='{outcome_name}', home={home_team}, away={away_team}")
            return ('team', outcome_participant_id, 'unknown')
    
    elif market_key == 'totals':
        # Total points (no participant)
        side = 'over' if outcome_name and outcome_name.lower() == 'over' else 'under'
        return ('total', None, side)
    
    elif market_key.startswith('player_'):
        # Player props - use player name as ID (could enhance with player registry later)
        player_id = outcome_description.lower().replace(' ', '_') if outcome_description else None
        side = 'over' if outcome_name and outcome_name.lower() == 'over' else 'under'
        return ('prop', player_id, side)
    
    else:
        # Unknown market type
        logger.debug(f"Unknown market type: {market_key}")
        return ('unknown', None, None)

def flatten_event_odds(event_data: OddsData, snapshot_timestamp: ISOTimestamp, snapshot_requested_ts: ISOTimestamp, snapshot_role: str, window_label: str, previous_timestamp: ISOTimestamp, next_timestamp: ISOTimestamp) -> List[OddsData]:
    """
    Flatten nested event odds data with STABLE SELECTION KEYS and semantic role metadata.
    
    WAREHOUSE-GRADE: Uses Odds API participant IDs for reliable team identification.
    Each record represents one outcome (bet option) with all context.
    """
    records = []
    
    if not event_data:
        return records
    
    # Event-level info
    # API can return 'id' or 'event_id' depending on the endpoint
    event_id = event_data.get('event_id') or event_data.get('id')
    sport_key = event_data.get('sport_key')
    sport_title = event_data.get('sport_title')
    commence_time = event_data.get('commence_time')
    home_team = event_data.get('home_team')
    away_team = event_data.get('away_team')
    
    # Get stable participant IDs for home/away teams
    home_participant_id = TEAM_REGISTRY.get_participant_id(home_team)
    away_participant_id = TEAM_REGISTRY.get_participant_id(away_team)
    
    # Loop through bookmakers
    for bookmaker in event_data.get('bookmakers', []):
        bookmaker_key = bookmaker.get('key')
        bookmaker_title = bookmaker.get('title')
        bookmaker_last_update = bookmaker.get('last_update')
        
        # Loop through markets
        for market in bookmaker.get('markets', []):
            market_key = market.get('key')
            market_last_update = market.get('last_update')
            
            # Loop through outcomes
            for outcome in market.get('outcomes', []):
                outcome_name = outcome.get('name')
                outcome_price = outcome.get('price')
                outcome_point = outcome.get('point')
                outcome_description = outcome.get('description')
                
                # Derive stable selection keys using participant IDs
                selection_type, participant_id, side = _parse_selection_keys(
                    market_key=market_key,
                    outcome_name=outcome_name,
                    outcome_description=outcome_description,
                    home_team=home_team,
                    away_team=away_team,
                    home_participant_id=home_participant_id,
                    away_participant_id=away_participant_id
                )
                
                records.append({
                    # Snapshot metadata
                    'snapshot_timestamp': snapshot_timestamp,
                    'snapshot_role': snapshot_role,
                    'window_label': window_label,
                    'previous_timestamp': previous_timestamp,
                    'next_timestamp': next_timestamp,
                    
                    # Event info
                    'event_id': event_id,
                    'sport_key': sport_key,
                    'sport_title': sport_title,
                    'commence_time': commence_time,
                    'home_team': home_team,
                    'away_team': away_team,
                    
                    # Bookmaker info
                    'bookmaker_key': bookmaker_key,
                    'bookmaker_title': bookmaker_title,
                    'bookmaker_last_update': bookmaker_last_update,
                    
                    # Market info
                    'market_key': market_key,
                    'market_last_update': market_last_update,
                    
                    # Outcome
                    'outcome_name': outcome_name,
                    'outcome_price': outcome_price,
                    'outcome_point': outcome_point,
                    'outcome_description': outcome_description,
                    
                    # STABLE SELECTION KEYS
                    'selection_type': selection_type,
                    'participant_id': participant_id,
                    'side': side,
                })
    
    return records

def normalize_odds_df(df: pd.DataFrame) -> pd.DataFrame:
    """Optimized normalization using vectorized operations instead of nested loops"""
    
    def _safe_bookmakers(obj):
        """Normalize bookmakers column to list format.
        
        Handles both pre-parsed lists and JSON strings from persistence layers.
        """
        if isinstance(obj, list):
            return obj
        if obj is None or obj == '':
            return []
        if isinstance(obj, str):
            try:
                parsed = json.loads(obj)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse bookmakers JSON: {e}")
                return []
        
        logger.warning(f"Unexpected bookmakers type: {type(obj)}")
        return []
    
    # Fix the bookmakers column to handle both list and string cases
    df = df.copy()
    df["bookmakers"] = df["bookmakers"].apply(_safe_bookmakers)
    
    # Pre-flatten the nested JSON structure using pd.json_normalize
    flattened_rows = []
    
    for _, row in df.iterrows():
        # Extract base game info once per game
        base_info = {
            'event_id': row['id'],
            'sport_key': row['sport_key'],
            'sport_title': row['sport_title'],
            'commence_time': row['commence_time'],
            'home_team': row['home_team'],
            'away_team': row['away_team']
        }
        
        # Flatten bookmakers and markets in one pass
        for bookmaker in row['bookmakers']:
            bookmaker_info = {
                'bookmaker_key': bookmaker['key'],
                'bookmaker_title': bookmaker['title'],
                'bookmaker_last_update': bookmaker['last_update']
            }
            
            for market in bookmaker['markets']:
                # Create base row with all info
                market_row = {**base_info, **bookmaker_info, 'market_key': market['key']}
                
                # Pre-create outcome lookup for this market
                outcome_lookup = {outcome['name']: outcome for outcome in market['outcomes']}
                
                # Initialize all odds columns
                market_row.update({
                    'home_team_odds': None, 'away_team_odds': None,
                    'home_team_spread': None, 'away_team_spread': None,
                    'home_team_spread_odds': None, 'away_team_spread_odds': None,
                    'over_odds': None, 'under_odds': None, 'total_points': None
                })
                
                # Vectorized market processing using lookup
                if market['key'] == 'h2h':
                    if row['home_team'] in outcome_lookup:
                        market_row['home_team_odds'] = outcome_lookup[row['home_team']]['price']
                    if row['away_team'] in outcome_lookup:
                        market_row['away_team_odds'] = outcome_lookup[row['away_team']]['price']
                
                elif market['key'] == 'spreads':
                    if row['home_team'] in outcome_lookup:
                        outcome = outcome_lookup[row['home_team']]
                        market_row['home_team_spread_odds'] = outcome['price']
                        market_row['home_team_spread'] = outcome.get('point', 0)
                    if row['away_team'] in outcome_lookup:
                        outcome = outcome_lookup[row['away_team']]
                        market_row['away_team_spread_odds'] = outcome['price']
                        market_row['away_team_spread'] = outcome.get('point', 0)
                
                elif market['key'] == 'totals':
                    if 'Over' in outcome_lookup:
                        outcome = outcome_lookup['Over']
                        market_row['over_odds'] = outcome['price']
                        market_row['total_points'] = outcome.get('point', 0)
                    if 'Under' in outcome_lookup:
                        market_row['under_odds'] = outcome_lookup['Under']['price']
                
                flattened_rows.append(market_row)
    
    return pd.DataFrame(flattened_rows)

def get_odds(api_key: Optional[str] = None, sport_key: SportKey = 'americanfootball_nfl', markets: Optional[List[str]] = None) -> pd.DataFrame:
    """Main function to fetch and process odds data, return clean DataFrame ready for database insert"""
    
    if markets is None:
        markets = ['h2h', 'spreads', 'totals']
    
    # Fetch data with retry logic
    data = fetch_odds_data(sport_key=sport_key, markets=markets)
    
    # Create initial DataFrame
    df = pd.DataFrame(data)
    
    # Process pipeline with unified odds enrichment (Phase 5 optimization)
    return (df
            .pipe(normalize_odds_df)
            .pipe(fix_commence_time)           # Handle timezone properly
            .pipe(enrich_odds_metrics, stake=100)  # Single-pass odds processing
            .drop_duplicates(subset=['game_id', 'bookmaker_key', 'market_key', 'home_team_odds', 'away_team_odds']))
