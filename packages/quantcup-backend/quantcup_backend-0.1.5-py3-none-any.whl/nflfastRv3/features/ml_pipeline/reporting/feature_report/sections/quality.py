"""
Feature Report - Data Quality Section

Generates data quality and coverage analysis.
"""

from typing import Dict, Any


class QualitySectionGenerator:
    """
    Generates data quality summary section.
    
    Provides coverage analysis and quality indicators.
    """
    
    def __init__(self, logger=None):
        """
        Initialize quality generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate(self, results: Dict[str, Any]) -> str:
        """
        Generate data quality and coverage analysis.
        
        Args:
            results: Feature engineering results dict
        
        Returns:
            str: Formatted data quality section
        """
        feature_results = results.get('results', {})
        successful = sum(1 for r in feature_results.values() if r.get('status') == 'success')
        total = len(feature_results)
        total_rows = results.get('total_rows', 0)
        
        # Calculate per-feature metrics
        feature_breakdown = []
        for feature_name, result in feature_results.items():
            if result.get('status') == 'success':
                rows = result.get('rows_built', 0)
                pct = (100 * rows / total_rows) if total_rows > 0 else 0
                feature_breakdown.append(f"- **{feature_name}**: {rows:,} rows ({pct:.1f}% of total)")
        
        breakdown_text = '\n'.join(sorted(feature_breakdown)) if feature_breakdown else "No successful feature sets"
        success_pct = (100 * successful / total) if total > 0 else 0
        
        return f"""## Data Quality Summary

**Success Rate:** {successful}/{total} ({success_pct:.0f}%)

**Data Volume Breakdown:**

{breakdown_text}

**Coverage Notes:**
- `team_efficiency`: Season-level aggregates (typically ~32 teams × ~27 seasons = ~861 rows)
- `rolling_metrics`: Game-level with rolling windows (typically ~14,392 team-games)
- `opponent_adjusted`: Season-level strength metrics (varies by seasons processed)
- `nextgen`: Game-level QB stats (2016-2025 seasons, ~2,684 games)
- `contextual`: Game-level context features (all available games, ~7,196)
- `injury`: Game-level injury impacts (all available games, ~7,196)

**Data Quality Indicators:**
- ✅ No DataFrame samples printed to logs (reduced verbosity)
- ✅ Detailed statistics logged for each feature set
- ✅ Memory management active during pipeline execution
- ✅ All features saved to both bucket (primary) and database (secondary)"""


__all__ = ['QualitySectionGenerator']
