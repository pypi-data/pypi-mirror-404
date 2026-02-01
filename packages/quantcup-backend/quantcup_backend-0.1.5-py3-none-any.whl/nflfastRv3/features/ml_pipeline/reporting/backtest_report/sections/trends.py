"""
Trends Section Generator for Backtest Reports

Generates performance trends and consistency analysis.
"""

import numpy as np
from typing import Dict, Any, List

from ...common import get_consistency_rating


class TrendsSectionGenerator:
    """
    Generates performance trends and consistency analysis sections.
    
    Responsibilities:
    - Performance trends over time
    - Consistency analysis with NFL-specific ratings
    """
    
    def __init__(self, logger=None):
        """
        Initialize trends section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_performance_trends(self, backtest_results: List[Dict[str, Any]]) -> str:
        """
        Analyze performance trends over time.
        
        Args:
            backtest_results: List of training results from each iteration
            
        Returns:
            str: Markdown formatted performance trends analysis
        """
        if len(backtest_results) < 3:
            return """## Performance Trends

Insufficient data for trend analysis (need at least 3 years)."""
        
        # Extract data
        years = [r.get('test_year', 0) for r in backtest_results]
        accuracies = [r['metrics'].get('accuracy', 0) for r in backtest_results]
        
        # Simple trend analysis
        first_half = accuracies[:len(accuracies)//2]
        second_half = accuracies[len(accuracies)//2:]
        
        trend_direction = "improving" if np.mean(second_half) > np.mean(first_half) else "declining"
        
        # Identify best and worst years
        best_idx = np.argmax(accuracies)
        worst_idx = np.argmin(accuracies)
        
        accuracy_range = float(max(accuracies) - min(accuracies))
        
        # Interpretation
        if accuracy_range < 0.10:
            interpretation = "Model shows stable performance across different years."
        else:
            interpretation = "Model performance varies significantly by year - investigate anomalies."
        
        return f"""## Performance Trends

**Trend Analysis:**
- **Direction:** Performance appears to be {trend_direction} over time
- **First Half Average:** {np.mean(first_half):.1%}
- **Second Half Average:** {np.mean(second_half):.1%}

**Extremes:**
- **Best Year:** {years[best_idx]} with {accuracies[best_idx]:.1%} accuracy
- **Worst Year:** {years[worst_idx]} with {accuracies[worst_idx]:.1%} accuracy
- **Range:** {accuracy_range:.1%} accuracy spread

**Interpretation:** {interpretation}"""
    
    def generate_consistency_analysis(self, backtest_results: List[Dict[str, Any]]) -> str:
        """
        Analyze model consistency.
        
        Args:
            backtest_results: List of training results from each iteration
            
        Returns:
            str: Markdown formatted consistency analysis
        """
        if not backtest_results:
            return """## Consistency Analysis

No results to analyze."""
        
        accuracies = [r['metrics'].get('accuracy', 0) for r in backtest_results]
        std_dev = float(np.std(accuracies))
        mean_acc = float(np.mean(accuracies))
        cv = std_dev / mean_acc if mean_acc > 0 else 0
        
        # Get consistency rating from config
        level, emoji, description = get_consistency_rating(std_dev)
        
        # Count years within ±5%
        years_within_5pct = sum(1 for a in accuracies if abs(a - mean_acc) < 0.05)
        
        # Assessment
        if std_dev < 0.05:
            assessment = "This training window provides reliable predictions across different years."
        else:
            assessment = "Consider investigating factors causing performance variation."
        
        return f"""## Consistency Analysis

**Consistency Rating:** {emoji} {level} - {description}

**Statistics:**
- **Standard Deviation:** {std_dev:.1%}
- **Coefficient of Variation:** {cv:.1%}
- **Years Within ±5%:** {years_within_5pct}/{len(backtest_results)}

**Assessment:** {assessment}"""
    
    def generate(self, backtest_results: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generate complete trends section.
        
        Args:
            backtest_results: List of training results
            kwargs: Additional arguments (ignored)
            
        Returns:
            str: Complete trends section
        """
        sections = [
            self.generate_performance_trends(backtest_results),
            self.generate_consistency_analysis(backtest_results),
        ]
        
        return '\n\n'.join(sections)


__all__ = ['TrendsSectionGenerator']
