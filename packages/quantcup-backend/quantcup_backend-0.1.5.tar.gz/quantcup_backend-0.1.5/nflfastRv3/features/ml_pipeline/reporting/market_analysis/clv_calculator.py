"""
CLV Calculator - Closing Line Value calculation and analysis

Extracts CLV-focused methods from MarketComparisonAnalyzer to create
a focused, testable module for closing line value calculations.

Pattern: Single Responsibility - CLV calculations only
Layer: 2 (Implementation - calls infrastructure directly)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from logging import Logger  # Type hint only


class CLVCalculator:
    """
    Calculates Closing Line Value (CLV) metrics.
    
    **Purpose**: Measure how model predictions compare to market closing probabilities
    
    **Key Metrics**:
    - CLV = Model Probability - Market Closing Probability
    - Edge buckets (small, medium, large)
    - Persistence analysis (CLV consistency over time/situations)
    
    **Refactoring Note**: Extracted from MarketComparisonAnalyzer (lines 46-636)
    to improve modularity and testability.
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize CLV calculator.
        
        Args:
            logger: Optional logger instance for diagnostic output
        """
        self.logger = logger
    
    def _select_market_prob_column(self, closing_odds_game: pd.DataFrame) -> tuple:
        """
        Select optimal market probability column based on calibration.
        
        Prefers vegas_home_wp (nflfastR calibrated) when available and when
        MAE vs consensus_home_prob exceeds 2% threshold.
        
        **Selection Logic**:
        1. If both columns exist, calculate MAE between them
        2. If MAE > 2%, prefer vegas_home_wp (more accurate)
        3. Otherwise use consensus_home_prob (derived from spread)
        4. Fall back to whichever column is available
        
        Args:
            closing_odds_game: Game-level odds DataFrame
            
        Returns:
            Tuple of (column_name: str, source_label: str, mae: float or None)
            
        Raises:
            ValueError: If no market probability column found
        """
        has_consensus = 'consensus_home_prob' in closing_odds_game.columns
        has_vegas = 'vegas_home_wp' in closing_odds_game.columns
        
        # If both exist, compare calibration
        if has_vegas and has_consensus:
            valid = closing_odds_game[
                closing_odds_game['consensus_home_prob'].notna() &
                closing_odds_game['vegas_home_wp'].notna()
            ]
            
            if len(valid) >= 10:  # Minimum sample size for meaningful MAE
                mae = (valid['consensus_home_prob'] - valid['vegas_home_wp']).abs().mean()
                
                if mae > 0.02:  # 2% threshold (from MarketCalibrator recommendation)
                    if self.logger:
                        self.logger.warning(
                            f"⚠️ consensus_home_prob MAE={mae:.4f} ({mae*100:.2f}%) exceeds 2% threshold"
                        )
                        self.logger.info(f"✓ Switching to vegas_home_wp (nflfastR calibrated baseline)")
                    return 'vegas_home_wp', 'vegas_calibrated', mae
                else:
                    if self.logger:
                        self.logger.info(f"✓ Using consensus_home_prob (MAE={mae:.4f}, {mae*100:.2f}% < 2% threshold)")
                    return 'consensus_home_prob', 'consensus_derived', mae
            else:
                # Insufficient data for MAE comparison, prefer calibrated source
                if self.logger:
                    self.logger.warning(f"⚠️ Only {len(valid)} games with both prob sources, defaulting to vegas_home_wp")
                return 'vegas_home_wp', 'vegas_calibrated', None
        
        # Fallback to whatever is available
        if has_consensus:
            if self.logger:
                self.logger.info("✓ Using consensus_home_prob (vegas_home_wp not available)")
            return 'consensus_home_prob', 'consensus_only', None
        elif has_vegas:
            if self.logger:
                self.logger.info("✓ Using vegas_home_wp (consensus_home_prob not available)")
            return 'vegas_home_wp', 'vegas_only', None
        else:
            error_msg = "No market probability column found (need consensus_home_prob or vegas_home_wp)"
            if self.logger:
                self.logger.error(f"❌ CLV calculation failed: {error_msg}")
            raise ValueError(error_msg)
    
    def calculate_clv(
        self,
        predictions_df: pd.DataFrame,
        closing_odds_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate Closing Line Value (CLV) for all predictions.
        
        CLV = Model Probability - Market Closing Probability
        
        Positive CLV indicates model sees value that market doesn't.
        
        **Design Decision**: Automatically selects optimal market probability source
        based on calibration (prefers vegas_home_wp when MAE > 2%). Also deduplicates
        play-level odds to game-level to handle both odds_features_v1 (play-level)
        and odds_features_game_v1 (game-level).
        
        Args:
            predictions_df: DataFrame with columns:
                - game_id (str)
                - predicted_home_win_prob (float, 0-1)
                - actual_home_win (int, 0 or 1) - optional for training reports
            closing_odds_df: DataFrame from odds_features_v1 OR odds_features_game_v1:
                - game_id (str)
                - consensus_home_prob (float, 0-1) - derived from spread
                - vegas_home_wp (float, 0-1) - nflfastR calibrated baseline (preferred)
                - vegas_wp (float, 0-1) - offense perspective
                - vegas_wpa (float) - play-level leverage
                - vegas_home_wpa (float) - home play-level leverage
                - consensus_spread (float)
                - consensus_total (float)
                
        Returns:
            DataFrame with CLV metrics:
                - game_id
                - predicted_home_win_prob
                - market_consensus_home_prob (selected via calibration)
                - market_prob_source (str): which column was used
                - market_prob_mae (float or None): MAE between sources if both available
                - clv (float): predicted - market
                - abs_clv (float): absolute CLV
                - has_edge (bool): abs_clv > 0.02 (2%+ edge)
                - edge_size (str): 'small', 'medium', 'large'
                - actual_home_win (if available)
                
        Raises:
            ValueError: If predictions_df is not game-level or no market prob column available
        """
        # CRITICAL: Validate predictions_df is game-level
        if not predictions_df['game_id'].is_unique:
            raise ValueError(
                f"predictions_df must be game-level (found {len(predictions_df)} rows, "
                f"{predictions_df['game_id'].nunique()} unique games)"
            )
        
        #  CRITICAL: Deduplicate odds to game level if needed
        if not closing_odds_df['game_id'].is_unique:
            n_rows = len(closing_odds_df)
            n_games = closing_odds_df['game_id'].nunique()
            
            if self.logger:
                self.logger.warning(
                    f"⚠️ Deduplicating play-level odds ({n_rows} rows) to game-level ({n_games} games)"
                )
            
            # Aggregate play-level to game-level (use CLOSING lines - last values)
            agg_dict = {
                'vegas_home_wpa': lambda x: x.abs().max() if x.notna().any() else np.nan  # Max leverage
            }
            
            # Include columns that exist
            for col in ['consensus_home_prob', 'consensus_spread', 'consensus_total', 'vegas_home_wp']:
                if col in closing_odds_df.columns:
                    agg_dict[col] = 'last'  # Closing line (not opening)
            
            closing_odds_game = closing_odds_df.groupby('game_id', as_index=False).agg(agg_dict)
        else:
            closing_odds_game = closing_odds_df
        
        # VALIDATE: Post-deduplication check
        assert closing_odds_game['game_id'].is_unique, "Deduplication failed - duplicate game_ids remain"
        
        # SELECT optimal market probability column based on calibration
        market_col, source_label, mae = self._select_market_prob_column(closing_odds_game)
        
        # Check for NULL values in selected column
        null_count = closing_odds_game[market_col].isna().sum()
        if null_count > 0 and self.logger:
            self.logger.warning(f"⚠️ {null_count}/{len(closing_odds_game)} odds records have NULL {market_col}")
        
        # Merge predictions with closing odds (now guaranteed 1:1)
        merged = predictions_df.merge(
            closing_odds_game[['game_id', market_col]],
            on='game_id',
            how='left'
        )
        
        # VALIDATE: Merge should not create row explosion
        assert len(merged) == len(predictions_df), \
            f"Merge created row explosion: {len(predictions_df)} games → {len(merged)} rows"
        
        # Rename selected column and add metadata
        merged = merged.rename(columns={
            market_col: 'market_consensus_home_prob'
        })
        merged['market_prob_source'] = source_label
        merged['market_prob_mae'] = mae if mae is not None else np.nan
        
        # Log merge quality
        if self.logger:
            unmatched = merged['market_consensus_home_prob'].isna().sum()
            if unmatched > 0:
                self.logger.warning(f"⚠️ {unmatched}/{len(merged)} predictions could not be matched to odds data")
        
        # Calculate CLV
        merged['clv'] = merged['predicted_home_win_prob'] - merged['market_consensus_home_prob']
        merged['abs_clv'] = merged['clv'].abs()
        
        # Edge detection (2%+ CLV = actionable edge)
        merged['has_edge'] = merged['abs_clv'] > 0.02
        
        # Classify edge size
        def classify_edge(abs_clv):
            if abs_clv < 0.02:
                return 'none'
            elif abs_clv < 0.05:
                return 'small'
            elif abs_clv < 0.10:
                return 'medium'
            else:
                return 'large'
        
        merged['edge_size'] = merged['abs_clv'].apply(classify_edge)
        
        # Log coverage
        coverage = merged['market_consensus_home_prob'].notna().sum()
        total = len(merged)
        
        if self.logger:
            self.logger.info(f"CLV calculation: {coverage}/{total} games matched with closing odds ({coverage/total:.1%})")
            self.logger.info(f"   Market prob source: {merged['market_prob_source'].iloc[0] if len(merged) > 0 else 'unknown'}")
            if mae is not None and not np.isnan(mae):
                self.logger.info(f"   MAE (consensus vs vegas): {mae:.4f} ({mae*100:.2f}%)")
        
        return merged
    
    def classify_edge_buckets(self, clv_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Classify bets into edge buckets for analysis.
        
        **Edge Buckets**:
        - Small Edge: 2-5% CLV
        - Medium Edge: 5-10% CLV
        - Large Edge: 10%+ CLV
        
        Args:
            clv_df: DataFrame from calculate_clv()
            
        Returns:
            Dict with bucket counts and percentages:
                - no_edge: Count of games with <2% CLV
                - small_edge: Count of 2-5% CLV games
                - medium_edge: Count of 5-10% CLV games
                - large_edge: Count of 10%+ CLV games
                - no_edge%: Percentage with no edge
                - small_edge%: Percentage with small edge
                - medium_edge%: Percentage with medium edge
                - large_edge%: Percentage with large edge
        """
        total_games = len(clv_df)
        
        buckets = {
            'no_edge': len(clv_df[clv_df['edge_size'] == 'none']),
            'small_edge': len(clv_df[clv_df['edge_size'] == 'small']),
            'medium_edge': len(clv_df[clv_df['edge_size'] == 'medium']),
            'large_edge': len(clv_df[clv_df['edge_size'] == 'large']),
        }
        
        # Calculate percentages
        bucket_pcts = {
            f"{key}%": (count / total_games * 100) if total_games > 0 else 0.0
            for key, count in buckets.items()
        }
        
        return {**buckets, **bucket_pcts}
    
    def calculate_leverage_aware_clv(
        self,
        predictions_with_clv: pd.DataFrame,
        closing_odds_df: pd.DataFrame,
        vegas_wpa_threshold: float = 0.15
    ) -> Dict[str, Any]:
        """
        Analyze CLV segmented by leverage using vegas_wpa.
        
        High-leverage situations (|WPA| > 0.15) represent critical moments
        where model edge matters most for betting outcomes.
        
        **Use Case**: Identify if model edges are concentrated in high-impact
        game situations or distributed randomly.
        
        Args:
            predictions_with_clv: DataFrame from calculate_clv()
            closing_odds_df: DataFrame with vegas_wpa column
            vegas_wpa_threshold: Threshold for high-leverage (default 0.15)
            
        Returns:
            Dict with leverage-aware metrics:
                - high_leverage_games: Count of high-leverage games
                - low_leverage_games: Count of low-leverage games
                - high_leverage_clv_mean: Average CLV on high-leverage plays
                - low_leverage_clv_mean: Average CLV on low-leverage plays
                - high_leverage_edge_pct: % of high-leverage plays with 2%+ edge
                - low_leverage_edge_pct: % of low-leverage plays with 2%+ edge
                - leverage_concentration: Ratio showing edge concentration (>1 = edges in high-leverage)
        """
        # Merge with vegas_wpa
        merged = predictions_with_clv.merge(
            closing_odds_df[['game_id', 'vegas_wpa', 'vegas_home_wpa']],
            on='game_id',
            how='left'
        )
        
        # Handle nulls in WPA data
        merged['vegas_home_wpa'] = merged['vegas_home_wpa'].fillna(0)
        merged['abs_vegas_wpa'] = merged['vegas_home_wpa'].abs()
        
        # Segment by leverage
        high_lev = merged[merged['abs_vegas_wpa'] > vegas_wpa_threshold]
        low_lev = merged[merged['abs_vegas_wpa'] <= vegas_wpa_threshold]
        
        result = {
            'high_leverage_games': len(high_lev),
            'low_leverage_games': len(low_lev),
            'high_leverage_clv_mean': high_lev['abs_clv'].mean() if len(high_lev) > 0 else 0.0,
            'low_leverage_clv_mean': low_lev['abs_clv'].mean() if len(low_lev) > 0 else 0.0,
            'high_leverage_edge_pct': (high_lev['has_edge'].sum() / len(high_lev) * 100) if len(high_lev) > 0 else 0.0,
            'low_leverage_edge_pct': (low_lev['has_edge'].sum() / len(low_lev) * 100) if len(low_lev) > 0 else 0.0
        }
        
        # Calculate leverage concentration (edges disproportionately in high-leverage?)
        if result['high_leverage_games'] > 0 and result['low_leverage_games'] > 0:
            result['leverage_concentration'] = result['high_leverage_edge_pct'] / result['low_leverage_edge_pct']
        else:
            result['leverage_concentration'] = 1.0
        
        if self.logger:
            self.logger.info(f"Leverage-aware CLV: {result['high_leverage_games']} high-leverage games, avg CLV {result['high_leverage_clv_mean']:.3f}%")
        
        return result
    
    def analyze_clv_persistence(
        self,
        clv_df: pd.DataFrame,
        group_by: str = 'week'
    ) -> Dict[str, Any]:
        """
        Measure if CLV patterns persist across time/teams/situations.
        
        **Persistence Interpretation**:
        - Persistent CLV = systematic model edge (skill)
        - Random CLV = noise / overfitting (luck)
        
        **Design Decision**: Uses standard deviation of group CLV means as persistence score.
        Higher std = stronger persistent patterns across groups.
        
        Args:
            clv_df: DataFrame from calculate_clv() with game metadata
            group_by: Grouping dimension ('week', 'home_team', 'away_team', 'spread_bucket')
            
        Returns:
            Dict with persistence metrics:
                - group_by: Dimension analyzed
                - group_clv_stats: DataFrame of CLV by group
                - persistence_score: Std dev of group CLV means (higher = more persistent)
                - consistent_groups: Groups with persistent +edge (>30% edge rate)
                - n_groups: Number of groups analyzed
                
        Returns error dict if group_by column not found.
        """
        if group_by not in clv_df.columns:
            if self.logger:
                self.logger.warning(f"Column '{group_by}' not found for persistence analysis")
            return {'error': f'Column {group_by} not found'}
        
        # Group-level CLV
        grouped = clv_df.groupby(group_by).agg({
            'abs_clv': ['mean', 'std', 'count'],
            'has_edge': 'sum',
            'clv': 'mean'  # Signed CLV to detect directional bias
        }).round(4)
        
        grouped.columns = ['avg_abs_clv', 'clv_std', 'n_games', 'n_edges', 'avg_clv_signed']
        grouped['edge_rate'] = (grouped['n_edges'] / grouped['n_games'] * 100).round(1)
        grouped = grouped.sort_values('avg_abs_clv', ascending=False)
        
        # Persistence score (standard deviation of group CLV means)
        # Higher std = more persistent patterns
        if len(grouped) == 1:
            persistence_score = 0.0  # Cannot measure persistence with 1 group
            if self.logger:
                self.logger.warning(f"Single {group_by} group - persistence cannot be measured")
        else:
            persistence_score = grouped['avg_abs_clv'].std()
        
        # Identify consistently high-edge groups
        consistent_groups = grouped[grouped['edge_rate'] > 30].index.tolist()
        
        result = {
            'group_by': group_by,
            'group_clv_stats': grouped.reset_index(),
            'persistence_score': persistence_score,
            'consistent_groups': consistent_groups,
            'n_groups': len(grouped)
        }
        
        if self.logger:
            self.logger.info(f"CLV persistence by {group_by}: {len(consistent_groups)} consistent groups, persistence score {persistence_score:.4f}")
        
        return result


__all__ = ['CLVCalculator']
