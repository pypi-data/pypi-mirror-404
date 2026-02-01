"""
Diagnostics Report Generator.
Generates comprehensive Markdown reports for model diagnostics.
"""
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from nflfastRv3.features.analytics_suite.reporting.diagnostics import (
    calculate_stability_ratio,
    perform_statistical_tests,
    check_training_growth_linearity,
    analyze_feature_correlations,
    analyze_misses
)


def create_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Generate a Markdown table.
    
    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of cell values
        
    Returns:
        Formatted Markdown table string
    """
    if not headers:
        return ""
        
    # Create header row
    header_row = "| " + " | ".join(headers) + " |"
    
    # Create separator row
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    
    # Create data rows
    data_rows = []
    for row in rows:
        # Ensure row has same length as headers (pad with empty strings if needed)
        padded_row = row + [""] * (len(headers) - len(row))
        # Convert all values to strings
        str_row = [str(cell) if cell is not None else "" for cell in padded_row]
        data_rows.append("| " + " | ".join(str_row) + " |")
        
    return "\n".join([header_row, separator_row] + data_rows)


def create_section(title: str, content: str, level: int = 2) -> str:
    """
    Create a formatted Markdown section.
    
    Args:
        title: Section title
        content: Section content
        level: Header level (1-6)
        
    Returns:
        Formatted section string
    """
    hashes = "#" * max(1, min(6, level))
    return f"{hashes} {title}\n\n{content}\n"


def format_metric(value: Optional[Union[float, int]], format_str: str = "{:.3f}") -> str:
    """
    Safely format a metric value.
    
    Args:
        value: Numeric value to format
        format_str: Format string (e.g., "{:.1%}")
        
    Returns:
        Formatted string or "N/A" if value is None
    """
    if value is None:
        return "N/A"
    try:
        return format_str.format(value)
    except (ValueError, TypeError):
        return str(value)


class DiagnosticsReportGenerator:
    """
    Generates detailed diagnostic reports for model validation.
    Achieves feature parity with validate_weekly.py comprehensive reporting.
    """
    
    def __init__(self, output_dir: str = "reports/analytics"):
        """
        Initialize diagnostics report generator with domain-based output directory.
        
        Args:
            output_dir: Directory to save reports (default: 'reports/analytics' for domain-based organization)
        
        Note:
            TODO: If generating multiple artifact types (e.g., diagnostics CSV, plots),
            consider using timestamped subfolders: 'reports/analytics/analysis_{timestamp}' to group
            related artifacts. See scripts/analyze_pbp_odds_data_v4.py for reference.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_timestamp(self) -> str:
        """Generate standard timestamp string."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def save_report(self, content: str, filename: str) -> Path:
        """
        Save report content to file.
        
        Args:
            content: Report content (Markdown/HTML)
            filename: Target filename
            
        Returns:
            Path to saved file
        """
        file_path = self.output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def generate_report(self, data: Dict[str, Any], **kwargs) -> Path:
        """
        Generate full diagnostics report with comprehensive sections.
        
        Args:
            data: Dictionary containing:
                - weekly_metrics: List[Dict] of weekly results
                - metadata: Run metadata dict
                
        Returns:
            Path to saved report
        """
        # Convert weekly_metrics to DataFrame
        weekly_metrics = data.get('weekly_metrics', [])
        if isinstance(weekly_metrics, list):
            results_df = pd.DataFrame(weekly_metrics)
        else:
            results_df = weekly_metrics
            
        metadata = data.get('metadata', kwargs.get('metadata', {}))
        timestamp = self.generate_timestamp()
        
        # Calculate core metrics
        acc_mean = results_df['accuracy'].mean()
        acc_std = results_df['accuracy'].std()
        acc_min = results_df['accuracy'].min()
        acc_max = results_df['accuracy'].max()
        acc_range = acc_max - acc_min
        avg_games = results_df['test_size'].mean() if 'test_size' in results_df else results_df.get('total_games', pd.Series([0])).mean()
        
        stability_ratio = calculate_stability_ratio(acc_mean, acc_std, avg_games)
        
        # Statistical tests
        random_test = perform_statistical_tests(results_df['accuracy'].tolist(), 0.5)
        home_baseline = results_df['actual_home_win_rate'].mean() if 'actual_home_win_rate' in results_df else 0.5
        baseline_test = perform_statistical_tests(results_df['accuracy'].tolist(), home_baseline)
        
        # Extract feature statistics
        feature_stats = self._extract_feature_stats(weekly_metrics)
        
        # Analyze correlations and misses
        correlation_stats = analyze_feature_correlations(weekly_metrics)
        miss_df = analyze_misses(weekly_metrics)
        
        # Calculate grades
        stability_grade = self._grade_stability(stability_ratio)
        weeks_below_random = (results_df['auc'] < 0.5).sum()
        reliability_grade = "A" if weeks_below_random == 0 else "B" if weeks_below_random <= 1 else "F"
        weeks_beating_home = results_df.get('beats_always_home', results_df['accuracy'] > home_baseline).sum()
        baseline_pct = weeks_beating_home / len(results_df)
        baseline_grade = "A" if baseline_pct >= 0.9 else "B" if baseline_pct >= 0.75 else "F"
        overall_assessment = self._get_overall_assessment(stability_ratio, results_df)
        
        # AUC and Bias metrics
        auc_min = results_df['auc'].min()
        auc_max = results_df['auc'].max()
        bias_min = results_df['home_win_bias'].min() if 'home_win_bias' in results_df else 0.0
        bias_max = results_df['home_win_bias'].max() if 'home_win_bias' in results_df else 0.0
        bias_range = bias_max - bias_min
        
        # Build report
        sections = []
        
        # Header
        sections.append(self._create_header(metadata))
        
        # Executive Summary
        sections.append(self._create_executive_summary(
            acc_mean, stability_ratio, stability_grade, results_df, 
            reliability_grade, weeks_beating_home, baseline_pct, baseline_grade,
            overall_assessment, acc_range, bias_min, bias_max, bias_range, weeks_below_random
        ))
        
        # Week-by-Week Performance
        sections.append(self._create_weekly_performance(results_df, metadata))
        
        # Statistical Analysis
        sections.append(self._create_statistical_analysis(
            results_df, acc_mean, acc_std, stability_ratio, random_test, 
            baseline_test, home_baseline, auc_min, auc_max, weeks_below_random,
            bias_min, bias_max, bias_range
        ))
        
        # Feature Importance Analysis
        if feature_stats:
            sections.append(self._create_feature_importance(feature_stats, results_df))
            sections.append(self._create_feature_stability(feature_stats))
            sections.append(self._create_feature_variance(feature_stats))
        
        # Feature Correlation Analysis
        if correlation_stats:
            sections.append(self._create_correlation_analysis(
                correlation_stats, results_df, feature_stats
            ))
        
        # Miss Analysis
        if miss_df is not None and not miss_df.empty:
            sections.append(self._create_miss_analysis(miss_df))
        
        # Historical Comparison
        sections.append(self._create_historical_comparison(
            metadata, acc_mean, acc_range, weeks_beating_home, len(results_df), results_df
        ))
        
        # Recommendations
        unstable_count = sum(1 for _, s in feature_stats.items() if s['cv'] >= 0.5) if feature_stats else 0
        sections.append(self._create_recommendations(overall_assessment, unstable_count))
        
        # Footer
        sections.append(f"\n---\n\n*Generated by DiagnosticsReportGenerator on {metadata.get('run_date', 'N/A')}*\n")
        
        # Save report
        filename = f"{metadata.get('test_season', 'unknown')}_validation_{timestamp}.md"
        return self.save_report("\n".join(sections), filename)

    def _extract_feature_stats(self, weekly_metrics: List[Dict]) -> Optional[Dict]:
        """Extract feature importance statistics from weekly results."""
        feature_importance_by_week = {}
        
        for r in weekly_metrics:
            if 'feature importance' in r and r['feature_importance']:
                week_dict = {item['feature']: item['importance'] for item in r['feature_importance']}
                feature_importance_by_week[r['week']] = week_dict
        
        if not feature_importance_by_week:
            return None
        
        # Calculate stats across weeks
        all_features = set()
        for week_features in feature_importance_by_week.values():
            all_features.update(week_features.keys())
        
        feature_stats = {}
        for feature in all_features:
            importances = [
                week_features.get(feature, 0)
                for week_features in feature_importance_by_week.values()
            ]
            mean_imp = np.mean(importances)
            feature_stats[feature] = {
                'mean': mean_imp,
                'std': np.std(importances),
                'min': np.min(importances),
                'max': np.max(importances),
                'cv': np.std(importances) / mean_imp if mean_imp > 0 else 0
            }
        
        return feature_stats

    def _create_header(self, metadata: Dict) -> str:
        """Create report header."""
        header = f"# {metadata.get('test_season', 'Unknown')} Season Validation Report\n\n"
        header += f"**Run Date:** {metadata.get('run_date', 'N/A')}  \n"
        header += f"**Run ID:** {metadata.get('run_id', 'N/A')}  \n"
        header += f"**Model:** {metadata.get('model_type', 'Unknown')} {metadata.get('model_version', '')}  \n"
        header += f"**Training:** {metadata.get('training_seasons', 'Unknown')}  \n"
        header += f"**Testing:** {metadata.get('test_season', 'Unknown')} Weeks 1-{metadata.get('max_week', 'Unknown')}\n\n"
        header += "---\n\n"
        return header

    def _create_executive_summary(self, acc_mean, stability_ratio, stability_grade, 
                                   results_df, reliability_grade, weeks_beating_home,
                                   baseline_pct, baseline_grade, overall_assessment,
                                   acc_range, bias_min, bias_max, bias_range, weeks_below_random) -> str:
        """Create executive summary section."""
        summary_rows = [
            ["Mean Accuracy", format_metric(acc_mean, "{:.1%}"), "-"],
            ["Stability Ratio", f"{stability_ratio:.2f}x", stability_grade],
            ["Reliability (AUC)", format_metric(results_df['auc'].mean()), reliability_grade],
            ["Weeks Beating Baseline", f"{weeks_beating_home}/{len(results_df)} ({baseline_pct:.1%})", baseline_grade],
            ["Overall Assessment", overall_assessment, "-"]
        ]
        
        content = create_table(["Metric", "Value", "Grade"], summary_rows)
        content += "\n\n### Key Findings\n"
        
        weeks_beating_random = (results_df.get('beats_random', results_df['accuracy'] > 0.5)).sum()
        content += f"- {'✓' if weeks_beating_random == len(results_df) else '⚠️'} Model beats random baseline in {weeks_beating_random}/{len(results_df)} weeks ({weeks_beating_random/len(results_df):.1%})\n"
        
        if stability_ratio < 1.25:
            content += f"- ✓ High stability detected (Ratio: {stability_ratio:.2f}x)\n"
        elif stability_ratio < 1.50:
            content += f"- ⚠️ Moderate stability detected (Ratio: {stability_ratio:.2f}x)\n"
        else:
            content += f"- ❌ Low stability detected (Ratio: {stability_ratio:.2f}x)\n"
        
        content += f"- {'✓' if weeks_below_random == 0 else '❌'} {weeks_below_random if weeks_below_random > 0 else 'No'} anti-predictive weeks (AUC < 0.5)\n"
        content += f"- {'⚠️' if abs(bias_range) > 0.15 else '✓'} Home win bias ranges from {bias_min:+.1%} to {bias_max:+.1%}\n"
        
        return create_section("Executive Summary", content)

    def _create_weekly_performance(self, results_df: pd.DataFrame, metadata: Dict) -> str:
        """Create week-by-week performance table."""
        headers = ["Week", "Train Size", "Test Size", "Accuracy", "AUC", "Home Bias", "Beats Home", "Improvement"]
        rows = []
        
        for _, row in results_df.iterrows():
            beats_home = "✓" if row.get('beats_always_home', False) else "✗"
            rows.append([
                int(row['week']),
                f"{int(row.get('train_size', 0)):,}",
                int(row.get('test_size', row.get('total_games', 0))),
                format_metric(row['accuracy'], "{:.1%}"),
                format_metric(row['auc']),
                format_metric(row.get('home_win_bias', 0.0), "{:+.1%}"),
                beats_home,
                format_metric(row.get('improvement_over_home', 0.0), "{:+.1%}")
            ])
        
        content = create_table(headers, rows)
        
        # Add training size progression
        if len(results_df) > 1 and 'train_size' in results_df:
            content += f"\n\n**Training Size Progression:**\n"
            content += f"- Week 1 (baseline): {int(results_df.iloc[0]['train_size']):,} games\n"
            content += f"- Week {metadata.get('max_week', len(results_df))} (final): {int(results_df.iloc[-1]['train_size']):,} games  \n"
            total_growth = int(results_df.iloc[-1]['train_size'] - results_df.iloc[0]['train_size'])
            content += f"- Total growth: {total_growth:,} games\n"
        
        return create_section("Week-by-Week Performance", content)

    def _create_statistical_analysis(self, results_df, acc_mean, acc_std, stability_ratio,
                                     random_test, baseline_test, home_baseline,
                                     auc_min, auc_max, weeks_below_random,
                                     bias_min, bias_max, bias_range) -> str:
        """Create statistical analysis section."""
        content = "### Accuracy Statistics\n"
        content += f"- **Range:** {results_df['accuracy'].min():.1%} - {results_df['accuracy'].max():.1%}\n"
        content += f"- **Mean:** {acc_mean:.1%}\n"
        content += f"- **Std Dev (Observed):** {acc_std:.1%}\n"
        content += f"- **Stability Ratio:** {stability_ratio:.2f}x (Observed / Theoretical)\n"
        content += f"- **Coefficient of Variation:** {(acc_std / acc_mean):.2%}\n\n"
        
        content += "**Statistical Tests:**\n"
        content += f"- Accuracy vs Random (50%): t={random_test['t_stat']:.3f}, p={random_test['p_value']:.4f}"
        if random_test['p_value'] < 0.05:
            content += f" → {'✓ Significantly better' if acc_mean > 0.5 else '❌ Significantly worse'} than random\n"
        else:
            content += " → Not significantly different from random\n"
        
        content += f"- Accuracy vs Always Home ({home_baseline:.1%}): t={baseline_test['t_stat']:.3f}, p={baseline_test['p_value']:.4f}"
        if baseline_test['p_value'] < 0.05:
            content += f" → {'✓ Significantly better' if acc_mean > home_baseline else '❌ Significantly worse'} than baseline\n"
        else:
            content += " → Not significantly different from baseline\n"
        
        content += "\n### AUC-ROC Statistics\n"
        content += f"- **Range:** {auc_min:.3f} - {auc_max:.3f}\n"
        content += f"- **Mean:** {results_df['auc'].mean():.3f}\n"
        content += f"- **Weeks with AUC < 0.5:** {weeks_below_random} ({weeks_below_random/len(results_df):.1%})\n\n"
        
        content += "### Home Win Bias\n"
        content += f"- **Range:** {bias_min:+.1%} to {bias_max:+.1%}\n"
        content += f"- **Swing:** {bias_range * 100:.1f} percentage points\n"
        content += f"- **Mean:** {results_df.get('home_win_bias', pd.Series([0.0])).mean():+.1%}\n"
        
        return create_section("Statistical Analysis", content)

    def _create_feature_importance(self, feature_stats: Dict, results_df: pd.DataFrame) -> str:
        """Create feature importance analysis section."""
        sorted_features = sorted(feature_stats.items(), key=lambda x: x[1]['mean'], reverse=True)
        
        content = "### Top 15 Most Important Features\n\n"
        headers = ["Rank", "Feature", "Mean", "Std Dev", "Min", "Max", "CV", "Status"]
        rows = []
        
        for i, (feature, stats) in enumerate(sorted_features[:15], 1):
            cv = stats['cv']
            status = "FROZEN" if cv < 0.01 else "STABLE" if cv < 0.3 else "VARIABLE" if cv < 0.5 else "UNSTABLE"
            rows.append([
                i, feature, f"{stats['mean']:.4f}", f"{stats['std']:.4f}",
                f"{stats['min']:.4f}", f"{stats['max']:.4f}", f"{cv:.2f}", status
            ])
        
        content += create_table(headers, rows)
        
        # Bottom 15
        content += "\n### Bottom 15 Least Important Features\n\n"
        rows = []
        total_features = len(sorted_features)
        start_rank = max(16, total_features - 14)
        
        for i, (feature, stats) in enumerate(sorted_features[-15:], start_rank):
            cv = stats['cv']
            status = "FROZEN" if cv < 0.01 else "STABLE" if cv < 0.3 else "VARIABLE" if cv < 0.5 else "UNSTABLE"
            rows.append([
                i, feature, f"{stats['mean']:.4f}", f"{stats['std']:.4f}",
                f"{stats['min']:.4f}", f"{stats['max']:.4f}", f"{cv:.2f}", status
            ])
        
        content += create_table(headers, rows)
        
        return create_section("Feature Importance Analysis", content)

    def _create_feature_stability(self, feature_stats: Dict) -> str:
        """Create feature stability assessment section."""
        frozen_count = sum(1 for _, s in feature_stats.items() if s['cv'] < 0.01)
        stable_count = sum(1 for _, s in feature_stats.items() if 0.01 <= s['cv'] < 0.3)
        variable_count = sum(1 for _, s in feature_stats.items() if 0.3 <= s['cv'] < 0.5)
        unstable_count = sum(1 for _, s in feature_stats.items() if s['cv'] >= 0.5)
        total = len(feature_stats)
        
        content = "### Stability Distribution\n\n"
        headers = ["Category", "Count", "Percentage", "Description"]
        rows = [
            ["FROZEN (CV < 0.01)", frozen_count, f"{frozen_count/total:.1%}", "❌ Indicates overfitting"],
            ["STABLE (0.01-0.3)", stable_count, f"{stable_count/total:.1%}", "✓ Healthy variation"],
            ["VARIABLE (0.3-0.5)", variable_count, f"{variable_count/total:.1%}", "⚠️ High variation"],
            ["UNSTABLE (CV ≥ 0.5)", unstable_count, f"{unstable_count/total:.1%}", "❌ Too unstable"]
        ]
        
        content += create_table(headers, rows)
        
        if frozen_count == 0:
            content += "\n**Assessment:** ✓ No frozen features - walk-forward validation working correctly!\n"
        else:
            content += f"\n**Assessment:** ⚠️ {frozen_count} frozen features detected - may indicate overfitting\n"
        
        if unstable_count > 0:
            content += "\n### Unstable Features Requiring Review\n\n"
            content += "The following features show high variance (CV ≥ 0.5) and may need refinement:\n\n"
            
            sorted_features = sorted(feature_stats.items(), key=lambda x: x[1]['mean'], reverse=True)
            unstable_features = [(f, s) for f, s in sorted_features if s['cv'] >= 0.5]
            
            for i, (feature, stats) in enumerate(unstable_features[:10], 1):
                content += f"{i}. **{feature}** (CV={stats['cv']:.2f}) - Range: [{stats['min']:.4f}, {stats['max']:.4f}]\n"
            
            content += "\n**Recommendations:**\n"
            content += "- Week-specific patterns not generalizable\n"
            content += "- Small sample size effects\n"
            content += "- Consider feature engineering improvements or removal\n"
        
        return create_section("Feature Stability Assessment", content)

    def _create_feature_variance(self, feature_stats: Dict) -> str:
        """Create feature variance analysis section."""
        headers = ["Feature", "Variance Across Weeks", "Interpretation"]
        rows = []
        
        variance_sorted = sorted(feature_stats.items(), key=lambda x: x[1]['std']**2, reverse=True)[:10]
        
        for feature, stats in variance_sorted:
            variance = stats['std'] ** 2
            interp = "Very high - unreliable" if variance > 0.001 else "High - week-dependent" if variance > 0.0005 else "Low - consistent importance"
            rows.append([feature, f"{variance:.5f}", interp])
        
        return create_section("Feature Variance Analysis", create_table(headers, rows))

    def _create_correlation_analysis(self, correlation_stats: Dict, results_df: pd.DataFrame, 
                                     feature_stats: Optional[Dict]) -> str:
        """Create comprehensive correlation analysis section."""
        sorted_corrs = sorted(correlation_stats.items(), key=lambda x: abs(x[1]['mean_correlation']), reverse=True)
        
        content = "### Correlation with Game Outcomes\n\n"
        content += "Measures actual predictive power (separate from XGBoost importance).\n\n"
        
        headers = ["Rank", "Feature", "Mean Corr", "Std Dev", "Range", "Weeks Sig", "Power"]
        rows = []
        
        for i, (feature, stats) in enumerate(sorted_corrs[:20], 1):
            rows.append([
                i, feature, f"{stats['mean_correlation']:+.3f}",
                f"{stats['std_correlation']:.3f}",
                f"[{stats['min_correlation']:+.3f}, {stats['max_correlation']:+.3f}]",
                f"{stats['weeks_significant']}/{len(results_df)}",
                stats['predictive_power']
            ])
        
        content += create_table(headers, rows)
        
        content += "\n**Interpretation:**\n"
        content += "- **Mean Corr**: Average correlation with home wins (higher = more predictive)\n"
        content += "- **Std Dev**: Consistency across weeks (lower = more stable)\n"
        content += "- **Weeks Sig**: Weeks with |correlation| > 0.1 (meaningful signal)\n"
        content += "- **Power**: STRONG (>0.15), MODERATE (0.08-0.15), WEAK (0.05-0.08), NONE (<0.05)\n\n"
        
        # Correlation vs Importance Comparison
        if feature_stats:
            content += "### Correlation vs Importance Comparison\n\n"
            content += "Features with HIGH importance but LOW correlation may indicate:\n"
            content += "- Interaction effects (feature works in combination with others)\n"
            content += "- Non-linear relationships\n"
            content += "- Overfitting to training data\n\n"
            
            headers = ["Feature", "XGBoost Importance", "Correlation", "Discrepancy"]
            rows = []
            
            discrepancies = []
            for feature in feature_stats.keys():
                if feature in correlation_stats:
                    importance = feature_stats[feature]['mean']
                    correlation = abs(correlation_stats[feature]['mean_correlation'])
                    
                    if importance > 0.02 and correlation < 0.08:
                        discrepancies.append((feature, importance, correlation_stats[feature]['mean_correlation']))
            
            discrepancies.sort(key=lambda x: x[1], reverse=True)
            
            for feature, importance, correlation in discrepancies[:10]:
                status = "⚠️ HIGH IMPORTANCE, LOW CORRELATION" if importance > 0.04 else "⚠️ Moderate discrepancy"
                rows.append([feature, f"{importance:.4f}", f"{correlation:+.3f}", status])
            
            if not discrepancies:
                rows.append(["*No significant discrepancies found*", "-", "-", "✓ Good alignment"])
            
            content += create_table(headers, rows) + "\n\n"
        
        # Injury Feature Analysis
        injury_features = [f for f in correlation_stats.keys() if 'injury' in f.lower() or 'qb_available' in f.lower()]
        
        if injury_features:
            content += "### Injury Feature Performance\n\n"
            headers = ["Feature", "Mean Corr", "Importance", "Status", "Recommendation"]
            rows = []
            
            for feature in injury_features:
                corr_stats = correlation_stats[feature]
                importance = feature_stats.get(feature, {}).get('mean', 0.0) if feature_stats else 0.0
                power = corr_stats['predictive_power']
                
                recommendation = "❌ REMOVE" if power == "NONE" else "⚠️ INVESTIGATE" if power == "WEAK" else "✓ KEEP"
                
                rows.append([
                    feature, f"{corr_stats['mean_correlation']:+.3f}",
                    f"{importance:.4f}", power, recommendation
                ])
            
            content += create_table(headers, rows)
            
            content += "\n**Assessment:**\n"
            none_count = sum(1 for f in injury_features if correlation_stats[f]['predictive_power'] == "NONE")
            
            if none_count == len(injury_features):
                content += "- ❌ ALL injury features show ZERO predictive power\n"
                content += "- Model ignores these features in favor of rolling performance metrics\n"
                content += "- **Recommendation: Remove all injury features from feature set**\n"
            elif none_count > 0:
                content += f"- ⚠️ {none_count}/{len(injury_features)} injury features show no predictive power\n"
                content += "- Consider removing low-performing injury features\n"
            else:
                content += "- ✓ Injury features show some predictive power\n"
        
        return create_section("Feature Correlation Analysis", content)

    def _create_miss_analysis(self, miss_df: pd.DataFrame) -> str:
        """Create miss analysis section."""
        content = "Analysis of incorrect predictions to identify patterns in model failures.\n\n"
        content += f"**Total Misses:** {len(miss_df)}\n"
        content += f"**Average Confidence on Misses:** {miss_df['confidence'].mean():.1%}\n\n"
        
        # High confidence misses
        high_conf_misses = miss_df[miss_df['confidence'] > 0.7]
        if not high_conf_misses.empty:
            content += "### ⚠️ High Confidence Misses (>70%)\n\n"
            headers = ["Week", "Game", "Pred", "Actual", "Conf", "Top Factor"]
            rows = []
            
            for _, row in high_conf_misses.sort_values('confidence', ascending=False).head(10).iterrows():
                game_str = f"{row['away_team']} @ {row['home_team']}"
                rows.append([
                    row['week'], game_str, row['predicted_winner'],
                    row['actual_winner'], f"{row['confidence']:.1%}",
                    row['top_factor_1']
                ])
            
            content += create_table(headers, rows)
        
        return create_section("Miss Analysis", content)

    def _create_historical_comparison(self, metadata: Dict, acc_mean: float, 
                                      acc_range: float, weeks_beating_home: int,
                                      total_weeks: int, results_df: pd.DataFrame) -> str:
        """Create historical comparison section."""
        test_year = metadata.get('test_season', 'Unknown')
        
        headers = ["Metric", "Historical (2023)", f"Current ({test_year})", "Change"]
        rows = [
            ["Mean Accuracy", "63.8%", f"{acc_mean:.1%}", 
             f"{(acc_mean - 0.638):+.1%} {'✓' if acc_mean > 0.638 else '⚠️'}"],
            ["Accuracy Range", "37.1 pp", f"{acc_range * 100:.1f} pp",
             f"{(acc_range * 100 - 37.1):+.1f} pp {'✓' if acc_range < 0.371 else '⚠️'}"],
            ["Weeks Beating Home", "66.7%", f"{weeks_beating_home/total_weeks:.1%}",
             f"{(weeks_beating_home/total_weeks - 0.667):+.1%} {'✓' if weeks_beating_home/total_weeks > 0.667 else '⚠️'}"],
            ["Mean AUC", "0.638", f"{results_df['auc'].mean():.3f}",
             f"{(results_df['auc'].mean() - 0.638):+.3f} {'✓' if results_df['auc'].mean() > 0.638 else '⚠️'}"]
        ]
        
        content = create_table(headers, rows)
        
        if acc_range < 0.371:
            content += "\n**Assessment:** ✓ IMPROVED - Stability improved compared to historical baseline\n"
        else:
            content += "\n**Assessment:** ⚠️ SIMILAR - Stability comparable to historical baseline\n"
        
        return create_section("Comparison to Historical Performance", content)

    def _create_recommendations(self, overall_assessment: str, unstable_count: int) -> str:
        """Create recommendations section."""
        content = "### Immediate Actions\n"
        
        if overall_assessment == "✓ PRODUCTION READY":
            content += "1. ✓ **Deploy to Production** - Model shows excellent performance\n"
        elif overall_assessment == "⚠️ NEEDS MONITORING":
            content += "1. ⚠️ **Deploy with Monitoring** - Model shows acceptable performance but requires monitoring\n"
        else:
            content += "1. ❌ **Do Not Deploy** - Model requires improvements before production\n"
        
        if unstable_count > 0:
            content += f"2. ⚠️ **Monitor Unstable Features** - Track {unstable_count} high-variance features weekly\n"
        
        content += "3. ⚠️ **Review Feature Correlations** - Consider removing redundant features\n\n"
        
        content += "### Future Improvements\n"
        if unstable_count > 0:
            content += "1. Investigate unstable features (CV ≥ 0.5) for potential removal\n"
        content += "2. Add feature interaction terms for top 5 features\n"
        content += "3. Implement ensemble methods to reduce variance\n"
        content += "4. Collect more data for low-sample features\n"
        
        return create_section("Recommendations", content)

    def _grade_stability(self, ratio: float) -> str:
        """Grade stability ratio."""
        if ratio < 1.10: return "A (Excellent)"
        if ratio < 1.25: return "B (Good)"
        if ratio < 1.50: return "C (Moderate)"
        return "F (Unstable)"

    def _get_overall_assessment(self, stability_ratio: float, results_df: pd.DataFrame) -> str:
        """Get overall assessment."""
        if stability_ratio < 1.25 and results_df['auc'].mean() > 0.55:
            return "✓ PRODUCTION READY"
        if stability_ratio > 1.50:
            return "❌ NOT PRODUCTION READY"
        return "⚠️ NEEDS MONITORING"