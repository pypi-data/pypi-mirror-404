"""
Training Mode Configuration

Lightweight metadata-only config defining available training modes.
Logic for mode determination lives in main.py (train_model_only).

Pattern: Configuration data only (0 complexity points)
"""

# Training mode metadata
TRAINING_MODES = {
    'production': {
        'name': 'Production Mode',
        'description': 'Relative training window based on years before test period',
        'required_args': ['train_years'],
        'optional_args': ['test_year', 'test_week'],
        'example': '--train-years 3 --test-year 2024',
        'use_cases': [
            'Production model training',
            'Automated training workflows',
            'Consistent N-year lookback',
            'Always uses most recent data'
        ]
    }
}

# Validation constraints
VALIDATION_CONSTRAINTS = {
    'test_year': {
        'min': 1999,
        'max_offset_from_now': 1,  # Allow next year
        'description': 'Valid NFL season year'
    },
    'test_week': {
        'min': 1,
        'max': 22,
        'description': 'NFL week including playoffs'
    },
    'train_years': {
        'min': 1,
        'recommended_min': 3,
        'description': 'Number of years to train on'
    }
}

# Mode priority order (used in main.py for determination)
MODE_PRIORITY = ['production']


def get_mode_info(mode: str) -> dict:
    """
    Get metadata for a specific training mode.
    
    Args:
        mode: Mode name ('production')
        
    Returns:
        dict: Mode metadata or empty dict if mode not found
    """
    return TRAINING_MODES.get(mode, {})


def get_all_modes() -> list:
    """Get list of all available mode names in priority order."""
    return MODE_PRIORITY.copy()


def get_validation_constraint(constraint_name: str) -> dict:
    """
    Get validation constraints for a specific parameter.
    
    Args:
        constraint_name: Parameter name ('test_year', 'test_week', 'train_years')
        
    Returns:
        dict: Constraint metadata or empty dict if not found
    """
    return VALIDATION_CONSTRAINTS.get(constraint_name, {})


__all__ = [
    'TRAINING_MODES',
    'VALIDATION_CONSTRAINTS',
    'MODE_PRIORITY',
    'get_mode_info',
    'get_all_modes',
    'get_validation_constraint'
]