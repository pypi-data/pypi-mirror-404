"""
Game Outcome Prediction Model

Binary classification model to predict which team wins the game.
Target: home_team_won (0 = away win, 1 = home win)

Features:
- Rolling EPA metrics (4g, 8g, 16g)
- Point differential trends
- Win rate trends
- Offensive/defensive efficiency
- Recent form indicators

Model Type: XGBoost Binary Classifier
Evaluation Metrics: Accuracy, AUC-ROC, Precision, Recall
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

# Module-level constants for safe merging
BASE_GAME_COLS = {"game_date", "home_team", "away_team", "home_score", "away_score"}

def safe_merge_game_features(game_df, feat_df, keys, *, name, logger):
    """
    Safely merge game-level features while protecting identity columns.
    
    Contract: game_df owns identity columns (home_team, away_team, scores, dates).
              Feature tables must only contribute computed features.
    
    Args:
        game_df: Target DataFrame (owns identity)
        feat_df: Feature DataFrame (should only have keys + features)
        keys: List of merge keys (e.g., ['game_id', 'season', 'week'])
        name: Feature table name for logging
        logger: Logger instance
    
    Returns:
        Merged DataFrame with protections against column clobbering
    
    Raises:
        ValueError: If feature table contains overlapping non-key columns
    """
    if feat_df is None or feat_df.empty:
        return game_df
    
    feat_df = feat_df.copy()
    
    # 1) Drop identity columns from feature table (should never be present)
    drop_these = list((set(feat_df.columns) & BASE_GAME_COLS) - set(keys))
    if drop_these:
        logger.warning(f"⚠️  Dropping identity cols from {name}: {drop_these} (feature tables should not contain these)")
        feat_df = feat_df.drop(columns=drop_these, errors="ignore")
    
    # 2) Guard against ANY remaining overlap (non-key columns)
    overlaps = (set(game_df.columns) & set(feat_df.columns)) - set(keys)
    if overlaps:
        # Fail-fast mode (detects merge conflicts immediately)
        raise ValueError(
            f"❌ {name} merge has overlapping columns (non-key): {sorted(overlaps)}. "
            f"Feature tables must only contribute new features, not overwrite existing columns."
        )
    
    return game_df.merge(feat_df, on=keys, how="left", validate="one_to_one")

class GameOutcomeModel(EnsembleClassifier):
    """
    Complete game outcome prediction model.
    
    Binary classification model to predict which team wins the game.
    Combines configuration, data preparation, feature engineering, and ensemble prediction
    in a single cohesive class.
    
    Features:
    - Rolling EPA metrics (4g, 8g, 16g)
    - Point differential trends
    - Win rate trends
    - Offensive/defensive efficiency
    - Recent form indicators
    
    Model Architecture:
    - XGBoost (tree features) + Elastic Net + Logistic Regression (linear features)
    - Season phase gating for temporal stability
    - Automatic poison pill detection
    """
    
    # ===== CLASS ATTRIBUTES (Configuration) =====
    
    # Model metadata
    MODEL_NAME = 'game_outcome'
    MODEL_TYPE = 'binary_classification'
    TARGET_VARIABLE = 'home_team_won'
    
    # Metadata columns (used for train/test split)
    METADATA_COLUMNS = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team']
    
    # Data source configuration
    FEATURE_TABLES = {
        'rolling_metrics': 'rolling_metrics_v1',
        'nextgen': 'nextgen_features_v1',
        'contextual': 'contextual_features_v1',
        'player_availability': 'player_availability_v1',  # Updated 2026-01-25: Replaces injury_features_v1
        'weather': 'weather_features_v1'  # Updated 2026-01-27: V1 observable weather features
    }
    FEATURE_SCHEMA = 'features'
    TARGET_TABLE = 'dim_game'
    TARGET_SCHEMA = 'warehouse'
    
    # Backward compatibility
    FEATURE_TABLE = 'rolling_metrics_v1'  # Primary feature table for trainer
    
    # Prediction configuration
    PREDICTION_CONFIG = {
        'requires_trained_model': True,
        'output_fields': ['game_id', 'prediction', 'confidence', 'home_win_prob', 'away_win_prob'],
        'min_confidence': 0.50,
        'recommended_confidence': 0.60,
        'confidence_thresholds': {
            'conservative': 0.55,    # More predictions, lower accuracy
            'balanced': 0.60,         # Recommended default
            'aggressive': 0.70,       # Fewer predictions, higher accuracy
            'very_aggressive': 0.80   # Very selective
        },
        'threshold_guidance': {
            0.55: "Conservative - Predicts ~80% of games, ~58% accuracy",
            0.60: "Balanced - Predicts ~60% of games, ~62% accuracy (RECOMMENDED)",
            0.70: "Aggressive - Predicts ~30% of games, ~68% accuracy",
            0.80: "Very Aggressive - Predicts ~10% of games, ~75% accuracy"
        }
    }
    
    # Versioning configuration
    VERSIONING_CONFIG = {
        'path_template': 'ml/models/game_outcome/{tag}/model.joblib',
        'default_tag': 'latest',
        'metadata_path': 'ml/models/game_outcome/versions.json'
    }
    
    # Training requirements
    MIN_TRAIN_YEARS = 2
    RECOMMENDED_TRAIN_YEARS = 3
    TEST_SCOPE = 'week'  # Recommended testing scope ('week' or 'season')
    
    # Walk-forward validation configuration
    SUPPORTS_WALK_FORWARD = True
    WALK_FORWARD_CONFIG = {
        'enabled_by_default': True,
        'min_completed_weeks': 1,
        'temporal_safety_hours': 24,
        'description': 'Automatically includes completed weeks from test season in training'
    }
    
    # ===== STATIC METHODS (Data Preparation & Utilities) =====
    
    @staticmethod
    def get_stability_score(team: str, week: int) -> float:
        """
        Get stability score for a team at a given week.
        
        Delegates to SeasonPhaseGating utility.
        
        Returns:
            float: 0.0 (Unstable) to 1.0 (Stable)
        """
        from nflfastRv3.features.ml_pipeline.utils import SeasonPhaseGating
        return SeasonPhaseGating.get_stability_score(team, week)

    @staticmethod
    def apply_walk_forward(
        train_seasons: str,
        test_season: int,
        test_week: int,
        db_service: Any,
        logger=None,
        bucket_adapter=None
    ) -> Dict[str, Any]:
        """
        Apply walk-forward validation for game outcome model.
        
        Delegates to shared TemporalValidator to prevent code duplication.
        
        Args:
            train_seasons: Base training seasons string
            test_season: Test season year
            test_week: Test week number
            db_service: Database service instance
            logger: Optional logger instance
            bucket_adapter: Optional BucketAdapter instance (uses DI with fallback pattern)
        """
        from nflfastRv3.shared.temporal_validator import TemporalValidator
        
        if logger is None:
            from commonv2 import get_logger
            logger = get_logger(__name__)
        
        logger.info(f"🔍 Applying walk-forward validation for {GameOutcomeModel.MODEL_NAME}")
        
        # Validate test week hasn't occurred yet
        is_safe, warning = TemporalValidator.validate_test_week(
            test_season, test_week, db_service, logger, bucket_adapter
        )
        
        if not is_safe:
            logger.warning(warning)
            logger.warning("⚠️ Proceeding with walk-forward despite temporal leakage risk")
        
        # Build walk-forward configuration
        return TemporalValidator.build_walk_forward_config(
            train_seasons, test_season, test_week, db_service, logger, bucket_adapter
        )
    
    @staticmethod
    def get_hyperparameters(random_state: int = 42) -> Dict[str, Any]:
        """
        Get XGBoost hyperparameters with increased regularization.
        
        Changes from v1 (2025-11-09):
        - Reduced max_depth: 6 → 4 (prevent overfitting to training noise)
        - Reduced learning_rate: 0.1 → 0.05 (slower, more stable convergence)
        - Reduced subsample: 0.8 → 0.7 (more randomness per tree)
        - Reduced colsample_bytree: 0.8 → 0.7 (prevent feature memorization)
        - Added reg_alpha: 0.1 (L1 regularization on weights)
        - Added reg_lambda: 1.0 (L2 regularization on weights)
        - Added min_child_weight: 3 (require more samples per leaf)
        
        These changes address overfitting issues discovered in Phase 6-7 analysis
        where identical feature importance across all tests indicated the model
        was memorizing training patterns rather than learning generalizable relationships.
        
        Args:
            random_state: Random seed for reproducibility
            
        Returns:
            dict: XGBoost hyperparameters
        """
        return {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            
            # Tree structure (more conservative)
            'max_depth': 3,              # Reduce from 4
            'min_child_weight': 10,      # Increase from 5 (Requires more games to create a rule)
            'gamma': 1.0,                # Increase from 0.5 (Requires major improvement to split)
            
            # Sampling (more aggressive)
            'subsample': 0.7,            # Reduce from 0.8 (Reduces reliance on specific games)
            'colsample_bytree': 0.7,     # Reduce from 0.8
            'colsample_bylevel': 0.7,    # Add level sampling
            
            # Regularization (stronger)
            'reg_alpha': 1.0,            # L1 regularization
            'reg_lambda': 2.0,           # L2 regularization (increase from 1.0)
            
            # Learning (slower, more stable)
            'learning_rate': 0.01,       # Reduce from 0.05
            'n_estimators': 500,         # Increase to compensate
            
            # Other
            'random_state': random_state,
            'n_jobs': -1
        }
    
    @staticmethod
    def create_model(random_state: int = 42) -> 'GameOutcomeModel':
        """
        Create configured Ensemble model for game outcome prediction.
        
        Returns:
            GameOutcomeModel: Configured ensemble model instance
        """
        return GameOutcomeModel(random_state=random_state)
    
    @staticmethod
    def engineer_features(df: pd.DataFrame, logger=None) -> pd.DataFrame:
        """
        Engineer game outcome-specific features.
        
        Delegates to FeatureSynthesis utility for differential, composite, and interaction features.
        This is the core feature engineering for binary win/loss prediction.
        
        Args:
            df: Game-level dataset with home/away prefixed features
            logger: Optional logger instance
            
        Returns:
            DataFrame with engineered differential features
        """
        from nflfastRv3.features.ml_pipeline.utils import FeatureSynthesis
        
        if logger is None:
            from commonv2 import get_logger
            logger = get_logger(__name__)
        
        logger.info("🔍 Engineering game outcome differential features")
        
        # Base features for differentials (using actual column names from rolling_metrics_v1)
        base_features = [
            # 4-game rolling metrics
            'rolling_4g_epa_offense', 'rolling_4g_epa_defense', 'rolling_4g_point_diff',
            'rolling_4g_points_for', 'rolling_4g_points_against', 'rolling_4g_win_rate',
            'rolling_4g_red_zone_eff', 'rolling_4g_third_down_eff', 'rolling_4g_turnover_diff',
            
            # 8-game rolling metrics
            'rolling_8g_epa_offense', 'rolling_8g_epa_defense', 'rolling_8g_point_diff',
            'rolling_8g_points_for', 'rolling_8g_points_against', 'rolling_8g_win_rate',
            'rolling_8g_red_zone_eff', 'rolling_8g_third_down_eff', 'rolling_8g_turnover_diff',
            
            # 16-game rolling metrics
            'rolling_16g_epa_offense', 'rolling_16g_epa_defense', 'rolling_16g_point_diff',
            
            # Trending metrics
            'epa_per_play_offense_trending', 'epa_per_play_defense_trending',
            'point_differential_trending',
            
            # Recent form
            'recent_4g_win_rate', 'recent_4g_avg_margin', 'recent_4g_epa_trend',
        ]
        
        # Create differential features (home - away)
        df = FeatureSynthesis.create_differential_features(
            df, base_features, prefix_a='home', prefix_b='away', suffix='_diff'
        )
        
        # Advanced composite features
        composites = [
            ('home_rolling_4g_epa_offense', 'home_rolling_4g_epa_defense',
             'away_rolling_4g_epa_offense', 'away_rolling_4g_epa_defense', 'epa_advantage_4game'),
            ('home_rolling_8g_epa_offense', 'home_rolling_8g_epa_defense',
             'away_rolling_8g_epa_offense', 'away_rolling_8g_epa_defense', 'epa_advantage_8game'),
        ]
        df = FeatureSynthesis.create_composite_features(df, composites)
        
        # Simple differentials for advantage metrics
        df = FeatureSynthesis.create_simple_differential(
            df, 'home_recent_4g_win_rate', 'away_recent_4g_win_rate', 'win_rate_advantage'
        )
        df = FeatureSynthesis.create_simple_differential(
            df, 'home_recent_4g_epa_trend', 'away_recent_4g_epa_trend', 'momentum_advantage'
        )
        
        # Interaction Features (Phase 3)
        # interaction_form_home: Recent form * Home field advantage
        # interaction_epa_home: EPA Advantage * Home Field
        interactions = [
            ('recent_4g_epa_trend_diff', 'stadium_home_win_rate', 'interaction_form_home'),
            ('epa_advantage_8game', 'stadium_home_win_rate', 'interaction_epa_home'),
        ]
        df = FeatureSynthesis.create_interaction_features(df, interactions)
        
        # Phase 2: Non-Linear Interactions (2025-12-13 - Moved from rolling_metrics.py)
        # CRITICAL: Create interactions HERE (after all merges) not in rolling_metrics.py
        # Required columns now available: differentials + contextual features
        logger.info("🔍 Creating Phase 2 non-linear interactions")
        
        interactions_created = []
        
        # Interaction 1: Polynomial (EPA × Dome)^2
        if all(col in df.columns for col in ['rolling_8g_epa_offense_diff', 'is_dome']):
            df['epa_dome_poly_interaction'] = (
                df['rolling_8g_epa_offense_diff'] * df['is_dome']
            ) ** 2
            interactions_created.append('epa_dome_poly_interaction (polynomial)')
        else:
            logger.warning("⚠️  Skipping epa_dome_poly_interaction - missing columns")
        
        # Interaction 2: Threshold (Point Diff > 3) × Conference
        if all(col in df.columns for col in ['rolling_4g_point_diff_diff', 'is_conference_game']):
            df['conference_threshold_intensity'] = (
                (df['rolling_4g_point_diff_diff'] > 3).astype(float) * df['is_conference_game']
            )
            interactions_created.append('conference_threshold_intensity (threshold)')
        else:
            logger.warning("⚠️  Skipping conference_threshold_intensity - missing columns")
        
        # Interaction 3: Ratio with variable denominator (Rest / Combined Performance Variance)
        # Uses both offense AND defense std for combined performance consistency measure
        if all(col in df.columns for col in ['rest_days_diff', 'home_rolling_4g_epa_offense_std', 'home_rolling_4g_epa_defense_std']):
            df['rest_performance_ratio'] = df['rest_days_diff'] / (
                df['home_rolling_4g_epa_offense_std'] + df['home_rolling_4g_epa_defense_std'] + 0.01
            )
            interactions_created.append('rest_performance_ratio (ratio)')
        else:
            logger.warning("⚠️  Skipping rest_performance_ratio - missing columns")
        
        # Interaction 4: Log(Stadium rate) × Form
        if all(col in df.columns for col in ['stadium_home_win_rate', 'recent_4g_win_rate_diff']):
            df['stadium_form_log_synergy'] = (
                np.log(df['stadium_home_win_rate'] * 100 + 1) * df['recent_4g_win_rate_diff']
            )
            interactions_created.append('stadium_form_log_synergy (logarithmic)')
        else:
            logger.warning("⚠️  Skipping stadium_form_log_synergy - missing columns")
        
        # Interaction 5: Threshold EPA × Altitude (optional)
        if all(col in df.columns for col in ['rolling_8g_epa_offense_diff', 'is_high_altitude']):
            df['epa_altitude_threshold'] = (
                (np.abs(df['rolling_8g_epa_offense_diff']) > 0.05).astype(float) *
                df['is_high_altitude']
            )
            interactions_created.append('epa_altitude_threshold (threshold)')
        else:
            logger.info("ℹ️  Altitude interaction not created (optional - columns not available)")
        
        # Summary
        if interactions_created:
            logger.info(f"✓ Created {len(interactions_created)} non-linear interactions:")
            for interaction in interactions_created:
                logger.info(f"  - {interaction}")
        else:
            logger.warning("⚠️  NO interactions created - all required columns missing!")
        
        logger.info(f"✓ Engineered differential features: {len(df.columns)} total columns")
        
        return df
    
    @staticmethod
    def select_features(df: pd.DataFrame, logger=None) -> pd.DataFrame:
        """
        Select features for game outcome model training.
        
        Filters the dataset to include only:
        - Metadata columns (game_id, season, week, etc.)
        - Active features from FeatureRegistry
        - Target variable (home_team_won)
        
        Args:
            df: Game-level dataset with engineered features
            logger: Optional logger instance
            
        Returns:
            DataFrame with selected features ready for modeling
        """
        if logger is None:
            from commonv2 import get_logger
            logger = get_logger(__name__)
        
        logger.info("🔍 Selecting features for game outcome model")
        
        # Get active features from Registry
        active_features = FeatureRegistry.get_active_features()
        
        # Filter for features that actually exist in the dataframe
        # (Prevents errors if a feature is enabled in config but not yet engineered)
        available_features = [f for f in active_features if f in df.columns]
        
        missing = set(active_features) - set(available_features)
        if missing:
            logger.warning(f"⚠️ Enabled features missing from dataframe: {missing}")
        
        # Add metadata and target columns
        metadata_cols = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team']
        target_cols = ['home_team_won']
        
        final_columns = metadata_cols + available_features + target_cols
        
        # CRITICAL VALIDATION: Ensure target variable exists before filtering
        # This catches merge conflicts early (e.g., if feature sets incorrectly include target)
        if 'home_team_won' not in df.columns:
            available_cols = sorted(df.columns.tolist())
            raise ValueError(
                f"Target variable 'home_team_won' not found in DataFrame after feature engineering. "
                f"This indicates a data preparation error (likely a merge conflict where target was dropped). "
                f"Available columns ({len(available_cols)}): {', '.join(available_cols[:30])}..."
            )
        
        result_df = df[[col for col in final_columns if col in df.columns]].copy()
        
        logger.info(f"✓ Selected {len(available_features)} active features for {len(result_df):,} games")
        
        return result_df
    
    @staticmethod
    def prepare_data(
        features_df: pd.DataFrame,
        target_df: pd.DataFrame,
        logger=None,
        bucket_adapter=None
    ) -> pd.DataFrame:
        """
        Prepare game-level data for training.
        
        Handles ALL game outcome-specific data preparation:
        1. Filter completed games
        2. Create home_team_won target
        3. Merge home team rolling metrics
        4. Merge away team rolling metrics
        5. Load and merge contextual features (game-level, no home/away split needed)
        
        This method encapsulates all game-specific logic, keeping the trainer generic.
        
        Args:
            features_df: Team-level features from FEATURE_TABLE (rolling_metrics_v1)
            target_df: Game-level outcomes from TARGET_TABLE (dim_game)
            logger: Optional logger instance
            bucket_adapter: Optional BucketAdapter instance (uses DI with fallback pattern)
            
        Returns:
            DataFrame: Game-level data with home/away features ready for engineer_features()
        """
        import gc
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        
        if logger is None:
            from commonv2 import get_logger
            logger = get_logger(__name__)
        
        logger.info("🔍 Preparing game outcome data...")
        
        # Step 1: Filter completed games and create target
        target_df = target_df[
            (target_df['home_score'].notna()) &
            (target_df['away_score'].notna())
        ].copy()
        
        target_df['home_team_won'] = (target_df['home_score'] > target_df['away_score']).astype(int)
        
        logger.info(f"✓ Filtered to {len(target_df):,} completed games")
        logger.info(f"   Unique game_ids: {target_df['game_id'].nunique()}")
        
        # Check for duplicates in target
        target_dupes = target_df.groupby('game_id').size()
        target_dupes = target_dupes[target_dupes > 1]
        if len(target_dupes) > 0:
            logger.warning(f"   ⚠️ DUPLICATES in target_df: {len(target_dupes)} games appear multiple times")
        
        # Step 2: Merge home team rolling metrics
        # CRITICAL: features_df is a team-game table (2 rows per game_id)
        # Must merge on ['game_id', 'season', 'week', 'team'] to avoid duplicates
        
        # Validate features_df uniqueness BEFORE merge
        feature_dupes = features_df.groupby(['game_id', 'team']).size()
        feature_dupes = feature_dupes[feature_dupes > 1]
        if len(feature_dupes) > 0:
            raise ValueError(
                f"features_df contains {len(feature_dupes)} duplicate (game_id, team) pairs. "
                f"This violates the team-game table contract and will cause incorrect predictions. "
                f"Sample duplicates: {dict(list(feature_dupes.head().items()))}"
            )
        
        home_features = features_df.rename(columns={
            col: f'home_{col}' for col in features_df.columns
            if col not in ['game_id', 'season', 'week', 'team']
        })
        
        game_df = target_df.merge(
            home_features,
            left_on=['game_id', 'season', 'week', 'home_team'],
            right_on=['game_id', 'season', 'week', 'team'],
            how='inner',
            validate='one_to_one'  # Hard-fail if duplicates exist
        ).drop(columns=['team'], errors='ignore')
        
        del home_features
        gc.collect()
        
        logger.info(f"✓ Merged home rolling metrics: {len(game_df):,} games")
        
        # Step 3: Merge away team rolling metrics
        away_features = features_df.rename(columns={
            col: f'away_{col}' for col in features_df.columns
            if col not in ['game_id', 'season', 'week', 'team']
        })
        
        game_df = game_df.merge(
            away_features,
            left_on=['game_id', 'season', 'week', 'away_team'],
            right_on=['game_id', 'season', 'week', 'team'],
            how='inner',
            validate='one_to_one'  # Hard-fail if duplicates exist
        ).drop(columns=['team'], errors='ignore')
        
        del away_features
        gc.collect()
        
        logger.info(f"✓ Merged away rolling metrics: {len(game_df):,} games")
        
        # Step 4: Load and merge contextual features (game-level, already computed)
        # Initialize variables for use across multiple feature loading steps
        # DI with fallback pattern: accept injected adapter or create new one
        bucket_adapter = bucket_adapter or get_bucket_adapter(logger=logger)
        seasons = game_df['season'].unique().tolist()
        filters = [('season', 'in', seasons)] if len(seasons) > 1 else [('season', '==', seasons[0])]
        
        try:
            logger.info(f"📊 Loading contextual features for seasons: {seasons}")
            
            contextual_df = bucket_adapter.read_data(
                table_name='contextual_features_v1',
                schema='features',
                filters=filters
            )
            
            if not contextual_df.empty:
                game_df = safe_merge_game_features(
                    game_df, contextual_df,
                    keys=['game_id', 'season', 'week'],
                    name='contextual',
                    logger=logger
                )
                logger.info(f"✓ Merged contextual features: {len(game_df):,} games")
            else:
                logger.warning("⚠️  No contextual features found - training without them")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load contextual features: {e}")
            logger.warning("   Training will proceed with rolling metrics only")
        
        # Step 5: Load and merge NextGen QB features (game-level, already computed)
        try:
            # Reuse seasons and filters from Step 4
            logger.info(f"📊 Loading NextGen QB features for seasons: {seasons}")
            
            nextgen_df = bucket_adapter.read_data(
                table_name='nextgen_features_v1',
                schema='features',
                filters=filters
            )
            
            if not nextgen_df.empty:
                game_df = safe_merge_game_features(
                    game_df, nextgen_df,
                    keys=['game_id', 'season', 'week'],
                    name='nextgen',
                    logger=logger
                )
                logger.info(f"✓ Merged NextGen QB features: {len(game_df):,} games")
            else:
                logger.warning("⚠️  No NextGen QB features found - training without them")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load NextGen QB features: {e}")
            logger.warning("   Training will proceed without NextGen features")
        
        # Step 6: Load and merge player availability features (game-level, already computed)
        # Updated 2026-01-25: Replaced injury_features_v1 with player_availability_v1
        try:
            # Reuse seasons and filters from Step 4
            logger.info(f"📊 Loading player availability features for seasons: {seasons}")
            
            player_availability_df = bucket_adapter.read_data(
                table_name='player_availability_v1',
                schema='features',
                filters=filters
            )
            
            if not player_availability_df.empty:
                game_df = safe_merge_game_features(
                    game_df, player_availability_df,
                    keys=['game_id', 'season', 'week'],
                    name='player_availability',
                    logger=logger
                )
                logger.info(f"✓ Merged player availability features: {len(game_df):,} games")
            else:
                logger.warning("⚠️  No player availability features found - training without them")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load player availability features: {e}")
            logger.warning("   Training will proceed without player availability features")
        
        # Step 7: Load and merge weather features (game-level, already computed)
        # Updated 2026-01-27: Added weather_features_v1 for V1 observable weather features
        try:
            # Reuse seasons and filters from Step 4
            logger.info(f"📊 Loading weather features for seasons: {seasons}")
            
            weather_df = bucket_adapter.read_data(
                table_name='weather_features_v1',
                schema='features',
                filters=filters
            )
            
            if not weather_df.empty:
                # Robust to key columns: use ['game_id', 'season', 'week'] if available
                merge_keys = ['game_id']
                if all(col in weather_df.columns for col in ['season', 'week']):
                    merge_keys = ['game_id', 'season', 'week']
                
                game_df = safe_merge_game_features(
                    game_df, weather_df,
                    keys=merge_keys,
                    name='weather',
                    logger=logger
                )
                logger.info(f"✓ Merged weather features: {len(game_df):,} games")
            else:
                logger.warning("⚠️  No weather features found - training without them")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load weather features: {e}")
            logger.warning("   Training will proceed without weather features")
        
        # VALIDATION: Ensure identity columns survived all merges
        required_cols = ['home_team', 'away_team']
        missing = [c for c in required_cols if c not in game_df.columns]
        if missing:
            raise ValueError(
                f"❌ Missing required matchup columns after feature merges: {missing}. "
                f"This indicates a merge conflict. Available columns: {sorted(game_df.columns.tolist())}"
            )
        
        # Check for null values in identity columns
        if game_df[required_cols].isnull().any().any():
            bad_rows = game_df[game_df[required_cols].isnull().any(axis=1)][['game_id', 'season', 'week'] + required_cols].head(10)
            raise ValueError(
                f"❌ Null values found in matchup columns after merges. "
                f"This indicates feature tables are overwriting identity columns.\n"
                f"Sample bad rows:\n{bad_rows}"
            )
        
        logger.info(f"✓ Validation passed: Identity columns intact")
        logger.info(f"✓ Final dataset: {len(game_df):,} games, {len(game_df.columns)} columns")
        
        return game_df
    
    @staticmethod
    def evaluate_model(
        model: BaseEstimator,
        X_test: pd.DataFrame,
        y_test: Union[pd.Series, NDArray],
        y_pred: NDArray,
        y_pred_proba: NDArray,
        logger=None
    ) -> Dict[str, Any]:
        """
        Game outcome-specific evaluation metrics with baseline comparisons.
        
        Delegates to BaselineEvaluator for generic comparisons.
        """
        from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix
        from nflfastRv3.features.ml_pipeline.utils import BaselineEvaluator
        
        if logger is None:
            from commonv2 import get_logger
            logger = get_logger(__name__)
        
        # Convert y_test to numpy array if it's a Series
        if isinstance(y_test, pd.Series):
            y_test_array = cast(NDArray, y_test.to_numpy())
        else:
            y_test_array = cast(NDArray, np.asarray(y_test))
        
        # Model performance
        model_accuracy = accuracy_score(y_test_array, y_pred)
        model_auc = roc_auc_score(y_test_array, y_pred_proba[:, 1])
        actual_home_win_rate = float(y_test_array.mean())
        predicted_home_win_rate = float(y_pred.mean())
        
        # Get baseline comparisons
        baselines = BaselineEvaluator.evaluate_classification_baselines(
            y_test_array, y_pred, y_pred_proba, positive_class_rate=0.565,
        )
        
        # Home win bias (difference between predicted and actual home win rates)
        home_win_bias = predicted_home_win_rate - actual_home_win_rate
        
        metrics = {
            # Model performance
            'accuracy': model_accuracy,
            'auc': model_auc,
            'actual_home_win_rate': actual_home_win_rate,
            'predicted_home_win_rate': predicted_home_win_rate,
            'home_win_bias': home_win_bias,
            'classification_report': classification_report(y_test_array, y_pred, target_names=['Away Win', 'Home Win']),
            'confusion_matrix': confusion_matrix(y_test_array, y_pred).tolist(),
            
            # Baseline comparisons (mapped from utility)
            'baseline_always_home_accuracy': baselines['baseline_always_positive_accuracy'],
            'baseline_random_accuracy': baselines['baseline_random_accuracy'],
            'baseline_historical_accuracy': baselines['baseline_historical_accuracy'],
            'improvement_over_home': baselines['improvement_over_always_positive'],
            'improvement_over_random': baselines['improvement_over_random'],
            'improvement_over_historical': baselines['improvement_over_historical'],
            
            # Model value assessment
            'beats_always_home': baselines['beats_always_positive'],
            'beats_random': baselines['beats_random'],
            'beats_historical': baselines['beats_historical'],
        }
        
        logger.info(f"Model Performance:")
        logger.info(f"  Accuracy: {metrics['accuracy']:.3f}")
        logger.info(f"  AUC-ROC: {metrics['auc']:.3f}")
        logger.info(f"  Home team win rate (actual): {metrics['actual_home_win_rate']:.3f}")
        logger.info(f"  Home team win rate (predicted): {metrics['predicted_home_win_rate']:.3f}")
        logger.info(f"  Home win bias: {metrics['home_win_bias']:+.3f} ({metrics['home_win_bias']*100:+.1f}%)")
        logger.info(f"")
        logger.info(f"Baseline Comparisons:")
        logger.info(f"  Always Home: {metrics['baseline_always_home_accuracy']:.3f} (improvement: {metrics['improvement_over_home']:+.3f})")
        logger.info(f"  Random: {metrics['baseline_random_accuracy']:.3f} (improvement: {metrics['improvement_over_random']:+.3f})")
        logger.info(f"  Historical: {metrics['baseline_historical_accuracy']:.3f} (improvement: {metrics['improvement_over_historical']:+.3f})")
        logger.info(f"")
        logger.info(f"Model Value:")
        logger.info(f"  Beats Always Home: {'✓' if metrics['beats_always_home'] else '✗'}")
        logger.info(f"  Beats Random: {'✓' if metrics['beats_random'] else '✗'}")
        logger.info(f"  Beats Historical: {'✓' if metrics['beats_historical'] else '✗'}")
        
        return metrics
    
    @staticmethod
    def analyze_feature_correlations(
        df: pd.DataFrame,
        logger=None
    ) -> pd.DataFrame:
        """
        Analyze correlation between features and game outcomes.
        
        Delegates to FeatureDiagnostics utility for generic correlation analysis.
        
        Args:
            df: Game-level dataset with features and home_team_won target
            logger: Optional logger instance
            
        Returns:
            DataFrame with correlation analysis results
        """
        from nflfastRv3.features.ml_pipeline.utils.feature_diagnostics import FeatureDiagnostics
        
        # Define feature patterns for game outcome model
        feature_patterns = [r'_diff$', r'_advantage$']
        
        return FeatureDiagnostics.analyze_correlations(
            df, 'home_team_won', feature_patterns=feature_patterns
        )
    
    @staticmethod
    def analyze_feature_importance_stability(
        feature_importance_history: List[Dict[str, Any]],
        logger=None
    ) -> Dict[str, Any]:
        """
        Analyze stability of feature importance across multiple training runs.
        
        Delegates to FeatureDiagnostics utility for generic stability analysis.
        
        Args:
            feature_importance_history: List of dicts, each containing feature importance
                                       from a different training run
            logger: Optional logger instance
            
        Returns:
            dict: Stability analysis metrics including frozen features count
        """
        from nflfastRv3.features.ml_pipeline.utils.feature_diagnostics import FeatureDiagnostics
        
        return FeatureDiagnostics.analyze_importance_stability(
            feature_importance_history, frozen_threshold=0.01, variable_threshold=0.5
        )
    
    @staticmethod
    def prepare_target(df: pd.DataFrame) -> pd.DataFrame:
        """
        DEPRECATED: Use prepare_data() instead.
        
        Prepare target variable for game outcome prediction.
        
        Creates 'home_team_won' binary target from 'result' column if not already present.
        result > 0 means home team won, result <= 0 means away team won.
        
        Args:
            df: DataFrame with game results
            
        Returns:
            DataFrame with home_team_won target variable
        """
        if 'result' in df.columns and 'home_team_won' not in df.columns:
            df['home_team_won'] = (df['result'] > 0).astype(int)
        return df
    
    # ===== INSTANCE METHODS (Model Implementation) =====
    
    def __init__(self, weights: Optional[Dict[str, float]] = None, random_state: int = 42) -> None:
        """
        Initialize game outcome model with game-specific configuration.
        
        Args:
            weights: Optional custom model weights (default: {'xgboost': 0.1, 'elastic_net': 0.45, 'logistic': 0.45})
            random_state: Random seed for reproducibility
        """
        # Updated weights (2025-12-13): Rebalanced after XGBoost feature starvation fix
        # XGBoost now has 25 features (vs 3) and 56.2% accuracy (vs 43.8%)
        # Equal weighting allows all components to contribute fairly
        weights = weights or {'xgboost': 0.33, 'elastic_net': 0.33, 'logistic': 0.34}
        
        # Custom XGBoost hyperparameters for game outcome
        # Updated 2025-12-13: Tuned for 25 features (was optimized for 7)
        xgboost_params = {
            'max_depth': 6,              # Deeper trees for more features (was 5)
            'reg_alpha': 0.15,
            'reg_lambda': 1.5,
            'colsample_bytree': 0.65,
            'learning_rate': 0.03,       # Slower for stability (was 0.05)
            'n_estimators': 300,         # More trees to compensate (was 200)
            'min_child_weight': 3,       # Allow more splits (was 4)
            'subsample': 0.7
        }
        
        # Initialize parent EnsembleClassifier with game outcome configuration
        super().__init__(
            linear_patterns=FeaturePatterns.GAME_OUTCOME_LINEAR,
            tree_patterns=FeaturePatterns.GAME_OUTCOME_TREE,
            weights=weights,
            enable_season_gating=True,
            xgboost_params=xgboost_params,
            elastic_net_params={'l1_ratio': 0.5, 'alpha': 0.01},
            logistic_params={'l1_ratio': 0.5, 'C': 1.0},
            random_state=random_state
        )


# Backward compatibility alias
GameOutcomeEnsemble = GameOutcomeModel

def create_game_outcome_model(random_state: int = 42) -> GameOutcomeModel:
    """
    Factory function to create a game outcome model instance.
    
    Args:
        random_state: Random seed for reproducibility
        
    Returns:
        GameOutcomeModel: Configured game outcome model
    """
    return GameOutcomeModel(random_state=random_state)


__all__ = ['GameOutcomeModel', 'create_game_outcome_model', 'GameOutcomeEnsemble']