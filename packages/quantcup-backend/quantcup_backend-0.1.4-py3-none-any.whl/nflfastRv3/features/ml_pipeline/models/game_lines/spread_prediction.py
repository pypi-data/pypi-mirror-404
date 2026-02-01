"""
Spread Prediction Model

Binary classification model to predict whether the home team will cover the spread.
Target: home_covers_spread (0 = fail to cover, 1 = cover)

Features:
- All game_outcome features (rolling metrics, differentials)
- Spread line info
- ATS (Against The Spread) trends

Model Type: Ensemble Classifier (XGBoost + ElasticNet + Logistic)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, List, cast
from numpy.typing import NDArray
from sklearn.base import BaseEstimator
from commonv2 import get_logger
from ...utils.feature_registry import FeatureRegistry
from ...utils.feature_patterns import FeaturePatterns
from ..base.ensemble import EnsembleClassifier

# Module logger
logger = get_logger(__name__)

class SpreadPredictionConfig:
    """
    Spread prediction model configuration and utilities.
    
    Encapsulates all spread-specific logic:
    - Target calculation (home_covers_spread)
    - Feature engineering (spread-specific features)
    - Model configuration
    """
    
    # Model metadata
    MODEL_NAME = 'spread_prediction'
    MODEL_TYPE = 'binary_classification'
    TARGET_VARIABLE = 'home_covers_spread'
    
    # Metadata columns
    METADATA_COLUMNS = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team', 'spread_line']
    
    # Data source configuration
    FEATURE_TABLES = {
        'rolling_metrics': 'rolling_metrics_v1',
        'nextgen': 'nextgen_features_v1',
        'contextual': 'contextual_features_v1',
        'injury': 'injury_features_v1'
    }
    FEATURE_SCHEMA = 'features'
    TARGET_TABLE = 'dim_game'
    TARGET_SCHEMA = 'warehouse'
    
    # Backward compatibility
    FEATURE_TABLE = 'rolling_metrics_v1'
    
    # Prediction configuration
    PREDICTION_CONFIG = {
        'requires_trained_model': True,
        'output_fields': ['game_id', 'prediction', 'confidence', 'cover_prob', 'fail_prob'],
        'min_confidence': 0.50,
        'recommended_confidence': 0.525, # Breakeven is ~52.4%
        'confidence_thresholds': {
            'conservative': 0.55,
            'balanced': 0.53,
            'aggressive': 0.51,
        }
    }
    
    # Versioning configuration
    VERSIONING_CONFIG = {
        'path_template': 'ml/models/spread_prediction/{tag}/model.joblib',
        'default_tag': 'latest',
        'metadata_path': 'ml/models/spread_prediction/versions.json'
    }
    
    # Training requirements
    MIN_TRAIN_YEARS = 2
    RECOMMENDED_TRAIN_YEARS = 3
    TEST_SCOPE = 'week'
    
    # Walk-forward support
    SUPPORTS_WALK_FORWARD = True
    WALK_FORWARD_CONFIG = {
        'enabled_by_default': True,
        'min_completed_weeks': 1,
        'temporal_safety_hours': 24,
        'description': 'Automatically includes completed weeks from test season in training'
    }

    @staticmethod
    def get_stability_score(team: str, week: int) -> float:
        from nflfastRv3.features.ml_pipeline.utils import SeasonPhaseGating
        return SeasonPhaseGating.get_stability_score(team, week)

    @staticmethod
    def apply_walk_forward(train_seasons, test_season, test_week, db_service):
        from nflfastRv3.shared.temporal_validator import TemporalValidator
        return TemporalValidator.build_walk_forward_config(
            train_seasons, test_season, test_week, db_service, logger
        )
    
    @staticmethod
    def get_hyperparameters(random_state: int = 42) -> Dict[str, Any]:
        """
        Get XGBoost hyperparameters for spread prediction.
        Spread is harder than moneyline, so we need more regularization.
        """
        return {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 3,              # Shallow trees to prevent overfitting noise
            'min_child_weight': 15,      # High weight to require strong patterns
            'gamma': 2.0,                # High gamma to prune weak splits
            'subsample': 0.6,            # High randomness
            'colsample_bytree': 0.6,
            'reg_alpha': 2.0,            # Strong L1
            'reg_lambda': 4.0,           # Strong L2
            'learning_rate': 0.01,
            'n_estimators': 600,
            'random_state': random_state,
            'n_jobs': -1
        }
    
    @staticmethod
    def create_model(random_state: int = 42) -> 'SpreadPredictionModel':
        return SpreadPredictionModel(random_state=random_state)
    
    @staticmethod
    def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer spread-specific features.
        Reuses GameOutcome logic but adds spread-specific context.
        """
        from nflfastRv3.features.ml_pipeline.utils import FeatureSynthesis
        
        logger.info("🔍 Engineering spread prediction features")
        
        # 1. Reuse Game Outcome Differential Features
        # We can call the GameOutcomeConfig method if we want, or duplicate the logic.
        # Duplicating for now to allow divergence later, but keeping it consistent.
        
        base_features = [
            'rolling_4g_epa_offense', 'rolling_4g_epa_defense', 'rolling_4g_point_diff',
            'rolling_4g_points_for', 'rolling_4g_points_against', 'rolling_4g_win_rate',
            'rolling_8g_epa_offense', 'rolling_8g_epa_defense', 'rolling_8g_point_diff',
            'rolling_16g_epa_offense', 'rolling_16g_epa_defense', 'rolling_16g_point_diff',
            'epa_per_play_offense_trending', 'epa_per_play_defense_trending',
            'recent_4g_win_rate', 'recent_4g_avg_margin', 'recent_4g_epa_trend',
        ]
        
        df = FeatureSynthesis.create_differential_features(
            df, base_features, prefix_a='home', prefix_b='away', suffix='_diff'
        )
        
        # 2. Spread-Specific Features
        # Calculate "ATS Margin" (how much they beat the spread by)
        # This requires historical spread data which might be in rolling metrics or need to be calculated
        # For now, we'll focus on the spread_line itself as a feature
        
        if 'spread_line' in df.columns:
            # Interaction: Spread * EPA Diff (Does the market over/under value EPA?)
            df['interaction_spread_epa'] = df['spread_line'] * df['rolling_16g_epa_offense_diff']
            
            # Interaction: Spread * Home Field (Is home field overvalued?)
            if 'stadium_home_win_rate' in df.columns:
                df['interaction_spread_home'] = df['spread_line'] * df['stadium_home_win_rate']
        
        logger.info(f"✓ Engineered spread features: {len(df.columns)} total columns")
        return df
    
    @staticmethod
    def select_features(df: pd.DataFrame) -> pd.DataFrame:
        """Select features for spread model."""
        logger.info("🔍 Selecting features for spread model")
        
        # Get active features from Registry
        active_features = FeatureRegistry.get_active_features()
        
        # Add spread-specific features that might not be in the default registry yet
        # For now, we'll assume they are or we'll add them dynamically
        spread_features = ['spread_line', 'interaction_spread_epa', 'interaction_spread_home']
        available_spread_features = [f for f in spread_features if f in df.columns]
        
        # Combine
        features_to_use = list(set(active_features + available_spread_features))
        available_features = [f for f in features_to_use if f in df.columns]
        
        # Metadata and target
        metadata_cols = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team', 'spread_line']
        target_cols = ['home_covers_spread']
        
        final_columns = metadata_cols + available_features + target_cols
        
        if 'home_covers_spread' not in df.columns:
             raise ValueError("Target 'home_covers_spread' not found in DataFrame")
             
        return df[[col for col in final_columns if col in df.columns]].copy()
    
    @staticmethod
    def prepare_data(features_df: pd.DataFrame, target_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for spread prediction.
        Calculates home_covers_spread target.
        """
        import gc
        from nflfastRv3.features.ml_pipeline.utils import MergeUtils
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        logger.info("🔍 Preparing spread prediction data...")
        
        # Step 1: Filter and Create Target
        # Ensure spread_line exists
        if 'spread_line' not in target_df.columns:
            raise ValueError("Target table missing 'spread_line' column")
            
        target_df = target_df[
            (target_df['home_score'].notna()) &
            (target_df['away_score'].notna()) &
            (target_df['spread_line'].notna())
        ].copy()
        
        # Calculate Cover
        # If spread_line is -3.5 (Home favored), Home Score + (-3.5) > Away Score
        target_df['home_covers_spread'] = (
            (target_df['home_score'] + target_df['spread_line']) > target_df['away_score']
        ).astype(int)
        
        # Push: If (Home + Spread) == Away, it's a push.
        # For binary classification, we usually drop pushes or treat as loss.
        # Let's drop pushes for training to avoid noise.
        target_df['spread_margin'] = (target_df['home_score'] + target_df['spread_line']) - target_df['away_score']
        push_mask = target_df['spread_margin'] == 0
        if push_mask.any():
            logger.info(f"   ℹ️ Dropping {push_mask.sum()} pushes from training data")
            target_df = target_df[~push_mask].copy()
        
        logger.info(f"✓ Filtered to {len(target_df):,} valid spread results")
        
        # Step 2: Merge Features (Reuse GameOutcome logic via MergeUtils/Manual)
        # ... (Copying merge logic from GameOutcomeConfig for consistency)
        
        # Merge Home
        home_features = features_df.rename(columns={
            col: f'home_{col}' for col in features_df.columns
            if col not in ['game_id', 'season', 'week', 'team']
        })
        game_df = target_df.merge(
            home_features,
            left_on=['game_id', 'season', 'week', 'home_team'],
            right_on=['game_id', 'season', 'week', 'team'],
            how='inner'
        ).drop(columns=['team'], errors='ignore')
        del home_features
        
        # Merge Away
        away_features = features_df.rename(columns={
            col: f'away_{col}' for col in features_df.columns
            if col not in ['game_id', 'season', 'week', 'team']
        })
        game_df = game_df.merge(
            away_features,
            left_on=['game_id', 'season', 'week', 'away_team'],
            right_on=['game_id', 'season', 'week', 'team'],
            how='inner'
        ).drop(columns=['team'], errors='ignore')
        del away_features
        gc.collect()
        
        # Step 3: Load Contextual/NextGen/Injury (Optional but recommended)
        # For brevity, we'll skip the complex loading here and assume basic features for now,
        # or we can copy the block from GameOutcomeConfig if we want full parity.
        # Let's stick to basic rolling metrics for the first pass of Spread model to ensure stability.
        
        return game_df

    @staticmethod
    def evaluate_model(model, X_test, y_test, y_pred, y_pred_proba):
        """Evaluate spread model."""
        from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
        
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba[:, 1])
        
        logger.info(f"Spread Model Performance:")
        logger.info(f"  Accuracy: {accuracy:.3f}")
        logger.info(f"  AUC-ROC: {auc:.3f}")
        
        return {
            'accuracy': accuracy,
            'auc': auc,
            'classification_report': classification_report(y_test, y_pred)
        }

class SpreadPredictionModel(EnsembleClassifier):
    """
    Spread prediction model using Ensemble Architecture.
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None, random_state: int = 42) -> None:
        # Spread is harder, so we might want different weights.
        # For now, stick to the proven 45/45/10 split.
        weights = weights or {'xgboost': 0.1, 'elastic_net': 0.45, 'logistic': 0.45}
        
        # Custom XGBoost params for spread
        xgboost_params = SpreadPredictionConfig.get_hyperparameters(random_state)
        
        super().__init__(
            linear_patterns=FeaturePatterns.SPREAD_LINEAR,
            tree_patterns=FeaturePatterns.SPREAD_TREE,
            weights=weights,
            enable_season_gating=True,
            xgboost_params=xgboost_params,
            elastic_net_params={'l1_ratio': 0.7, 'alpha': 0.05}, # Stronger regularization
            logistic_params={'l1_ratio': 0.7, 'C': 0.5},         # Stronger regularization
            random_state=random_state
        )

def create_spread_prediction_model(random_state: int = 42) -> SpreadPredictionModel:
    return SpreadPredictionModel(random_state=random_state)

__all__ = ['SpreadPredictionConfig', 'SpreadPredictionModel', 'create_spread_prediction_model']