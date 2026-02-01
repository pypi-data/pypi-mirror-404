"""
Training Report Generator

Generic report orchestrator that delegates complex analysis to specialized components.
Following the same pattern as feature_orchestrator.py and model_trainer.py.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Orchestrator → Analyzers/Interpreters)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .analyzers import create_metrics_analyzer


class TrainingReportGenerator:
    """
    Generic report orchestrator.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + orchestration)
    Depth: 1 layer (delegates to analyzers/interpreters)
    
    Matches pattern from:
    - feature_orchestrator.py (FeatureEngineerImplementation)
    - model_trainer.py (ModelTrainerImplementation)
    """
    
    def __init__(self, logger=None):
        """
        Initialize with optional logger.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        
        # Delegate complex analysis to specialized components
        self.analyzer = create_metrics_analyzer()
    
    def generate_report(
        self,
        model,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        y_pred: np.ndarray,
        y_pred_proba: Optional[np.ndarray],
        test_metadata: pd.DataFrame,
        metrics: Dict[str, Any],
        train_seasons: List[int],
        test_seasons: List[int],
        test_week: Optional[int] = None,
        model_path: Optional[str] = None,
        output_dir: str = 'reports'
    ) -> str:
        """
        Generate comprehensive markdown training report.
        
        Orchestrates report generation by delegating to specialized components.
        
        Args:
            model: Trained machine learning model
            X_train: Training features
            X_test: Test features
            y_train: Training targets
            y_test: Test targets
            y_pred: Test predictions
            y_pred_proba: Test prediction probabilities (None for regression models)
            test_metadata: Test game metadata (game_id, teams, dates, etc.)
            metrics: Performance metrics dictionary
            train_seasons: Training seasons
            test_seasons: Test seasons
            test_week: Optional specific test week
            model_path: Path where model was saved
            output_dir: Directory to save report
            
        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'training_report_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build report sections (orchestrate)
        report_sections = []
        
        # Simple formatting (keep in orchestrator)
        report_sections.append(self._generate_header(train_seasons, test_seasons, test_week))
        report_sections.append(self._generate_executive_summary(metrics, len(X_train), len(X_test)))
        report_sections.append(self._generate_nfl_benchmarking_context())
        report_sections.append(self._generate_model_config(model, len(X_train.columns)))
        report_sections.append(self._generate_performance_metrics(metrics, y_test, y_pred))
        
        # Determine correct feature names (handle feature splitting)
        feature_names = X_test.columns
        if hasattr(model, 'tree_features_') and model.tree_features_:
            feature_names = model.tree_features_

        # Complex analysis (delegate to analyzer)
        report_sections.append(self.analyzer.analyze_confusion_matrix(y_test, y_pred))
        report_sections.append(self.analyzer.analyze_feature_importance(model, feature_names, X_train, y_train))
        
        # Ensemble diagnostics (if ensemble model)
        if hasattr(model, 'xgboost_model') and hasattr(model, 'linear_model') and y_pred_proba is not None:
            report_sections.append(self.analyzer.analyze_ensemble_components(
                model, X_test, y_test, y_pred_proba
            ))
        
        # Market comparison analysis (CLV & ROI + advanced analytics)
        if y_pred_proba is not None and 'game_id' in test_metadata.columns:
            try:
                from .market_analysis import create_market_analyzer
                from nflfastRv3.shared.bucket_adapter import get_bucket_adapter
                
                # Build predictions DataFrame with game metadata
                predictions_df = test_metadata.copy()
                predictions_df['predicted_home_win_prob'] = y_pred_proba[:, 1] if y_pred_proba.ndim > 1 else y_pred_proba
                predictions_df['actual_home_win'] = y_test.values
                
                # CRITICAL: Deduplicate to game-level (feature joins can explode rows)
                if not predictions_df['game_id'].is_unique:
                    n_rows = len(predictions_df)
                    n_games = predictions_df['game_id'].nunique()
                    if self.logger:
                        self.logger.warning(
                            f"⚠️ Deduplicating predictions: {n_rows} rows → {n_games} unique games "
                            f"(feature joins likely caused row explosion)"
                        )
                    # Keep first occurrence of each game_id (preserves pred probs and outcomes)
                    predictions_df = predictions_df.groupby('game_id', as_index=False).first()
                
                # Try to load closing odds from bucket (prefer game-level)
                try:
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
                    
                    if len(closing_odds_filtered) > 0:
                        # Run CLV analysis
                        market_analyzer = create_market_analyzer(logger=self.logger)
                        
                        if self.logger:
                            self.logger.info(f"📊 Calculating CLV for {len(closing_odds_filtered)} games with odds data...")
                        
                        predictions_with_clv = market_analyzer.calculate_clv(predictions_df, closing_odds_filtered)
                        
                        # Validate CLV calculation succeeded
                        valid_clv_count = predictions_with_clv['market_consensus_home_prob'].notna().sum()
                        if valid_clv_count == 0:
                            if self.logger:
                                self.logger.warning(f"⚠️ Market comparison skipped: CLV calculation failed (0 valid market probabilities)")
                                self.logger.debug(f"   Odds columns: {closing_odds_filtered.columns.tolist()}")
                                self.logger.debug(f"   Missing consensus_home_prob: {closing_odds_filtered['consensus_home_prob'].isna().sum()}/{len(closing_odds_filtered)}")
                        else:
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
                                
                                # Save bet log to CSV
                                if bet_log is not None and len(bet_log) > 0:
                                    bet_log_dir = Path(output_dir) / 'bet_logs'
                                    bet_log_dir.mkdir(parents=True, exist_ok=True)
                                    
                                    # Determine filename based on test seasons
                                    test_season_str = '_'.join(map(str, test_seasons))
                                    bet_log_path = bet_log_dir / f'bet_log_{test_season_str}.csv'
                                    
                                    bet_log.to_csv(bet_log_path, index=False)
                                    
                                    if self.logger:
                                        self.logger.info(f"💾 Saved bet log: {bet_log_path} ({len(bet_log)} bets)")
                                    
                                    # Generate ROI diagnostic report
                                    try:
                                        roi_diagnostic = market_analyzer.generate_roi_diagnostic_report(bet_log)
                                        report_sections.append(roi_diagnostic)
                                        
                                        if self.logger:
                                            self.logger.info(f"✓ ROI diagnostic analysis added (odds + edge buckets)")
                                    except Exception as diag_error:
                                        if self.logger:
                                            self.logger.warning(f"⚠️ ROI diagnostic analysis failed: {str(diag_error)}")
                                
                                # Generate base market comparison section
                                market_section = market_analyzer.generate_market_comparison_report(predictions_with_clv, roi_metrics)
                                report_sections.append(market_section)
                                
                                # NEW: Add enhanced odds reporting sections
                                # Enhancement 1: Top 10 Model Edges
                                try:
                                    top_edges = market_analyzer.generate_top_edges_table(predictions_with_clv, n_top=10)
                                    if top_edges:
                                        report_sections.append(top_edges)
                                        if self.logger:
                                            self.logger.info("✓ Top 10 Edges table added")
                                except Exception as edges_error:
                                    if self.logger:
                                        self.logger.warning(f"⚠️ Top edges table generation failed: {str(edges_error)}")
                                
                                # Enhancement 2: CLV Time Series by Week
                                try:
                                    clv_time_series = market_analyzer.generate_clv_time_series(predictions_with_clv)
                                    if clv_time_series:
                                        report_sections.append(clv_time_series)
                                        if self.logger:
                                            self.logger.info("✓ CLV Time Series by Week added")
                                except Exception as timeseries_error:
                                    if self.logger:
                                        self.logger.warning(f"⚠️ CLV time series generation failed: {str(timeseries_error)}")
                                
                                # Enhancement 3: Market Baseline Summary
                                try:
                                    market_baseline = market_analyzer.generate_market_baseline_summary(closing_odds_filtered)
                                    if market_baseline:
                                        report_sections.append(market_baseline)
                                        if self.logger:
                                            self.logger.info("✓ Market Baseline Summary added")
                                except Exception as baseline_error:
                                    if self.logger:
                                        self.logger.warning(f"⚠️ Market baseline summary generation failed: {str(baseline_error)}")
                                
                                if self.logger:
                                    self.logger.info(f"✓ Base market comparison section added ({valid_clv_count}/{len(predictions_with_clv)} games with valid CLV)")
                            except Exception as section_error:
                                if self.logger:
                                    import traceback
                                    self.logger.error(f"❌ Failed to generate market comparison section: {str(section_error)}")
                                    self.logger.error(f"   Traceback: {traceback.format_exc()}")
                        
                        # Enhanced analytics (if Vegas columns available)
                        enhanced_sections = []
                        
                        # 1. Market calibration (linear spread conversion vs Vegas calibrated)
                        if 'vegas_home_wp' in closing_odds_filtered.columns and 'consensus_home_prob' in closing_odds_filtered.columns:
                            try:
                                calibration = market_analyzer.assess_market_calibration(closing_odds_filtered)
                                if 'error' not in calibration:
                                    enhanced_sections.append(f"""### Market Calibration Assessment

**Comparison:** Linear spread conversion vs. nflfastR Vegas-calibrated WP

- **Mean Absolute Difference:** {calibration['mean_abs_difference']:.4f} ({calibration['mean_abs_difference']*100:.2f}%)
- **Correlation:** {calibration['correlation']:.4f}
- **Systematic Bias:** {calibration['bias_overall']:+.4f}
  - Favorites: {calibration['bias_favorites']:+.4f}
  - Underdogs: {calibration['bias_underdogs']:+.4f}

**Recommendation:** {calibration['recommendation']}
""")
                            except Exception as cal_error:
                                if self.logger:
                                    self.logger.debug(f"Market calibration skipped: {cal_error}")
                        
                        # 2. Leverage-aware CLV (high vs low leverage situations)
                        if 'vegas_home_wpa' in closing_odds_filtered.columns or 'vegas_wpa' in closing_odds_filtered.columns:
                            try:
                                leverage_metrics = market_analyzer.calculate_leverage_aware_clv(
                                    predictions_with_clv,
                                    closing_odds_filtered
                                )
                                if 'error' not in leverage_metrics:
                                    lev_conc = leverage_metrics.get('leverage_concentration', 1.0)
                                    lev_conc_rating = "🟢 Concentrated" if lev_conc > 1.3 else "🟡 Balanced" if lev_conc > 0.7 else "🔴 Weak"
                                    
                                    enhanced_sections.append(f"""### Leverage-Aware CLV Analysis
 
**High-Leverage Situations** (|WPA| > 0.15):
- **Games:** {leverage_metrics['high_leverage_games']}
- **Avg CLV:** {leverage_metrics['high_leverage_clv_mean']:.3f}
- **Edge Rate:** {leverage_metrics['high_leverage_edge_pct']:.1f}%

**Low-Leverage Situations:**
- **Games:** {leverage_metrics['low_leverage_games']}
- **Avg CLV:** {leverage_metrics['low_leverage_clv_mean']:.3f}
- **Edge Rate:** {leverage_metrics['low_leverage_edge_pct']:.1f}%

**Leverage Concentration:** {lev_conc:.2f}x ({lev_conc_rating})
{f"Model finds {lev_conc:.1f}x more edges in high-leverage moments (clutch time)" if lev_conc > 1.2 else "Model edges are balanced across leverage levels"}
""")
                            except Exception as lev_error:
                                if self.logger:
                                    self.logger.debug(f"Leverage analysis skipped: {lev_error}")
                        
                        # 3. Kelly Criterion bet sizing (optimal bankroll management)
                        try:
                            kelly_df = market_analyzer.calculate_kelly_stakes(
                                predictions_with_clv,
                                bankroll=10000.0,
                                kelly_fraction=0.25
                            )
                            
                            kelly_bets = kelly_df[kelly_df['bet_recommendation'] == 'BET']
                            if len(kelly_bets) > 0:
                                total_kelly = kelly_bets['capped_stake'].sum()
                                avg_kelly = kelly_bets['capped_stake'].mean()
                                max_kelly = kelly_bets['capped_stake'].max()
                                
                                enhanced_sections.append(f"""### Kelly Criterion Bet Sizing

**Optimal Bankroll Management** (Quarter-Kelly with $10,000 bankroll):

- **Recommended Bets:** {len(kelly_bets)}
- **Total Capital Deployed:** ${total_kelly:,.2f} ({total_kelly/10000:.1%} of bankroll)
- **Average Bet Size:** ${avg_kelly:,.2f}
- **Max Bet Size:** ${max_kelly:,.2f}

**Note:** Kelly Criterion maximizes long-term growth while managing risk. Quarter-Kelly (25%) provides conservative risk management vs. full Kelly.
""")
                        except Exception as kelly_error:
                            if self.logger:
                                self.logger.debug(f"Kelly analysis skipped: {kelly_error}")
                        
                        # 4. CLV persistence (skill vs luck)
                        if 'week' in predictions_with_clv.columns:
                            try:
                                persistence = market_analyzer.analyze_clv_persistence(
                                    predictions_with_clv,
                                    group_by='week'
                                )
                                if 'error' not in persistence:
                                    pers_score = persistence['persistence_score']
                                    pers_rating = "🟢 Strong" if pers_score > 0.02 else "🟡 Moderate" if pers_score > 0.01 else "🔴 Weak"
                                    
                                    enhanced_sections.append(f"""### CLV Persistence Analysis

**Week-to-Week Consistency:**
- **Persistence Score:** {pers_score:.4f} ({pers_rating})
- **Consistent High-Edge Weeks:** {len(persistence['consistent_groups'])}

{f"**Interpretation:** CLV patterns persist across weeks, indicating genuine model skill rather than random luck." if pers_score > 0.015 else "**Interpretation:** CLV varies week-to-week. Consider additional validation before live deployment."}
""")
                            except Exception as pers_error:
                                if self.logger:
                                    self.logger.debug(f"Persistence analysis skipped: {pers_error}")
                        
                        # 5. Model calibration curve
                        try:
                            calibration_curve = market_analyzer.generate_calibration_curve(predictions_with_clv)
                            if 'error' not in calibration_curve:
                                brier = calibration_curve['brier_score']
                                ece = calibration_curve['expected_calibration_error']
                                
                                brier_rating = "🟢 Excellent" if brier < 0.20 else "🟡 Good" if brier < 0.25 else "🔴 Poor"
                                ece_rating = "🟢 Well-calibrated" if ece < 0.05 else "🟡 Fair" if ece < 0.10 else "🔴 Poorly calibrated"
                                
                                enhanced_sections.append(f"""### Model Calibration Metrics

**Probabilistic Accuracy:**
- **Brier Score:** {brier:.4f} ({brier_rating}) - Lower is better (0-1 scale)
- **Log Loss:** {calibration_curve['log_loss']:.4f}
- **Expected Calibration Error:** {ece:.4f} ({ece_rating})

**Interpretation:** {'Model probabilities are trustworthy for Kelly betting' if ece < 0.08 else 'Consider probability recalibration before using Kelly criterion'}
""")
                        except Exception as cal_error:
                            if self.logger:
                                self.logger.debug(f"Calibration curve skipped: {cal_error}")
                        
                        # 6. Situational CLV (if contextual features available)
                        if 'consensus_spread' in predictions_with_clv.columns:
                            try:
                                situational = market_analyzer.analyze_situational_clv(predictions_with_clv)
                                if len(situational) > 0:
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
                                    
                                    if sit_sections:
                                        enhanced_sections.append(f"""### Situational CLV Breakdown

{chr(10).join(sit_sections)}

**Note:** Identifies profitable niches where model consistently finds edge.
""")
                            except Exception as sit_error:
                                if self.logger:
                                    self.logger.debug(f"Situational analysis skipped: {sit_error}")
                        
                        # Append enhanced sections if any were generated
                        if enhanced_sections:
                            report_sections.append("\n## Advanced Market Analytics\n\n" + "\n".join(enhanced_sections))
                        
                        if self.logger:
                            self.logger.debug(f"✓ Market comparison analysis complete ({len(closing_odds_filtered)} games, {len(enhanced_sections)} enhanced analytics)")
                    else:
                        if self.logger:
                            self.logger.debug("Market comparison skipped: No odds data for test games")
                except Exception as odds_error:
                    if self.logger:
                        self.logger.debug(f"Market comparison skipped: {str(odds_error)}")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Market comparison analysis unavailable: {str(e)}")
        
        # Feature selection audits (comprehensive visibility)
        # 1. Registry audit - design decisions and data availability
        report_sections.append(self.analyzer.analyze_feature_selection_audit(
            X_train, X_test, y_train, model.__class__
        ))
        
        # 2. Gauntlet audit - complete pipeline from Registry → XGBoost final usage
        if hasattr(model, 'feature_selector') and model.feature_selector:
            # Get post-Gauntlet transformed features for Step 6 correlation analysis
            X_train_selected = None
            try:
                if hasattr(model.feature_selector, 'selected_features_'):
                    # Extract only the selected features after The Gauntlet
                    selected_cols = model.feature_selector.selected_features_
                    if selected_cols:
                        X_train_selected = X_train[selected_cols]
            except Exception:
                # If transformation fails, Step 6 will fall back to importance-only
                pass
            
            report_sections.append(self.analyzer.analyze_gauntlet_audit(
                selector=model.feature_selector,
                original_features=X_train.columns.tolist(),
                X=X_train,
                y=y_train,
                X_selected=X_train_selected,  # Post-Gauntlet transformed features
                y_selected=y_train,
                model=model  # Pass model for Steps 4-6 (splitting, poison pills, XGBoost usage)
            ))
        
        # Test games details (show individual games tested)
        if y_pred_proba is not None:
            report_sections.append(self._generate_test_games_table(
                test_metadata, y_test, y_pred, y_pred_proba
            ))
        
        # Prediction analysis (delegate to analyzer)
        if y_pred_proba is not None:
            report_sections.append(self.analyzer.analyze_prediction_confidence(y_test, y_pred, y_pred_proba))
        
        # Simple sections (keep in orchestrator)
        report_sections.append(self._generate_artifacts_section(model_path, report_path))
        
        # Write report
        report_content = '\n\n'.join(report_sections)
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Training report saved: {report_path}")
        
        return str(report_path)
    
    def _generate_header(self, train_seasons: List[int], test_seasons: List[int],
                        test_week: Optional[int]) -> str:
        """Generate report header (simple formatting - keep in orchestrator)."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        test_desc = f"Week {test_week}" if test_week else "Full Season"
        
        return f"""# NFL Game Outcome Model - Training Report

**Generated:** {timestamp}

**Training Seasons:** {', '.join(map(str, train_seasons))}  
**Test Seasons:** {', '.join(map(str, test_seasons))} ({test_desc})

---"""
    
    def _generate_executive_summary(self, metrics: Dict[str, Any],
                                    train_size: int, test_size: int) -> str:
        """Generate executive summary (simple formatting - keep in orchestrator)."""
        accuracy = metrics.get('accuracy', 0)
        auc = metrics.get('auc', 0)
        
        # NFL-specific performance rating
        if accuracy >= 0.68:
            rating = "🟢 Elite"
            perf_level = "Top 1% professional"
        elif accuracy >= 0.63:
            rating = "🟢 Exceptional"
            perf_level = "Elite professional"
        elif accuracy >= 0.60:
            rating = "🟡 Strong"
            perf_level = "Consistently profitable"
        elif accuracy >= 0.58:
            rating = "🟡 Good"
            perf_level = "Professional"
        elif accuracy >= 0.55:
            rating = "🟠 Fair"
            perf_level = "Above break-even"
        elif accuracy >= 0.524:
            rating = "🟠 Marginal"
            perf_level = "Near break-even"
        else:
            rating = "🔴 Below Break-Even"
            perf_level = "Needs improvement"
        
        return f"""## Executive Summary

**Model Performance:** {rating} - {perf_level}

- **Accuracy:** {accuracy:.1%} ({int(accuracy * test_size)}/{test_size} games predicted correctly)
- **AUC-ROC:** {auc:.3f} (discrimination ability)
- **Training Set:** {train_size:,} games
- **Test Set:** {test_size:,} games

**Key Takeaway:** The model achieved {accuracy:.1%} accuracy on {test_size} unseen games. See NFL benchmarking context below for performance interpretation."""
    
    def _generate_model_config(self, model, num_features: int) -> str:
        """Generate model configuration section (simple introspection - keep in orchestrator)."""
        params = model.get_params()
        
        # Detect model type
        model_type = type(model).__name__
        model_module = type(model).__module__
        
        # Build algorithm description
        if 'xgboost' in model_module.lower():
            algorithm = "XGBoost Classifier (Gradient Boosting)"
        elif 'sklearn.ensemble' in model_module:
            if 'RandomForest' in model_type:
                algorithm = "Random Forest Classifier"
            elif 'GradientBoosting' in model_type:
                algorithm = "Gradient Boosting Classifier"
            else:
                algorithm = model_type
        elif 'lightgbm' in model_module.lower():
            algorithm = "LightGBM Classifier"
        elif 'catboost' in model_module.lower():
            algorithm = "CatBoost Classifier"
        else:
            algorithm = model_type
        
        # Build hyperparameters section
        hyperparams = []
        common_params = ['n_estimators', 'max_depth', 'learning_rate', 'subsample',
                         'colsample_bytree', 'min_samples_split', 'min_samples_leaf',
                         'max_features', 'random_state']
        
        for param in common_params:
            if param in params and params[param] is not None:
                param_name = param.replace('_', ' ').title()
                hyperparams.append(f"- {param_name}: {params[param]}")
        
        hyperparams_str = '\n'.join(hyperparams) if hyperparams else "- Default parameters used"
        
        return f"""## Model Configuration

**Algorithm:** {algorithm}

**Hyperparameters:**
{hyperparams_str}

**Features:** {num_features} differential features (home team - away team)"""
    
    def _generate_nfl_benchmarking_context(self) -> str:
        """Generate NFL-specific benchmarking context section."""
        # Helper function for table formatting (defined inline)
        def format_table(headers, rows):
            if not rows:
                return ""
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
            header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
            separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
            data_rows = []
            for row in rows:
                formatted_row = "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
                data_rows.append(formatted_row)
            return header_row + "\n" + separator + "\n" + "\n".join(data_rows)
        
        # Prepare benchmarking table data
        headers = ['Accuracy', 'Status', 'Estimated ROI*', 'Performance Level']
        rows = [
            ['68%+', '🟢 Elite', '30%+', 'Top 1% of professional handicappers'],
            ['63-67%', '🟢 Exceptional', '15-29%', 'Elite professional performance'],
            ['60-62%', '🟡 Strong', '9-14%', 'Consistently profitable professional'],
            ['58-59%', '🟡 Good', '5-8%', 'Professional handicapper'],
            ['55-57%', '🟠 Fair', '2-4%', 'Beating the market'],
            ['52.4-54%', '🟠 Marginal', '0-1%', 'Near break-even'],
            ['<52.4%', '🔴 Unprofitable', 'Negative', 'Losing money after vig']
        ]
        
        benchmark_table = format_table(headers, rows)
        
        return f"""## 📊 NFL Prediction Benchmarking Context

**Why NFL Prediction Differs from Traditional ML:**

NFL game prediction is fundamentally different from typical machine learning classification tasks:
- Games are designed to be ~50/50 propositions by oddsmakers
- High inherent variance due to injuries, weather, officiating, and human factors
- Limited sample sizes (only 272 games per regular season)
- High competitive parity by design (draft system, salary cap, revenue sharing)
- Continuous roster turnover and coaching changes

**Industry Performance Benchmarks:**

{benchmark_table}

*Estimated ROI assuming standard -110 betting odds with flat bet sizing.

**Expected Variance:**
- Even elite handicappers experience ±3-5% accuracy variance year-to-year
- Standard deviation of 5-8% is NORMAL for sports betting, not a flaw
- NFL parity increases naturally (injuries, rule changes, coaching turnover)

**Key Takeaway:** In NFL prediction, 60% accuracy is STRONG performance, 65% is EXCEPTIONAL, and 70%+ sustained across full seasons is nearly impossible. Don't compare to 90%+ accuracies seen in other ML domains - NFL games are specifically designed to be coin flips."""
    
    def _generate_performance_metrics(self, metrics: Dict[str, Any],
                                      y_test: pd.Series, y_pred: np.ndarray) -> str:
        """Generate detailed performance metrics (simple formatting - keep in orchestrator)."""
        accuracy = metrics.get('accuracy', 0)
        auc = metrics.get('auc', 0)
        actual_home_rate = metrics.get('actual_home_win_rate', 0)
        pred_home_rate = metrics.get('predicted_home_win_rate', 0)
        
        # Calculate additional metrics
        home_advantage_bias = pred_home_rate - actual_home_rate
        
        return f"""## Performance Metrics

### Overall Performance
- **Accuracy:** {accuracy:.1%}
- **AUC-ROC:** {auc:.3f}
- **Error Rate:** {(1-accuracy):.1%}

### Home Field Advantage Analysis
- **Actual Home Win Rate:** {actual_home_rate:.1%}
- **Predicted Home Win Rate:** {pred_home_rate:.1%}
- **Bias:** {home_advantage_bias:+.1%} {'(slight over-prediction of home wins)' if home_advantage_bias > 0.02 else '(slight under-prediction of home wins)' if home_advantage_bias < -0.02 else '(well-calibrated)'}

### Classification Report
```
{metrics.get('classification_report', 'N/A')}
```"""
    
    def _generate_test_games_table(self, test_metadata: pd.DataFrame,
                                   y_test: pd.Series, y_pred: np.ndarray,
                                   y_pred_proba: np.ndarray) -> str:
        """Generate detailed test games table showing individual predictions (simple formatting - keep in orchestrator)."""
        if len(test_metadata) == 0:
            return """## Test Games Detailed Results

No test games available."""
        
        # Build game-by-game results with confidence for sorting
        game_data = []
        
        for idx in range(len(y_test)):
            # Extract metadata
            if 'home_team' in test_metadata.columns and 'away_team' in test_metadata.columns:
                home_team = test_metadata.iloc[idx].get('home_team', 'HOME')
                away_team = test_metadata.iloc[idx].get('away_team', 'AWAY')
            else:
                home_team = 'HOME'
                away_team = 'AWAY'
            
            # Get actual outcome (1 = home win, 0 = away win)
            actual_home_win = bool(y_test.iloc[idx])
            actual_winner = home_team if actual_home_win else away_team
            
            # Get prediction
            pred_home_win = bool(y_pred[idx])
            predicted_winner = home_team if pred_home_win else away_team
            
            # Get probabilities
            home_prob = y_pred_proba[idx][1] if len(y_pred_proba[idx]) > 1 else y_pred_proba[idx][0]
            confidence = max(home_prob, 1 - home_prob)
            
            # Check if correct
            is_correct = (pred_home_win == actual_home_win)
            result_icon = "✅" if is_correct else "❌"
            
            # Format matchup
            matchup = f"{away_team} @ {home_team}"
            
            # Confidence level
            if confidence >= 0.8:
                conf_level = "🟢 High"
            elif confidence >= 0.6:
                conf_level = "🟡 Medium"
            else:
                conf_level = "🔴 Low"
            
            game_data.append({
                'confidence_raw': confidence,
                'row': [
                    matchup,
                    predicted_winner,
                    f"{home_prob:.1%}",
                    f"{(1-home_prob):.1%}",
                    f"{confidence:.1%}",
                    conf_level,
                    actual_winner,
                    result_icon
                ]
            })
        
        # Sort by confidence descending (highest confidence first)
        game_data.sort(key=lambda x: x['confidence_raw'], reverse=True)
        
        # Extract sorted rows
        table_rows = [game['row'] for game in game_data]
        
        # Use dynamic table formatting
        headers = ['Matchup', 'Predicted', 'Home Win %', 'Away Win %', 'Confidence', 'Level', 'Actual', 'Result']
        table_content = self._format_table(headers, table_rows)
        
        return f"""## Test Games Detailed Results

Individual predictions for each test game (sorted by confidence):

{table_content}"""
    
    def _format_table(self, headers, rows):
        """Format a markdown table with dynamic column widths based on actual content."""
        if not rows:
            return ""
        
        # Calculate max width for each column (accounting for emoji display width)
        col_widths = [self._display_width(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], self._display_width(str(cell)))
        
        # Build header row
        header_row = "| " + " | ".join(self._pad_to_width(h, col_widths[i]) for i, h in enumerate(headers)) + " |"
        
        # Build separator row
        separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
        
        # Build data rows
        data_rows = []
        for row in rows:
            formatted_row = "| " + " | ".join(self._pad_to_width(str(cell), col_widths[i]) for i, cell in enumerate(row)) + " |"
            data_rows.append(formatted_row)
        
        return header_row + "\n" + separator + "\n" + "\n".join(data_rows)
    
    def _display_width(self, text):
        """Calculate display width accounting for emojis taking up ~2 character widths."""
        import re
        # Common emoji patterns (circle emojis used in tables)
        emoji_pattern = re.compile(r'[\U0001F534-\U0001F7FF]|[\u2705\u274C]|[\U0001F7E0-\U0001F7E2]')
        
        # Count emojis
        emoji_count = len(emoji_pattern.findall(text))
        
        # Regular character count
        char_count = len(text)
        
        # Each emoji takes ~2 display widths but counts as 1-2 chars
        # So add 1 extra width per emoji
        return char_count + emoji_count
    
    def _pad_to_width(self, text, target_width):
        """Pad text to target display width, accounting for emoji widths."""
        current_width = self._display_width(text)
        padding_needed = target_width - current_width
        
        if padding_needed > 0:
            return text + (' ' * padding_needed)
        return text
    
    def _generate_artifacts_section(self, model_path: Optional[str],
                                   report_path: Path) -> str:
        """Generate artifacts section (simple formatting - keep in orchestrator)."""
        sections = ["""## Model Artifacts

**Report Location:** `{}`""".format(report_path)]
        
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

def create_report_generator(logger=None):
    """
    Factory function to create report generator.
    
    Matches pattern from:
    - create_feature_engineer()
    - create_model_trainer()
    
    Args:
        logger: Optional logger instance
        
    Returns:
        TrainingReportGenerator: Configured report generator
    """
    return TrainingReportGenerator(logger=logger)


__all__ = ['TrainingReportGenerator', 'create_report_generator']