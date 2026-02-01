"""
ML Pipeline Utilities

Comprehensive utility classes for ML pipeline v2 features, organized by category:

Feature Engineering:
- FeaturePatterns: Regex patterns for feature groups
- FeatureRegistry: Master list of active/inactive features
- FeatureSplitter: Logic to split features into linear/tree groups
- FeatureSynthesis: Logic to create differential/interaction features
- FeatureSelector: "The Gauntlet" for pruning features
- FeatureDiagnostics: Correlation and stability analysis
- FeatureAvailabilityChecker: Feature availability checking and auto-building

Model Management:
- ModelFactory: Creates XGBoost/Linear model instances
- ModelVersionManager: Model versioning and selection
- TrainingPreview: Dry-run preview generation

Validation:
- BaselineEvaluator: Compares models against baselines
- SeasonPhaseGating: Logic for early/late season model switching

Data Utilities:
- MergeUtils: Safe merging logic
- apply_shrinkage: Bayesian shrinkage function
- get_league_prior: League prior calculation

Ensemble Models (re-exported from models.base for backward compatibility):
- BaseEnsemble: Abstract base class for ensemble models
- EnsembleClassifier: Generic ensemble classifier with season gating
- EnsembleRegressor: Generic ensemble regressor with season gating

Note: TemporalValidator moved to nflfastRv3.shared for cross-feature reuse
Note: Ensemble models moved to models/base/ but still exported here for compatibility
"""

# Feature Engineering (from features/ subdirectory)
from .features.feature_patterns import FeaturePatterns
from .features.feature_splitter import FeatureSplitter
from .features.feature_synthesis import FeatureSynthesis
from .features.merge_utils import MergeUtils
from .features.shrinkage import apply_shrinkage, get_league_prior

# Model Management (from training/ subdirectory)
from .training.model_factory import ModelFactory
from .training.model_version_manager import ModelVersionManager
from .training.training_preview import TrainingPreview

# Validation (from training/ subdirectory)
from .training.baseline_evaluator import BaselineEvaluator
from .training.season_phase_gating import SeasonPhaseGating
from .training.feature_selector import FeatureSelector

# Shared utilities (still at root level)
from .feature_checker import FeatureAvailabilityChecker
from .feature_diagnostics import FeatureDiagnostics
from .feature_registry import FeatureRegistry


# Ensemble Models (moved to models/base/)
from ..models.base.ensemble import BaseEnsemble, EnsembleClassifier, EnsembleRegressor

__all__ = [
    # Feature Engineering
    'FeaturePatterns',
    'FeatureRegistry',
    'FeatureSplitter',
    'FeatureSynthesis',
    'FeatureSelector',
    'FeatureDiagnostics',
    'FeatureAvailabilityChecker',
    
    # Model Management
    'ModelFactory',
    'ModelVersionManager',
    'TrainingPreview',
    
    # Validation
    'BaselineEvaluator',
    'SeasonPhaseGating',
    
    # Data Utilities
    'MergeUtils',
    'apply_shrinkage',
    'get_league_prior',
    
    # Ensemble Models
    'BaseEnsemble',
    'EnsembleClassifier',
    'EnsembleRegressor',
]