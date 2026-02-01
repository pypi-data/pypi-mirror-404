"""
Shared utility functions for feature analysis.

Extracted from analyzers.py - provides feature categorization and
registry interaction helpers.
"""


def categorize_feature(feature_name):
    """
    Categorize feature by name pattern.
    
    Args:
        feature_name: Feature name string
        
    Returns:
        str: Category name
        
    Categories:
        - Composite/Interaction: Combined features and advantages
        - Rolling Differentials: Rolling window statistics
        - Trending: Trend indicators
        - Contextual - Rest: Rest days
        - Contextual - Weather: Weather conditions
        - Contextual - Season: Season timing
        - Contextual - Stadium: Venue factors
        - Contextual - Division: Division/conference
        - Injury Features: Injury impacts
        - NextGen QB: QB-specific metrics
        - Efficiency Metrics: EPA, red zone, etc.
        - Recent Form: Recent performance
        - Other: Uncategorized
    """
    feature_lower = feature_name.lower()
    
    if 'interaction_' in feature_lower or feature_name in ['epa_advantage_4game', 'epa_advantage_8game', 'win_rate_advantage', 'momentum_advantage']:
        return 'Composite/Interaction'
    elif 'rolling_' in feature_lower:
        return 'Rolling Differentials'
    elif 'trending' in feature_lower:
        return 'Trending'
    elif 'rest' in feature_lower:
        return 'Contextual - Rest'
    elif any(w in feature_lower for w in ['weather', 'temp', 'precipitation', 'wind']):
        return 'Contextual - Weather'
    elif 'season' in feature_lower or 'games_remaining' in feature_lower:
        return 'Contextual - Season'
    elif any(w in feature_lower for w in ['stadium', 'dome', 'altitude', 'site']):
        return 'Contextual - Stadium'
    elif 'division' in feature_lower or 'conference' in feature_lower:
        return 'Contextual - Division'
    elif 'injury' in feature_lower or 'qb_available' in feature_lower or 'starter_injuries' in feature_lower:
        return 'Injury Features'
    elif 'qb_' in feature_lower:
        return 'NextGen QB'
    elif any(w in feature_lower for w in ['epa', 'efficiency', 'red_zone', 'third_down']):
        return 'Efficiency Metrics'
    elif 'recent_' in feature_lower:
        return 'Recent Form'
    else:
        return 'Other'


def get_registry_feature_reasons():
    """
    Extract exclusion reasons from FeatureRegistry using enhanced metadata.
    
    Returns:
        dict: Mapping of feature names to exclusion reasons
        
    Example:
        >>> reasons = get_registry_feature_reasons()
        >>> reasons['feature_name']
        'Low correlation (correlation: -0.002) [Tested: 2024-01-15]'
    """
    try:
        from nflfastRv3.features.ml_pipeline.utils.feature_registry import FeatureRegistry
        
        # Use new enhanced metadata methods
        reasons = {}
        disabled_features = FeatureRegistry.get_disabled_features()
        
        for feature_name, metadata in disabled_features.items():
            if isinstance(metadata, dict):
                # Enhanced format - extract reason and additional context
                reason = metadata.get('disabled_reason', 'No reason documented')
                
                # Add correlation info if available
                if metadata.get('tested_correlation') is not None:
                    reason += f" (correlation: {metadata['tested_correlation']:+.3f})"
                
                # Add test date if available
                if metadata.get('disabled_date'):
                    reason += f" [Tested: {metadata['disabled_date']}]"
                
                reasons[feature_name] = reason
            else:
                # Legacy format or simple boolean
                reasons[feature_name] = 'No reason documented'
        
        return reasons
    except Exception:
        return {}


__all__ = [
    'categorize_feature',
    'get_registry_feature_reasons',
]
