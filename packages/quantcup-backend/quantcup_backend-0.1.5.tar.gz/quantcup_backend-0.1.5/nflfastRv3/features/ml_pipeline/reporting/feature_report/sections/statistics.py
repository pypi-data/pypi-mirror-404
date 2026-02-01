"""
Feature Report - Statistics Section

Generates statistical analysis sections:
- Column inventory
- Correlation analysis  
- Variance analysis
- Temporal stability
"""

import pandas as pd
from typing import Dict, Any

from ....feature_sets import FEATURE_REGISTRY


class StatisticsSectionGenerator:
    """
    Generates statistical analysis sections.
    
    Handles column inventory, correlations, variance, and temporal stability.
    """
    
    def __init__(self, logger=None):
        """
        Initialize statistics generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_column_inventory(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed column inventory for all feature sets.
        
        Args:
            results: Feature engineering results dict
        
        Returns:
            str: Formatted column inventory section
        """
        feature_results = results.get('results', {})

        if not feature_results:
            return """## Column Inventory

No feature sets were processed."""

        sections = ["## Column Inventory\n"]

        # Process each feature set
        for feature_name in FEATURE_REGISTRY.keys():
            if feature_name not in feature_results:
                continue

            result = feature_results[feature_name]
            statistics = result.get('statistics', {})

            if not statistics or 'columns' not in statistics:
                continue

            columns = statistics['columns']

            section_parts = [f"### {feature_name.replace('_', ' ').title()}\n"]

            # Create table header
            section_parts.append("| Column | Type | Null % | Unique | Min | Max | Mean |")
            section_parts.append("|--------|------|--------|--------|-----|-----|------|")

            # Add each column (columns is a dict with column names as keys)
            for col_name, col_info in columns.items():
                col_type = col_info.get('dtype', 'unknown')
                null_pct = col_info.get('null_percentage', 0)
                unique = col_info.get('unique_values', 0)
                min_val = col_info.get('min', 'N/A')
                max_val = col_info.get('max', 'N/A')
                mean_val = col_info.get('mean', 'N/A')

                # Format values
                if isinstance(min_val, (int, float)) and not pd.isna(min_val):
                    min_val = f"{min_val:.3f}"
                if isinstance(max_val, (int, float)) and not pd.isna(max_val):
                    max_val = f"{max_val:.3f}"
                if isinstance(mean_val, (int, float)) and not pd.isna(mean_val):
                    mean_val = f"{mean_val:.3f}"

                section_parts.append(f"| `{col_name}` | {col_type} | {null_pct:.1f}% | {unique:,} | {min_val} | {max_val} | {mean_val} |")

            sections.append('\n'.join(section_parts))

        return '\n\n'.join(sections)
    
    def generate_correlation_analysis(self, results: Dict[str, Any]) -> str:
        """
        Generate correlation analysis with target variables.
        
        Args:
            results: Feature engineering results dict
        
        Returns:
            str: Formatted correlation analysis section
        """
        feature_results = results.get('results', {})

        if not feature_results:
            return """## Correlation Analysis

No feature sets were processed."""

        sections = ["## Correlation Analysis\n"]

        # Process each feature set
        for feature_name in FEATURE_REGISTRY.keys():
            if feature_name not in feature_results:
                continue

            result = feature_results[feature_name]
            statistics = result.get('statistics', {})

            if not statistics or 'correlations' not in statistics:
                continue

            correlations = statistics['correlations']
            target_col = correlations.get('target_column', 'unknown')

            section_parts = [f"### {feature_name.replace('_', ' ').title()}\n"]
            section_parts.append(f"**Target Variable:** `{target_col}`\n")

            # Strong positive correlations
            strong_pos = correlations.get('strong_positive', {})
            if strong_pos:
                section_parts.append("**Strong Positive Correlations (>0.15):**")
                for col, corr in sorted(strong_pos.items(), key=lambda x: x[1], reverse=True):
                    section_parts.append(f"- `{col}`: {corr:+.4f}")
                section_parts.append("")

            # Moderate positive correlations
            mod_pos = correlations.get('moderate_positive', {})
            if mod_pos:
                section_parts.append("**Moderate Positive Correlations (0.08-0.15):**")
                for col, corr in sorted(mod_pos.items(), key=lambda x: x[1], reverse=True):
                    section_parts.append(f"- `{col}`: {corr:+.4f}")
                section_parts.append("")

            # Weak positive correlations
            weak_pos = correlations.get('weak_positive', {})
            if weak_pos:
                section_parts.append("**Weak Positive Correlations (0.05-0.08):**")
                for col, corr in sorted(weak_pos.items(), key=lambda x: x[1], reverse=True):
                    section_parts.append(f"- `{col}`: {corr:+.4f}")
                section_parts.append("")

            # Negative correlations
            weak_neg = correlations.get('weak_negative', {})
            mod_neg = correlations.get('moderate_negative', {})
            strong_neg = correlations.get('strong_negative', {})

            if weak_neg or mod_neg or strong_neg:
                section_parts.append("**Negative Correlations:**")
                # Combine all negative correlations
                all_neg = {**weak_neg, **mod_neg, **strong_neg}
                for col, corr in sorted(all_neg.items(), key=lambda x: x[1]):  # Sort ascending (most negative first)
                    strength = "STRONG" if corr < -0.15 else "MODERATE" if corr < -0.08 else "WEAK"
                    section_parts.append(f"- `{col}`: {corr:+.4f} ({strength})")
                section_parts.append("")

            sections.append('\n'.join(section_parts))

        return '\n\n'.join(sections)
    
    def generate_variance_analysis(self, results: Dict[str, Any]) -> str:
        """
        Generate variance analysis for feature informativeness.
        
        Args:
            results: Feature engineering results dict
        
        Returns:
            str: Formatted variance analysis section
        """
        feature_results = results.get('results', {})

        if not feature_results:
            return """## Variance Analysis

No feature sets were processed."""

        sections = ["## Variance Analysis\n"]

        # Process each feature set
        for feature_name in FEATURE_REGISTRY.keys():
            if feature_name not in feature_results:
                continue

            result = feature_results[feature_name]
            statistics = result.get('statistics', {})

            if not statistics or 'variance_analysis' not in statistics:
                continue

            variance_data = statistics['variance_analysis']

            section_parts = [f"### {feature_name.replace('_', ' ').title()}\n"]

            # Highest variance features
            highest_var = variance_data.get('highest_variance', {})
            if highest_var:
                section_parts.append("**Highest Variance Features (Most Informative):**")
                section_parts.append("")
                section_parts.append("| Feature | Variance | Std Dev |")
                section_parts.append("|---------|----------|---------|")

                for col, var in list(highest_var.items())[:10]:  # Top 10
                    std = var ** 0.5
                    section_parts.append(f"| `{col}` | {var:.6f} | {std:.4f} |")

                section_parts.append("")

            # Lowest variance features
            lowest_var = variance_data.get('lowest_variance', {})
            if lowest_var:
                section_parts.append("**Lowest Variance Features (Least Informative):**")
                section_parts.append("")
                section_parts.append("| Feature | Variance | Std Dev |")
                section_parts.append("|---------|----------|---------|")

                for col, var in list(lowest_var.items())[:5]:  # Bottom 5
                    std = var ** 0.5
                    section_parts.append(f"| `{col}` | {var:.6f} | {std:.4f} |")

                section_parts.append("")

            # Zero variance features
            zero_var = variance_data.get('zero_variance', [])
            if zero_var:
                section_parts.append(f"**Zero Variance Features ({len(zero_var)} features):**")
                section_parts.append("These features have no variation and provide no information:")
                for col in zero_var[:10]:  # Show first 10
                    section_parts.append(f"- `{col}`")
                if len(zero_var) > 10:
                    section_parts.append(f"*... and {len(zero_var) - 10} more*")
                section_parts.append("")

            sections.append('\n'.join(section_parts))

        return '\n\n'.join(sections)
    
    def generate_temporal_stability(self, results: Dict[str, Any]) -> str:
        """
        Generate temporal stability analysis across seasons.
        
        Args:
            results: Feature engineering results dict
        
        Returns:
            str: Formatted temporal stability section
        """
        feature_results = results.get('results', {})

        if not feature_results:
            return """## Temporal Stability

No feature sets were processed."""

        sections = ["## Temporal Stability\n"]

        # Process each feature set
        for feature_name in FEATURE_REGISTRY.keys():
            if feature_name not in feature_results:
                continue

            result = feature_results[feature_name]
            statistics = result.get('statistics', {})

            if not statistics or 'temporal_stability' not in statistics:
                continue

            stability_data = statistics['temporal_stability']

            section_parts = [f"### {feature_name.replace('_', ' ').title()}\n"]

            section_parts.append("**Season-over-Season Stability (Coefficient of Variation):**")
            section_parts.append("")

            # stability_data is dict with column names as keys, each containing stability info
            for column_name, stability_info in stability_data.items():
                cv = stability_info.get('cv_percentage', 0)
                stability_level = stability_info.get('stability', 'UNKNOWN')
                section_parts.append(f"- `{column_name}`: {cv:.1f}% ({stability_level})")

            sections.append('\n'.join(section_parts))

        return '\n\n'.join(sections)


__all__ = ['StatisticsSectionGenerator']
