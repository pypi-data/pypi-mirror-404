"""
Odds Features (Game-Level) - Aggregated market consensus for CLV/ROI reporting

Transforms play-by-play odds into game-level features for betting analysis.
This table supports CLV (Closing Line Value) calculations and ROI simulations
in training reports without grain mismatch issues.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Implementation - calls infrastructure directly)

Data Source: odds_features_v1 (play-by-play table)
Output: odds_features_game_v1 table (features schema, game-level)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List


class OddsGameFeatures:
    """
    Aggregate play-by-play odds to game-level for CLV/ROI reporting.
    
    **Purpose**: Provide game-grain odds for market comparison without row explosion
    
    **Data Flow**:
    1. Load odds_features_v1 (play-by-play level)
    2. Aggregate to game level:
       - Opening lines: FIRST play values
       - Closing lines: LAST play values
       - Leverage: MAX absolute WPA
    3. Return game-level DataFrame
    
    **Pattern**: Minimum Viable Decoupling (2 complexity points)
    Follows same pattern as OddsFeatures and ContextualFeatures.
    """
    
    def __init__(self, db_service, logger, bucket_adapter=None):
        """
        Initialize game-level odds feature builder.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            bucket_adapter: Optional bucket adapter (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        self.bucket_adapter = bucket_adapter
    
    def build_features(self, seasons: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Build game-level odds features for specified seasons.
        
        Args:
            seasons: List of seasons to build (e.g., [2024, 2025]). If None, builds all available.
            
        Returns:
            Dictionary with:
                - status (str): 'success' or 'error'
                - dataframe (DataFrame): Game-level odds features
                - features_built (int): Number of games
                - seasons_processed (int): Number of seasons
        """
        self.logger.info(f"Building game-level odds features for seasons: {seasons or 'all'}")
        
        try:
            # Load play-by-play odds from bucket
            from commonv2.persistence.bucket_adapter import get_bucket_adapter
            
            bucket = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
            
            self.logger.info(" Loading play-by-play odds (odds_features_v1)...")
            pbp_odds = bucket.read_data('odds_features_v1', 'features')
            
            if pbp_odds is None or pbp_odds.empty:
                raise RuntimeError("odds_features_v1 table is empty - run odds feature build first")
            
            self.logger.info(f"✓ Loaded {len(pbp_odds):,} play-level odds rows")
            
            # Filter seasons if requested
            if seasons:
                season_list = list(seasons) if isinstance(seasons, (list, tuple)) else [seasons]
                pbp_odds = pbp_odds[pbp_odds['season'].isin(season_list)]
                self.logger.info(f"    Filtered to seasons {season_list}: {len(pbp_odds):,} rows")
            
            # Aggregate to game level
            self.logger.info("📊 Aggregating play-by-play odds to game level...")
            game_odds = self._aggregate_to_game_level(pbp_odds)
            
            self.logger.info(f"✓ Built game-level odds for {len(game_odds):,} games")
            
            return {
                'status': 'success',
                'dataframe': game_odds,
                'features_built': len(game_odds),
                'seasons_processed': game_odds['season'].nunique()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build game-level odds features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _aggregate_to_game_level(self, pbp_odds: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate play-level odds to game-level.
        
        Aggregation strategy:
        - Opening lines: FIRST play of game (earliest timestamp)
        - Closing lines: LAST play of game (latest timestamp)
        - Leverage: MAX absolute WPA in game
        
        Args:
            pbp_odds: Play-by-play odds DataFrame
            
        Returns:
            Game-level DataFrame (1 row per game)
        """
        # Sort by game_id to ensure proper first/last aggregation
        pbp_odds = pbp_odds.sort_index()
        
        # Aggregate to game level
        game_agg = pbp_odds.groupby('game_id', as_index=False).agg({
            'season': 'first',
            'week': 'first',
            
            # Opening lines (first play)
            'consensus_spread': 'first',
            'consensus_total': 'first',
            'consensus_home_prob': 'first',
            'vegas_home_wp': 'first',
            'vegas_wp': 'first',
            
            # Closing lines (last play)
            # Note: spread_line/total_line typically constant within game,
            # but we capture both first/last for future use
            
            # Leverage metrics (maximum critical moment in game)
            'vegas_home_wpa': lambda x: x.abs().max() if x.notna().any() else np.nan,
            'vegas_wpa': lambda x: x.abs().max() if x.notna().any() else np.nan
        })
        
        # Keep standard column names for market_analyzer compatibility
        # Just add the game-level aggregations
        game_agg['consensus_spread_close'] = game_agg['consensus_spread']  # For future use
        game_agg['consensus_total_close'] = game_agg['consensus_total']
        game_agg['max_leverage_home'] = game_agg['vegas_home_wpa'].abs()
        game_agg['max_leverage'] = game_agg['vegas_wpa'].abs()
        
        # vegas_home_wpa is now the max leverage (for compatibility with leverage analysis)
        game_agg['vegas_home_wpa'] = game_agg['max_leverage_home']
        game_agg['vegas_wpa'] = game_agg['max_leverage']
        
        # Log coverage statistics
        total = len(game_agg)
        self.logger.info(f"  Game-level coverage:")
        self.logger.info(f"    consensus_spread: {game_agg['consensus_spread'].notna().sum()}/{total} ({game_agg['consensus_spread'].notna().mean():.1%})")
        self.logger.info(f"    consensus_home_prob: {game_agg['consensus_home_prob'].notna().sum()}/{total} ({game_agg['consensus_home_prob'].notna().mean():.1%})")
        self.logger.info(f"    vegas_home_wp: {game_agg['vegas_home_wp'].notna().sum()}/{total} ({game_agg['vegas_home_wp'].notna().mean():.1%})")
        self.logger.info(f"    max_leverage_home: {game_agg['max_leverage_home'].notna().sum()}/{total} ({game_agg['max_leverage_home'].notna().mean():.1%})")
        
        return game_agg


def create_odds_game_features(db_service=None, logger=None, bucket_adapter=None):
    """
    Factory function to create game-level odds features builder.
    
    Matches pattern from:
    - create_odds_features()
    - create_contextual_features()
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        OddsGameFeatures: Configured builder
    """
    from ....shared.database_router import get_database_router
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline.odds_game_features')
    
    return OddsGameFeatures(db_service, logger, bucket_adapter)


__all__ = ['OddsGameFeatures', 'create_odds_game_features']
