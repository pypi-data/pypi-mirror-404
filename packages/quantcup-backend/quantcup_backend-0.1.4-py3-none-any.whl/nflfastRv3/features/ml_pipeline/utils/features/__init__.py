"""
Feature Engineering Utilities

Utilities for building and manipulating features during feature engineering.
Used by feature_sets/* during feature building.

Modules:
- FeaturePatterns: Regex patterns for feature groups
- FeatureSplitter: Logic to split features into linear/tree groups  
- FeatureSynthesis: Logic to create differential/interaction features
- MergeUtils: Safe DataFrame merging with duplicate detection
- shrinkage: Bayesian shrinkage for early-season metrics
"""

from .feature_patterns import FeaturePatterns
from .feature_splitter import FeatureSplitter
from .feature_synthesis import FeatureSynthesis
from .merge_utils import MergeUtils
from .shrinkage import apply_shrinkage, get_league_prior

__all__ = [
    'FeaturePatterns',
    'FeatureSplitter',
    'FeatureSynthesis',
    'MergeUtils',
    'apply_shrinkage',
    'get_league_prior',
]
