"""
Window Optimization Reporting Module

Provides backward-compatible facade for optimization report generation.
"""

from .generator import OptimizationReportGenerator


def create_optimize_reporter(logger=None):
    """
    Factory function to create optimization report generator.
    
    Maintains backward compatibility with original API.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        OptimizationReportGenerator: Configured optimization reporter
    """
    return OptimizationReportGenerator(logger=logger)


__all__ = ['OptimizationReportGenerator', 'create_optimize_reporter']
