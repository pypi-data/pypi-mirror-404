"""
Game-level dimension builder for nflfastRv3.

This module creates a TRUE game-level dimension table by aggregating
play-by-play data. Replaces the old dim_game which was actually play-level.

Pattern: Simple aggregation function (2 complexity points)
- Aggregation logic: 1 point
- Data type conversions: +1 point
"""

import pandas as pd
from commonv2 import get_logger
from .cleaning_dimensions import categorize_weather


def build_dim_game(engine, logger=None) -> pd.DataFrame:
    """
    Build TRUE game-level dimension from play-by-play data.
    
    Aggregates play-level data (~46K rows) to game-level (~258 rows).
    
    Args:
        engine: DataFrameEngine with play_by_play data OR SQLAlchemy engine
        logger: Optional logger
        
    Returns:
        pd.DataFrame: Game-level dimension with ~35 columns
        
    Example:
        Input:  46,136 plays across 258 games
        Output: 258 game-level rows (99.4% reduction)
    """
    from .dataframe_engine import DataFrameEngine
    
    logger = logger or get_logger('nflfastRv3.transformations.dimension_game')
    
    # Extract DataFrame from DataFrameEngine or use engine directly
    if isinstance(engine, DataFrameEngine):
        raw_pbp = engine.df
        logger.info(f"Building true dim_game from {len(raw_pbp):,} plays (bucket mode)...")
    else:
        # Database mode - would need SQL query here (not implemented yet)
        raise NotImplementedError("Database mode not yet implemented for dim_game. Use bucket mode.")
    
    # Step 1: Define aggregation rules
    agg_rules = {
        # Identifiers (constant per game - take first)
        'season': 'first',
        'week': 'first',
        'game_date': 'first',
        'season_type': 'first',
        
        # Teams (constant per game - take first)
        'home_team': 'first',
        'away_team': 'first',
        'home_coach': 'first',
        'away_coach': 'first',
        'div_game': 'first',
        
        # Venue (constant per game - take first)
        'stadium_id': 'first',
        'game_stadium': 'first',  # Use this instead of 'stadium' (100% null in 1999 data)
        'location': 'first',
        'roof': 'first',
        'surface': 'first',
        'temp': 'first',          # 23% nulls - OK for first()
        'wind': 'first',          # 23% nulls - OK for first()
        'weather': 'first',  # 100% null but needed 
        
        # Scores (accumulate to final - take max)
        'total_home_score': 'max',
        'total_away_score': 'max',
        
        # Betting (constant per game - take first)
        'spread_line': 'first',
        'total_line': 'first',
        
        # Game stats (aggregate from plays)
        'yards_gained': 'sum',
        'touchdown': 'sum',
        'interception': 'sum',
        'fumble_lost': 'sum',
        'field_goal_attempt': 'sum',
        'punt_attempt': 'sum',
        'penalty': 'sum',
        'penalty_yards': 'sum',  # 93% nulls but sum() handles it
    }
    
    # Step 2: Group by game_id and aggregate
    logger.info("Aggregating plays to game level...")
    dim_game = raw_pbp.groupby('game_id', as_index=False).agg(agg_rules)
    
    # Step 3: Rename columns to match dim_game schema
    dim_game = dim_game.rename(columns={
        'total_home_score': 'home_score',
        'total_away_score': 'away_score',
        'game_stadium': 'stadium',  # Rename to standard 'stadium'
        'yards_gained': 'total_yards',
        'touchdown': 'total_touchdowns',
        'interception': 'total_interceptions',
        'fumble_lost': 'total_fumbles_lost',
        'field_goal_attempt': 'total_field_goal_attempts',
        'punt_attempt': 'total_punts',
        'penalty': 'total_penalties',
        'penalty_yards': 'total_penalty_yards',
    })
    
    # Step 4: Add derived columns
    logger.info("Calculating derived fields...")
    
    # Total plays per game
    play_counts = raw_pbp.groupby('game_id', observed=True).size().reset_index(name='total_plays')
    dim_game = dim_game.merge(play_counts, on='game_id', how='left')
    
    # Game outcomes
    dim_game['result'] = dim_game['home_score'] - dim_game['away_score']
    dim_game['total'] = dim_game['home_score'] + dim_game['away_score']
    dim_game['total_turnovers'] = (
        dim_game['total_interceptions'] + dim_game['total_fumbles_lost']
    )
    dim_game['home_team_won'] = (dim_game['result'] > 0).astype(int)
    
    # Step 5: Data type conversions
    dim_game['game_date'] = pd.to_datetime(dim_game['game_date'])
    dim_game['season'] = dim_game['season'].astype('Int64')
    dim_game['week'] = dim_game['week'].astype('Int64')
    dim_game['home_score'] = dim_game['home_score'].astype('Int64')
    dim_game['away_score'] = dim_game['away_score'].astype('Int64')
    dim_game['result'] = dim_game['result'].astype('Int64')
    dim_game['total'] = dim_game['total'].astype('Int64')
    dim_game['div_game'] = dim_game['div_game'].astype('boolean')
    
    # Step 6: Add categorizations (from existing cleaning_dimensions.py)
    # Note: weather column is 100% null in 1999 data, so weather_category will be 'Unknown'
    # But categorize_weather also adds venue_type and game type indicators
    dim_game = categorize_weather(dim_game)
    
    # Step 7: Handle nulls in optional columns
    dim_game['stadium'] = dim_game['stadium'].fillna('Unknown')
    dim_game['stadium_id'] = dim_game['stadium_id'].fillna('Unknown')
    dim_game['home_coach'] = dim_game['home_coach'].fillna('Unknown')
    dim_game['away_coach'] = dim_game['away_coach'].fillna('Unknown')
    
    logger.info(f"✓ Built true dim_game: {len(dim_game):,} games with {len(dim_game.columns)} columns")
    return dim_game
