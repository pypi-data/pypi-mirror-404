"""
⚠️ DEPRECATED: Use player_availability_features.py instead

Injury Impact Features - Player Availability and Depth Chart Analysis

**DEPRECATION NOTICE (2026-01-25):**
This module is DEPRECATED and will be removed in a future release.
Use `player_availability_features.py` instead, which:
- Uses warehouse/player_availability table (single source of truth)
- Correctly handles all unavailability types (injuries, IR, suspensions, cuts)
- Has simpler, cleaner architecture (no complex multi-source merges)
- Fixes bugs (e.g., IR players incorrectly showing as available)

Migration Guide:
OLD:
    from .injury_features import InjuryFeatures
    features = InjuryFeatures(logger=logger)
    df = features.calculate(games, depth_chart, injuries, snap_counts)

NEW:
    from .player_availability_features import PlayerAvailabilityFeatureCalculator
    calculator = PlayerAvailabilityFeatureCalculator(logger=logger)
    df = calculator.calculate_features(games, player_availability)

See: nflfastRv3/features/data_pipeline/transformations/warehouse_player_availability.py
Test: scripts/test_player_availability_features.py

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

Features:
- Position-weighted injury impact scores
- Starter availability indicators
- Depth chart quality metrics

Based on FEATURE_ENHANCEMENT_PLAN.md Phase 3 implementation.
Follows same pattern as RollingMetricsFeatures and ContextualFeatures.

NOTE: This module has been refactored into injury_analysis/ (Phase 5 - 2026-01-24)
All implementation logic is now in the self-contained injury_analysis module.
This file maintains backward compatibility by re-exporting the public API.
"""

import warnings

# Show deprecation warning on import
warnings.warn(
    "injury_features.py is deprecated. Use player_availability_features.py instead. "
    "See docstring for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export public API from refactored injury_analysis module
from .injury_analysis import (
    InjuryFeatures,
    create_injury_features
)

__all__ = ['InjuryFeatures', 'create_injury_features']
