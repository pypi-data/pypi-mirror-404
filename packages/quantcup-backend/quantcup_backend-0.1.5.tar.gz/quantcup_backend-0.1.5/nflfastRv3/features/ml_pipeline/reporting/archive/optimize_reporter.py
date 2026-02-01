"""
Window Optimization Report Generator

Generates aggregated reports for training window optimization experiments.
Following the same pattern as generator.py and backtest_reporter.py.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Orchestrator → Analyzers/Interpreters)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy import stats

from .analyzers import create_metrics_analyzer


class OptimizationReportGenerator:
    """
    Window optimization report orchestrator.
    
    Aggregates training results across different window sizes to identify
    the optimal amount of training data for a specific test period.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + orchestration)
    Depth: 1 layer (simple aggregation)
    """
    
    def __init__(self, logger=None):
        """
        Initialize with optional logger.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_report(
        self,
        optimization_results: List[Dict[str, Any]],
        model_name: str,
        test_year: int,
        test_week: int,
        min_years: int,
        max_years: int,
        output_dir: str = 'reports'
    ) -> str:
        """
        Generate comprehensive window optimization report.
        
        Args:
            optimization_results: List of training results from each window size
            model_name: Model name
            test_year: Test year
            test_week: Test week
            min_years: Minimum training years tested
            max_years: Maximum training years tested
            output_dir: Directory to save report
            
        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'optimization_report_{model_name}_{test_year}_week{test_week}_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build report sections
        report_sections = []
        
        report_sections.append(self._generate_header(model_name, test_year, test_week, min_years, max_years))
        report_sections.append(self._generate_executive_summary(optimization_results))
        report_sections.append(self._generate_nfl_benchmarking_context())
        
        # Add feature selection audit (same features used across all window sizes)
        if optimization_results and 'X_train' in optimization_results[0] and 'X_test' in optimization_results[0]:
            analyzer = create_metrics_analyzer()
            # Use the optimal result's data for the audit
            best_result = max(optimization_results, key=lambda x: x['metrics'].get('accuracy', 0))
            audit_section = analyzer.analyze_feature_selection_audit(
                best_result['X_train'],
                best_result['X_test'],
                best_result.get('y_train')
            )
            # Add context note for optimization reports
            audit_with_note = audit_section.replace(
                "\n## Feature Selection Audit",
                "\n## Feature Selection Audit\n\n**Note:** The same feature set is used across all " +
                f"{len(optimization_results)} window sizes tested. This audit shows which features " +
                "contributed to finding the optimal training window."
            )
            report_sections.append(audit_with_note)
        
        report_sections.append(self._generate_window_comparison_table(optimization_results))
        report_sections.append(self._generate_optimal_window_analysis(optimization_results))
        report_sections.append(self._generate_diminishing_returns_analysis(optimization_results))
        report_sections.append(self._generate_recommendations(optimization_results, test_year, test_week))
        
        # Write report
        report_content = '\n\n'.join(report_sections)
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Optimization report saved: {report_path}")
        
        return str(report_path)
    
    def _generate_header(self, model_name: str, test_year: int, test_week: int,
                        min_years: int, max_years: int) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""# NFL Training Window Optimization Report

**Generated:** {timestamp}

**Model:** {model_name}  
**Test Period:** {test_year} Week {test_week}  
**Window Range Tested:** {min_years}-{max_years} years

---"""
    
    def _generate_executive_summary(self, results: List[Dict[str, Any]]) -> str:
        """Generate executive summary with optimal window."""
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
    
    def _generate_nfl_benchmarking_context(self) -> str:
        """Generate NFL-specific benchmarking context section."""
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
    
    def _generate_window_comparison_table(self, results: List[Dict[str, Any]]) -> str:
        """Generate detailed comparison table with statistical measures."""
        if not results:
            return """## Window Size Comparison

No results available."""
        
        # Sort by window size
        sorted_results = sorted(results, key=lambda x: x.get('train_years', 0))
        
        # Find best
        best_accuracy = max(r['metrics'].get('accuracy', 0) for r in results)
        
        # Check if we have standard deviations (multi-seed results)
        has_std = any(r['metrics'].get('accuracy_std', 0) > 0 for r in results)
        
        # Build table header
        if has_std:
            table_rows = ["""## Window Size Comparison

| Window (Years) | Accuracy (Mean ± Std) | Range | AUC-ROC | Training Games | Test Games | Status |
|----------------|----------------------|-------|---------|----------------|------------|--------|"""]
        else:
            table_rows = ["""## Window Size Comparison

| Window (Years) | Accuracy | AUC-ROC | Training Games | Test Games | Status |
|----------------|----------|---------|----------------|------------|--------|"""]
        
        for result in sorted_results:
            window = result.get('train_years', 0)
            metrics = result.get('metrics', {})
            accuracy = metrics.get('accuracy', 0)
            accuracy_std = metrics.get('accuracy_std', 0)
            accuracy_min = metrics.get('accuracy_min', accuracy)
            accuracy_max = metrics.get('accuracy_max', accuracy)
            auc = metrics.get('auc', 0)
            train_size = result.get('train_size', 0)
            test_size = result.get('test_size', 0)
            
            # Mark optimal
            status = "✨ **OPTIMAL**" if accuracy == best_accuracy else ""
            
            if has_std and accuracy_std > 0:
                table_rows.append(
                    f"| {window} | {accuracy:.1%} ± {accuracy_std:.1%} | "
                    f"{accuracy_min:.1%}-{accuracy_max:.1%} | {auc:.3f} | "
                    f"{train_size:,} | {test_size:,} | {status} |"
                )
            else:
                table_rows.append(
                    f"| {window} | {accuracy:.1%} | {auc:.3f} | {train_size:,} | {test_size:,} | {status} |"
                )
        
        return '\n'.join(table_rows)
    
    def _generate_optimal_window_analysis(self, results: List[Dict[str, Any]]) -> str:
        """Analyze the optimal window configuration with statistical significance."""
        if not results:
            return """## Optimal Window Analysis

No results to analyze."""
        
        # Find best
        best_result = max(results, key=lambda x: x['metrics'].get('accuracy', 0))
        best_window = best_result.get('train_years', 0)
        best_accuracy = best_result['metrics'].get('accuracy', 0)
        best_std = best_result['metrics'].get('accuracy_std', 0)
        
        # Compare to neighbors
        sorted_results = sorted(results, key=lambda x: x.get('train_years', 0))
        best_idx = next(i for i, r in enumerate(sorted_results) if r.get('train_years') == best_window)
        
        # Get neighbors
        prev_window = sorted_results[best_idx - 1] if best_idx > 0 else None
        next_window = sorted_results[best_idx + 1] if best_idx < len(sorted_results) - 1 else None
        
        analysis = [f"""## Optimal Window Analysis

**Best Configuration:** {best_window} years with {best_accuracy:.1%}"""]
        
        if best_std > 0:
            analysis.append(f" accuracy (±{best_std:.1%} std)")
        else:
            analysis.append(" accuracy")
        
        analysis.append("\n**Comparison with Adjacent Windows:**")
        
        if prev_window:
            prev_acc = prev_window['metrics'].get('accuracy', 0)
            prev_years = prev_window.get('train_years', 0)
            diff = best_accuracy - prev_acc
            analysis.append(f"- **{prev_years} years:** {prev_acc:.1%} ({diff:+.1%} worse)")
        
        if next_window:
            next_acc = next_window['metrics'].get('accuracy', 0)
            next_years = next_window.get('train_years', 0)
            diff = best_accuracy - next_acc
            analysis.append(f"- **{next_years} years:** {next_acc:.1%} ({diff:+.1%} worse)")
        
        # Add statistical significance analysis if we have multi-seed results
        if best_std > 0 and len(results) > 1:
            analysis.append("\n### Statistical Significance")
            
            # Calculate if differences are statistically significant
            num_seeds = best_result.get('num_seeds', 1)
            if num_seeds > 1:
                from scipy import stats
                
                analysis.append(f"\n**Based on {num_seeds} random seeds:**")
                
                # Compare best to each other window
                for other in sorted_results:
                    if other['train_years'] == best_window:
                        continue
                    
                    other_acc = other['metrics'].get('accuracy', 0)
                    other_std = other['metrics'].get('accuracy_std', 0)
                    other_years = other.get('train_years', 0)
                    
                    if other_std > 0:
                        # Two-sample t-test
                        se_diff = np.sqrt((best_std**2 + other_std**2) / num_seeds)
                        
                        if se_diff > 0:
                            t_stat = (best_accuracy - other_acc) / se_diff
                            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=2*num_seeds-2))
                            
                            sig_marker = "✓" if p_value < 0.05 else "✗"
                            analysis.append(
                                f"- **{best_window} vs {other_years} years:** "
                                f"{best_accuracy - other_acc:+.1%} difference, p={p_value:.3f} {sig_marker}"
                            )
        
        # Stability assessment
        if prev_window and next_window:
            prev_acc = prev_window['metrics'].get('accuracy', 0)
            next_acc = next_window['metrics'].get('accuracy', 0)
            
            if abs(best_accuracy - prev_acc) < 0.01 and abs(best_accuracy - next_acc) < 0.01:
                stability = "🟢 Very stable - Performance is consistent around this window size"
            elif abs(best_accuracy - prev_acc) < 0.03 and abs(best_accuracy - next_acc) < 0.03:
                stability = "🟡 Moderately stable - Some sensitivity to window size"
            else:
                stability = "🔴 Unstable - Performance highly sensitive to window size"
            
            analysis.append(f"\n**Stability:** {stability}")
        
        return '\n'.join(analysis)
    
    def _generate_diminishing_returns_analysis(self, results: List[Dict[str, Any]]) -> str:
        """Analyze diminishing returns as window size increases."""
        if len(results) < 3:
            return """## Diminishing Returns Analysis

Insufficient data for diminishing returns analysis (need at least 3 window sizes)."""
        
        # Sort by window size
        sorted_results = sorted(results, key=lambda x: x.get('train_years', 0))
        
        # Calculate marginal improvements
        marginal_improvements = []
        for i in range(1, len(sorted_results)):
            curr_acc = sorted_results[i]['metrics'].get('accuracy', 0)
            prev_acc = sorted_results[i-1]['metrics'].get('accuracy', 0)
            curr_years = sorted_results[i].get('train_years', 0)
            prev_years = sorted_results[i-1].get('train_years', 0)
            
            years_added = curr_years - prev_years
            improvement = curr_acc - prev_acc
            marginal = improvement / years_added if years_added > 0 else 0
            
            marginal_improvements.append({
                'from_years': prev_years,
                'to_years': curr_years,
                'years_added': years_added,
                'improvement': improvement,
                'marginal': marginal
            })
        
        # Identify point of diminishing returns
        positive_marginals = [m for m in marginal_improvements if m['marginal'] > 0]
        
        if positive_marginals:
            max_marginal = max(positive_marginals, key=lambda x: x['marginal'])
            diminishing_point = max_marginal['to_years']
        else:
            diminishing_point = sorted_results[0].get('train_years', 0)
        
        analysis = ["""## Diminishing Returns Analysis

**Marginal Improvement per Additional Year:**"""]
        
        for mi in marginal_improvements[-5:]:  # Show last 5
            analysis.append(
                f"- **{mi['from_years']}→{mi['to_years']} years:** "
                f"{mi['improvement']:+.1%} gain ({mi['marginal']:+.2%} per year)"
            )
        
        analysis.append(f"\n**Point of Diminishing Returns:** Around {diminishing_point} years")
        analysis.append(
            f"\n**Interpretation:** Adding data beyond {diminishing_point} years provides "
            f"{'minimal benefit' if diminishing_point < max(r.get('train_years', 0) for r in sorted_results) / 2 else 'continued value'}."
        )
        
        return '\n'.join(analysis)
    
    def _generate_recommendations(self, results: List[Dict[str, Any]],
                                  test_year: int, test_week: int) -> str:
        """Generate actionable recommendations."""
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


def create_optimize_reporter(logger=None):
    """
    Factory function to create optimization report generator.
    
    Matches pattern from create_report_generator()
    
    Args:
        logger: Optional logger instance
        
    Returns:
        OptimizationReportGenerator: Configured optimization reporter
    """
    return OptimizationReportGenerator(logger=logger)


__all__ = ['OptimizationReportGenerator', 'create_optimize_reporter']