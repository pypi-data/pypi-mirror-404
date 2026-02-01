"""
ROI Analyzer - Return on Investment calculation and diagnostics

Extracts ROI-focused methods from MarketComparisonAnalyzer to create
a focused, testable module for betting simulation and profitability analysis.

Pattern: Single Responsibility - ROI calculations only
Layer: 2 (Implementation - calls infrastructure directly)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, Tuple
from logging import Logger  # Type hint only


class ROIAnalyzer:
    """
    Calculates and analyzes Return on Investment (ROI) metrics.
    
    **Purpose**: Simulate flat betting ROI using actual closing odds
    
    **Key Metrics**:
    - Net profit/loss
    - ROI percentage
    - Win rate
    - ROI by odds bucket (favorites vs underdogs)
    - ROI by edge bucket (small vs medium vs large CLV)
    
    **Refactoring Note**: Extracted from MarketComparisonAnalyzer (lines 179-936)
    to improve modularity and testability.
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize ROI analyzer.
        
        Args:
            logger: Optional logger instance for diagnostic output
        """
        self.logger = logger
    
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
        
        **Design Decision**: Converts probability to American odds dynamically
        to handle varying market consensus. Caps extreme probabilities (0.001/0.999)
        to prevent division by zero.
        
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
        
        # Diagnostic logging for null propagation
        if self.logger:
            null_home_odds = df['home_american_odds'].isna().sum()
            null_away_odds = df['away_american_odds'].isna().sum()
            if null_home_odds > 0 or null_away_odds > 0:
                self.logger.error(
                    f"❌ American odds calculation produced NaNs: "
                    f"home={null_home_odds}, away={null_away_odds}"
                )
                self.logger.debug(
                    f"   market_consensus_home_prob nulls: "
                    f"{df['market_consensus_home_prob'].isna().sum()}"
                )
                # Drop rows with null odds to prevent downstream errors
                initial_len = len(df)
                df = df[df['home_american_odds'].notna() & df['away_american_odds'].notna()]
                self.logger.warning(
                    f"   Dropped {initial_len - len(df)} games with null odds, "
                    f"{len(df)} games remain for ROI calculation"
                )
        
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
    
    def analyze_roi_by_odds_bucket(self, bet_log: pd.DataFrame) -> pd.DataFrame:
        """
        Segment ROI performance by betting odds brackets.
        
        **Use Case**: Identify if model performs better on favorites vs underdogs
        
        **Odds Buckets**:
        - Heavy Favorite: <-180 (implied prob >64%)
        - Favorite: -180 to -130 (implied prob 57-64%)
        - Pick'em: -130 to +130 (implied prob 43-57%)
        - Underdog: +130 to +180 (implied prob 36-43%)
        - Big Underdog: >+180 (implied prob <36%)
        
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
                'roi': round(((x['payout'].sum() - len(x) * bet_size) / (len(x) * bet_size)) * 100, 1) if len(x) > 0 else 0.0
            }),
            include_groups=False
        ).reset_index()
        
        return results
    
    def analyze_roi_by_edge_bucket(self, bet_log: pd.DataFrame) -> pd.DataFrame:
        """
        Segment ROI performance by CLV edge size.
        
        **Use Case**: Verify if larger CLV edges actually translate to better ROI
        (tests if model edge is real or spurious)
        
        **Edge Buckets**:
        - Small: 2-5% CLV
        - Medium: 5-10% CLV
        - Large: 10%+ CLV
        
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
                'roi': round(((x['payout'].sum() - len(x) * bet_size) / (len(x) * bet_size)) * 100, 1) if len(x) > 0 else 0.0
            }),
            include_groups=False
        ).reset_index()
        
        return results
    
    def generate_roi_diagnostic_report(self, bet_log: pd.DataFrame) -> str:
        """
        Generate markdown section with ROI bucket analysis.
        
        **Use Case**: Identify specific betting scenarios where model excels or struggles
        
        **Diagnostic Insights**:
        - Which odds ranges are profitable?
        - Do larger edges actually produce better ROI?
        - Is model overconfident on certain bet types?
        
        Args:
            bet_log: DataFrame with bet results (from calculate_roi with return_bet_log=True)
            
        Returns:
            str: Markdown-formatted diagnostic report with:
                - ROI by odds bucket table
                - ROI by edge bucket table
                - Actionable diagnosis and recommendations
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


__all__ = ['ROIAnalyzer']
