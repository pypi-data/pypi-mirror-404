"""
Model Diagnostics Implementation
Pattern: Minimum Viable Decoupling (MVD)

Consolidates 4 model diagnostic scripts with special focus on
validate_weekly.py (1,123 lines) extraction into WalkForwardValidator.
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from commonv2 import get_logger
from nflfastRv3.shared.database_router import get_database_router
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from nflfastRv3.shared.temporal_validator import TemporalValidator
from nflfastRv3.features.ml_pipeline.orchestrators.model_trainer import create_model_trainer
from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeModel
from nflfastRv3.features.analytics_suite.reporting.generator import DiagnosticsReportGenerator

@dataclass
class WeekMetrics:
    """Metrics for a single week of validation."""
    week: int
    accuracy: float
    log_loss: float
    auc: float
    brier_score: float
    total_games: int
    correct_predictions: int
    avg_confidence: float
    calibration_error: float


class WalkForwardValidator:
    """
    Encapsulates walk-forward validation logic from validate_weekly.py.
    
    This class isolates the complex stateful simulation loop and provides
    methods for analyzing results across multiple dimensions.
    
    Consolidates: validate_weekly.py (1,123 lines)
    """
    
    def __init__(
        self,
        model_trainer,
        logger=None,
        temporal_validator=None,
        db_service=None,
        bucket_adapter=None
    ):
        """
        Initialize walk-forward validator.
        
        Args:
            model_trainer: Model trainer instance
            logger: Logger instance
            temporal_validator: Temporal validator for safety checks
            db_service: Database service for data loading
            bucket_adapter: Bucket adapter for feature loading
        """
        self.trainer = model_trainer
        self.logger = logger or get_logger(__name__)
        self.temporal_validator = temporal_validator or TemporalValidator()
        self.db_service = db_service or get_database_router(self.logger)
        self.bucket_adapter = bucket_adapter or get_bucket_adapter(self.logger)
        
        # State storage
        self.week_models = {}  # {week: model}
        self.week_predictions = {}  # {week: predictions_df}
        self.week_metrics = {}  # {week: WeekMetrics}
        self.feature_importance_by_week = {}  # {week: importance_dict}
        
        self.logger.info("WalkForwardValidator initialized")

    def run_validation(self, year: int, baseline_year: int = 2000) -> pd.DataFrame:
        """
        Run week-by-week walk-forward validation for specified year.
        
        This is the main orchestrator that replicates the core loop from
        validate_weekly.py (lines 45-320).
        
        Args:
            year: Year to validate (e.g., 2024)
            baseline_year: Starting year for training data
        
        Returns:
            DataFrame with weekly metrics
        """
        start_time = time.time()
        self.logger.info(f"Starting walk-forward validation for {year}")
        
        # Reset state
        self.week_models = {}
        self.week_predictions = {}
        self.week_metrics = {}
        self.feature_importance_by_week = {}
        
        # Calculate training seasons
        train_end_year = year - 1
        base_train_seasons = f'{baseline_year}-{train_end_year}'
        
        # Track cumulative completed weeks for walk-forward
        cumulative_test_weeks = []
        weekly_results = []
        
        # Validate each week (1-18 for regular season)
        for week in range(1, 19):
            self.logger.info(f"Validating week {week}/{18}")
            
            # Determine training configuration
            if week == 1:
                # Week 1: Only historical data (baseline)
                train_seasons = base_train_seasons
                train_weeks = None
            else:
                # Week 2+: Historical + completed test year weeks
                train_seasons = f'{base_train_seasons},{year}'
                train_weeks = {year: cumulative_test_weeks.copy()}
            
            try:
                metrics = self._validate_week(year, week, train_seasons, train_weeks)
                weekly_results.append(metrics)
                
                # Add current week to cumulative list for next iteration
                cumulative_test_weeks.append(week)
                
                # Log progress
                self.logger.info(
                    f"Week {week}: Accuracy={metrics.accuracy:.3f}, "
                    f"LogLoss={metrics.log_loss:.3f}, AUC={metrics.auc:.3f}"
                )
                
            except ValueError as e:
                if "No test data found" in str(e):
                    self.logger.info(f"Stopping validation at week {week}: No test data available.")
                    break
                else:
                    self.logger.error(f"Error validating week {week}: {e}")
                    continue
            except Exception as e:
                self.logger.error(f"Error validating week {week}: {e}")
                # Continue with next week
                continue
        
        # Convert to DataFrame
        results_df = pd.DataFrame([vars(m) for m in weekly_results])
        
        duration = time.time() - start_time
        
        if not results_df.empty:
            self.logger.info(
                f"Walk-forward validation completed in {duration:.2f}s. "
                f"Overall accuracy: {results_df['accuracy'].mean():.3f}"
            )
        else:
            self.logger.warning(f"Walk-forward validation completed in {duration:.2f}s with no results.")
        
        return results_df
    
    def _validate_week(self, year: int, week: int, train_seasons: str, train_weeks: Optional[Dict] = None) -> WeekMetrics:
        """
        Validate a single week using walk-forward approach via ModelTrainer.
        
        Args:
            year: Year being validated
            week: Week number (1-18)
            train_seasons: Training seasons string
            train_weeks: Optional dict of weeks to include in training
        
        Returns:
            WeekMetrics for this week
        """
        # Delegate to ModelTrainer
        result = self.trainer.train_model(
            model_class=GameOutcomeModel,
            train_seasons=train_seasons,
            train_weeks=train_weeks,
            test_seasons=str(year),
            test_week=week,
            save_model=False,
            return_correlations=False,
            return_predictions=True
        )
        
        if result['status'] != 'success':
            raise ValueError(f"Training failed: {result.get('message')}")
            
        # Extract components
        model = result['model']
        predictions = result['predictions']
        metrics_dict = result['metrics']
        
        # Store model
        self.week_models[week] = model
        
        # Store predictions (rename columns to match expected format)
        predictions = predictions.rename(columns={
            'prediction': 'predicted',
            'home_team_won': 'actual',
            'home_win_prob': 'win_prob'
        })
        self.week_predictions[week] = predictions
        
        # Extract feature importance
        if 'feature_importance' in metrics_dict:
            # Convert list of dicts to dict
            importance_dict = {item['feature']: item['importance'] for item in metrics_dict['feature_importance']}
            self.feature_importance_by_week[week] = importance_dict
            
        # Calculate additional metrics (calibration error, etc.)
        # We need to reconstruct y_true and y_pred_prob from predictions
        y_true = np.array(predictions['actual'].values, dtype=int)
        y_pred_prob = np.array(predictions['win_prob'].values, dtype=float)
        
        calibration_error = self._calculate_calibration_error(y_true, y_pred_prob)
        
        # Create WeekMetrics
        return WeekMetrics(
            week=week,
            accuracy=metrics_dict['accuracy'],
            log_loss=metrics_dict.get('log_loss', 0.0), # ModelTrainer might not return log_loss
            auc=metrics_dict['auc'],
            brier_score=metrics_dict.get('brier_score', 0.0),
            total_games=result['test_size'],
            correct_predictions=int(metrics_dict['accuracy'] * result['test_size']),
            avg_confidence=float(y_pred_prob.mean()),
            calibration_error=calibration_error
        )
    
    def _calculate_calibration_error(
        self,
        y_true: np.ndarray,
        y_pred_prob: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """
        Calculate Expected Calibration Error (ECE).
        
        Args:
            y_true: True labels
            y_pred_prob: Predicted probabilities
            n_bins: Number of bins for calibration
        
        Returns:
            ECE value
        """
        bins = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(y_pred_prob, bins) - 1
        
        ece = 0.0
        for i in range(n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                bin_accuracy = y_true[mask].mean()
                bin_confidence = y_pred_prob[mask].mean()
                bin_weight = mask.sum() / len(y_true)
                ece += bin_weight * abs(bin_accuracy - bin_confidence)
        
        return ece

    def analyze_feature_importance(self) -> pd.DataFrame:
        """
        Aggregate feature importance across all weeks.
        
        Consolidates: validate_weekly.py lines 325-480
        
        Returns:
            DataFrame with feature importance rankings
        """
        if not self.feature_importance_by_week:
            self.logger.warning("No feature importance data available")
            return pd.DataFrame()
        
        # Convert to DataFrame
        importance_df = pd.DataFrame(self.feature_importance_by_week).T
        
        # Calculate aggregate statistics
        importance_stats = pd.DataFrame({
            'mean_importance': importance_df.mean(),
            'std_importance': importance_df.std(),
            'min_importance': importance_df.min(),
            'max_importance': importance_df.max(),
            'weeks_in_top10': (importance_df.rank(ascending=False, axis=1) <= 10).sum(axis=0)
        }).sort_values('mean_importance', ascending=False)
        
        return importance_stats
    
    def analyze_miss_patterns(self) -> Dict[str, pd.DataFrame]:
        """
        Identify systematic prediction misses.
        
        Consolidates: validate_weekly.py lines 485-680
        
        Analyzes:
        - Which teams are hardest to predict
        - Which matchups cause issues
        - Home/away patterns
        - Confidence vs accuracy relationship
        
        Returns:
            Dictionary containing DataFrames for different miss patterns
        """
        if not self.week_predictions:
            self.logger.warning("No prediction data available")
            return {}
        
        # Combine all predictions
        all_predictions = pd.concat(self.week_predictions.values(), ignore_index=True)
        
        # Identify misses
        all_predictions['miss'] = all_predictions['predicted'] != all_predictions['actual']
        all_predictions['correct'] = ~all_predictions['miss']
        
        # Team-level miss patterns
        team_patterns = []
        
        for team in all_predictions['home_team'].unique():
            team_games = all_predictions[
                (all_predictions['home_team'] == team) | 
                (all_predictions['away_team'] == team)
            ]
            
            team_patterns.append({
                'team': team,
                'total_games': len(team_games),
                'misses': team_games['miss'].sum(),
                'miss_rate': team_games['miss'].mean(),
                'avg_confidence_when_wrong': team_games[team_games['miss']]['confidence'].mean(),
                'avg_confidence_when_right': team_games[team_games['correct']]['confidence'].mean()
            })
        
        team_df = pd.DataFrame(team_patterns).sort_values('miss_rate', ascending=False)
        
        # Matchup patterns
        matchup_patterns = all_predictions.groupby(['home_team', 'away_team']).agg({
            'miss': ['sum', 'mean'],
            'game_id': 'count'
        }).reset_index()
        matchup_patterns.columns = ['home_team', 'away_team', 'total_misses', 'miss_rate', 'games']
        matchup_patterns = matchup_patterns[matchup_patterns['games'] >= 2]  # At least 2 games
        matchup_patterns = matchup_patterns.sort_values('miss_rate', ascending=False)
        
        # Location patterns
        if 'location' in all_predictions.columns:
            location_patterns = all_predictions.groupby('location').agg({
                'miss': ['sum', 'mean'],
                'confidence': 'mean',
                'game_id': 'count'
            })
        else:
            self.logger.warning("Location column not found in predictions. Skipping location pattern analysis.")
            location_patterns = pd.DataFrame()
        
        return {
            'team_patterns': team_df,
            'matchup_patterns': matchup_patterns.head(20),
            'location_patterns': location_patterns
        }
    
    def analyze_correlations(self) -> pd.DataFrame:
        """
        Analyze feature correlations with prediction errors.
        
        Consolidates: validate_weekly.py lines 685-890
        
        Identifies features that correlate with:
        - Prediction errors
        - Overconfidence
        - Underconfidence
        
        Returns:
            DataFrame with correlation analysis
        """
        if not self.week_predictions:
            self.logger.warning("No prediction data available")
            return pd.DataFrame()
        
        # Combine all predictions with features
        all_data = []
        
        for week, predictions in self.week_predictions.items():
            # Predictions already contain features from ModelTrainer
            merged = predictions.copy()
            merged['prediction_error'] = abs(merged['win_prob'] - merged['actual'])
            merged['overconfident'] = (merged['win_prob'] > 0.7) & (merged['actual'] == 0)
            merged['underconfident'] = (merged['win_prob'] < 0.3) & (merged['actual'] == 1)
            
            all_data.append(merged)
        
        combined = pd.concat(all_data, ignore_index=True)
        
        # Get feature columns (exclude metadata)
        feature_cols = [col for col in combined.columns if col.startswith(('avg_', 'diff_', 'ctx_'))]
        
        # Calculate correlations with prediction error
        error_correlations = combined[feature_cols].corrwith(combined['prediction_error'])
        
        # Calculate correlations with overconfidence
        overconfident_correlations = combined[feature_cols].corrwith(combined['overconfident'].astype(int))
        
        # Combine into analysis DataFrame
        correlation_analysis = pd.DataFrame({
            'feature': feature_cols,
            'error_correlation': error_correlations.values,
            'overconfident_correlation': overconfident_correlations.values,
            'abs_error_correlation': error_correlations.abs().values
        }).sort_values('abs_error_correlation', ascending=False)
        
        return correlation_analysis
    
    def get_summary_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary report.
        
        Consolidates: validate_weekly.py lines 1000-1123
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.week_metrics:
            return {'error': 'No validation data available'}
        
        # Convert metrics to DataFrame
        metrics_df = pd.DataFrame([vars(m) for m in self.week_metrics.values()])
        
        # Overall statistics
        summary = {
            'overall_accuracy': metrics_df['accuracy'].mean(),
            'overall_log_loss': metrics_df['log_loss'].mean(),
            'overall_auc': metrics_df['auc'].mean(),
            'overall_brier_score': metrics_df['brier_score'].mean(),
            'total_games': metrics_df['total_games'].sum(),
            'total_correct': metrics_df['correct_predictions'].sum(),
            'best_week': {
                'week': metrics_df.loc[metrics_df['accuracy'].idxmax(), 'week'],
                'accuracy': metrics_df['accuracy'].max()
            },
            'worst_week': {
                'week': metrics_df.loc[metrics_df['accuracy'].idxmin(), 'week'],
                'accuracy': metrics_df['accuracy'].min()
            },
            'accuracy_std': metrics_df['accuracy'].std(),
            'avg_calibration_error': metrics_df['calibration_error'].mean()
        }
        
        # Week-by-week trends
        summary['weekly_trend'] = {
            'early_season_accuracy': metrics_df[metrics_df['week'] <= 6]['accuracy'].mean(),
            'mid_season_accuracy': metrics_df[(metrics_df['week'] > 6) & (metrics_df['week'] <= 12)]['accuracy'].mean(),
            'late_season_accuracy': metrics_df[metrics_df['week'] > 12]['accuracy'].mean()
        }
        
        return summary


class ModelDiagnosticsImpl:
    """
    Centralized model diagnostics and validation.
    
    Consolidates functionality from:
    - analyze_variance.py (182 lines)
    - validate_weekly.py (1,123 lines) - via WalkForwardValidator
    - diagnose_ensemble.py (129 lines)
    - inspect_predictions.py (182 lines)
    """
    
    def __init__(
        self,
        db_service=None,
        logger=None,
        bucket_adapter=None,
        model_trainer=None
    ):
        """
        Initialize model diagnostics service.
        
        Args:
            db_service: Database service
            logger: Logger instance
            bucket_adapter: Bucket adapter
            model_trainer: Model trainer instance
        """
        self.logger = logger or get_logger(__name__)
        self.db_service = db_service or get_database_router(self.logger)
        self.bucket_adapter = bucket_adapter or get_bucket_adapter(logger=self.logger)
        self.model_trainer = model_trainer  # Lazy load if needed
        
        self.logger.info("ModelDiagnosticsImpl initialized")
    
    def _get_trainer(self):
        """Lazy load model trainer."""
        if self.model_trainer is None:
            self.model_trainer = create_model_trainer(self.logger)
        return self.model_trainer
    
    def run_diagnostics(self, **kwargs) -> Dict[str, Any]:
        """
        Orchestrator for all model diagnostics.
        
        Args:
            **kwargs: Arguments for specific diagnostics
        
        Returns:
            Dictionary with all diagnostic results
        """
        self.logger.info("Running model diagnostics suite")
        
        results = {}
        
        # Run each diagnostic
        if kwargs.get('variance'):
            results['variance_analysis'] = self.analyze_variance(**kwargs)
        
        if kwargs.get('weekly'):
            results['weekly_validation'] = self.validate_weekly_performance(**kwargs)
        
        if kwargs.get('ensemble'):
            results['ensemble_diagnosis'] = self.diagnose_ensemble(**kwargs)
        
        if kwargs.get('predictions'):
            results['prediction_inspection'] = self.inspect_latest_predictions(**kwargs)
        
        return results
    
    def analyze_variance(
        self,
        start_year: int = 2022,
        end_year: int = 2024
    ) -> Dict[str, Any]:
        """
        Analyze prediction variance across teams, divisions, and season phases.
        
        Consolidates: analyze_variance.py (182 lines)
        
        Args:
            start_year: Start year for analysis
            end_year: End year for analysis
        
        Returns:
            Dictionary with variance analysis
        """
        self.logger.info(f"Analyzing variance for {start_year}-{end_year}")
        
        # MATCH ORIGINAL: Generate predictions on-the-fly like analyze_variance.py
        # Original script doesn't read saved predictions - it generates them!
        trainer = self._get_trainer()
        all_predictions = []
        
        # Generate predictions for each season using walk-forward approach
        for year in range(start_year, end_year + 1):
            self.logger.info(f"Processing {year} season...")
            
            # Train on history up to year-1
            train_seasons = f"2000-{year-1}"
            cumulative_test_weeks = []
            
            # Iterate through weeks like original script (lines 54-89)
            for week in range(1, 23):  # Include playoffs like original
                try:
                    # Define training data (walk-forward)
                    if week == 1:
                        train_seasons_str = train_seasons
                        train_weeks = None
                    else:
                        train_seasons_str = f"{train_seasons},{year}"
                        train_weeks = {year: cumulative_test_weeks.copy()}
                    
                    # Train & Predict (delegate to ModelTrainer)
                    result = trainer.train_model(
                        model_class=GameOutcomeModel,
                        train_seasons=train_seasons_str,
                        train_weeks=train_weeks,
                        test_seasons=str(year),
                        test_week=week,
                        save_model=False,
                        return_predictions=True
                    )
                    
                    if result['status'] == 'success' and 'predictions' in result:
                        preds = result['predictions']
                        preds['season'] = year
                        preds['week'] = week
                        all_predictions.append(preds)
                        cumulative_test_weeks.append(week)
                        self.logger.debug(f"  Week {week}: {len(preds)} games predicted")
                    
                except ValueError as e:
                    if "No test data found" in str(e):
                        # End of season reached
                        break
                    self.logger.warning(f"  Week {week} failed: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"  Week {week} error: {e}")
                    continue
        
        if not all_predictions:
            raise ValueError(
                f"No predictions generated for {start_year}-{end_year}. "
                f"Check that training data is available in bucket."
            )
        
        # Combine all predictions
        df = pd.concat(all_predictions, ignore_index=True)
        self.logger.info(f"Total games analyzed: {len(df)}")
        
        # Calculate accuracy metrics (match original script lines 100-103)
        df['correct'] = (df['prediction'] == df['home_team_won']).astype(int)
        df['brier_score'] = (df['home_win_prob'] - df['home_team_won']) ** 2
        
        # Stack home and away to get per-team stats (match original lines 108-118)
        home_df = df[['season', 'week', 'home_team', 'correct', 'brier_score']].rename(
            columns={'home_team': 'team'}
        )
        away_df = df[['season', 'week', 'away_team', 'correct', 'brier_score']].rename(
            columns={'away_team': 'team'}
        )
        team_df = pd.concat([home_df, away_df], ignore_index=True)
        
        # Team-level variance
        team_variance = team_df.groupby('team').agg({
            'correct': ['count', 'mean'],
            'brier_score': 'mean'
        })
        team_variance.columns = ['games', 'accuracy', 'brier_score']
        team_variance = team_variance.sort_values('accuracy')
        
        # Season phase variance (match original lines 133-143)
        df['phase'] = df['week'].apply(lambda w: 'Early (1-5)' if w <= 5 else 'Late (6+)')
        phase_variance = df.groupby('phase').agg({
            'correct': ['count', 'mean'],
            'brier_score': 'mean'
        })
        phase_variance.columns = ['games', 'accuracy', 'brier_score']
        
        # Early season team variance (match original lines 146-157)
        team_df['phase'] = team_df['week'].apply(lambda w: 'Early' if w <= 5 else 'Late')
        early_team_stats = team_df[team_df['phase'] == 'Early'].groupby('team').agg({
            'correct': ['count', 'mean']
        })
        early_team_stats.columns = ['games', 'accuracy']
        early_team_stats = early_team_stats[early_team_stats['games'] >= 5]  # Min sample
        early_team_stats = early_team_stats.sort_values('accuracy')
        
        # Build results matching original script structure (lines 120-178)
        results = {
            'total_games': len(df),
            'overall_accuracy': df['correct'].mean(),
            'overall_brier': df['brier_score'].mean(),
            'team_variance': team_variance.to_dict('index'),
            'phase_variance': phase_variance.to_dict('index'),
            'early_team_variance': early_team_stats.to_dict('index')
        }
        
        # Log summary like original
        self.logger.info(f"\nOverall Accuracy: {results['overall_accuracy']:.3f}")
        self.logger.info(f"Overall Brier Score: {results['overall_brier']:.3f}")
        self.logger.info(f"\nMost unpredictable teams:")
        for team in team_variance.head(5).index:
            acc = team_variance.loc[team, 'accuracy']
            self.logger.info(f"  {team}: {acc:.3f}")
        
        return results
    
    def validate_weekly_performance(self, test_year: int) -> Dict[str, Any]:
        """
        Perform walk-forward validation for a season.
        
        Consolidates: validate_weekly.py (1,123 lines)
        Delegates to: WalkForwardValidator
        
        Args:
            test_year: Year to validate
        
        Returns:
            Dictionary with validation results and analysis
        """
        self.logger.info(f"Starting weekly validation for {test_year}")
        
        # Create validator
        validator = WalkForwardValidator(
            model_trainer=self._get_trainer(),
            logger=self.logger,
            db_service=self.db_service,
            bucket_adapter=self.bucket_adapter
        )
        
        # Run validation
        weekly_results = validator.run_validation(test_year)
        
        # Perform analyses
        feature_importance = validator.analyze_feature_importance()
        miss_patterns = validator.analyze_miss_patterns()
        correlations = validator.analyze_correlations()
        summary = validator.get_summary_report()
        
        return {
            'weekly_metrics': weekly_results.to_dict(),
            'feature_importance': feature_importance.to_dict(),
            'miss_patterns': miss_patterns,
            'correlations': correlations.to_dict(),
            'summary': summary
        }
    
    def diagnose_ensemble(
        self,
        train_seasons: str = "2000-2023",
        test_season: int = 2024
    ) -> Dict[str, Any]:
        """
        Diagnose ensemble model components by training fresh and inspecting.
        
        Consolidates: diagnose_ensemble.py (129 lines)
        
        CRITICAL: Trains ensemble from scratch like original script (lines 20-58),
        then inspects component predictions (lines 60-126).
        
        Args:
            train_seasons: Training seasons range (default: 2000-2023)
            test_season: Test season for component inspection
        
        Returns:
            Dictionary with ensemble diagnostics
        """
        self.logger.info("Diagnosing ensemble model")
        
        # MATCH ORIGINAL: Train ensemble fresh like diagnose_ensemble.py
        from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeEnsemble
        from sklearn.metrics import roc_auc_score, brier_score_loss
        
        trainer = self._get_trainer()
        
        # Train ensemble for test season (match original lines 24-58)
        self.logger.info(f"Training ensemble on {train_seasons}, testing on {test_season}")
        
        result = trainer.train_model(
            model_class=GameOutcomeModel,
            train_seasons=train_seasons,
            test_seasons=str(test_season),
            save_model=False,
            return_predictions=True
        )
        
        if result['status'] != 'success':
            return {
                'error': 'Training failed',
                'message': result.get('message', 'Unknown error'),
                'recommendation': 'Check training data availability'
            }
        
        # Extract components (match original lines 60-85)
        ensemble = result['model']
        X_test = result.get('X_test')
        y_test = result.get('y_test')
        test_metadata = result.get('test_metadata', {})
        
        if X_test is None or y_test is None:
            return {
                'error': 'Test data not available',
                'message': 'Model trainer did not return X_test/y_test',
                'recommendation': 'Ensure return_predictions=True includes test data'
            }
        
        # Generate component predictions
        self.logger.info("Generating component predictions...")
        
        # XGBoost
        xgb_prob = ensemble.xgboost_model.predict_proba(X_test)[:, 1]
        
        # Elastic Net (clip to 0-1)
        en_pred = ensemble.elastic_net_model.predict(X_test)
        en_prob = np.clip(en_pred, 0, 1)
        
        # Logistic Regression
        lr_prob = ensemble.logistic_model.predict_proba(X_test)[:, 1]
        
        # Ensemble weighted average
        ensemble_prob = ensemble.predict_proba(X_test)[:, 1]
        
        # Build results DataFrame (match original lines 77-85)
        results_df = pd.DataFrame({
            'xgb_prob': xgb_prob,
            'en_prob': en_prob,
            'lr_prob': lr_prob,
            'ensemble_prob': ensemble_prob,
            'actual': y_test.values
        })
        
        # Component correlations (match original lines 88-90)
        correlations = results_df[['xgb_prob', 'en_prob', 'lr_prob']].corr()
        
        # Weight verification (match original lines 93-104)
        expected_weights = {'xgboost': 0.5, 'elasticnet': 0.3, 'logistic': 0.2}
        manual_calc = (
            0.5 * results_df['xgb_prob'] +
            0.3 * results_df['en_prob'] +
            0.2 * results_df['lr_prob']
        )
        weight_diff = (results_df['ensemble_prob'] - manual_calc).abs()
        max_weight_error = weight_diff.max()
        
        # Component performance (match original lines 107-119)
        component_performance = {
            'xgboost': {
                'auc': roc_auc_score(y_test, xgb_prob),
                'brier_score': brier_score_loss(y_test, xgb_prob),
                'std_dev': float(xgb_prob.std())
            },
            'elasticnet': {
                'auc': roc_auc_score(y_test, en_prob),
                'brier_score': brier_score_loss(y_test, en_prob),
                'std_dev': float(en_prob.std())
            },
            'logistic': {
                'auc': roc_auc_score(y_test, lr_prob),
                'brier_score': brier_score_loss(y_test, lr_prob),
                'std_dev': float(lr_prob.std())
            },
            'ensemble': {
                'auc': roc_auc_score(y_test, ensemble_prob),
                'brier_score': brier_score_loss(y_test, ensemble_prob),
                'std_dev': float(ensemble_prob.std())
            }
        }
        
        # Log summary like original
        self.logger.info("\n=== Component Performance (AUC) ===")
        for comp, metrics in component_performance.items():
            self.logger.info(f"{comp}: {metrics['auc']:.4f}")
        
        self.logger.info(f"\nMax weight error: {max_weight_error:.6f}")
        
        return {
            'component_correlations': correlations.to_dict(),
            'weight_verification': {
                'expected_weights': expected_weights,
                'max_error': float(max_weight_error),
                'mean_error': float(weight_diff.mean()),
                'weights_valid': max_weight_error < 0.01
            },
            'component_performance': component_performance,
            'test_games': len(y_test)
        }
    
    def inspect_latest_predictions(self, limit: int = 10) -> Dict[str, Any]:
        """
        Inspect recent prediction files.
        
        Consolidates: inspect_predictions.py (182 lines)
        
        Args:
            limit: Number of recent files to inspect
        
        Returns:
            Dictionary with prediction inspection results
        """
        self.logger.info(f"Inspecting latest {limit} prediction files")
        
        # List prediction files using BucketAdapter.list_files()
        prediction_files = self.bucket_adapter.list_files(prefix='ml/predictions/')
        
        if not prediction_files:
            return {
                'error': 'No prediction files found',
                'message': 'No predictions in ml/predictions/ path',
                'recommendation': 'Generate predictions first: quantcup nflfastrv3 ml predict'
            }
        
        # Filter to parquet files only
        parquet_files = [f for f in prediction_files if f.endswith('.parquet')]
        
        # Sort by filename (timestamp in filename) and get most recent
        recent_files = sorted(parquet_files, reverse=True)[:limit]
        
        # Inspect each file
        inspections = []
        for file_key in recent_files:
            try:
                df = self.bucket_adapter._read_single_parquet(file_key)
                
                inspection = {
                    'file': file_key,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'has_game_id': 'game_id' in df.columns,
                    'has_probabilities': 'home_win_prob' in df.columns,
                    'date_range': f"{df['game_date'].min()} to {df['game_date'].max()}" if 'game_date' in df.columns else 'N/A'
                }
                inspections.append(inspection)
                
            except Exception as e:
                self.logger.warning(f"Could not inspect {file_key}: {e}")
                inspections.append({
                    'file': file_key,
                    'error': str(e)
                })
        
        self.logger.info(f"Inspected {len(inspections)} prediction files")
        
        return {
            'status': 'success',
            'files_inspected': len(inspections),
            'inspections': inspections,
            'total_prediction_files': len(parquet_files)
        }