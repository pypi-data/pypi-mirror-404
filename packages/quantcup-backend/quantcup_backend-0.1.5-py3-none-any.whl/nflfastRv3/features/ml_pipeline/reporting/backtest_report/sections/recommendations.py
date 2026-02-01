"""
Recommendations Section Generator for Backtest Reports

Generates actionable recommendations based on backtest results.
"""

import numpy as np
from typing import Dict, Any, List

from ...common import calculate_roi


class RecommendationsSectionGenerator:
    """
    Generates actionable recommendations section.
    
    Responsibilities:
    - Performance-based recommendations
    - Consistency-based recommendations
    - General best practices
    """
    
    def __init__(self, logger=None):
        """
        Initialize recommendations section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate(
        self,
        backtest_results: List[Dict[str, Any]],
        train_years: int,
        **kwargs
    ) -> str:
        """
        Generate actionable recommendations based on backtest results.
        
        Args:
            backtest_results: List of training results from each iteration
            train_years: Number of training years used
            kwargs: Additional arguments (ignored)
            
        Returns:
            str: Markdown formatted recommendations
        """
        if not backtest_results:
            return """## Recommendations

Unable to generate recommendations - no successful results."""
        
        accuracies = [r['metrics'].get('accuracy', 0) for r in backtest_results]
        avg_accuracy = float(np.mean(accuracies))
        std_dev = float(np.std(accuracies))
        
        recommendations = ["""## Recommendations"""]
        
        # NFL-specific performance-based recommendations
        roi = calculate_roi(avg_accuracy)
        
        if avg_accuracy >= 0.68 and std_dev < 0.06:
            recommendations.append(f"""
### ✅ Elite Performance - Deploy with Confidence

Your {train_years}-year window is performing at the TOP 1% of NFL handicappers:

- **Estimated ROI:** {roi:.1%} at standard -110 odds
- **Performance Level:** Elite professional / sharp bettor
- **Recommendation:** Continue current approach, monitor for drift

**Action Items:**
1. **Deploy for live predictions** - This performance justifies real-world use
2. **Document this configuration** - Preserve what's working
3. **Monitor model drift** - Track ongoing performance to detect degradation
4. **Consider ensemble** - Combine with other methods for robustness""")
        elif avg_accuracy >= 0.60 and std_dev < 0.08:
            recommendations.append(f"""
### ✅ Strong Professional Performance

Your {train_years}-year window is SOLIDLY PROFITABLE:

- **Estimated ROI:** {roi:.1%} at standard -110 odds
- **Performance Level:** Professional handicapper
- **Recommendation:** This is strong performance - avoid over-optimization

**Action Items:**
1. **Consider deployment** - Model is ready for careful real-world testing
2. **Minor tuning only** - Don't fix what isn't broken
3. **Feature analysis** - Understand which features drive performance
4. **Test on current season** - Validate with live predictions""")
        elif avg_accuracy >= 0.55:
            recommendations.append(f"""
### 🟡 Profitable Performance - Room for Improvement

Your {train_years}-year window beats the market:

- **Estimated ROI:** {roi:.1%} at standard -110 odds
- **Performance Level:** Beating break-even, profitable
- **Recommendation:** Feature engineering may unlock additional gains

**Action Items:**
1. **Test adjacent windows** - Try {max(1, train_years-2)} and {train_years+2} years
2. **Add contextual features** - Injuries, weather, rest days, situational factors
3. **Analyze errors** - Study misclassified games for patterns
4. **Consider ensemble** - Combine multiple models for stability""")
        else:
            recommendations.append(f"""
### ⚠️ Below Profitable Threshold

Your {train_years}-year window is not yet profitable:

- **Estimated ROI:** {roi:.1%} at standard -110 odds (need 52.4%+ for break-even)
- **Performance Level:** Below market efficiency
- **Recommendation:** Significant improvements needed before deployment

**Action Items:**
1. **Run window optimization** - Test 1-25 years to find optimal training size
2. **Review feature quality** - Ensure features are predictive, not just descriptive
3. **Check for data leakage** - Verify no future information in training
4. **Try different algorithms** - XGBoost, LightGBM, ensemble methods
5. **Increase training data** - If possible, add more historical seasons""")
        
        # Consistency-based recommendations
        if std_dev > 0.10:
            recommendations.append("""
### 🔴 High Performance Variance Detected

Your model's year-to-year performance varies more than typical for NFL:

**Note:** Even professional handicappers expect ±5-8% variance year-to-year in NFL prediction.

**Action Items:**
1. **Investigate anomalous years** - What made best/worst years different?
2. **Check for overfitting** - Model may be too tuned to specific historical patterns
3. **Add temporal features** - Rule changes, roster turnover, coaching changes
4. **Use ensemble methods** - Combine multiple window sizes to smooth variance
5. **Accept some variance** - NFL has inherent unpredictability""")
        
        # General best practices
        recommendations.append("""
### General Best Practices

1. **Rerun annually** - Backtest with latest data to verify stability
2. **Track live performance** - Compare predictions to actual outcomes
3. **Version your models** - Save models from each backtest iteration
4. **Document findings** - Keep notes on what works and what doesn't
5. **Share results** - Collaborate with other analysts for insights""")
        
        return '\n'.join(recommendations)


__all__ = ['RecommendationsSectionGenerator']
