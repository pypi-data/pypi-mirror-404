"""
QB Passing Touchdowns Prediction Model

TODO: Predict quarterback passing touchdowns for a specific game.
Target: passing_tds (regression or classification for over/under)

Features:
- QB's recent TD rate (TDs per game, TDs per attempt)
- Red zone efficiency
- Opponent red zone defense ranking
- Opponent pass defense TD rate allowed
- Home/away splits
- Weather conditions
- Game total prediction (higher scoring = more TDs)
- Target share of top receivers

Model Type: XGBoost Regressor or Poisson Regression
Evaluation Metrics: MAE, Over/Under prop accuracy, Exact count accuracy
Expected Performance: MAE ~0.5-0.7 TDs

Use Cases:
- QB passing TDs over/under props
- Anytime TD scorer correlations
- DFS optimization

Data Requirements:
- Player-level TD stats from play-by-play
- Red zone play filtering
- Opponent defensive stats in red zone

Example Props:
- Patrick Mahomes Over 2.5 passing TDs (-120)
- Joe Burrow Under 1.5 passing TDs (+110)
"""