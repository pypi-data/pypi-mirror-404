"""
Margin of Victory Prediction Model

TODO: Predict the exact point differential (home_score - away_score).
Target: result (regression, can be positive or negative)

Features:
- All differential features from game_outcome
- Historical margin trends
- Strength of schedule adjustments
- Blowout indicators
- Garbage time tendencies

Model Type: XGBoost Regressor
Evaluation Metrics: MAE, RMSE, R², Directional Accuracy
Expected Performance: MAE ~10-12 points

Use Cases:
- More granular than binary win/loss
- Can derive spread predictions
- Useful for prop betting (team totals)
- Parlay optimization

Data Requirements:
- dim_game.result (already available)
- dim_game.home_score, away_score (already available)
"""