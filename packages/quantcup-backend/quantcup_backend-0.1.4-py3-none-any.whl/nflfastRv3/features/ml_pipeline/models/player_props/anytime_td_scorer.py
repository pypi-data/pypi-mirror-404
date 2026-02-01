"""
Anytime TD Scorer Prediction Model

TODO: Predict probability that a player scores a touchdown (any type).
Target: scored_td (binary classification)

Features:
- Player's recent TD rate (TDs per game)
- Red zone touches/targets
- Goal line usage percentage
- Opponent red zone defense ranking
- Game total prediction (more TDs in high-scoring games)
- Player position (RB/WR/TE have different TD rates)
- Home/away splits
- Weather conditions

Model Type: XGBoost Binary Classifier
Evaluation Metrics: AUC-ROC, Precision, Recall, Calibration
Expected Performance: AUC ~0.70-0.75

Use Cases:
- Anytime TD scorer props (very popular)
- First TD scorer props (requires additional modeling)
- Last TD scorer props
- Parlay building
- DFS optimization

Data Requirements:
- Player-level TD stats from play-by-play
- Red zone play filtering
- Position-specific TD rates

Example Props:
- Christian McCaffrey Anytime TD (-150)
- Travis Kelce Anytime TD (+120)
- Tyreek Hill Anytime TD (+140)

Note: First TD and Last TD require different models with adjusted probabilities
based on game flow and scoring distribution.
"""