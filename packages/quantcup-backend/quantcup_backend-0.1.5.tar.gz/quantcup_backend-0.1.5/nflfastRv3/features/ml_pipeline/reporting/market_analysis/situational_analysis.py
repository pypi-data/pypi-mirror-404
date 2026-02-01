"""
Situational Analysis - CLV performance by game context

Extracts situational analysis from MarketComparisonAnalyzer to create
a focused, testable module for context-specific CLV insights.

Pattern: Single Responsibility - Situational segmentation only
Layer: 2 (Implementation - calls infrastructure directly)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from logging import Logger  # Type hint only


class SituationalAnalyzer:
    """
    Segments CLV performance by game situation.
    
    **Purpose**: Identify profitable niches where model excels
    (e.g., "Model excels on rested favorites in domes")
   
    **Key Segmentations**:
    - By spread (favorites vs underdogs)
    - By total (high-scoring vs low-scoring)
    - By season phase (early vs late season)
    - By contextual features (division games, weather, etc.)
    
    **Refactoring Note**: Extracted from MarketComparisonAnalyzer (lines 710-803)
    to improve modularity and testability.
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize situational analyzer.
        
        Args:
            logger: Optional logger instance for diagnostic output
        """
        self.logger = logger
    
    def analyze_situational_clv(
        self,
        clv_df: pd.DataFrame,
        contextual_features: Optional[pd.DataFrame] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Segment CLV performance by game situation.
        
        Identifies profitable niches (e.g., "Model excels on rested favorites in domes").
        
        **Built-in Segmentations**:
        1. **By Spread**: Big Favorite, Favorite, Pick'em, Underdog, Big Underdog
        2. **By Total**: Low Scoring (<42), Mid Scoring (42-48), High Scoring (>48)
        3. **By Season Phase**: Early (weeks 1-6), Mid (7-12), Late (13+)
        
        **Optional Contextual Segmentations** (if contextual_features provided):
        4. **By Division**: Division vs Non-Division games
        5. **By Weather**: (if is_dome, weather_type columns available)
        6. **By Rest**: (if rest_days column available)
        
        Args:
            clv_df: DataFrame from calculate_clv()
            contextual_features: Optional DataFrame with situational columns
                (rest_days, weather, is_dome, is_division, etc.)
            
        Returns:
            Dict of DataFrames, each named by dimension and showing:
                - situation: Category label
                - n_games: Game count
                - avg_clv: Mean absolute CLV
                - edge_hit_rate%: Percentage with 2%+ CLV
        """
        situations = {}
        
        # Spread buckets (from consensus_spread if available)
        if 'consensus_spread' in clv_df.columns:
            df = clv_df.copy()
            df['spread_bucket'] = pd.cut(
                df['consensus_spread'],
                bins=[-np.inf, -7, -3, 3, 7, np.inf],
                labels=['Big Favorite', 'Favorite', 'Pickem', 'Underdog', 'Big Underdog']
            )
            
            spread_analysis = df.groupby('spread_bucket', observed=True).agg({
                'abs_clv': 'mean',
                'has_edge': lambda x: (x.sum() / len(x) * 100),
                'game_id': 'count'
            }).round(3)
            spread_analysis.columns = ['avg_clv', 'edge_hit_rate%', 'n_games']
            situations['by_spread'] =spread_analysis.reset_index()
        
        # Total buckets (from consensus_total if available)
        if 'consensus_total' in clv_df.columns:
            df = clv_df.copy()
            df['total_bucket'] = pd.cut(
                df['consensus_total'],
                bins=[0, 42, 48, 100],
                labels=['Low Scoring', 'Mid Scoring', 'High Scoring']
            )
            
            total_analysis = df.groupby('total_bucket', observed=True).agg({
                'abs_clv': 'mean',
                'has_edge': lambda x: (x.sum() / len(x) * 100),
                'game_id': 'count'
            }).round(3)
            total_analysis.columns = ['avg_clv', 'edge_hit_rate%', 'n_games']
            situations['by_total'] = total_analysis.reset_index()
        
        # Week analysis (early season vs. late season)
        if 'week' in clv_df.columns:
            df = clv_df.copy()
            df['season_phase'] = pd.cut(
                df['week'],
                bins=[0, 6, 12, 20],
                labels=['Early (Weeks 1-6)', 'Mid (Weeks 7-12)', 'Late (Weeks 13+)']
            )
            
            week_analysis = df.groupby('season_phase', observed=True).agg({
                'abs_clv': 'mean',
                'has_edge': lambda x: (x.sum() / len(x) * 100),
                'game_id': 'count'
            }).round(3)
            week_analysis.columns = ['avg_clv', 'edge_hit_rate%', 'n_games']
            situations['by_season_phase'] = week_analysis.reset_index()
        
        # Contextual features (if provided)
        if contextual_features is not None:
            merged = clv_df.merge(contextual_features, on='game_id', how='left')
            
            # Division game analysis
            if 'is_division' in merged.columns:
                div_analysis = merged.groupby('is_division').agg({
                    'abs_clv': 'mean',
                    'has_edge': lambda x: (x.sum() / len(x) * 100),
                    'game_id': 'count'
                }).round(3)
                div_analysis.columns = ['avg_clv', 'edge_hit_rate%', 'n_games']
                situations['by_division'] = div_analysis.reset_index()
                situations['by_division']['is_division'] = situations['by_division']['is_division'].map({True: 'Division', False: 'Non-Division'})
        
        if self.logger:
            self.logger.info(f"Situational CLV analysis: {len(situations)} dimensions analyzed")
        
        return situations


__all__ = ['SituationalAnalyzer']
