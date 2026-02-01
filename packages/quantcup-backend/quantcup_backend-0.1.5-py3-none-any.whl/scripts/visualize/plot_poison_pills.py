#!/usr/bin/env python3
"""
One-off script to visualize poison pill detection: Feature Importance vs Correlation scatter plot.

This script loads the most recent trained model and training data to create a scatter plot
showing feature importance on x-axis and absolute correlation on y-axis. The poison pill
zone (importance > 0.15, correlation < 0.02) is shaded in red.

Usage:
    python scripts/plot_poison_pills.py [--season YYYY]

Requirements:
    - matplotlib
    - pandas
    - numpy
    - joblib
    - Recent training run with saved model
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os
import joblib
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from commonv2.persistence.bucket_adapter import BucketAdapter
from nflfastRv3.features.ml_pipeline.utils.feature_diagnostics import FeatureDiagnostics
from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeModel
from commonv2 import get_logger

logger = get_logger(__name__)

def find_latest_model() -> Path:
    """Find the most recent model file in ml/models/game_outcome/"""
    bucket = BucketAdapter()
    
    # List all model files
    model_files = bucket.list_files('ml/models/game_outcome/')
    
    if not model_files:
        raise FileNotFoundError("No model files found in ml/models/game_outcome/")
    
    # Filter for .joblib files and get the most recent
    joblib_files = [f for f in model_files if f.endswith('.joblib')]
    
    if not joblib_files:
        raise FileNotFoundError("No .joblib model files found")
    
    # Return the first one (assuming it's the most recent)
    # You may need to parse timestamps from filenames to truly get the latest
    return Path(joblib_files[0])

def load_model_from_bucket(model_path: str):
    """Load a trained model from the bucket."""
    bucket = BucketAdapter()
    
    if not bucket._is_available():
        raise RuntimeError("Bucket not available - cannot load model")
    
    try:
        # Get the model file from S3 (s3_client/bucket_name guaranteed not None by _is_available)
        assert bucket.s3_client is not None and bucket.bucket_name is not None
        response = bucket.s3_client.get_object(
            Bucket=bucket.bucket_name,
            Key=model_path
        )
        
        # Load model from bytes
        model_bytes = response['Body'].read()
        
        # Save to temp file and load with joblib
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as tmp:
            tmp.write(model_bytes)
            tmp_path = tmp.name
        
        try:
            model = joblib.load(tmp_path)
            return model
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            
    except Exception as e:
        raise RuntimeError(f"Failed to load model from {model_path}: {e}")

def main():
    """Create poison pill visualization plot."""
    parser = argparse.ArgumentParser(description='Generate poison pill visualization')
    parser.add_argument('--season', type=int, default=2023, help='Season to use for training data (default: 2023)')
    args = parser.parse_args()
    
    logger.info("🎨 Creating poison pill detection visualization")
    logger.info(f"Using season {args.season} for training data")

    try:
        # Initialize bucket adapter
        bucket = BucketAdapter()

        # Step 1: Load the trained model using ModelVersionManager
        logger.info("Loading trained model...")
        try:
            from nflfastRv3.features.ml_pipeline.utils.model_version_manager import ModelVersionManager
            
            # Use ModelVersionManager to load the latest model (same logic as training pipeline)
            # Returns tuple: (model, metadata)
            model, metadata = ModelVersionManager.load_model(
                model_name='game_outcome',
                version='latest'
            )
            logger.info(f"✓ Loaded latest model: {metadata.get('model_path', 'unknown path')}")
            logger.info(f"   Created: {metadata.get('created_at', 'unknown')}")
            metrics = metadata.get('metrics', {})
            if metrics:
                logger.info(f"   Accuracy: {metrics.get('accuracy', 'N/A')}")
        except Exception as e:
            logger.error(f"Could not load model: {e}")
            logger.info("Please ensure you have a trained model")
            logger.info("Train using: quantcup nflfastrv3 ml train --model-name game_outcome --train-years 6")
            return

        # Step 2: Load feature data from warehouse/features
        logger.info("Loading feature tables...")
        
        # Load dim_game for target variable and game context
        # Filters must be list of tuples: [(column, operator, value)]
        season_filter = [('season', '==', args.season)]
        
        dim_game = bucket.read_data('dim_game', schema='warehouse',
                                    filters=season_filter)
        
        if dim_game is None or len(dim_game) == 0:
            logger.error(f"No game data found for season {args.season}")
            return
        
        # Load all feature tables used by the model
        rolling_metrics = bucket.read_data('rolling_metrics_v1', schema='features',
                                          filters=season_filter)
        contextual_features = bucket.read_data('contextual_features_v1', schema='features',
                                              filters=season_filter)
        
        logger.info(f"Loaded {len(dim_game)} games from season {args.season}")
        
        # Step 3: Build feature set manually
        logger.info("Building feature set...")
        
        # Get target from dim_game
        target_col = 'home_team_won'
        if target_col not in dim_game.columns:
            logger.error(f"Target column '{target_col}' not found in dim_game")
            return
        
        # Select only NUMERIC metric columns from rolling_metrics (exclude identifiers and non-numeric)
        id_cols = ['game_id', 'team', 'season', 'week', 'game_date', 'home_team', 'away_team', 'venue']
        
        # Get numeric columns only
        numeric_rolling_cols = rolling_metrics.select_dtypes(include=[np.number]).columns
        metric_cols = [col for col in numeric_rolling_cols if col not in id_cols]
        
        logger.info(f"Rolling metrics: {len(metric_cols)} numeric metric columns")
        
        # Prepare home and away rolling metrics with only metrics (keep game_id and team for merging)
        home_rolling = rolling_metrics[['game_id', 'team', *metric_cols]].copy()
        away_rolling = rolling_metrics[['game_id', 'team', *metric_cols]].copy()
        
        # Rename metric columns to add home/away prefix
        home_rolling = home_rolling.rename(columns={col: f'home_{col}' for col in metric_cols})
        away_rolling = away_rolling.rename(columns={col: f'away_{col}' for col in metric_cols})
        
        # Merge home team rolling metrics
        merged = dim_game.merge(
            home_rolling,
            left_on=['game_id', 'home_team'],
            right_on=['game_id', 'team'],
            how='left'
        ).drop(columns=['team'], errors='ignore')
        
        # Merge away team rolling metrics
        merged = merged.merge(
            away_rolling,
            left_on=['game_id', 'away_team'],
            right_on=['game_id', 'team'],
            how='left'
        ).drop(columns=['team'], errors='ignore')
        
        # Create differentials (home - away) for the numeric rolling metrics
        for col in metric_cols:
            home_col = f'home_{col}'
            away_col = f'away_{col}'
            if home_col in merged.columns and away_col in merged.columns:
                # Only subtract if both columns are numeric
                if pd.api.types.is_numeric_dtype(merged[home_col]) and pd.api.types.is_numeric_dtype(merged[away_col]):
                    merged[f'{col}_diff'] = merged[home_col] - merged[away_col]
        
        # Merge contextual features (these are already game-level, no home/away split needed)
        if contextual_features is not None and len(contextual_features) > 0:
            # Only merge on columns that exist in both
            merge_cols = ['game_id']
            if 'season' in contextual_features.columns and 'season' in merged.columns:
                merge_cols.append('season')
            if 'week' in contextual_features.columns and 'week' in merged.columns:
                merge_cols.append('week')
            
            merged = merged.merge(
                contextual_features,
                on=merge_cols,
                how='left',
                suffixes=('', '_ctx')
            )
        
        # Get feature columns (numeric only, exclude identifiers and target)
        exclude_cols = ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team',
                       'home_score', 'away_score', 'home_team_won', 'team']
        
        # Get all numeric columns except excluded ones
        numeric_cols = merged.select_dtypes(include=[np.number]).columns
        feature_cols = [col for col in numeric_cols if not any(excl in col for excl in exclude_cols)]
        
        X_train = merged[feature_cols].fillna(0)
        y_train = merged[target_col]
        
        logger.info(f"Built feature set: {len(X_train)} samples with {len(feature_cols)} features")

        # Step 4: Get feature importances from the model
        # The model might be an ensemble, so we need to get the XGBoost component
        if hasattr(model, 'xgboost_model'):
            # It's an ensemble - use the XGBoost model
            xgb_model = model.xgboost_model
            logger.info("Using XGBoost model from ensemble")
        elif hasattr(model, 'feature_importances_'):
            # It's a direct model
            xgb_model = model
            logger.info("Using direct model")
        else:
            logger.error("Model does not have feature_importances_ attribute")
            logger.error(f"Model type: {type(model)}")
            logger.error(f"Model attributes: {dir(model)}")
            return

        # Get the feature names the model was trained on
        if hasattr(xgb_model, 'feature_names_in_'):
            model_features = list(xgb_model.feature_names_in_)
            logger.info(f"Model was trained on {len(model_features)} features")
        elif hasattr(xgb_model, 'get_booster'):
            # XGBoost booster feature names
            booster = xgb_model.get_booster()
            model_features = booster.feature_names
            logger.info(f"Model was trained on {len(model_features)} features (from booster)")
        else:
            logger.error("Cannot determine which features the model was trained on")
            logger.error(f"Model attributes: {[attr for attr in dir(xgb_model) if 'feature' in attr.lower()]}")
            return
        
        # Filter X_train to only include features the model was trained on
        missing_features = [f for f in model_features if f not in X_train.columns]
        if missing_features:
            logger.warning(f"Model trained on {len(missing_features)} features not in current data: {missing_features[:5]}...")
            # Fill missing features with zeros
            for feat in missing_features:
                X_train[feat] = 0
        
        # Select only the features the model knows about, in the correct order
        X_train = X_train[model_features]
        
        importances = xgb_model.feature_importances_
        feature_names = X_train.columns.tolist()
        
        logger.info(f"Using {len(feature_names)} features that match the trained model")
        
        if len(importances) != len(feature_names):
            logger.error(f"Mismatch: {len(importances)} importances but {len(feature_names)} features")
            logger.error(f"This shouldn't happen after filtering!")
            return

        # Step 5: Calculate correlations
        logger.info("Calculating correlations...")
        numeric_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
        correlations = X_train[numeric_cols].corrwith(y_train).abs()

        # Step 6: Create the plot
        logger.info("Creating visualization...")
        plt.figure(figsize=(14, 10))

        # Plot all features
        plt.scatter(importances, correlations, alpha=0.6, s=60, c='blue', edgecolors='black', linewidth=0.5)

        # Shade poison pill zone (importance > 0.15, correlation < 0.02)
        # Use fill_between for proper rectangular shading in data coordinates
        import matplotlib.patches as patches
        ax = plt.gca()
        
        # Create rectangle: x from 0.15 to max, y from 0 to 0.02
        x_max_for_zone = max(importances.max() * 1.1, 1.0)
        poison_zone = patches.Rectangle(
            (0.15, 0),  # Bottom-left corner (x, y)
            width=x_max_for_zone - 0.15,  # Width (extends to right edge)
            height=0.02,  # Height (from y=0 to y=0.02)
            facecolor='red',
            alpha=0.3,
            label='Poison Pill Zone (High Importance, Low Correlation)',
            zorder=0  # Draw behind scatter points
        )
        ax.add_patch(poison_zone)

        # Add threshold lines
        plt.axvline(x=0.15, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Importance Threshold (0.15)')
        plt.axhline(y=0.02, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Correlation Threshold (0.02)')

        # Labels and title
        plt.xlabel('Feature Importance', fontsize=14, fontweight='bold')
        plt.ylabel('Absolute Correlation with Target', fontsize=14, fontweight='bold')
        plt.title(f'Poison Pill Detection: Feature Importance vs Correlation\nSeason {args.season} Training Data',
                 fontsize=16, fontweight='bold')

        # Add grid and legend
        plt.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
        plt.legend(fontsize=11, loc='upper right')

        # Set axis limits
        plt.xlim(0, max(importances.max() * 1.1, 0.25))
        plt.ylim(0, min(1.0, correlations.max() * 1.1))

        # Annotate ALL features with labels
        poison_pills = FeatureDiagnostics.detect_poison_pills(xgb_model, X_train, y_train, 0.15, 0.02)
        logger.info(f"Annotating {len(feature_names)} features (Poison pills: {len(poison_pills) if poison_pills else 0})")
        
        for idx, (feature_name, imp, corr) in enumerate(zip(feature_names, importances, correlations)):
            # Determine if this feature is a poison pill
            is_poison = feature_name in poison_pills if poison_pills else False
            
            # Color-code labels: yellow for poison pills, light green for safe features
            label_color = 'yellow' if is_poison else 'lightgreen'
            edge_color = 'red' if is_poison else 'darkgreen'
            
            # Alternate label positions to reduce overlap
            if idx % 2 == 0:
                xytext = (12, 12)
            else:
                xytext = (12, -18)
            
            # Add feature label with appropriate styling
            plt.annotate(
                feature_name,
                (imp, corr),
                xytext=xytext,
                textcoords='offset points',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.5', facecolor=label_color,
                         edgecolor=edge_color, alpha=0.9, linewidth=1.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2',
                               color=edge_color, linewidth=1.2)
            )

        # Save plot
        output_path = f'scripts/poison_pill_plot_season{args.season}.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        logger.info(f"📊 Plot saved to {output_path}")

        # Show plot (if running interactively)
        try:
            plt.show()
        except:
            logger.info("(Not displaying plot - may be running headless)")

        logger.info("✅ Poison pill visualization complete")
        
        # Print summary statistics
        logger.info(f"\n📈 Summary Statistics:")
        logger.info(f"   Total features: {len(feature_names)}")
        logger.info(f"   Poison pills detected: {len(poison_pills) if poison_pills else 0}")
        logger.info(f"   Importance range: {importances.min():.4f} - {importances.max():.4f}")
        logger.info(f"   Correlation range: {correlations.min():.4f} - {correlations.max():.4f}")

    except Exception as e:
        logger.error(f"Error creating visualization: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()