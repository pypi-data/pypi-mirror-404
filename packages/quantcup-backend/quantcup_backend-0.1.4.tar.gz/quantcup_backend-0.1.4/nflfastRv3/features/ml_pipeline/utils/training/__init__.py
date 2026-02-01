"""
ML Training Utilities

Utilities for model training, evaluation, and versioning.
Used by orchestrators/model_trainer.py during training pipeline.

Modules:
- ModelFactory: Creates XGBoost/Linear model instances
- ModelVersionManager: Model versioning and selection
- TrainingPreview: Dry-run preview generation
- BaselineEvaluator: Compares models against baselines  
- SeasonPhaseGating: Logic for early/late season model switching
- FeatureSelector: "The Gauntlet" for pruning features
"""

from .model_factory import ModelFactory
from .model_version_manager import ModelVersionManager
from .training_preview import TrainingPreview
from .baseline_evaluator import BaselineEvaluator
from .season_phase_gating import SeasonPhaseGating
from .feature_selector import FeatureSelector

__all__ = [
    'ModelFactory',
    'ModelVersionManager',
    'TrainingPreview',
    'BaselineEvaluator',
    'SeasonPhaseGating',
    'FeatureSelector',
]
