"""
First Half Total Prediction Model

TODO: Predict first half total points (over/under).
Target: first_half_total (sum of Q1 + Q2 scores)

Features:
- First quarter scoring trends
- Script tendencies (aggressive vs conservative early)
- Coaching philosophy (Andy Reid vs Bill Belichick)
- Weather conditions (worse in 2nd half typically)
- Pace of play metrics
- Time of possession trends

Model Type: XGBoost Regressor or Binary Classifier (over/under line)
Evaluation Metrics: MAE, Over/Under accuracy
Expected Performance: MAE ~3-4 points

Use Cases:
- First half over/under props
- Live betting preparation
- Game script analysis

Data Requirements:
- Need to aggregate play-by-play data by quarter
- Extract Q1 + Q2 scores from pbp data
- Currently not in dim_game - requires new feature engineering
"""