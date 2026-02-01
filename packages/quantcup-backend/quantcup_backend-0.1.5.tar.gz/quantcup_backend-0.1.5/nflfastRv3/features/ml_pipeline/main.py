"""
ML Pipeline Implementation

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

Follows clean architecture with maximum 3 layers:
Layer 1: Public API (nflfastRv3/__init__.py)
Layer 2: This implementation
Layer 3: Infrastructure (database, model storage)

"Can I Trace This?" test:
User calls run_ml_pipeline() → MLPipelineImpl.process() → Database/Model services
✅ 3 layers, easily traceable
"""

from datetime import datetime
from typing import Any, Optional, Dict, Type
from ...shared.database_router import get_database_router
from .orchestrators.feature_orchestrator import create_feature_engineer
from .orchestrators.model_trainer import create_model_trainer
from .orchestrators.predictor import create_predictor
from .models.game_lines.game_outcome import GameOutcomeModel


class MLPipelineImpl:
    """
    Core ML pipeline business logic.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + orchestration)
    Depth: 1 layer (calls implementation components)
    
    """
    
    def __init__(self, db_service, logger):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        
        # Initialize ML components (Layer 2 - Implementation components)
        self.feature_engineer = create_feature_engineer(db_service, logger)
        self.model_trainer = create_model_trainer(db_service, logger)
        self.predictor = create_predictor(logger)
    
    def process(self, train_seasons, feature_sets=None,
               generate_predictions=True, prediction_week=None, prediction_season=None):
        """
        Execute complete ML pipeline workflow.
        
        Real ML flow (migrated from V2):
        1. Engineer features (FeatureEngineer)
        2. Train models (ModelTrainer)
        3. Generate predictions (Predictor)
        4. Return comprehensive summary
        
        Args:
            train_seasons: Seasons for training (e.g., '2020-2023')
            feature_sets: Feature sets to build ['team_efficiency', 'rolling_metrics', 'opponent_adjusted']
            generate_predictions: Whether to generate predictions after training
            prediction_week: Week to predict (default: current week)
            prediction_season: Season to predict (default: current season)
            
        Returns:
            dict: Complete ML pipeline summary
        """
        feature_sets = feature_sets or ['team_efficiency', 'rolling_metrics', 'opponent_adjusted']
        
        self.logger.info(f"Starting ML pipeline: seasons={train_seasons}, features={feature_sets}")
        
        try:
            total_start_time = datetime.now()
            
            # Step 1: Feature Engineering (Layer 2 call)
            # Note: Feature engineer will handle season parsing internally
            self.logger.info("Step 1: Building ML features")
            features_result = self.feature_engineer.build_features(
                feature_sets=feature_sets,
                seasons=None  # Build all available seasons for full pipeline
            )
            
            if features_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f"Feature engineering failed: {features_result.get('message', 'Unknown error')}",
                    'pipeline_stage': 'feature_engineering'
                }
            
            # Step 2: Model Training (Layer 2 call)
            self.logger.info("Step 2: Training ML models")
            training_result = self.model_trainer.train_model(
                model_class=GameOutcomeModel,
                train_seasons=train_seasons,
                save_model=True,
                auto_build_features=False  # Features already built in Step 1
            )
            
            if training_result['status'] != 'success':
                return {
                    'status': 'error', 
                    'message': f"Model training failed: {training_result.get('message', 'Unknown error')}",
                    'pipeline_stage': 'model_training',
                    'features_result': features_result
                }
            
            # Step 3: Generate Predictions (Layer 2 call - optional)
            prediction_result = None
            if generate_predictions:
                self.logger.info("Step 3: Generating predictions")
                
                # Default to current week/season if not specified
                current_date = datetime.now()
                pred_season = prediction_season or current_date.year
                pred_week = prediction_week or min(18, max(1, current_date.isocalendar()[1] - 35))
                
                # Note: process() currently hardcodes game_outcome for backward compatibility
                # For multi-model predictions, use predict() directly with explicit model_name
                prediction_result = self.predictor.generate_predictions(
                    model_name='game_outcome',  # TODO: Make configurable via process() params
                    week=pred_week,
                    season=pred_season,
                    save_predictions=True
                )
                
                if prediction_result['status'] != 'success':
                    self.logger.warning(f"Prediction generation failed: {prediction_result.get('message')}")
            
            # Step 4: Calculate pipeline summary
            total_duration = datetime.now() - total_start_time
            
            self.logger.info("✅ ML pipeline completed successfully")
            
            # Extract metrics safely with proper type handling
            metrics = training_result.get('metrics', {})
            training_accuracy = metrics.get('accuracy') if isinstance(metrics, dict) else None
            training_auc = metrics.get('auc') if isinstance(metrics, dict) else None
            
            return {
                'status': 'success',
                'pipeline_duration': str(total_duration),
                'model_path': training_result.get('model_path'),
                'features_built': features_result.get('features_built', 0),
                'total_features_rows': features_result.get('total_rows', 0),
                'training_accuracy': training_accuracy,
                'training_auc': training_auc,
                'predictions_generated': prediction_result.get('num_predictions', 0) if prediction_result else 0,
                'results': {
                    'feature_engineering': features_result,
                    'model_training': training_result,
                    'predictions': prediction_result
                }
            }
            
        except Exception as e:
            self.logger.error(f"ML pipeline failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'pipeline_stage': 'orchestration'
            }
    
    def build_features_only(self, feature_sets=None, seasons=None):
        """
        Run only feature engineering step.
        
        Args:
            feature_sets: Feature sets to build ['team_efficiency', 'rolling_metrics', 'opponent_adjusted']
            seasons: Seasons to build for (list of ints, or None for all available seasons in warehouse)
            
        Returns:
            dict: Feature engineering results
        """
        self.logger.info("Running feature engineering only")
        return self.feature_engineer.build_features(feature_sets, seasons)
    
    def train_model_only(self, model_name: Optional[str] = None, train_years: Optional[int] = None,
                        test_year: Optional[int] = None, test_week: Optional[int] = None,
                        model_class: Optional[Type[Any]] = None, tag: Optional[str] = None,
                        dry_run: bool = False, auto_build_features: bool = True,
                        force: bool = False, random_state: int = 42, **kwargs):
        """
        Run only model training step (always uses enhanced v2 trainer).
        
        ARCHITECTURAL NOTE: This method returns training data WITHOUT generating reports.
        Report generation is delegated to the CLI layer where operation context is known.
        
        This design prevents duplicate reports during batch operations (backtesting, optimization)
        while allowing single runs to generate detailed reports. The CLI layer decides:
        - _handle_train(): Generates detailed training report (single run)
        - _handle_backtest(): Generates aggregated backtest report (batch run)
        - _handle_optimize_window(): Generates aggregated optimization report (batch run)
        
        Training Mode:
        - Production (Relative): Uses train_years to automatically calculate training window
        
        Enhanced Features (always enabled):
        - Temporal leakage validation (prevents training on incomplete future weeks)
        - Dry-run preview mode (preview without training)
        - Auto feature building (ensure required features exist)
        - Model versioning and metadata tracking
        
        Args:
            model_name: Model to train (e.g., 'game_outcome', 'spread_prediction', 'total_points')
            train_years: Number of years to train on before test period
            test_year: Year to test on (default: current year)
            test_week: Specific week to test (1-22)
            model_class: Model class to train (deprecated - use model_name instead)
            tag: Version tag (e.g., 'week9_3yr', 'latest')
            dry_run: Preview training config without executing (default: False)
            auto_build_features: Auto-build missing features (default: True)
            force: Force training even with temporal leakage warning (default: False)
            **kwargs: Deprecated - use explicit parameters instead
            
        Returns:
            dict: Model training results with all data needed for external reporting
        """
        # Get model class from registry
        if model_class is None:
            from .models import MODEL_REGISTRY
            
            if not model_name:
                raise ValueError(
                    "model_name is required. "
                    f"Available models: {', '.join(MODEL_REGISTRY.keys())}"
                )
            
            if model_name not in MODEL_REGISTRY:
                raise ValueError(
                    f"Invalid model: {model_name}. "
                    f"Available models: {', '.join(MODEL_REGISTRY.keys())}"
                )
            
            model_class = MODEL_REGISTRY[model_name]['class']
            self.logger.info(f"Using model from registry: {model_name}")
        
        # Ensure model_class is not None at this point
        assert model_class is not None, "model_class must be provided either directly or via model_name"
        
        # ========================================
        # VALIDATE ARGUMENTS & CALCULATE TRAINING WINDOW
        # ========================================
        
        from commonv2.domain.schedules import SeasonParser
        from .config.training_modes import VALIDATION_CONSTRAINTS
        
        # Validate required args
        if train_years is None:
            raise ValueError(
                "Training requires --train-years. "
                "Example: --train-years 5 --test-year 2024"
            )
        
        # Determine test period using NFL-aware logic
        final_test_year = test_year or SeasonParser.get_current_season(self.logger)
        
        # Validate test_year range using config constraints
        year_constraints = VALIDATION_CONSTRAINTS['test_year']
        max_year = datetime.now().year + year_constraints['max_offset_from_now']
        if final_test_year < year_constraints['min'] or final_test_year > max_year:
            raise ValueError(
                f"Invalid test year: {final_test_year}. "
                f"Must be between {year_constraints['min']} and {max_year}"
            )
        
        final_test_week = test_week
        final_test_seasons = str(final_test_year)
        
        # Validate week if specified using config constraints
        if final_test_week is not None:
            week_constraints = VALIDATION_CONSTRAINTS['test_week']
            if not week_constraints['min'] <= final_test_week <= week_constraints['max']:
                raise ValueError(
                    f"Invalid week: {final_test_week}. "
                    f"Must be {week_constraints['min']}-{week_constraints['max']} (includes playoffs)."
                )
        
        # Calculate training window
        start_year = final_test_year - train_years
        end_year = final_test_year - 1  # Exclude test year
        
        if start_year >= end_year:
            raise ValueError(
                f"Invalid training window: {start_year}-{end_year}. "
                f"Need at least 1 year of training data. "
                f"Try increasing --train-years or adjusting --test-year."
            )
        
        final_train_seasons = f"{start_year}-{end_year}"
        
        self.logger.info("🚀 Training with relative window (most recent data)")
        self.logger.info(f"   Train seasons: {final_train_seasons} ({train_years} years)")
        self.logger.info(f"   Test seasons: {final_test_seasons}" +
                       (f" week {final_test_week}" if final_test_week else " (full season)"))
        
        # ========================================
        # EXECUTE TRAINING (always uses enhanced trainer)
        # ========================================
        
        self.logger.info(f"Running {model_class.MODEL_NAME} training with v2 enhancements")
        result: Dict[str, Any] = self.model_trainer.train_model(
            model_class=model_class,
            train_seasons=final_train_seasons,
            test_seasons=final_test_seasons or final_train_seasons,
            test_week=final_test_week,
            tag=tag,
            dry_run=dry_run,
            auto_build_features=auto_build_features,
            force=force,
            random_state=random_state
        )
        
        # Store season info for external reporting (needed by CLI layer)
        if result.get('status') == 'success':
            result['train_seasons_str'] = final_train_seasons
            result['test_seasons_str'] = final_test_seasons or final_train_seasons
            if final_test_week is not None:
                result['test_week'] = final_test_week
        
        # NO report generation here - handled at CLI layer (context-aware)
        # CLI _handle_train() generates reports for single runs
        # CLI _handle_backtest() generates aggregated backtest reports
        # CLI _handle_optimize_window() generates aggregated optimization reports
        
        return result
    
    def predict(self, model_name, week=None, season=None, model_version='latest'):
        """
        Run only prediction generation step.
        
        Args:
            model_name: Model to use (required - e.g., 'game_outcome', 'spread_prediction', 'total_points')
            week: Week to predict (None = auto-detect current week)
            season: Season to predict (None = auto-detect current season)
            model_version: Model version to use (default: 'latest')
            
        Returns:
            dict: Prediction results with enriched metadata
        """
        self.logger.info("Running prediction generation only")
        
        # model_name is now required - no default
        
        # Generate predictions (predictor handles None season/week)
        result = self.predictor.generate_predictions(
            model_name=model_name,
            week=week,
            season=season,
            model_version=model_version
        )
        
        # Enrich result with metadata for reporting
        if result.get('status') == 'success':
            predictions = result.get('predictions', [])
            
            # Add metadata that report generator needs
            result['model_name'] = model_name
            result['model_version'] = model_version
            
            # Add summary statistics for CLI output
            result['summary'] = {
                'total_games': len(predictions),
                'high_confidence': sum(1 for p in predictions if p.get('confidence', 0) >= 0.8)
            }
            
            # Generate report if predictions exist (business logic)
            # Uses ReportOrchestrator facade for consistency with other report types
            if predictions:
                from .reporting.orchestrator import ReportOrchestrator
                
                report_path = ReportOrchestrator.generate_prediction_report(
                    predictions=predictions,
                    season=int(result['season']),
                    week=int(result['week']),
                    model_name=model_name,
                    model_version=model_version,
                    logger=self.logger
                )
                if report_path:
                    result['report_path'] = report_path
                    self.logger.info(f"📊 Report generated: {report_path}")
        
        return result
    

# Convenience function for direct usage
def create_ml_pipeline(db_service=None, logger=None):
    """
    Create ML pipeline with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        
    Returns:
        MLPipelineImpl: Configured ML pipeline
    """
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.ml_pipeline')
    
    return MLPipelineImpl(db_service, logger)
