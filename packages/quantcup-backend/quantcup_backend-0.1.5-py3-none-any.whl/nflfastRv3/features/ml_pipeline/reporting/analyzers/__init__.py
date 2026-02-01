"""
Statistical analysis components for ML reports.

Refactored with facade pattern for better organization.
Pattern: Facade Pattern (3 complexity points)
- Public API: MetricsAnalyzer (facade)
- Internal: BasicMetricsAnalyzer, FeatureAnalyzer, EnsembleAnalyzer
"""

from nflfastRv3.features.ml_pipeline.reporting.analyzers.basic_metrics import BasicMetricsAnalyzer
from nflfastRv3.features.ml_pipeline.reporting.analyzers.feature_analysis import FeatureAnalyzer
from nflfastRv3.features.ml_pipeline.reporting.analyzers.ensemble_diagnostics import EnsembleAnalyzer
from nflfastRv3.features.ml_pipeline.reporting.analyzers.utils import categorize_feature, get_registry_feature_reasons


class MetricsAnalyzer:
    """
    Analyzes model performance metrics.
    
    Pattern: Facade Pattern - delegates to specialized internal analyzers
    Complexity: 3 points (facade + 3 internal classes)
    
    This facade provides backward-compatible access to all analysis methods
    while organizing them internally by responsibility:
    - Basic metrics (confusion matrix, confidence)
    - Feature analysis (importance, selection, gauntlet)
    - Ensemble diagnostics
    """
    
    def __init__(self):
        """Initialize with specialized analyzer instances."""
        self._metrics = BasicMetricsAnalyzer()
        self._features = FeatureAnalyzer()
        self._ensemble = EnsembleAnalyzer()
    
    # ========================================================================
    # Basic Metrics Delegation
    # ========================================================================
    
    def analyze_confusion_matrix(self, y_test, y_pred):
        """
        Generate confusion matrix analysis.
        
        Args:
            y_test: True labels
            y_pred: Predicted labels
            
        Returns:
            str: Formatted markdown confusion matrix analysis
        """
        return self._metrics.analyze_confusion_matrix(y_test, y_pred)
    
    def analyze_prediction_confidence(self, y_test, y_pred, y_pred_proba):
        """
        Analyze prediction confidence distribution.
        
        Args:
            y_test: True labels
            y_pred: Predicted labels
            y_pred_proba: Prediction probabilities
            
        Returns:
            str: Formatted markdown confidence analysis
        """
        return self._metrics.analyze_prediction_confidence(y_test, y_pred, y_pred_proba)
    
    # ========================================================================
    # Feature Analysis Delegation
    # ========================================================================
    
    def analyze_feature_importance(self, model, feature_names, X_train=None, y_train=None):
        """
        Generate feature importance analysis.

        Args:
            model: Trained model with feature_importances_ attribute or ensemble with xgboost_model
            feature_names: List or Index of feature names
            X_train: Training features (required for XGBoost diagnostics)
            y_train: Training labels (required for XGBoost diagnostics)

        Returns:
            str: Formatted markdown feature importance analysis
        """
        return self._features.analyze_feature_importance(model, feature_names, X_train, y_train)
    
    def analyze_feature_selection_audit(self, X_train, X_test, y_train=None, model_class=None):
        """
        Generate comprehensive feature selection audit.
        
        Shows:
        - Complete list of features used
        - Features available but excluded
        - Exclusion reasons from FeatureRegistry
        - Feature statistics and quality metrics
        
        Args:
            X_train: Training features DataFrame
            X_test: Test features DataFrame
            y_train: Training target (optional, for correlation calculation)
            model_class: Model class for accessing registry (optional)
            
        Returns:
            str: Formatted markdown feature audit
        """
        return self._features.analyze_feature_selection_audit(X_train, X_test, y_train, model_class)
    
    def analyze_gauntlet_audit(self, selector, original_features, X=None, y=None, X_selected=None, y_selected=None, model=None):
        """
        Generate complete feature pipeline audit from Registry → Final XGBoost Usage.
        
        Shows the entire journey:
        1. The Gauntlet (variance, collinearity, relevance) with WHY details
        2. Feature Splitting (linear vs tree groups)
        3. Poison Pill Detection (if any removed)
        4. XGBoost Final Usage (which features actually got used)
        
        Args:
            selector: FeatureSelector instance with dropped_features_ attribute
            original_features: List of original feature names before selection
            X: Optional DataFrame with original features (for correlation calculations in Stages 1-3)
            y: Optional Series with target variable (for correlation calculations in Stages 1-3)
            X_selected: Optional DataFrame with post-Gauntlet transformed features (for Step 6 correlation)
            y_selected: Optional Series with target variable (for Step 6 correlation)
            model: Optional trained model (for feature splitting and XGBoost usage info)
            
        Returns:
            str: Markdown formatted complete pipeline audit with WHY details
        """
        return self._features.analyze_gauntlet_audit(selector, original_features, X, y, X_selected, y_selected, model)
    
    # ========================================================================
    # Ensemble Analysis Delegation
    # ========================================================================
    
    def analyze_ensemble_components(self, model, X_test, y_test, y_pred_proba):
        """
        Analyze ensemble component performance and interaction.
        
        Args:
            model: Ensemble model with component models
            X_test: Test features DataFrame
            y_test: Test labels Series
            y_pred_proba: Ensemble prediction probabilities
            
        Returns:
            str: Markdown formatted ensemble diagnostics
        """
        return self._ensemble.analyze_ensemble_components(model, X_test, y_test, y_pred_proba)
    
    # ========================================================================
    # Shared Utility Access (for backward compatibility)
    # ========================================================================
    
    def _categorize_feature(self, feature_name):
        """Categorize feature by name pattern."""
        return categorize_feature(feature_name)
    
    def _get_registry_feature_reasons(self):
        """Extract exclusion reasons from FeatureRegistry."""
        return get_registry_feature_reasons()


# ============================================================================
# Factory Function
# ============================================================================

def create_metrics_analyzer():
    """Factory function to create metrics analyzer."""
    return MetricsAnalyzer()


__all__ = ['MetricsAnalyzer', 'create_metrics_analyzer']
