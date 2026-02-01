"""
Market Calibration - Probability calibration and betting stake analysis

Extracts calibration-focused methods from MarketComparisonAnalyzer to create
a focused, testable module for market probability assessment.

Pattern: Single Responsibility - Calibration analysis only
Layer: 2 (Implementation - calls infrastructure directly)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from logging import Logger  # Type hint only

from nflfastRv3.features.ml_pipeline.reporting.common.correlation_utils import safe_correlation


class MarketCalibrator:
    """
    Analyzes market calibration and optimal betting stakes.
    
    **Purpose**: Assess how well model probabilities calibrate against actual outcomes
    and calculate optimal bet sizing using Kelly Criterion
    
    **Key Methods**:
    - assess_market_calibration: Compare market consensus vs nflfastR baseline
    - calculate_kelly_stakes: Optimal bet sizing given bankroll
    - generate_calibration_curve: Reliability diagram (predicted vs actual)
    
    **Refactoring Note**: Extracted from MarketComparisonAnalyzer (lines 440-708)
    to improve modularity and testability.
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize market calibrator.
        
        Args:
            logger: Optional logger instance for diagnostic output
        """
        self.logger = logger
    
    def assess_market_calibration(
        self,
        closing_odds_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compare derived consensus_home_prob vs. vegas_home_wp calibration.
        
        Measures how much accuracy is lost using linear spread conversion
        vs. nflfastR's calibrated Vegas WP.
        
        **Use Case**: Determine which market probability source is more reliable
        for CLV calculations.
        
        **Design Decision**: Uses Mean Absolute Error (MAE) as primary metric.
        MAE >2% suggests using vegas_home_wp instead of consensus_home_prob.
        
        Args:
            closing_odds_df: DataFrame with consensus_home_prob and vegas_home_wp
            
        Returns:
            Dict with calibration metrics:
                - mean_abs_difference: Avg difference between methods
                - max_difference: Maximum difference observed
                - correlation: Pearson correlation coefficient
                - bias_overall: Systematic over/under estimation
                - bias_favorites: Bias when team is favored
                - bias_underdogs: Bias when team is underdog
                - games_analyzed: Sample size
                - recommendation: Which method to use
                
        Returns error dict if no data available.
        """
        df = closing_odds_df.copy()
        
        # Filter to rows with both values
        df = df[df['consensus_home_prob'].notna() & df['vegas_home_wp'].notna()]
        
        if len(df) == 0:
            return {'error': 'No data available for calibration comparison'}
        
        # Calculate differences
        df['diff'] = df['consensus_home_prob'] - df['vegas_home_wp']
        df['abs_diff'] = df['diff'].abs()
        
        # Correlation (using safe calculation to avoid constant series warnings)
        correlation = safe_correlation(
            df['consensus_home_prob'], 
            df['vegas_home_wp'],
            self.logger
        )
        
        # Handle case where correlation couldn't be calculated
        if pd.isna(correlation):
            if self.logger:
                self.logger.warning("Correlation calculation skipped (constant series or insufficient data)")
            correlation = 0.0
        
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
        
        **Kelly Formula**:
            stake = (bankroll * edge) / odds
            where edge = model_prob - market_prob
        
        **Risk Management**: Uses fractional Kelly (25% of full Kelly by default)
        to reduce variance and protect against model uncertainty.
        
        **Design Decision**: Caps individual bets at max_bet_pct (default 5%)
        of bankroll to prevent ruin risk from any single outcome.
        
        **Note**: This calculates *individual* bet sizing. Use calculate_weekly_exposure()
        to enforce portfolio-level risk constraints across multiple simultaneous bets.
        
        Args:
            predictions_with_clv: DataFrame from calculate_clv()
            bankroll: Total bankroll ($) (default 10,000)
            kelly_fraction: Fraction of full Kelly (0.25 = 25% for risk management)
            max_bet_pct: Maximum % of bankroll per bet (default 5%, recommended range 0.02-0.05)
            
        Returns:
            DataFrame with additional columns:
                - kelly_edge: Probability edge (model_prob - market_prob)
                - kelly_stake_full: Full Kelly bet size
                - kelly_stake: Fractional Kelly bet size
                - kelly_pct: % of bankroll to bet
                - capped_stake: Kelly stake capped at max_bet
                - bet_recommendation: 'BET' or 'PASS'
        """
        # Input validation
        if not (0 < kelly_fraction <= 1):
            raise ValueError(f"kelly_fraction must be in (0, 1], got {kelly_fraction}")
        if not (0 < max_bet_pct <= 1):
            raise ValueError(f"max_bet_pct must be in (0, 1], got {max_bet_pct}")
        if bankroll <= 0:
            raise ValueError(f"bankroll must be positive, got {bankroll}")
        
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
        
        # Improved logging with clearer semantics
        if self.logger:
            kelly_bets = df[df['bet_recommendation'] == 'BET']
            n_bets = len(kelly_bets)
            
            if n_bets > 0:
                total_kelly_stake = kelly_bets['capped_stake'].sum()
                avg_stake = total_kelly_stake / n_bets
                max_stake = kelly_bets['capped_stake'].max()
                
                self.logger.info(f"Kelly sizing: {n_bets} bets")
                self.logger.info(f"   Total staked (season): ${total_kelly_stake:,.2f}")
                self.logger.info(f"   Avg stake per bet: ${avg_stake:,.2f} ({avg_stake/bankroll:.1%} of bankroll)")
                self.logger.info(f"   Max single-bet stake: ${max_stake:,.2f} ({max_stake/bankroll:.1%} of bankroll, {max_bet_pct:.0%} cap)")
            else:
                self.logger.info(f"Kelly sizing: No bets recommended (no positive edges > 2%)")
        
        return df
    
    def calculate_weekly_exposure(
        self,
        kelly_df: pd.DataFrame,
        bankroll: float = 10000.0,
        weekly_exposure_cap: float = 0.35
    ) -> pd.DataFrame:
        """
        Calculate weekly cumulative exposure and identify weeks exceeding risk limits.
        
        **Risk Management**: Even with individual bet caps (5%), placing multiple bets
        in one week creates portfolio risk. This method ensures weekly exposure stays
        within bankroll-feasible limits.
        
        **Design Decision**: Default 35% weekly cap balances opportunity capture
        with risk of adverse outcomes clustering (e.g., all Week 1 favorites lose).
        
        **Example**:
            - Week 1: 5 bets @ $400 each = $2000 total (20% of $10k bankroll) ✓
            - Week 2: 10 bets @ $400 each = $4000 total (40% of $10k bankroll) ✗
              → Scales down proportionally to $3500 (35%)
        
        Args:
            kelly_df: DataFrame from calculate_kelly_stakes()
            bankroll: Total bankroll ($) (default 10,000)
            weekly_exposure_cap: Max % of bankroll to risk per week (default 35%)
            
        Returns:
            DataFrame with added columns:
                - week: Game week (if available)
                - weekly_stake_total: Sum of stakes for that week
                - weekly_exposure_pct: % of bankroll exposed that week
                - exceeds_weekly_cap: Boolean flag
                - scale_factor: Multiplier to apply (1.0 = no scaling, <1.0 = scaled down)
                - scaled_stake: Stake after applying weekly cap (if needed)
                
        Raises:
            ValueError: If weekly_exposure_cap not in (0, 1] or bankroll <= 0
        """
        # Input validation
        if not (0 < weekly_exposure_cap <= 1):
            raise ValueError(f"weekly_exposure_cap must be in (0, 1], got {weekly_exposure_cap}")
        if bankroll <= 0:
            raise ValueError(f"bankroll must be positive, got {bankroll}")
        
        # Check if week column exists
        if 'week' not in kelly_df.columns:
            if self.logger:
                self.logger.warning("⚠️ Weekly exposure calc skipped: 'week' column not in data")
            # Return with placeholder columns
            kelly_df['weekly_stake_total'] = 0.0
            kelly_df['weekly_exposure_pct'] = 0.0
            kelly_df['exceeds_weekly_cap'] = False
            kelly_df['scale_factor'] = 1.0
            kelly_df['scaled_stake'] = kelly_df.get('capped_stake', 0.0)
            return kelly_df
        
        df = kelly_df.copy()
        bets_only = df[df['bet_recommendation'] == 'BET']
        
        if len(bets_only) == 0:
            # No bets, return with safe defaults
            df['weekly_stake_total'] = 0.0
            df['weekly_exposure_pct'] = 0.0
            df['exceeds_weekly_cap'] = False
            df['scale_factor'] = 1.0
            df['scaled_stake'] = df.get('capped_stake', 0.0)
            return df
        
        # Calculate weekly totals
        weekly_totals = bets_only.groupby('week')['capped_stake'].sum().rename('weekly_stake_total')
        df = df.merge(weekly_totals, left_on='week', right_index=True, how='left')
        df['weekly_stake_total'] = df['weekly_stake_total'].fillna(0)
        
        # Calculate exposure percentage
        df['weekly_exposure_pct'] = df['weekly_stake_total'] / bankroll
        df['exceeds_weekly_cap'] = df['weekly_exposure_pct'] > weekly_exposure_cap
        
        # Scale down stakes for weeks exceeding cap
        df['scale_factor'] = np.where(
            df['exceeds_weekly_cap'],
            weekly_exposure_cap / df['weekly_exposure_pct'],  # Scale down proportionally
            1.0
        )
        df['scaled_stake'] = df['capped_stake'] * df['scale_factor']
        
        # Logging
        if self.logger:
            weeks_over_cap = df[df['exceeds_weekly_cap']]['week'].nunique()
            max_weekly_exposure = df['weekly_exposure_pct'].max()
            
            if weeks_over_cap > 0:
                self.logger.warning(f"⚠️ {weeks_over_cap} weeks exceed {weekly_exposure_cap:.0%} exposure cap")
                self.logger.info(f"   Automatically scaling stakes to respect weekly limits")
            
            self.logger.info(f"   Peak weekly exposure: {max_weekly_exposure:.1%} of bankroll")
        
        return df
    
    def generate_calibration_curve(
        self,
        predictions_with_outcomes: pd.DataFrame,
        n_bins: int = 10
    ) -> Dict[str, Any]:
        """
        Create calibration curve (reliability diagram).
        
        **Calibration Interpretation**:
        - Perfect calibration: Games predicted 70% home win → 70% actually win
        - Overconfident model: Predicts 80% → only 60% win
        - Underconfident model: Predicts 60% → 80% win
        
        **Metrics Explained**:
        - **Brier Score**: Mean squared error (0-1, lower = better)
        - **Log Loss**: Cross-entropy loss (0-∞, lower = better)
        - **ECE**: Expected Calibration Error (0-1, lower = better)
        
        Args:
            predictions_with_outcomes: DataFrame with pred prob and actual outcomes
            n_bins: Number of probability bins (default 10 for deciles)
            
        Returns:
            Dict with:
                - calibration_data: DataFrame for plotting [bin, predicted_prob, actual_rate, n_games]
                - brier_score: Overall calibration metric (lower is better, 0-1)
                - log_loss: Probabilistic accuracy metric (lower is better)
                - expected_calibration_error: Mean deviation from perfect calibration
                - n_games_analyzed: Sample size
                
        Returns error dict if no actual outcomes available.
        """
        if 'actual_home_win' not in predictions_with_outcomes.columns:
            return {'error': 'No actual outcomes available for calibration analysis'}
        
        df = predictions_with_outcomes.copy()
        df = df[df['predicted_home_win_prob'].notna() & df['actual_home_win'].notna()]
        
        if len(df) == 0:
            return {'error': 'No valid data for calibration'}
        
        # Create bins using quantile-based binning to ensure balanced bins
        try:
            df['prob_bin'] = pd.qcut(
                df['predicted_home_win_prob'],
                q=n_bins,
                labels=False,
                duplicates='drop'  # Handles case where many predictions are identical
            )
        except ValueError:
            # Fallback if qcut fails (e.g., < n_bins unique values)
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
        
        # Expected Calibration Error (ECE) - with error handling for zero variance
        try:
            calibration_data['calibration_error'] = (
                calibration_data['predicted_prob'] - calibration_data['actual_rate']
            ).abs()
            calibration_data['weight'] = calibration_data['n_games'] / len(df)
            ece = (calibration_data['calibration_error'] * calibration_data['weight']).sum()
        except (ValueError, ZeroDivisionError):
            if self.logger:
                self.logger.warning("Calibration curve ECE calculation failed due to insufficient variance")
            ece = np.nan
        
        # Clean calibration_data to prevent correlation warnings
        # Drop any columns with zero variance (constant values) that cause division by zero in correlations
        numeric_cols = calibration_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if calibration_data[col].nunique() <= 1:
                if self.logger:
                    self.logger.debug(f"Dropping constant column from calibration_data: {col}")
                calibration_data = calibration_data.drop(columns=[col])
        
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


__all__ = ['MarketCalibrator']
