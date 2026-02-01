"""
Reporting Configuration

Centralized configuration for NFL performance benchmarks, thresholds,
and other hardcoded values used across reporting modules.
"""

from typing import NamedTuple, List, Tuple


class PerformanceThreshold(NamedTuple):
    """Performance threshold for NFL prediction accuracy."""
    min_accuracy: float
    max_accuracy: float
    min_std_dev: float
    max_std_dev: float
    rating: str
    emoji: str
    level: str
    min_roi: float
    max_roi: float


# NFL Performance Benchmarks
# Based on industry standards for sports betting and handicapping
NFL_PERFORMANCE_THRESHOLDS: List[PerformanceThreshold] = [
    PerformanceThreshold(
        min_accuracy=0.68,
        max_accuracy=1.0,
        min_std_dev=0.0,
        max_std_dev=0.06,
        rating="Elite",
        emoji="🟢",
        level="Top 1% of professional handicappers",
        min_roi=0.30,
        max_roi=1.0
    ),
    PerformanceThreshold(
        min_accuracy=0.63,
        max_accuracy=0.68,
        min_std_dev=0.0,
        max_std_dev=0.08,
        rating="Exceptional",
        emoji="🟢",
        level="Elite professional performance",
        min_roi=0.15,
        max_roi=0.29
    ),
    PerformanceThreshold(
        min_accuracy=0.60,
        max_accuracy=0.63,
        min_std_dev=0.0,
        max_std_dev=0.10,
        rating="Strong",
        emoji="🟡",
        level="Consistently profitable professional",
        min_roi=0.09,
        max_roi=0.14
    ),
    PerformanceThreshold(
        min_accuracy=0.58,
        max_accuracy=0.60,
        min_std_dev=0.0,
        max_std_dev=1.0,
        rating="Good",
        emoji="🟡",
        level="Professional handicapper",
        min_roi=0.05,
        max_roi=0.08
    ),
    PerformanceThreshold(
        min_accuracy=0.55,
        max_accuracy=0.58,
        min_std_dev=0.0,
        max_std_dev=1.0,
        rating="Fair",
        emoji="🟠",
        level="Beating the market",
        min_roi=0.02,
        max_roi=0.04
    ),
    PerformanceThreshold(
        min_accuracy=0.524,
        max_accuracy=0.55,
        min_std_dev=0.0,
        max_std_dev=1.0,
        rating="Marginal",
        emoji="🟠",
        level="Near break-even",
        min_roi=0.0,
        max_roi=0.01
    ),
    PerformanceThreshold(
        min_accuracy=0.0,
        max_accuracy=0.524,
        min_std_dev=0.0,
        max_std_dev=1.0,
        rating="Unprofitable",
        emoji="🔴",
        level="Losing money after vig",
        min_roi=-1.0,
        max_roi=0.0
    ),
]


# Consistency Thresholds (Standard Deviation)
CONSISTENCY_THRESHOLDS = {
    'exceptional': 0.04,  # Unusually stable for NFL
    'strong': 0.06,       # Expected professional variance
    'normal': 0.08,       # Typical for NFL prediction
    'fair': 0.10,         # Moderate variation
    'high_variance': float('inf')  # Investigate systematic issues
}


# Feature Stability Thresholds (Coefficient of Variation)
FEATURE_STABILITY_THRESHOLDS = {
    'pinned': 1e-6,           # Very small variance - check precision
    'extremely_stable': 0.01,  # Highly reliable core predictor
    'stable': 0.20,           # Reliable predictor
    'variable': 0.50,         # Context-dependent
    'unstable': float('inf')  # Unreliable - consider removal
}


# ROI Calculation Constants
ROI_BREAKEVEN_ACCURACY = 0.524  # 52.4% needed to break even at -110 odds
ROI_PAYOUT_MULTIPLIER_110 = 1.909  # Payout for -110 odds (100/110 * 2 + 10/110)


# Statistical Testing Thresholds
STATISTICAL_SIGNIFICANCE_ALPHA = 0.05  # p-value threshold
STATISTICAL_TEST_HYPOTHESES = {
    'random': 0.50,      # Better than coin flip
    'breakeven': 0.524,  # Better than break-even
    'good': 0.58,        # Better than "good" threshold
}


# NFL Benchmarking Context
NFL_BENCHMARKING_TEXT = """## 📊 NFL Prediction Benchmarking Context

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

**Key Takeaway:** In NFL prediction, 60% accuracy is STRONG performance, 65% is EXCEPTIONAL, and 70%+ sustained across full seasons is nearly impossible. Don't compare to 90%+ accuracies seen in other ML domains - NFL games are specifically designed to be coin flips."""


def get_performance_rating(accuracy: float, std_dev: float = 0.0) -> Tuple[str, str, str]:
    """
    Get performance rating based on accuracy and standard deviation.
    
    Args:
        accuracy: Model accuracy (0.0 to 1.0)
        std_dev: Standard deviation of accuracy across years (0.0 to 1.0)
        
    Returns:
        Tuple of (rating, emoji, level)
        
    Example:
        >>> rating, emoji, level = get_performance_rating(0.65, 0.05)
        >>> print(f"{emoji} {rating} - {level}")
        🟢 Exceptional - Elite professional performance
    """
    for threshold in NFL_PERFORMANCE_THRESHOLDS:
        if (threshold.min_accuracy <= accuracy < threshold.max_accuracy and
            std_dev < threshold.max_std_dev):
            return (threshold.rating, threshold.emoji, threshold.level)
    
    # Fallback
    return ("Unknown", "⚪", "Performance level could not be determined")


def get_consistency_rating(std_dev: float) -> Tuple[str, str, str]:
    """
    Get consistency rating based on standard deviation.
    
    Args:
        std_dev: Standard deviation of accuracy across years
        
    Returns:
        Tuple of (level, emoji, description)
        
    Example:
        >>> level, emoji, desc = get_consistency_rating(0.05)
        >>> print(f"{emoji} {level} - {desc}")
        🟢 Strong - Expected professional variance
    """
    if std_dev < CONSISTENCY_THRESHOLDS['exceptional']:
        return ("Exceptional", "🟢", "Unusually stable for NFL prediction")
    elif std_dev < CONSISTENCY_THRESHOLDS['strong']:
        return ("Strong", "🟢", "Expected professional variance")
    elif std_dev < CONSISTENCY_THRESHOLDS['normal']:
        return ("Normal", "🟡", "Typical for NFL prediction")
    elif std_dev < CONSISTENCY_THRESHOLDS['fair']:
        return ("Fair", "🟠", "Moderate year-to-year variation")
    else:
        return ("High Variance", "🔴", "Investigate systematic issues")


def get_feature_stability_rating(cv: float) -> Tuple[str, str]:
    """
    Get feature stability rating based on coefficient of variation.
    
    Args:
        cv: Coefficient of variation (std_dev / mean)
        
    Returns:
        Tuple of (stability_label, note)
        
    Example:
        >>> label, note = get_feature_stability_rating(0.15)
        >>> print(f"{label}: {note}")
        ✅ STABLE: Reliable predictor
    """
    if cv < FEATURE_STABILITY_THRESHOLDS['pinned']:
        return ("📌 PINNED", "Check precision - very small variance")
    elif cv < FEATURE_STABILITY_THRESHOLDS['extremely_stable']:
        return ("🔒 EXTREMELY STABLE", "Highly reliable core predictor")
    elif cv < FEATURE_STABILITY_THRESHOLDS['stable']:
        return ("✅ STABLE", "Reliable predictor")
    elif cv < FEATURE_STABILITY_THRESHOLDS['variable']:
        return ("⚠️ VARIABLE", "Context-dependent")
    else:
        return ("❌ UNSTABLE", "Unreliable - consider removal")


__all__ = [
    'NFL_PERFORMANCE_THRESHOLDS',
    'CONSISTENCY_THRESHOLDS',
    'FEATURE_STABILITY_THRESHOLDS',
    'ROI_BREAKEVEN_ACCURACY',
    'ROI_PAYOUT_MULTIPLIER_110',
    'STATISTICAL_SIGNIFICANCE_ALPHA',
    'STATISTICAL_TEST_HYPOTHESES',
    'NFL_BENCHMARKING_TEXT',
    'get_performance_rating',
    'get_consistency_rating',
    'get_feature_stability_rating',
]
