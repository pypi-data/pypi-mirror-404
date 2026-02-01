"""
Regression tests for Phase 5 injury features refactoring.

Verifies that the refactored module maintains 100% backward compatibility
with the original injury_features.py API.

Pattern: Golden master testing - verify outputs match expectations
"""

import pytest


def test_backward_compatible_import():
    """Verify original import path still works."""
    # This should work without any changes to existing code
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_features import (
        InjuryFeatures,
        create_injury_features
    )
    
    assert InjuryFeatures is not None
    assert create_injury_features is not None
    assert hasattr(InjuryFeatures, 'build_features')


def test_new_module_import():
    """Verify new module import path works."""
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis import (
        InjuryFeatures,
        create_injury_features
    )
    
    assert InjuryFeatures is not None
    assert create_injury_features is not None
    assert hasattr(InjuryFeatures, 'build_features')


def test_both_imports_are_same_class():
    """Verify both import paths reference the same class (not duplicates)."""
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_features import InjuryFeatures as OldPath
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis import InjuryFeatures as NewPath
    
    # Both should be the exact same class object (not just equivalent classes)
    assert OldPath is NewPath, "Import paths should reference identical class object"


def test_module_structure():
    """Verify new module structure has all expected components."""
    from nflfastRv3.features.ml_pipeline.feature_sets import injury_analysis
    
    # Check submodules exist
    assert hasattr(injury_analysis, 'InjuryFeatures')
    assert hasattr(injury_analysis, 'create_injury_features')
    
    # Check that specialized components can be imported (for advanced users)
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis.data_loaders import InjuryDataLoader
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis.starter_identification import StarterIdentifier
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis.nickel_validation import NickelValidator
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis.impact_calculation import InjuryImpactCalculator
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis.quality_logging import QualityLogger
    
    assert InjuryDataLoader is not None
    assert StarterIdentifier is not None
    assert NickelValidator is not None
    assert InjuryImpactCalculator is not None
    assert QualityLogger is not None


def test_constants_module():
    """Verify constants module has expected values."""
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis.constants import (
        POSITION_WEIGHTS,
        INJURY_STATUS_WEIGHTS,
        INJURY_SEVERITY,
        INJURY_SEVERITY_PATTERNS
    )
    
    # Check key constants exist
    assert 'QB' in POSITION_WEIGHTS
    assert POSITION_WEIGHTS['QB'] == 0.35
    
    assert 'Out' in INJURY_STATUS_WEIGHTS
    assert INJURY_STATUS_WEIGHTS['Out'] == 1.0
    
    assert 'ACL' in INJURY_SEVERITY
    assert INJURY_SEVERITY['ACL'] == 1.0
    
    assert 'Concussion' in INJURY_SEVERITY_PATTERNS
    assert 'concussion' in INJURY_SEVERITY_PATTERNS['Concussion']


def test_class_initialization():
    """Verify InjuryFeatures can be initialized with expected parameters."""
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_features import InjuryFeatures
    
    # Mock dependencies
    class MockDBService:
        pass
    
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg, exc_info=False): pass
    
    db_service = MockDBService()
    logger = MockLogger()
    
    # Test initialization
    injury_features = InjuryFeatures(db_service, logger)
    
    assert injury_features.db_service is db_service
    assert injury_features.logger is logger
    assert hasattr(injury_features, 'data_loader')
    assert hasattr(injury_features, 'starter_id')
    assert hasattr(injury_features, 'nickel')
    assert hasattr(injury_features, 'impact')
    assert hasattr(injury_features, 'quality')


def test_factory_function():
    """Verify create_injury_features factory function works."""
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_features import create_injury_features
    
    class MockDBService:
        pass
    
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg, exc_info=False): pass
    
    db_service = MockDBService()
    logger = MockLogger()
    
    # Test factory
    injury_features = create_injury_features(db_service, logger)
    
    assert injury_features is not None
    assert hasattr(injury_features, 'build_features')


def test_internal_helpers_not_exposed():
    """Verify internal helpers like SeverityClassifier are not exposed in public API."""
    from nflfastRv3.features.ml_pipeline.feature_sets import injury_analysis
    
    # Public API should not include internal classes
    assert not hasattr(injury_analysis, 'SeverityClassifier'), \
        "SeverityClassifier should be internal to impact_calculation module"
    
    # But it should be accessible for advanced usage if needed
    from nflfastRv3.features.ml_pipeline.feature_sets.injury_analysis.impact_calculation import SeverityClassifier
    assert SeverityClassifier is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
