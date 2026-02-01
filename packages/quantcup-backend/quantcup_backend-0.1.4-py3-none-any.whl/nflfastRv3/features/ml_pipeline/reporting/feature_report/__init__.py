"""
Feature Report Module

Backward-compatible facade for feature engineering report generation.

This module provides a factory function for creating feature report generators.
"""

from .generator import FeatureReportGenerator


def create_feature_reporter(logger=None):
    """
    Factory function to create feature report generator.
    
    Provides backward compatibility with original API.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        FeatureReportGenerator: Configured feature reporter
    
    Example:
        >>> reporter = create_feature_reporter(logger)
        >>> report_path = reporter.generate_report(results)
    """
    return FeatureReportGenerator(logger=logger)


__all__ = [
    'FeatureReportGenerator',
    'create_feature_reporter',
]
