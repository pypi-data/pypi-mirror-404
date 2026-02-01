"""
Summary Section Generator for Backtest Reports

Generates header, executive summary, and NFL benchmarking context.
"""

import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

from ...common import (
    get_performance_rating,
    calculate_roi,
    NFL_BENCHMARKING_TEXT,
)


class SummarySectionGenerator:
    """
    Generates summary sections for backtest reports.
    
    Responsibilities:
    - Report header with metadata
    - Executive summary with aggregate statistics
    - NFL benchmarking context for interpretation
    """
    
    def __init__(self, logger=None):
        """
        Initialize summary section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_header(
        self,
        model_name: str,
        train_years: int,
        start_year: int,
        end_year: int,
        test_week: Optional[int]
    ) -> str:
        """
        Generate report header with metadata.
        
        Args:
            model_name: Model name
            train_years: Number of training years
            start_year: Backtest start year
            end_year: Backtest end year
            test_week: Optional specific test week
            
        Returns:
            str: Markdown formatted header
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        test_desc = f"Week {test_week}" if test_week else "Full Season"
        num_years = end_year - start_year + 1
        
        return f"""# NFL Model Backtesting Report

**Generated:** {timestamp}

**Model:** {model_name}  
**Training Window:** {train_years} years  
**Test Period:** {start_year}-{end_year} ({num_years} years, {test_desc})

---"""
    
    def generate_executive_summary(
        self,
        backtest_results: List[Dict[str, Any]],
        train_years: int
    ) -> str:
        """
        Generate executive summary with key statistics.
        
        Args:
            backtest_results: List of training results from each iteration
            train_years: Number of training years
            
        Returns:
            str: Markdown formatted executive summary
        """
        if not backtest_results:
            return """## Executive Summary

**No results to analyze** - All backtest iterations failed."""
        
        # Extract metrics
        accuracies = [r['metrics'].get('accuracy', 0) for r in backtest_results]
        aucs = [r['metrics'].get('auc', 0) for r in backtest_results]
        
        avg_accuracy = float(np.mean(accuracies))
        avg_auc = float(np.mean(aucs))
        std_accuracy = float(np.std(accuracies))
        
        # Get performance rating and ROI
        rating, emoji, level = get_performance_rating(avg_accuracy, std_accuracy)
        roi = calculate_roi(avg_accuracy)
        
        # Consistency assessment
        if std_accuracy < 0.05:
            consistency_desc = "exceptional"
        elif std_accuracy < 0.08:
            consistency_desc = "strong"
        else:
            consistency_desc = "normal"
        
        return f"""## Executive Summary

**Overall Performance:** {emoji} {rating} - {level} (~{roi:.1%} ROI)

**Aggregate Metrics (across {len(backtest_results)} years):**
- **Average Accuracy:** {avg_accuracy:.1%} ± {std_accuracy:.1%}
- **Estimated ROI:** {roi:.1%} at -110 odds
- **Average AUC-ROC:** {avg_auc:.3f}
- **Best Year:** {max(accuracies):.1%} accuracy
- **Worst Year:** {min(accuracies):.1%} accuracy
- **Consistency (Std Dev):** {std_accuracy:.1%}

**Key Insight:** The {train_years}-year training window achieved {avg_accuracy:.1%} average accuracy across {len(backtest_results)} test years, with {std_accuracy:.1%} standard deviation indicating {consistency_desc} consistency for NFL prediction."""
    
    def generate_benchmarking_context(self) -> str:
        """
        Generate NFL benchmarking context section.
        
        Returns:
            str: Markdown formatted benchmarking context
        """
        return NFL_BENCHMARKING_TEXT
    
    def generate(
        self,
        model_name: str,
        train_years: int,
        start_year: int,
        end_year: int,
        test_week: Optional[int],
        backtest_results: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """
        Generate complete summary section.
        
        Args:
            model_name: Model name
            train_years: Number of training years
            start_year: Backtest start year
            end_year: Backtest end year
            test_week: Optional specific test week
            backtest_results: List of training results
            kwargs: Additional arguments (ignored)
            
        Returns:
            str: Complete summary section
        """
        sections = [
            self.generate_header(model_name, train_years, start_year, end_year, test_week),
            self.generate_executive_summary(backtest_results, train_years),
            self.generate_benchmarking_context(),
        ]
        
        return '\n\n'.join(sections)


__all__ = ['SummarySectionGenerator']
