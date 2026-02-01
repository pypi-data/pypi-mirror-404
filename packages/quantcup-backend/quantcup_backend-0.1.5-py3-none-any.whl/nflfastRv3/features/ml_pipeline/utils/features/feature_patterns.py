"""
Feature Pattern Definitions

Centralized feature pattern configurations for model-specific feature splitting.
Extracted from game_outcome.py to enable reuse across all models (game outcomes, player props, etc.).

Usage:
    from nflfastRv3.features.ml_pipeline.utils.feature_patterns import FeaturePatterns
    
    # Get patterns for game outcome model
    linear_patterns = FeaturePatterns.GAME_OUTCOME_LINEAR
    tree_patterns = FeaturePatterns.GAME_OUTCOME_TREE
    
    # Or use the helper method
    patterns = FeaturePatterns.get_patterns('game_outcome', 'linear')
"""

from typing import List, Dict, Optional


class FeaturePatterns:
    """Feature pattern definitions for different model types."""
    
    # ===== GAME OUTCOME PATTERNS =====
    
    # Linear models (Elastic Net, Logistic) get fundamental metrics
    # These are stable, predictive features based on team performance
    GAME_OUTCOME_LINEAR = [
        r'^rolling_',      # Rolling averages (4g, 8g, 16g)
        r'^recent_',       # Recent form indicators
        r'^epa_',          # EPA metrics
        r'^win_rate_',     # Win rate trends
        r'^point_diff'     # Point differential metrics
    ]
    
    # Tree models (XGBoost) get BOTH team strength AND context (PHASE 1 FIX - 2025-12-13)
    # CRITICAL: XGBoost needs rolling metrics to learn team strength patterns.
    # Without these, XGBoost makes naive predictions based only on stadium/contextual features.
    # Previous config (7 features) → 43.8% accuracy, 93.8% home bias
    # This fix (25+ features) → Expected 58-62% accuracy, balanced predictions
    GAME_OUTCOME_TREE = [
        # SHARED: Team strength signals (enables XGBoost to learn performance patterns)
        r'^rolling_',      # Rolling averages - SHARED with linear (Phase 1 fix)
        r'^recent_',       # Recent form - SHARED with linear (Phase 1 fix)
        r'^epa_',          # EPA metrics - SHARED with linear (Phase 1 fix)
        r'^win_rate_',     # Win rate trends - SHARED with linear (Phase 1 fix)
        r'^point_diff',    # Point differentials - SHARED with linear (Phase 1 fix)
        
        # EXCLUSIVE: Contextual features for nonlinear interaction learning
        r'^interaction_',  # Interaction features (form × context)
        r'^home_rest_',    # Rest days for home team
        r'^away_rest_',    # Rest days for away team
        r'^stadium_',      # Stadium/venue effects
        r'^weather_',      # Weather conditions
        r'^is_',           # Binary flags (is_primetime, is_divisional, etc.)
        r'^h2h_',          # Head-to-head history
        r'^temp_',         # Temperature features
        r'^wind_',         # Wind features
        r'^games_remaining', # Schedule position
        
        # PHASE 2: Multiplicative interactions (XGBoost-specific, 2025-12-13 REVISED)
        r'.*_interaction$',  # Multiplicative interactions (EPA × context)
        r'.*_synergy$',      # Synergy features (venue × form)
        r'.*_index$',        # Indices (consistency, predictability)
        r'.*_amplifier$',    # Amplifier features (from future phases)
        r'.*_intensity$',    # Intensity features (conference_threshold_intensity)
        r'.*_ratio$',        # Ratio features (rest_performance_ratio)
        r'.*_threshold$'     # Threshold features (epa_altitude_threshold)
    ]
    
    # ===== SPREAD PREDICTION PATTERNS =====
    # Similar to game outcome but may emphasize different metrics
    SPREAD_LINEAR = GAME_OUTCOME_LINEAR + [
        r'^spread_line',   # The spread itself
        r'^ats_'           # Against The Spread history
    ]
    
    SPREAD_TREE = GAME_OUTCOME_TREE + [
        r'^line_movement_', # Line movement
        r'^public_betting_' # Public betting %
    ]
    
    # ===== TOTAL POINTS PATTERNS =====
    # Focus on scoring rates, pace, and weather
    TOTAL_LINEAR = [
        r'^rolling_.*_points_',    # Points scored/allowed
        r'^rolling_.*_epa_',       # EPA (highly correlated with scoring)
        r'^pace_',                 # Pace of play
        r'^total_line'             # The total line itself
    ]
    
    TOTAL_TREE = [
        r'^weather_',      # Weather is critical for totals
        r'^stadium_',      # Dome vs Outdoor
        r'^is_primetime',  # Primetime games often go under
        r'^rest_days_',    # Rest impact on defense vs offense
        r'^over_under_rate' # Historical over/under rates
    ]
    
    # ===== MARGIN OF VICTORY PATTERNS (Regression) =====
    MOV_LINEAR = GAME_OUTCOME_LINEAR
    MOV_TREE = GAME_OUTCOME_TREE

    # ===== PLAYER PROP PATTERNS (for future use) =====
    
    # QB Passing Yards Patterns
    QB_VOLUME = [
        r'^targets_',      # Target volume
        r'^attempts_',     # Pass attempts
        r'^snaps_'         # Snap counts
    ]
    
    QB_EFFICIENCY = [
        r'^yards_per_',    # Yards per attempt/completion
        r'^completion_',   # Completion percentage
        r'^success_rate_'  # Success rate metrics
    ]
    
    QB_CONTEXT = [
        r'^opponent_',     # Opponent defense metrics
        r'^weather_',      # Weather conditions
        r'^home_away_',    # Home/away splits
        r'^pressure_'      # Pressure rate
    ]
    
    # RB Rushing Yards Patterns
    RB_VOLUME = [
        r'^carries_',      # Carry volume
        r'^touches_',      # Total touches
        r'^snaps_'         # Snap counts
    ]
    
    RB_EFFICIENCY = [
        r'^yards_per_',    # Yards per carry
        r'^success_rate_', # Success rate
        r'^explosive_'     # Explosive play rate
    ]
    
    RB_CONTEXT = [
        r'^opponent_',     # Opponent run defense
        r'^ol_',           # Offensive line metrics
        r'^game_script_'   # Game script indicators
    ]
    
    # WR Receiving Yards Patterns
    WR_VOLUME = [
        r'^targets_',      # Target volume
        r'^routes_',       # Route participation
        r'^snaps_'         # Snap counts
    ]
    
    WR_EFFICIENCY = [
        r'^yards_per_',    # Yards per target/reception
        r'^catch_rate_',   # Catch rate
        r'^adot_'          # Average depth of target
    ]
    
    WR_CONTEXT = [
        r'^opponent_',     # Opponent coverage
        r'^qb_',           # QB metrics
        r'^coverage_'      # Coverage scheme
    ]
    
    @staticmethod
    def get_patterns(model_type: str, feature_group: str) -> List[str]:
        """
        Get feature patterns for a specific model and group.
        
        Args:
            model_type: Type of model ('game_outcome', 'qb_passing', 'rb_rushing', 'wr_receiving')
            feature_group: Feature group ('linear', 'tree', 'volume', 'efficiency', 'context')
            
        Returns:
            List of regex patterns for the specified model and group
            
        Example:
            >>> patterns = FeaturePatterns.get_patterns('game_outcome', 'linear')
            >>> print(patterns)
            ['^rolling_', '^recent_', '^epa_', '^win_rate_', '^point_diff']
        """
        pattern_map = {
            'game_outcome': {
                'linear': FeaturePatterns.GAME_OUTCOME_LINEAR,
                'tree': FeaturePatterns.GAME_OUTCOME_TREE
            },
            'spread_prediction': {
                'linear': FeaturePatterns.SPREAD_LINEAR,
                'tree': FeaturePatterns.SPREAD_TREE
            },
            'total_points': {
                'linear': FeaturePatterns.TOTAL_LINEAR,
                'tree': FeaturePatterns.TOTAL_TREE
            },
            'margin_of_victory': {
                'linear': FeaturePatterns.MOV_LINEAR,
                'tree': FeaturePatterns.MOV_TREE
            },
            'qb_passing': {
                'volume': FeaturePatterns.QB_VOLUME,
                'efficiency': FeaturePatterns.QB_EFFICIENCY,
                'context': FeaturePatterns.QB_CONTEXT
            },
            'rb_rushing': {
                'volume': FeaturePatterns.RB_VOLUME,
                'efficiency': FeaturePatterns.RB_EFFICIENCY,
                'context': FeaturePatterns.RB_CONTEXT
            },
            'wr_receiving': {
                'volume': FeaturePatterns.WR_VOLUME,
                'efficiency': FeaturePatterns.WR_EFFICIENCY,
                'context': FeaturePatterns.WR_CONTEXT
            }
        }
        
        return pattern_map.get(model_type, {}).get(feature_group, [])
    
    @staticmethod
    def get_all_patterns(model_type: str) -> Dict[str, List[str]]:
        """
        Get all feature pattern groups for a specific model.
        
        Args:
            model_type: Type of model ('game_outcome', 'qb_passing', 'rb_rushing', 'wr_receiving')
            
        Returns:
            Dictionary mapping group names to pattern lists
            
        Example:
            >>> patterns = FeaturePatterns.get_all_patterns('game_outcome')
            >>> print(patterns.keys())
            dict_keys(['linear', 'tree'])
        """
        all_patterns = {
            'game_outcome': {
                'linear': FeaturePatterns.GAME_OUTCOME_LINEAR,
                'tree': FeaturePatterns.GAME_OUTCOME_TREE
            },
            'spread_prediction': {
                'linear': FeaturePatterns.SPREAD_LINEAR,
                'tree': FeaturePatterns.SPREAD_TREE
            },
            'total_points': {
                'linear': FeaturePatterns.TOTAL_LINEAR,
                'tree': FeaturePatterns.TOTAL_TREE
            },
            'margin_of_victory': {
                'linear': FeaturePatterns.MOV_LINEAR,
                'tree': FeaturePatterns.MOV_TREE
            },
            'qb_passing': {
                'volume': FeaturePatterns.QB_VOLUME,
                'efficiency': FeaturePatterns.QB_EFFICIENCY,
                'context': FeaturePatterns.QB_CONTEXT
            },
            'rb_rushing': {
                'volume': FeaturePatterns.RB_VOLUME,
                'efficiency': FeaturePatterns.RB_EFFICIENCY,
                'context': FeaturePatterns.RB_CONTEXT
            },
            'wr_receiving': {
                'volume': FeaturePatterns.WR_VOLUME,
                'efficiency': FeaturePatterns.WR_EFFICIENCY,
                'context': FeaturePatterns.WR_CONTEXT
            }
        }
        
        return all_patterns.get(model_type, {})


__all__ = ['FeaturePatterns']