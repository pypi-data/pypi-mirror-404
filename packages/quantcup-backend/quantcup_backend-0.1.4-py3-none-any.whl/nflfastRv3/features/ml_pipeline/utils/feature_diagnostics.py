"""Feature Diagnostics Utilities.

Generic utilities for analyzing feature quality, correlations, and importance stability.
Applicable to all ML models (game outcomes, player props, etc.).

Key Functions:
- analyze_correlations(): Identify features correlated with target
- analyze_importance_stability(): Detect overfitting via frozen feature importance
- detect_poison_pills(): Find high-importance, low-correlation features
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from numpy.typing import NDArray

from commonv2 import get_logger

# Module logger
logger = get_logger(__name__)


class FeatureDiagnostics:
    """Generic feature analysis utilities for ML models."""
    
    @staticmethod
    def analyze_correlations(
        df: pd.DataFrame,
        target_col: str,
        feature_patterns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Analyze correlation between features and target variable.
        
        Identifies which features have meaningful relationships with the target
        and which may be noise. Helps guide feature engineering and selection.
        
        Args:
            df: DataFrame with features and target
            target_col: Name of target column
            feature_patterns: Optional list of regex patterns to filter features
                             (e.g., [r'_diff$', r'^epa_'])
            
        Returns:
            DataFrame with correlation analysis results sorted by absolute correlation
            
        Example:
            >>> corr_df = FeatureDiagnostics.analyze_correlations(
            ...     df, 'home_team_won', feature_patterns=[r'_diff$']
            ... )
            >>> print(corr_df.head())
        """
        logger.info(f"🔍 Analyzing feature correlations with {target_col}")
        
        # Get features to analyze
        if feature_patterns:
            import re
            features = []
            for col in df.columns:
                if col != target_col and any(re.search(pattern, col) for pattern in feature_patterns):
                    features.append(col)
        else:
            features = [col for col in df.columns if col != target_col]
        
        # Calculate correlations
        correlations = []
        for feature in features:
            if feature in df.columns and pd.api.types.is_numeric_dtype(df[feature]):
                corr = df[feature].corr(df[target_col])
                abs_corr = abs(corr)
                
                correlations.append({
                    'feature': feature,
                    'correlation': corr,
                    'abs_correlation': abs_corr,
                    'direction': 'positive' if corr > 0 else 'negative',
                    'strength': 'strong' if abs_corr > 0.3 else 'moderate' if abs_corr > 0.1 else 'weak'
                })
        
        # Create results dataframe
        corr_df = pd.DataFrame(correlations)
        corr_df = corr_df.sort_values('abs_correlation', ascending=False)
        
        logger.info(f"\nTop 10 Most Correlated Features:")
        for idx, row in corr_df.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['correlation']:+.3f} ({row['strength']})")
        
        logger.info(f"\nCorrelation Strength Distribution:")
        logger.info(f"  Strong (|r| > 0.3): {(corr_df['abs_correlation'] > 0.3).sum()}")
        logger.info(f"  Moderate (0.1 < |r| ≤ 0.3): {((corr_df['abs_correlation'] > 0.1) & (corr_df['abs_correlation'] <= 0.3)).sum()}")
        logger.info(f"  Weak (|r| ≤ 0.1): {(corr_df['abs_correlation'] <= 0.1).sum()}")
        
        # Identify potentially useless features
        weak_features = corr_df[corr_df['abs_correlation'] < 0.05]['feature'].tolist()
        if weak_features:
            logger.info(f"\n⚠️  Features with very weak correlation (|r| < 0.05):")
            for feat in weak_features[:5]:
                logger.info(f"  - {feat}")
            if len(weak_features) > 5:
                logger.info(f"  ... and {len(weak_features) - 5} more")
        
        return corr_df
    
    @staticmethod
    def analyze_importance_stability(
        feature_importance_history: List[Dict[str, Any]],
        frozen_threshold: float = 0.01,
        variable_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Analyze stability of feature importance across multiple training runs.
        
        Detects if feature importance is frozen (overfitting) or varies appropriately
        across different test periods. Frozen feature importance (CV < 0.01) indicates
        the model has memorized training patterns rather than learning from data.
        
        Args:
            feature_importance_history: List of dicts, each containing feature importance
                                       from a different training run
            frozen_threshold: CV threshold for frozen features (default: 0.01 = 1% variation)
            variable_threshold: CV threshold for highly variable features (default: 0.5 = 50% variation)
            
        Returns:
            dict: Stability analysis metrics including:
                - total_features: Number of features analyzed
                - frozen_features_count: Number of frozen features
                - frozen_features: List of frozen feature names
                - variable_features_count: Number of highly variable features
                - variable_features: List of variable feature names
                - mean_cv: Mean coefficient of variation
                - median_cv: Median coefficient of variation
                - variance_df: DataFrame with detailed variance metrics
                
        Example:
            >>> history = [
            ...     {'epa_diff': 0.15, 'win_rate_diff': 0.10},
            ...     {'epa_diff': 0.15, 'win_rate_diff': 0.12}
            ... ]
            >>> analysis = FeatureDiagnostics.analyze_importance_stability(history)
            >>> print(f"Frozen features: {analysis['frozen_features']}")
        """
        logger.info("🔍 Analyzing feature importance stability")
        
        # Convert to DataFrame for easier analysis
        importance_df = pd.DataFrame(feature_importance_history)
        
        # Calculate variance for each feature across runs
        feature_variance = {}
        for col in importance_df.columns:
            if col != 'run_id':
                mean_val = importance_df[col].mean()
                std_val = importance_df[col].std()
                cv = std_val / mean_val if mean_val > 0 else 0
                
                feature_variance[col] = {
                    'mean': mean_val,
                    'std': std_val,
                    'cv': cv,
                    'range': importance_df[col].max() - importance_df[col].min()
                }
        
        # Sort by coefficient of variation (CV)
        variance_df = pd.DataFrame(feature_variance).T
        variance_df = variance_df.sort_values('cv')
        
        # Identify frozen and variable features
        frozen_features = variance_df[variance_df['cv'] < frozen_threshold].index.tolist()
        variable_features = variance_df[variance_df['cv'] > variable_threshold].index.tolist()
        
        analysis = {
            'total_features': len(variance_df),
            'frozen_features_count': len(frozen_features),
            'frozen_features': frozen_features,
            'variable_features_count': len(variable_features),
            'variable_features': variable_features,
            'mean_cv': variance_df['cv'].mean(),
            'median_cv': variance_df['cv'].median(),
            'variance_df': variance_df
        }
        
        logger.info(f"\nFeature Importance Stability Analysis:")
        logger.info(f"  Total features: {analysis['total_features']}")
        logger.info(f"  Frozen features (CV < {frozen_threshold}): {analysis['frozen_features_count']}")
        logger.info(f"  Variable features (CV > {variable_threshold}): {analysis['variable_features_count']}")
        logger.info(f"  Mean CV: {analysis['mean_cv']:.3f}")
        logger.info(f"  Median CV: {analysis['median_cv']:.3f}")
        
        if frozen_features:
            logger.info(f"\n⚠️  Frozen Features (potential overfitting):")
            for feat in frozen_features[:5]:
                logger.info(f"  - {feat} (CV: {variance_df.loc[feat, 'cv']:.4f})")
            if len(frozen_features) > 5:
                logger.info(f"  ... and {len(frozen_features) - 5} more")
        
        return analysis
    
    @staticmethod
    def detect_poison_pills(
        model,
        X: pd.DataFrame,
        y: pd.Series,
        importance_threshold: float = 0.15,
        correlation_threshold: float = 0.02
    ) -> List[str]:
        """
        Detect poison pill features (very high importance, near-zero correlation).
        
        Poison pills are features that the model assigns very high importance to,
        but which have near-zero correlation with the target. This indicates the
        model is overfitting to noise or spurious patterns.
        
        IMPORTANT: Uses strict thresholds to avoid false positives with nonlinear features.
        XGBoost often finds predictive value in features with low bivariate correlation
        through nonlinear splits and interactions.
        
        Args:
            model: Fitted tree-based model with feature_importances_ attribute
            X: Training features DataFrame
            y: Training target Series
            importance_threshold: Minimum importance to check (default: 0.15 = 15%)
                                 Only features with very high importance are examined
            correlation_threshold: Maximum correlation for poison pill (default: 0.02 = 2%)
                                  Only features with near-zero correlation are flagged
            
        Returns:
            List of poison pill feature names
            
        Example:
            >>> from xgboost import XGBClassifier
            >>> model = XGBClassifier().fit(X_train, y_train)
            >>> poison_pills = FeatureDiagnostics.detect_poison_pills(
            ...     model, X_train, y_train
            ... )
            >>> print(f"Found {len(poison_pills)} poison pills")
            
        Note:
            Stricter thresholds (0.15 importance, 0.02 correlation) prevent removing
            legitimate nonlinear features that are predictive despite low correlation.
            This preserves:
            - EPA differential features
            - Rolling window metrics
            - NextGen QB statistics
            - Interaction features
            - Sparse/bucketed indicators
        """
        if not hasattr(model, 'feature_importances_'):
            logger.warning("Model does not have feature_importances_ attribute")
            return []
        
        importances = model.feature_importances_
        feature_names = X.columns.tolist()
        
        logger.info(f"   📊 Poison pill thresholds: importance > {importance_threshold}, correlation < {correlation_threshold}")
        
        # Calculate correlations for numeric columns only
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            logger.warning("No numeric columns found for correlation analysis")
            return []
        
        correlations = X[numeric_cols].corrwith(y).abs()
        
        poison_pills = []
        for idx, feat in enumerate(feature_names):
            if feat in correlations:
                importance = importances[idx]
                correlation = correlations[feat]
                
                # Poison Pill Criteria (STRICT):
                # 1. VERY High Importance (> 0.15, not 0.05)
                # 2. NEAR-ZERO Correlation (< 0.02, not 0.05)
                # This prevents flagging legitimate nonlinear features
                if importance > importance_threshold and correlation < correlation_threshold:
                    poison_pills.append(feat)
                    logger.warning(f"   💊 {feat}: Importance={importance:.4f}, Corr={correlation:.4f}")
        
        if poison_pills:
            logger.warning(f"💊 Found {len(poison_pills)} POISON PILLS (Very High Importance, Near-Zero Correlation)")
        else:
            logger.info("✓ No poison pills detected")
        
        return poison_pills


__all__ = ['FeatureDiagnostics']