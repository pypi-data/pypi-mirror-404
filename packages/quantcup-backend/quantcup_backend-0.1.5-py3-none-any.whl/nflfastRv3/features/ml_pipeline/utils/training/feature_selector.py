"""
Feature Selector Component ("The Gauntlet")

Automated feature pruning pipeline that filters features based on:
1. Variance (Sanity Check)
2. Collinearity (Redundancy)
3. Relevance (Correlation with Target)
4. Model-Based Importance (Expert Filter)

This component replaces the static FeatureRegistry with a dynamic, data-driven approach.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from commonv2.core.logging import get_logger

class FeatureSelector:
    """
    Dynamic feature selection pipeline.
    
    Implements a multi-stage filtering process to ensure only high-quality
    features reach the model.
    """
    
    def __init__(self,
                 variance_threshold: float = 0.0,
                 correlation_threshold: float = 0.005,
                 correlation_threshold_tree: Optional[float] = None,
                 logger=None):
        """
        Initialize the FeatureSelector.
        
        Args:
            variance_threshold: Minimum variance required to keep a feature.
            correlation_threshold: Minimum absolute correlation with target required (for linear models).
            correlation_threshold_tree: Optional separate threshold for tree models (default: 0.001).
                                       Tree models can use low-correlation features via interactions.
            logger: Optional logger instance.
        """
        self.variance_threshold = variance_threshold
        self.correlation_threshold = correlation_threshold
        # Default tree threshold to 0.001 (5x more lenient) per Case Study #12
        self.correlation_threshold_tree = correlation_threshold_tree if correlation_threshold_tree is not None else 0.001
        self.logger = logger or get_logger(__name__)
        
        # State
        self.selected_features_: List[str] = []
        self.linear_features_: List[str] = []  # Features passing linear threshold
        self.tree_features_: List[str] = []    # Features passing tree threshold
        self.dropped_features_: Dict[str, List[str]] = {
            'variance': [],
            'correlation': [],
            'correlation_tree': [],  # Separate tracking for tree-specific drops
            'collinearity': [],
            'model_based': []
        }
        
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'FeatureSelector':
        """
        Fit the feature selector to the training data.
        
        Creates TWO feature sets:
        - linear_features_: Stricter filtering (correlation >= 0.005) for linear models
        - tree_features_: Lenient filtering (correlation >= 0.001) for tree models
        
        Args:
            X: Training features
            y: Training target
            
        Returns:
            self
        """
        if self.logger:
            self.logger.info(f"🛡️ Entering The Gauntlet: {len(X.columns)} features")
            
        # Reset state
        current_features = X.columns.tolist()
        self.dropped_features_ = {k: [] for k in self.dropped_features_}
        
        # Stage 1: Variance Filter (Sanity) - Same for both
        current_features = self._filter_variance(X[current_features])
        
        # Stage 2: Collinearity Filter (Redundancy) - Same for both
        current_features = self._filter_collinearity(X[current_features], y)
        
        # Stage 3a: Relevance Filter for LINEAR models (strict threshold)
        self.linear_features_ = self._filter_relevance(
            X[current_features], y,
            threshold=self.correlation_threshold,
            model_type='linear'
        )
        
        # Stage 3b: Relevance Filter for TREE models (lenient threshold)
        # Per Case Study #12: Trees can use low-correlation features via interactions
        self.tree_features_ = self._filter_relevance(
            X[current_features], y,
            threshold=self.correlation_threshold_tree,
            model_type='tree'
        )
        
        # Stage 4: Model-Based Filter (Expert)
        # TODO: Implement in Phase 2
        
        # Default selected_features_ to linear (backward compatibility)
        self.selected_features_ = self.linear_features_
        
        if self.logger:
            dropped_linear = len(current_features) - len(self.linear_features_)
            dropped_tree = len(current_features) - len(self.tree_features_)
            self.logger.info(f"✅ The Gauntlet Complete:")
            self.logger.info(f"   Linear features: {len(self.linear_features_)} survivors ({dropped_linear} additional dropped)")
            self.logger.info(f"   Tree features: {len(self.tree_features_)} survivors ({dropped_tree} additional dropped)")
            
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the dataset to keep only selected features.
        
        Returns union of linear_features_ and tree_features_ (dual-threshold approach).
        
        Args:
            X: Feature dataframe
            
        Returns:
            DataFrame with union of linear and tree features
        """
        # Use union of both feature sets (dual-threshold approach)
        all_selected = list(set(self.linear_features_ + self.tree_features_))
        
        if not all_selected:
            # If fit hasn't been called or no features selected, return original
            if self.logger:
                self.logger.warning("⚠️ FeatureSelector not fitted or no features selected. Returning original.")
            return X
            
        # Ensure all selected features exist in X
        missing = [f for f in all_selected if f not in X.columns]
        if missing:
            if self.logger:
                self.logger.warning(f"⚠️ {len(missing)} selected features missing from input. Filling with 0.")
            # Create missing columns with 0s (safe default for linear/tree models)
            for col in missing:
                X[col] = 0
                
        return X[all_selected]
    
    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """
        Fit to data, then transform it.
        """
        return self.fit(X, y).transform(X)
        
    def _filter_variance(self, X: pd.DataFrame) -> List[str]:
        """
        Stage 1: Remove constant or near-constant features.
        """
        from sklearn.feature_selection import VarianceThreshold
        
        # Only check numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        non_numeric_cols = list(set(X.columns) - set(numeric_cols))
        
        if not numeric_cols:
            return non_numeric_cols
            
        selector = VarianceThreshold(threshold=self.variance_threshold)
        selector.fit(X[numeric_cols])
        
        kept_indices = selector.get_support(indices=True)
        kept_numeric = [numeric_cols[i] for i in kept_indices]
        
        # Combine kept numeric with non-numeric (which we assume are metadata/categorical and keep)
        kept_features = kept_numeric + non_numeric_cols
        
        dropped = list(set(X.columns) - set(kept_features))
        self.dropped_features_['variance'] = dropped
        
        if self.logger and dropped:
            self.logger.info(f"  🗑️ Dropped {len(dropped)} constant features (Variance < {self.variance_threshold})")
            # Log first 5 dropped
            for f in dropped[:5]:
                self.logger.debug(f"     - {f}")
                
        return kept_features

    def _filter_collinearity(self, X: pd.DataFrame, y: pd.Series) -> List[str]:
        """
        Stage 2: Remove highly correlated features (Redundancy).
        
        If two features have correlation > 0.90, keep the one with higher
        correlation to the target.
        """
        # Only check numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        non_numeric_cols = list(set(X.columns) - set(numeric_cols))
        
        if len(numeric_cols) < 2:
            return X.columns.tolist()
            
        # Calculate correlation matrix
        corr_matrix = X[numeric_cols].corr().abs()
        
        # Calculate correlation with target for tie-breaking
        target_corr = X[numeric_cols].corrwith(y).abs()
        
        # Identify pairs to drop
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = set()
        
        for column in upper.columns:
            # Find features that are highly correlated with this column
            correlated_features = upper.index[upper[column] > 0.90].tolist()
            
            for feat in correlated_features:
                # Compare target correlation
                if target_corr[column] > target_corr[feat]:
                    to_drop.add(feat)
                else:
                    to_drop.add(column)
                    
        kept_numeric = [c for c in numeric_cols if c not in to_drop]
        kept_features = kept_numeric + non_numeric_cols
        
        self.dropped_features_['collinearity'] = list(to_drop)
        
        if self.logger and to_drop:
            self.logger.info(f"  🗑️ Dropped {len(to_drop)} redundant features (Collinearity > 0.90)")
            # LOG ALL DROPPED FEATURES (not just 5) with correlation partners
            for f in sorted(to_drop):
                # Find what this feature was correlated with
                corr_partner = None
                max_corr = 0.0
                for column in upper.columns:
                    if column != f and f in upper.index:
                        corr_val = upper.loc[f, column] if column in upper.columns else 0.0
                        if corr_val > max_corr:
                            max_corr = corr_val
                            corr_partner = column
                
                partner_str = f" (r={max_corr:.3f} with {corr_partner})" if corr_partner else ""
                self.logger.info(f"     - {f}{partner_str}")
                
        return kept_features

    def _filter_relevance(self, X: pd.DataFrame, y: pd.Series,
                          threshold: Optional[float] = None,
                          model_type: str = 'all') -> List[str]:
        """
        Stage 3: Remove features with low correlation to target.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            threshold: Override correlation threshold (uses self.correlation_threshold if None)
            model_type: 'linear', 'tree', or 'all' (for logging only)
        
        Note: Per Case Study #12 - Tree models can use low-correlation features via
              multivariate splits and interactions. Linear models need strong correlation.
        """
        # Only check numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        non_numeric_cols = list(set(X.columns) - set(numeric_cols))
        
        if not numeric_cols:
            return non_numeric_cols
        
        # Use provided threshold or default
        effective_threshold = threshold if threshold is not None else self.correlation_threshold
        
        # Calculate correlations
        correlations = X[numeric_cols].corrwith(y).abs()
        
        # Identify features below threshold
        kept_numeric = correlations[correlations >= effective_threshold].index.tolist()
        
        # Combine kept numeric with non-numeric (which we assume are metadata/categorical and keep)
        kept_features = kept_numeric + non_numeric_cols
        
        dropped = list(set(X.columns) - set(kept_features))
        
        # Store dropped features with model-specific key
        drop_key = 'correlation_tree' if model_type == 'tree' else 'correlation'
        self.dropped_features_[drop_key] = dropped
        
        if self.logger and dropped:
            model_label = f" ({model_type} models)" if model_type != 'all' else ""
            self.logger.info(f"  🗑️ Dropped {len(dropped)} irrelevant features{model_label} (Corr < {effective_threshold})")
            # LOG ALL DROPPED FEATURES with correlation values
            for f in sorted(dropped):
                corr_val = correlations.get(f, 0.0) if f in correlations else 0.0
                # Highlight known problematic features from Case Study #12
                # (stadium_home_win_rate was identified as poison pill - high importance, zero correlation)
                toxic_watch = ['stadium_home_win_rate', 'stadium_scoring_rate', 'home_site_bias']
                if any(t in f for t in toxic_watch):
                    self.logger.info(f"     🎯 KNOWN ISSUE: {f} (corr: {corr_val:.4f}) - See Case Study #12")
                else:
                    self.logger.info(f"     - {f} (corr: {corr_val:.4f})")
                     
        return kept_features