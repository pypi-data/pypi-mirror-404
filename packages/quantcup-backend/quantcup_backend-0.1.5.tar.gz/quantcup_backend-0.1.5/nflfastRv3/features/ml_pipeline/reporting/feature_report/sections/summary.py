"""
Feature Report - Executive Summary Section

Generates executive summary with key statistics and build status.
"""

from typing import Dict, Any


class SummarySectionGenerator:
    """
    Generates executive summary section.
    
    Displays high-level feature engineering status and key metrics.
    """
    
    def __init__(self, logger=None):
        """
        Initialize summary generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate(self, results: Dict[str, Any]) -> str:
        """
        Generate executive summary section.
        
        Args:
            results: Feature engineering results dict
        
        Returns:
            str: Formatted executive summary section
        """
        status = results.get('status', 'unknown')
        features_built = results.get('features_built', 0)
        total_features = results.get('total_features', 0)
        total_rows = results.get('total_rows', 0)
        
        # Status indicator
        if status == 'success':
            status_emoji = "✅"
            status_text = "All features built successfully"
        elif status == 'partial':
            status_emoji = "⚠️"
            status_text = "Some features failed to build"
        else:
            status_emoji = "❌"
            status_text = "Feature engineering failed"
        
        success_rate = (100 * features_built / total_features) if total_features > 0 else 0
        
        return f"""## Executive Summary

**Status:** {status_emoji} {status_text}

**Feature Sets Built:** {features_built}/{total_features}  
**Total Rows Generated:** {total_rows:,}

**Key Metrics:**
- Feature sets successfully engineered: {features_built}
- Total data points across all sets: {total_rows:,}
- Success rate: {success_rate:.0f}%"""


__all__ = ['SummarySectionGenerator']
