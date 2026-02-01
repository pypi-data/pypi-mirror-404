"""
Team Totals Prediction Model

TODO: Predict individual team point totals (home and away separately).
Targets: 
- home_score (regression)
- away_score (regression)

Features:
- Team-specific offensive metrics
- Opponent defensive metrics
- Venue effects (home field advantage)
- Weather impacts on scoring
- Rest and travel factors
- Historical scoring patterns vs similar opponents

Model Type: XGBoost Regressor (separate models for home/away or multi-output)
Evaluation Metrics: MAE, RMSE, Over/Under accuracy for team total props
Expected Performance: MAE ~3-4 points per team

Use Cases:
- Team total over/under props
- Derive game total predictions (sum of both)
- Derive spread predictions (difference)
- Player prop correlations (QB/RB/WR stats scale with team scoring)

Data Requirements:
- dim_game.home_score, away_score (already available)
- Need to build team-specific offensive/defensive features
"""