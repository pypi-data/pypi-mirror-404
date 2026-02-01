"""
Player dimension builder for nflfastRv3.

Pattern: Enhanced simple function (3 complexity points)
- Base function: 1 point
- Multi-source consolidation: +1 point
- Complex data enrichment: +1 point

Preserves V2 sophistication:
- 4-table data consolidation (players, rosters, ff_playerids, roster_ids)
- 15+ fantasy platform ID mappings
- Current team assignment logic
- Age calculations and position standardization
"""

import pandas as pd
from commonv2 import get_logger
from .dataframe_engine import DataFrameEngine
from .sql_templates_dimensions import (
    get_player_base_sql,
    get_player_current_team_sql,
    get_player_fantasy_ids_sql
)
from .cleaning_dimensions import (
    clean_player_data,
    calculate_player_age,
    standardize_positions
)
from .warehouse_utils import validate_table_data


def build_dim_player(engine, logger=None) -> pd.DataFrame:
    """
    Build player dimension with consolidated multi-source player data.
    
    Preserves V2 features:
    - Multi-source consolidation (players, rosters, fantasy IDs)
    - Comprehensive ID mapping for fantasy platforms
    - Current team assignment with recency logic
    - Age calculations and position standardization
    
    UPDATED: Supports bucket-first architecture via DataFrameEngine
    
    Args:
        engine: SQLAlchemy database engine OR DataFrameEngine (bucket data)
        logger: Optional logger override (Layer 3)
        
    Returns:
        pd.DataFrame: Complete player dimension
    """
    logger = logger or get_logger('nflfastRv3.transformations.player')
    logger.info("Building dim_player with V2 multi-source consolidation...")
    
    try:
        # Bucket-first architecture: Load directly from bucket (no DataFrameEngine needed)
        from nflfastRv3.shared.bucket_adapter import BucketAdapter
        
        logger.info("dim_player: Loading player data from bucket")
        bucket = BucketAdapter(logger=logger)
        
        # Load all player-related tables from bucket
        df_players = bucket.read_data('players', schema='raw_nflfastr')
        df_wkly_rosters = bucket.read_data('wkly_rosters', schema='raw_nflfastr')
        
        logger.info(f"Loaded {len(df_players):,} rows from players table")
        logger.info(f"Loaded {len(df_wkly_rosters):,} rows from wkly_rosters table")
        
        if df_players.empty:
            raise ValueError("No players table found in bucket. Cannot build dim_player without source data.")
        
        # Use players table as base (has birth_date, college, etc.)
        df = df_players.copy()
        
        # Enrich with current_team from most recent roster
        if not df_wkly_rosters.empty:
            latest_rosters = df_wkly_rosters.sort_values(
                ['season', 'week'], ascending=False
            ).groupby('gsis_id').first().reset_index()
            
            df = df.merge(
                latest_rosters[['gsis_id', 'team', 'season', 'week']],
                on='gsis_id',
                how='left'
            )
            df = df.rename(columns={
                'team': 'current_team',
                'season': 'current_season',
                'week': 'current_week'
            })
            logger.info(f"✓ Enriched with current team data")
        else:
            logger.warning("No wkly_rosters table found - current team data will be null")
            df['current_team'] = None
            df['current_season'] = None
            df['current_week'] = None
        
        logger.info(f"dim_player: Extracted {len(df):,} players from bucket")
        
        # Step 4: Clean and enrich data (V2 business logic preserved)
        logger.info("dim_player: Cleaning and standardizing player data")
        df = clean_player_data(df)
        df = calculate_player_age(df)
        df = standardize_positions(df)
        
        # Step 5: Validate data quality
        validation_result = validate_table_data(
            df, 
            'dim_player',
            required_columns=['gsis_id', 'player_name', 'position'],
            logger=logger
        )
        
        if validation_result['status'] == 'error':
            logger.error(f"dim_player validation failed: {validation_result['issues']}")
            return pd.DataFrame()
        
        logger.info(f"✓ Built dim_player: {len(df):,} players with complete ID mapping")
        return df
        
    except Exception as e:
        logger.error(f"Failed to build dim_player: {e}", exc_info=True)
        return pd.DataFrame()


def create_dim_player_builder(engine=None, logger=None):
    """
    Create dim_player builder with default dependencies.
    
    Args:
        engine: Optional database engine override
        logger: Optional logger override
        
    Returns:
        function: Configured dim_player builder function
    """
    def _build_dim_player():
        return build_dim_player(engine, logger)
    
    return _build_dim_player
