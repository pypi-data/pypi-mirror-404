"""
Pipeline Report Source Details Section Generator

Generates per-source breakdown section for pipeline ingestion reports.
Shows detailed metrics for each data source processed.
"""

from typing import Dict, Any

from ...common.formatters import (
    format_section_header,
    format_markdown_table,
    format_metric_row
)
from ...common.config import get_status_indicator, get_success_rate_rating
from ...common.metrics import calculate_success_rate


class SourceDetailsSectionGenerator:
    """
    Generates source-by-source breakdown section for pipeline reports.
    
    Provides:
    - Per-source row counts
    - Success/failure status per source
    - Loading strategy information
    - Storage location details
    """
    
    def __init__(self, logger=None):
        """
        Initialize source details section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_source_breakdown(self, result: Dict[str, Any]) -> str:
        """
        Generate detailed breakdown for each data source.
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            str: Formatted source breakdown section
        """
        sections = [format_section_header("Source Details", level=2)]
        
        group_results = result.get('group_results', {})
        
        if not group_results:
            sections.append("_No group results available._")
            return "\n\n".join(sections)
        
        # Process each group
        for group_name, group_data in group_results.items():
            sections.append(self._generate_group_section(group_name, group_data))
        
        # Generate summary table
        sections.append(self._generate_sources_summary_table(group_results))
        
        return "\n\n".join(sections)
    
    def _generate_group_section(self, group_name: str, group_data: Dict[str, Any]) -> str:
        """
        Generate section for a specific group.
        
        Args:
            group_name: Name of the group
            group_data: Group result data
            
        Returns:
            str: Formatted group section
        """
        status = group_data.get('status', 'unknown')
        rows = group_data.get('rows', 0)
        status_emoji = get_status_indicator(status)
        
        section_lines = [
            format_section_header(f"Group: {group_name}", level=3),
            f"**Status:** {status_emoji} {status.upper()}",
            format_metric_row("Rows Processed", rows),
        ]
        
        # Add error info if failed
        if status == 'failed' and group_data.get('error'):
            section_lines.append(f"\n**Error:** {group_data['error']}")
        
        # Add source details if available (Enhanced with Phase 1-4 metrics)
        if group_data.get('source_details'):
            section_lines.append("\n**Sources:**")
            for source_name, source_info in group_data['source_details'].items():
                source_rows = source_info.get('rows', 0)
                rows_fetched = source_info.get('rows_fetched', 0)
                rows_after_cleaning = source_info.get('rows_after_cleaning', 0)
                data_loss_pct = source_info.get('data_loss_pct', 0)
                source_status = source_info.get('status', 'unknown')
                loading_strategy = source_info.get('loading_strategy', 'unknown')
                bucket_success = source_info.get('bucket_success', False)
                database_success = source_info.get('database_success', False)
                duration = source_info.get('duration', 0)
                
                # Downgrade status if storage failed
                # If bucket storage is expected but failed, this is a warning even if status shows success
                if not bucket_success and source_info.get('bucket_configured', True):
                    if source_status == 'success':
                        source_status = 'warning'
                        if self.logger:
                            self.logger.warning(
                                f"Source '{source_name}' marked as success but bucket storage failed - downgrading to warning"
                            )
                
                # If we got 0 rows AND storage failed, definitely a warning
                if source_rows == 0 and (not bucket_success or not database_success):
                    if source_status == 'success':
                        source_status = 'warning'
                        if self.logger:
                            self.logger.warning(
                                f"Source '{source_name}' has 0 rows with storage failures - downgrading to warning"
                            )
                
                source_emoji = get_status_indicator(source_status)
                
                # Build comprehensive source line
                source_line = f"- {source_emoji} **{source_name}:** {source_rows:,} rows ({loading_strategy.replace('_', ' ').title()})"
                section_lines.append(source_line)
                
                # Add detailed metrics if available
                if rows_fetched > 0:
                    section_lines.append(f"  - Fetched: {rows_fetched:,} rows | After Cleaning: {rows_after_cleaning:,} | Loss: {data_loss_pct:.1f}%")
                
                # Add storage status
                bucket_icon = '✓' if bucket_success else '✗'
                db_icon = '✓' if database_success else '✗'
                section_lines.append(f"  - Storage: {bucket_icon} Bucket, {db_icon} Database")
                
                # Add performance if available
                if duration > 0:
                    rate = source_rows / duration if duration > 0 else 0
                    section_lines.append(f"  - Duration: {duration:.1f}s | Rate: {rate:,.0f} rows/sec")
                
                # Add warnings if needed
                if not bucket_success or not database_success:
                    if not bucket_success:
                        section_lines.append(f"  - **⚠️ Warning:** Bucket storage failed - data may be lost!")
                    elif not database_success:
                        section_lines.append(f"  - **⚠️ Warning:** Database routing failed - data safe in bucket, manual sync needed")
        
        return "\n".join(section_lines)
    
    def _generate_sources_summary_table(self, group_results: Dict[str, Any]) -> str:
        """
        Generate summary table of all sources.
        
        Args:
            group_results: Dictionary of group results
            
        Returns:
            str: Formatted summary table
        """
        sections = [format_section_header("Sources Summary", level=3)]
        
        # Collect all sources with enhanced metrics
        all_sources = []
        has_detailed_metrics = False
        
        for group_name, group_data in group_results.items():
            source_details = group_data.get('source_details', {})
            
            if source_details:
                has_detailed_metrics = True
                for source_name, source_info in source_details.items():
                    rows_fetched = source_info.get('rows_fetched', 0)
                    rows_after_clean = source_info.get('rows_after_cleaning', 0)
                    rows = source_info.get('rows', 0)
                    data_loss_pct = source_info.get('data_loss_pct', 0)
                    loading_strategy = source_info.get('loading_strategy', 'unknown')
                    bucket_success = source_info.get('bucket_success', False)
                    database_success = source_info.get('database_success', False)
                    status = source_info.get('status', 'unknown')
                    
                    # Storage status icons
                    storage_status = ''
                    if bucket_success and database_success:
                        storage_status = '✓B ✓DB'
                    elif bucket_success:
                        storage_status = '✓B ✗DB'
                    elif database_success:
                        storage_status = '✗B ✓DB'
                    else:
                        storage_status = '✗B ✗DB'
                    
                    all_sources.append([
                        source_name,
                        f"{rows_fetched:,}" if rows_fetched > 0 else 'N/A',
                        f"{rows_after_clean:,}",
                        f"{rows_fetched - rows_after_clean:,}" if rows_fetched > 0 else 'N/A',
                        f"{data_loss_pct:.1f}%" if rows_fetched > 0 else 'N/A',
                        loading_strategy.replace('_', ' ').title()[:11],  # Truncate long strategies
                        storage_status,
                        f"{get_status_indicator(status)} {status}"
                    ])
            else:
                # Fallback for groups without source details
                status = group_data.get('status', 'unknown')
                rows = group_data.get('rows', 0)
                all_sources.append([
                    group_name,
                    'N/A',
                    f"{rows:,}",
                    'N/A',
                    'N/A',
                    'N/A',
                    'N/A',
                    f"{get_status_indicator(status)} {status}"
                ])
        
        if not all_sources:
            return ""
        
        # Create enhanced table
        if has_detailed_metrics:
            headers = ['Source', 'Rows Fetched', 'After Clean', 'Lost', 'Loss %', 'Strategy', 'Storage', 'Status']
        else:
            headers = ['Group', 'Fetched', 'Rows Processed', 'Lost', 'Loss %', 'Strategy', 'Storage', 'Status']
        
        table = format_markdown_table(headers, all_sources)
        
        sections.append(table)
        
        # Calculate and add totals - handle N/A values
        total_rows = 0
        for row in all_sources:
            fetched_value = row[1].replace(',', '')
            if fetched_value != 'N/A':
                try:
                    total_rows += int(fetched_value)
                except ValueError:
                    pass  # Skip invalid values
        
        successful_groups = sum(1 for row in all_sources if 'success' in row[7].lower())
        total_groups = len(all_sources)
        
        success_rate = calculate_success_rate(successful_groups, total_groups)
        rating, emoji, level = get_success_rate_rating(success_rate)
        
        summary_lines = [
            "",
            "**Totals:**",
            format_metric_row("Total Rows", total_rows),
            format_metric_row("Successful Groups", successful_groups),
            format_metric_row("Total Groups", total_groups),
            format_metric_row("Success Rate", success_rate, "%"),
            f"- **Rating:** {emoji} {rating} - {level}",
        ]
        
        sections.append("\n".join(summary_lines))
        
        return "\n\n".join(sections)
    
    def generate_loading_strategy_details(self) -> str:
        """
        Generate information about loading strategies used.
        
        Returns:
            str: Formatted loading strategy section
        """
        sections = [format_section_header("Loading Strategies", level=3)]
        
        strategy_info = """
**Incremental Loading:**
- Loads only current season data
- Optimized for frequently updated tables (pbp, rosters, player_stats)
- Reduces processing time and API calls

**Full Refresh Loading:**
- Loads all available historical data
- Used for reference tables (teams, stadiums, officials)
- Ensures complete historical records

**Strategy Selection:**
- Configured per table in data source configuration
- Automatically determines temporal scope
- No manual season parameter management required
"""
        
        sections.append(strategy_info.strip())
        return "\n\n".join(sections)


__all__ = ['SourceDetailsSectionGenerator']
