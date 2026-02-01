"""
Recommendations Section Generator

Generates actionable recommendations based on window optimization results.
"""

import numpy as np
from typing import Dict, Any, List


class RecommendationsSectionGenerator:
    """
    Generates recommendations section.
    
    Provides actionable recommendations for optimal window selection and best practices.
    """
    
    def __init__(self, logger=None):
        """
        Initialize recommendations generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate(
        self,
        results: List[Dict[str, Any]],
        test_year: int,
        test_week: int
    ) -> str:
        """
        Generate actionable recommendations.
        
        Args:
            results: List of training results from each window size
            test_year: Test year
            test_week: Test week
            
        Returns:
            str: Formatted recommendations section
        """
        if not results:
            return """## Recommendations

Unable to generate recommendations - no successful results."""
        
        # Find best
        best_result = max(results, key=lambda x: x['metrics'].get('accuracy', 0))
        best_window = best_result.get('train_years', 0)
        best_accuracy = best_result['metrics'].get('accuracy', 0)
        
        recommendations = ["""## Recommendations"""]
        
        # Check sample size and add warning if needed
        test_size = best_result.get('test_size', 0)
        sample_warning = ""
        if test_size < 50:
            sample_warning = f"""

**⚠️ Sample Size Warning:** This optimization was tested on only {test_size} games, which may not provide statistically reliable results. Consider:
- Running optimization on a full season (250+ games) for more robust findings
- Testing the recommended window on multiple weeks/years before deploying
- Using these results as directional guidance, not definitive answers"""
        
        # Primary recommendation with NFL context
        recommendations.append(f"""
### ✅ Use {best_window}-Year Training Window

For predicting {test_year} Week {test_week}, use **{best_window} years** of training data:

**Configuration:**
```bash
quantcup nflfastrv3 ml train \\
  --model-name game_outcome \\
  --train-years {best_window} \\
  --test-year {test_year} \\
  --test-week {test_week}
```

**Expected Performance:** {best_accuracy:.1%} accuracy (see NFL benchmarks above for context){sample_warning}""")
        
        # Validation recommendation
        all_accuracies = [r['metrics'].get('accuracy', 0) for r in results]
        std_dev = np.std(all_accuracies)
        
        if std_dev > 0.05:
            recommendations.append("""
### ⚠️ High Sensitivity to Window Size

Performance varies significantly by window size. Consider:

1. **Run backtest** - Test this window across multiple years to verify stability
2. **Use ensemble methods** - Combine predictions from top 3 window sizes for robustness
3. **Investigate feature stability** - Some features may degrade over long training periods
4. **Accept some variance** - Small differences (<3%) may be within normal NFL variance""")
        
        # Additional best practices with NFL context
        recommendations.append("""
### 🎯 Best Practices for NFL Prediction

1. **Revalidate regularly** - Optimal window may shift as NFL evolves (rule changes, strategy shifts)
2. **Test on full seasons** - Single-week optimization has limited statistical power
3. **Consider recency bias** - Shorter windows emphasize recent trends, longer windows smooth variance
4. **Monitor live performance** - Track actual outcomes to validate your chosen window
5. **Document your choice** - Record rationale for window selection and performance over time
6. **Benchmark against industry** - 60%+ on full seasons is strong, 65%+ is exceptional""")
        
        # Efficiency recommendation
        sorted_results = sorted(results, key=lambda x: x['metrics'].get('accuracy', 0), reverse=True)
        top_3 = sorted_results[:3]
        
        if len(top_3) >= 3:
            recommendations.append(f"""
### 🔄 Alternative Window Sizes

Top 3 performing windows (within {0.03:.1%} of best):""")
            
            for i, r in enumerate(top_3, 1):
                window = r.get('train_years', 0)
                accuracy = r['metrics'].get('accuracy', 0)
                recommendations.append(f"{i}. **{window} years:** {accuracy:.1%} accuracy")
        
        return '\n'.join(recommendations)


__all__ = ['RecommendationsSectionGenerator']
