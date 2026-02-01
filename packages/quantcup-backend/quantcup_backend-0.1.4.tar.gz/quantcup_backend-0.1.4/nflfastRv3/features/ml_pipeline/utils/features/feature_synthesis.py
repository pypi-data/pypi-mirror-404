"""
Feature Synthesis Utilities

Generic utilities for creating differential and interaction features.
Extracted from game_outcome.py to enable reuse across player prop models.

Usage:
    from nflfastRv3.features.ml_pipeline.utils.feature_synthesis import FeatureSynthesis
    
    # Create differential features (home - away)
    df = FeatureSynthesis.create_differential_features(
        df, base_features=['epa_offense', 'epa_defense'],
        prefix_a='home', prefix_b='away'
    )
    
    # Create interaction features (A × B)
    df = FeatureSynthesis.create_interaction_features(
        df, interactions=[
            ('recent_4g_epa_trend_diff', 'stadium_home_win_rate', 'interaction_form_home')
        ]
    )
"""

import pandas as pd
from typing import List, Optional, Tuple

from commonv2 import get_logger

# Module logger
logger = get_logger(__name__)


class FeatureSynthesis:
    """Generic feature synthesis utilities for ML models."""
    
    @staticmethod
    def create_differential_features(
        df: pd.DataFrame,
        base_features: List[str],
        prefix_a: str = 'home',
        prefix_b: str = 'away',
        suffix: str = '_diff'
    ) -> pd.DataFrame:
        """
        Create differential features (A - B) for all base features.
        
        This is the core pattern for binary prediction models where you want to
        compare two entities (e.g., home vs away, player vs opponent).
        
        Args:
            df: DataFrame with prefixed features
            base_features: List of base feature names (without prefix)
                          e.g., ['epa_offense', 'epa_defense', 'point_diff']
            prefix_a: Prefix for first group (e.g., 'home', 'player')
            prefix_b: Prefix for second group (e.g., 'away', 'opponent')
            suffix: Suffix for differential features (default: '_diff')
            
        Returns:
            DataFrame with differential features added
            
        Example:
            >>> df = pd.DataFrame({
            ...     'home_epa_offense': [0.2, 0.3],
            ...     'away_epa_offense': [0.1, 0.4]
            ... })
            >>> result = FeatureSynthesis.create_differential_features(
            ...     df, ['epa_offense'], prefix_a='home', prefix_b='away'
            ... )
            >>> 'epa_offense_diff' in result.columns
            True
            >>> result['epa_offense_diff'].tolist()
            [0.1, -0.1]
        """
        logger.info(f"🔍 Creating differential features ({prefix_a} - {prefix_b})")
        
        created_count = 0
        for feature in base_features:
            col_a = f'{prefix_a}_{feature}'
            col_b = f'{prefix_b}_{feature}'
            diff_col = f'{feature}{suffix}'
            
            if col_a in df.columns and col_b in df.columns:
                df[diff_col] = df[col_a] - df[col_b]
                created_count += 1
            else:
                logger.debug(f"   Skipping {feature}: Missing {col_a} or {col_b}")
        
        logger.info(f"✓ Created {created_count}/{len(base_features)} differential features")
        
        return df
    
    @staticmethod
    def create_composite_features(
        df: pd.DataFrame,
        composites: List[Tuple[str, str, str, str, str]]
    ) -> pd.DataFrame:
        """
        Create composite features from combinations of existing features.
        
        A composite feature combines multiple features using arithmetic operations.
        For example: EPA Advantage = (Home EPA Off - Home EPA Def) - (Away EPA Off - Away EPA Def)
        
        Args:
            df: DataFrame with source features
            composites: List of (feat_a, feat_b, feat_c, feat_d, output_name) tuples
                       Formula: (feat_a - feat_b) - (feat_c - feat_d)
            
        Returns:
            DataFrame with composite features added
            
        Example:
            >>> df = pd.DataFrame({
            ...     'home_epa_off': [0.2, 0.3],
            ...     'home_epa_def': [0.1, 0.2],
            ...     'away_epa_off': [0.15, 0.25],
            ...     'away_epa_def': [0.12, 0.18]
            ... })
            >>> result = FeatureSynthesis.create_composite_features(
            ...     df, [('home_epa_off', 'home_epa_def', 'away_epa_off', 'away_epa_def', 'epa_advantage')]
            ... )
            >>> 'epa_advantage' in result.columns
            True
        """
        logger.info(f"🔍 Creating {len(composites)} composite features")
        
        created_count = 0
        for feat_a, feat_b, feat_c, feat_d, output_name in composites:
            if all(col in df.columns for col in [feat_a, feat_b, feat_c, feat_d]):
                df[output_name] = (df[feat_a] - df[feat_b]) - (df[feat_c] - df[feat_d])
                created_count += 1
            else:
                missing = [col for col in [feat_a, feat_b, feat_c, feat_d] if col not in df.columns]
                logger.debug(f"   Skipping {output_name}: Missing {missing}")
        
        logger.info(f"✓ Created {created_count}/{len(composites)} composite features")
        
        return df
    
    @staticmethod
    def create_interaction_features(
        df: pd.DataFrame,
        interactions: List[Tuple[str, str, str]]
    ) -> pd.DataFrame:
        """
        Create interaction features (A × B).
        
        Interaction features capture non-linear relationships between features.
        For example: Form × Home Field = Recent EPA Trend × Stadium Win Rate
        
        Args:
            df: DataFrame with source features
            interactions: List of (feature_a, feature_b, output_name) tuples
                         Formula: feature_a * feature_b
            
        Returns:
            DataFrame with interaction features added
            
        Example:
            >>> df = pd.DataFrame({
            ...     'recent_epa_trend': [0.2, -0.1],
            ...     'stadium_win_rate': [0.6, 0.55]
            ... })
            >>> result = FeatureSynthesis.create_interaction_features(
            ...     df, [('recent_epa_trend', 'stadium_win_rate', 'interaction_form_home')]
            ... )
            >>> 'interaction_form_home' in result.columns
            True
            >>> result['interaction_form_home'].tolist()
            [0.12, -0.055]
        """
        logger.info(f"🔍 Creating {len(interactions)} interaction features")
        
        created_count = 0
        for feat_a, feat_b, output_name in interactions:
            if feat_a in df.columns and feat_b in df.columns:
                df[output_name] = df[feat_a] * df[feat_b]
                created_count += 1
            else:
                missing = [col for col in [feat_a, feat_b] if col not in df.columns]
                logger.debug(f"   Skipping {output_name}: Missing {missing}")
        
        logger.info(f"✓ Created {created_count}/{len(interactions)} interaction features")
        
        return df
    
    @staticmethod
    def create_simple_differential(
        df: pd.DataFrame,
        col_a: str,
        col_b: str,
        output_name: str
    ) -> pd.DataFrame:
        """
        Create a single differential feature (A - B).
        
        Convenience method for creating one-off differentials without specifying
        full base_features list.
        
        Args:
            df: DataFrame
            col_a: First column name
            col_b: Second column name
            output_name: Name for differential column
            
        Returns:
            DataFrame with differential feature added
            
        Example:
            >>> df = pd.DataFrame({
            ...     'home_win_rate': [0.6, 0.7],
            ...     'away_win_rate': [0.5, 0.6]
            ... })
            >>> result = FeatureSynthesis.create_simple_differential(
            ...     df, 'home_win_rate', 'away_win_rate', 'win_rate_advantage'
            ... )
            >>> 'win_rate_advantage' in result.columns
            True
            >>> result['win_rate_advantage'].tolist()
            [0.1, 0.1]
        """
        if col_a in df.columns and col_b in df.columns:
            df[output_name] = df[col_a] - df[col_b]
            logger.debug(f"✓ Created {output_name} = {col_a} - {col_b}")
        else:
            missing = [col for col in [col_a, col_b] if col not in df.columns]
            logger.warning(f"⚠️ Cannot create {output_name}: Missing {missing}")
        
        return df


__all__ = ['FeatureSynthesis']