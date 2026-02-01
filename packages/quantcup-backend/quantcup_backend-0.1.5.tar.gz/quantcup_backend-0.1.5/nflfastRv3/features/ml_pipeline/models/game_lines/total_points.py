"""
Total Points (Over/Under) Prediction Model

Binary classification model to predict whether the game total will go OVER the line.
Target: over_total (0 = Under, 1 = Over)

Features:
- Scoring trends (Points For/Against)
- EPA metrics (Offense/Defense)
- Pace of play
- Weather and Stadium conditions
- Total line info

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

class TotalPointsConfig:
    """
    Total points prediction model configuration and utilities.
    """
    
    # Model metadata
    MODEL_NAME = 'total_points'
    MODEL_TYPE = 'binary_classification'
    TARGET_VARIABLE = 'over_total'
    
    # Metadata columns
    METADATA_COLUMNS = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team', 'total_line']
    
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
        'output_fields': ['game_id', 'prediction', 'confidence', 'over_prob', 'under_prob'],
        'min_confidence': 0.50,
        'recommended_confidence': 0.525,
        'confidence_thresholds': {
            'conservative': 0.55,
            'balanced': 0.53,
            'aggressive': 0.51,
        }
    }
    
    # Versioning configuration
    VERSIONING_CONFIG = {
        'path_template': 'ml/models/total_points/{tag}/model.joblib',
        'default_tag': 'latest',
        'metadata_path': 'ml/models/total_points/versions.json'
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
        Get XGBoost hyperparameters for total points.
        Totals are notoriously noisy, so we need extreme regularization.
        """
        return {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 3,
            'min_child_weight': 20,      # Very high to prevent overfitting
            'gamma': 3.0,                # Very high gamma
            'subsample': 0.6,
            'colsample_bytree': 0.6,
            'reg_alpha': 3.0,            # Strong L1
            'reg_lambda': 5.0,           # Strong L2
            'learning_rate': 0.01,
            'n_estimators': 500,
            'random_state': random_state,
            'n_jobs': -1
        }
    
    @staticmethod
    def create_model(random_state: int = 42) -> 'TotalPointsModel':
        return TotalPointsModel(random_state=random_state)
    
    @staticmethod
    def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer total points features.
        Focuses on combined offensive/defensive metrics rather than differentials.
        """
        logger.info("🔍 Engineering total points features")
        
        # 1. Combined Metrics (Home Offense + Away Defense, etc.)
        # We need to sum metrics instead of differencing them
        
        metrics = [
            'rolling_4g_points_for', 'rolling_4g_points_against',
            'rolling_8g_points_for', 'rolling_8g_points_against',
            'rolling_16g_points_for', 'rolling_16g_points_against',
            'rolling_4g_epa_offense', 'rolling_4g_epa_defense',
            'rolling_8g_epa_offense', 'rolling_8g_epa_defense'
        ]
        
        for metric in metrics:
            if f'home_{metric}' in df.columns and f'away_{metric}' in df.columns:
                # Sum of Home and Away metrics (e.g., Home Points For + Away Points For)
                # This gives a sense of the "total energy" of the game
                df[f'{metric}_sum'] = df[f'home_{metric}'] + df[f'away_{metric}']
                
        # 2. Projected Totals based on averages
        if 'home_rolling_4g_points_for' in df.columns and 'away_rolling_4g_points_for' in df.columns:
            df['projected_total_4g'] = df['home_rolling_4g_points_for'] + df['away_rolling_4g_points_for']
            
        if 'home_rolling_16g_points_for' in df.columns and 'away_rolling_16g_points_for' in df.columns:
            df['projected_total_16g'] = df['home_rolling_16g_points_for'] + df['away_rolling_16g_points_for']
            
        # 3. Total Line Interactions
        if 'total_line' in df.columns:
            if 'projected_total_4g' in df.columns:
                df['total_diff_4g'] = df['projected_total_4g'] - df['total_line']
            
            if 'projected_total_16g' in df.columns:
                df['total_diff_16g'] = df['projected_total_16g'] - df['total_line']
                
        logger.info(f"✓ Engineered total points features: {len(df.columns)} total columns")
        return df
    
    @staticmethod
    def select_features(df: pd.DataFrame) -> pd.DataFrame:
        """Select features for total points model."""
        logger.info("🔍 Selecting features for total points model")
        
        # Get active features from Registry
        active_features = FeatureRegistry.get_active_features()
        
        # Add total-specific features
        total_features = [
            'total_line', 'projected_total_4g', 'projected_total_16g',
            'total_diff_4g', 'total_diff_16g'
        ]
        # Also include the summed metrics we created
        summed_metrics = [c for c in df.columns if c.endswith('_sum')]
        
        features_to_use = list(set(active_features + total_features + summed_metrics))
        available_features = [f for f in features_to_use if f in df.columns]
        
        # Metadata and target
        metadata_cols = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team', 'total_line']
        target_cols = ['over_total']
        
        final_columns = metadata_cols + available_features + target_cols
        
        if 'over_total' not in df.columns:
             raise ValueError("Target 'over_total' not found in DataFrame")
             
        return df[[col for col in final_columns if col in df.columns]].copy()
    
    @staticmethod
    def prepare_data(features_df: pd.DataFrame, target_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for total points prediction.
        Calculates over_total target.
        """
        import gc
        
        logger.info("🔍 Preparing total points prediction data...")
        
        # Step 1: Filter and Create Target
        if 'total_line' not in target_df.columns:
            raise ValueError("Target table missing 'total_line' column")
            
        target_df = target_df[
            (target_df['home_score'].notna()) &
            (target_df['away_score'].notna()) &
            (target_df['total_line'].notna())
        ].copy()
        
        # Calculate Over
        target_df['actual_total'] = target_df['home_score'] + target_df['away_score']
        target_df['over_total'] = (target_df['actual_total'] > target_df['total_line']).astype(int)
        
        # Drop pushes
        push_mask = target_df['actual_total'] == target_df['total_line']
        if push_mask.any():
            logger.info(f"   ℹ️ Dropping {push_mask.sum()} pushes from training data")
            target_df = target_df[~push_mask].copy()
        
        logger.info(f"✓ Filtered to {len(target_df):,} valid total results")
        
        # Step 2: Merge Features (Reuse GameOutcome logic)
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
        
        return game_df

    @staticmethod
    def evaluate_model(model, X_test, y_test, y_pred, y_pred_proba):
        """Evaluate total points model."""
        from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
        
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba[:, 1])
        
        logger.info(f"Total Points Model Performance:")
        logger.info(f"  Accuracy: {accuracy:.3f}")
        logger.info(f"  AUC-ROC: {auc:.3f}")
        
        return {
            'accuracy': accuracy,
            'auc': auc,
            'classification_report': classification_report(y_test, y_pred)
        }

class TotalPointsModel(EnsembleClassifier):
    """
    Total points prediction model using Ensemble Architecture.
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None, random_state: int = 42) -> None:
        weights = weights or {'xgboost': 0.1, 'elastic_net': 0.45, 'logistic': 0.45}
        
        xgboost_params = TotalPointsConfig.get_hyperparameters(random_state)
        
        super().__init__(
            linear_patterns=FeaturePatterns.TOTAL_LINEAR,
            tree_patterns=FeaturePatterns.TOTAL_TREE,
            weights=weights,
            enable_season_gating=True,
            xgboost_params=xgboost_params,
            elastic_net_params={'l1_ratio': 0.8, 'alpha': 0.1}, # Very strong regularization
            logistic_params={'l1_ratio': 0.8, 'C': 0.1},        # Very strong regularization
            random_state=random_state
        )

def create_total_points_model(random_state: int = 42) -> TotalPointsModel:
    return TotalPointsModel(random_state=random_state)

__all__ = ['TotalPointsConfig', 'TotalPointsModel', 'create_total_points_model']