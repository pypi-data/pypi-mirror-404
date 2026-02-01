"""
Feature Report - Header Section

Generates report header and metadata.
"""

from datetime import datetime


class HeaderSectionGenerator:
    """
    Generates report header with metadata.
    
    Minimal single-responsibility section generator.
    """
    
    def __init__(self, logger=None):
        """
        Initialize header generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate(self) -> str:
        """
        Generate report header with timestamp.
        
        Returns:
            str: Formatted header section
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""# NFL Feature Engineering Report

**Generated:** {timestamp}

This report documents the feature sets created during the ML feature engineering pipeline.
Each feature set provides specialized transformations and statistics for NFL game prediction.

---"""


__all__ = ['HeaderSectionGenerator']
