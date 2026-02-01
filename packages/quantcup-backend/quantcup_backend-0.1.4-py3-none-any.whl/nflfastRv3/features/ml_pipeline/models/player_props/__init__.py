"""
Player Props Prediction Models

This package contains models for predicting individual player performance metrics.
These are high-value betting markets with significant liquidity.

Categories:
- QB Props: Passing yards, TDs, completions, interceptions
- RB Props: Rushing yards, attempts, TDs, receptions
- WR/TE Props: Receiving yards, receptions, TDs
- Kicker Props: FG made, XP made, total points
- Defense Props: Sacks, interceptions, tackles

Data Requirements:
- Player-level statistics from play-by-play data
- Opponent defensive rankings
- Game script predictions (affects volume)
- Weather conditions (affects passing)
"""

__all__ = [
    'qb_passing_yards',
    'qb_passing_tds',
    'rb_rushing_yards',
    'rb_rushing_tds',
    'wr_receiving_yards',
    'wr_receiving_tds',
    'anytime_td_scorer',
]