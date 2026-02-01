"""
Results Section Generator for Backtest Reports

Generates year-by-year results table.
"""

from typing import Dict, Any, List

from ...common import get_performance_rating


class ResultsSectionGenerator:
    """
    Generates year-by-year results table for backtest reports.
    
    Responsibilities:
    - Year-by-year performance breakdown
    - Test/train sample sizes
    - Per-year ratings
    """
    
    def __init__(self, logger=None):
        """
        Initialize results section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate(
        self,
        backtest_results: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """
        Generate year-by-year results table.
        
        Args:
            backtest_results: List of training results from each iteration
            kwargs: Additional arguments (ignored)
            
        Returns:
            str: Markdown formatted results table
        """
        if not backtest_results:
            return """## Year-by-Year Results

No results available."""
        
        # Build table header
        table_rows = ["""## Year-by-Year Results

| Test Year | Accuracy | AUC-ROC | Test Games | Train Games | Rating |
|-----------|----------|---------|------------|-------------|--------|"""]
        
        for result in backtest_results:
            year = result.get('test_year', 'Unknown')
            metrics = result.get('metrics', {})
            accuracy = metrics.get('accuracy', 0)
            auc = metrics.get('auc', 0)
            test_size = result.get('test_size', 0)
            train_size = result.get('train_size', 0)
            
            # Get NFL-specific rating
            rating_text, emoji, _ = get_performance_rating(accuracy)
            rating = f"{emoji} {rating_text}"
            
            table_rows.append(
                f"| {year} | {accuracy:.1%} | {auc:.3f} | {test_size:,} | {train_size:,} | {rating} |"
            )
        
        return '\n'.join(table_rows)


__all__ = ['ResultsSectionGenerator']
