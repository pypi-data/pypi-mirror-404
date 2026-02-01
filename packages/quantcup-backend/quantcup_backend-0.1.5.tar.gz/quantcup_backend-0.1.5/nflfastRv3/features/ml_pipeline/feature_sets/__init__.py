"""
Feature Sets Module - V3 Implementation

Pattern: Minimum Viable Decoupling
Complexity: 1 point (module organization)
Layer: 2 (Implementation)

Feature engineering modules for ML pipeline:
- team_efficiency: EPA calculations, red zone metrics, turnover rates
- rolling_metrics: Time-series features, moving averages
- opponent_adjusted: Strength-of-schedule adjustments
- contextual_features: Game context, rest days, division games, stadium advantage, weather, playoff implications
- injury_features: Position-weighted injury impact, starter availability (Phase 3)
- odds_features: Market consensus probabilities from betting lines (Phase 3 CLV)

Migrated from nflfastRv2 with V3 clean architecture patterns.
All modules follow REFACTORING_SPECS.md compliance.
"""

from .team_efficiency import TeamEfficiencyFeatures, create_team_efficiency_features
from .rolling_metrics import RollingMetricsFeatures, create_rolling_metrics_features
from .opponent_adjusted import OpponentAdjustedFeatures, create_opponent_adjusted_features
from .contextual_features import ContextualFeatures, create_contextual_features
from .nextgen_features import NextGenFeatures, create_nextgen_features
from .injury_features import InjuryFeatures, create_injury_features
from .player_availability_features import PlayerAvailabilityFeatures, create_player_availability_features
from .odds_features import OddsFeatures, create_odds_features
from .odds_features_game import OddsGameFeatures, create_odds_game_features
from .weather_features import WeatherFeatures, create_weather_features


# ============================================================================
# FEATURE REGISTRY - Lightweight mapping for CLI and orchestration
# ============================================================================

FEATURE_REGISTRY = {
    'team_efficiency': {
        'factory': create_team_efficiency_features,
        'table': 'team_efficiency_v1',
        'description': 'EPA calculations, red zone metrics, turnover rates',
        'phase': 'baseline'
    },
    'rolling_metrics': {
        'factory': create_rolling_metrics_features,
        'table': 'rolling_metrics_v1',
        'description': 'Time-series features, moving averages, momentum',
        'phase': 'baseline'
    },
    'opponent_adjusted': {
        'factory': create_opponent_adjusted_features,
        'table': 'team_opponent_adjusted_v1',
        'description': 'Strength-of-schedule adjustments',
        'phase': 'baseline'
    },
    'nextgen': {
        'factory': create_nextgen_features,
        'table': 'nextgen_features_v1',
        'description': 'QB performance metrics from NextGen Stats',
        'phase': 'phase0'
    },
    'contextual': {
        'factory': create_contextual_features,
        'table': 'contextual_features_v1',
        'description': 'Rest days, division games, stadium advantage, weather',
        'phase': 'phase1-2'
    },
    'injury': {
        'factory': create_injury_features,
        'table': 'injury_features_v1',
        'description': 'Position-weighted injury impact, starter availability (DEPRECATED - use player_availability)',
        'phase': 'phase3'
    },
    'player_availability': {
        'factory': create_player_availability_features,
        'table': 'player_availability_v1',
        'description': 'Unified player availability from warehouse (injuries, IR, suspensions, cuts)',
        'phase': 'phase3'
    },
    #odds build time ~ 4 mins
    'odds': {
        'factory': create_odds_features,
        'table': 'odds_features_v1',
        'description': 'Market consensus probabilities from betting lines (play-by-play)',
        'phase': 'phase3-clv'
    },
    'odds_game': {
        'factory': create_odds_game_features,
        'table': 'odds_features_game_v1',
        'description': 'Game-level aggregated odds for CLV/ROI reporting',
        'phase': 'phase3-clv-reporting'
    },
    'weather': {
        'factory': create_weather_features,
        'table': 'weather_features_v1',
        'description': 'Weather impact (temp, wind, precip keywords) - V1 observables only',
        'phase': 'phase2-weather'
    }
}


def get_available_feature_sets():
    """Get list of all available feature set names."""
    return list(FEATURE_REGISTRY.keys())


def get_feature_info(feature_set_name):
    """Get metadata for a specific feature set."""
    return FEATURE_REGISTRY.get(feature_set_name)


def validate_feature_sets(feature_set_names):
    """
    Validate that feature set names are valid.
    
    Args:
        feature_set_names: List of feature set names to validate
        
    Returns:
        Tuple of (valid_sets, invalid_sets)
    """
    available = set(FEATURE_REGISTRY.keys())
    requested = set(feature_set_names)
    
    valid = list(requested & available)
    invalid = list(requested - available)
    
    return valid, invalid


__all__ = [
    # Team efficiency features
    'TeamEfficiencyFeatures',
    'create_team_efficiency_features',
    
    # Rolling metrics features
    'RollingMetricsFeatures',
    'create_rolling_metrics_features',
    
    # Opponent adjusted features
    'OpponentAdjustedFeatures',
    'create_opponent_adjusted_features',
    
    # NextGen QB features (Phase 0)
    'NextGenFeatures',
    'create_nextgen_features',
    
    # Contextual features (Phase 1 & 2)
    'ContextualFeatures',
    'create_contextual_features',
    
    # Injury features (Phase 3 - DEPRECATED)
    'InjuryFeatures',
    'create_injury_features',
    
    # Player availability features (Phase 3 - replaces injury)
    'PlayerAvailabilityFeatures',
    'create_player_availability_features',
    
    # Odds features (Phase 3 CLV)
    'OddsFeatures',
    'create_odds_features',
    
    # Odds game features (Phase 3 CLV Reporting)
    'OddsGameFeatures',
    'create_odds_game_features',
    
    # Weather features (Phase 2)
    'WeatherFeatures',
    'create_weather_features',
    
    # Feature registry
    'FEATURE_REGISTRY',
    'get_available_feature_sets',
    'get_feature_info',
    'validate_feature_sets'
]
