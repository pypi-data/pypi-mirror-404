"""
Market Comparison Analyzer - Calculates CLV and ROI metrics

Compares model predictions against market consensus (closing odds) to calculate:
- Closing Line Value (CLV)
- Simulated ROI with flat betting strategy
- Edge classification and betting recommendations

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Implementation - calls infrastructure directly)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, Tuple
from logging import Logger  # Type hint only

from commonv2.core.logging import get_logger


class MarketComparisonAnalyzer:
    """
    Analyzes model predictions vs market consensus.
    
    **Purpose**: Calculate Closing Line Value (CLV) and simulated betting ROI
    
    **Data Flow**:
    1. Load model predictions (from training/prediction results)
    2. Load market consensus (from odds_features_v1 table)
    3. Calculate CLV = model_prob - market_prob
    4. Simulate flat betting with actual closing odds
    5. Generate markdown report with betting insights
    
    **Pattern**: Minimum Viable Decoupling (2 complexity points)
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize market comparison analyzer.
        
        Args:
            logger: Optional logger instance. If None, creates unified logger.
        """
        self.logger = logger or get_logger('nflfastRv3.ml_pipeline.market_analyzer')
    
    def calculate_clv(
        self,
        predictions_df: pd.DataFrame,
        closing_odds_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate Closing Line Value (CLV) for all predictions.
        
        CLV = Model Probability - Market Closing Probability
        
        Positive CLV indicates model sees value that market doesn't.
        
        Args:
            predictions_df: DataFrame with columns:
                - game_id (str)
                - predicted_home_win_prob (float, 0-1)
                - actual_home_win (int, 0 or 1) - optional for training reports
            closing_odds_df: DataFrame from odds_features_v1 OR odds_features_game_v1:
                - game_id (str)
                - consensus_home_prob (float, 0-1) - derived from spread
                - vegas_home_wp (float, 0-1) - nflfastR calibrated baseline
                - vegas_wp (float, 0-1) - offense perspective
                - vegas_wpa (float) - play-level leverage
                - vegas_home_wpa (float) - home play-level leverage
                - consensus_spread (float)
                - consensus_total (float)
                
        Returns:
            DataFrame with CLV metrics:
                - game_id
                - predicted_home_win_prob
                - market_consensus_home_prob
                - clv (float): predicted - market
                - abs_clv (float): absolute CLV
                - has_edge (bool): abs_clv > 0.02 (2%+ edge)
                - edge_size (str): 'small', 'medium', 'large'
                - actual_home_win (if available)
        """
        # CRITICAL: Validate predictions_df is game-level
        if not predictions_df['game_id'].is_unique:
            raise ValueError(
                f"predictions_df must be game-level (found {len(predictions_df)} rows, "
                f"{predictions_df['game_id'].nunique()} unique games)"
            )
        
        # CRITICAL: Deduplicate odds to game level if needed
        if not closing_odds_df['game_id'].is_unique:
            n_rows = len(closing_odds_df)
            n_games = closing_odds_df['game_id'].nunique()
            
            if self.logger:
                self.logger.warning(
                    f"⚠️ Deduplicating play-level odds ({n_rows} rows) to game-level ({n_games} games)"
                )
            
            # Aggregate play-level to game-level (use opening/first values)
            closing_odds_game = closing_odds_df.groupby('game_id', as_index=False).agg({
                'consensus_home_prob': 'first',  # Opening line
                'consensus_spread': 'first',
                'consensus_total': 'first',
                'vegas_home_wp': 'first',
                'vegas_home_wpa': lambda x: x.abs().max() if x.notna().any() else np.nan  # Max leverage
            })
        else:
            closing_odds_game = closing_odds_df
        
        # VALIDATE: Post-deduplication check
        assert closing_odds_game['game_id'].is_unique, "Deduplication failed - duplicate game_ids remain"
        
        # VALIDATE: Check if consensus_home_prob exists and has values
        if 'consensus_home_prob' not in closing_odds_game.columns:
            error_msg = "consensus_home_prob column missing from odds data"
            if self.logger:
                self.logger.error(f"❌ CLV calculation failed: {error_msg}")
                self.logger.debug(f"   Available columns: {closing_odds_game.columns.tolist()}")
            raise ValueError(error_msg)
        
        # Check for NULL values
        null_count = closing_odds_game['consensus_home_prob'].isna().sum()
        if null_count > 0 and self.logger:
            self.logger.warning(f"⚠️ {null_count}/{len(closing_odds_game)} odds records have NULL consensus_home_prob")
        
        # Merge predictions with closing odds (now guaranteed 1:1)
        merged = predictions_df.merge(
            closing_odds_game[['game_id', 'consensus_home_prob']],
            on='game_id',
            how='left'
        )
        
        # VALIDATE: Merge should not create row explosion
        assert len(merged) == len(predictions_df), \
            f"Merge created row explosion: {len(predictions_df)} games → {len(merged)} rows"
        
        # Rename for clarity
        merged = merged.rename(columns={
            'consensus_home_prob': 'market_consensus_home_prob'
        })
        
        # Log merge quality
        if self.logger:
            unmatched = merged['market_consensus_home_prob'].isna().sum()
            if unmatched > 0:
                self.logger.warning(f"⚠️ {unmatched}/{len(merged)} predictions could not be matched to odds data")
        
        # Calculate CLV
        merged['clv'] = merged['predicted_home_win_prob'] - merged['market_consensus_home_prob']
        merged['abs_clv'] = merged['clv'].abs()
        
        #  Edge detection (2%+ CLV = actionable edge)
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
        
        return merged
    
    def calculate_roi(
        self,
        predictions_with_clv: pd.DataFrame,
        bet_size: float = 100.0,
        only_bet_with_edge: bool = True,
        return_bet_log: bool = False
    ) -> Union[Dict[str, Any], Tuple[Dict[str, Any], pd.DataFrame]]:
        """
        Simulate flat betting ROI using actual closing odds.
        
        **Flat Betting Strategy**:
        - Bet $100 on every game (or only games with edge if only_bet_with_edge=True)
        - Use actual closing moneyline odds
        - Calculate profit/loss based on actual game outcomes
        
        **Assumptions**:
        - Standard -110 juice if consensus_home_prob not available
        - Model bets home team if predicted_home_win_prob > 0.5
        
        Args:
            predictions_with_clv: DataFrame from calculate_clv() with actual_home_win column
            bet_size: Flat bet size (default $100)
            only_bet_with_edge: Only bet when abs_clv > 2% (default True)
            return_bet_log: If True, return (roi_metrics, bet_log_df) tuple (default False)
            
        Returns:
            If return_bet_log=False (default):
                Dict with ROI metrics:
                    - total_bets (int): Number of bets placed
                    - total_wagered (float): Total amount bet
                    - total_payout (float): Total payout from wins
                    - net_profit (float): Payout - wagered
                    - roi (float): net_profit / total_wagered
                    - win_rate (float): % of bets won
                    - avg_clv (float): Average CLV on bets placed
                    - profitable_with_edge (bool): Made money betting only +edge games
            
            If return_bet_log=True:
                Tuple of (roi_metrics dict, bet_log DataFrame with columns):
                    - game_id
                    - predicted_home_win_prob
                    - model_bets_home (bool)
                    - actual_home_win
                    - home_american_odds
                    - away_american_odds
                    - payout ($ won/lost)
                    - won_bet (bool)
                    - clv (signed edge)
                    - abs_clv
                    - edge_size ('none', 'small', 'medium', 'large')
        """
        # Require actual_home_win column
        if 'actual_home_win' not in predictions_with_clv.columns:
            if self.logger:
                self.logger.warning("ROI calculation skipped: actual_home_win column not found (prediction mode)")
            return {
                'total_bets': 0,
                'total_wagered': 0.0,
                'total_payout': 0.0,
                'net_profit': 0.0,
                'roi': 0.0,
                'win_rate': 0.0,
                'avg_clv': 0.0,
                'profitable_with_edge': False,
                'skipped_reason': 'No actual outcomes available'
            }
        
        df = predictions_with_clv.copy()
        
        # Filter to only games with edge if requested
        if only_bet_with_edge:
            df = df[df['has_edge']]
        
        if len(df) == 0:
            return {
                'total_bets': 0,
                'total_wagered': 0.0,
                'total_payout': 0.0,
                'net_profit': 0.0,
                'roi': 0.0,
                'win_rate': 0.0,
                'avg_clv': 0.0,
                'profitable_with_edge': False,
                'skipped_reason': 'No bets with edge found'
            }
        
        # Determine model bet (home or away)
        df['model_bets_home'] = df['predicted_home_win_prob'] > 0.5
        
        # Convert consensus probability to American odds
        # consensus_home_prob = 0.55 → American odds ≈ -122
        # consensus_home_prob = 0.45 → American odds ≈ +122
        def prob_to_american_odds(prob):
            """Convert probability to American odds."""
            # Handle edge cases to avoid division by zero
            if prob >= 0.999:  # Effectively 100% - cap to avoid division by zero
                return -10000  # Extremely low payout for near-certain favorites
            elif prob <= 0.001:  # Effectively 0% - cap to avoid division by zero
                return 10000  # Extremely high payout for near-impossible underdogs
            elif prob >= 0.5:
                return -100 * prob / (1 - prob)
            else:
                return 100 * (1 - prob) / prob
        
        df['home_american_odds'] = df['market_consensus_home_prob'].apply(prob_to_american_odds)
        df['away_american_odds'] = (1 - df['market_consensus_home_prob']).apply(prob_to_american_odds)
        
        # Calculate payout for each bet
        def calculate_payout(row):
            """Calculate payout based on bet outcome."""
            if row['model_bets_home']:
                # Bet on home team
                correct = row['actual_home_win'] == 1
                odds = row['home_american_odds']
            else:
                # Bet on away team
                correct = row['actual_home_win'] == 0
                odds = row['away_american_odds']
            
            if not correct:
                return 0.0  # Lost bet
            
            # Won bet - calculate payout
            if odds < 0:
                # Favorite: Bet $100 to win $100 / |odds/100|
                profit = bet_size * (100 / abs(odds))
            else:
                # Underdog: Bet $100 to win $odds
                profit = bet_size * (odds / 100)
            
            return bet_size + profit  # Return stake + profit
        
        df['payout'] = df.apply(calculate_payout, axis=1)
        df['won_bet'] = df['payout'] > 0
        
        # Calculate ROI metrics
        total_bets = len(df)
        total_wagered = bet_size * total_bets
        total_payout = df['payout'].sum()
        net_profit = total_payout - total_wagered
        roi = net_profit / total_wagered if total_wagered > 0 else 0.0
        win_rate = df['won_bet'].mean()
        avg_clv = df['clv'].abs().mean()
        
        roi_metrics = {
            'total_bets': total_bets,
            'total_wagered': total_wagered,
            'total_payout': total_payout,
            'net_profit': net_profit,
            'roi': roi,
            'win_rate': win_rate,
            'avg_clv': avg_clv,
            'profitable_with_edge': net_profit > 0
        }
        
        # Return bet log if requested
        if return_bet_log:
            bet_log_columns = [
                'game_id', 'predicted_home_win_prob', 'model_bets_home',
                'actual_home_win', 'home_american_odds', 'away_american_odds',
                'payout', 'won_bet', 'clv', 'abs_clv', 'edge_size'
            ]
            # Filter to only existing columns (in case some are missing)
            available_columns = [col for col in bet_log_columns if col in df.columns]
            bet_log = df[available_columns].copy()
            return roi_metrics, bet_log
        
        return roi_metrics
    
    def classify_edge_buckets(self, clv_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Classify bets into edge buckets for analysis.
        
        Edge Buckets:
        - Small Edge: 2-5% CLV
        - Medium Edge: 5-10% CLV
        - Large Edge: 10%+ CLV
        
        Args:
            clv_df: DataFrame from calculate_clv()
            
        Returns:
            Dict with bucket counts and percentages
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
        
        Args:
            predictions_with_clv: DataFrame from calculate_clv()
            closing_odds_df: DataFrame with vegas_wpa column
            vegas_wpa_threshold: Threshold for high-leverage (default 0.15)
            
        Returns:
            Dict with leverage-aware metrics:
                - high_leverage_clv_mean: Average CLV on high-leverage plays
                - low_leverage_clv_mean: Average CLV on low-leverage plays
                - high_leverage_edge_pct: % of high-leverage plays with 2%+ edge
                - leverage_concentration: Are edges concentrated in high-leverage moments?
                - high_leverage_roi: ROI when betting only high-leverage edges
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
    
    def assess_market_calibration(
        self,
        closing_odds_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compare derived consensus_home_prob vs. vegas_home_wp calibration.
        
        Measures how much accuracy is lost using linear spread conversion
        vs. nflfastR's calibrated Vegas WP.
        
        Args:
            closing_odds_df: DataFrame with consensus_home_prob and vegas_home_wp
            
        Returns:
            Dict with calibration metrics:
                - mean_abs_difference: Avg difference between methods
                - correlation: Pearson correlation coefficient
                - bias: Systematic over/under estimation
                - recommendation: Which method to use
        """
        df = closing_odds_df.copy()
        
        # Filter to rows with both values
        df = df[df['consensus_home_prob'].notna() & df['vegas_home_wp'].notna()]
        
        if len(df) == 0:
            return {'error': 'No data available for calibration comparison'}
        
        # Calculate differences
        df['diff'] = df['consensus_home_prob'] - df['vegas_home_wp']
        df['abs_diff'] = df['diff'].abs()
        
        # Correlation
        correlation = df['consensus_home_prob'].corr(df['vegas_home_wp'])
        
        # Bias analysis (do they diverge for favorites?)
        df['is_favorite'] = df['vegas_home_wp'] > 0.55
        df['is_underdog'] = df['vegas_home_wp'] < 0.45
        
        result = {
            'mean_abs_difference': df['abs_diff'].mean(),
            'max_difference': df['abs_diff'].max(),
            'correlation': correlation,
            'bias_overall': df['diff'].mean(),
            'bias_favorites': df[df['is_favorite']]['diff'].mean() if df['is_favorite'].any() else 0.0,
            'bias_underdogs': df[df['is_underdog']]['diff'].mean() if df['is_underdog'].any() else 0.0,
            'games_analyzed': len(df)
        }
        
        # Recommendation
        if result['mean_abs_difference'] > 0.02:
            result['recommendation'] = 'Use vegas_home_wp (calibrated) instead of consensus_home_prob (derived)'
        else:
            result['recommendation'] = 'Both methods are well-aligned'
        
        if self.logger:
            self.logger.info(f"Market calibration: MAE={result['mean_abs_difference']:.4f}, correlation={result['correlation']:.4f}")
        
        return result
    
    def calculate_kelly_stakes(
        self,
        predictions_with_clv: pd.DataFrame,
        bankroll: float = 10000.0,
        kelly_fraction: float = 0.25,
        max_bet_pct: float = 0.05
    ) -> pd.DataFrame:
        """
        Calculate optimal bet sizes using Kelly Criterion.
        
        Kelly Formula:
            stake = (bankroll * edge) / odds
            where edge = model_prob - market_prob
        
        Args:
            predictions_with_clv: DataFrame from calculate_clv()
            bankroll: Total bankroll ($)
            kelly_fraction: Fraction of full Kelly (0.25 = 25% for risk management)
            max_bet_pct: Maximum % of bankroll per bet (default 5%)
            
        Returns:
            DataFrame with additional columns:
                - kelly_edge: Probability edge (model_prob - market_prob)
                - kelly_stake_full: Full Kelly bet size
                - kelly_stake: Fractional Kelly bet size
                - kelly_pct: % of bankroll to bet
                - capped_stake: Kelly stake capped at max_bet
                - bet_recommendation: 'BET' or 'PASS'
        """
        df = predictions_with_clv.copy()
        
        # Kelly edge (signed, not absolute)
        df['kelly_edge'] = df['predicted_home_win_prob'] - df['market_consensus_home_prob']
        
        # Only bet when we have positive edge
        df['should_bet'] = df['kelly_edge'] > 0.02  # 2% minimum edge
        
        # Convert market prob to decimal odds for Kelly formula
        # Home side odds when betting home
        df['decimal_odds_home'] = 1 / df['market_consensus_home_prob']
        df['decimal_odds_away'] = 1 / (1 - df['market_consensus_home_prob'])
        
        # Determine which side model prefers
        df['model_bets_home'] = df['predicted_home_win_prob'] > 0.5
        df['decimal_odds'] = np.where(df['model_bets_home'], df['decimal_odds_home'], df['decimal_odds_away'])
        df['model_prob'] = np.where(df['model_bets_home'], df['predicted_home_win_prob'], 1 - df['predicted_home_win_prob'])
        
        # Kelly formula: f = (p * (b+1) - 1) / b, where b = decimal_odds - 1
        df['b'] = df['decimal_odds'] - 1
        df['b'] = df['b'].replace(0, np.nan)  # Prevent divide by zero
        df['kelly_fraction_full'] = ((df['model_prob'] * (df['b'] + 1) - 1) / df['b']).fillna(0)
        df['kelly_fraction_full'] = df['kelly_fraction_full'].clip(lower=0)  # No negative bets
        
        # Apply fractional Kelly
        df['kelly_stake_full'] = df['kelly_fraction_full'] * bankroll
        df['kelly_stake'] = df['kelly_stake_full'] * kelly_fraction
        df['kelly_pct'] = df['kelly_fraction_full'] * kelly_fraction * 100
        
        # Cap at max bet
        max_bet = bankroll * max_bet_pct
        df['capped_stake'] = df['kelly_stake'].clip(upper=max_bet)
        
        # Bet recommendation
        df['bet_recommendation'] = np.where(
            df['should_bet'] & (df['capped_stake'] > 0),
            'BET',
            'PASS'
        )
        
        if self.logger:
            total_kelly_stake = df[df['bet_recommendation'] == 'BET']['capped_stake'].sum()
            n_bets = (df['bet_recommendation'] == 'BET').sum()
            self.logger.info(f"Kelly sizing: {n_bets} bets, total stake ${total_kelly_stake:,.2f} ({total_kelly_stake/bankroll:.1%} of bankroll)")
        
        return df
    
    def analyze_clv_persistence(
        self,
        clv_df: pd.DataFrame,
        group_by: str = 'week'
    ) -> Dict[str, Any]:
        """
        Measure if CLV patterns persist across time/teams/situations.
        
        Persistent CLV = systematic model edge (skill)
        Random CLV = noise / overfitting (luck)
        
        Args:
            clv_df: DataFrame from calculate_clv() with game metadata
            group_by: Grouping dimension ('week', 'home_team', 'away_team', 'spread_bucket')
            
        Returns:
            Dict with persistence metrics:
                - group_clv_stats: DataFrame of CLV by group
                - persistence_score: Correlation of group CLV with overall CLV
                - consistent_groups: Groups with persistent +edge
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
    
    def generate_calibration_curve(
        self,
        predictions_with_outcomes: pd.DataFrame,
        n_bins: int = 10
    ) -> Dict[str, Any]:
        """
        Create calibration curve (reliability diagram).
        
        Perfect calibration: Games predicted 70% home win → 70% actually win
        Overconfident model: Predicts 80% → only 60% win
        Underconfident model: Predicts 60% → 80% win
        
        Args:
            predictions_with_outcomes: DataFrame with pred prob and actual outcomes
            n_bins: Number of probability bins (default 10)
            
        Returns:
            Dict with:
                - calibration_data: DataFrame for plotting [bin_center, actual_rate, predicted_prob, n_games]
                - brier_score: Overall calibration metric (lower is better, 0-1)
                - log_loss: Probabilistic accuracy metric (lower is better)
                - expected_calibration_error: Mean deviation from perfect calibration
        """
        if 'actual_home_win' not in predictions_with_outcomes.columns:
            return {'error': 'No actual outcomes available for calibration analysis'}
        
        df = predictions_with_outcomes.copy()
        df = df[df['predicted_home_win_prob'].notna() & df['actual_home_win'].notna()]
        
        if len(df) == 0:
            return {'error': 'No valid data for calibration'}
        
        # Create bins
        df['prob_bin'] = pd.cut(df['predicted_home_win_prob'], bins=n_bins, labels=False)
        
        # Calculate calibration metrics per bin
        calibration_data = df.groupby('prob_bin').agg({
            'predicted_home_win_prob': 'mean',
            'actual_home_win': ['mean', 'count']
        }).reset_index()
        
        calibration_data.columns = ['bin', 'predicted_prob', 'actual_rate', 'n_games']
        
        # Brier Score: Mean squared error of predictions
        brier_score = ((df['predicted_home_win_prob'] - df['actual_home_win']) ** 2).mean()
        
        # Log Loss: Cross-entropy loss
        epsilon = 1e-15  # Avoid log(0)
        df['log_loss_contrib'] = -(
            df['actual_home_win'] * np.log(df['predicted_home_win_prob'].clip(epsilon, 1-epsilon)) +
            (1 - df['actual_home_win']) * np.log((1 - df['predicted_home_win_prob']).clip(epsilon, 1-epsilon))
        )
        log_loss = df['log_loss_contrib'].mean()
        
        # Expected Calibration Error (ECE)
        calibration_data['calibration_error'] = (calibration_data['predicted_prob'] - calibration_data['actual_rate']).abs()
        calibration_data['weight'] = calibration_data['n_games'] / len(df)
        ece = (calibration_data['calibration_error'] * calibration_data['weight']).sum()
        
        result = {
            'calibration_data': calibration_data,
            'brier_score': round(brier_score, 4),
            'log_loss': round(log_loss, 4),
            'expected_calibration_error': round(ece, 4),
            'n_games_analyzed': len(df)
        }
        
        if self.logger:
            self.logger.info(f"Calibration curve: Brier={result['brier_score']:.4f}, ECE={result['expected_calibration_error']:.4f}")
        
        return result
    
    def analyze_situational_clv(
        self,
        clv_df: pd.DataFrame,
        contextual_features: Optional[pd.DataFrame] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Segment CLV performance by game situation.
        
        Identifies profitable niches (e.g., "Model excels on rested favorites in domes").
        
        Args:
            clv_df: DataFrame from calculate_clv()
            contextual_features: Optional DataFrame with situational columns
                (rest_days, weather, is_dome, is_division, etc.)
            
        Returns:
            Dict of DataFrames, each showing:
                - situation
                - n_games
                - avg_clv
                - edge_hit_rate (% with 2%+ CLV)
                - avg_roi (if outcomes available)
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
            situations['by_spread'] = spread_analysis.reset_index()
        
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
    
    def analyze_roi_by_odds_bucket(self, bet_log: pd.DataFrame) -> pd.DataFrame:
        """
        Segment ROI performance by betting odds brackets.
        
        Args:
            bet_log: DataFrame with bet results (from calculate_roi with return_bet_log=True)
            
        Returns:
            DataFrame with columns:
                - odds_bucket: Odds range label
                - n_bets: Number of bets in bucket
                - win_rate: Win rate percentage
                - roi: ROI percentage
        """
        bet_log = bet_log.copy()
        
        # Determine which odds apply to the model's bet
        bet_log['model_odds'] = np.where(
            bet_log['model_bets_home'],
            bet_log['home_american_odds'],
            bet_log['away_american_odds']
        )
        
        # Create odds buckets
        bet_log['odds_bucket'] = pd.cut(
            bet_log['model_odds'],
            bins=[-np.inf, -180, -130, 130, 180, np.inf],
            labels=['Heavy Fav (<-180)', 'Fav (-180/-130)', 'Pick (-130/+130)', 'Dog (+130/+180)', 'Big Dog (>+180)']
        )
        
        # Calculate metrics per bucket (bet_size assumed $100 from calculate_roi)
        bet_size = 100.0
        
        results = bet_log.groupby('odds_bucket', observed=True).apply(
            lambda x: pd.Series({
                'n_bets': len(x),
                'win_rate': round(x['won_bet'].mean() * 100, 1),
                'roi': round(((x['payout'].sum() - len(x) * bet_size) / (len(x) * bet_size)) * 100, 1)
            })
        ).reset_index()
        
        return results
    
    def analyze_roi_by_edge_bucket(self, bet_log: pd.DataFrame) -> pd.DataFrame:
        """
        Segment ROI performance by CLV edge size.
        
        Args:
            bet_log: DataFrame with bet results (from calculate_roi with return_bet_log=True)
            
        Returns:
            DataFrame with columns:
                - edge_size: Edge category ('small', 'medium', 'large')
                - n_bets: Number of bets in bucket
                - avg_clv: Average CLV in bucket
                - win_rate: Win rate percentage
                - roi: ROI percentage
        """
        # bet_size assumed $100 from calculate_roi
        bet_size = 100.0
        
        results = bet_log.groupby('edge_size', observed=True).apply(
            lambda x: pd.Series({
                'n_bets': len(x),
                'avg_clv': round(x['abs_clv'].mean() * 100, 1),
                'win_rate': round(x['won_bet'].mean() * 100, 1),
                'roi': round(((x['payout'].sum() - len(x) * bet_size) / (len(x) * bet_size)) * 100, 1)
            })
        ).reset_index()
        
        return results
    
    def generate_top_edges_table(
        self,
        predictions_with_clv: pd.DataFrame,
        n_top: int = 10
    ) -> str:
        """
        Generate Top 10 Model Edges table showing games with highest absolute CLV.
        
        Identifies games where model had strongest disagreement with market,
        sorted by absolute CLV to highlight both positive and negative edges.
        
        Args:
            predictions_with_clv: DataFrame from calculate_clv()
            n_top: Number of top edges to show (default 10)
            
        Returns:
            str: Markdown-formatted table with top edges
        """
        if len(predictions_with_clv) == 0:
            return ""
        
        # Filter to games with valid market data
        df = predictions_with_clv[predictions_with_clv['market_consensus_home_prob'].notna()].copy()
        
        if len(df) == 0:
            return ""
        
        # Sort by absolute CLV (highest disagreement first)
        df_sorted = df.nlargest(n_top, 'abs_clv')
        
        # Build markdown table
        sections = []
        sections.append(f"\n### Top {n_top} Model Edges\n")
        sections.append("Games where model had strongest disagreement with market (sorted by absolute CLV):\n")
        
        # Table header
        if 'home_team' in df_sorted.columns and 'away_team' in df_sorted.columns:
            sections.append("| Matchup | Model Home Win % | Market Home Win % | CLV | Edge Direction | Actual | Result |")
            sections.append("|---------|------------------|-------------------|-----|----------------|--------|--------|")
            
            # Table rows
            for _, row in df_sorted.iterrows():
                matchup = f"{row.get('away_team', 'AWAY')} @ {row.get('home_team', 'HOME')}"
                model_pct = f"{row['predicted_home_win_prob']:.1%}"
                market_pct = f"{row['market_consensus_home_prob']:.1%}"
                clv = f"{row['clv']:+.1%}"  # Signed CLV
                
                # Edge direction
                if row['clv'] > 0.05:
                    edge = "🟢 Model likes HOME"
                elif row['clv'] < -0.05:
                    edge = "🔴 Model likes AWAY"
                else:
                    edge = "🟡 Marginal"
                
                # Actual result (if available)
                if 'actual_home_win' in row and not pd.isna(row['actual_home_win']):
                    actual = "HOME" if row['actual_home_win'] == 1 else "AWAY"
                    
                    # Check if prediction was correct
                    model_pick = "HOME" if row['predicted_home_win_prob'] > 0.5 else "AWAY"
                    result = "✅" if model_pick == actual else "❌"
                else:
                    actual = "TBD"
                    result = "—"
                
                sections.append(f"| {matchup} | {model_pct} | {market_pct} | {clv} | {edge} | {actual} | {result} |")
        else:
            # Fallback if team names not available
            sections.append("| Game ID | Model Home Win % | Market Home Win % | CLV | Edge Size |")
            sections.append("|---------|------------------|-------------------|-----|-----------|")
            
            for _, row in df_sorted.iterrows():
                game_id = row.get('game_id', 'Unknown')
                model_pct = f"{row['predicted_home_win_prob']:.1%}"
                market_pct = f"{row['market_consensus_home_prob']:.1%}"
                clv = f"{row['clv']:+.1%}"
                edge_size = row.get('edge_size', 'unknown').capitalize()
                
                sections.append(f"| {game_id} | {model_pct} | {market_pct} | {clv} | {edge_size} |")
        
        sections.append("\n**Interpretation:** Large absolute CLV indicates highest-signal games for post-game review and feature analysis.\n")
        
        return '\n'.join(sections)
    
    def generate_clv_time_series(
        self,
        predictions_with_clv: pd.DataFrame
    ) -> str:
        """
        Generate CLV Time Series by Week showing weekly CLV trends.
        
        Tracks CLV consistency week-to-week to identify if edges persist
        or fluctuate randomly (skill vs luck indicator).
        
        Args:
            predictions_with_clv: DataFrame from calculate_clv() with 'week' column
            
        Returns:
            str: Markdown-formatted time series table
        """
        if 'week' not in predictions_with_clv.columns:
            if self.logger:
                self.logger.debug("Week column not available for CLV time series")
            return ""
        
        df = predictions_with_clv[predictions_with_clv['market_consensus_home_prob'].notna()].copy()
        
        if len(df) == 0:
            return ""
        
        # Group by week
        weekly = df.groupby('week').agg({
            'game_id': 'count',
            'abs_clv': 'mean',
            'has_edge': lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0,
            'clv': 'mean'  # Signed CLV to detect directional bias
        }).reset_index()
        
        weekly.columns = ['week', 'n_games', 'avg_abs_clv', 'edge_rate_pct', 'avg_clv_signed']
        weekly = weekly.sort_values('week')
        
        # Build markdown table
        sections = []
        sections.append("\n### CLV Time Series by Week\n")
        sections.append("Weekly CLV trends showing edge consistency:\n")
        sections.append("| Week | Games | Avg Abs CLV | Edge Rate | Avg CLV (Signed) | Rating |")
        sections.append("|------|-------|-------------|-----------|------------------|--------|")
        
        for _, row in weekly.iterrows():
            week = int(row['week'])
            n_games = int(row['n_games'])
            avg_abs_clv = f"{row['avg_abs_clv']:.3f}"
            edge_rate = f"{row['edge_rate_pct']:.1f}%"
            avg_clv_signed = f"{row['avg_clv_signed']:+.3f}"
            
            # Rating based on edge rate
            if row['edge_rate_pct'] > 75:
                rating = "🟢 Excellent"
            elif row['edge_rate_pct'] > 50:
                rating = "🟡 Good"
            elif row['edge_rate_pct'] > 25:
                rating = "🟠 Fair"
            else:
                rating = "🔴 Weak"
            
            sections.append(f"| {week} | {n_games} | {avg_abs_clv} | {edge_rate} | {avg_clv_signed} | {rating} |")
        
        # Summary stats
        sections.append(f"\n**Summary:**")
        sections.append(f"- Mean weekly edge rate: {weekly['edge_rate_pct'].mean():.1f}%")
        sections.append(f"- Best week: Week {int(weekly.loc[weekly['edge_rate_pct'].idxmax(), 'week'])} ({weekly['edge_rate_pct'].max():.1f}% edge rate)")
        sections.append(f"- Worst week: Week {int(weekly.loc[weekly['edge_rate_pct'].idxmin(), 'week'])} ({weekly['edge_rate_pct'].min():.1f}% edge rate)")
        sections.append(f"- Edge rate std dev: {weekly['edge_rate_pct'].std():.1f}% (lower = more consistent)")
        
        sections.append("\n**Interpretation:** Consistent high edge rates across weeks indicate genuine model skill rather than random variance.\n")
        
        return '\n'.join(sections)
    
    def generate_market_baseline_summary(
        self,
        closing_odds_df: pd.DataFrame
    ) -> str:
        """
        Generate Market Baseline Summary showing consensus spread/total ranges.
        
        Condensed version of full market baseline showing key summary statistics
        about market consensus and bookmaker disagreement.
        
        Args:
            closing_odds_df: DataFrame from odds_features with consensus columns
            
        Returns:
            str: Markdown-formatted summary stats
        """
        if len(closing_odds_df) == 0:
            return ""
        
        df = closing_odds_df.copy()
        
        sections = []
        sections.append("\n### Market Baseline Summary\n")
        sections.append("Summary of market consensus and bookmaker disagreement:\n")
        
        # Spread statistics
        if 'consensus_spread' in df.columns:
            spread_stats = df['consensus_spread'].describe()
            sections.append("**Spread Consensus:**")
            sections.append(f"- Mean spread: {spread_stats['mean']:.2f}")
            sections.append(f"- Spread range: {spread_stats['min']:.1f} to {spread_stats['max']:.1f}")
            sections.append(f"- Median spread: {spread_stats['50%']:.1f}")
            
            # Identify close games (spread < 3)
            close_games = (df['consensus_spread'].abs() < 3).sum()
            sections.append(f"- Close games (|spread| < 3): {close_games} ({close_games/len(df)*100:.1f}%)\n")
        
        # Total statistics
        if 'consensus_total' in df.columns:
            total_stats = df['consensus_total'].describe()
            sections.append("**Total (Over/Under) Consensus:**")
            sections.append(f"- Mean total: {total_stats['mean']:.1f}")
            sections.append(f"- Total range: {total_stats['min']:.1f} to {total_stats['max']:.1f}")
            sections.append(f"- Median total: {total_stats['50%']:.1f}\n")
        
        # Bookmaker disagreement (if available)
        disagreement_cols = [col for col in df.columns if 'disagreement' in col.lower()]
        if disagreement_cols:
            sections.append("**Bookmaker Disagreement:**")
            for col in disagreement_cols:
                if df[col].notna().sum() > 0:
                    mean_disagreement = df[col].mean()
                    max_disagreement = df[col].max()
                    
                    market_type = col.replace('bookmaker_disagreement_', '').replace('_', ' ').title()
                    sections.append(f"- {market_type}: Mean {mean_disagreement:.3f}, Max {max_disagreement:.3f}")
            
            sections.append("\n**Note:** Higher disagreement = more market uncertainty = potential opportunity for model edge.\n")
        else:
            sections.append("**Note:** Bookmaker disagreement metrics not available in current odds data.\n")
        
        return '\n'.join(sections)
    
    def generate_roi_diagnostic_report(self, bet_log: pd.DataFrame) -> str:
        """
        Generate markdown section with ROI bucket analysis.
        
        Args:
            bet_log: DataFrame with bet results (from calculate_roi with return_bet_log=True)
            
        Returns:
            str: Markdown-formatted diagnostic report
        """
        sections = []
        
        sections.append("\n## ROI Diagnostic Analysis\n")
        sections.append("Per-game betting performance segmented by odds and edge size.\n")
        
        # Odds bucket table
        odds_buckets = self.analyze_roi_by_odds_bucket(bet_log)
        sections.append("### ROI by Odds Bucket\n")
        sections.append(odds_buckets.to_markdown(index=False))
        sections.append("\n")
        
        # Edge bucket table
        edge_buckets = self.analyze_roi_by_edge_bucket(bet_log)
        sections.append("### ROI by Edge Bucket\n")
        sections.append(edge_buckets.to_markdown(index=False))
        sections.append("\n")
        
        # Diagnosis
        sections.append("### Diagnosis\n")
        
        # Identify worst odds bucket
        if len(odds_buckets) > 0 and not odds_buckets['roi'].isna().all():
            worst_idx = int(odds_buckets['roi'].idxmin())
            worst_roi: float = float(odds_buckets.at[worst_idx, 'roi'])
            if worst_roi < -5:
                worst_bucket: str = str(odds_buckets.at[worst_idx, 'odds_bucket'])
                worst_n_bets: int = int(odds_buckets.at[worst_idx, 'n_bets'])
                sections.append(f"- ⚠️ **{worst_bucket}** losing {worst_roi:.1f}% ROI ({worst_n_bets} bets)")
        
        # Identify worst edge bucket
        if len(edge_buckets) > 0 and not edge_buckets['roi'].isna().all():
            worst_edge_idx = int(edge_buckets['roi'].idxmin())
            worst_edge_roi: float = float(edge_buckets.at[worst_edge_idx, 'roi'])
            worst_edge_size: str = str(edge_buckets.at[worst_edge_idx, 'edge_size'])
            worst_edge_n_bets: int = int(edge_buckets.at[worst_edge_idx, 'n_bets'])
            if worst_edge_size == 'large' and worst_edge_roi < 0:
                sections.append(f"- 🔴 **Large edge games** are unprofitable ({worst_edge_roi:.1f}% ROI on {worst_edge_n_bets} bets)")
                sections.append("  → Model is overconfident on high-CLV predictions")
                sections.append("  → **Recommendation:** Only bet small/medium edges (2-10% CLV)")
        
        # Identify best performing bucket
        if len(edge_buckets) > 0 and not edge_buckets['roi'].isna().all():
            best_edge_idx = int(edge_buckets['roi'].idxmax())
            best_roi: float = float(edge_buckets.at[best_edge_idx, 'roi'])
            if best_roi > 5:
                best_edge_size: str = str(edge_buckets.at[best_edge_idx, 'edge_size'])
                best_n_bets: int = int(edge_buckets.at[best_edge_idx, 'n_bets'])
                sections.append(f"- ✅ **{best_edge_size.capitalize()} edge** performing well (+{best_roi:.1f}% ROI on {best_n_bets} bets)")
        
        return '\n'.join(sections)
    
    def generate_market_comparison_report(
        self,
        predictions_with_clv: pd.DataFrame,
        roi_metrics: Dict[str, Any]
    ) -> str:
        """
        Generate markdown report section for training reports.
        
        Args:
            predictions_with_clv: DataFrame from calculate_clv()
            roi_metrics: Dict from calculate_roi()
            
        Returns:
            str: Markdown-formatted report section
        """
        sections = []
        
        sections.append("## Market Comparison & CLV Analysis\n")
        
        # Coverage summary
        coverage = predictions_with_clv['market_consensus_home_prob'].notna().sum()
        total = len(predictions_with_clv)
        coverage_pct = (coverage / total) if total > 0 else 0.0  # Keep as ratio 0-1, format string handles %
        
        if self.logger:
            self.logger.info(f"Generating market comparison report: {coverage}/{total} games with valid odds ({coverage_pct:.1f}%)")
        
        sections.append(f"**Odds Coverage:** {coverage}/{total} test games matched to closing lines ({coverage_pct:.1%})\n")
        
        if coverage == 0:
            if self.logger:
                self.logger.warning("⚠️ Market report section incomplete: No valid closing odds matched")
            sections.append("⚠️ **No closing odds data available** - CLV analysis skipped.\n")
            return '\n'.join(sections)
        
        # CLV distribution
        edge_buckets = self.classify_edge_buckets(predictions_with_clv)
        
        sections.append("### CLV Distribution\n")
        sections.append(f"- **No Edge (<2%)**: {edge_buckets['no_edge']} games ({edge_buckets['no_edge%']:.1f}%)")
        sections.append(f"- **Small Edge (2-5%)**: {edge_buckets['small_edge']} games ({edge_buckets['small_edge%']:.1f}%)")
        sections.append(f"- **Medium Edge (5-10%)**: {edge_buckets['medium_edge']} games ({edge_buckets['medium_edge%']:.1f}%)")
        sections.append(f"- **Large Edge (10%+)**: {edge_buckets['large_edge']} games ({edge_buckets['large_edge%']:.1f}%)\n")
        
        # ROI simulation
        skipped = roi_metrics.get('skipped_reason')
        if skipped:
            sections.append(f"### Simulated ROI\n")
            sections.append(f"⚠️ **ROI calculation skipped**: {skipped}\n")
        else:
            sections.append("### Simulated ROI (Flat Betting Strategy)\n")
            sections.append(f"**Strategy:** Bet $100 on every game with 2%+ edge using closing odds\n")
            sections.append(f"- **Total Bets:** {roi_metrics['total_bets']}")
            sections.append(f"- **Total Wagered:** ${roi_metrics['total_wagered']:,.2f}")
            sections.append(f"- **Total Payout:** ${roi_metrics['total_payout']:,.2f}")
            sections.append(f"- **Net Profit:** ${roi_metrics['net_profit']:+,.2f}")
            
            # ROI rating
            roi = roi_metrics['roi']
            if roi > 0.15:
                roi_rating = "🟢 Elite"
            elif roi > 0.08:
                roi_rating = "🟢 Exceptional"
            elif roi > 0.03:
                roi_rating = "🟡 Good"
            elif roi > 0.0:
                roi_rating = "🟡 Marginal"
            else:
                roi_rating = "🔴 Unprofitable"
            
            sections.append(f"- **ROI:** {roi:.1%} ({roi_rating})")
            sections.append(f"- **Win Rate:** {roi_metrics['win_rate']:.1%}")
            sections.append(f"- **Average CLV:** {roi_metrics['avg_clv']:.1%}\n")
        
        # Key insights
        sections.append("### Key Insights\n")
        
        avg_clv = predictions_with_clv['abs_clv'].mean()
        total_edge_games = edge_buckets['small_edge'] + edge_buckets['medium_edge'] + edge_buckets['large_edge']
        
        if avg_clv < 0.01:
            sections.append("- ⚠️ **Model closely tracks market** - Average CLV < 1%, difficult to find actionable edge")
        elif avg_clv < 0.03:
            sections.append("- 🟡 **Modest disagreement with market** - Model occasionally identifies +2-3% edges")
        else:
            sections.append("- 🟢 **Meaningful market disagreement** - Model frequently identifies significant edges")
        
        if total_edge_games == 0:
            sections.append("- ❌ **No betting opportunities** - Model predictions align too closely with market")
        elif total_edge_games < 3:
            sections.append(f"- 🟡 **Limited opportunities** - Only {total_edge_games} games with 2%+ edge")
        else:
            sections.append(f"- ✅ **Betting opportunities exist** - {total_edge_games} games with 2%+ edge identified")
        
        if not skipped:
            if roi_metrics['profitable_with_edge']:
                sections.append("- ✅ **Profitable when betting +edge games** -Model successfully beats closing lines")
            else:
                sections.append("- ⚠️ **Unprofitable even with +edge** - Model's edges not holding up in reality")
        
        sections.append("\n**Note:** CLV (Closing Line Value) measures if the model's probability is more accurate than the market's final consensus. Positive CLV indicates the model sees value.")
        
        return '\n'.join(sections)


def create_market_analyzer(logger=None):
    """
    Factory function to create market comparison analyzer.
    
    Unified logging pattern: Uses commonv2.get_logger by default
    
    Pattern matches:
    - create_metrics_analyzer()
    - create_report_generator()
    
    Args:
        logger: Optional logger instance (uses unified logger if None)
        
    Returns:
        MarketComparisonAnalyzer: Configured analyzer with unified logger
    """
    if logger is None:
        logger = get_logger('nflfastRv3.ml_pipeline.market_analyzer')
    return MarketComparisonAnalyzer(logger=logger)


__all__ = ['MarketComparisonAnalyzer', 'create_market_analyzer']
