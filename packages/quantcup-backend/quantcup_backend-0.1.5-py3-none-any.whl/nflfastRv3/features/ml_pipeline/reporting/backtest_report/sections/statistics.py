"""
Statistics Section Generator for Backtest Reports

Generates statistical significance testing section.
"""

import numpy as np
from scipy import stats
from typing import Dict, Any, List

from ...common import (
    STATISTICAL_SIGNIFICANCE_ALPHA,
    STATISTICAL_TEST_HYPOTHESES,
)


class StatisticsSectionGenerator:
    """
    Generates statistical significance testing section.
    
    Responsibilities:
    - T-tests against benchmarks (random, break-even, good)
    - Result interpretation with NFL context
    """
    
    def __init__(self, logger=None):
        """
        Initialize statistics section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def _format_table_helper(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Helper for markdown table formatting.
        
        Args:
            headers: Table headers
            rows: Table rows
            
        Returns:
            str: Formatted markdown table
        """
        if not rows:
            return ""
        
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
        separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
        
        data_rows = []
        for row in rows:
            formatted_row = "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
            data_rows.append(formatted_row)
        
        return header_row + "\n" + separator + "\n" + "\n".join(data_rows)
    
    def generate(self, backtest_results: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generate statistical significance testing section.
        
        Tests whether observed accuracy is statistically significant
        vs random chance and break-even thresholds.
        
        Args:
            backtest_results: List of training results from each test year
            kwargs: Additional arguments (ignored)
            
        Returns:
            str: Markdown formatted statistical test results
        """
        if not backtest_results:
            return ""
        
        accuracies = [r['metrics'].get('accuracy', 0) for r in backtest_results]
        n = len(accuracies)
        
        if n < 2:
            return ""  # Need at least 2 years for t-test
        
        mean_acc = float(np.mean(accuracies))
        
        # Test 1: vs Random (50%)
        t_stat_random, p_val_random = stats.ttest_1samp(accuracies, STATISTICAL_TEST_HYPOTHESES['random'])  # type: ignore[assignment]
        
        # Test 2: vs Break-even (52.4%)
        t_stat_breakeven, p_val_breakeven = stats.ttest_1samp(accuracies, STATISTICAL_TEST_HYPOTHESES['breakeven'])  # type: ignore[assignment]
        
        # Test 3: vs Good threshold (58%)
        t_stat_good, p_val_good = stats.ttest_1samp(accuracies, STATISTICAL_TEST_HYPOTHESES['good'])  # type: ignore[assignment]
        
        report = ["## Statistical Significance Testing\n"]
        report.append(f"Testing {n} years of backtest results for statistical significance:\n")
        
        # Results table
        headers = ['Hypothesis', 't-statistic', 'p-value', 'Result']
        rows = []
        
        # Test 1
        sig_random = "✅ Significant" if p_val_random < STATISTICAL_SIGNIFICANCE_ALPHA else "❌ Not Significant"  # type: ignore[operator]
        rows.append([
            "Accuracy > 50% (Random)",
            f"{t_stat_random:.3f}",
            f"{p_val_random:.4f}",
            sig_random
        ])
        
        # Test 2
        sig_breakeven = "✅ Significant" if p_val_breakeven < STATISTICAL_SIGNIFICANCE_ALPHA else "❌ Not Significant"  # type: ignore[operator]
        rows.append([
            "Accuracy > 52.4% (Break-even)",
            f"{t_stat_breakeven:.3f}",
            f"{p_val_breakeven:.4f}",
            sig_breakeven
        ])
        
        # Test 3
        sig_good = "✅ Significant" if p_val_good < STATISTICAL_SIGNIFICANCE_ALPHA else "❌ Not Significant"  # type: ignore[operator]
        rows.append([
            "Accuracy > 58% (Good)",
            f"{t_stat_good:.3f}",
            f"{p_val_good:.4f}",
            sig_good
        ])
        
        report.append(self._format_table_helper(headers, rows))
        report.append("")
        
        # Interpretation
        report.append("### Interpretation\n")
        
        if p_val_random < STATISTICAL_SIGNIFICANCE_ALPHA:  # type: ignore[operator]
            report.append(f"✅ **Performance is statistically better than random** (p={p_val_random:.4f})")
        else:
            report.append(f"⚠️ **Cannot prove performance better than random** (p={p_val_random:.4f})")
        
        if p_val_breakeven < STATISTICAL_SIGNIFICANCE_ALPHA:  # type: ignore[operator]
            report.append(f"✅ **Performance is statistically profitable** (p={p_val_breakeven:.4f})")
        else:
            report.append(f"⚠️ **Cannot prove profitability** (p={p_val_breakeven:.4f})")
        
        report.append(f"\n**Note:** p-value < {STATISTICAL_SIGNIFICANCE_ALPHA} indicates 95% confidence that results are not due to chance.")
        
        return '\n'.join(report)


__all__ = ['StatisticsSectionGenerator']
