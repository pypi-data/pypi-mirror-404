"""
Stability Section Generator for Backtest Reports

Generates feature importance stability analysis section.
"""

import pandas as pd
from typing import Dict, Any, List

from ..calculators import StabilityCalculator


class StabilitySectionGenerator:
    """
    Generates feature importance stability analysis section.
    
    Responsibilities:
    - Feature importance stability across years
    - Identification of reliable vs unreliable features
    """
    
    def __init__(self, logger=None):
        """
        Initialize stability section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.calculator = StabilityCalculator(logger=logger)
    
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
        Generate feature importance stability analysis section.
        
        Critical for backtesting: Shows which features are reliable predictors
        vs year-specific noise.
        
        Args:
            backtest_results: List of training results from each test year
            kwargs: Additional arguments (ignored)
            
        Returns:
            str: Markdown formatted feature stability analysis
        """
        # Calculate stability metrics
        stability_df = self.calculator.calculate_feature_stability(backtest_results)
        
        if stability_df is None or len(stability_df) == 0:
            return ""
        
        # Build report
        report = ["## Feature Importance Stability Across Years\n"]
        report.append("Which features are consistently predictive vs year-specific?\n")
        
        # Summary counts
        pinned_count = sum(1 for _, row in stability_df.iterrows() if 'PINNED' in row['stability'])
        extremely_stable_count = sum(1 for _, row in stability_df.iterrows() 
                                     if 'EXTREMELY STABLE' in row['stability'])
        stable_count = sum(1 for _, row in stability_df.iterrows() if row['stability'] == '✅ STABLE')
        variable_count = sum(1 for _, row in stability_df.iterrows() if 'VARIABLE' in row['stability'])
        unstable_count = sum(1 for _, row in stability_df.iterrows() if 'UNSTABLE' in row['stability'])
        
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


__all__ = ['StabilitySectionGenerator']
