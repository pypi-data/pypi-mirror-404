
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime, timedelta, timezone
from odds_api.core.types import OddsData

from odds_api.etl.transform.analytics import (
  add_best_odds_tracking, add_odds_movement_metrics,
deduplicate_facts, add_snapshot_flags, add_implied_probability,
add_opening_closing_lines, validate_odds_sanity, add_vig_metrics)

from commonv2.core.logging import setup_logger

# Setup logger
logger = setup_logger('odds_api.transform.historical', project_name='ODDS_API')

def _create_dim_game(df: pd.DataFrame) -> pd.DataFrame:
    """Create dim_oddapi_game dimension table."""
    dim_game = df[['event_id', 'sport_key', 'sport_title', 'commence_time',
                   'home_team', 'away_team']].drop_duplicates()
    dim_game['_extracted_at'] = pd.Timestamp.now(tz=timezone.utc)
    return dim_game.sort_values('event_id').reset_index(drop=True)

def _create_dim_teams(df: pd.DataFrame) -> pd.DataFrame:
    """Create dim_teams dimension table."""
    # Extract unique teams
    dim_game = df[['home_team', 'away_team', 'sport_key']].drop_duplicates()
    home_teams = dim_game[['home_team', 'sport_key']].rename(columns={'home_team': 'team_name'})
    away_teams = dim_game[['away_team', 'sport_key']].rename(columns={'away_team': 'team_name'})
    all_teams = pd.concat([home_teams, away_teams]).drop_duplicates()
    
    dim_teams = all_teams.copy()
    dim_teams['team_id'] = dim_teams['team_name'].str.replace(' ', '_').str.lower()
    dim_teams['sport_key'] = dim_teams['sport_key'].iloc[0] if not dim_teams.empty else None
    dim_teams['_extracted_at'] = pd.Timestamp.now(tz=timezone.utc)
    dim_teams['_note'] = 'Derived from game data. Enhance with /participants endpoint for team_id mapping.'
    
    return dim_teams.sort_values('team_id').reset_index(drop=True)

def _create_dim_bookmaker(df: pd.DataFrame) -> pd.DataFrame:
    """Create dim_bookmaker dimension table."""
    dim_bookmaker = df[['bookmaker_key', 'bookmaker_title']].drop_duplicates()
    dim_bookmaker = dim_bookmaker.rename(columns={'bookmaker_title': 'bookmaker_name'})
    dim_bookmaker['region'] = 'us'
    dim_bookmaker['_extracted_at'] = pd.Timestamp.now(tz=timezone.utc)
    return dim_bookmaker.sort_values('bookmaker_key').reset_index(drop=True)

def _create_dim_market(df: pd.DataFrame) -> pd.DataFrame:
    """Create dim_market dimension table."""
    market_names = {
        'h2h': 'Moneyline (Head to Head)',
        'spreads': 'Point Spread',
        'totals': 'Over/Under Total Points',
        'player_points': 'Player Total Points',
        'player_pass_tds': 'Player Passing Touchdowns',
        'player_pass_yds': 'Player Passing Yards',
        'player_rush_yds': 'Player Rushing Yards',
        'player_receptions': 'Player Receptions',
        'h2h_q1': 'Moneyline - 1st Quarter',
        'h2h_h1': 'Moneyline - 1st Half',
    }
    
    dim_market = df[['market_key']].drop_duplicates()
    dim_market['market_name'] = dim_market['market_key'].apply(
        lambda k: market_names.get(k, k.replace('_', ' ').title()) if isinstance(k, str) else k
    )
    dim_market['_extracted_at'] = pd.Timestamp.now(tz=timezone.utc)
    return dim_market.sort_values('market_key').reset_index(drop=True)

def _create_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """Create dim_date dimension table."""
    dim_game_copy = df[['commence_time']].drop_duplicates().copy()
    dim_game_copy['commence_time'] = pd.to_datetime(dim_game_copy['commence_time'])
    dim_game_copy['date'] = dim_game_copy['commence_time'].dt.date
    
    dim_date = dim_game_copy[['date']].drop_duplicates()
    dim_date['date'] = pd.to_datetime(dim_date['date'])
    dim_date['year'] = dim_date['date'].dt.year
    dim_date['month'] = dim_date['date'].dt.month
    dim_date['day'] = dim_date['date'].dt.day
    dim_date['day_of_week'] = dim_date['date'].dt.dayofweek
    dim_date['week_of_year'] = dim_date['date'].dt.isocalendar().week
    dim_date['is_weekend'] = dim_date['day_of_week'].isin([5, 6])
    dim_date['_extracted_at'] = pd.Timestamp.now(tz=timezone.utc)
    
    return dim_date.sort_values('date').reset_index(drop=True)

def _create_fact_odds_raw(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create IMMUTABLE fact_odds_raw table (TRUTH LAYER).
    
    Contains ONLY:
    - What the API returned
    - Stable selection keys
    - Semantic snapshot metadata (role + window label)
    - Timestamps from API
    
    NO DERIVED FIELDS! This keeps your truth layer clean.
    """
    fact_odds_raw = df[[
        # Composite key (WITH stable selection keys)
        'event_id', 'snapshot_timestamp', 'bookmaker_key', 'market_key',
        'selection_type', 'participant_id', 'side',
        
        # Snapshot metadata (SEMANTIC ROLES - NEW!)
        'snapshot_role',        # OPEN_T6D | PREGAME_SCHEDULED | IN_GAME
        'window_label',         # TNF | SNF | MNF | SUN_EARLY | SUN_LATE | etc.
        
        # Raw odds data (FROM API)
        'outcome_price',        # American odds (e.g., -110, +150)
        'outcome_point',        # Spread/total line (e.g.,  -3.5, 47.5)
        'outcome_description',  # Player name for props
        
        # Timestamps (FROM API)
        'bookmaker_last_update',
        'market_last_update',
        
        # Reference keys
        'sport_key',
        'commence_time',
        
        # Legacy (for backwards compatibility - can deprecate later)
        'outcome_name',         # String like "Minnesota Vikings"
    ]].copy()
    
    fact_odds_raw = fact_odds_raw.rename(columns={
        'outcome_price': 'odds_price',
        'outcome_point': 'odds_point',
        'outcome_description': 'player_name',
    })
    
    # Deduplicate on composite key (ONLY deduplication, no other transformations)
    fact_odds_raw['_odds_point_filled'] = fact_odds_raw['odds_point'].fillna(-999999)
    fact_odds_raw['_participant_id_filled'] = fact_odds_raw['participant_id'].fillna('__none__')
    
    composite_key = [
        'event_id', 'snapshot_timestamp', 'bookmaker_key', 'market_key',
        'selection_type', '_participant_id_filled', 'side', '_odds_point_filled'
    ]
    
    before_count = len(fact_odds_raw)
    fact_odds_raw = fact_odds_raw.drop_duplicates(subset=composite_key, keep='last')
    after_count = len(fact_odds_raw)
    
    # Drop temporary columns
    fact_odds_raw = fact_odds_raw.drop(columns=['_odds_point_filled', '_participant_id_filled'])
    
    if before_count != after_count:
        logger.warning(f"⚠️  Removed {before_count - after_count} duplicate raw records")
    
    # Add extraction metadata
    fact_odds_raw['_extracted_at'] = pd.Timestamp.now(tz=timezone.utc)
    
    # Convert timestamps to string for CSV compatibility
    fact_odds_raw['snapshot_timestamp'] = fact_odds_raw['snapshot_timestamp'].astype(str)
    fact_odds_raw['commence_time'] = fact_odds_raw['commence_time'].astype(str)
    fact_odds_raw['bookmaker_last_update'] = fact_odds_raw['bookmaker_last_update'].astype(str)
    fact_odds_raw['market_last_update'] = fact_odds_raw['market_last_update'].astype(str)
    
    fact_odds_raw = fact_odds_raw.sort_values([
        'snapshot_timestamp', 'event_id', 'bookmaker_key', 'market_key',
        'selection_type', 'participant_id', 'side', 'odds_point'
    ]).reset_index(drop=True)
    
    return fact_odds_raw

def _create_fact_odds_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create DERIVED fact_odds_features table (ANALYTICS LAYER).
    
    All fields here can be recomputed from fact_odds_raw.
    This keeps your truth layer clean and formulas agile!
    """
    # Start with raw data plus keys needed for analytics
    fact_odds = df[[
        'event_id', 'snapshot_timestamp', 'bookmaker_key', 'market_key',
        'selection_type', 'participant_id', 'side',
        'snapshot_role', 'window_label',  # NEW: Semantic metadata
        'outcome_price', 'outcome_point',
        'bookmaker_last_update',
        'market_last_update',
        'sport_key', 'commence_time',
    ]].copy()
    
    fact_odds = fact_odds.rename(columns={
        'outcome_price': 'odds_price',
        'outcome_point': 'odds_point',
    })
    
    # Apply ALL derived transformations
    fact_odds = add_implied_probability(fact_odds)
    fact_odds = add_vig_metrics(fact_odds)  # Add vig calculations (must run AFTER implied_probability)
    fact_odds = add_snapshot_flags(fact_odds)
    fact_odds = add_best_odds_tracking(fact_odds)
    fact_odds = add_odds_movement_metrics(fact_odds)
    fact_odds = deduplicate_facts(fact_odds)
    
    # Validate
    anomalies = validate_odds_sanity(fact_odds)
    if not anomalies.empty:
        logger.warning(f"      Anomalous odds in features:")
        logger.warning(f"      - Extreme odds (>±10000): {len(anomalies[anomalies['odds_price'].abs() > 10000])}")
        logger.warning(f"      - Invalid probabilities: {len(anomalies[(anomalies['implied_probability'] > 1.0) | (anomalies['implied_probability'] < 0)])}")
    
    # Add opening/closing line tracking
    fact_odds = add_opening_closing_lines(fact_odds, pregame_scheduled_minutes=15)
    
    # Metadata: Track when features were computed and which version
    fact_odds['_computed_at'] = pd.Timestamp.now(tz=timezone.utc)
    fact_odds['_features_version'] = 'v1.0'  # Track formula versions!
    
    # Convert timestamps to string for CSV compatibility
    fact_odds['snapshot_timestamp'] = fact_odds['snapshot_timestamp'].astype(str)
    fact_odds['commence_time'] = fact_odds['commence_time'].astype(str)
    fact_odds['opening_timestamp'] = fact_odds['opening_timestamp'].astype(str)
    fact_odds['closing_bookmaker_update_time'] = fact_odds['closing_bookmaker_update_time'].astype(str)
    fact_odds['closing_captured_at'] = fact_odds['closing_captured_at'].astype(str)
    
    fact_odds = fact_odds.sort_values([
        'snapshot_timestamp', 'event_id', 'bookmaker_key', 'market_key',
        'selection_type', 'participant_id', 'side', 'odds_point'
    ]).reset_index(drop=True)
    
    return fact_odds

def _create_dim_snapshot_navigation(df: pd.DataFrame) -> pd.DataFrame:
    """Create dim_snapshot_navigation dimension table."""
    dim_snapshot_nav = df[['snapshot_timestamp', 'previous_timestamp',
                           'next_timestamp']].drop_duplicates()
    dim_snapshot_nav['_extracted_at'] = pd.Timestamp.now(tz=timezone.utc)
    return dim_snapshot_nav.sort_values('snapshot_timestamp').reset_index(drop=True)


def normalize_to_star_schema(flat_records: List[OddsData]) -> Dict[str, pd.DataFrame]:
    """
    Normalize flattened odds records into ENHANCED star schema tables.
    
    Creates 7 normalized tables with analytics enhancements:
    - dim_oddapi_game: Game reference (event_id PK)
    - dim_team: Team reference (team_id PK) - placeholder for /participants data
    - dim_bookmaker: Bookmaker reference (bookmaker_key PK) with region
    - dim_market: Market type reference (market_key PK)
    - dim_date: Date dimension (date PK) for temporal analysis
    - fact_odds: Outcome-level odds with ANALYTICS (composite PK)
      * Implied probability, first/last snapshot flags, best odds tracking, movement metrics
    - dim_snapshot_navigation: Temporal navigation (snapshot_timestamp PK)
    
    Args:
        flat_records: List of flattened odds records from flatten_event_odds()
        
    Returns:
        Dict of table_name → DataFrame
    """
    if not flat_records:
        return {}
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(flat_records)
    
    # Create all dimension tables
    dim_game = _create_dim_game(df)
    dim_team = _create_dim_teams(df)
    dim_bookmaker = _create_dim_bookmaker(df)
    dim_market = _create_dim_market(df)
    dim_date = _create_dim_date(df)
    dim_snapshot_nav = _create_dim_snapshot_navigation(df)
    fact_odds = _create_fact_odds_raw(df)
    fact_odds_features = _create_fact_odds_features(df)
    
    return {
        'dim_oddapi_game': dim_game,
        'dim_team': dim_team,
        'dim_bookmaker': dim_bookmaker,
        'dim_market': dim_market,
        'dim_date': dim_date,
        'fact_odds_raw': fact_odds,
        'fact_odds_features': fact_odds_features,
        'dim_snapshot_navigation': dim_snapshot_nav,
    }
