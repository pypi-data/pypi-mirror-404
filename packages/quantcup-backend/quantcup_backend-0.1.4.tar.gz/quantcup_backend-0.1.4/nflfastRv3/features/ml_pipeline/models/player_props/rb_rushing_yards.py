"""
RB Rushing Yards Prediction Model

TODO: Predict running back rushing yards for a specific game.
Target: rushing_yards (regression)

Features:
- RB's recent rushing yard averages (4g, 8g, season)
- Carries per game trend
- Opponent rush defense ranking (yards allowed per game)
- Opponent defensive front EPA
- Game script prediction (leading teams run more)
- Weather conditions (rain/snow favors running)
- Offensive line strength
- Home/away splits
- RB injury status / workload share

Model Type: XGBoost Regressor
Evaluation Metrics: MAE, RMSE, Over/Under prop accuracy
Expected Performance: MAE ~15-25 yards

Use Cases:
- RB rushing yards over/under props
- DFS optimization
- Parlay building

Data Requirements:
- Player-level rushing stats from play-by-play
- Need to aggregate by player_id and game_id
- Opponent defensive stats
- Game script indicators

Example Props:
- Christian McCaffrey Over 85.5 rushing yards
- Derrick Henry Under 95.5 rushing yards
- Saquon Barkley Over 70.5 rushing yards
"""