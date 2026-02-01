"""
Summary Section Generator

Generates the executive summary and header sections for window optimization reports.
"""

import numpy as np
from datetime import datetime
from typing import Dict, Any, List


class SummarySectionGenerator:
    """
    Generates header and executive summary sections.
    
    Provides overview of optimization results and identifies optimal window.
    """
    
    def __init__(self, logger=None):
        """
        Initialize summary generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_header(
        self,
        model_name: str,
        test_year: int,
        test_week: int,
        min_years: int,
        max_years: int
    ) -> str:
        """
        Generate report header.
        
        Args:
            model_name: Model name
            test_year: Test year
            test_week: Test week
            min_years: Minimum training years tested
            max_years: Maximum training years tested
            
        Returns:
            str: Formatted header section
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""# NFL Training Window Optimization Report

**Generated:** {timestamp}

**Model:** {model_name}  
**Test Period:** {test_year} Week {test_week}  
**Window Range Tested:** {min_years}-{max_years} years

---"""
    
    def generate_executive_summary(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate executive summary with optimal window.
        
        Args:
            results: List of training results from each window size
            
        Returns:
            str: Formatted executive summary section
        """
        if not results:
            return """## Executive Summary

**No results to analyze** - All optimization iterations failed."""
        
        # Find best window
        best_result = max(results, key=lambda x: x['metrics'].get('accuracy', 0))
        best_window = best_result.get('train_years', 0)
        best_accuracy = best_result['metrics'].get('accuracy', 0)
        best_auc = best_result['metrics'].get('auc', 0)
        
        # Calculate improvement vs alternatives
        all_accuracies = [r['metrics'].get('accuracy', 0) for r in results]
        avg_accuracy = np.mean(all_accuracies)
        improvement = best_accuracy - avg_accuracy
        
        return f"""## Executive Summary

**🏆 Optimal Training Window: {best_window} Years**

**Performance:**
- **Best Accuracy:** {best_accuracy:.1%}
- **Best AUC-ROC:** {best_auc:.3f}
- **Improvement vs Average:** +{improvement:.1%}

**Configurations Tested:** {len(results)} different window sizes

**Key Insight:** Using {best_window} years of training data achieves {best_accuracy:.1%} accuracy for this test period, outperforming the average by {improvement:.1%}."""
    
    def generate_nfl_benchmarking_context(self) -> str:
        """
        Generate NFL-specific benchmarking context section.
        
        Returns:
            str: Formatted benchmarking context section
        """
        return """## 📊 NFL Prediction Benchmarking Context

**Why NFL Prediction Differs from Traditional ML:**

NFL game prediction is fundamentally different from typical machine learning classification tasks:
- Games are designed to be ~50/50 propositions by oddsmakers
- High inherent variance due to injuries, weather, officiating, and human factors
- Limited sample sizes (only 272 games per regular season)
- High competitive parity by design (draft system, salary cap, revenue sharing)
- Continuous roster turnover and coaching changes

**Industry Performance Benchmarks:**

| Accuracy | Status | Estimated ROI* | Performance Level |
|----------|--------|---------------|-------------------|
| 68%+ | 🟢 Elite | 30%+ | Top 1% of professional handicappers |
| 63-67% | 🟢 Exceptional | 15-29% | Elite professional performance |
| 60-62% | 🟡 Strong | 9-14% | Consistently profitable professional |
| 58-59% | 🟡 Good | 5-8% | Professional handicapper |
| 55-57% | 🟠 Fair | 2-4% | Beating the market |
| 52.4-54% | 🟠 Marginal | 0-1% | Near break-even |
| <52.4% | 🔴 Unprofitable | Negative | Losing money after vig |

*Estimated ROI assuming standard -110 betting odds with flat bet sizing.

**Expected Variance:**
- Even elite handicappers experience ±3-5% accuracy variance year-to-year
- Standard deviation of 5-8% is NORMAL for sports betting, not a flaw
- NFL parity increases naturally (injuries, rule changes, coaching turnover)

**Important Note on Sample Size:**
- Single-week tests (~16 games) have high variance and limited statistical power
- Full-season tests (250+ games) provide more reliable window optimization
- Small differences between window sizes may not be meaningful with small samples

**Key Takeaway:** In NFL prediction, 60% accuracy is STRONG performance, 65% is EXCEPTIONAL, and 70%+ sustained across full seasons is nearly impossible. Use this context when interpreting window size differences."""


__all__ = ['SummarySectionGenerator']
