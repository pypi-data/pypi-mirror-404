"""
Advanced Prediction Models

This package contains sophisticated models for specialized betting markets
and live/in-game predictions.

Categories:
- Live Predictions: Win probability, next score, drive outcomes
- Situational Models: Weather-dependent, divisional games, rest scenarios
- Exotic Markets: Parlays, teasers, same-game parlays
- Advanced Analytics: EPA predictions, DVOA forecasts

Data Requirements:
- Real-time game state (for live models)
- Play-by-play sequences
- Situational context
- Correlation matrices (for parlays)
"""

__all__ = [
    'live_win_probability',
    'next_score_type',
    'drive_outcome',
]