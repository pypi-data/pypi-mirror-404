"""
Futures Prediction Models

This package contains models for predicting season-long outcomes and awards.
These markets have long-term value and require different feature engineering.

Categories:
- Season Wins: Total wins, playoff probability
- Championships: Division, Conference, Super Bowl
- Awards: MVP, OPOY, DPOY, ROTY, Coach of Year
- Milestones: 1000-yard seasons, Pro Bowl selections

Data Requirements:
- Season-to-date statistics
- Strength of schedule (remaining games)
- Historical team/player trajectories
- Injury reports and roster changes
"""

__all__ = [
    'season_wins',
    'playoff_probability',
    'division_winner',
    'super_bowl_winner',
]