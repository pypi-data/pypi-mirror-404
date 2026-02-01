"""
Training Preview

Generates dry-run previews for training operations.
Shows what will happen without actually executing training.

Pattern: Static utility class
Complexity: 2 points (database query + calculation)
"""

from typing import Dict, Any, Optional
import pandas as pd

from commonv2 import get_logger


class TrainingPreview:
    """
    Generate training preview for dry-run mode.
    
    Provides users with information about what training will do:
    - Number of training/test games
    - Estimated time and memory
    - Configuration summary
    
    Helps users validate configuration before expensive training.
    """
    
    @staticmethod
    def preview_training(
        model_name: str,
        train_seasons: str,
        test_seasons: Optional[str],
        test_week: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate training preview.
        
        Args:
            model_name: Name of the model to train
            train_seasons: Training seasons (e.g., '2021-2023')
            test_seasons: Test seasons (e.g., '2024'), or None for auto-split
            test_week: Optional specific week to test
            
        Returns:
            Dict with preview information
            
        Example:
            >>> preview = TrainingPreview.preview_training(
            ...     'game_outcome',
            ...     '2021-2023',
            ...     '2024',
            ...     test_week=9
            ... )
            >>> print(f"Training games: {preview['train_games']}")
        """
        logger = get_logger('nflfastRv3.training_preview')
        
        try:
            from commonv2.persistence.bucket_adapter import get_bucket_adapter
            
            bucket_adapter = get_bucket_adapter(logger=logger)
            
            # Parse seasons
            train_start, train_end = TrainingPreview._parse_season_range(train_seasons)
            
            # Handle auto-split if test_seasons is None
            if test_seasons is None:
                # Auto-split: use last training year as test
                test_season = train_end
                train_end = train_end - 1  # Exclude last year from training
                if train_start > train_end:
                    raise ValueError("Cannot auto-split: need at least 2 years of data")
            else:
                test_season = int(test_seasons.split('-')[0])  # Get first year if range
            
            # Read dim_game from bucket (warehouse tables are bucket-only now)
            dim_game = bucket_adapter.read_data(
                table_name='dim_game',
                schema='warehouse'
            )
            
            if dim_game.empty:
                raise ValueError("No game data found in warehouse.dim_game")
            
            # Count training games
            train_games_df = dim_game[
                (dim_game['season'] >= train_start) &
                (dim_game['season'] <= train_end) &
                (dim_game['home_score'].notna()) &
                (dim_game['away_score'].notna())
            ]
            train_games = len(train_games_df)
            
            # Count test games
            if test_week:
                test_games_df = dim_game[
                    (dim_game['season'] == test_season) &
                    (dim_game['week'] == test_week) &
                    (dim_game['home_score'].notna()) &
                    (dim_game['away_score'].notna())
                ]
            else:
                test_games_df = dim_game[
                    (dim_game['season'] == test_season) &
                    (dim_game['home_score'].notna()) &
                    (dim_game['away_score'].notna())
                ]
            
            test_games = len(test_games_df)
            
            # Estimate resources
            # Based on empirical observations: ~0.5 seconds per game + 2 min overhead
            estimated_time_seconds = train_games * 0.5 + 120
            
            # Based on empirical observations: ~3 MB per game
            estimated_memory_mb = train_games * 3
            
            preview = {
                'model': model_name,
                'train_seasons': train_seasons,
                'test_seasons': test_seasons,
                'test_week': test_week,
                'train_games': train_games,
                'test_games': test_games,
                'estimated_time_seconds': int(estimated_time_seconds),
                'estimated_memory_mb': int(estimated_memory_mb),
                'estimated_time_minutes': int(estimated_time_seconds // 60),
                'estimated_memory_gb': round(estimated_memory_mb / 1024, 1)
            }
            
            logger.info(f"Preview generated: {train_games} train games, {test_games} test games")
            
            return preview
            
        except Exception as e:
            logger.error(f"Failed to generate training preview: {e}", exc_info=True)
            # Return minimal preview on error
            return {
                'model': model_name,
                'train_seasons': train_seasons,
                'test_seasons': test_seasons,
                'test_week': test_week,
                'train_games': 0,
                'test_games': 0,
                'estimated_time_seconds': 0,
                'estimated_memory_mb': 0,
                'error': str(e)
            }
    
    @staticmethod
    def display_preview(preview: Dict[str, Any], logger) -> None:
        """
        Display training preview in user-friendly format.
        
        Args:
            preview: Preview dictionary from preview_training()
            logger: Logger instance
            
        Example:
            >>> preview = TrainingPreview.preview_training(...)
            >>> TrainingPreview.display_preview(preview, logger)
        """
        logger.info("🔍 DRY RUN - No training will occur\n")
        
        if 'error' in preview:
            logger.error(f"❌ Preview generation failed: {preview['error']}")
            return
        
        logger.info("Configuration:")
        logger.info(f"  Model: {preview['model']}")
        logger.info(f"  Training: {preview['train_seasons']} ({preview['train_games']:,} games)")
        
        test_scope = f"Week {preview['test_week']}" if preview['test_week'] else "Full season"
        logger.info(f"  Testing: {preview['test_seasons']} {test_scope} ({preview['test_games']:,} games)")
        
        logger.info(f"\nEstimated Resources:")
        logger.info(f"  Time: ~{preview.get('estimated_time_minutes', 0)} minutes")
        logger.info(f"  Memory: ~{preview.get('estimated_memory_gb', 0)} GB")
        
        logger.info(f"\nTo execute: Remove --dry-run flag")
    
    @staticmethod
    def _parse_season_range(seasons: str) -> tuple:
        """
        Parse season range to start and end years.
        
        Args:
            seasons: Season string (e.g., '2020-2023' or '2020,2021,2022')
            
        Returns:
            Tuple of (start_year, end_year)
            
        Example:
            >>> start, end = TrainingPreview._parse_season_range('2020-2023')
            >>> print(start, end)  # 2020 2023
        """
        if '-' in seasons:
            # Range format: '2020-2023'
            start, end = seasons.split('-')
            return int(start), int(end)
        else:
            # Comma-separated format: '2020,2021,2022'
            season_list = [int(s.strip()) for s in seasons.split(',')]
            return min(season_list), max(season_list)


__all__ = ['TrainingPreview']