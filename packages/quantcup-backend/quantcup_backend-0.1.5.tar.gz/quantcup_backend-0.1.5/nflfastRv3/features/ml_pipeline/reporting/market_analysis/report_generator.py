"""
Report Generator - Market comparison report assembly

Assembles market comparison reports by coordinating CLVCalculator, ROIAnalyzer,
MarketCalibrator, and SituationalAnalyzer.

Pattern: Composition - coordinates specialized analyzers
Layer: 2 (Implementation - calls infrastructure directly)
"""

import pandas as pd
from typing import Dict, Any, Optional
from logging import Logger  # Type hint only


class MarketReportGenerator:
    """
    Generates comprehensive market comparison reports.
    
    **Purpose**: Coordinate analysis modules to produce training report sections
    
    **Report Components**:
    - CLV distribution and edge classification
    - Simulated ROI metrics
    - Top model edges table
    - CLV time series (if week data available)
    - Market baseline summary
    - Key insights and recommendations
    
    **Refactoring Note**: Extracted from MarketComparisonAnalyzer (lines 878-1263)
    to improve modularity and testability. Coordinates specialized analyzers
    via composition.
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize report generator.
        
        Args:
            logger: Optional logger instance for diagnostic output
        """
        self.logger = logger
    
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
    
    def generate_market_comparison_report(
        self,
        predictions_with_clv: pd.DataFrame,
        roi_metrics: Dict[str, Any],
        edge_buckets: Dict[str, Any]
    ) -> str:
        """
        Generate markdown report section for training reports.
        
        **Composition Pattern**: Coordinates outputs from CLVCalculator and ROIAnalyzer
        to produce unified report section.
        
        Args:
            predictions_with_clv: DataFrame from CLVCalculator.calculate_clv()
            roi_metrics: Dict from ROIAnalyzer.calculate_roi()
            edge_buckets: Dict from CLVCalculator.classify_edge_buckets()
            
        Returns:
            str: Markdown-formatted report section with:
                - Odds coverage summary
                - CLV distribution
                - Simulated ROI metrics
                - Key insights and recommendations
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
            sections.append("- ⚠ **Model closely tracks market** - Average CLV < 1%, difficult to find actionable edge")
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
                sections.append("- ✅ **Profitable when betting +edge games** - Model successfully beats closing lines")
            else:
                sections.append("- ⚠ **Unprofitable even with +edge** - Model's edges not holding up in reality")
        
        sections.append("\n**Note:** CLV (Closing Line Value) measures if the model's probability is more accurate than the market's final consensus. Positive CLV indicates the model sees value.")
        
        return '\n'.join(sections)


__all__ = ['MarketReportGenerator']
