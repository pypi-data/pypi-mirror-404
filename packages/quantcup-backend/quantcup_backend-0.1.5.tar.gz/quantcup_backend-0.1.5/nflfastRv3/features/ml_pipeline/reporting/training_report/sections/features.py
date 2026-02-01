"""
Training Report Features Section Generator

Generates feature importance, feature selection audit, and gauntlet audit sections.

**Refactoring Note**: Extracted from TrainingReportGenerator (lines 104-472)
to improve modularity and testability. Handles feature analysis sections
by delegating to analyzer.
"""

import pandas as pd
from typing import Optional


class FeaturesSectionGenerator:
    """
    Generates training report features sections.
    
    **Responsibilities**:
    - Feature importance analysis (delegates to analyzer)
    - Feature selection audit (delegates to analyzer)
    - Gauntlet audit (delegates to analyzer)
    
    **Pattern**: Composition over Inheritance - delegates complex analysis
    """
    
    def __init__(self, analyzer=None, logger=None):
        """
        Initialize features section generator.
        
        Args:
            analyzer: MetricsAnalyzer instance for feature analysis
            logger: Optional logger instance
        """
        self.analyzer = analyzer
        self.logger = logger
    
    def generate_feature_importance_section(
        self,
        model,
        feature_names,
        X_train: pd.DataFrame,
        y_train: pd.Series
    ) -> str:
        """
        Generate feature importance section (delegates to analyzer).
        
        Args:
            model: Trained model instance
            feature_names: Feature column names
            X_train: Training features
            y_train: Training labels
            
        Returns:
            str: Formatted feature importance section
        """
        if self.analyzer is None:
            return ""
        
        return self.analyzer.analyze_feature_importance(model, feature_names, X_train, y_train)
    
    def generate_feature_selection_audit(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        model_class
    ) -> str:
        """
        Generate feature selection audit section (delegates to analyzer).
        
        Args:
            X_train: Training features
            X_test: Test features
            y_train: Training labels
            model_class: Model class type
            
        Returns:
            str: Formatted feature selection audit section
        """
        if self.analyzer is None:
            return ""
        
        return self.analyzer.analyze_feature_selection_audit(
            X_train, X_test, y_train, model_class
        )
    
    def generate_gauntlet_audit(
        self,
        selector,
        original_features,
        X: pd.DataFrame,
        y: pd.Series,
        X_selected: Optional[pd.DataFrame],
        y_selected: pd.Series,
        model
    ) -> str:
        """
        Generate gauntlet audit section (delegates to analyzer).
        
        Complete pipeline from Registry → XGBoost final usage.
        
        Args:
            selector: Feature selector instance
            original_features: Original feature column names
            X: Input features
            y: Target labels
            X_selected: Post-gauntlet selected features (optional)
            y_selected: Labels for selected features
            model: Trained model for Steps 4-6
            
        Returns:
            str: Formatted gauntlet audit section
        """
        if self.analyzer is None:
            return ""
        
        if not hasattr(selector, '__class__'):
            return ""
        
        return self.analyzer.analyze_gauntlet_audit(
            selector=selector,
            original_features=original_features,
            X=X,
            y=y,
            X_selected=X_selected,
            y_selected=y_selected,
            model=model
        )


__all__ = ['FeaturesSectionGenerator']
