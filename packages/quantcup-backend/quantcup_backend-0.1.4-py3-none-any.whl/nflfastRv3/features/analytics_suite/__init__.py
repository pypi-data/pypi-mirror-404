"""
Analytics Suite - NFL Data Analysis Capabilities

Pattern: Minimum Viable Decoupling
Complexity: 2 points average across modules
Layer: 2 (Implementation - calls infrastructure directly)

This module provides comprehensive analytics capabilities for NFL data including:
- Exploratory data analysis
- Feature analysis and quality assessment  
- Multicollinearity detection
- Team performance analysis
- Seasonal trend analysis

All components follow the V3 clean architecture patterns with:
- Maximum 3 layers depth
- 5 complexity points budget per module
- Dependency injection throughout
- Direct infrastructure calls (no complex patterns)

Example Usage:
    from nflfastRv3.features.analytics_suite import create_analytics_suite
    
    analytics = create_analytics_suite()
    
    # Run exploratory analysis
    results = analytics.process('exploratory')
    
    # Run feature analysis
    results = analytics.process('feature_analysis')
"""

from .main import AnalyticsImpl, create_analytics_suite
from .exploratory import ExploratoryAnalysisImpl, create_exploratory_analysis
from .feature_analysis import FeatureAnalysisImpl, create_feature_analysis
from .player_analytics import PlayerAnalyticsImpl, create_player_analytics



__all__ = [
    'AnalyticsImpl',
    'ExploratoryAnalysisImpl',
    'FeatureAnalysisImpl',
    'PlayerAnalyticsImpl',
    'create_analytics_suite',
    'create_exploratory_analysis',
    'create_feature_analysis',
    'create_player_analytics',
]
