"""
Feature Patterns - Compatibility Shim

This file provides backward compatibility for imports like:
    from nflfastRv3.features.ml_pipeline.utils.feature_patterns import FeaturePatterns

The actual implementation is in utils/features/feature_patterns.py
This shim re-exports it for compatibility with existing imports.
"""

from .features.feature_patterns import FeaturePatterns

__all__ = ['FeaturePatterns']
