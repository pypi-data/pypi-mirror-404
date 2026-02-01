"""Model Factory Utilities.

Factory for creating configured ML models with standardized hyperparameters.
Applicable to all ML models (game outcomes, player props, etc.).

Key Functions:
- create_xgboost_classifier(): XGBoost for binary classification
- create_xgboost_regressor(): XGBoost for regression (player props)
- create_elastic_net_pipeline(): Elastic Net with scaling
- create_logistic_pipeline(): Logistic Regression with scaling
"""

from typing import Dict, Any, Optional
from xgboost import XGBClassifier, XGBRegressor
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline


class ModelFactory:
    """Factory for creating configured ML models."""
    
    @staticmethod
    def create_xgboost_classifier(
        hyperparameters: Optional[Dict[str, Any]] = None,
        random_state: int = 42
    ) -> XGBClassifier:
        """
        Create configured XGBoost classifier for binary classification.
        
        Default hyperparameters are tuned for NFL game outcome prediction
        with strong regularization to prevent overfitting.
        
        Args:
            hyperparameters: Optional hyperparameter overrides
            random_state: Random seed for reproducibility
            
        Returns:
            Configured XGBClassifier
            
        Example:
            >>> model = ModelFactory.create_xgboost_classifier()
            >>> model.fit(X_train, y_train)
            >>> predictions = model.predict(X_test)
        """
        default_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            
            # Tree structure (conservative to prevent overfitting)
            'max_depth': 3,
            'min_child_weight': 10,
            'gamma': 1.0,
            
            # Sampling (aggressive to reduce variance)
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'colsample_bylevel': 0.7,
            
            # Regularization (strong)
            'reg_alpha': 1.0,
            'reg_lambda': 2.0,
            
            # Learning (slow and stable)
            'learning_rate': 0.01,
            'n_estimators': 500,
            
            # Other
            'random_state': random_state,
            'n_jobs': -1
        }
        
        if hyperparameters:
            default_params.update(hyperparameters)
        
        return XGBClassifier(**default_params)
    
    @staticmethod
    def create_xgboost_regressor(
        hyperparameters: Optional[Dict[str, Any]] = None,
        random_state: int = 42
    ) -> XGBRegressor:
        """
        Create configured XGBoost regressor for continuous predictions.
        
        Optimized for player prop predictions (passing yards, rushing yards, etc.)
        with moderate regularization.
        
        Args:
            hyperparameters: Optional hyperparameter overrides
            random_state: Random seed for reproducibility
            
        Returns:
            Configured XGBRegressor
            
        Example:
            >>> model = ModelFactory.create_xgboost_regressor()
            >>> model.fit(X_train, y_train)
            >>> predictions = model.predict(X_test)
        """
        default_params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            
            # Tree structure (slightly deeper for regression)
            'max_depth': 4,
            'min_child_weight': 5,
            'gamma': 0.5,
            
            # Sampling
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            
            # Regularization (moderate)
            'reg_alpha': 0.5,
            'reg_lambda': 1.0,
            
            # Learning
            'learning_rate': 0.05,
            'n_estimators': 200,
            
            # Other
            'random_state': random_state,
            'n_jobs': -1
        }
        
        if hyperparameters:
            default_params.update(hyperparameters)
        
        return XGBRegressor(**default_params)
    
    @staticmethod
    def create_elastic_net_pipeline(
        l1_ratio: float = 0.5,
        alpha: float = 0.01,
        random_state: int = 42
    ):
        """
        Create Elastic Net pipeline with feature scaling.
        
        Combines L1 (Lasso) and L2 (Ridge) regularization for feature selection
        and coefficient shrinkage. Requires feature scaling.
        
        Args:
            l1_ratio: L1/L2 balance (0 = Ridge, 1 = Lasso, 0.5 = balanced)
            alpha: Regularization strength (higher = more regularization)
            random_state: Random seed for reproducibility
            
        Returns:
            Pipeline with StandardScaler + ElasticNet
            
        Example:
            >>> model = ModelFactory.create_elastic_net_pipeline()
            >>> model.fit(X_train, y_train)
            >>> predictions = model.predict(X_test)
        """
        return make_pipeline(
            StandardScaler(),
            ElasticNet(
                l1_ratio=l1_ratio,
                alpha=alpha,
                max_iter=10000,
                random_state=random_state
            )
        )
    
    @staticmethod
    def create_logistic_pipeline(
        l1_ratio: float = 0.5,
        C: float = 1.0,
        random_state: int = 42
    ):
        """
        Create Logistic Regression pipeline with feature scaling.
        
        Uses elastic net penalty for binary classification with feature scaling.
        
        Args:
            l1_ratio: L1/L2 balance (0 = Ridge, 1 = Lasso, 0.5 = balanced)
            C: Inverse regularization strength (lower = more regularization)
            random_state: Random seed for reproducibility
            
        Returns:
            Pipeline with StandardScaler + LogisticRegression
            
        Example:
            >>> model = ModelFactory.create_logistic_pipeline()
            >>> model.fit(X_train, y_train)
            >>> predictions = model.predict_proba(X_test)
        """
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(
                penalty='elasticnet',
                solver='saga',
                l1_ratio=l1_ratio,
                C=C,
                max_iter=10000,
                random_state=random_state
            )
        )
    
    @staticmethod
    def create_ridge_pipeline(
        alpha: float = 1.0,
        random_state: int = 42
    ):
        """
        Create Ridge Regression pipeline with feature scaling.
        
        Standard L2 regularization for regression.
        
        Args:
            alpha: Regularization strength
            random_state: Random seed for reproducibility
            
        Returns:
            Pipeline with StandardScaler + Ridge
        """
        return make_pipeline(
            StandardScaler(),
            Ridge(
                alpha=alpha,
                random_state=random_state
            )
        )


__all__ = ['ModelFactory']