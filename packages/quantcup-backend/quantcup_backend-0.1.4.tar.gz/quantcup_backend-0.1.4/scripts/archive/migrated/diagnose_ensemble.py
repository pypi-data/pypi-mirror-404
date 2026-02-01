import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from commonv2 import get_logger
from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeEnsemble, GameOutcomeModel
from nflfastRv3.features.ml_pipeline.orchestrators.model_trainer import ModelTrainerImplementation
from nflfastRv3.shared.database_router import DatabaseRouter

# Configure logging
logger = get_logger(__name__)

def diagnose_ensemble():
    logger.info("Starting Ensemble Diagnostic...")
    
    # 1. Load Data (using ModelTrainer logic)
    db_router = DatabaseRouter()
    trainer = ModelTrainerImplementation(db_service=db_router, logger=logger)
    
    train_seasons = list(range(2000, 2024))
    test_seasons = [2024]
    
    # Prepare data (loads features and targets for all seasons)
    logger.info("Preparing data...")
    # Note: _prepare_training_data is internal but we use it for diagnostics
    game_df = trainer._prepare_training_data(
        train_seasons=train_seasons,
        test_seasons=test_seasons,
        model_class=GameOutcomeModel
    )
    
    # Engineer features
    logger.info("Engineering features...")
    game_df = GameOutcomeModel.engineer_features(game_df, logger)
    
    # Select features
    logger.info("Selecting features...")
    model_df = GameOutcomeModel.select_features(game_df, logger)
    
    # Create train/test split
    logger.info("Creating train/test split...")
    X_train, X_test, y_train, y_test, test_metadata = trainer._create_train_test_split(
        model_df=model_df,
        train_seasons=train_seasons,
        test_seasons=test_seasons,
        model_class=GameOutcomeModel
    )
    
    # 2. Initialize and Train Ensemble
    logger.info("Initializing Ensemble...")
    ensemble = GameOutcomeEnsemble(random_state=42)
    
    logger.info("Training Ensemble (this may take a moment)...")
    ensemble.fit(X_train, y_train)
    
    # 3. Inspect Component Predictions
    logger.info("Generating component predictions for 2024...")
    
    # XGBoost
    xgb_prob = ensemble.xgboost_model.predict_proba(X_test)[:, 1]
    
    # Elastic Net (clip to 0-1)
    en_pred = ensemble.elastic_net_model.predict(X_test)
    en_prob = np.clip(en_pred, 0, 1)
    
    # Logistic Regression
    lr_prob = ensemble.logistic_model.predict_proba(X_test)[:, 1]
    
    # Ensemble Weighted Average
    ensemble_prob = ensemble.predict_proba(X_test)[:, 1]
    
    # 4. Analysis
    results = pd.DataFrame({
        'game_id': test_metadata['game_id'],
        'week': test_metadata['week'],
        'actual': y_test.values,
        'xgb_prob': xgb_prob,
        'en_prob': en_prob,
        'lr_prob': lr_prob,
        'ensemble_prob': ensemble_prob
    })
    
    # Correlation Matrix
    logger.info("\n=== Component Correlations ===")
    correlations = results[['xgb_prob', 'en_prob', 'lr_prob']].corr()
    print(correlations)
    
    # Weight Verification
    logger.info("\n=== Weight Verification (First 5 rows) ===")
    # Manual calculation
    results['manual_calc'] = (
        0.5 * results['xgb_prob'] + 
        0.3 * results['en_prob'] + 
        0.2 * results['lr_prob']
    )
    results['diff'] = results['ensemble_prob'] - results['manual_calc']
    print(results[['ensemble_prob', 'manual_calc', 'diff']].head())
    
    max_diff = results['diff'].abs().max()
    logger.info(f"Max difference between ensemble output and manual calculation: {max_diff:.6f}")
    
    # Performance by Component
    from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss
    
    logger.info("\n=== Component Performance (AUC) ===")
    logger.info(f"XGBoost AUC: {roc_auc_score(y_test, xgb_prob):.4f}")
    logger.info(f"Elastic Net AUC: {roc_auc_score(y_test, en_prob):.4f}")
    logger.info(f"Logistic Reg AUC: {roc_auc_score(y_test, lr_prob):.4f}")
    logger.info(f"Ensemble AUC: {roc_auc_score(y_test, ensemble_prob):.4f}")
    
    logger.info("\n=== Component Performance (Brier Score - Lower is Better) ===")
    logger.info(f"XGBoost Brier: {brier_score_loss(y_test, xgb_prob):.4f}")
    logger.info(f"Elastic Net Brier: {brier_score_loss(y_test, en_prob):.4f}")
    logger.info(f"Logistic Reg Brier: {brier_score_loss(y_test, lr_prob):.4f}")
    logger.info(f"Ensemble Brier: {brier_score_loss(y_test, ensemble_prob):.4f}")

    # Variance Analysis (Standard Deviation of Predictions)
    logger.info("\n=== Prediction Volatility (Std Dev) ===")
    logger.info(f"XGBoost Std: {xgb_prob.std():.4f}")
    logger.info(f"Elastic Net Std: {en_prob.std():.4f}")
    logger.info(f"Logistic Reg Std: {lr_prob.std():.4f}")
    logger.info(f"Ensemble Std: {ensemble_prob.std():.4f}")

if __name__ == "__main__":
    diagnose_ensemble()