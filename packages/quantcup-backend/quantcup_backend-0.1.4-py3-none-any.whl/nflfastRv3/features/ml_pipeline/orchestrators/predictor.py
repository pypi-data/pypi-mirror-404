"""
Prediction Generation Implementation for nflfastRv3

Migrates proven Predictor business logic from nflfastRv2 into clean architecture.
Following REFACTORING_SPECS.md: Maximum 5 complexity points, 3 layers depth.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Implementation - calls infrastructure directly)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from commonv2 import get_logger
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from ....shared.schedule_provider import ScheduleDataProvider
from ..models.game_lines.game_outcome import GameOutcomeModel
from ..utils.feature_registry import FeatureRegistry


class PredictorImplementation:
    """
    Core prediction generation business logic.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + business logic)
    Depth: 1 layer (calls infrastructure directly)
    
    Migrated from nflfastRv2.Predictor with architectural simplification.
    """
    
    def __init__(self, logger):
        """
        Initialize with injected dependencies.
        
        Args:
            logger: Logger instance (Layer 3)
        """
        self.logger = logger
        self.bucket_adapter = get_bucket_adapter(logger=self.logger)
    
    def generate_predictions(self, model_name, week=None, season=None,
                           model_version='latest', save_predictions=True, output_file=None,
                           include_preseason=False, include_postseason=False):
        """
        Execute prediction generation workflow.
        
        ENHANCED in v2: Supports model version selection and auto-detection of season/week.
        
        Simple prediction flow (migrated from V2):
        1. Load trained model (Layer 3 call) - NOW WITH VERSION SUPPORT
        2. Load upcoming games (Layer 3 call)
        3. Generate predictions for each game (Layer 3 calls)
        4. Save predictions if requested (Layer 3 call)
        5. Return summary
        
        Args:
            model_name: Model to use for predictions (default: 'game_outcome')
            week: NFL week to predict (None = auto-detect current week)
            season: NFL season (None = auto-detect current season)
            model_version: Model version to use (NEW in v2, default: 'latest')
            save_predictions: Save predictions to database
            output_file: Save predictions to CSV file
            include_preseason: Include preseason games
            include_postseason: Include postseason games
            
        Returns:
            dict: Prediction results with status and predictions
        """
        # Auto-detect season/week if not provided
        if season is None:
            from commonv2.domain.schedules import SeasonParser
            season = SeasonParser.get_current_season(self.logger)
        
        if week is None:
            from commonv2.domain.schedules import WeekParser
            week = WeekParser.get_current_week(season=season, logger=self.logger)
        
        self.logger.info(f"Starting prediction generation for Week {week}, {season} season")
        self.logger.info(f"Using model: {model_name} (version: {model_version})")
        
        try:
            # Step 1: Load trained model with version support (ENHANCED)
            model = self._load_model_version(model_name, model_version)
            if model is None:
                return {
                    'status': 'error',
                    'message': f'Model {model_name} (version {model_version}) not found',
                    'predictions': []
                }
            
            # Step 2: Load upcoming games (Layer 3 call)
            upcoming_games = self._load_upcoming_games(
                week, season, include_preseason, include_postseason
            )
            
            if upcoming_games.empty:
                self.logger.warning("No upcoming games found for prediction")
                return {
                    'status': 'success',
                    'predictions': [],
                    'message': 'No games to predict'
                }
            
            self.logger.info(f"Found {len(upcoming_games)} games to predict")
            
            # Step 3: Generate predictions for each game (Layer 3 calls)
            predictions_list = []
            
            for _, game in upcoming_games.iterrows():
                try:
                    prediction = self._generate_game_prediction(
                        game, model, model_name, week, season
                    )
                    if prediction:
                        predictions_list.append(prediction)
                        
                except Exception as e:
                    self.logger.error(f"Failed to predict {game.get('game_id', 'unknown')}: {e}")
                    continue
            
            if not predictions_list:
                self.logger.warning("No predictions generated")
                return {
                    'status': 'success',
                    'predictions': [],
                    'message': 'No predictions could be generated'
                }
            
            predictions_df = pd.DataFrame(predictions_list)
            
            # Step 4: Save predictions if requested (Layer 3 calls)
            if save_predictions:
                self._save_predictions_to_bucket(predictions_df, model_name)
            
            if output_file:
                predictions_df.to_csv(output_file, index=False)
                self.logger.info(f"Predictions saved to {output_file}")
            else:
                # Default to root data folder if no output file specified
                data_dir = Path.cwd() / "data"
                data_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_output = data_dir / f"predictions_{model_name}_{season}_{week}_{timestamp}.csv"
                predictions_df.to_csv(default_output, index=False)
                self.logger.info(f"Predictions saved to default location: {default_output}")
            
            self.logger.info("✅ Prediction generation completed successfully")
            
            return {
                'status': 'success',
                'predictions': predictions_list,
                'num_predictions': len(predictions_list),
                'season': season,  # Include for downstream use
                'week': week,      # Include for downstream use
                'output_file': output_file
            }
            
        except Exception as e:
            self.logger.error(f"Prediction generation failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'predictions': []
            }
    
    def _load_model_version(self, model_name, version):
        """
        Load specific model version from version manager.
        
        Args:
            model_name: Name of the model to load
            version: Version tag to load (default: 'latest')
            
        Returns:
            Loaded model or None if not found
        """
        try:
            from ..utils import ModelVersionManager
            
            model, metadata = ModelVersionManager.load_model(model_name, version)
            
            self.logger.info(f"✓ Loaded model version: {version}")
            self.logger.info(f"   Trained: {metadata.get('created_at', 'unknown')}")
            self.logger.info(f"   Accuracy: {metadata.get('metrics', {}).get('accuracy', 'unknown')}")
            
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name} version {version}: {e}")
            return None
    
    def _load_upcoming_games(self, week, season, include_preseason=False, include_postseason=False):
        """
        Load upcoming games from schedule using real CommonV2 integration.
        
        Args:
            week: NFL week
            season: NFL season
            include_preseason: Include preseason games
            include_postseason: Include postseason games
            
        Returns:
            DataFrame with upcoming games
        """
        try:
            # Use real schedule provider integration
            schedule_provider = ScheduleDataProvider()
            
            # Get schedule data for the specific week
            schedule_games = schedule_provider.get_games_for_week(season, week)
            
            if not schedule_games:
                self.logger.warning(f"No schedule games found for Week {week}, {season}")
                return pd.DataFrame()
            
            # Convert to DataFrame format expected by prediction pipeline
            games_data = []
            for game in schedule_games:
                # Filter based on actual season_type field (not unreliable week numbers)
                #season_type values: 'PRE' (preseason), 'REG' (regular season), 'POST' (postseason)
                if not include_preseason and game.season_type == 'PRE':
                    continue
                if not include_postseason and game.season_type == 'POST':
                    continue
                
                # Create game record
                game_data = {
                    'game_id': game.game_id,
                    'home_team': game.home_team,
                    'away_team': game.away_team,
                    'week': game.week,
                    'season': game.season,
                    'game_date': game.game_date.isoformat() if game.game_date else None,
                    'stadium': game.stadium,
                    'weather': game.weather
                }
                games_data.append(game_data)
            
            df = pd.DataFrame(games_data)
            self.logger.info(f"Loaded {len(df)} upcoming games for Week {week}, {season}")
            
            # Log week breakdown
            if not df.empty:
                week_breakdown = df['week'].value_counts().to_dict()
                self.logger.debug(f"Games by week: {week_breakdown}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load upcoming games: {e}")
            raise ValueError(
                f"Failed to load upcoming games for Week {week}, {season}: {e}. "
                "Check that schedule data is available in the database."
            ) from e
    
    def _generate_game_prediction(self, game, model, model_name, week, season):
        """
        Generate prediction for a single game.
        
        Args:
            game: Game data row
            model: Trained model
            model_name: Name of the model
            week: NFL week
            season: NFL season
            
        Returns:
            dict: Prediction data or None if failed
        """
        try:
            # Step 1: Prepare features for this game (Layer 3 call)
            # Step 1: Prepare features for this game (Layer 3 call)
            # UPDATED: Use warehouse features to match training pipeline
            game_features = self._prepare_features_from_warehouse(
                game['game_id'], game['home_team'], game['away_team'], season, week
            )
            
            if game_features is None or game_features.empty:
                self.logger.error(f"Could not generate features for {game['game_id']}")
                raise ValueError(
                    f"Could not generate features for game {game['game_id']}. "
                    "Check that historical data is available."
                )
            
            # Step 2: Generate prediction (Layer 3 call)
            # Pass DataFrame directly to preserve feature names
            home_win_prob = model.predict_proba(game_features)[0][1]
            
            # Step 3: Calculate derived metrics
            # Confidence = probability of predicted winner
            confidence = max(home_win_prob, 1 - home_win_prob)
            predicted_winner = game['home_team'] if home_win_prob >= 0.5 else game['away_team']
            
            # Construct prediction result
            result = {
                'game_id': game['game_id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'week': week,
                'season': season,
                'game_date': game.get('game_date', None),
                'home_win_prob': float(home_win_prob),
                'confidence': float(confidence),
                'predicted_winner': predicted_winner,
                'model_version': model_name,
                'prediction_date': datetime.now()
            }

            # Add key features for explainability
            # These help answer "why did the model pick this?"
            explainability_features = [
                'epa_advantage_4game',
                'rolling_4g_epa_offense_diff',
                'rolling_4g_epa_defense_diff',
                'win_rate_advantage',
                'momentum_advantage',
                'rest_days_diff',
                'stadium_home_win_rate'
            ]

            for feature in explainability_features:
                if feature in game_features.columns:
                    result[feature] = float(game_features[feature].iloc[0])

            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate prediction for {game.get('game_id', 'unknown')}: {e}")
            return None
    
    def _prepare_features_from_warehouse(self, game_id, home_team, away_team, season, week):
        """
        Prepare features using the exact same pipeline as training.
        
        Fetches latest rolling metrics from warehouse and applies GameOutcomeModel logic.
        
        Args:
            game_id: Game identifier
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            season: NFL season
            week: NFL week
            
        Returns:
            DataFrame with single row of features
        """
        try:
            from commonv2.persistence.bucket_adapter import get_bucket_adapter
            bucket_adapter = get_bucket_adapter(logger=self.logger)
            
            # 1. Fetch latest rolling metrics for both teams
            # We need the stats ENTERING this week.
            # If the pipeline has run for this week, we might have rows for this week.
            # If not, we should use the most recent available row for this season.
            
            self.logger.info(f"🔍 Fetching warehouse features for {home_team} vs {away_team}")
            
            # Load rolling metrics for this season
            rolling_df = bucket_adapter.read_data(
                table_name='rolling_metrics_v1',
                schema='features',
                filters=[('season', '==', season)]
            )
            
            if rolling_df.empty:
                # Fallback to previous season if early in season?
                # For now, just error out
                raise ValueError(f"No rolling metrics found for season {season}")
            
            # Get latest row for home team
            home_rows = rolling_df[rolling_df['team'] == home_team].sort_values('week', ascending=False)
            if home_rows.empty:
                raise ValueError(f"No rolling metrics found for home team {home_team}")
            
            # Use the most recent row available
            # Ideally this is week-1, but we take what we have
            home_stats = home_rows.iloc[0:1].copy()
            self.logger.debug(f"Using home stats from week {home_stats['week'].iloc[0]}")
            
            # Get latest row for away team
            away_rows = rolling_df[rolling_df['team'] == away_team].sort_values('week', ascending=False)
            if away_rows.empty:
                raise ValueError(f"No rolling metrics found for away team {away_team}")
            
            away_stats = away_rows.iloc[0:1].copy()
            self.logger.debug(f"Using away stats from week {away_stats['week'].iloc[0]}")
            
            # 2. Construct a target-like dictionary for this game
            # We need to mimic the structure expected by GameOutcomeModel.prepare_data
            # But prepare_data does the merging. We can do it manually here to be precise.
            
            # Create base game dictionary
            game_data = {
                'game_id': game_id,
                'season': season,
                'week': week,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': 0, # Dummy
                'away_score': 0  # Dummy
            }
            
            # 3. Merge features manually (since we're using specific rows, not joining on week)
            # Rename home stats
            for col in home_stats.columns:
                if col not in ['game_id', 'season', 'week', 'team']:
                    game_data[f'home_{col}'] = home_stats[col].iloc[0]
            
            # Rename away stats
            for col in away_stats.columns:
                if col not in ['game_id', 'season', 'week', 'team']:
                    game_data[f'away_{col}'] = away_stats[col].iloc[0]
            
            # 4. Add contextual features if available
            try:
                contextual_df = bucket_adapter.read_data(
                    table_name='contextual_features_v1',
                    schema='features',
                    filters=[('season', '==', season)]
                )
                # Try to find exact game match
                game_ctx = contextual_df[contextual_df['game_id'] == game_id]
                if not game_ctx.empty:
                    for col in game_ctx.columns:
                        if col not in game_data:
                            game_data[col] = game_ctx[col].iloc[0]
            except Exception as e:
                self.logger.warning(f"Could not load contextual features: {e}")

            # 5. Add NextGen features if available
            try:
                nextgen_df = bucket_adapter.read_data(
                    table_name='nextgen_features_v1',
                    schema='features',
                    filters=[('season', '==', season)]
                )
                game_ng = nextgen_df[nextgen_df['game_id'] == game_id]
                if not game_ng.empty:
                    for col in game_ng.columns:
                        if col not in game_data:
                            game_data[col] = game_ng[col].iloc[0]
            except Exception:
                pass

            # 6. Add Injury features if available
            try:
                injury_df = bucket_adapter.read_data(
                    table_name='injury_features_v1',
                    schema='features',
                    filters=[('season', '==', season)]
                )
                game_inj = injury_df[injury_df['game_id'] == game_id]
                if not game_inj.empty:
                    for col in game_inj.columns:
                        if col not in game_data:
                            game_data[col] = game_inj[col].iloc[0]
            except Exception:
                pass
            
            # Create DataFrame once to avoid fragmentation
            game_row = pd.DataFrame([game_data])
            
            # 7. Apply Feature Engineering
            # This creates the _diff columns
            game_row = GameOutcomeModel.engineer_features(game_row, logger=None)
            
            # 8. Select Features
            # We need to add dummy target for select_features to work
            game_row['home_team_won'] = 0
            
            model_df = GameOutcomeModel.select_features(game_row, logger=None)
            
            # Drop metadata and target to get just the feature vector
            exclude_cols = GameOutcomeModel.METADATA_COLUMNS + [GameOutcomeModel.TARGET_VARIABLE]
            feature_cols = [col for col in model_df.columns if col not in exclude_cols]
            
            X = model_df[feature_cols].fillna(0)
            
            # 9. Ensure all required features are present (fill with 0 if missing)
            # This handles cases where contextual/nextgen/injury data is missing for future games
            required_features = FeatureRegistry.get_active_features()
            
            for feature in required_features:
                if feature not in X.columns:
                    self.logger.debug(f"Missing feature {feature}, filling with 0")
                    X[feature] = 0.0
                    
            # Filter X to only include active features (removes extra columns)
            X = X[required_features]
            
            self.logger.debug(f"Generated {len(X.columns)} features matching training pipeline")
            
            return X
            
        except Exception as e:
            self.logger.error(f"Failed to prepare warehouse features for {game_id}: {e}")
            raise ValueError(f"Failed to prepare features for {game_id}: {e}") from e
    
    def _save_predictions_to_bucket(self, predictions_df, model_name):
        """
        Save predictions to the bucket.
        
        Args:
            predictions_df: DataFrame with predictions
            model_name: Name of the model used
        """
        try:
            # Add model_name to predictions
            predictions_df = predictions_df.copy()
            predictions_df['model_name'] = model_name
            
            # Save predictions (Layer 3 call)
            # We append to a single file or partition by season/week?
            # For now, let's save as a single file per run to avoid overwriting history
            # or maybe partition by season/week
            
            season = predictions_df['season'].iloc[0]
            week = predictions_df['week'].iloc[0]
            
            # Construct a unique key for this prediction run
            # ml/predictions/season=2025/week=12/predictions_2025_12_timestamp.parquet
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"ml/predictions/season={season}/week={week}/predictions_{season}_{week}_{timestamp}.parquet"
            
            # Use bucket adapter to store directly
            # We use s3_client directly to put object at specific key since store_data enforces schema structure
            
            if not self.bucket_adapter._is_available():
                self.logger.warning("Bucket not available - skipping prediction save")
                return

            # Ensure client and bucket are available (for type checker)
            if self.bucket_adapter.s3_client is None or self.bucket_adapter.bucket_name is None:
                self.logger.error("Bucket adapter is available but client or bucket name is None")
                return

            parquet_buffer = predictions_df.to_parquet(index=False, engine='pyarrow')
            
            self.bucket_adapter.s3_client.put_object(
                Bucket=self.bucket_adapter.bucket_name,
                Key=key,
                Body=parquet_buffer,
                ContentType='application/octet-stream'
            )
            
            self.logger.info(f"✓ Saved {len(predictions_df)} predictions to bucket: {key}")
            
        except Exception as e:
            self.logger.error(f"Failed to save predictions to bucket: {e}")


def create_predictor(logger=None):
    """
    Create predictor with default dependencies.
    
    Args:
        logger: Optional logger override
        
    Returns:
        PredictorImplementation: Configured predictor
    """
    logger = logger or get_logger('nflfastRv3.predictor')
    
    return PredictorImplementation(logger)


__all__ = ['PredictorImplementation', 'create_predictor']
