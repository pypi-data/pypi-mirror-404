"""
Season Phase Gating Utility

Provides variance-based gating logic for NFL game predictions based on season phase.
Addresses the early-season instability problem where recent form is unreliable.

Key Concepts:
- Early Season (Weeks 1-4): Trust only long-term priors, not recent form
- Late Season (Weeks 6+): Trust everything including recent form
- Unstable Teams: Extended gating through Week 8 for high-variance teams

This utility enables models to adapt their feature sets based on:
1. Week number (temporal stability)
2. Team stability (variance-based team classification)
3. Matchup stability (combined home/away stability)

Usage:
    from nflfastRv3.features.ml_pipeline.utils.season_phase_gating import SeasonPhaseGating
    
    # Get stability score for a team
    stability = SeasonPhaseGating.get_stability_score('ATL', week=3)
    
    # Determine which model to use
    use_early = SeasonPhaseGating.should_use_early_model(
        week=3, home_team='ATL', away_team='KC'
    )
    
    # Get feature patterns for a week
    patterns = SeasonPhaseGating.get_feature_patterns(week=3)
"""

import re
from typing import List, Set, Optional
import numpy as np
import pandas as pd


class SeasonPhaseGating:
    """
    Season phase gating logic for NFL predictions.
    
    Provides methods to determine which features and models to use based on
    season phase and team stability characteristics.
    """
    
    # Early Season (Weeks 1-4): Trust only priors
    EARLY_SEASON_PATTERNS = [
        r'^rolling_16g_',  # Long-term priors
        r'^stadium_(?!home_win_rate)',  # Fixed attributes (exclude raw win rate to prevent bias)
        r'^is_',           # Fixed attributes
        r'^h2h_'           # Historical matchup
    ]
    
    # Late Season (Weeks 6+): Trust everything
    LATE_SEASON_PATTERNS = [
        r'.*'  # All features allowed
    ]
    
    # Safe Priors (Fallback features if all context features are toxic)
    # These are long-term rolling metrics that are generally stable and predictive.
    SAFE_PRIORS = [
        'rolling_16g_epa_offense_diff',
        'rolling_16g_epa_defense_diff',
        'rolling_16g_point_diff_diff',
        'rolling_16g_win_rate_diff'
    ]
    
    # Unstable Teams (Identified via Variance Analysis 2022-2024)
    # These teams have < 40% accuracy in Weeks 1-5
    UNSTABLE_TEAMS: Set[str] = {'ATL', 'PIT', 'ARI', 'IND', 'CLE'}
    
    # Week thresholds
    EARLY_SEASON_CUTOFF = 4  # Weeks 1-4 are always early
    UNSTABLE_TEAM_CUTOFF = 8  # Unstable teams use early model through Week 8
    
    @staticmethod
    def get_stability_score(team: str, week: int) -> float:
        """
        Get stability score for a team at a given week.
        
        Args:
            team: Team abbreviation (e.g., 'ATL', 'KC')
            week: Week number (1-18)
            
        Returns:
            float: 0.0 (Unstable) to 1.0 (Stable)
        """
        # Late season is always stable
        if week > SeasonPhaseGating.UNSTABLE_TEAM_CUTOFF:
            return 1.0
            
        # Early season check
        if team in SeasonPhaseGating.UNSTABLE_TEAMS:
            return 0.0
            
        # Default to stable for others after Week 4
        if week > SeasonPhaseGating.EARLY_SEASON_CUTOFF:
            return 1.0
            
        # Week 1-4 is unstable for everyone by default
        return 0.0
    
    @staticmethod
    def should_use_early_model(week: int, home_team: str, away_team: str) -> bool:
        """
        Determine if early model (priors) should be used for a matchup.
        
        Logic:
        - Week 1-4: Always use early model
        - Week 5-8: Use early model if either team is unstable
        - Week 9+: Always use late model
        
        Args:
            week: Week number (1-18)
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            
        Returns:
            bool: True if early model should be used, False for late model
        """
        # Base Gate: Week 1-4 is always Early
        if week <= SeasonPhaseGating.EARLY_SEASON_CUTOFF:
            return True
            
        # Extended Gate: Weeks 5-8 for Unstable Teams
        if week <= SeasonPhaseGating.UNSTABLE_TEAM_CUTOFF:
            if home_team in SeasonPhaseGating.UNSTABLE_TEAMS or away_team in SeasonPhaseGating.UNSTABLE_TEAMS:
                return True
        
        # Otherwise Late
        return False
    
    @staticmethod
    def get_feature_patterns(week: int) -> List[str]:
        """
        Get allowed feature patterns for a given week.
        
        Args:
            week: Week number (1-18)
            
        Returns:
            List of regex patterns for allowed features
        """
        if week <= SeasonPhaseGating.EARLY_SEASON_CUTOFF:
            return SeasonPhaseGating.EARLY_SEASON_PATTERNS
        else:
            return SeasonPhaseGating.LATE_SEASON_PATTERNS
    
    @staticmethod
    def filter_features_by_week(
        features: List[str],
        week: int
    ) -> List[str]:
        """
        Filter feature list based on week number.
        
        Args:
            features: List of feature names
            week: Week number (1-18)
            
        Returns:
            Filtered list of features allowed for this week
        """
        patterns = SeasonPhaseGating.get_feature_patterns(week)
        
        # If all features allowed (late season), return as-is
        if patterns == SeasonPhaseGating.LATE_SEASON_PATTERNS:
            return features
        
        # Filter features by patterns
        filtered = []
        for feature in features:
            if any(re.match(pattern, feature) for pattern in patterns):
                filtered.append(feature)
        
        return filtered
    
    @staticmethod
    def get_gating_mask(
        weeks: np.ndarray,
        home_teams: np.ndarray,
        away_teams: np.ndarray
    ) -> np.ndarray:
        """
        Vectorized gating decision for batch predictions.
        
        Args:
            weeks: Array of week numbers
            home_teams: Array of home team abbreviations
            away_teams: Array of away team abbreviations
            
        Returns:
            Boolean array: True = use early model, False = use late model
        """
        n_samples = len(weeks)
        use_early = np.zeros(n_samples, dtype=bool)
        
        unstable_set = SeasonPhaseGating.UNSTABLE_TEAMS
        
        for i in range(n_samples):
            week = weeks[i]
            home = home_teams[i]
            away = away_teams[i]
            
            # Base Gate: Week 1-4 is always Early
            if week <= SeasonPhaseGating.EARLY_SEASON_CUTOFF:
                use_early[i] = True
                continue
                
            # Extended Gate: Weeks 5-8 for Unstable Teams
            if week <= SeasonPhaseGating.UNSTABLE_TEAM_CUTOFF:
                if home in unstable_set or away in unstable_set:
                    use_early[i] = True
                    continue
            
            # Otherwise Late
            use_early[i] = False
        
        return use_early
    
    @staticmethod
    def identify_early_features(
        all_features: List[str]
    ) -> List[str]:
        """
        Identify which features should be used in early season model.
        
        Args:
            all_features: List of all available feature names
            
        Returns:
            List of features allowed in early season
        """
        early_features = []
        for col in all_features:
            if any(re.match(pattern, col) for pattern in SeasonPhaseGating.EARLY_SEASON_PATTERNS):
                early_features.append(col)
        
        # Fallback if no early features found
        if not early_features:
            early_features = all_features
        
        return early_features
    
    @staticmethod
    def get_safe_priors(available_features: List[str]) -> List[str]:
        """
        Get safe prior features that are available in the dataset.
        
        Safe priors are long-term rolling metrics that are stable and predictive,
        used as a fallback when all context features are toxic.
        
        Args:
            available_features: List of features available in the dataset
            
        Returns:
            List of safe prior features that exist in available_features
        """
        return [
            prior for prior in SeasonPhaseGating.SAFE_PRIORS
            if prior in available_features
        ]


__all__ = ['SeasonPhaseGating']