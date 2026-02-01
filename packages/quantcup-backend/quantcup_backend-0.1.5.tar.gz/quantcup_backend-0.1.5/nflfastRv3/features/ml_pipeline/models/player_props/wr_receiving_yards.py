"""
WR/TE Receiving Yards Prediction Model

TODO: Predict wide receiver/tight end receiving yards for a specific game.
Target: receiving_yards (regression)

Features:
- WR's recent receiving yard averages (4g, 8g, season)
- Target share percentage
- Air yards per target
- Opponent pass defense ranking (yards allowed)
- Opponent coverage scheme (man vs zone)
- QB passing volume prediction
- Weather conditions (wind affects deep passes)
- Home/away splits
- Matchup vs specific CB (if shadow coverage)

Model Type: XGBoost Regressor
Evaluation Metrics: MAE, RMSE, Over/Under prop accuracy
Expected Performance: MAE ~15-20 yards

Use Cases:
- WR/TE receiving yards over/under props
- DFS optimization
- Parlay building

Data Requirements:
- Player-level receiving stats from play-by-play
- Target data (receptions, targets, air yards)
- Opponent secondary stats
- QB-WR connection history

Example Props:
- Tyreek Hill Over 75.5 receiving yards
- Travis Kelce Under 65.5 receiving yards
- CeeDee Lamb Over 80.5 receiving yards
"""