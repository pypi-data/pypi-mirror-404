"""
Training Report Diagnostics Section Generator

Generates ensemble diagnostics, market comparison, and advanced analytics sections.

**Refactoring Note**: Extracted from TrainingReportGenerator (lines 111-443)
to improve modularity and testability. Handles complex diagnostic analysis
and market comparison logic.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List


class DiagnosticsSectionGenerator:
    """
    Generates training report diagnostics sections.
    
    **Responsibilities**:
    - Ensemble component analysis (delegates to analyzer)
    - Market comparison analysis (CLV & ROI)
    - Advanced market analytics integration
    - Artifacts section generation
    
    **Pattern**: Composition over Inheritance - orchestrates complex analysis
    """
    
    def __init__(self, analyzer=None, logger=None):
        """
        Initialize diagnostics section generator.
        
        Args:
            analyzer: MetricsAnalyzer instance for ensemble analysis
            logger: Optional logger instance
        """
        self.analyzer = analyzer
        self.logger = logger
    
    def generate_ensemble_diagnostics(
        self,
        model,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        y_pred_proba: np.ndarray
    ) -> str:
        """
        Generate ensemble diagnostics section (delegates to analyzer).
        
        Args:
            model: Ensemble model instance
            X_test: Test features
            y_test: Test labels
            y_pred_proba: Prediction probabilities
            
        Returns:
            str: Formatted ensemble diagnostics section
        """
        if self.analyzer is None:
            return ""
        
        # Check if model is ensemble
        if not (hasattr(model, 'xgboost_model') and hasattr(model, 'linear_model')):
            return ""
        
        return self.analyzer.analyze_ensemble_components(
            model, X_test, y_test, y_pred_proba
        )
    
    def generate_market_comparison_section(
        self,
        y_pred_proba: Optional[np.ndarray],
        test_metadata: pd.DataFrame,
        y_test: pd.Series,
        output_dir: str,
        test_seasons: List[int]
    ) -> List[str]:
        """
        Generate market comparison and advanced analytics sections.
        
        Handles CLV calculation, ROI analysis, and enhanced odds reporting.
        
        Args:
            y_pred_proba: Prediction probabilities
            test_metadata: Test game metadata
            y_test: Test labels
            output_dir: Output directory for bet logs
            test_seasons: Test season years
            
        Returns:
            List[str]: List of formatted section strings
        """
        sections = []
        
        # Check preconditions
        if y_pred_proba is None or 'game_id' not in test_metadata.columns:
            return sections
        
        try:
            from nflfastRv3.features.ml_pipeline.reporting.market_analysis import create_market_analyzer
            from nflfastRv3.shared.bucket_adapter import get_bucket_adapter
            
            # Build predictions DataFrame with game metadata
            predictions_df = test_metadata.copy()
            predictions_df['predicted_home_win_prob'] = y_pred_proba[:, 1] if y_pred_proba.ndim > 1 else y_pred_proba
            predictions_df['actual_home_win'] = y_test.values
            
            # CRITICAL: Deduplicate to game-level
            predictions_df = self._deduplicate_predictions(predictions_df)
            
            # Load closing odds
            closing_odds_filtered = self._load_closing_odds(predictions_df)
            
            if closing_odds_filtered is None or len(closing_odds_filtered) == 0:
                if self.logger:
                    self.logger.debug("Market comparison skipped: No odds data for test games")
                return sections
            
            # Initialize market analyzer
            market_analyzer = create_market_analyzer(logger=self.logger)
            
            # Calculate CLV
            if self.logger:
                self.logger.info(f"📊 Calculating CLV for {len(closing_odds_filtered)} games with odds data...")
            
            predictions_with_clv = market_analyzer.calculate_clv(predictions_df, closing_odds_filtered)
            
            # Validate CLV calculation
            valid_clv_count = predictions_with_clv['market_consensus_home_prob'].notna().sum()
            if valid_clv_count == 0:
                if self.logger:
                    self.logger.warning("⚠️ Market comparison skipped: CLV calculation failed (0 valid market probabilities)")
                return sections
            
            # Calculate ROI and get bet log
            roi_sections = self._generate_roi_sections(
                market_analyzer, predictions_with_clv, output_dir, test_seasons
            )
            sections.extend(roi_sections)
            
            # Generate base market comparison section
            market_section = self._generate_base_market_section(
                market_analyzer, predictions_with_clv, valid_clv_count
            )
            if market_section:
                sections.append(market_section)
            
            # Generate enhanced analytics sections
            enhanced_sections = self._generate_enhanced_analytics(
                market_analyzer, predictions_with_clv, closing_odds_filtered
            )
            if enhanced_sections:
                sections.append("\n## Advanced Market Analytics\n\n" + "\n".join(enhanced_sections))
            
            if self.logger:
                self.logger.debug(f"✓ Market comparison analysis complete ({len(closing_odds_filtered)} games, {len(enhanced_sections)} enhanced analytics)")
        
        except Exception as e:
            # Log full error with traceback
            import traceback
            error_msg = f"Market comparison analysis failed: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
                self.logger.error(f"   Traceback:\n{traceback.format_exc()}")
            
            # Make error visible in report instead of silently skipping
            sections.append(f"\n## ⚠️ Market Comparison & CLV Analysis\n\n**Error:** {error_msg}\n\nCheck training logs for full traceback.\n")
        
        return sections
    
    def generate_artifacts_section(
        self,
        model_path: Optional[str],
        report_path: Path
    ) -> str:
        """
        Generate artifacts section showing file locations.
        
        Args:
            model_path: Path to saved model
            report_path: Path to report file
            
        Returns:
            str: Formatted artifacts section
        """
        sections = [f"""## Model Artifacts

**Report Location:** `{report_path}`"""]
        
        if model_path:
            sections.append(f"**Saved Model:** `{model_path}`")
        
        sections.append("""
**Usage:**
```python
# Load model
import joblib
model = joblib.load('path/to/model.joblib')

# Make predictions
predictions = model.predict(X_new)
probabilities = model.predict_proba(X_new)
```""")
        
        return '\n'.join(sections)
    
    # Helper methods
    
    def _deduplicate_predictions(self, predictions_df: pd.DataFrame) -> pd.DataFrame:
        """Deduplicate predictions to game-level."""
        if not predictions_df['game_id'].is_unique:
            n_rows = len(predictions_df)
            n_games = predictions_df['game_id'].nunique()
            if self.logger:
                self.logger.warning(
                    f"⚠️ Deduplicating predictions: {n_rows} rows → {n_games} unique games "
                    f"(feature joins likely caused row explosion)"
                )
            # Keep first occurrence of each game_id
            predictions_df = predictions_df.groupby('game_id', as_index=False).first()
        
        return predictions_df
    
    def _load_closing_odds(self, predictions_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Load closing odds from bucket."""
        try:
            from nflfastRv3.shared.bucket_adapter import get_bucket_adapter
            bucket = get_bucket_adapter()
            
            # Try game-level first (preferred), fall back to play-level
            try:
                closing_odds = bucket.read_data('odds_features_game_v1', 'features')
                if self.logger:
                    self.logger.info("✓ Using game-level odds (odds_features_game_v1)")
            except Exception:
                closing_odds = bucket.read_data('odds_features_v1', 'features')
                if self.logger:
                    self.logger.warning("⚠️ Using play-level odds (will deduplicate in market_analyzer)")
            
            # Filter to test games
            test_game_ids = predictions_df['game_id'].unique().tolist()
            closing_odds_filtered = closing_odds[closing_odds['game_id'].isin(test_game_ids)]
            
            return closing_odds_filtered
        
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Failed to load closing odds: {str(e)}")
            return None
    
    def _generate_roi_sections(
        self,
        market_analyzer,
        predictions_with_clv: pd.DataFrame,
        output_dir: str,
        test_seasons: List[int]
    ) -> List[str]:
        """Generate ROI analysis sections."""
        sections = []
        
        try:
            # Calculate ROI and get bet log
            roi_result = market_analyzer.calculate_roi(
                predictions_with_clv,
                bet_size=100.0,
                only_bet_with_edge=True,
                return_bet_log=True
            )
            
            # Unpack results (handle both old and new return signatures)
            if isinstance(roi_result, tuple):
                roi_metrics, bet_log = roi_result
            else:
                roi_metrics = roi_result
                bet_log = None
            
            # Save bet log and generate diagnostic report
            if bet_log is not None and len(bet_log) > 0:
                self._save_bet_log(bet_log, output_dir, test_seasons)
                
                # Generate ROI diagnostic report
                try:
                    # Validate bet_log has required columns
                    required_cols = ['model_bets_home', 'home_american_odds', 'away_american_odds',
                                     'won_bet', 'payout', 'edge_size', 'abs_clv']
                    missing_cols = [col for col in required_cols if col not in bet_log.columns]
                    
                    if missing_cols:
                        error_msg = f"Bet log missing required columns: {missing_cols}"
                        if self.logger:
                            self.logger.error(f"❌ {error_msg}")
                            self.logger.debug(f"   Available columns: {bet_log.columns.tolist()}")
                        # Add error to report instead of silently skipping
                        sections.append(f"\n## ⚠️ ROI Diagnostic Analysis\n\n**Error:** {error_msg}\n\nCheck training logs for details.\n")
                    else:
                        if self.logger:
                            self.logger.info(f"📊 Generating ROI diagnostic for {len(bet_log)} bets")
                        
                        roi_diagnostic = market_analyzer.generate_roi_diagnostic_report(bet_log)
                        sections.append(roi_diagnostic)
                        
                        if self.logger:
                            self.logger.info("✓ ROI diagnostic analysis added (odds + edge buckets)")
                        
                except Exception as diag_error:
                    # Full error logging with traceback
                    import traceback
                    error_msg = f"ROI diagnostic analysis failed: {str(diag_error)}"
                    
                    if self.logger:
                        self.logger.error(f"❌ {error_msg}")
                        self.logger.error(f"   Traceback:\n{traceback.format_exc()}")
                    
                    # Make error visible in report instead of silently omitting
                    sections.append(f"\n## ⚠️ ROI Diagnostic Analysis\n\n**Error:** {error_msg}\n\nCheck training logs for full traceback.\n")
        
        except Exception as e:
            # Full error logging with traceback
            import traceback
            error_msg = f"ROI analysis failed: {str(e)}"
            
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
                self.logger.error(f"   Traceback:\n{traceback.format_exc()}")
            
            # Make error visible in report instead of silently omitting section
            sections.append(
                f"\n## ⚠️ ROI Diagnostic Analysis\n\n"
                f"**Error:** {error_msg}\n\n"
                f"Check training logs for full traceback.\n"
            )
        
        return sections
    
    def _save_bet_log(self, bet_log: pd.DataFrame, output_dir: str, test_seasons: List[int]):
        """Save bet log to CSV file."""
        bet_log_dir = Path(output_dir) / 'bet_logs'
        bet_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine filename based on test seasons
        test_season_str = '_'.join(map(str, test_seasons))
        bet_log_path = bet_log_dir / f'bet_log_{test_season_str}.csv'
        
        bet_log.to_csv(bet_log_path, index=False)
        
        if self.logger:
            self.logger.info(f"💾 Saved bet log: {bet_log_path} ({len(bet_log)} bets)")
    
    def _generate_base_market_section(
        self,
        market_analyzer,
        predictions_with_clv: pd.DataFrame,
        valid_clv_count: int
    ) -> Optional[str]:
        """Generate base market comparison section."""
        try:
            # We need ROI metrics for the base section
            roi_result = market_analyzer.calculate_roi(
                predictions_with_clv,
                bet_size=100.0,
                only_bet_with_edge=True,
                return_bet_log=False
            )
            
            if isinstance(roi_result, tuple):
                roi_metrics = roi_result[0]
            else:
                roi_metrics = roi_result
            
            market_section = market_analyzer.generate_market_comparison_report(
                predictions_with_clv, roi_metrics
            )
            
            # Add enhanced reporting sections
            enhanced_sections = self._generate_enhanced_reporting(market_analyzer, predictions_with_clv)
            if enhanced_sections:
                market_section += "\n\n" + "\n\n".join(enhanced_sections)
            
            if self.logger:
                self.logger.info(f"✓ Base market comparison section added ({valid_clv_count}/{len(predictions_with_clv)} games with valid CLV)")
            
            return market_section
        
        except Exception as e:
            if self.logger:
                import traceback
                self.logger.error(f"❌ Failed to generate market comparison section: {str(e)}")
                self.logger.error(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def _generate_enhanced_reporting(
        self,
        market_analyzer,
        predictions_with_clv: pd.DataFrame
    ) -> List[str]:
        """Generate enhanced odds reporting sections."""
        sections = []
        
        # Enhancement 1: Top 10 Model Edges
        try:
            top_edges = market_analyzer.generate_top_edges_table(predictions_with_clv, n_top=10)
            if top_edges:
                sections.append(top_edges)
                if self.logger:
                    self.logger.info("✓ Top 10 Edges table added")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Top edges table generation failed: {str(e)}")
        
        # Enhancement 2: CLV Time Series by Week
        try:
            clv_time_series = market_analyzer.generate_clv_time_series(predictions_with_clv)
            if clv_time_series:
                sections.append(clv_time_series)
                if self.logger:
                    self.logger.info("✓ CLV Time Series by Week added")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ CLV time series generation failed: {str(e)}")
        
        return sections
    
    def _generate_enhanced_analytics(
        self,
        market_analyzer,
        predictions_with_clv: pd.DataFrame,
        closing_odds_filtered: pd.DataFrame
    ) -> List[str]:
        """Generate advanced market analytics sections."""
        enhanced_sections = []
        
        # 1. Market Baseline Summary
        try:
            market_baseline = market_analyzer.generate_market_baseline_summary(closing_odds_filtered)
            if market_baseline:
                enhanced_sections.append(market_baseline)
                if self.logger:
                    self.logger.info("✓ Market Baseline Summary added")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Market baseline summary generation failed: {str(e)}")
        
        # 2. Market calibration (if Vegas columns available)
        if 'vegas_home_wp' in closing_odds_filtered.columns and 'consensus_home_prob' in closing_odds_filtered.columns:
            try:
                calibration = market_analyzer.assess_market_calibration(closing_odds_filtered)
                if 'error' not in calibration:
                    enhanced_sections.append(self._format_calibration_section(calibration))
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Market calibration skipped: {e}")
        
        # 3. Leverage-aware CLV
        if 'vegas_home_wpa' in closing_odds_filtered.columns or 'vegas_wpa' in closing_odds_filtered.columns:
            try:
                leverage_metrics = market_analyzer.calculate_leverage_aware_clv(
                    predictions_with_clv, closing_odds_filtered
                )
                if 'error' not in leverage_metrics:
                    enhanced_sections.append(self._format_leverage_section(leverage_metrics))
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Leverage analysis skipped: {e}")
        
        # 4. Kelly Criterion bet sizing with weekly exposure control
        try:
            bankroll = 10000.0
            kelly_df = market_analyzer.calculate_kelly_stakes(
                predictions_with_clv, bankroll=bankroll, kelly_fraction=0.25
            )
            
            # Add weekly exposure analysis if 'week' column available
            kelly_df = market_analyzer.calculate_weekly_exposure(
                kelly_df, bankroll=bankroll, weekly_exposure_cap=0.35
            )
            
            kelly_section = self._format_kelly_section(kelly_df, bankroll=bankroll)
            if kelly_section:
                enhanced_sections.append(kelly_section)
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Kelly analysis skipped: {e}")
        
        # 5. CLV persistence
        if 'week' in predictions_with_clv.columns:
            try:
                persistence = market_analyzer.analyze_clv_persistence(
                    predictions_with_clv, group_by='week'
                )
                if 'error' not in persistence:
                    enhanced_sections.append(self._format_persistence_section(persistence))
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Persistence analysis skipped: {e}")
        
        # 6. Model calibration curve
        try:
            calibration_curve = market_analyzer.generate_calibration_curve(predictions_with_clv)
            if 'error' not in calibration_curve:
                enhanced_sections.append(self._format_calibration_curve_section(calibration_curve))
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Calibration curve skipped: {e}")
        
        # 7. Situational CLV
        if 'consensus_spread' in predictions_with_clv.columns:
            try:
                situational = market_analyzer.analyze_situational_clv(predictions_with_clv)
                if len(situational) > 0:
                    enhanced_sections.append(self._format_situational_section(situational))
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Situational analysis skipped: {e}")
        
        return enhanced_sections
    
    # Formatting helper methods
    
    def _format_calibration_section(self, calibration: dict) -> str:
        """Format market calibration section."""
        return f"""### Market Calibration Assessment

**Comparison:** Linear spread conversion vs. nflfastR Vegas-calibrated WP

- **Mean Absolute Difference:** {calibration['mean_abs_difference']:.4f} ({calibration['mean_abs_difference']*100:.2f}%)
- **Correlation:** {calibration['correlation']:.4f}
- **Systematic Bias:** {calibration['bias_overall']:+.4f}
  - Favorites: {calibration['bias_favorites']:+.4f}
  - Underdogs: {calibration['bias_underdogs']:+.4f}

**Recommendation:** {calibration['recommendation']}
"""
    
    def _format_leverage_section(self, leverage_metrics: dict) -> str:
        """Format leverage-aware CLV section."""
        lev_conc = leverage_metrics.get('leverage_concentration', 1.0)
        lev_conc_rating = "🟢 Concentrated" if lev_conc > 1.3 else "🟡 Balanced" if lev_conc > 0.7 else "🔴 Weak"
        interp = f"Model finds {lev_conc:.1f}x more edges in high-leverage moments (clutch time)" if lev_conc > 1.2 else "Model edges are balanced across leverage levels"
        
        return f"""### Leverage-Aware CLV Analysis

**High-Leverage Situations** (|WPA| > 0.15):
- **Games:** {leverage_metrics['high_leverage_games']}
- **Avg CLV:** {leverage_metrics['high_leverage_clv_mean']:.3f}
- **Edge Rate:** {leverage_metrics['high_leverage_edge_pct']:.1f}%

**Low-Leverage Situations:**
- **Games:** {leverage_metrics['low_leverage_games']}
- **Avg CLV:** {leverage_metrics['low_leverage_clv_mean']:.3f}
- **Edge Rate:** {leverage_metrics['low_leverage_edge_pct']:.1f}%

**Leverage Concentration:** {lev_conc:.2f}x ({lev_conc_rating})
{interp}
"""
    
    def _format_kelly_section(self, kelly_df: pd.DataFrame, bankroll: float = 10000.0) -> Optional[str]:
        """Format Kelly Criterion section WITH weekly exposure awareness."""
        kelly_bets = kelly_df[kelly_df['bet_recommendation'] == 'BET']
        if len(kelly_bets) == 0:
            return None
        
        total_kelly = kelly_bets['capped_stake'].sum()
        avg_kelly = kelly_bets['capped_stake'].mean()
        max_kelly = kelly_bets['capped_stake'].max()
        
        # Weekly exposure analysis (if available)
        weekly_section = ""
        if 'weekly_exposure_pct' in kelly_df.columns and 'week' in kelly_df.columns:
            max_weekly_pct = kelly_df['weekly_exposure_pct'].max()
            
            # Calculate average weekly exposure for weeks with bets
            weekly_bets = kelly_bets.groupby('week')['capped_stake'].sum() / bankroll
            avg_weekly = weekly_bets.mean() if len(weekly_bets) > 0 else 0.0
            
            # Check if any weeks exceeded cap
            weeks_over_cap = kelly_df[kelly_df['exceeds_weekly_cap']]['week'].nunique() if 'exceeds_weekly_cap' in kelly_df.columns else 0
            
            cap_status = f"⚠️ {weeks_over_cap} weeks scaled down to respect 35% cap)" if weeks_over_cap > 0 else "✓ All weeks within limits)"
            
            weekly_section = f"""
**Weekly Exposure Risk Management:**
- **Peak Weekly Exposure:** {max_weekly_pct:.1%} of bankroll ({cap_status}
- **Avg Weekly Exposure:** {avg_weekly:.1%} of bankroll (weeks with bets)
- **Portfolio Feasibility:** {"⚠️ Some weeks rebalanced" if weeks_over_cap > 0 else "✅ Bankroll sufficient for all bets"}
"""
        
        return f"""### Kelly Criterion Bet Sizing

**Optimal Bankroll Management** (Quarter-Kelly with ${bankroll:,.0f} bankroll):

- **Recommended Bets:** {len(kelly_bets)}
- **Total Staked (Cumulative Season):** ${total_kelly:,.2f} (serial deployment, not simultaneous)
- **Avg Stake Per Bet:** ${avg_kelly:,.2f} ({avg_kelly/bankroll:.1%} per bet)
- **Max Single-Bet Stake:** ${max_kelly:,.2f} ({max_kelly/bankroll:.1%} cap)
{weekly_section}
**Note:** Kelly Criterion maximizes long-term growth. Quarter-Kelly (25%) provides conservative risk management. Individual bets capped at 5% of bankroll. Weekly exposure monitored to prevent portfolio blow-up from clustering.
"""
    
    def _format_persistence_section(self, persistence: dict) -> str:
        """Format CLV persistence section."""
        pers_score = persistence['persistence_score']
        pers_rating = "🟢 Strong" if pers_score > 0.02 else "🟡 Moderate" if pers_score > 0.01 else "🔴 Weak"
        interp = "CLV patterns persist across weeks, indicating genuine model skill rather than random luck." if pers_score > 0.015 else "CLV varies week-to-week. Consider additional validation before live deployment."
        
        return f"""### CLV Persistence Analysis

**Week-to-Week Consistency:**
- **Persistence Score:** {pers_score:.4f} ({pers_rating})
- **Consistent High-Edge Weeks:** {len(persistence['consistent_groups'])}

**Interpretation:** {interp}
"""
    
    def _format_calibration_curve_section(self, calibration_curve: dict) -> str:
        """Format model calibration curve section."""
        brier = calibration_curve['brier_score']
        ece = calibration_curve['expected_calibration_error']
        
        brier_rating = "🟢 Excellent" if brier < 0.20 else "🟡 Good" if brier < 0.25 else "🔴 Poor"
        ece_rating = "🟢 Well-calibrated" if ece < 0.05 else "🟡 Fair" if ece < 0.10 else "🔴 Poorly calibrated"
        interp = "Model probabilities are trustworthy for Kelly betting" if ece < 0.08 else "Consider probability recalibration before using Kelly criterion"
        
        return f"""### Model Calibration Metrics

**Probabilistic Accuracy:**
- **Brier Score:** {brier:.4f} ({brier_rating}) - Lower is better (0-1 scale)
- **Log Loss:** {calibration_curve['log_loss']:.4f}
- **Expected Calibration Error:** {ece:.4f} ({ece_rating})

**Interpretation:** {interp}
"""
    
    def _format_situational_section(self, situational: dict) -> str:
        """Format situational CLV section."""
        sit_sections = []
        
        if 'by_spread' in situational:
            by_spread = situational['by_spread']
            sit_sections.append("**By Spread:**")
            for _, row in by_spread.iterrows():
                sit_sections.append(f"- {row['spread_bucket']}: {row['avg_clv']:.3f} CLV ({row['edge_hit_rate%']:.1f}% edge rate)")
        
        if 'by_total' in situational:
            by_total = situational['by_total']
            sit_sections.append("\n**By Total (Scoring Environment):**")
            for _, row in by_total.iterrows():
                sit_sections.append(f"- {row['total_bucket']}: {row['avg_clv']:.3f} CLV ({row['edge_hit_rate%']:.1f}% edge rate)")
        
        if 'by_season_phase' in situational:
            by_phase = situational['by_season_phase']
            sit_sections.append("\n**By Season Phase:**")
            for _, row in by_phase.iterrows():
                sit_sections.append(f"- {row['season_phase']}: {row['avg_clv']:.3f} CLV ({row['edge_hit_rate%']:.1f}% edge rate)")
        
        if not sit_sections:
            return ""
        
        return f"""### Situational CLV Breakdown

{chr(10).join(sit_sections)}

**Note:** Identifies profitable niches where model consistently finds edge.
"""


__all__ = ['DiagnosticsSectionGenerator']
