"""
Models Module - Registry for ML Models

Available models:
- game_outcome: Binary classification for game winner prediction
- spread_prediction: Binary classification for spread covering prediction  
- total_points: Binary classification for over/under prediction

Pattern: Minimum Viable Decoupling (Registry pattern)
Complexity: 1 point (module organization)
Layer: 2 (Implementation)
"""

from .game_lines.game_outcome import GameOutcomeModel, create_game_outcome_model
from .game_lines.spread_prediction import SpreadPredictionModel, create_spread_prediction_model
from .game_lines.total_points import TotalPointsModel, create_total_points_model


# ============================================================================
# MODEL REGISTRY - Lightweight mapping for CLI and orchestration
# ============================================================================

MODEL_REGISTRY = {
    'game_outcome': {
        'factory': create_game_outcome_model,
        'class': GameOutcomeModel,
        'target': 'home_team_won',
        'description': 'Predict game winner (home vs away)',
        'status': 'production',  # production, beta, development
        'table': 'game_outcome_predictions_v1'
    },
    'spread_prediction': {
        'factory': create_spread_prediction_model,
        'class': SpreadPredictionModel,
        'target': 'home_covers_spread',
        'description': 'Predict if home team covers spread',
        'status': 'beta',
        'table': 'spread_predictions_v1'
    },
    'total_points': {
        'factory': create_total_points_model,
        'class': TotalPointsModel,
        'target': 'over_total',
        'description': 'Predict if game total goes over the line',
        'status': 'beta',
        'table': 'total_predictions_v1'
    }
}


def get_available_models():
    """Get list of all available model names."""
    return list(MODEL_REGISTRY.keys())


def get_model_info(model_name):
    """
    Get metadata for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        dict: Model metadata or None if not found
    """
    return MODEL_REGISTRY.get(model_name)


def validate_models(model_names):
    """
    Validate that model names are valid.
    
    Args:
        model_names: List of model names to validate
        
    Returns:
        Tuple of (valid_models, invalid_models)
    """
    available = set(MODEL_REGISTRY.keys())
    requested = set(model_names)
    
    valid = list(requested & available)
    invalid = list(requested - available)
    
    return valid, invalid


__all__ = [
    # Game outcome model
    'GameOutcomeModel',
    'create_game_outcome_model',
    
    # Spread prediction model
    'SpreadPredictionModel',
    'create_spread_prediction_model',
    
    # Total points model
    'TotalPointsModel',
    'create_total_points_model',
    
    # Model registry
    'MODEL_REGISTRY',
    'get_available_models',
    'get_model_info',
    'validate_models'
]