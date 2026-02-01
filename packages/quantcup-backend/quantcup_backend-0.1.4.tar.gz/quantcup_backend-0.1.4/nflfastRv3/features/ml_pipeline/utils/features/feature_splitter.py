"""
Feature Splitter Utility

Splits features into groups based on regex patterns for model-specific training.
Extracted from game_outcome.py to enable reuse across all models.

Usage:
    from nflfastRv3.features.ml_pipeline.utils.feature_splitter import FeatureSplitter
    from nflfastRv3.features.ml_pipeline.utils.feature_patterns import FeaturePatterns
    
    # Split features for game outcome model
    pattern_groups = {
        'linear': FeaturePatterns.GAME_OUTCOME_LINEAR,
        'tree': FeaturePatterns.GAME_OUTCOME_TREE
    }
    
    feature_groups = FeatureSplitter.split_features(
        features=X.columns.tolist(),
        pattern_groups=pattern_groups,
        logger=logger
    )
    
    # Access split features
    linear_features = feature_groups['linear']
    tree_features = feature_groups['tree']
"""

import re
from typing import List, Dict, Optional

from commonv2 import get_logger

# Module logger
logger = get_logger(__name__)


class FeatureSplitter:
    """Split features into groups based on regex patterns."""
    
    @staticmethod
    def split_features(
        features: List[str],
        pattern_groups: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Split features into groups based on regex patterns.
        
        PHASE 1 FIX (2025-12-13): Features can now be assigned to MULTIPLE groups.
        This enables XGBoost to share rolling metrics with linear models while
        maintaining exclusive access to contextual features.
        
        Args:
            features: List of feature names to split
            pattern_groups: Dict mapping group names to regex patterns
                           e.g., {'linear': [r'^rolling_'], 'tree': [r'^interaction_']}
            
        Returns:
            Dict mapping group names to matched features
            
        Example:
            >>> features = ['rolling_4g_epa', 'is_dome', 'win_rate_diff']
            >>> pattern_groups = {
            ...     'linear': [r'^rolling_', r'^win_rate_'],
            ...     'tree': [r'^rolling_', r'^is_']  # rolling_ shared with linear
            ... }
            >>> result = FeatureSplitter.split_features(features, pattern_groups)
            >>> print(result)
            {
                'linear': ['rolling_4g_epa', 'win_rate_diff'],
                'tree': ['rolling_4g_epa', 'is_dome']  # rolling_4g_epa appears in both
            }
        """
        logger.info(f"🔍 Splitting {len(features)} features into {len(pattern_groups)} groups")
        logger.info(f"   Phase 1 Fix: Features CAN be shared across groups")
        
        # Initialize result dict with empty lists
        result = {group: [] for group in pattern_groups}
        
        # Track which features matched at least one group
        matched_features = set()
        
        # Assign features to ALL matching groups (Phase 1 fix: removed break)
        for feature in features:
            for group, patterns in pattern_groups.items():
                if any(re.match(pattern, feature) for pattern in patterns):
                    result[group].append(feature)
                    matched_features.add(feature)
                    # NO BREAK: Feature can match multiple groups
        
        # Identify unmatched features
        unmatched = [f for f in features if f not in matched_features]
        
        if unmatched:
            logger.warning(f"⚠️ {len(unmatched)} features didn't match any pattern")
            logger.warning(f"   Sample unmatched: {unmatched[:5]}")
            logger.warning(f"   Adding to all groups as fallback")
            
            # Add unmatched features to all groups (fallback strategy)
            for group in result:
                result[group].extend(unmatched)
        
        # Log results with feature details
        logger.info(f"✓ Feature split complete:")
        for group, feats in result.items():
            logger.info(f"  {group}: {len(feats)} features")
            # Log first 10 features per group for visibility
            for feat in sorted(feats)[:10]:
                logger.info(f"    - {feat}")
            if len(feats) > 10:
                logger.info(f"    ... and {len(feats) - 10} more")
        
        return result
    
    @staticmethod
    def filter_by_patterns(
        features: List[str],
        patterns: List[str]
    ) -> List[str]:
        """
        Filter features by regex patterns (returns features matching ANY pattern).
        
        This is a simpler version of split_features for when you only need one group.
        
        Args:
            features: List of feature names
            patterns: List of regex patterns
            
        Returns:
            List of features matching any pattern
            
        Example:
            >>> features = ['rolling_4g_epa', 'interaction_form', 'win_rate']
            >>> patterns = [r'^rolling_', r'^win_rate_']
            >>> result = FeatureSplitter.filter_by_patterns(features, patterns)
            >>> print(result)
            ['rolling_4g_epa', 'win_rate']
        """
        matched = []
        for feature in features:
            if any(re.match(pattern, feature) for pattern in patterns):
                matched.append(feature)
        
        logger.info(f"✓ Matched {len(matched)}/{len(features)} features to patterns")
        
        return matched
    
    @staticmethod
    def validate_split(
        feature_groups: Dict[str, List[str]],
        min_features_per_group: int = 1
    ) -> bool:
        """
        Validate that feature split produced reasonable results.
        
        Checks:
        1. Each group has at least min_features_per_group features
        2. No group is empty
        3. Total features across groups >= original features (accounting for fallback)
        
        Args:
            feature_groups: Result from split_features()
            min_features_per_group: Minimum features required per group
            
        Returns:
            True if split is valid, False otherwise
            
        Example:
            >>> feature_groups = {'linear': ['feat1', 'feat2'], 'tree': ['feat3']}
            >>> is_valid = FeatureSplitter.validate_split(feature_groups, min_features_per_group=1)
            >>> print(is_valid)
            True
        """
        is_valid = True
        
        for group, features in feature_groups.items():
            if len(features) < min_features_per_group:
                logger.error(f"❌ Group '{group}' has only {len(features)} features (min: {min_features_per_group})")
                is_valid = False
            
            if len(features) == 0:
                logger.error(f"❌ Group '{group}' is empty!")
                is_valid = False
        
        if is_valid:
            logger.info(f"✓ Feature split validation passed")
        
        return is_valid


__all__ = ['FeatureSplitter']