"""
Market Analysis - Closing Line Value and ROI analysis (refactored)

This module provides a backward-compatible facade for the refactored market analysis
functionality. The original MarketComparisonAnalyzer class has been split into:
- CLVCalculator: CLV calculations
- ROIAnalyzer: ROI simulations
- MarketCalibrator: Probability calibration
- SituationalAnalyzer: Context-specific CLV
- MarketReportGenerator: Report assembly

The facade pattern ensures existing code continues to work without changes.

Pattern: Facade (maintains backward compatibility)
Layer: 2 (Implementation - calls infrastructure directly)
"""

import pandas as pd
from typing import Dict, Any, Optional, Union, Tuple
from logging import Logger  # Type hint only

from commonv2.core.logging import get_logger
from .clv_calculator import CLVCalculator
from .roi_analyzer import ROIAnalyzer
from .market_calibration import MarketCalibrator
from .situational_analysis import SituationalAnalyzer
from .report_generator import MarketReportGenerator


class MarketComparisonAnalyzer:
    """
    Facade for market comparison analysis (maintains backward compatibility).
    
    **Refactoring Note**: This class now delegates to specialized analyzers:
    - `clv`: CLVCalculator
    - `roi`: ROIAnalyzer
    - `calibration`: MarketCalibrator
    - `situational`: SituationalAnalyzer
    - `reporter`: MarketReportGenerator
    
    All existing method signatures remain unchanged to ensure zero breaking changes.
    
    **Original Size**: 1,065 lines, 14 methods
    **New Size**: ~80 lines facade + 6 focused modules (80-240 lines each)
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize market comparison analyzer facade.
        
        Args:
            logger: Optional logger instance. If None, creates unified logger.
        """
        self.logger = logger or get_logger('nflfastRv3.ml_pipeline.market_analyzer')
        
        # Initialize specialized analyzers
        self.clv = CLVCalculator(logger=self.logger)
        self.roi = ROIAnalyzer(logger=self.logger)
        self.calibration = MarketCalibrator(logger=self.logger)
        self.situational = SituationalAnalyzer(logger=self.logger)
        self.reporter = MarketReportGenerator(logger=self.logger)
    
    # ========================================
    # CLV Calculation Methods (delegate to CLVCalculator)
    # ========================================
    
    def calculate_clv(
        self,
        predictions_df: pd.DataFrame,
        closing_odds_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate Closing Line Value (CLV) for all predictions."""
        return self.clv.calculate_clv(predictions_df, closing_odds_df)
    
    def classify_edge_buckets(self, clv_df: pd.DataFrame) -> Dict[str, Any]:
        """Classify bets into edge buckets for analysis."""
        return self.clv.classify_edge_buckets(clv_df)
    
    def calculate_leverage_aware_clv(
        self,
        predictions_with_clv: pd.DataFrame,
        closing_odds_df: pd.DataFrame,
        vegas_wpa_threshold: float = 0.15
    ) -> Dict[str, Any]:
        """Analyze CLV segmented by leverage using vegas_wpa."""
        return self.clv.calculate_leverage_aware_clv(
            predictions_with_clv, closing_odds_df, vegas_wpa_threshold
        )
    
    def analyze_clv_persistence(
        self,
        clv_df: pd.DataFrame,
        group_by: str = 'week'
    ) -> Dict[str, Any]:
        """Measure if CLV patterns persist across time/teams/situations."""
        return self.clv.analyze_clv_persistence(clv_df, group_by)
    
    # ========================================
    # ROI Calculation Methods (delegate to ROIAnalyzer)
    # ========================================
    
    def calculate_roi(
        self,
        predictions_with_clv: pd.DataFrame,
        bet_size: float = 100.0,
        only_bet_with_edge: bool = True,
        return_bet_log: bool = False
    ) -> Union[Dict[str, Any], Tuple[Dict[str, Any], pd.DataFrame]]:
        """Simulate flat betting ROI using actual closing odds."""
        return self.roi.calculate_roi(
            predictions_with_clv, bet_size, only_bet_with_edge, return_bet_log
        )
    
    def analyze_roi_by_odds_bucket(self, bet_log: pd.DataFrame) -> pd.DataFrame:
        """Segment ROI performance by betting odds brackets."""
        return self.roi.analyze_roi_by_odds_bucket(bet_log)
    
    def analyze_roi_by_edge_bucket(self, bet_log: pd.DataFrame) -> pd.DataFrame:
        """Segment ROI performance by CLV edge size."""
        return self.roi.analyze_roi_by_edge_bucket(bet_log)
    
    def generate_roi_diagnostic_report(self, bet_log: pd.DataFrame) -> str:
        """Generate markdown section with ROI bucket analysis."""
        return self.roi.generate_roi_diagnostic_report(bet_log)
    
    # ========================================
    # Calibration Methods (delegate to MarketCalibrator)
    # ========================================
    
    def assess_market_calibration(
        self,
        closing_odds_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compare derived consensus_home_prob vs. vegas_home_wp calibration."""
        return self.calibration.assess_market_calibration(closing_odds_df)
    
    def calculate_kelly_stakes(
        self,
        predictions_with_clv: pd.DataFrame,
        bankroll: float = 10000.0,
        kelly_fraction: float = 0.25,
        max_bet_pct: float = 0.05
    ) -> pd.DataFrame:
        """Calculate optimal bet sizes using Kelly Criterion."""
        return self.calibration.calculate_kelly_stakes(
            predictions_with_clv, bankroll, kelly_fraction, max_bet_pct
        )
    
    def generate_calibration_curve(
        self,
        predictions_with_outcomes: pd.DataFrame,
        n_bins: int = 10
    ) -> Dict[str, Any]:
        """Create calibration curve (reliability diagram)."""
        return self.calibration.generate_calibration_curve(predictions_with_outcomes, n_bins)
    
    # ========================================
    # Situational Analysis Methods (delegate to SituationalAnalyzer)
    # ========================================
    
    def analyze_situational_clv(
        self,
        clv_df: pd.DataFrame,
        contextual_features: Optional[pd.DataFrame] = None
    ) -> Dict[str, pd.DataFrame]:
        """Segment CLV performance by game situation."""
        return self.situational.analyze_situational_clv(clv_df, contextual_features)
    
    # ========================================
    # Report Generation Methods (delegate to MarketReportGenerator)
    # ========================================
    
    def generate_market_comparison_report(
        self,
        predictions_with_clv: pd.DataFrame,
        roi_metrics: Dict[str, Any]
    ) -> str:
        """Generate markdown report section for training reports."""
        # Calculate edge buckets inline (needed by reporter)
        edge_buckets = self.classify_edge_buckets(predictions_with_clv)
        return self.reporter.generate_market_comparison_report(
            predictions_with_clv, roi_metrics, edge_buckets
        )
    
    def generate_top_edges_table(
        self,
        predictions_with_clv: pd.DataFrame,
        n_top: int = 10
    ) -> str:
        """Generate Top 10 Model Edges table."""
        return self.reporter.generate_top_edges_table(predictions_with_clv, n_top)
    
    def generate_clv_time_series(
        self,
        predictions_with_clv: pd.DataFrame
    ) -> str:
        """Generate CLV Time Series by Week table."""
        return self.reporter.generate_clv_time_series(predictions_with_clv)
    
    def generate_market_baseline_summary(
        self,
        closing_odds_df: pd.DataFrame
    ) -> str:
        """Generate Market Baseline Summary showing consensus spread/total ranges."""
        return self.reporter.generate_market_baseline_summary(closing_odds_df)


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
