"""
Model Training Implementation for nflfastRv3

Generic model trainer that delegates model-specific logic to model classes.
Following REFACTORING_SPECS.md: Maximum 5 complexity points, 3 layers depth.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Implementation - calls infrastructure directly)

Architecture:
- ModelTrainerImplementation: Generic training orchestrator
  - Public API: train_model() - Full-featured training with safety checks
  - Internal workflow: _execute_training_workflow() - Core training logic
  - Helper methods: Extracted for maintainability and testability
- Model Classes (e.g., GameOutcomeModel): Model-specific logic
  - Feature engineering
  - Hyperparameter configuration
  - Target variable definition
  - Feature selection

Refactored (Dec 2024): Extracted helper methods to reduce complexity
and improve maintainability while staying within architecture guidelines.
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Type

from commonv2 import get_logger
from nflfastRv3.shared.database_router import get_database_router
# Report generation moved to CLI orchestration layer


class ModelTrainerImplementation:
    """
    Core ML model training business logic.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 6 points (within infrastructure tolerance)
    Depth: 2-3 layers maximum (compliant)
    
    Public API:
        train_model() - Primary training method with all safety features
    
    Internal Methods:
        _execute_training_workflow() - Core training orchestration
        _validate_training_parameters() - Parameter validation
        _configure_walk_forward_if_supported() - Walk-forward setup
        _engineer_and_select_features() - Feature processing
        _perform_model_training() - Model training step
        _build_training_result() - Result construction
    
    Migrated from nflfastRv2.ModelTrainer with architectural simplification.
    Refactored Dec 2024: Extracted helpers to reduce method complexity.
    """
    
    def __init__(self, db_service, logger, feature_builder=None, schedule_provider=None):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            feature_builder: Optional real feature builder
            schedule_provider: Optional schedule data provider
        """
        self.db_service = db_service
        self.logger = logger
        # self.feature_builder = feature_builder or RealFeatureBuilder(schedule_provider)
        # self.schedule_provider = schedule_provider or ScheduleDataProvider()
        # self.opponent_features = OpponentAdjustedFeatures(db_service, logger, schedule_provider)
        # Report generation moved to orchestration layer (CLI commands)
        # No longer instantiated here to prevent duplicate reports in batch operations
    
    def _validate_training_parameters(self, model_class: Type[Any], train_seasons: Optional[str],
                                      test_seasons: Optional[str], test_week: Optional[int]):
        """
        Validate and parse training parameters.
        
        Args:
            model_class: Model class to train
            train_seasons: Training seasons string
            test_seasons: Optional test seasons string
            test_week: Optional test week
            
        Returns:
            tuple: (train_season_list, test_season_list)
        """
        # Validate required parameters
        if model_class is None:
            raise ValueError(
                "model_class is required. "
                "Use train_model() for public API."
            )
        
        if train_seasons is None:
            raise ValueError(
                "train_seasons is required. "
                "Provide seasons as '2020-2023' (range) or '2020,2021,2022,2023' (comma-separated)"
            )
        
        # Parse season parameters
        train_season_list = self._parse_seasons(train_seasons)
        
        if test_seasons is None:
            # Auto-split with proper separation
            if len(train_season_list) < 2:
                raise ValueError(
                    "Cannot auto-split single season. "
                    "Provide at least 2 seasons (e.g., '2022-2023') or use "
                    "--train-seasons and --test-seasons explicitly."
                )
            
            test_season_list = [train_season_list[-1]]
            train_season_list = train_season_list[:-1]  # Remove from training
            
            self.logger.info(f"Auto-split: train={train_season_list}, test={test_season_list}")
        else:
            # Explicit split (production mode always ensures no overlap by design)
            test_season_list = self._parse_seasons(test_seasons)
        
        self.logger.info(f"Training on seasons: {train_season_list}")
        self.logger.info(f"Testing on seasons: {test_season_list}")
        
        # Validate test_week if provided
        if test_week is not None:
            if not 1 <= test_week <= 22:
                raise ValueError(
                    f"Invalid week: {test_week}. Must be 1-22 (includes playoffs)."
                )
            self.logger.info(f"Testing on week: {test_week}")
        
        return train_season_list, test_season_list
    
    def _configure_walk_forward_if_supported(self, model_class: Type[Any], train_seasons: Optional[str],
                                            test_season_list: List[int], test_week: Optional[int],
                                            train_weeks: Optional[Dict[int, List[int]]],
                                            bucket_adapter):
        """
        Apply walk-forward validation if model supports it.
        
        Args:
            model_class: Model class to check
            train_seasons: Original training seasons string
            test_season_list: Parsed test seasons
            test_week: Optional test week
            train_weeks: Optional manually specified train weeks
            bucket_adapter: BucketAdapter instance to pass through
            
        Returns:
            tuple: (updated_train_seasons, updated_train_weeks)
        """
        # Check if model supports walk-forward and should apply it
        if (hasattr(model_class, 'SUPPORTS_WALK_FORWARD') and
            model_class.SUPPORTS_WALK_FORWARD and
            test_week is not None and
            train_weeks is None):  # Only if not manually specified
            
            self.logger.info(f"🔍 Model supports walk-forward validation")
            
            # Get walk-forward configuration from model
            walk_forward_config = model_class.apply_walk_forward(
                train_seasons=train_seasons,
                test_season=test_season_list[0],  # Use first test season
                test_week=test_week,
                db_service=self.db_service,
                logger=self.logger,
                bucket_adapter=bucket_adapter
            )
            
            # Update training configuration with walk-forward settings
            if walk_forward_config['train_weeks']:
                updated_train_seasons = walk_forward_config['train_seasons']
                updated_train_weeks = walk_forward_config['train_weeks']
                
                self.logger.info(f"✓ Walk-forward applied: Updated training configuration")
                self.logger.info(f"   Train seasons: {self._parse_seasons(updated_train_seasons)}")
                self.logger.info(f"   Train weeks: {updated_train_weeks}")
                
                return updated_train_seasons, updated_train_weeks
        
        return train_seasons, train_weeks
    
    def _engineer_and_select_features(self, game_df: pd.DataFrame, model_class: Type[Any]) -> pd.DataFrame:
        """
        Apply model-specific feature engineering and selection.
        
        Args:
            game_df: Raw game data
            model_class: Model class with feature methods
            
        Returns:
            DataFrame: Model-ready dataset with engineered and selected features
        """
        # Model-specific feature engineering
        self.logger.info(f"Applying {model_class.MODEL_NAME} feature engineering...")
        game_df = model_class.engineer_features(game_df, self.logger)
        
        # Model-specific feature selection
        self.logger.info(f"Selecting {model_class.MODEL_NAME} features...")
        model_df = model_class.select_features(game_df, self.logger)
        
        return model_df
    
    def _perform_model_training(self, model_class: Type[Any], X_train: pd.DataFrame,
                                y_train: pd.Series, random_state: int):
        """
        Train the model with given data.
        
        Args:
            model_class: Model class to instantiate
            X_train: Training features
            y_train: Training targets
            random_state: Random seed for reproducibility
            
        Returns:
            Trained model instance
        """
        self.logger.info(f"Training {model_class.MODEL_NAME} model...")
        model = model_class.create_model(random_state)
        model.fit(X_train, y_train)
        self.logger.info(f"✓ Model trained with {len(X_train)} games and {len(X_train.columns)} features")
        return model
    
    def _build_training_result(self, model, metrics: Dict[str, Any],
                              X_train: pd.DataFrame, X_test: pd.DataFrame,
                              y_train: pd.Series, y_test: pd.Series,
                              y_pred, y_pred_proba,
                              test_metadata: pd.DataFrame, return_predictions: bool) -> Dict[str, Any]:
        """
        Build the training result dictionary with all data needed for reporting.
        
        Args:
            model: Trained model
            metrics: Evaluation metrics
            X_train: Training features
            X_test: Test features
            y_train: Training targets
            y_test: True test labels
            y_pred: Predictions
            y_pred_proba: Prediction probabilities
            test_metadata: Test game metadata
            return_predictions: Whether to include predictions DataFrame
            
        Returns:
            dict: Complete training result with all data for external reporting
        """
        result = {
            'status': 'success',
            'model': model,
            'model_path': None,  # Will be set by train_model() if saved
            'metrics': metrics,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'num_features': len(X_train.columns),
            # Include all data needed for report generation at orchestration layer
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba,
            'test_metadata': test_metadata
        }
        
        if return_predictions:
            # Create predictions DataFrame with metadata and features
            predictions_df = test_metadata.copy()
            predictions_df['prediction'] = y_pred
            predictions_df['home_team_won'] = y_test.values
            
            if y_pred_proba is not None:
                predictions_df['home_win_prob'] = y_pred_proba[:, 1]
                predictions_df['confidence'] = predictions_df['home_win_prob'].apply(lambda p: max(p, 1-p))
            
            # Add features for analysis
            for col in X_test.columns:
                predictions_df[col] = X_test[col].values
                
            result['predictions'] = predictions_df
        
        return result
    
    def _execute_training_workflow(
            self,
            model_class: Type[Any],
            train_seasons: Optional[str] = None,
            test_seasons: Optional[str] = None,
            test_week: Optional[int] = None,
            train_weeks: Optional[Dict[int, List[int]]] = None,
            save_model: bool = False,
            random_state: int = 42,
            return_correlations: bool = False,
            return_predictions: bool = False
        ) -> Dict[str, Any]:
        """
        Execute generic model training workflow (internal method).
        
        NOTE: This is called internally by train_model().
        External code should use train_model() instead.
        
        Generic training flow using extracted helper methods:
        1. Validate and parse parameters
        2. Configure walk-forward if supported
        3. Prepare training data
        4. Engineer and select features
        5. Create train/test split
        6. Train model
        7. Evaluate and report
        
        Args:
            model_class: (required) Model class (e.g., GameOutcomeModel)
            train_seasons: (required) Training seasons (e.g., '2020-2023')
            test_seasons: Test seasons (default: auto-split from train_seasons)
            test_week: Specific week to test (1-22). If None, tests entire season.
            train_weeks: Optional dict for walk-forward validation
            random_state: Random seed for reproducibility
            return_correlations: Whether to calculate feature-outcome correlations
            return_predictions: Whether to return predictions DataFrame
            
        Returns:
            dict: Training results with model and metrics
        """
        self.logger.info(f"Starting {model_class.MODEL_NAME} training: train={train_seasons}, test={test_seasons}, week={test_week}")
        
        try:
            # Create bucket_adapter early for use throughout workflow
            from commonv2.persistence.bucket_adapter import get_bucket_adapter
            bucket_adapter = get_bucket_adapter(logger=self.logger)
            
            # Step 1: Validate and parse parameters
            train_season_list, test_season_list = self._validate_training_parameters(
                model_class, train_seasons, test_seasons, test_week
            )
            
            # Step 2: Configure walk-forward if supported
            final_train_seasons, final_train_weeks = self._configure_walk_forward_if_supported(
                model_class, train_seasons, test_season_list, test_week, train_weeks, bucket_adapter
            )
            
            # Re-parse if walk-forward updated seasons
            if final_train_seasons != train_seasons:
                train_season_list = self._parse_seasons(final_train_seasons)
            
            # Step 3: Prepare training data (pass bucket_adapter to avoid re-instantiation)
            game_df = self._prepare_training_data(
                train_season_list, test_season_list, test_week, model_class, bucket_adapter
            )
            
            # Step 4: Engineer and select features
            model_df = self._engineer_and_select_features(game_df, model_class)
            
            # Step 5: Create train/test split
            X_train, X_test, y_train, y_test, test_metadata = self._create_train_test_split(
                model_df, train_season_list, test_season_list, test_week,
                model_class, final_train_weeks
            )
            
            if X_train.empty or X_test.empty:
                return {
                    'status': 'error',
                    'message': 'No training data available',
                    'model': None
                }
            
            self.logger.info(f"Training set: {len(X_train)} games, {len(X_train.columns)} features")
            self.logger.info(f"Test set: {len(X_test)} games")
            
            # Step 6: Train model
            model = self._perform_model_training(model_class, X_train, y_train, random_state)
            
            # Step 7: Evaluate model (no report generation - returns data only)
            metrics, y_pred, y_pred_proba = self._evaluate_model(
                model, X_train, X_test, y_train, y_test, test_metadata,
                train_season_list, test_season_list, test_week,
                model_class, None, return_correlations
            )
            
            self.logger.info("✅ Model training completed successfully")
            
            # Build and return result with all data for external reporting
            return self._build_training_result(
                model, metrics, X_train, X_test, y_train, y_test,
                y_pred, y_pred_proba, test_metadata, return_predictions
            )
            
        except Exception as e:
            self.logger.error(f"Model training failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'model': None
            }

    def _load_features(self, feature_table: str, feature_schema: str,
                      train_seasons: List[int], test_seasons: List[int],
                      test_week: Optional[int], bucket_adapter) -> pd.DataFrame:
        """
        Load feature data from bucket with optional week filtering.
        
        Args:
            feature_table: Feature table name
            feature_schema: Feature schema name
            train_seasons: Training seasons
            test_seasons: Test seasons
            test_week: Optional specific week for testing
            bucket_adapter: Bucket adapter instance
            
        Returns:
            DataFrame: Combined feature data
        """
        import gc
        
        all_seasons = list(set(train_seasons + test_seasons))
        
        if test_week is not None:
            # Load training data (all weeks for training seasons)
            train_filters = [('season', 'in', train_seasons)] if len(train_seasons) > 1 else [('season', '==', train_seasons[0])]
            
            self.logger.info(f"📊 Loading training features for seasons: {train_seasons} (all weeks)")
            train_features = bucket_adapter.read_data(
                table_name=feature_table,
                schema=feature_schema,
                filters=train_filters
            )
            
            # Load test data (ONLY specific week) - MEMORY OPTIMIZATION
            test_filters = [
                ('season', 'in', test_seasons) if len(test_seasons) > 1 else ('season', '==', test_seasons[0]),
                ('week', '==', test_week)
            ]
            
            self.logger.info(f"📊 Loading test features for seasons: {test_seasons}, week: {test_week}")
            test_features = bucket_adapter.read_data(
                table_name=feature_table,
                schema=feature_schema,
                filters=test_filters
            )
            
            # Validate test data
            if test_features.empty:
                all_features = bucket_adapter.read_data(
                    feature_table, feature_schema,
                    filters=[('season', 'in', test_seasons)]
                )
                available_weeks = sorted(all_features['week'].unique()) if not all_features.empty else []
                
                raise ValueError(
                    f"No test data found for week {test_week} in seasons {test_seasons}. "
                    f"Available weeks: {available_weeks}."
                )
            
            # Combine train and test features
            features_df = pd.concat([train_features, test_features], ignore_index=True)
            
            # Deduplicate (handle overlap between train_seasons and test_week)
            # This happens when walk-forward adds the test season to training
            before_dedup = len(features_df)
            features_df = features_df.drop_duplicates()
            
            if len(features_df) < before_dedup:
                self.logger.info(f"✓ Deduplicated features: {before_dedup:,} → {len(features_df):,} rows")
            
            del train_features, test_features
            gc.collect()
            
            self.logger.info(f"✓ Loaded features with week filtering: {len(features_df):,} rows")
        else:
            # Load all data together (no week filter)
            filters = [('season', 'in', all_seasons)] if len(all_seasons) > 1 else [('season', '==', all_seasons[0])]
            
            self.logger.info(f"📊 Loading features for seasons: {all_seasons} (all weeks)")
            features_df = bucket_adapter.read_data(
                table_name=feature_table,
                schema=feature_schema,
                filters=filters
            )
        
        if features_df.empty:
            raise ValueError(
                "No pre-built features found in bucket. "
                "Please run feature engineering first: quantcup nflfastrv3 ml features --season <YEAR>"
            )
        
        features_mb = features_df.memory_usage(deep=True).sum() / (1024 * 1024)
        self.logger.info(f"✓ Loaded {len(features_df):,} feature rows, {features_mb:.1f}MB")
        
        return features_df
    
    def _load_targets(self, target_table: str, target_schema: str,
                     all_seasons: List[int], bucket_adapter) -> pd.DataFrame:
        """
        Load target data from bucket.
        
        Args:
            target_table: Target table name
            target_schema: Target schema name
            all_seasons: All seasons to load
            bucket_adapter: Bucket adapter instance
            
        Returns:
            DataFrame: Target data
        """
        self.logger.info(f"📊 Loading target data from {target_schema}.{target_table} for seasons: {all_seasons}")
        
        filters = [('season', 'in', all_seasons)] if len(all_seasons) > 1 else [('season', '==', all_seasons[0])]
        target_df = bucket_adapter.read_data(
            table_name=target_table,
            schema=target_schema,
            filters=filters
        )
        
        if target_df.empty:
            raise ValueError(
                f"No target data found in {target_schema}.{target_table}. "
                "Please rebuild warehouse: quantcup nflfastrv3 data warehouse --rebuild"
            )
        
        target_mb = target_df.memory_usage(deep=True).sum() / (1024 * 1024)
        self.logger.info(f"✓ Loaded {target_table}: {len(target_df):,} rows, {target_mb:.1f}MB")
        
        return target_df
    
    def _prepare_training_data(self, train_seasons: List[int], test_seasons: List[int],
                               test_week: Optional[int] = None, model_class=None,
                               bucket_adapter=None):
        """
        Load raw data and delegate preparation to model.
        
        GENERIC: Just loads feature and target tables, then delegates ALL prep to model.
        This makes the trainer truly model-agnostic.
        
        MEMORY OBSERVABILITY: Tracks memory usage during data loading.
        MEMORY OPTIMIZATION: Uses bucket-side filtering for week-specific queries.
        
        Args:
            train_seasons: List of training seasons
            test_seasons: List of test seasons
            test_week: Optional specific week to test (1-22). If None, uses entire season.
            model_class: Model class that defines data sources and prep logic
            bucket_adapter: Optional BucketAdapter instance (uses DI with fallback pattern)
            
        Returns:
            DataFrame: Model-ready dataset (after model's prepare_data())
        """
        if model_class is None:
            raise ValueError("model_class is required to determine data source configuration")
        
        try:
            from commonv2.persistence.bucket_adapter import get_bucket_adapter
            from commonv2.utils.memory.manager import create_memory_manager
            import gc
            
            # Initialize memory manager for observability
            memory_mgr = create_memory_manager(logger=self.logger)
            self.logger.info("🔍 Starting training data preparation...")
            memory_mgr.log_status()
            
            # DI with fallback pattern
            bucket_adapter = bucket_adapter or get_bucket_adapter(logger=self.logger)
            all_seasons = list(set(train_seasons + test_seasons))
            
            # Step 1: Load features using helper method
            features_df = self._load_features(
                model_class.FEATURE_TABLE,
                model_class.FEATURE_SCHEMA,
                train_seasons,
                test_seasons,
                test_week,
                bucket_adapter
            )
            memory_mgr.log_status()
            
            # Step 2: Load targets using helper method
            target_df = self._load_targets(
                model_class.TARGET_TABLE,
                model_class.TARGET_SCHEMA,
                all_seasons,
                bucket_adapter
            )
            memory_mgr.log_status()
            
            # Step 3: Delegate ALL data preparation to model
            self.logger.info(f"📊 Delegating data preparation to {model_class.MODEL_NAME}...")
            game_df = model_class.prepare_data(
                features_df,
                target_df,
                logger=self.logger,
                bucket_adapter=bucket_adapter  # Pass injected adapter to prevent duplicate instantiation
            )
            
            # Clear source DataFrames
            del features_df, target_df
            gc.collect()
            
            if game_df.empty:
                raise ValueError("Model's prepare_data() returned empty DataFrame")
            
            # Log final status
            final_mb = game_df.memory_usage(deep=True).sum() / (1024 * 1024)
            final_status = memory_mgr.get_status()
            self.logger.info(
                f"✓ Data ready: {len(game_df):,} games, {len(game_df.columns)} columns, {final_mb:.1f}MB"
            )
            self.logger.info(
                f"✓ Memory: {final_status['current_usage_mb']:.1f}MB / {final_status['max_memory_mb']}MB "
                f"({final_status['usage_percent']:.1f}% used)"
            )
            
            return game_df
            
        except Exception as e:
            self.logger.error(f"Failed to prepare training data: {e}", exc_info=True)
            raise ValueError(f"Failed to prepare training data: {e}") from e
    
    def _create_train_test_split(self, model_df: pd.DataFrame, train_seasons: List[int],
                                 test_seasons: List[int], test_week: Optional[int] = None,
                                 model_class=None, train_weeks: Optional[Dict[int, List[int]]] = None):
        """
        Create time-series aware train/test split (GENERIC for all models).
        
        Uses model_class.METADATA_COLUMNS and model_class.TARGET_VARIABLE
        to determine what to exclude from features. This makes the method
        truly model-agnostic.
        
        MEMORY OBSERVABILITY: Tracks memory during train/test split.
        
        Args:
            model_df: Model-ready dataset
            train_seasons: Training seasons
            test_seasons: Test seasons
            test_week: Optional specific week to test. If None, uses entire season.
            model_class: Model class that defines TARGET_VARIABLE and METADATA_COLUMNS
            train_weeks: Optional dict mapping season to list of weeks to include in training.
                        Example: {2024: [1, 2, 3]} includes only weeks 1-3 of 2024.
            
        Returns:
            Tuple: (X_train, X_test, y_train, y_test, test_metadata_df)
        """
        if model_class is None:
            raise ValueError("model_class is required for train/test split")
        from commonv2.utils.memory.manager import create_memory_manager
        import gc
        
        memory_mgr = create_memory_manager(logger=self.logger)
        self.logger.info("🔍 Creating train/test split")
        memory_mgr.log_status()
        
        # Get model-specific configuration
        target_col = model_class.TARGET_VARIABLE
        metadata_cols = model_class.METADATA_COLUMNS
        
        # Create time-series split
        train_mask = model_df['season'].isin(train_seasons)
        test_mask = model_df['season'].isin(test_seasons)
        
        # ✅ NEW: Additional week filtering if specified
        # Note: Most filtering already done at bucket read, but this handles edge cases
        if test_week is not None:
            if 'week' not in model_df.columns:
                raise ValueError("Cannot filter by week: 'week' column not found in model_df")
            
            self.logger.info(f"Applying week filter: test_week={test_week}")
            test_mask = test_mask & (model_df['week'] == test_week)
            
            # ✅ VALIDATE: Check we have test data after filtering
            if not test_mask.any():
                available_weeks = model_df[model_df['season'].isin(test_seasons)]['week'].unique()
                raise ValueError(
                    f"No test data found for week {test_week} in seasons {test_seasons}. "
                    f"Available weeks: {sorted(available_weeks)}"
                )
        
        train_df = model_df[train_mask].copy()
        test_df = model_df[test_mask].copy()
        
        # Apply train_weeks filter if specified (for walk-forward validation)
        # This filters ONLY the training data, leaving test data untouched
        if train_weeks is not None:
            original_train_size = len(train_df)
            
            for season, weeks in train_weeks.items():
                # Keep all data from other seasons, filter specified season to only include specified weeks
                mask = (
                    (train_df['season'] != season) |
                    (train_df['week'].isin(weeks))
                )
                train_df = train_df[mask]
            
            filtered_train_size = len(train_df)
            self.logger.info(
                f"✓ Applied walk-forward week filter to training data: "
                f"{original_train_size:,} → {filtered_train_size:,} rows "
                f"({filtered_train_size - original_train_size:+,} games)"
            )
        
        # Separate features and targets (exclude metadata and target)
        exclude_cols = metadata_cols + [target_col]
        feature_cols = [col for col in model_df.columns if col not in exclude_cols]
        
        # Extract metadata for test games (for detailed reporting)
        test_metadata = test_df[[col for col in metadata_cols if col in test_df.columns]].copy()
        
        X_train = train_df[feature_cols].fillna(0)
        X_test = test_df[feature_cols].fillna(0)
        y_train = train_df[target_col]
        y_test = test_df[target_col]
        
        # Clear intermediate DataFrames
        del train_df, test_df
        gc.collect()
        
        # Log final sizes
        X_train_mb = X_train.memory_usage(deep=True).sum() / (1024 * 1024)
        X_test_mb = X_test.memory_usage(deep=True).sum() / (1024 * 1024)
        final_status = memory_mgr.get_status()
        
        self.logger.info(f"✓ Train/test split: {len(X_train):,} train ({X_train_mb:.1f}MB), {len(X_test):,} test ({X_test_mb:.1f}MB)")
        self.logger.info(
            f"✓ Memory: {final_status['current_usage_mb']:.1f}MB / {final_status['max_memory_mb']}MB "
            f"({final_status['usage_percent']:.1f}% used)"
        )
        
        return X_train, X_test, y_train, y_test, test_metadata
    
    def _evaluate_model(self, model, X_train, X_test, y_train, y_test, test_metadata,
                       train_seasons, test_seasons, test_week=None, model_class=None, model_path=None,
                       return_correlations=False):
        """
        Evaluate trained model (GENERIC - delegates to model class).
        
        Returns metrics and predictions WITHOUT generating reports.
        Report generation moved to CLI orchestration layer to prevent
        duplicate reports during batch operations (backtesting, optimization).
        
        Args:
            model: Trained model
            X_train: Training features
            X_test: Test features
            y_train: Training targets
            y_test: Test targets
            test_metadata: Test game metadata (game_id, teams, dates, etc.)
            train_seasons: Training seasons
            test_seasons: Test seasons
            test_week: Optional specific test week
            model_class: Model class that defines evaluation logic
            model_path: Optional path where model was saved (unused - kept for compatibility)
            return_correlations: Whether to calculate feature-outcome correlations
            
        Returns:
            tuple: (metrics dict, y_pred, y_pred_proba)
        """
        if model_class is None:
            raise ValueError("model_class is required for evaluation")
        
        self.logger.info(f"Evaluating {model_class.MODEL_NAME} on {len(X_test)} test games")
        
        # Generate predictions (generic)
        # For classifiers, use predict_classes() to get class labels (0/1)
        # For regressors, use predict() to get continuous values
        if hasattr(model, 'predict_classes'):
            y_pred = model.predict_classes(X_test)
            y_pred_proba = model.predict_proba(X_test)
        else:
            y_pred = model.predict(X_test)
            y_pred_proba = None
            
            # Get probabilities if available (classification models without predict_classes)
            if hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_test)
        
        # Delegate model-specific evaluation to model class
        metrics = model_class.evaluate_model(
            model, X_test, y_test, y_pred, y_pred_proba, logger=self.logger
        )
        
        # Generic feature importance (works for tree-based models)
        if hasattr(model, 'feature_importances_'):
            # Handle feature splitting (if model uses subset of features)
            feature_names = X_test.columns
            if hasattr(model, 'tree_features_') and model.tree_features_:
                feature_names = model.tree_features_
            
            # Validate lengths match before creating DataFrame
            if len(feature_names) == len(model.feature_importances_):
                feature_importance = pd.DataFrame({
                    'feature': feature_names,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                self.logger.info("Top 10 Most Important Features:")
                for idx, row in feature_importance.head(10).iterrows():
                    self.logger.info(f"  {row['feature']}: {row['importance']:.4f}")
                
                metrics['feature_importance'] = feature_importance.to_dict('records')
            else:
                self.logger.warning(
                    f"Feature importance mismatch: {len(feature_names)} names vs "
                    f"{len(model.feature_importances_)} importance values. Skipping importance logging."
                )
        
        # Calculate feature-outcome correlations if requested
        if return_correlations:
            self.logger.info("Calculating feature-outcome correlations...")
            feature_correlations = {}
            
            for feature in X_test.columns:
                try:
                    corr = X_test[feature].corr(y_test)
                    # Handle NaN correlations (constant features)
                    feature_correlations[feature] = float(corr) if not pd.isna(corr) else 0.0
                except Exception as e:
                    self.logger.warning(f"Failed to calculate correlation for {feature}: {e}")
                    feature_correlations[feature] = 0.0
            
            metrics['feature_correlations'] = feature_correlations
            self.logger.info(f"✓ Calculated correlations for {len(feature_correlations)} features")
        
        # ✅ REMOVED: Report generation - now handled at CLI orchestration layer
        # This prevents generating N reports during backtesting or optimization
        
        return metrics, y_pred, y_pred_proba

    def _parse_seasons(self, seasons_str):
        """
        Parse season string to list of integers.
        
        Supports formats:
        - '2020-2023' (range)
        - '2020,2021,2022,2023' (comma-separated)
        - '2000-2022,2024' (mixed: range and individual seasons)
        
        Args:
            seasons_str: Season string
            
        Returns:
            list: List of season integers
        """
        seasons = []
        
        # Split by comma first to handle mixed formats
        parts = seasons_str.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range format: '2020-2023'
                start, end = part.split('-')
                seasons.extend(range(int(start), int(end) + 1))
            else:
                # Single season: '2024'
                seasons.append(int(part))
        
        return seasons
    
    def train_model(self, model_class: Type[Any], train_seasons: str,
                   test_seasons: Optional[str] = None,
                   test_week: Optional[int] = None,
                   tag: Optional[str] = None,
                   save_model: bool = True,
                   random_state: int = 42,
                   metadata: Optional[Dict[str, Any]] = None,
                   dry_run: bool = False,
                   auto_build_features: bool = True,
                   force: bool = False):
        """
        Execute model training with comprehensive v2 features.
        
        This is the PRIMARY public training method that includes all safety features:
        - Temporal leakage validation (prevents training on incomplete future weeks)
        - Dry-run preview mode (preview without training)
        - Auto feature building (ensure required features exist)
        - Model versioning and metadata tracking
        
        Args:
            model_class: (required) Model class (e.g., GameOutcomeModel)
            train_seasons: (required) Training seasons (e.g., '2020-2023')
            test_seasons: Test seasons (default: auto-split from train_seasons)
            test_week: Specific week to test (1-22)
            tag: Version tag (e.g., 'week9_3yr', 'latest')
            save_model: Whether to save the trained model
            random_state: Random seed for reproducibility
            metadata: Additional metadata to store with model
            dry_run: Preview training config without executing (default: False)
            auto_build_features: Auto-build missing features (default: True)
            force: Force training even with temporal leakage warning (default: False)
            
        Returns:
            dict: Training results with version info, or preview if dry_run=True
        """
        
        # Step 1: Temporal leakage validation
        # Distinguish between backtesting (completed weeks) and live prediction (future weeks)
        if test_week and not force:
            from datetime import datetime
            from nflfastRv3.shared.temporal_validator import TemporalValidator
            
            test_season_int = int(test_seasons.split('-')[0]) if test_seasons else int(train_seasons.split('-')[-1])
            current_year = datetime.now().year
            
            # Only validate temporal leakage for current or future seasons
            if test_season_int >= current_year:
                self.logger.info(f"🔍 Checking temporal status for season {test_season_int} week {test_week}...")
                
                # Get completed weeks to determine if this is backtesting or live prediction
                completed_weeks = TemporalValidator.get_completed_weeks(
                    test_season_int, self.db_service, self.logger
                )
                
                if test_week in completed_weeks:
                    # Week already completed - this is historical backtesting, allow it
                    self.logger.info(f"✓ Backtesting mode: Week {test_week} of {test_season_int} already completed")
                else:
                    # Week not completed - this is predicting the future, check for leakage
                    self.logger.warning(
                        f"⚠️ TEMPORAL LEAKAGE WARNING: Week {test_week} of {test_season_int} has not been completed!\n"
                        f"   Testing on incomplete/future weeks produces misleading results.\n"
                        f"   Completed weeks: {completed_weeks}\n"
                        f"   Safe test weeks (completed): {completed_weeks[:5] if completed_weeks else 'None'}"
                    )
                    self.logger.error("❌ Training cancelled due to temporal leakage risk. Use --force to override.")
                    return {
                        'status': 'error',
                        'message': 'Temporal leakage detected - testing on incomplete/future week. Use --force to override'
                    }
            else:
                # Historical testing - no temporal leakage possible
                self.logger.info(f"✓ Historical testing on {test_season_int} Week {test_week} - skipping temporal validation")
        
        # Step 2: Dry-run preview
        if dry_run:
            from ..utils import TrainingPreview
            
            preview = TrainingPreview.preview_training(
                model_class.MODEL_NAME, train_seasons, test_seasons, test_week
            )
            TrainingPreview.display_preview(preview, self.logger)
            return {'status': 'dry_run', 'preview': preview}
        
        # Step 3: Auto-build features (MODEL-AWARE)
        if auto_build_features:
            from ..utils.feature_checker import FeatureAvailabilityChecker
            
            # ✅ GET REQUIRED FEATURES FROM MODEL CLASS
            required_features = list(model_class.FEATURE_TABLES.keys())
            
            self.logger.info(f"🔍 Model {model_class.MODEL_NAME} requires: {required_features}")
            
            success = FeatureAvailabilityChecker.auto_build_features(
                train_seasons, required_features, self.logger
            )
            if not success:
                self.logger.error("❌ Feature building failed")
                return {
                    'status': 'error',
                    'message': 'Feature building failed'
                }
        
        # Step 4: Call core training workflow (no saving - returns model)
        # ✅ ARCHITECTURAL FIX: _execute_training_workflow() no longer saves, we handle it here
        result = self._execute_training_workflow(
            model_class=model_class,
            train_seasons=train_seasons,
            test_seasons=test_seasons,
            test_week=test_week,
            random_state=random_state
        )
        
        # Step 5: Save model with versioning if successful
        # ✅ SINGLE SAVE PATH: All models saved through ModelVersionManager
        if result['status'] == 'success' and save_model:
            # Use new versioned save
            from ..utils import ModelVersionManager
            
            # Prepare metadata
            version_metadata = {
                'metrics': result['metrics'],
                'config': {
                    'train_seasons': train_seasons,
                    'test_seasons': test_seasons,
                    'test_week': test_week,
                    'random_state': random_state
                },
                'test_games': result['test_size'],
                'train_games': result['train_size'],
                'num_features': result['num_features']
            }
            
            # Add any additional metadata
            if metadata:
                version_metadata.update(metadata)

            # Save with version tag
            model_path = ModelVersionManager.save_model(
                result['model'],
                model_class.MODEL_NAME,
                tag or 'latest',
                version_metadata
            )
            
            result['model_path'] = model_path
            result['version_tag'] = tag or 'latest'
            
            self.logger.info(f"✓ Model saved with version tag: {tag or 'latest'}")
        
        return result

def create_model_trainer(db_service=None, logger=None, feature_builder=None, schedule_provider=None):
    """
    Create model trainer with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        feature_builder: Optional real feature builder override
        schedule_provider: Optional schedule provider override
        
    Returns:
        ModelTrainerImplementation: Configured model trainer
    """
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.model_trainer')
    
    return ModelTrainerImplementation(db_service, logger, feature_builder, schedule_provider)


__all__ = ['ModelTrainerImplementation', 'create_model_trainer']