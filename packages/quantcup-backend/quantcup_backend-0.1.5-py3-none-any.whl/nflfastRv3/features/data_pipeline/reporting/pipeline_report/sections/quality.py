"""
Pipeline Report Quality Section Generator

Generates data quality and data loss tracking section for pipeline reports.
Monitors cleaning impact, schema validation, and data integrity.
"""

from typing import Dict, Any

from ...common.formatters import (
    format_section_header,
    format_markdown_table,
    format_metric_row,
    format_percentage
)
from ...common.config import get_data_loss_rating
from ...common.metrics import calculate_data_loss_percentage


class QualitySectionGenerator:
    """
    Generates data quality section for pipeline reports.
    
    Provides:
    - Data loss tracking during cleaning
    - Schema validation results
    - Data quality metrics
    - Recommendations for quality improvements
    """
    
    def __init__(self, logger=None):
        """
        Initialize quality section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_quality_metrics(self, result: Dict[str, Any]) -> str:
        """
        Generate data quality metrics section.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted quality metrics section
        """
        sections = [format_section_header("Data Quality & Loss Tracking", level=2)]
        
        # Extract quality metrics from result
        quality_data = result.get('quality_metrics', {})
        
        if not quality_data and not result.get('group_results'):
            sections.append("_No quality metrics available._")
            return "\n\n".join(sections)
        
        # Generate overall quality summary
        sections.append(self._generate_quality_summary(result))
        
        # Generate data loss analysis
        sections.append(self._generate_data_loss_analysis(result))
        
        # Generate schema validation results
        sections.append(self._generate_schema_validation_results(result))
        
        return "\n\n".join(sections)
    
    def _generate_quality_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate overall quality summary.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted quality summary
        """
        sections = [format_section_header("Quality Summary", level=3)]
        
        # Calculate overall metrics
        total_rows_in = result.get('total_rows_fetched', result.get('total_rows', 0))
        total_rows_out = result.get('total_rows', 0)
        
        if total_rows_in > 0:
            data_loss_pct = calculate_data_loss_percentage(total_rows_in, total_rows_out)
            rating, emoji, level = get_data_loss_rating(data_loss_pct)
            
            summary_lines = [
                format_metric_row("Rows Fetched", total_rows_in),
                format_metric_row("Rows After Cleaning", total_rows_out),
                format_metric_row("Rows Lost", total_rows_in - total_rows_out),
                format_metric_row("Data Loss Percentage", data_loss_pct, "%"),
                f"\n**Quality Rating:** {emoji} {rating}",
                f"_{level}_",
            ]
        else:
            summary_lines = [
                "_No data loss metrics available._"
            ]
        
        sections.append("\n".join(summary_lines))
        return "\n\n".join(sections)
    
    def _generate_data_loss_analysis(self, result: Dict[str, Any]) -> str:
        """
        Generate detailed data loss analysis per source.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted data loss analysis
        """
        sections = [format_section_header("Data Loss by Source", level=3)]
        
        group_results = result.get('group_results', {})
        
        if not group_results:
            sections.append("_No source-level data available._")
            return "\n\n".join(sections)
        
        # Collect data loss info per source
        loss_rows = []
        has_loss_data = False
        
        for group_name, group_data in group_results.items():
            source_details = group_data.get('source_details', {})
            
            for source_name, source_info in source_details.items():
                rows_fetched = source_info.get('rows_fetched', source_info.get('rows', 0))
                rows_after_clean = source_info.get('rows_after_cleaning', source_info.get('rows', 0))
                
                if rows_fetched > 0:
                    has_loss_data = True
                    rows_lost = rows_fetched - rows_after_clean
                    loss_pct = calculate_data_loss_percentage(rows_fetched, rows_after_clean)
                    rating, emoji, _ = get_data_loss_rating(loss_pct)
                    
                    loss_rows.append([
                        source_name,
                        f"{rows_fetched:,}",
                        f"{rows_after_clean:,}",
                        f"{rows_lost:,}",
                        format_percentage(loss_pct),
                        f"{emoji} {rating}"
                    ])
        
        if not has_loss_data or not loss_rows:
            sections.append("_No data loss metrics available for individual sources._")
            return "\n\n".join(sections)
        
        # Create table
        headers = ['Source', 'Fetched', 'After Cleaning', 'Lost', 'Loss %', 'Rating']
        table = format_markdown_table(headers, loss_rows)
        
        sections.append(table)
        
        # Add interpretation notes
        notes = """
**Note:** Data loss during cleaning is normal and expected. Quality checks remove:
- Duplicate records
- Invalid data (missing required fields)
- Records outside configured temporal scope
- Data failing schema validation

Loss rates <1% are excellent. Rates >5% should be investigated.
"""
        sections.append(notes.strip())
        
        return "\n\n".join(sections)
    
    def _generate_schema_validation_results(self, result: Dict[str, Any]) -> str:
        """
        Generate schema validation results section.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted schema validation results
        """
        sections = [format_section_header("Schema Validation", level=3)]
        
        schema_issues = result.get('schema_issues', [])
        
        if not schema_issues:
            sections.append("✅ **No schema drift detected** across all sources.")
            return "\n\n".join(sections)
        
        # Count critical vs warning issues
        critical_count = sum(1 for issue in schema_issues if issue.get('severity') == 'critical')
        warning_count = len(schema_issues) - critical_count
        
        sections.append(f"\n⚠️ **{len(schema_issues)} schema issue(s) detected:**")
        sections.append(f"- 🔴 Critical: {critical_count} (requires immediate action)")
        sections.append(f"- 🟡 Warning: {warning_count} (monitor and plan mitigation)\n")
        
        # Group issues by severity and table
        critical_issues = [i for i in schema_issues if i.get('severity') == 'critical']
        warning_issues = [i for i in schema_issues if i.get('severity') != 'critical']
        
        # Show critical issues first
        if critical_issues:
            sections.append("**Critical Schema Issues:**\n")
            for issue in critical_issues:
                table = issue.get('table', 'unknown')
                message = issue.get('message', 'No details')
                requires_drop = issue.get('requires_drop', False)
                breaking_changes = issue.get('breaking_changes', [])
                
                sections.append(f"- 🔴 **{table}:** {message}")
                
                if requires_drop:
                    sections.append(f"  - **Action Required:** Table must be dropped and recreated")
                
                if breaking_changes:
                    sections.append(f"  - **Breaking Changes:**")
                    for change in breaking_changes[:3]:  # Show first 3
                        sections.append(f"    - {change}")
                    if len(breaking_changes) > 3:
                        sections.append(f"    - ... and {len(breaking_changes) - 3} more")
        
        # Show warning issues
        if warning_issues:
            sections.append("\n**Warning Schema Issues:**\n")
            for issue in warning_issues:
                table = issue.get('table', 'unknown')
                message = issue.get('message', 'No details')
                missing_columns = issue.get('missing_columns', [])
                
                sections.append(f"- 🟡 **{table}:** {message}")
                
                if missing_columns:
                    sections.append(f"  - **Missing Columns:** {', '.join(missing_columns[:5])}")
                    if len(missing_columns) > 5:
                        sections.append(f"  - ... and {len(missing_columns) - 5} more")
        
        # Add schema issue recommendations
        recommendation_text = """
**Schema Issue Recommendations:**
- 🔴 **Critical Issues:** Require immediate database maintenance before next pipeline run
- 🟡 **Warning Issues:** Plan DATABASE migration to add missing columns
- **Manual Intervention:** Schema drift cannot be auto-resolved - review logs for details
"""
        sections.append(recommendation_text.strip())
        
        return "\n\n".join(sections)
    
    def generate_quality_recommendations(self, result: Dict[str, Any]) -> str:
        """
        Generate quality improvement recommendations.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted recommendations
        """
        sections = [format_section_header("Quality Recommendations", level=2)]
        
        recommendations = []
        
        # Check data loss rates
        total_rows_in = result.get('total_rows_fetched', result.get('total_rows', 0))
        total_rows_out = result.get('total_rows', 0)
        
        if total_rows_in > 0:
            data_loss_pct = calculate_data_loss_percentage(total_rows_in, total_rows_out)
            
            if data_loss_pct > 0.10:  # >10% loss
                recommendations.append(
                    "🔴 **High Data Loss Detected:** Review cleaning rules and validation logic. "
                    "Loss rates >10% may indicate overly aggressive cleaning or data quality issues in source."
                )
            elif data_loss_pct > 0.05:  # >5% loss
                recommendations.append(
                    "🟠 **Moderate Data Loss:** Consider reviewing cleaning rules for optimization. "
                    "Some loss is normal, but rates >5% warrant investigation."
                )
        
        # Check schema issues
        schema_issues = result.get('schema_issues', [])
        if schema_issues:
            recommendations.append(
                "⚠️ **Schema Issues Detected:** Review schema validation results above. "
                "Schema drift may require table recreation or migration."
            )
        
        # Check group failures
        group_results = result.get('group_results', {})
        failed_groups = [
            name for name, data in group_results.items() 
            if data.get('status') == 'failed'
        ]
        if failed_groups:
            recommendations.append(
                f"❌ **Failed Groups:** {', '.join(failed_groups)}. "
                "Review error logs and consider circuit breaker activation."
            )
        
        if not recommendations:
            recommendations.append(
                "✅ **No Issues Detected:** Pipeline quality metrics are within acceptable ranges. "
                "Continue monitoring for trends over time."
            )
        
        sections.append("\n\n".join(recommendations))
        
        return "\n\n".join(sections)


__all__ = ['QualitySectionGenerator']
