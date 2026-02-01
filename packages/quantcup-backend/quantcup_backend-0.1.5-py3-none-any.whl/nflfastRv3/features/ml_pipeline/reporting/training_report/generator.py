"""
Training Report Generator

Main orchestrator that composes section generators to produce comprehensive training reports.

**Refactoring Note**: Extracted from monolithic TrainingReportGenerator (852 lines)
to separate orchestration from business logic. Uses composition pattern to delegate
section generation to specialized generators.

**Pattern**: Minimum Viable Decoupling (2 complexity points)
- Orchestrator coordinates section generators (composition)
- Each section generator handles specific responsibility (SRP)
- Maintains backward compatibility through consistent API
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..analyzers import create_metrics_analyzer
from .sections import (
    SummarySectionGenerator,
    MetricsSectionGenerator,
    FeaturesSectionGenerator,
    DiagnosticsSectionGenerator
)


class TrainingReportGenerator:
    """
    Main orchestrator for training report generation.
    
    **Composition Pattern**: Delegates section generation to specialized generators:
    - SummarySectionGenerator: Header, executive summary, model config
    - MetricsSectionGenerator: Performance metrics, test games table
    - FeaturesSectionGenerator: Feature importance, selection audits
    - DiagnosticsSectionGenerator: Ensemble analysis, market comparison
    
    **Backward Compatibility**: Maintains same public API as original monolithic class
    """
    
    def __init__(self, logger=None):
        """
        Initialize training report generator with composed section generators.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        
        # Create shared analyzer (complex analysis delegated here)
        self.analyzer = create_metrics_analyzer()
        
        # Compose section generators
        self.summary_gen = SummarySectionGenerator(logger=logger)
        self.metrics_gen = MetricsSectionGenerator(analyzer=self.analyzer, logger=logger)
        self.features_gen = FeaturesSectionGenerator(analyzer=self.analyzer, logger=logger)
        self.diagnostics_gen = DiagnosticsSectionGenerator(analyzer=self.analyzer, logger=logger)
    
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
        output_dir: str = 'reports/training'
    ) -> str:
        """
        Generate comprehensive markdown training report.
        
        Note:
            TODO: If generating multiple artifact types beyond the report MD (e.g., model files,
            metrics CSVs, plots), consider using timestamped subfolders like:
            'reports/training/train_{timestamp}' to group related artifacts together.
            See scripts/analyze_pbp_odds_data_v4.py for reference implementation.
        
        Orchestrates report generation by delegating to section generators.
        
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
        
        # 1. Header and summary sections
        report_sections.append(self.summary_gen.generate_header(train_seasons, test_seasons, test_week))
        report_sections.append(self.summary_gen.generate_executive_summary(metrics, len(X_train), len(X_test)))
        report_sections.append(self.summary_gen.generate_nfl_benchmarking_context())
        report_sections.append(self.summary_gen.generate_model_config(model, len(X_train.columns)))
        
        # 2. Performance metrics sections
        report_sections.append(self.metrics_gen.generate_performance_metrics(metrics, y_test, y_pred))
        report_sections.append(self.metrics_gen.generate_confusion_matrix_section(y_test, y_pred))
        
        # 3. Feature analysis sections
        # Determine correct feature names (handle feature splitting)
        feature_names = X_test.columns
        if hasattr(model, 'tree_features_') and model.tree_features_:
            feature_names = model.tree_features_
        
        report_sections.append(self.features_gen.generate_feature_importance_section(
            model, feature_names, X_train, y_train
        ))
        
        # 4. Ensemble diagnostics (if ensemble model)
        if y_pred_proba is not None:
            ensemble_section = self.diagnostics_gen.generate_ensemble_diagnostics(
                model, X_test, y_test, y_pred_proba
            )
            if ensemble_section:
                report_sections.append(ensemble_section)
        
        # 5. Market comparison analysis (CLV & ROI + advanced analytics)
        market_sections = self.diagnostics_gen.generate_market_comparison_section(
            y_pred_proba, test_metadata, y_test, output_dir, test_seasons
        )
        report_sections.extend(market_sections)
        
        # 6. Feature selection audits
        report_sections.append(self.features_gen.generate_feature_selection_audit(
            X_train, X_test, y_train, model.__class__
        ))
        
        # 7. Gauntlet audit (if feature selector present)
        if hasattr(model, 'feature_selector') and model.feature_selector:
            X_train_selected = self._get_selected_features(model, X_train)
            report_sections.append(self.features_gen.generate_gauntlet_audit(
                selector=model.feature_selector,
                original_features=X_train.columns.tolist(),
                X=X_train,
                y=y_train,
                X_selected=X_train_selected,
                y_selected=y_train,
                model=model
            ))
        
        # 8. Test games details
        if y_pred_proba is not None:
            report_sections.append(self.metrics_gen.generate_test_games_table(
                test_metadata, y_test, y_pred, y_pred_proba
            ))
        
        # 9. Prediction confidence analysis
        if y_pred_proba is not None:
            report_sections.append(self.metrics_gen.generate_prediction_confidence_section(
                y_test, y_pred, y_pred_proba
            ))
        
        # 10. Artifacts section
        report_sections.append(self.diagnostics_gen.generate_artifacts_section(model_path, report_path))
        
        # Write report
        report_content = '\n\n'.join(filter(None, report_sections))  # Filter out None/empty sections
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Training report saved: {report_path}")
        
        return str(report_path)
    
    # Helper methods
    
    def _get_selected_features(self, model, X_train: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Extract post-Gauntlet selected features for correlation analysis.
        
        Args:
            model: Model with feature selector
            X_train: Training features
            
        Returns:
            DataFrame with selected features or None if extraction fails
        """
        try:
            if hasattr(model.feature_selector, 'selected_features_'):
                selected_cols = model.feature_selector.selected_features_
                if selected_cols:
                    return X_train[selected_cols]
        except Exception:
            # If transformation fails, Step 6 will fall back to importance-only
            pass
        
        return None


def create_report_generator(logger=None):
    """
    Factory function to create report generator.
    
    Maintains backward compatibility with original factory pattern.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        TrainingReportGenerator: Configured report generator
    """
    return TrainingReportGenerator(logger=logger)


__all__ = ['TrainingReportGenerator', 'create_report_generator']
