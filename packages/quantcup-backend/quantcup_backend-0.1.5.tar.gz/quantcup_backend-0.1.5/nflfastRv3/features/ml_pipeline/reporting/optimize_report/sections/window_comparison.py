"""
Window Comparison Section Generator

Generates detailed comparison tables and analyses for different training window sizes.
"""

import numpy as np
from typing import Dict, Any, List
from scipy import stats


class WindowComparisonSectionGenerator:
    """
    Generates window size comparison and analysis sections.
    
    Provides detailed comparison tables, optimal window analysis, and diminishing returns analysis.
    """
    
    def __init__(self, logger=None):
        """
        Initialize window comparison generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_comparison_table(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate detailed comparison table with statistical measures.
        
        Args:
            results: List of training results from each window size
            
        Returns:
            str: Formatted comparison table section
        """
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
    
    def generate_optimal_window_analysis(self, results: List[Dict[str, Any]]) -> str:
        """
        Analyze the optimal window configuration with statistical significance.
        
        Args:
            results: List of training results from each window size
            
        Returns:
            str: Formatted optimal window analysis section
        """
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
    
    def generate_diminishing_returns_analysis(self, results: List[Dict[str, Any]]) -> str:
        """
        Analyze diminishing returns as window size increases.
        
        Args:
            results: List of training results from each window size
            
        Returns:
            str: Formatted diminishing returns analysis section
        """
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


__all__ = ['WindowComparisonSectionGenerator']
