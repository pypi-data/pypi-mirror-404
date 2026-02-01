"""
Report Generation Orchestrator

Context-aware report orchestration that delegates to specialized report generators.
Keeps CLI thin by centralizing all reporting business logic here.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Business Logic - orchestrates report generators)
"""

from typing import Dict, Any, List, Optional
from .training_report import create_report_generator
from .backtest_report import create_backtest_reporter
from .optimize_report import create_optimize_reporter
from .feature_report import create_feature_reporter


class ReportOrchestrator:
    """
    Context-aware report orchestration.
    
    Determines which report generator to use based on operation type.
    Centralizes reporting business logic, keeping CLI layer thin.
    
    Pattern: Strategy Pattern
    Complexity: 2 points (orchestration + delegation)
    Depth: 1 layer (delegates to report generators)
    """
    
    @staticmethod
    def _parse_seasons(seasons_str: str) -> List[int]:
        """
        Parse season string to list of integers.
        
        Supports formats:
        - '2020-2023' (range)
        - '2020,2021,2022,2023' (comma-separated)
        - '2000-2022,2024' (mixed)
        
        Args:
            seasons_str: Season string
            
        Returns:
            list: List of season integers
        """
        seasons = []
        parts = seasons_str.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                seasons.extend(range(int(start), int(end) + 1))
            else:
                seasons.append(int(part))
        
        return seasons
    
    @staticmethod
    def generate_training_report(
        result: Dict[str, Any],
        logger=None
    ) -> Optional[str]:
        """
        Generate detailed training report for single training run.
        
        Extracts data from training result and delegates to TrainingReportGenerator.
        
        Args:
            result: Training result dictionary from MLPipelineImpl.train_model_only()
            logger: Optional logger instance
            
        Returns:
            str: Path to generated report, or None if report generation failed
        """
        if result.get('status') != 'success':
            if logger:
                logger.warning("Cannot generate report - training did not succeed")
            return None
        
        # Validate required fields exist
        required_fields = ['X_train', 'X_test', 'y_train', 'y_test', 'y_pred', 'test_metadata']
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            if logger:
                logger.warning(f"Cannot generate report - missing required fields: {missing_fields}")
            return None
        
        try:
            report_generator = create_report_generator(logger=logger)
            
            # Parse season strings
            train_seasons = ReportOrchestrator._parse_seasons(
                result.get('train_seasons_str', '')
            )
            test_seasons = ReportOrchestrator._parse_seasons(
                result.get('test_seasons_str', '')
            )
            
            # Generate report using complete training data
            # Type assertion: We've validated these exist above
            report_path = report_generator.generate_report(
                model=result['model'],
                X_train=result['X_train'],  # type: ignore
                X_test=result['X_test'],  # type: ignore
                y_train=result['y_train'],  # type: ignore
                y_test=result['y_test'],  # type: ignore
                y_pred=result['y_pred'],  # type: ignore
                y_pred_proba=result.get('y_pred_proba'),
                test_metadata=result['test_metadata'],  # type: ignore
                metrics=result['metrics'],
                train_seasons=train_seasons,
                test_seasons=test_seasons,
                test_week=result.get('test_week'),
                model_path=result.get('model_path')
            )
            
            return report_path
            
        except Exception as e:
            if logger:
                logger.warning(f"Failed to generate training report: {e}")
            return None
    
    @staticmethod
    def generate_backtest_report(
        backtest_results: List[Dict[str, Any]],
        model_name: str,
        train_years: int,
        start_year: int,
        end_year: int,
        test_week: Optional[int] = None,
        logger=None
    ) -> Optional[str]:
        """
        Generate aggregated backtest report across multiple years.
        
        Delegates to BacktestReportGenerator for aggregated analysis.
        
        Args:
            backtest_results: List of training results from each test year
            model_name: Model name
            train_years: Number of training years
            start_year: First test year
            end_year: Last test year
            test_week: Optional specific test week
            logger: Optional logger instance
            
        Returns:
            str: Path to generated report, or None if report generation failed
        """
        if not backtest_results:
            if logger:
                logger.warning("Cannot generate backtest report - no successful results")
            return None
        
        try:
            backtest_reporter = create_backtest_reporter(logger=logger)
            
            report_path = backtest_reporter.generate_report(
                backtest_results=backtest_results,
                model_name=model_name,
                train_years=train_years,
                start_year=start_year,
                end_year=end_year,
                test_week=test_week
            )
            
            return report_path
            
        except Exception as e:
            if logger:
                logger.warning(f"Failed to generate backtest report: {e}")
            return None
    
    @staticmethod
    def generate_optimization_report(
        optimization_results: List[Dict[str, Any]],
        model_name: str,
        test_year: int,
        test_week: int,
        min_years: int,
        max_years: int,
        logger=None
    ) -> Optional[str]:
        """
        Generate aggregated optimization report across window sizes.
        
        Delegates to OptimizationReportGenerator for window size analysis.
        
        Args:
            optimization_results: List of training results from each window size
            model_name: Model name
            test_year: Test year
            test_week: Test week
            min_years: Minimum training years tested
            max_years: Maximum training years tested
            logger: Optional logger instance
            
        Returns:
            str: Path to generated report, or None if report generation failed
        """
        if not optimization_results:
            if logger:
                logger.warning("Cannot generate optimization report - no successful results")
            return None
        
        try:
            optimize_reporter = create_optimize_reporter(logger=logger)
            
            report_path = optimize_reporter.generate_report(
                optimization_results=optimization_results,
                model_name=model_name,
                test_year=test_year,
                test_week=test_week,
                min_years=min_years,
                max_years=max_years
            )
            
            return report_path
            
        except Exception as e:
            if logger:
                logger.warning(f"Failed to generate optimization report: {e}")
            return None
    
    @staticmethod
    def generate_prediction_report(
        predictions: List[Dict[str, Any]],
        season: int,
        week: int,
        model_name: str = 'game_outcome',
        model_version: str = 'latest',
        logger=None
    ) -> Optional[str]:
        """
        Generate prediction report for upcoming games.
        
        Delegates to PredictionReportGenerator for comprehensive game predictions.
        
        Args:
            predictions: List of prediction dictionaries from predictor
            season: NFL season
            week: NFL week
            model_name: Model name
            model_version: Model version tag
            logger: Optional logger instance
            
        Returns:
            str: Path to generated report, or None if report generation failed
        """
        if not predictions:
            if logger:
                logger.warning("Cannot generate prediction report - no predictions")
            return None
        
        try:
            from .prediction_reporter import create_prediction_report_generator
            prediction_reporter = create_prediction_report_generator(logger=logger)
            
            report_path = prediction_reporter.generate_report(
                predictions=predictions,
                season=season,
                week=week,
                model_name=model_name,
                model_version=model_version
            )
            
            return report_path
            
        except Exception as e:
            if logger:
                logger.warning(f"Failed to generate prediction report: {e}")
            return None
    
    @staticmethod
    def generate_feature_report(
        results: Dict[str, Any],
        logger=None
    ) -> Optional[str]:
        """
        Generate feature engineering documentation report.
        
        Delegates to FeatureReportGenerator for comprehensive feature set documentation.
        
        Args:
            results: Feature engineering results from FeatureEngineerImplementation
                Expected structure:
                {
                    'status': 'success' | 'partial' | 'error',
                    'features_built': int,
                    'total_features': int,
                    'total_rows': int,
                    'results': {
                        'feature_name': {
                            'status': 'success' | 'failed',
                            'rows_built': int,
                            'error': str (optional)
                        }
                    }
                }
            logger: Optional logger instance
            
        Returns:
            str: Path to generated report, or None if report generation failed
        """
        if not results or results.get('status') == 'error':
            if logger:
                logger.warning("Cannot generate feature report - feature engineering failed")
            return None
        
        try:
            feature_reporter = create_feature_reporter(logger=logger)
            
            # Use default domain-based output_dir from generator (reports/features)
            report_path = feature_reporter.generate_report(
                results=results
            )
            
            return report_path
            
        except Exception as e:
            if logger:
                logger.warning(f"Failed to generate feature report: {e}")
            return None


def create_report_orchestrator(logger=None):
    """
    Factory function to create report orchestrator.
    
    Note: ReportOrchestrator uses static methods, so this returns the class itself.
    Provided for consistency with other create_* factory functions.
    
    Args:
        logger: Optional logger instance (unused - kept for API consistency)
        
    Returns:
        ReportOrchestrator: Report orchestrator class
    """
    return ReportOrchestrator


__all__ = ['ReportOrchestrator', 'create_report_orchestrator']