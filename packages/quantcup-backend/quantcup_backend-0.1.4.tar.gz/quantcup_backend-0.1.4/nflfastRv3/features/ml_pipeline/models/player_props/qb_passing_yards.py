"""
QB Passing Yards Prediction Model

TODO: Predict quarterback passing yards for a specific game.
Target: passing_yards (regression)

Features:
- QB's recent passing yard averages (4g, 8g, season)
- Opponent pass defense ranking (yards allowed per game)
- Opponent pass defense EPA
- Weather conditions (wind, precipitation)
- Venue type (dome vs outdoor)
- Game script prediction (trailing teams pass more)
- Home/away splits
- Division game indicator (often lower scoring)
- QB injury status / practice participation

Model Type: XGBoost Regressor
Evaluation Metrics: MAE, RMSE, Over/Under prop accuracy
Expected Performance: MAE ~30-40 yards

Use Cases:
- QB passing yards over/under props (most popular player prop)
- Parlay building
- DFS optimization

Data Requirements:
- Player-level passing stats from play-by-play
- Need to aggregate by player_id and game_id
- Opponent defensive stats
- Weather data (already in dim_game)

Example Props:
- Patrick Mahomes Over 275.5 passing yards
- Josh Allen Under 250.5 passing yards
"""