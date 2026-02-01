"""
Temporal Validator - Prevent temporal leakage in training.

Shared utility for models that need walk-forward validation.
"""

from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional, Any
import pandas as pd


class TemporalValidator:
    """Validates temporal aspects of training to prevent leakage."""
    
    @staticmethod
    def get_completed_weeks(season: int, db_service, logger, bucket_adapter=None) -> List[int]:
        """
        Get list of completed weeks in a season.
        
        A week is "completed" if:
        1. All games in that week have final scores
        2. The week's last game was >24 hours ago (settled)
        
        Args:
            season: Season year
            db_service: Database service for querying games
            logger: Logger instance
            bucket_adapter: Optional BucketAdapter instance (uses DI with fallback pattern)
            
        Returns:
            List of completed week numbers
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        try:
            # DI with fallback pattern
            bucket_adapter = bucket_adapter or get_bucket_adapter(logger=logger)
            
            # Load games for this season
            games = bucket_adapter.read_data(
                'dim_game',
                'warehouse',
                filters=[('season', '==', season)]
            )
            
            if games.empty:
                logger.warning(f"No games found for season {season}")
                return []
            
            # Convert game_date to datetime
            games['game_date'] = pd.to_datetime(games['game_date'])
            
            # Get current time
            now = datetime.now()
            cutoff = now - timedelta(hours=24)  # Games must be >24h old
            
            # Find completed weeks
            completed_weeks = []
            for week in sorted(games['week'].unique()):
                week_games = games[games['week'] == week]
                
                # Check if all games have scores
                has_scores = (
                    week_games['home_score'].notna().all() and
                    week_games['away_score'].notna().all()
                )
                
                # Check if all games are >24h old
                all_settled = (week_games['game_date'] < cutoff).all()
                
                if has_scores and all_settled:
                    completed_weeks.append(week)
            
            logger.info(f"✓ Season {season}: {len(completed_weeks)} completed weeks: {completed_weeks}")
            return completed_weeks
            
        except Exception as e:
            logger.error(f"Failed to get completed weeks: {e}")
            return []
    
    @staticmethod
    def validate_test_week(test_season: int, test_week: int, db_service, logger, bucket_adapter=None) -> Tuple[bool, str]:
        """
        Validate that test week hasn't occurred yet (prevent leakage).
        
        DEPRECATED: This method has inverted logic for backtesting scenarios.
        Use get_completed_weeks() directly and check if week is in the list:
        - If week IS in completed_weeks: Safe for backtesting (historical validation)
        - If week NOT in completed_weeks: Unsafe for live prediction (temporal leakage)
        
        Args:
            test_season: Season to test
            test_week: Week to test
            db_service: Database service
            logger: Logger instance
            bucket_adapter: Optional BucketAdapter instance (uses DI with fallback pattern)
            
        Returns:
            Tuple of (is_safe, warning_message)
            Note: Returns False when week is completed (backwards for backtesting)
        """
        completed_weeks = TemporalValidator.get_completed_weeks(test_season, db_service, logger, bucket_adapter)
        
        if test_week in completed_weeks:
            # Week is completed - this is actually SAFE for backtesting
            # but this method returns False (legacy behavior)
            warning = (
                f"⚠️ Week {test_week} of {test_season} is already complete.\n"
                f"   This is safe for backtesting but unsafe for live prediction.\n"
                f"   Completed weeks: {completed_weeks}\n"
                f"   Incomplete weeks: {[w for w in range(1, 23) if w not in completed_weeks][:5]}"
            )
            return False, warning
        
        # Week not completed - safe for this method's original purpose
        return True, ""
    
    @staticmethod
    def build_walk_forward_config(train_seasons: str, test_season: int, test_week: int,
                                   db_service, logger, bucket_adapter=None) -> Dict[str, Any]:
        """
        Build walk-forward training configuration.
        
        Automatically includes completed weeks from test season in training.
        
        Args:
            train_seasons: Base training seasons (e.g., "2000-2022")
            test_season: Season to test
            test_week: Week to test
            db_service: Database service
            logger: Logger instance
            bucket_adapter: Optional BucketAdapter instance (uses DI with fallback pattern)
            
        Returns:
            Dict with train_seasons, train_weeks, and metadata
        """
        # Get completed weeks in test season
        completed_weeks = TemporalValidator.get_completed_weeks(test_season, db_service, logger, bucket_adapter)
        
        # Filter to weeks before test week
        prior_weeks = [w for w in completed_weeks if w < test_week]
        
        if not prior_weeks:
            # No completed weeks before test week - use base training only
            logger.info(f"✓ Walk-forward: No completed weeks before Week {test_week}")
            return {
                'train_seasons': train_seasons,
                'train_weeks': None,
                'added_weeks': [],
                'added_games': 0
            }
        
        # Build walk-forward configuration
        logger.info(f"✓ Walk-forward: Including {len(prior_weeks)} completed weeks from {test_season}")
        logger.info(f"   Weeks: {prior_weeks}")
        
        # Combine base seasons with test season
        combined_seasons = f"{train_seasons},{test_season}"
        train_weeks = {test_season: prior_weeks}
        
        # Estimate added games (approximate)
        estimated_games = len(prior_weeks) * 16
        
        return {
            'train_seasons': combined_seasons,
            'train_weeks': train_weeks,
            'added_weeks': prior_weeks,
            'added_games': estimated_games
        }