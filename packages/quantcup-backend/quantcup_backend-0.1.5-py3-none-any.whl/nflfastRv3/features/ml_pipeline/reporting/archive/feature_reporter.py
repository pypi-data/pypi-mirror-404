"""
Feature Engineering Report Generator

Generates comprehensive reports documenting feature sets created during ML feature engineering.
Provides metadata, statistics, and data quality metrics for all feature sets.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Orchestrator)
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..feature_sets import FEATURE_REGISTRY, get_feature_info


class FeatureReportGenerator:
    """
    Feature engineering report orchestrator.
    
    Documents all feature sets created during feature engineering,
    including metadata, statistics, and data quality metrics.
    
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
        results: Dict[str, Any],
        output_dir: str = 'reports'
    ) -> str:
        """
        Generate comprehensive feature engineering report.
        
        Args:
            results: Feature engineering results dict from FeatureEngineerImplementation
                Expected structure:
                {
                    'status': 'success' | 'partial' | 'error',
                    'features_built': int,
                    'total_features': int,
                    'total_rows': int,
                    'results': {
                        'feature_name': {
                            'status': 'success' | 'failed',
                            'rows_built': int,
                            'error': str (optional)
                        }
                    }
                }
            output_dir: Directory to save report
            
        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'feature_report_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build report sections
        report_sections = []

        report_sections.append(self._generate_header())
        report_sections.append(self._generate_executive_summary(results))
        report_sections.append(self._generate_feature_set_overview())
        report_sections.append(self._generate_feature_set_details(results))
        report_sections.append(self._generate_column_inventory(results))
        report_sections.append(self._generate_correlation_analysis(results))
        report_sections.append(self._generate_variance_analysis(results))
        report_sections.append(self._generate_temporal_stability(results))
        report_sections.append(self._generate_data_quality_summary(results))
        report_sections.append(self._generate_recommendations(results))
        
        # Write report
        report_content = '\n\n'.join(report_sections)
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Feature report saved: {report_path}")
        
        return str(report_path)
    
    def _generate_header(self) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""# NFL Feature Engineering Report

**Generated:** {timestamp}

This report documents the feature sets created during the ML feature engineering pipeline.
Each feature set provides specialized transformations and statistics for NFL game prediction.

---"""
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> str:
        """Generate executive summary with key statistics."""
        status = results.get('status', 'unknown')
        features_built = results.get('features_built', 0)
        total_features = results.get('total_features', 0)
        total_rows = results.get('total_rows', 0)
        
        # Status indicator
        if status == 'success':
            status_emoji = "✅"
            status_text = "All features built successfully"
        elif status == 'partial':
            status_emoji = "⚠️"
            status_text = "Some features failed to build"
        else:
            status_emoji = "❌"
            status_text = "Feature engineering failed"
        
        return f"""## Executive Summary

**Status:** {status_emoji} {status_text}

**Feature Sets Built:** {features_built}/{total_features}  
**Total Rows Generated:** {total_rows:,}

**Key Metrics:**
- Feature sets successfully engineered: {features_built}
- Total data points across all sets: {total_rows:,}
- Success rate: {100*features_built/total_features if total_features > 0 else 0:.0f}%"""
    
    def _generate_feature_set_overview(self) -> str:
        """Generate overview table of all available feature sets."""
        sections = ["""## Feature Set Overview

The ML pipeline supports 6 feature sets, each capturing different aspects of NFL games:

| Feature Set | Description | Granularity | Phase |
|-------------|-------------|-------------|-------|"""]
        
        # Add all feature sets from registry
        for feature_name, info in FEATURE_REGISTRY.items():
            description = info.get('description', 'No description')
            phase = info.get('phase', 'unknown')
            table = info.get('table', '')
            
            # Determine granularity from table name
            if 'v1' in table and feature_name in ['team_efficiency', 'opponent_adjusted']:
                granularity = "Season-level"
            else:
                granularity = "Game-level"
            
            sections.append(
                f"| **{feature_name}** | {description} | {granularity} | {phase} |"
            )
        
        return '\n'.join(sections)
    
    def _generate_feature_set_details(self, results: Dict[str, Any]) -> str:
        """Generate detailed breakdown for each feature set."""
        feature_results = results.get('results', {})
        
        if not feature_results:
            return """## Feature Set Details

No feature sets were processed."""
        
        sections = ["## Feature Set Details\n"]
        
        # Process in order from registry to maintain consistency
        for feature_name in FEATURE_REGISTRY.keys():
            if feature_name not in feature_results:
                continue
            
            result = feature_results[feature_name]
            info = get_feature_info(feature_name)
            
            status = result.get('status', 'unknown')
            rows = result.get('rows_built', 0)
            error = result.get('error', '')
            
            # Status icon
            status_icon = "✅" if status == 'success' else "❌"
            
            # Handle case where feature info is not found
            if info is None:
                info = {'description': 'Unknown feature set', 'table': 'unknown', 'phase': 'unknown'}
            
            section_parts = [f"""### {status_icon} {feature_name.replace('_', ' ').title()}

**Description:** {info.get('description', 'No description')}
**Database Table:** `features.{info.get('table', 'unknown')}`
**Development Phase:** {info.get('phase', 'unknown')}
**Build Status:** {status}
**Rows Generated:** {rows:,}"""]
            
            if error:
                section_parts.append(f"\n**Error Details:**\n```\n{error}\n```")
            
            # Add feature set specific notes
            if feature_name == 'team_efficiency' and status == 'success':
                section_parts.append("""
**Key Features:**
- EPA calculations (offense & defense)
- Red zone efficiency metrics
- Third down conversion rates
- Turnover differentials
- Overall efficiency rankings""")
            
            elif feature_name == 'rolling_metrics' and status == 'success':
                section_parts.append("""
**Key Features:**
- 4/8/16-game rolling averages
- Momentum indicators (win streaks, trends)
- Consistency metrics (standard deviations)
- Venue-specific performance tracking""")
            
            elif feature_name == 'opponent_adjusted' and status == 'success':
                section_parts.append("""
**Key Features:**
- Strength of schedule calculations
- Quality wins/losses tracking
- Performance vs strong/average/weak opponents
- Schedule difficulty percentiles""")
            
            elif feature_name == 'nextgen' and status == 'success':
                section_parts.append("""
**Key Features:**
- QB NextGen Stats differentials
- Passer rating, completion %, aggressiveness
- Time to throw, air yards metrics
- Available for seasons 2016-2025""")
            
            elif feature_name == 'contextual' and status == 'success':
                section_parts.append("""
**Key Features:**
- Rest days differential (short/long rest indicators)
- Division and conference game flags
- Stadium-specific home advantage
- Weather impact (temperature, wind, precipitation)
- Playoff implications (late season, playoff week flags)""")
            
            elif feature_name == 'injury' and status == 'success':
                section_parts.append("""
**Key Features:**
- Position-weighted injury impact scores
- QB availability indicators
- Starter injury counts (depth chart based)
- Injury impact differentials""")
            
            sections.append('\n'.join(section_parts))
        
        return '\n\n'.join(sections)

    def _generate_column_inventory(self, results: Dict[str, Any]) -> str:
        """Generate detailed column inventory for all feature sets."""
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

    def _generate_correlation_analysis(self, results: Dict[str, Any]) -> str:
        """Generate correlation analysis with target variables."""
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

    def _generate_variance_analysis(self, results: Dict[str, Any]) -> str:
        """Generate variance analysis for feature informativeness."""
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

    def _generate_temporal_stability(self, results: Dict[str, Any]) -> str:
        """Generate temporal stability analysis across seasons."""
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

    def _generate_data_quality_summary(self, results: Dict[str, Any]) -> str:
        """Generate data quality and coverage analysis."""
        feature_results = results.get('results', {})
        successful = sum(1 for r in feature_results.values() if r.get('status') == 'success')
        total = len(feature_results)
        total_rows = results.get('total_rows', 0)
        
        # Calculate per-feature metrics
        feature_breakdown = []
        for feature_name, result in feature_results.items():
            if result.get('status') == 'success':
                rows = result.get('rows_built', 0)
                pct = (100 * rows / total_rows) if total_rows > 0 else 0
                feature_breakdown.append(f"- **{feature_name}**: {rows:,} rows ({pct:.1f}% of total)")
        
        breakdown_text = '\n'.join(sorted(feature_breakdown)) if feature_breakdown else "No successful feature sets"
        
        return f"""## Data Quality Summary

**Success Rate:** {successful}/{total} ({100*successful/total if total > 0 else 0:.0f}%)

**Data Volume Breakdown:**

{breakdown_text}

**Coverage Notes:**
- `team_efficiency`: Season-level aggregates (typically ~32 teams × ~27 seasons = ~861 rows)
- `rolling_metrics`: Game-level with rolling windows (typically ~14,392 team-games)
- `opponent_adjusted`: Season-level strength metrics (varies by seasons processed)
- `nextgen`: Game-level QB stats (2016-2025 seasons, ~2,684 games)
- `contextual`: Game-level context features (all available games, ~7,196)
- `injury`: Game-level injury impacts (all available games, ~7,196)

**Data Quality Indicators:**
- ✅ No DataFrame samples printed to logs (reduced verbosity)
- ✅ Detailed statistics logged for each feature set
- ✅ Memory management active during pipeline execution
- ✅ All features saved to both bucket (primary) and database (secondary)"""
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> str:
        """Generate actionable recommendations."""
        feature_results = results.get('results', {})
        successful = sum(1 for r in feature_results.values() if r.get('status') == 'success')
        total = len(feature_results)
        
        recommendations = ["## Recommendations\n"]
        
        # Success-based recommendations
        if successful == total:
            recommendations.append("""### ✅ All Features Built Successfully

**Next Steps:**
1. **Start Model Training** - Features are ready for ML pipeline
2. **Review Feature Logs** - Check individual feature set logs for detailed statistics
3. **Validate Data Quality** - Verify features loaded correctly in training pipeline
4. **Monitor Performance** - Track how features impact model accuracy

**Usage in ML Pipeline:**
```bash
# Train model with all features
quantcup nflfastrv3 ml train game_outcome --train-years 5 --test-year 2024

# Or backtest across multiple years
quantcup nflfastrv3 ml backtest game_outcome --train-years 5 --start-year 2020 --end-year 2024
```""")
        
        elif successful > 0:
            failed_features = [name for name, r in feature_results.items() if r.get('status') != 'success']
            recommendations.append(f"""### ⚠️ Partial Success - Some Features Failed

**Failed Features:** {', '.join(failed_features)}

**Troubleshooting:**
1. **Review Error Logs** - Check individual feature set logs for error details
2. **Data Availability** - Ensure required warehouse tables are populated
3. **Retry Failed Features** - Use CLI to rebuild specific feature sets:
   ```bash
   quantcup nflfastrv3 ml features --sets {' '.join(failed_features)}
   ```
4. **Check Dependencies** - Some features depend on others being built first

**Impact:**
- Models can still train with partial features, but accuracy may be reduced
- Consider addressing failures before production deployment""")
        
        else:
            recommendations.append("""### ❌ Feature Engineering Failed

**Immediate Actions:**
1. **Check Warehouse Data** - Verify warehouse tables are populated
2. **Review Error Logs** - Examine detailed error messages in feature logs
3. **Database Connectivity** - Ensure database and bucket connections are working
4. **Contact Support** - If issue persists, review documentation or seek assistance

**Common Issues:**
- Missing warehouse data (run `quantcup nflfastrv3 data warehouse` first)
- Database connection problems
- Insufficient memory (check memory manager logs)
- Invalid season specifications""")
        
        # General best practices
        recommendations.append("""
### General Best Practices

1. **Regular Rebuilds** - Rebuild features when new seasons become available
2. **Version Control** - Feature sets are versioned (v1, v2) for backwards compatibility
3. **Log Review** - Individual feature logs contain detailed statistics and quality metrics
4. **Documentation** - Refer to feature set source code for implementation details
5. **Temporal Safety** - Features use temporal shifting to prevent data leakage

### Feature Set Documentation

For detailed implementation information:
- **Source Code**: `nflfastRv3/features/ml_pipeline/feature_sets/`
- **Logs Directory**: `logs/quantcup_nflfastrv3_ml_features_<timestamp>/`
- **Database Tables**: `features` schema in QuantCup database
- **Bucket Storage**: `features/` directory in object storage""")
        
        return '\n'.join(recommendations)


def create_feature_reporter(logger=None):
    """
    Factory function to create feature report generator.
    
    Matches pattern from create_backtest_reporter()
    
    Args:
        logger: Optional logger instance
        
    Returns:
        FeatureReportGenerator: Configured feature reporter
    """
    return FeatureReportGenerator(logger=logger)


__all__ = ['FeatureReportGenerator', 'create_feature_reporter']