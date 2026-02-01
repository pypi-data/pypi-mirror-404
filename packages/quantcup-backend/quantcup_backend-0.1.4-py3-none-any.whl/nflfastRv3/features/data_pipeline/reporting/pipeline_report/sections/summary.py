"""
Pipeline Report Summary Section Generator

Generates executive summary section for pipeline ingestion reports.
Provides high-level overview of pipeline execution with key metrics.
"""

from typing import Dict, Any
from datetime import datetime

from ...common.formatters import (
    format_section_header,
    format_metric_row,
    format_duration
)
from ...common.config import get_status_indicator
from ...common.templates import create_status_badge


class SummarySectionGenerator:
    """
    Generates executive summary section for pipeline reports.
    
    Provides:
    - Pipeline status overview
    - High-level metrics (total rows, sources processed)
    - Duration and performance summary
    - Status indicators
    """
    
    def __init__(self, logger=None):
        """
        Initialize summary section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_header(self, result: Dict[str, Any]) -> str:
        """
        Generate report header with metadata.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted header section
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = result.get('status', 'unknown')
        
        # Check for storage failures across all sources
        # If any source has storage failures, downgrade status to warning
        status = self._check_storage_failures(result, status)
        
        status_emoji = get_status_indicator(status)
        
        header = f"""# Data Pipeline Ingestion Report

**Generated:** {timestamp}
**Report Type:** Pipeline Ingestion
**Status:** {create_status_badge(status.upper(), status_emoji)}
"""
        
        # Add metadata if available
        if result.get('group_results'):
            groups_processed = list(result['group_results'].keys())
            header += f"**Groups Processed:** {', '.join(groups_processed)}  \n"
        
        if result.get('tables'):
            header += f"**Tables Updated:** {len(result['tables'])}  \n"
        
        header += "\n"
        return header
    
    def generate_executive_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate executive summary with key metrics.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted executive summary section
        """
        sections = [format_section_header("Executive Summary", level=2)]
        
        status = result.get('status', 'unknown')
        total_rows = result.get('total_rows', 0)
        total_rows_fetched = result.get('total_rows_fetched', 0)
        tables_count = len(result.get('tables', []))
        
        # Calculate data loss
        data_loss = total_rows_fetched - total_rows if total_rows_fetched > 0 else 0
        data_loss_pct = (data_loss / total_rows_fetched * 100) if total_rows_fetched > 0 else 0
        
        # Build summary content
        summary_lines = []
        
        if status == 'success':
            summary_lines.append(
                f"✅ Pipeline completed successfully, processing **{total_rows:,}** total rows "
                f"across **{tables_count}** tables."
            )
        elif status == 'warning':
            summary_lines.append(
                f"⚠️ Pipeline completed with warnings. Some sources may have issues."
            )
        else:
            summary_lines.append(
                f"❌ Pipeline encountered errors during execution."
            )
        
        # Add high-level quality indicator
        if total_rows_fetched > 0:
            if data_loss_pct < 1.0:
                summary_lines.append(f"\n🟢 **Data Quality:** Excellent ({data_loss_pct:.1f}% loss during cleaning)")
            elif data_loss_pct < 5.0:
                summary_lines.append(f"\n🟡 **Data Quality:** Good ({data_loss_pct:.1f}% loss during cleaning)")
            else:
                summary_lines.append(f"\n🔴 **Data Quality:** Needs Review ({data_loss_pct:.1f}% loss during cleaning)")
        
        summary_lines.append("")
        summary_lines.append("### Key Metrics")
        summary_lines.append("")
        summary_lines.append(format_metric_row("Total Rows Processed", total_rows))
        
        # Add fetched rows if available (Phase 1)
        if total_rows_fetched > 0:
            summary_lines.append(format_metric_row("Total Rows Fetched", total_rows_fetched))
            summary_lines.append(format_metric_row("Data Loss", f"{data_loss:,} rows ({data_loss_pct:.1f}%)"))
        
        summary_lines.append(format_metric_row("Tables Updated", tables_count))
        
        # Add group counts if available
        if result.get('group_results'):
            groups_processed = len(result['group_results'])
            groups_success = sum(
                1 for g in result['group_results'].values() 
                if g.get('status') == 'success'
            )
            summary_lines.append(format_metric_row("Groups Processed", groups_processed))
            summary_lines.append(format_metric_row("Groups Successful", groups_success))
        
        # Add duration if available
        if result.get('duration'):
            duration = result['duration']
            summary_lines.append(format_metric_row("Duration", format_duration(duration), unit=""))
        
        sections.append("\n".join(summary_lines))
        return "\n\n".join(sections)
    
    def generate_data_pipeline_context(self) -> str:
        """
        Generate context about data pipeline architecture.
        
        Returns:
            str: Formatted context section
        """
        sections = [format_section_header("Pipeline Architecture", level=2)]
        
        context = """
This report documents NFL data pipeline ingestion operations following the **bucket-first architecture**:

1. **Data Fetching:** Pull data from nflfastR R package via R integration
2. **Data Cleaning:** Apply quality checks and schema validation
3. **Bucket Storage:** Store in Google Cloud Storage (primary storage)
4. **Database Routing:** Route to configured databases (secondary storage)

**Key Features:**
- ✅ Incremental loading for current season data
- ✅ Full refresh for historical/reference tables
- ✅ Schema drift detection
- ✅ Circuit breaker pattern for failure recovery
- ✅ Memory-optimized processing
"""
        
        sections.append(context.strip())
        return "\n\n".join(sections)
    
    def _check_storage_failures(self, result: Dict[str, Any], current_status: str) -> str:
        """
        Check for storage failures and downgrade status if needed.
        
        Args:
            result: Pipeline result dictionary
            current_status: Current pipeline status
            
        Returns:
            str: Updated status (may be downgraded to 'warning' if storage failures detected)
        """
        # Only downgrade if currently showing success
        if current_status != 'success':
            return current_status
        
        # Check for bucket/database storage failures in source details
        group_results = result.get('group_results', {})
        storage_failures = []
        
        for group_name, group_data in group_results.items():
            source_details = group_data.get('source_details', {})
            
            for source_name, source_info in source_details.items():
                bucket_success = source_info.get('bucket_success', False)
                database_success = source_info.get('database_success', False)
                bucket_configured = source_info.get('bucket_configured', True)
                
                # If bucket is configured but failed, that's critical
                if bucket_configured and not bucket_success:
                    storage_failures.append(f"{source_name} (bucket storage failed)")
                    if self.logger:
                        self.logger.warning(
                            f"Downgrading pipeline status to WARNING due to bucket storage failure in '{source_name}'"
                        )
        
        # Downgrade to warning if we found storage failures
        if storage_failures:
            return 'warning'
        
        return current_status


__all__ = ['SummarySectionGenerator']
