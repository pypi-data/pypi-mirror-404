"""
Backtest Report Module

Backward-compatible facade for the refactored backtest report generator.

Public API:
- BacktestReportGenerator: Main class (delegates to generator.py)
- create_backtest_reporter: Factory function
"""

from .generator import BacktestReportGenerator as _BacktestReportGenerator


class BacktestReportGenerator(_BacktestReportGenerator):
    """
    Backward-compatible facade for BacktestReportGenerator.
    
    Delegates to the refactored generator while maintaining
    the original public API.
    """
    pass


def create_backtest_reporter(logger=None):
    """
    Factory function to create backtest report generator.
    
    Matches pattern from create_report_generator()
    
    Args:
        logger: Optional logger instance
        
    Returns:
        BacktestReportGenerator: Configured backtest reporter
    """
    return BacktestReportGenerator(logger=logger)


__all__ = ['BacktestReportGenerator', 'create_backtest_reporter']
