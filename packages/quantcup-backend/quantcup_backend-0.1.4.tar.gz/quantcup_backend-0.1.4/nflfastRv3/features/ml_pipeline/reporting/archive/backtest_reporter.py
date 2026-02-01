"""
Backtest Report Generator

Generates aggregated reports for backtesting operations across multiple years.
Following the same pattern as generator.py.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Orchestrator → Analyzers/Interpreters)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
from scipy import stats

from .analyzers import create_metrics_analyzer


class BacktestReportGenerator:
    """
    Backtest report orchestrator.
    
    Aggregates training results across multiple years to show
    model stability and performance trends over time.
    
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
    
    def _calculate_roi(self, accuracy: float) -> float:
        """
        Calculate estimated ROI at standard -110 betting odds.
        
        Formula: ROI = (accuracy * 1.909 - 1) for -110 odds
        Where 1.909 comes from winning $100 on $110 bet (100/110 * 2 + 10/110)
        
        Args:
            accuracy: Win rate (0.0 to 1.0)
            
        Returns:
            float: Estimated ROI as decimal (e.g., 0.12 = 12% ROI)
        """
        if accuracy < 0.524:
            # Below break-even
            return (accuracy - 0.524) * 2  # Approximate loss rate
        else:
            # Simplified ROI calculation for -110 odds
            # More accurate: ((wins * 0.909) - losses) / total_bets
            wins_per_100 = accuracy * 100
            losses_per_100 = (1 - accuracy) * 100
            profit = (wins_per_100 * 0.909) - losses_per_100
            return profit / 100
    
    def generate_report(
        self,
        backtest_results: List[Dict[str, Any]],
        model_name: str,
        train_years: int,
        start_year: int,
        end_year: int,
        test_week: Optional[int] = None,
        output_dir: str = 'reports'
    ) -> str:
        """
        Generate comprehensive backtest report.
        
        Args:
            backtest_results: List of training results from each iteration
            model_name: Model name
            train_years: Number of training years
            start_year: Backtest start year
            end_year: Backtest end year
            test_week: Optional specific test week
            output_dir: Directory to save report
            
        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        week_suffix = f"_week{test_week}" if test_week else ""
        report_filename = f'backtest_report_{model_name}_{start_year}_{end_year}{week_suffix}_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build report sections
        report_sections = []
        
        report_sections.append(self._generate_header(model_name, train_years, start_year, end_year, test_week))
        report_sections.append(self._generate_executive_summary(backtest_results, train_years))
        report_sections.append(self._generate_nfl_benchmarking_context())
        
        # Add feature selection audit (same features used across all test years)
        if backtest_results and 'X_train' in backtest_results[0] and 'X_test' in backtest_results[0]:
            analyzer = create_metrics_analyzer()
            first_result = backtest_results[0]
            audit_section = analyzer.analyze_feature_selection_audit(
                first_result['X_train'],
                first_result['X_test'],
                first_result.get('y_train')
            )
            # Add context note for backtest reports
            audit_with_note = audit_section.replace(
                "\n## Feature Selection Audit",
                "\n## Feature Selection Audit\n\n**Note:** The same feature set is used across all " +
                f"{len(backtest_results)} test years. This audit shows which features contributed to " +
                "the backtest results above."
            )
            report_sections.append(audit_with_note)
        
        report_sections.append(self._generate_year_by_year_results(backtest_results))
        report_sections.append(self._generate_performance_trends(backtest_results))
        report_sections.append(self._generate_consistency_analysis(backtest_results))
        
        # Add new analysis sections
        report_sections.append(self._generate_statistical_tests(backtest_results))
        report_sections.append(self._generate_feature_importance_stability(backtest_results))
        
        report_sections.append(self._generate_recommendations(backtest_results, train_years))
        
        # Write report
        report_content = '\n\n'.join(report_sections)
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Backtest report saved: {report_path}")
        
        return str(report_path)
    
    def _generate_header(self, model_name: str, train_years: int,
                        start_year: int, end_year: int, test_week: Optional[int]) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        test_desc = f"Week {test_week}" if test_week else "Full Season"
        num_years = end_year - start_year + 1
        
        return f"""# NFL Model Backtesting Report

**Generated:** {timestamp}

**Model:** {model_name}  
**Training Window:** {train_years} years  
**Test Period:** {start_year}-{end_year} ({num_years} years, {test_desc})

---"""
    
    def _generate_executive_summary(self, results: List[Dict[str, Any]], 
                                   train_years: int) -> str:
        """Generate executive summary with key statistics."""
        if not results:
            return """## Executive Summary

**No results to analyze** - All backtest iterations failed."""
        
        # Extract metrics
        accuracies = [r['metrics'].get('accuracy', 0) for r in results]
        aucs = [r['metrics'].get('auc', 0) for r in results]
        
        avg_accuracy = np.mean(accuracies)
        avg_auc = np.mean(aucs)
        std_accuracy = np.std(accuracies)
        
        # NFL-specific performance rating
        roi = self._calculate_roi(avg_accuracy)
        
        if avg_accuracy >= 0.68 and std_accuracy < 0.06:
            rating = "🟢 Elite - Top Sharp Performance"
            perf_note = f"(~{roi:.1%} ROI potential)"
        elif avg_accuracy >= 0.63 and std_accuracy < 0.08:
            rating = "🟢 Exceptional - Elite Professional"
            perf_note = f"(~{roi:.1%} ROI)"
        elif avg_accuracy >= 0.60 and std_accuracy < 0.10:
            rating = "🟡 Strong - Consistently Profitable"
            perf_note = f"(~{roi:.1%} ROI)"
        elif avg_accuracy >= 0.58:
            rating = "🟡 Good - Profitable Performance"
            perf_note = f"(~{roi:.1%} ROI)"
        elif avg_accuracy >= 0.55:
            rating = "🟠 Fair - Above Break-Even"
            perf_note = f"(~{roi:.1%} ROI)"
        elif avg_accuracy >= 0.524:
            rating = "🟠 Marginal - Near Break-Even"
            perf_note = "(~0% ROI)"
        else:
            rating = "🔴 Below Break-Even"
            perf_note = f"(~{roi:.1%} ROI)"
        
        return f"""## Executive Summary

**Overall Performance:** {rating} {perf_note}

**Aggregate Metrics (across {len(results)} years):**
- **Average Accuracy:** {avg_accuracy:.1%} ± {std_accuracy:.1%}
- **Estimated ROI:** {roi:.1%} at -110 odds
- **Average AUC-ROC:** {avg_auc:.3f}
- **Best Year:** {max(accuracies):.1%} accuracy
- **Worst Year:** {min(accuracies):.1%} accuracy
- **Consistency (Std Dev):** {std_accuracy:.1%}

**Key Insight:** The {train_years}-year training window achieved {avg_accuracy:.1%} average accuracy across {len(results)} test years, with {std_accuracy:.1%} standard deviation indicating {'exceptional' if std_accuracy < 0.05 else 'strong' if std_accuracy < 0.08 else 'normal'} consistency for NFL prediction."""
    
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

**Key Takeaway:** In NFL prediction, 60% accuracy is STRONG performance, 65% is EXCEPTIONAL, and 70%+ sustained across full seasons is nearly impossible. Don't compare to 90%+ accuracies seen in other ML domains - NFL games are specifically designed to be coin flips."""
    
    def _generate_year_by_year_results(self, results: List[Dict[str, Any]]) -> str:
        """Generate detailed year-by-year breakdown."""
        if not results:
            return """## Year-by-Year Results

No results available."""
        
        # Build table header
        table_rows = ["""## Year-by-Year Results

| Test Year | Accuracy | AUC-ROC | Test Games | Train Games | Rating |
|-----------|----------|---------|------------|-------------|--------|"""]
        
        for result in results:
            year = result.get('test_year', 'Unknown')
            metrics = result.get('metrics', {})
            accuracy = metrics.get('accuracy', 0)
            auc = metrics.get('auc', 0)
            test_size = result.get('test_size', 0)
            train_size = result.get('train_size', 0)
            
            # NFL-specific rating
            if accuracy >= 0.68:
                rating = "🟢 Elite"
            elif accuracy >= 0.63:
                rating = "🟢 Exceptional"
            elif accuracy >= 0.60:
                rating = "🟡 Strong"
            elif accuracy >= 0.58:
                rating = "🟡 Good"
            elif accuracy >= 0.55:
                rating = "🟠 Fair"
            elif accuracy >= 0.524:
                rating = "🟠 Marginal"
            else:
                rating = "🔴 Unprofitable"
            
            table_rows.append(
                f"| {year} | {accuracy:.1%} | {auc:.3f} | {test_size:,} | {train_size:,} | {rating} |"
            )
        
        return '\n'.join(table_rows)
    
    def _generate_performance_trends(self, results: List[Dict[str, Any]]) -> str:
        """Analyze performance trends over time."""
        if len(results) < 3:
            return """## Performance Trends

Insufficient data for trend analysis (need at least 3 years)."""
        
        # Extract data
        years = [r.get('test_year', 0) for r in results]
        accuracies = [r['metrics'].get('accuracy', 0) for r in results]
        
        # Simple trend analysis
        first_half = accuracies[:len(accuracies)//2]
        second_half = accuracies[len(accuracies)//2:]
        
        trend_direction = "improving" if np.mean(second_half) > np.mean(first_half) else "declining"
        
        # Identify best and worst years
        best_idx = np.argmax(accuracies)
        worst_idx = np.argmin(accuracies)
        
        return f"""## Performance Trends

**Trend Analysis:**
- **Direction:** Performance appears to be {trend_direction} over time
- **First Half Average:** {np.mean(first_half):.1%}
- **Second Half Average:** {np.mean(second_half):.1%}

**Extremes:**
- **Best Year:** {years[best_idx]} with {accuracies[best_idx]:.1%} accuracy
- **Worst Year:** {years[worst_idx]} with {accuracies[worst_idx]:.1%} accuracy
- **Range:** {max(accuracies) - min(accuracies):.1%} accuracy spread

**Interpretation:** {'Model shows stable performance across different years.' if max(accuracies) - min(accuracies) < 0.10 else 'Model performance varies significantly by year - investigate anomalies.'}"""
    
    def _generate_consistency_analysis(self, results: List[Dict[str, Any]]) -> str:
        """Analyze model consistency."""
        if not results:
            return """## Consistency Analysis

No results to analyze."""
        
        accuracies = [r['metrics'].get('accuracy', 0) for r in results]
        std_dev = np.std(accuracies)
        
        # NFL-specific consistency rating
        if std_dev < 0.04:
            consistency = "🟢 Exceptional - Unusually stable for NFL prediction"
        elif std_dev < 0.06:
            consistency = "🟢 Strong - Expected professional variance"
        elif std_dev < 0.08:
            consistency = "🟡 Normal - Typical for NFL prediction"
        elif std_dev < 0.10:
            consistency = "🟠 Fair - Moderate year-to-year variation"
        else:
            consistency = "🔴 High Variance - Investigate systematic issues"
        
        return f"""## Consistency Analysis

**Consistency Rating:** {consistency}

**Statistics:**
- **Standard Deviation:** {std_dev:.1%}
- **Coefficient of Variation:** {std_dev / np.mean(accuracies):.1%}
- **Years Within ±5%:** {sum(1 for a in accuracies if abs(a - np.mean(accuracies)) < 0.05)}/{len(results)}

**Assessment:** {'This training window provides reliable predictions across different years.' if std_dev < 0.05 else 'Consider investigating factors causing performance variation.'}"""
    
    def _format_table_helper(self, headers, rows):
        """Helper for markdown table formatting."""
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
    
    def _generate_feature_importance_stability(self, backtest_results: List[Dict[str, Any]]) -> str:
        """
        Analyze feature importance stability across test years.
        
        Critical for backtesting: Shows which features are reliable predictors
        vs year-specific noise.
        
        Args:
            backtest_results: List of training results from each test year
            
        Returns:
            str: Markdown formatted feature stability analysis
        """
        # DIAGNOSTIC: Log input validation
        if self.logger:
            self.logger.debug(f"[DIAG] _generate_feature_importance_stability called with {len(backtest_results) if backtest_results else 0} results")
        
        if not backtest_results or 'model' not in backtest_results[0]:
            if self.logger:
                self.logger.warning(f"[DIAG] Early return: backtest_results empty={not backtest_results}, has_model={'model' in backtest_results[0] if backtest_results else 'N/A'}")
            return ""
        
        # Extract feature importances from each year
        feature_data = defaultdict(list)
        
        for idx, result in enumerate(backtest_results):
            model = result.get('model')
            
            # DIAGNOSTIC: Log model validation
            if self.logger:
                self.logger.debug(f"[DIAG] Year {idx}: model exists={model is not None}, has_feature_importances={hasattr(model, 'feature_importances_') if model else False}")
            
            if not model or not hasattr(model, 'feature_importances_'):
                if self.logger:
                    self.logger.warning(f"[DIAG] Year {idx}: Skipping - model={type(model).__name__ if model else 'None'}")
                continue
            
            # Handle ensemble model (get XGBoost importances)
            if hasattr(model, 'xgboost_model') and hasattr(model, 'tree_features_'):
                feature_names = model.tree_features_
                importances = model.xgboost_model.feature_importances_
                if self.logger:
                    self.logger.debug(f"[DIAG] Year {idx}: Using ensemble XGBoost - {len(feature_names)} features")
            else:
                # Standard model
                feature_names = result.get('X_test', pd.DataFrame()).columns
                importances = model.feature_importances_
                if self.logger:
                    self.logger.debug(f"[DIAG] Year {idx}: Using standard model - {len(feature_names)} features")
            
            # DIAGNOSTIC: Validate feature count match
            if len(feature_names) != len(importances):
                if self.logger:
                    self.logger.error(f"[DIAG] Year {idx}: MISMATCH - {len(feature_names)} feature names vs {len(importances)} importances")
                continue
            
            for feat, imp in zip(feature_names, importances):
                feature_data[feat].append(imp)
        
        if not feature_data:
            if self.logger:
                self.logger.warning(f"[DIAG] No feature data collected after processing {len(backtest_results)} results")
            return ""
        
        # Calculate stability metrics
        stability_stats = []
        for feat, importances in feature_data.items():
            mean_imp = np.mean(importances)
            std_imp = np.std(importances)
            
            # DIAGNOSTIC: Check for edge cases
            if mean_imp <= 0:
                if self.logger:
                    self.logger.warning(f"[DIAG] Feature '{feat}': mean_imp={mean_imp} (non-positive)")
            
            cv = std_imp / mean_imp if mean_imp > 0.001 else 0  # Avoid div by zero
            
            # Classify stability (updated thresholds for NFL context)
            # Low CV = stable importance across years = GOOD for production models
            if std_imp < 1e-6:
                stability = "📌 PINNED"
                note = "Check precision - very small variance"
            elif cv < 0.01:
                stability = "🔒 EXTREMELY STABLE"
                note = "Highly reliable core predictor"
            elif cv < 0.20:
                stability = "✅ STABLE"
                note = "Reliable predictor"
            elif cv < 0.50:
                stability = "⚠️ VARIABLE"
                note = "Context-dependent"
            else:
                stability = "❌ UNSTABLE"
                note = "Unreliable - consider removal"
            
            stability_stats.append({
                'feature': feat,
                'mean_imp': mean_imp,
                'std_imp': std_imp,
                'cv': cv,
                'stability': stability,
                'note': note
            })
        
        # Sort by mean importance
        stability_df = pd.DataFrame(stability_stats).sort_values('mean_imp', ascending=False)
        
        # Build report
        report = ["## Feature Importance Stability Across Years\n"]
        report.append("Which features are consistently predictive vs year-specific?\n")
        
        # Summary counts (updated for new categories)
        pinned_count = sum(1 for s in stability_stats if 'PINNED' in s['stability'])
        extremely_stable_count = sum(1 for s in stability_stats if 'EXTREMELY STABLE' in s['stability'])
        stable_count = sum(1 for s in stability_stats if s['stability'] == '✅ STABLE')
        variable_count = sum(1 for s in stability_stats if 'VARIABLE' in s['stability'])
        unstable_count = sum(1 for s in stability_stats if 'UNSTABLE' in s['stability'])
        
        report.append(f"**Stability Summary:**")
        report.append(f"- 🔒 Extremely Stable Features: {extremely_stable_count} (core predictors)")
        report.append(f"- ✅ Stable Features: {stable_count} (reliable predictors)")
        report.append(f"- ⚠️ Variable Features: {variable_count} (context-dependent)")
        report.append(f"- ❌ Unstable Features: {unstable_count} (consider removal)")
        if pinned_count > 0:
            report.append(f"- 📌 Pinned Features: {pinned_count} (check display precision)\n")
        else:
            report.append("")
        
        # Top 20 features by mean importance
        report.append("### Top 20 Features by Mean Importance\n")
        
        headers = ['Feature', 'Mean Imp', 'Std Dev', 'CV', 'Stability', 'Assessment']
        rows = []
        for _, row in stability_df.head(20).iterrows():
            # Show more precision for very small std values to avoid "0.0000" display
            std_display = f"{row['std_imp']:.6f}" if row['std_imp'] < 0.01 else f"{row['std_imp']:.4f}"
            rows.append([
                row['feature'],
                f"{row['mean_imp']:.4f}",
                std_display,
                f"{row['cv']:.2f}",
                row['stability'],
                row['note']
            ])
        
        report.append(self._format_table_helper(headers, rows))
        report.append("")
        
        # Unstable features requiring attention
        unstable_features = stability_df[stability_df['cv'] >= 0.50].sort_values('mean_imp', ascending=False)
        if len(unstable_features) > 0:
            report.append(f"### ❌ Unstable Features Requiring Review ({len(unstable_features)})\n")
            report.append("These features have high variance across years (CV ≥ 0.50):\n")
            
            for _, row in unstable_features.iterrows():
                report.append(f"- `{row['feature']}`: CV={row['cv']:.2f}, Mean Imp={row['mean_imp']:.4f}")
            report.append("")
        
        return '\n'.join(report)
    
    def _generate_statistical_tests(self, results: List[Dict[str, Any]]) -> str:
        """
        Statistical significance testing for backtest performance.
        
        Tests whether observed accuracy is statistically significant
        vs random chance and break-even thresholds.
        
        Args:
            results: List of training results from each test year
            
        Returns:
            str: Markdown formatted statistical test results
        """
        if not results:
            return ""
        
        accuracies = [r['metrics'].get('accuracy', 0) for r in results]
        n = len(accuracies)
        
        if n < 2:
            return ""  # Need at least 2 years for t-test
        
        mean_acc = np.mean(accuracies)
        std_acc = np.std(accuracies, ddof=1)  # Sample std
        
        # Test 1: vs Random (50%)
        t_stat_random, p_val_random = stats.ttest_1samp(accuracies, 0.50)  # type: ignore[assignment]
        
        # Test 2: vs Break-even (52.4%)
        t_stat_breakeven, p_val_breakeven = stats.ttest_1samp(accuracies, 0.524)  # type: ignore[assignment]
        
        # Test 3: vs Good threshold (58%)
        t_stat_good, p_val_good = stats.ttest_1samp(accuracies, 0.58)  # type: ignore[assignment]
        
        report = ["## Statistical Significance Testing\n"]
        report.append(f"Testing {n} years of backtest results for statistical significance:\n")
        
        # Results table
        headers = ['Hypothesis', 't-statistic', 'p-value', 'Result']
        rows = []
        
        # Test 1
        sig_random = "✅ Significant" if p_val_random < 0.05 else "❌ Not Significant"  # type: ignore[operator]
        rows.append([
            "Accuracy > 50% (Random)",
            f"{t_stat_random:.3f}",
            f"{p_val_random:.4f}",
            sig_random
        ])
        
        # Test 2
        sig_breakeven = "✅ Significant" if p_val_breakeven < 0.05 else "❌ Not Significant"  # type: ignore[operator]
        rows.append([
            "Accuracy > 52.4% (Break-even)",
            f"{t_stat_breakeven:.3f}",
            f"{p_val_breakeven:.4f}",
            sig_breakeven
        ])
        
        # Test 3
        sig_good = "✅ Significant" if p_val_good < 0.05 else "❌ Not Significant"  # type: ignore[operator]
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
        
        if p_val_random < 0.05:  # type: ignore[operator]
            report.append(f"✅ **Performance is statistically better than random** (p={p_val_random:.4f})")
        else:
            report.append(f"⚠️ **Cannot prove performance better than random** (p={p_val_random:.4f})")
        
        if p_val_breakeven < 0.05:  # type: ignore[operator]
            report.append(f"✅ **Performance is statistically profitable** (p={p_val_breakeven:.4f})")
        else:
            report.append(f"⚠️ **Cannot prove profitability** (p={p_val_breakeven:.4f})")
        
        report.append(f"\n**Note:** p-value < 0.05 indicates 95% confidence that results are not due to chance.")
        
        return '\n'.join(report)
    
    def _generate_recommendations(self, results: List[Dict[str, Any]],
                                  train_years: int) -> str:
        """Generate actionable recommendations."""
        if not results:
            return """## Recommendations

Unable to generate recommendations - no successful results."""
        
        accuracies = [r['metrics'].get('accuracy', 0) for r in results]
        avg_accuracy = np.mean(accuracies)
        std_dev = np.std(accuracies)
        
        recommendations = ["""## Recommendations"""]
        
        # NFL-specific performance-based recommendations
        roi = self._calculate_roi(float(avg_accuracy))
        
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


def create_backtest_reporter(logger=None):
    """
    Factory function to create backtest report generator.
    
    Matches pattern from create_report_generator()
    
    Args:
        logger: Optional logger instance
        
    Returns:
        BacktestReportGenerator: Configured backtest reporter
    """
    return BacktestReportGenerator(logger=logger)


__all__ = ['BacktestReportGenerator', 'create_backtest_reporter']