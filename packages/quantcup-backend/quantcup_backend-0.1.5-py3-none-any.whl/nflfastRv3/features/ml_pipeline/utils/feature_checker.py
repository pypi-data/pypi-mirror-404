"""
Feature Availability Checker

Checks feature availability and auto-builds missing features.
Integrates with GameFeatureBuilder for seamless feature management.

Pattern: Static utility class
Complexity: 2 points (bucket check + builder integration)
"""

from typing import List, Dict, Any

from commonv2 import get_logger
from nflfastRv3.features.ml_pipeline.feature_sets import FEATURE_REGISTRY


class FeatureAvailabilityChecker:
    """
    Check and auto-build missing features.
    
    Provides automatic feature building integration to ensure
    all required features are available before training.
    
    Prevents training failures due to missing features.
    """
    
    @staticmethod
    def check_features(seasons: str, feature_sets: List[str]) -> Dict[str, Any]:
        """
        Check which features are available for given seasons.
        
        Args:
            seasons: Season string (e.g., '2020-2023' or '2020,2021,2022')
            feature_sets: List of feature set names
                         (e.g., ['rolling_metrics', 'team_efficiency', 'opponent_adjusted'])
        
        Returns:
            Dict with 'available', 'missing', and 'coverage' keys
            
        Example:
            >>> status = FeatureAvailabilityChecker.check_features(
            ...     '2020-2023',
            ...     ['rolling_metrics', 'team_efficiency']
            ... )
            >>> print(f"Coverage: {status['coverage']:.1%}")
            >>> print(f"Missing: {status['missing']}")
        """
        logger = get_logger('nflfastRv3.feature_checker')
        
        try:
            from nflfastRv3.features.ml_pipeline.builders.game_feature_builder import RealFeatureBuilder
            from commonv2.persistence.bucket_adapter import get_bucket_adapter
            
            bucket_adapter = get_bucket_adapter(logger=logger)
            
            # Parse seasons
            season_list = FeatureAvailabilityChecker._parse_seasons(seasons)
            
            available = []
            missing = []
            
            # ✅ Build feature mapping from centralized FEATURE_REGISTRY
            # Single source of truth - automatically includes all registered features
            feature_table_map = {
                name: info['table']
                for name, info in FEATURE_REGISTRY.items()
            }
            
            logger.info(f"Checking feature availability for {seasons} ({len(season_list)} seasons)")
            
            for feature_set in feature_sets:
                table_name = feature_table_map.get(feature_set)
                
                if not table_name:
                    logger.warning(f"Unknown feature set: {feature_set}")
                    missing.append(feature_set)
                    continue
                
                # Check if features exist in bucket
                try:
                    data = bucket_adapter.read_data(
                        table_name=table_name,
                        schema='features',
                        filters=[('season', 'in', season_list)],
                        columns=['season']  # Only load season column for existence check
                    )
                    
                    if not data.empty:
                        available.append(feature_set)
                        logger.info(f"  ✓ {feature_set}: available ({len(data)} rows)")
                    else:
                        missing.append(feature_set)
                        logger.info(f"  ✗ {feature_set}: missing")
                        
                except Exception as e:
                    logger.warning(f"  ✗ {feature_set}: error checking ({e})")
                    missing.append(feature_set)
            
            coverage = len(available) / len(feature_sets) if feature_sets else 1.0
            
            return {
                'available': available,
                'missing': missing,
                'coverage': coverage,
                'seasons': seasons,
                'season_list': season_list
            }
            
        except Exception as e:
            logger.error(f"Failed to check feature availability: {e}", exc_info=True)
            return {
                'available': [],
                'missing': feature_sets,
                'coverage': 0.0,
                'seasons': seasons,
                'season_list': []
            }
    
    @staticmethod
    def auto_build_features(seasons: str, feature_sets: List[str], logger) -> bool:
        """
        Automatically build missing features.
        
        Args:
            seasons: Season string (e.g., '2020-2023')
            feature_sets: List of feature set names to build
            logger: Logger instance
            
        Returns:
            bool: True if successful, False otherwise
            
        Example:
            >>> success = FeatureAvailabilityChecker.auto_build_features(
            ...     '2020-2023',
            ...     ['rolling_metrics', 'team_efficiency'],
            ...     logger
            ... )
        """
        try:
            # Check current status
            status = FeatureAvailabilityChecker.check_features(seasons, feature_sets)
            
            if not status['missing']:
                logger.info("✅ All required features available")
                return True
            
            logger.warning(
                f"⚠️  Missing features: {', '.join(status['missing'])}\n"
                f"   Building features automatically..."
            )
            
            # Build missing features
            from nflfastRv3.features.ml_pipeline.orchestrators.feature_orchestrator import create_feature_engineer
            from nflfastRv3.shared.database_router import get_database_router
            
            db_service = get_database_router()
            feature_engineer = create_feature_engineer(db_service, logger)
            
            # Parse seasons for feature builder
            season_list = status['season_list']
            
            for feature_set in status['missing']:
                logger.info(f"   Building {feature_set} for seasons {seasons}...")
                
                try:
                    # Build features for this set
                    result = feature_engineer.build_features(
                        feature_sets=[feature_set],
                        seasons=season_list
                    )
                    
                    if result.get('status') == 'success':
                        logger.info(f"   ✓ {feature_set} built successfully")
                    else:
                        logger.error(f"   ✗ {feature_set} build failed: {result.get('message')}")
                        return False
                        
                except Exception as e:
                    logger.error(f"   ✗ {feature_set} build failed: {e}")
                    return False
            
            logger.info("✅ Feature building complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to auto-build features: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _parse_seasons(seasons: str) -> List[int]:
        """
        Parse season string to list of integers.
        
        Args:
            seasons: Season string (e.g., '2020-2023' or '2020,2021,2022')
            
        Returns:
            List of season integers
            
        Example:
            >>> seasons = FeatureAvailabilityChecker._parse_seasons('2020-2023')
            >>> print(seasons)  # [2020, 2021, 2022, 2023]
        """
        if '-' in seasons:
            # Range format: '2020-2023'
            start, end = seasons.split('-')
            return list(range(int(start), int(end) + 1))
        else:
            # Comma-separated format: '2020,2021,2022'
            return [int(s.strip()) for s in seasons.split(',')]


__all__ = ['FeatureAvailabilityChecker']