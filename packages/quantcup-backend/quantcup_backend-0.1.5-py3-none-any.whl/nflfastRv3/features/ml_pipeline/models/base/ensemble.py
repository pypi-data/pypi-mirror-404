"""
Ensemble Models with Season Phase Gating.

This module combines BaseEnsemble, EnsembleClassifier, and EnsembleRegressor into a single file
to reduce code duplication and improve maintainability.

Classes:
- BaseEnsemble: Abstract base class for ensemble models
- EnsembleClassifier: Ensemble for classification tasks (Game Outcome, Player Props)
- EnsembleRegressor: Ensemble for regression tasks (Spread, Totals)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from numpy.typing import NDArray
from abc import ABC, abstractmethod
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.utils.validation import check_is_fitted

class BaseEnsemble(BaseEstimator, ABC):
    """
    Abstract base class for ensemble models with feature splitting and season gating.
    
    Shared Features:
    - Feature selection via FeatureSelector
    - Feature splitting (linear vs tree patterns)
    - Poison pill detection and removal
    - Season phase gating (early vs late season models)
    - Configurable model weights
    
    Subclasses must implement:
    - _build_models(): Create model instances
    - _predict_internal(): Generate predictions from fitted models
    - _get_model_type(): Return 'classifier' or 'regressor'
    """
    
    def __init__(
        self,
        linear_patterns: List[str],
        tree_patterns: List[str],
        weights: Dict[str, float],
        enable_season_gating: bool = True,
        xgboost_params: Optional[Dict[str, Any]] = None,
        linear_model_params: Optional[Dict[str, Any]] = None,
        secondary_linear_params: Optional[Dict[str, Any]] = None,
        random_state: int = 42
    ):
        """
        Initialize base ensemble.
        
        Args:
            linear_patterns: Regex patterns for linear model features
            tree_patterns: Regex patterns for tree model features
            weights: Model weights dict (keys depend on subclass)
            enable_season_gating: Whether to use season phase gating
            xgboost_params: Optional XGBoost hyperparameter overrides
            linear_model_params: Optional primary linear model parameter overrides
            secondary_linear_params: Optional secondary linear model parameter overrides
            random_state: Random seed for reproducibility
        """
        self.linear_patterns = linear_patterns
        self.tree_patterns = tree_patterns
        self.weights = weights
        self.enable_season_gating = enable_season_gating
        self.xgboost_params = xgboost_params or {}
        self.linear_model_params = linear_model_params or {}
        self.secondary_linear_params = secondary_linear_params or {}
        self.random_state = random_state
        
        # Models (initialized during fit by subclass)
        self.xgboost_model: Optional[Any] = None
        self.linear_model: Optional[Any] = None
        self.secondary_linear_model: Optional[Any] = None
        
        # Feature lists (populated during fit)
        self.linear_features_: Optional[List[str]] = None
        self.tree_features_: Optional[List[str]] = None
        
        # Season gating models (if enabled)
        self.model_early: Optional['BaseEnsemble'] = None
        self.early_features_: Optional[List[str]] = None
        
        # Feature selector
        self.feature_selector: Optional[Any] = None
        
        # Poison pills tracking
        self.poison_pills_removed_: Optional[List[str]] = None
    
    @abstractmethod
    def _build_models(self):
        """
        Build model instances using ModelFactory.
        
        Subclasses must create:
        - self.xgboost_model
        - self.linear_model (primary linear model)
        - self.secondary_linear_model (secondary linear model)
        """
        pass
    
    @abstractmethod
    def _predict_internal(self, X: pd.DataFrame) -> NDArray:
        """
        Generate predictions from fitted models.
        
        Args:
            X: Features DataFrame
            
        Returns:
            Predictions array (shape depends on subclass)
        """
        pass
    
    @abstractmethod
    def _get_model_type(self) -> str:
        """Return 'classifier' or 'regressor' for logging."""
        pass
    
    @abstractmethod
    def _create_gated_instance(self, enable_gating: bool) -> 'BaseEnsemble':
        """
        Create a new instance of the same type for season gating.
        
        Args:
            enable_gating: Whether to enable gating for the new instance
            
        Returns:
            New instance of the same ensemble type
        """
        pass
    
    def _split_features(self, X: pd.DataFrame) -> Dict[str, List[str]]:
        """Split features into linear and tree groups."""
        from nflfastRv3.features.ml_pipeline.utils import FeatureSplitter
        
        pattern_groups = {
            'linear': self.linear_patterns,
            'tree': self.tree_patterns
        }
        
        return FeatureSplitter.split_features(
            features=X.columns.tolist(),
            pattern_groups=pattern_groups,
        )
    
    def _fit_internal(self, X: pd.DataFrame, y: pd.Series):
        """
        Internal fit method for sub-models (standard ensemble logic).
        
        This method contains the core training pipeline:
        1. Feature selection
        2. Feature splitting (linear vs tree)
        3. Model building and initial training
        4. Poison pill detection and removal
        5. Model retraining if needed
        """
        from commonv2.core.logging import get_logger
        from nflfastRv3.features.ml_pipeline.utils import FeatureSelector, FeatureDiagnostics, SeasonPhaseGating
        
        logger = get_logger(f'nflfastRv3.{self._get_model_type()}')
        
        logger.info(f"🚀 Starting {self._get_model_type()} training")
        logger.info(f"   Training samples: {len(X)}")
        logger.info(f"   Input features: {len(X.columns)}")
        
        # 1. Run Feature Selection with Dual Thresholds
        # Per Case Study #12: Tree models can use low-correlation features via interactions
        # - Linear models: correlation >= 0.005 (stricter)
        # - Tree models: correlation >= 0.001 (5x more lenient)
        self.feature_selector = FeatureSelector(
            variance_threshold=0.0,
            correlation_threshold=0.005,      # For linear models
            correlation_threshold_tree=0.001, # For tree models (Case Study #12)
            logger=logger
        )
        
        self.feature_selector.fit(X, y)
        logger.info(f"   ✓ Feature selection complete:")
        logger.info(f"     - Linear features: {len(self.feature_selector.linear_features_)}")
        logger.info(f"     - Tree features: {len(self.feature_selector.tree_features_)}")
        
        # 2. Get model-specific feature sets from selector
        # Use selector's linear_features_ and tree_features_ directly (already split by threshold)
        self.linear_features_ = self.feature_selector.linear_features_
        self.tree_features_ = self.feature_selector.tree_features_
        
        # Validation: Ensure feature lists are non-None
        if self.linear_features_ is None:
            self.linear_features_ = []
        if self.tree_features_ is None:
            self.tree_features_ = []
        
        # Create transformed datasets from union of both feature sets
        all_selected_features = list(set(self.linear_features_ + self.tree_features_))
        X_selected = X[all_selected_features]
        
        # Fallback: If no features match patterns, use all available
        if not self.linear_features_:
            logger.warning("   ⚠️ No linear features passed gauntlet, using all selected features")
            self.linear_features_ = X_selected.columns.tolist()
        if not self.tree_features_:
            logger.warning("   ⚠️ No tree features passed gauntlet, using all selected features")
            self.tree_features_ = X_selected.columns.tolist()
        
        # At this point, both are guaranteed to be non-None lists
        assert self.linear_features_ is not None
        assert self.tree_features_ is not None
        
        logger.info(f"   ✓ Feature splitting complete:")
        logger.info(f"     - Linear features: {len(self.linear_features_)}")
        logger.info(f"     - Tree features: {len(self.tree_features_)}")
        
        # Create feature subsets
        X_linear = X_selected[self.linear_features_]
        X_tree = X_selected[self.tree_features_]
        
        # 3. Build and train models
        logger.info("   🔨 Building models...")
        self._build_models()
        logger.info("   ✓ Models built successfully")
        
        # Train XGBoost on tree features (Pass 1)
        logger.info(f"   🌳 Training XGBoost on {len(X_tree.columns)} tree features...")
        if self.xgboost_model is None:
            raise ValueError("XGBoost model not initialized by _build_models()")
        self.xgboost_model.fit(X_tree, y)
        logger.info("   ✓ XGBoost training complete (Pass 1)")
        
        # 4. Iterative Poison Pill Detection (strict thresholds to preserve nonlinear features)
        logger.info("   🔍 Running iterative poison pill detection...")
        
        max_iterations = 5
        iteration = 1
        all_removed_pills = []
        
        while iteration <= max_iterations:
            poison_pills = FeatureDiagnostics.detect_poison_pills(
                self.xgboost_model, X_tree, y,
                importance_threshold=0.15,  # Very high importance only
                correlation_threshold=0.02   # Near-zero correlation only
            )
            
            if not poison_pills:
                if iteration == 1:
                    logger.info("   ✅ No poison pills detected - all features passed")
                else:
                    logger.info(f"   ✅ Iteration {iteration}: No more poison pills - convergence reached")
                break
            
            logger.warning(f"   💊 Iteration {iteration}: Found {len(poison_pills)} poison pills: {poison_pills}")
            all_removed_pills.extend(poison_pills)
            
            # Remove poison pills
            X_tree = X_tree.drop(columns=poison_pills)
            
            # Update feature selector state
            if self.feature_selector:
                self.feature_selector.selected_features_ = [
                    f for f in self.feature_selector.selected_features_
                    if f not in poison_pills
                ]
                if self.tree_features_ is not None:
                    self.tree_features_ = [f for f in self.tree_features_ if f not in poison_pills]
                if self.linear_features_ is not None:
                    self.linear_features_ = [f for f in self.linear_features_ if f not in poison_pills]
            
            # Recreate X_linear with updated linear_features_ (after poison pill removal)
            if self.linear_features_ is not None:
                X_linear = X_selected[self.linear_features_]
            
            # Check if all tree features were removed
            if X_tree.empty:
                logger.warning("⚠️ All tree features dropped! Falling back to Safe Priors.")
                
                # Get safe priors
                available_priors = SeasonPhaseGating.get_safe_priors(X_selected.columns.tolist())
                
                if available_priors:
                    logger.info(f"   ✓ Added {len(available_priors)} safe priors: {available_priors}")
                    X_tree = X_selected[available_priors].copy()
                    
                    if self.tree_features_ is None:
                        self.tree_features_ = []
                    self.tree_features_.extend(available_priors)
                else:
                    logger.warning("   ❌ No tree features available! Disabling XGBoost in ensemble.")
                    logger.warning("   Setting XGBoost weight to 0, using linear models only.")
                    self.xgboost_model = None  # Don't train at all
                    self.weights['xgboost'] = 0.0
                    
                    # Renormalize other weights to sum to 1
                    remaining_keys = [k for k in self.weights.keys() if k != 'xgboost']
                    total = sum(self.weights[k] for k in remaining_keys)
                    if total > 0:
                        for key in remaining_keys:
                            self.weights[key] = self.weights[key] / total
                    
                    logger.info(f"   ✓ Renormalized weights: {self.weights}")
                    break
            
            # Rebuild and retrain XGBoost
            self._build_models()  # Rebuild to reset state
            if self.xgboost_model is None:
                raise ValueError("XGBoost model not initialized")
            
            logger.info(f"   🔄 Retraining XGBoost (Pass {iteration + 1}) on {len(X_tree.columns)} features...")
            self.xgboost_model.fit(X_tree, y)
            
            iteration += 1
        
        # Store all removed poison pills for reporting
        self.poison_pills_removed_ = all_removed_pills
        
        if all_removed_pills:
            logger.warning(f"💊 Total poison pills removed across all iterations: {len(all_removed_pills)}")
            logger.info(f"   Removed features: {all_removed_pills}")
            
            # Log final XGBoost diagnostics
            logger.info("   📊 Final model diagnostics:")
            if self.xgboost_model and not X_tree.empty:
                importances = self.xgboost_model.feature_importances_
                correlations = X_tree.corrwith(y).abs()
                
                logger.info(f"   Remaining {len(X_tree.columns)} tree features:")
                for idx, feat in enumerate(X_tree.columns):
                    imp = importances[idx]
                    corr = correlations[feat]
                    logger.info(f"     {feat}: Importance={imp:.4f}, Corr={corr:.4f}")
        
        # 5. Train linear models
        logger.info(f"   📊 Training linear models on {len(X_linear.columns)} features...")
        if self.linear_model is None or self.secondary_linear_model is None:
            raise ValueError("Linear models not initialized by _build_models()")
        self.linear_model.fit(X_linear, y)
        self.secondary_linear_model.fit(X_linear, y)
        logger.info("   ✓ Linear models training complete")
        
        logger.info(f"✅ {self._get_model_type().title()} training complete!")
        
        return self
    
    def _has_temporal_columns(self, X: pd.DataFrame) -> bool:
        """Check if DataFrame has temporal columns needed for gating."""
        required_cols = ['week', 'home_team', 'away_team']
        return all(col in X.columns for col in required_cols)
    
    def _fit_with_gating(self, X: pd.DataFrame, y: pd.Series):
        """
        Fit with season phase gating.
        
        Trains two internal models:
        1. model_early: Restricted to early season features
        2. self: Uses all features (acts as late model)
        """
        from commonv2.core.logging import get_logger
        from nflfastRv3.features.ml_pipeline.utils import SeasonPhaseGating
        
        logger = get_logger(f'nflfastRv3.{self._get_model_type()}')
        
        logger.info("🔀 Season phase gating enabled")
        
        # 1. Identify early season features
        all_features = X.columns.tolist()
        self.early_features_ = SeasonPhaseGating.identify_early_features(all_features)
        logger.info(f"   ✓ Identified {len(self.early_features_)} early-season safe features")
        
        # 2. Train early model (restricted features)
        logger.info("   📅 Training EARLY season model...")
        X_early = X[self.early_features_]
        
        self.model_early = self._create_gated_instance(enable_gating=False)
        self.model_early._fit_internal(X_early, y)
        logger.info("   ✓ Early season model complete")
        
        # 3. Train self as late model (all features)
        logger.info("   📅 Training LATE season model (self)...")
        self._fit_internal(X, y)
        
        logger.info("✅ Season-gated ensemble training complete!")
        
        return self

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        Train the ensemble with optional season phase gating.
        
        If season gating is enabled and temporal columns are present,
        trains two internal models for early/late season predictions.
        
        Args:
            X: Training features DataFrame
            y: Training target Series
            
        Returns:
            self
        """
        from commonv2.core.logging import get_logger
        
        logger = get_logger(f'nflfastRv3.{self._get_model_type()}')
        
        if self.enable_season_gating and self._has_temporal_columns(X):
            logger.info("🎯 Fitting with season phase gating")
            return self._fit_with_gating(X, y)
        else:
            logger.info("🎯 Fitting standard ensemble (no gating)")
            return self._fit_internal(X, y)
    
    def predict(self, X: pd.DataFrame) -> NDArray:
        """
        Generate ensemble predictions with optional season gating.
        
        Args:
            X: Features DataFrame
            
        Returns:
            Predictions array (shape depends on subclass)
        """
        if not self.enable_season_gating or not self._has_temporal_columns(X):
            # No gating - use standard prediction
            return self._predict_internal(X)
        
        # Season gating enabled
        from nflfastRv3.features.ml_pipeline.utils import SeasonPhaseGating
        
        n_samples = len(X)
        
        # Get gating mask - convert to numpy arrays with explicit dtype
        weeks = np.asarray(X['week'].values, dtype=np.int64)
        home_teams = np.asarray(X['home_team'].values, dtype=object)
        away_teams = np.asarray(X['away_team'].values, dtype=object)
        
        use_early = SeasonPhaseGating.get_gating_mask(weeks, home_teams, away_teams)
        
        early_mask = use_early
        late_mask = ~use_early
        
        # Initialize predictions array (subclass-specific shape)
        sample_pred = self._predict_internal(X.iloc[:1])
        if sample_pred.ndim == 1:
            final_preds = np.zeros(n_samples)
        else:
            final_preds = np.zeros((n_samples, sample_pred.shape[1]))
        
        # Predict early games
        if early_mask.any():
            if self.model_early is None:
                raise ValueError("Model not fitted (model_early is None)")
            early_features = self.early_features_ or []
            X_early_subset = X.loc[early_mask, early_features]
            final_preds[early_mask] = self.model_early._predict_internal(X_early_subset)
        
        # Predict late games
        if late_mask.any():
            X_late_subset = X.loc[late_mask]
            final_preds[late_mask] = self._predict_internal(X_late_subset)
        
        return final_preds
    
    @property
    def feature_importances_(self) -> Optional[NDArray]:
        """Return feature importances from XGBoost model (primary component)."""
        if self.xgboost_model and hasattr(self.xgboost_model, 'feature_importances_'):
            return self.xgboost_model.feature_importances_
        return None


class EnsembleClassifier(BaseEnsemble, ClassifierMixin):
    """
    Generic ensemble classifier with feature splitting and season gating.
    
    Features:
    - Combines XGBoost (tree features) + Elastic Net + Logistic (linear features)
    - Optional season phase gating (early vs late season models)
    - Automatic poison pill detection and removal
    - Feature selection integration
    - Configurable model weights
    
    This class provides the core ensemble logic that was previously embedded
    in GameOutcomeEnsemble, making it reusable for player prop models.
    """
    
    def __init__(
        self,
        linear_patterns: List[str],
        tree_patterns: List[str],
        weights: Optional[Dict[str, float]] = None,
        enable_season_gating: bool = True,
        xgboost_params: Optional[Dict[str, Any]] = None,
        elastic_net_params: Optional[Dict[str, Any]] = None,
        logistic_params: Optional[Dict[str, Any]] = None,
        random_state: int = 42
    ):
        """
        Initialize ensemble with feature patterns and configuration.
        
        Args:
            linear_patterns: Regex patterns for linear model features
            tree_patterns: Regex patterns for tree model features
            weights: Model weights (default: {'xgboost': 0.1, 'elastic_net': 0.45, 'logistic': 0.45})
            enable_season_gating: Whether to use season phase gating
            xgboost_params: Optional XGBoost hyperparameter overrides
            elastic_net_params: Optional Elastic Net parameter overrides
            logistic_params: Optional Logistic Regression parameter overrides
            random_state: Random seed for reproducibility
        """
        # Set default weights for classifier (2025-12-13: Rebalanced after XGBoost feature fix)
        weights = weights or {'xgboost': 0.33, 'elastic_net': 0.33, 'logistic': 0.34}
        
        # Initialize base class
        super().__init__(
            linear_patterns=linear_patterns,
            tree_patterns=tree_patterns,
            weights=weights,
            enable_season_gating=enable_season_gating,
            xgboost_params=xgboost_params,
            linear_model_params=elastic_net_params or {},
            secondary_linear_params=logistic_params or {},
            random_state=random_state
        )
        
        # Classifier-specific: classes
        self.classes_ = np.array([0, 1])
    
    def _get_model_type(self) -> str:
        """Return model type for logging."""
        return 'ensemble_classifier'
    
    def _build_models(self):
        """Build classifier model instances using ModelFactory."""
        from nflfastRv3.features.ml_pipeline.utils import ModelFactory
        
        # Build XGBoost Classifier
        # Updated 2025-12-13: Tuned for ~25 features (was optimized for 7)
        xgb_params = {
            'max_depth': 6,              # Deeper trees for more features (was 5)
            'reg_alpha': 0.15,
            'reg_lambda': 1.5,
            'colsample_bytree': 0.65,
            'learning_rate': 0.03,       # Slower for stability (was 0.05)
            'n_estimators': 300,         # More trees to compensate (was 200)
            'min_child_weight': 3,       # Allow more splits (was 4)
            'subsample': 0.7
        }
        xgb_params.update(self.xgboost_params)
        
        self.xgboost_model = ModelFactory.create_xgboost_classifier(
            hyperparameters=xgb_params,
            random_state=self.random_state
        )
        
        # Build Elastic Net (used as classifier via predict -> clip)
        en_params = {'l1_ratio': 0.5, 'alpha': 0.01}
        en_params.update(self.linear_model_params)
        
        self.linear_model = ModelFactory.create_elastic_net_pipeline(
            **en_params,
            random_state=self.random_state
        )
        
        # Build Logistic Regression
        lr_params = {'l1_ratio': 0.5, 'C': 1.0}
        lr_params.update(self.secondary_linear_params)
        
        self.secondary_linear_model = ModelFactory.create_logistic_pipeline(
            **lr_params,
            random_state=self.random_state
        )
    
    def _create_gated_instance(self, enable_gating: bool) -> 'EnsembleClassifier':
        """Create a new instance for season gating."""
        return EnsembleClassifier(
            linear_patterns=self.linear_patterns,
            tree_patterns=self.tree_patterns,
            weights=self.weights,
            enable_season_gating=enable_gating,
            xgboost_params=self.xgboost_params,
            elastic_net_params=self.linear_model_params,
            logistic_params=self.secondary_linear_params,
            random_state=self.random_state
        )
    
    def _predict_internal(self, X: pd.DataFrame) -> NDArray:
        """
        Internal prediction logic for classifier.
        
        Returns probabilities as (n_samples, 2) array.
        """
        check_is_fitted(self, ['linear_model', 'secondary_linear_model'])
        
        if self.linear_model is None or self.secondary_linear_model is None:
            raise ValueError("Linear models must be fitted before prediction")
        
        # Apply feature selection
        if self.feature_selector:
            X_selected = self.feature_selector.transform(X)
        else:
            X_selected = X
        
        # Split features
        available_cols = set(X_selected.columns)
        linear_features = self.linear_features_ or []
        tree_features = self.tree_features_ or []
        
        linear_cols = [c for c in linear_features if c in available_cols]
        tree_cols = [c for c in tree_features if c in available_cols]
        
        X_linear = X_selected[linear_cols]
        X_tree = X_selected[tree_cols]
        
        # Get predictions from XGBoost (if trained)
        if self.xgboost_model is not None:
            xgb_prob = self.xgboost_model.predict_proba(X_tree)[:, 1]
        else:
            # XGBoost was disabled due to no valid tree features
            xgb_prob = np.zeros(len(X))
        
        # Elastic Net predicts raw values, clip to [0, 1]
        en_pred = self.linear_model.predict(X_linear)
        en_prob = np.clip(en_pred, 0, 1)
        
        # Logistic Regression
        lr_prob = self.secondary_linear_model.predict_proba(X_linear)[:, 1]
        
        # Weighted average
        final_prob = (
            self.weights['xgboost'] * xgb_prob +
            self.weights['elastic_net'] * en_prob +
            self.weights['logistic'] * lr_prob
        )
        
        # Return as (n_samples, 2) array [prob_0, prob_1]
        return np.column_stack((1 - final_prob, final_prob))
    
    def predict_proba(self, X: pd.DataFrame) -> NDArray:
        """
        Generate ensemble probability predictions with optional season gating.
        
        Args:
            X: Features DataFrame
            
        Returns:
            Array of shape (n_samples, 2) with class probabilities
        """
        return self.predict(X)
    
    def predict(self, X: pd.DataFrame) -> NDArray:
        """
        Generate ensemble predictions.
        
        For classifiers, this returns probabilities via the base class predict method.
        Use predict_proba() for the same result, or threshold at 0.5 for class labels.
        
        Args:
            X: Features DataFrame
            
        Returns:
            Array of shape (n_samples, 2) with class probabilities
        """
        return super().predict(X)
    
    def predict_classes(self, X: pd.DataFrame) -> NDArray:
        """
        Generate class predictions (0 or 1).
        
        Args:
            X: Features DataFrame
            
        Returns:
            Array of class predictions
        """
        proba = self.predict_proba(X)[:, 1]
        return (proba >= 0.5).astype(int)


class EnsembleRegressor(BaseEnsemble, RegressorMixin):
    """
    Generic ensemble regressor with feature splitting and season gating.
    
    Features:
    - Combines XGBoost (tree features) + Elastic Net + Ridge (linear features)
    - Optional season phase gating (early vs late season models)
    - Automatic poison pill detection and removal
    - Feature selection integration
    - Configurable model weights
    """
    
    def __init__(
        self,
        linear_patterns: List[str],
        tree_patterns: List[str],
        weights: Optional[Dict[str, float]] = None,
        enable_season_gating: bool = True,
        xgboost_params: Optional[Dict[str, Any]] = None,
        elastic_net_params: Optional[Dict[str, Any]] = None,
        ridge_params: Optional[Dict[str, Any]] = None,
        random_state: int = 42
    ):
        """
        Initialize ensemble regressor.
        
        Args:
            linear_patterns: Regex patterns for linear model features
            tree_patterns: Regex patterns for tree model features
            weights: Model weights (default: {'xgboost': 0.2, 'elastic_net': 0.4, 'ridge': 0.4})
            enable_season_gating: Whether to use season phase gating
            xgboost_params: Optional XGBoost hyperparameter overrides
            elastic_net_params: Optional Elastic Net parameter overrides
            ridge_params: Optional Ridge Regression parameter overrides
            random_state: Random seed for reproducibility
        """
        # Set default weights for regressor
        weights = weights or {'xgboost': 0.2, 'elastic_net': 0.4, 'ridge': 0.4}
        
        # Initialize base class
        super().__init__(
            linear_patterns=linear_patterns,
            tree_patterns=tree_patterns,
            weights=weights,
            enable_season_gating=enable_season_gating,
            xgboost_params=xgboost_params,
            linear_model_params=elastic_net_params or {},
            secondary_linear_params=ridge_params or {},
            random_state=random_state
        )
    
    def _get_model_type(self) -> str:
        """Return model type for logging."""
        return 'ensemble_regressor'
    
    def _build_models(self):
        """Build regressor model instances using ModelFactory."""
        from nflfastRv3.features.ml_pipeline.utils import ModelFactory
        
        # Build XGBoost Regressor
        xgb_params = {
            'max_depth': 4,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'objective': 'reg:squarederror'
        }
        xgb_params.update(self.xgboost_params)
        
        self.xgboost_model = ModelFactory.create_xgboost_regressor(
            hyperparameters=xgb_params,
            random_state=self.random_state
        )
        
        # Build Elastic Net (Regressor)
        en_params = {'l1_ratio': 0.5, 'alpha': 0.01}
        en_params.update(self.linear_model_params)
        
        self.linear_model = ModelFactory.create_elastic_net_pipeline(
            **en_params,
            random_state=self.random_state
        )
        
        # Build Ridge Regression
        r_params = {'alpha': 1.0}
        r_params.update(self.secondary_linear_params)
        
        self.secondary_linear_model = ModelFactory.create_ridge_pipeline(
            **r_params,
            random_state=self.random_state
        )
    
    def _create_gated_instance(self, enable_gating: bool) -> 'EnsembleRegressor':
        """Create a new instance for season gating."""
        return EnsembleRegressor(
            linear_patterns=self.linear_patterns,
            tree_patterns=self.tree_patterns,
            weights=self.weights,
            enable_season_gating=enable_gating,
            xgboost_params=self.xgboost_params,
            elastic_net_params=self.linear_model_params,
            ridge_params=self.secondary_linear_params,
            random_state=self.random_state
        )
    
    def _predict_internal(self, X: pd.DataFrame) -> NDArray:
        """
        Internal prediction logic for regressor.
        
        Returns continuous predictions as 1D array.
        """
        check_is_fitted(self, ['linear_model', 'secondary_linear_model'])
        
        if self.linear_model is None or self.secondary_linear_model is None:
            raise ValueError("Linear models must be fitted before prediction")
        
        # Apply feature selection
        if self.feature_selector:
            X_selected = self.feature_selector.transform(X)
        else:
            X_selected = X
        
        # Split features
        available_cols = set(X_selected.columns)
        linear_features = self.linear_features_ or []
        tree_features = self.tree_features_ or []
        
        linear_cols = [c for c in linear_features if c in available_cols]
        tree_cols = [c for c in tree_features if c in available_cols]
        
        X_linear = X_selected[linear_cols]
        X_tree = X_selected[tree_cols]
        
        # Get predictions from XGBoost (if trained)
        if self.xgboost_model is not None:
            xgb_pred = self.xgboost_model.predict(X_tree)
        else:
            # XGBoost was disabled due to no valid tree features
            xgb_pred = np.zeros(len(X))
        
        # Get predictions from linear models
        en_pred = self.linear_model.predict(X_linear)
        r_pred = self.secondary_linear_model.predict(X_linear)
        
        # Weighted average
        final_pred = (
            self.weights['xgboost'] * xgb_pred +
            self.weights['elastic_net'] * en_pred +
            self.weights['ridge'] * r_pred
        )
        
        return final_pred


__all__ = ['BaseEnsemble', 'EnsembleClassifier', 'EnsembleRegressor']