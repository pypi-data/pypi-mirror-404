"""
Odds Features - Extract market consensus from play-by-play odds data

Transforms raw betting line data (from nflfastR play_by_play table) into
play-by-play level odds features for use in ML training and CLV analysis.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Implementation - calls infrastructure directly)

Data Source: raw_nflfastr.play_by_play (spread_line, total_line columns)
Output: odds_features_v1 table (features schema, play-by-play level)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List


class OddsFeatures:
    """
    Build consensus odds features from play-by-play betting line data.
    
    **Purpose**: Transform play-level odds from nflfastR play_by_play
    
    **Data Flow**:
    1. Load play_by_play table from bucket (raw_nflfastr schema)
    2. Transform spread_line and total_line at play level
    3. Convert spread_line to implied home win probability for each play
    4. Return play-by-play level features
    
    **Pattern**: Minimum Viable Decoupling (2 complexity points)
    Follows same pattern as InjuryFeatures and ContextualFeatures.
    """
    
    def __init__(self, db_service, logger, bucket_adapter=None):
        """
        Initialize odds feature builder.
        
        Args:
            db_service: Database service (Layer 3) - for consistency with other feature sets
            logger: Logger instance (Layer 3)
            bucket_adapter: Optional bucket adapter (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        self.bucket_adapter = bucket_adapter
    
    def build_features(self, seasons: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Build odds features for specified seasons.
        
        Args:
            seasons: List of seasons to build (e.g., [2024, 2025]). If None, builds all available.
            
        Returns:
            Dictionary with:
                - status (str): 'success' or 'error'
                - dataframe (DataFrame): Play-by-play odds features
                - features_built (int): Number of plays
                - seasons_processed (int): Number of seasons
        """
        self.logger.info(f"Building odds features for seasons: {seasons or 'all'}")
        
        try:
            # FIX: Use DataFrameEngine for multi-season support (like warehouse does)
            # This handles partitioned play_by_play data correctly
            from commonv2.persistence.bucket_adapter import get_bucket_adapter
            from ...data_pipeline.transformations import create_dataframe_engine
            
            bucket = self.bucket_adapter or get_bucket_adapter(logger=self.logger)
            
            # Log season loading intent
            if seasons:
                season_list = list(seasons) if isinstance(seasons, (list, tuple)) else [seasons]
                self.logger.info(f"   Loading data for seasons: {season_list}")
            else:
                self.logger.info(f"   Loading data for all available seasons")
            
            # Load play_by_play using DataFrameEngine (supports multi-partition loading)
            columns = [
                'game_id', 'season', 'week',
                'spread_line', 'total_line',
                'vegas_wp', 'vegas_home_wp',      # Vegas-adjusted WP (99%+ coverage)
                'vegas_wpa', 'vegas_home_wpa'     # Vegas-adjusted WPA (98%+ coverage)
            ]
            engine = create_dataframe_engine(
                table_name='play_by_play',
                schema='raw_nflfastr',
                seasons=seasons,  # None = all seasons, list = specific seasons
                columns=columns,  # Column pruning for memory efficiency
                max_memory_mb=1536,  # Conservative for S2 instance
                bucket_adapter=bucket,
                logger=self.logger
            )
            
            # Extract DataFrame from engine
            pbp = engine.df
            self.logger.info(f"✓ Loaded {len(pbp):,} plays from play_by_play")
            
            # Transform at play level (NO aggregation)
            self.logger.info("📊 Transforming odds at play-by-play level...")
            odds_features = self._transform_play_level_odds(pbp)
            
            self.logger.info(f"✓ Built odds features for {len(odds_features):,} plays")
            
            return {
                'status': 'success',
                'dataframe': odds_features,
                'features_built': len(odds_features),
                'seasons_processed': odds_features['season'].nunique()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build odds features: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0
            }
    
    def _transform_play_level_odds(self, pbp: pd.DataFrame) -> pd.DataFrame:
        """
        Transform play-level odds columns (already in nflfastR).
        
        nflfastR stores spread_line and total_line on EVERY play in a game.
        We simply transform these columns and add implied probability calculation.
        NO aggregation - maintains play-by-play granularity.
        
        Args:
            pbp: Play-by-play DataFrame
            
        Returns:
            Play-level DataFrame with odds features (same row count as input)
        """
        # Create odds features DataFrame (same length as input)
        odds_features = pd.DataFrame({
            'game_id': pbp['game_id'],
            'season': pbp['season'],
            'week': pbp['week'],
            'consensus_spread': pbp['spread_line'],
            'consensus_total': pbp['total_line'],
            'vegas_wp': pbp['vegas_wp'],                  # Vegas-calibrated WP (offense)
            'vegas_home_wp': pbp['vegas_home_wp'],        # Vegas-calibrated home WP
            'vegas_wpa': pbp['vegas_wpa'],                # Play-level leverage (offense)
            'vegas_home_wpa': pbp['vegas_home_wpa']       # Play-level leverage (home)
        })
        
        # Convert spread to implied home win probability for EACH play
        odds_features['consensus_home_prob'] = pbp['spread_line'].apply(
            self._spread_to_prob
        )
        
        # Log coverage at PLAY level for all odds features
        total = len(odds_features)
        self.logger.info(f"  Coverage statistics:")
        self.logger.info(f"    consensus_spread: {odds_features['consensus_spread'].notna().sum():,}/{total:,} ({odds_features['consensus_spread'].notna().mean():.1%})")
        self.logger.info(f"    consensus_total: {odds_features['consensus_total'].notna().sum():,}/{total:,} ({odds_features['consensus_total'].notna().mean():.1%})")
        self.logger.info(f"    vegas_home_wp: {odds_features['vegas_home_wp'].notna().sum():,}/{total:,} ({odds_features['vegas_home_wp'].notna().mean():.1%})")
        self.logger.info(f"    vegas_wp: {odds_features['vegas_wp'].notna().sum():,}/{total:,} ({odds_features['vegas_wp'].notna().mean():.1%})")
        self.logger.info(f"    vegas_home_wpa: {odds_features['vegas_home_wpa'].notna().sum():,}/{total:,} ({odds_features['vegas_home_wpa'].notna().mean():.1%})")
        self.logger.info(f"    vegas_wpa: {odds_features['vegas_wpa'].notna().sum():,}/{total:,} ({odds_features['vegas_wpa'].notna().mean():.1%})")
        
        return odds_features
    
    @staticmethod
    def _spread_to_prob(spread: float) -> float:
        """
        Convert point spread to implied home win probability.
        
        Uses standard market efficiency formula based on empirical NFL data.
        
        Formula: P(home wins) = 0.5 - (spread / 25.0)
        
        Rationale:
        - Negative spread (home favored): Higher probability
        - Positive spread (away favored): Lower probability
        - Zero spread (pick'em): 50/50
        - Rule of thumb: Each 2.5 point spread ≈ 10% probability shift
        
        Args:
            spread: Point spread (negative = home favored, positive = away favored)
            
        Returns:
            float: Implied home win probability (0-1)
            
        Examples:
            >>> _spread_to_prob(-7.0)   # Home favored by 7
            0.78
            >>> _spread_to_prob(0.0)    # Pick'em
            0.50
            >>> _spread_to_prob(+3.0)   # Away favored by 3
            0.38
        """
        if pd.isna(spread):
            return np.nan
        
        # Spread to probability conversion
        # -7 spread → 0.5 - (-7 / 25) = 0.5 + 0.28 = 0.78 (78% home win prob)
        # +3 spread → 0.5 - (+3 / 25) = 0.5 - 0.12 = 0.38 (38% home win prob)
        prob = 0.5 - (spread / 25.0)
        
        # Clamp to [0, 1] range
        return max(0.0, min(1.0, prob))


def create_odds_features(db_service=None, logger=None, bucket_adapter=None):
    """
    Factory function to create odds features builder.
    
    Matches pattern from:
    - create_rolling_metrics_features()
    - create_injury_features()
    - create_contextual_features()
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        OddsFeatures: Configured builder
    """
    from ....shared.database_router import get_database_router
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline.odds_features')
    
    return OddsFeatures(db_service, logger, bucket_adapter)


__all__ = ['OddsFeatures', 'create_odds_features']
