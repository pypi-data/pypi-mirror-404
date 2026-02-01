"""
Pipeline Report Performance Section Generator

Generates performance metrics and bottleneck analysis sections for pipeline reports.
Tracks processing rates, timing breakdowns, and identifies optimization opportunities.
"""

from typing import Dict, Any, List, Tuple

from ...common.formatters import (
    format_section_header,
    format_markdown_table,
    format_metric_row,
    format_duration
)


class PerformanceSectionGenerator:
    """
    Generates performance analysis section for pipeline reports.
    
    Provides:
    - Processing rate analysis (rows/second)
    - Timing breakdowns (fetch, clean, store)
    - Bottleneck identification
    - Performance recommendations
    """
    
    def __init__(self, logger=None):
        """
        Initialize performance section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_performance_analysis(self, result: Dict[str, Any]) -> str:
        """
        Generate comprehensive performance analysis section.
        
        Args:
            result: Pipeline result dictionary with performance_metrics
            
        Returns:
            str: Formatted performance analysis section
        """
        sections = [format_section_header("Performance Metrics", level=2)]
        
        perf_metrics = result.get('performance_metrics', {})
        
        if not perf_metrics:
            sections.append("_No performance metrics available for this pipeline run._")
            sections.append("\n**Why:** Performance tracking requires Phase 3 timing metrics from the processing pipeline.")
            sections.append("\n**To Enable:** Ensure the pipeline implementation is calling `_calculate_performance_metrics()` and including the result in the return dictionary.")
            sections.append("\n**Expected Data:** `performance_metrics` dict with `total_duration_seconds`, `average_rate_rows_per_sec`, `peak_rate`, `slowest_source`, and per-source timing details.")
            return "\n\n".join(sections)
        
        # Generate sub-sections
        sections.append(self._generate_pipeline_performance_summary(result, perf_metrics))
        sections.append(self._generate_processing_time_breakdown(perf_metrics))
        sections.append(self._generate_performance_analysis_insights(perf_metrics))
        sections.append(self._generate_stage_timing_analysis(perf_metrics))
        
        return "\n\n".join(sections)
    
    def _generate_pipeline_performance_summary(self, result: Dict[str, Any], perf_metrics: Dict[str, Any]) -> str:
        """
        Generate high-level pipeline performance summary.
        
        Args:
            result: Pipeline result dictionary
            perf_metrics: Performance metrics dictionary
            
        Returns:
            str: Formatted performance summary
        """
        sections = [format_section_header("Pipeline Performance", level=3)]
        
        total_duration = perf_metrics.get('total_duration_seconds', 0)
        avg_rate = perf_metrics.get('average_rate_rows_per_sec', 0)
        peak_rate = perf_metrics.get('peak_rate', 0)
        slowest_source = perf_metrics.get('slowest_source', 'N/A')
        
        summary_lines = [
            format_metric_row("Total Duration", format_duration(total_duration), ""),
            format_metric_row("Average Processing Rate", f"{avg_rate:,.0f} rows/second", ""),
            format_metric_row("Peak Processing Rate", f"{peak_rate:,.0f} rows/second", ""),
            format_metric_row("Slowest Source", slowest_source, ""),
        ]
        
        sections.append("\n".join(summary_lines))
        return "\n\n".join(sections)
    
    def _generate_processing_time_breakdown(self, perf_metrics: Dict[str, Any]) -> str:
        """
        Generate detailed processing time breakdown per source.
        
        Args:
            perf_metrics: Performance metrics dictionary
            
        Returns:
            str: Formatted processing time breakdown table
        """
        sections = [format_section_header("Processing Time Breakdown", level=3)]
        
        sources = perf_metrics.get('sources', {})
        
        if not sources:
            sections.append("_No per-source timing data available._")
            return "\n\n".join(sections)
        
        # Collect sources with metadata for sorting
        source_data = []
        for source_name, source_metrics in sources.items():
            duration = source_metrics.get('duration', 0)
            rows = source_metrics.get('rows', 0)
            rate = source_metrics.get('rate', 0)
            percent_of_total = source_metrics.get('percent_of_total', 0)
            
            # Determine status emoji based on performance
            if rate == perf_metrics.get('peak_rate', 0):
                status = '⚡ Fastest'
            elif source_name == perf_metrics.get('slowest_source'):
                status = '⏱️ Slowest'
            elif percent_of_total > 30:
                status = '⏱️'
            elif rate > perf_metrics.get('average_rate_rows_per_sec', 0):
                status = '⚡'
            else:
                status = '⚪'
            
            source_data.append({
                'name': source_name,
                'duration': duration,
                'duration_formatted': format_duration(duration),
                'rows': rows,
                'rate': rate,
                'percent': percent_of_total,
                'status': status
            })
        
        # Sort by raw duration value descending (slowest first)
        # Fixed: Sorting by numeric value instead of trying to parse formatted string
        source_data.sort(key=lambda x: x['duration'], reverse=True)
        
        # Build table rows from sorted data
        source_rows = [
            [
item['name'],
                item['duration_formatted'],
                f"{item['rows']:,}",
                f"{item['rate']:,.0f}",
                f"{item['percent']:.1f}%",
                item['status']
            ]
            for item in source_data
        ]
        
        # Create table
        headers = ['Source', 'Duration', 'Rows', 'Rate (rows/s)', '% of Total Time', 'Status']
        table = format_markdown_table(headers, source_rows)
        
        sections.append(table)
        
        return "\n\n".join(sections)
    
    def _generate_performance_analysis_insights(self, perf_metrics: Dict[str, Any]) -> str:
        """
        Generate performance analysis insights and bottleneck identification.
        
        Args:
            perf_metrics: Performance metrics dictionary
            
        Returns:
            str: Formatted performance analysis insights
        """
        sections = [format_section_header("Performance Analysis", level=3)]
        
        sources = perf_metrics.get('sources', {})
        avg_rate = perf_metrics.get('average_rate_rows_per_sec', 0)
        
        if not sources or avg_rate == 0:
            sections.append("_Insufficient data for performance analysis._")
            return "\n\n".join(sections)
        
        # Analyze each source's performance relative to average
        # Skip bottleneck analysis for small datasets (<1000 rows) to avoid false positives
        MIN_ROWS_FOR_BOTTLENECK_ANALYSIS = 1000
        
        insights = ["**Bottleneck Identification:**"]
        
        bottlenecks = []
        moderate = []
        optimized = []
        
        for source_name, source_metrics in sources.items():
            rate = source_metrics.get('rate', 0)
            rows = source_metrics.get('rows', 0)
            percent_of_total = source_metrics.get('percent_of_total', 0)
            
            # Skip small datasets or zero-rate sources
            if rate == 0 or rows < MIN_ROWS_FOR_BOTTLENECK_ANALYSIS:
                continue
            
            deviation = ((rate - avg_rate) / avg_rate) * 100
            
            if deviation < -20:  # More than 20% below average
                bottlenecks.append((source_name, deviation, percent_of_total))
            elif deviation < -5:  # 5-20% below average
                moderate.append((source_name, deviation, percent_of_total))
            else:  # At or above average
                optimized.append((source_name, deviation, percent_of_total))
        
        if bottlenecks:
            for source, deviation, pct in bottlenecks:
                insights.append(f"- 🔴 **{source}:** Processing rate {abs(deviation):.0f}% below average (optimize cleaning rules)")
        
        if moderate:
            for source, deviation, pct in moderate:
                insights.append(f"- 🟡 **{source}:** Processing rate {abs(deviation):.0f}% below average")
        
        if optimized:
            for source, deviation, pct in optimized[:2]:  # Show top 2 optimized
                insights.append(f"- 🟢 **{source}:** Processing rate {deviation:.0f}% above average (well optimized)")
        
        sections.append("\n".join(insights))
        
        # Add recommendations
        recommendations = ["\n**Recommendations:**"]
        
        if bottlenecks:
            slowest = max(bottlenecks, key=lambda x: abs(x[1]))
            recommendations.append(f"- Consider optimizing {slowest[0]} cleaning rules (largest bottleneck)")
            recommendations.append("- Review memory usage during large table processing")
        else:
            recommendations.append("- Current performance is **acceptable** for production use")
            recommendations.append("- Continue monitoring for performance trends over time")
        
        sections.append("\n".join(recommendations))
        
        return "\n\n".join(sections)
    
    def _generate_stage_timing_analysis(self, perf_metrics: Dict[str, Any]) -> str:
        """
        Generate timing analysis for each processing stage (fetch, clean, store).
        
        Args:
            perf_metrics: Performance metrics dictionary
            
        Returns:
            str: Formatted stage timing analysis
        """
        sections = [format_section_header("Stage Timing Analysis", level=3)]
        
        sources = perf_metrics.get('sources', {})
        
        if not sources:
            sections.append("_No stage timing data available._")
            return "\n\n".join(sections)
        
        # Collect stage timing data
        stage_rows = []
        for source_name, source_metrics in sources.items():
            fetch_duration = source_metrics.get('fetch_duration', 0)
            cleaning_duration = source_metrics.get('cleaning_duration', 0)
            storage_duration = source_metrics.get('storage_duration', 0)
            total_duration = source_metrics.get('duration', 0)
            
            if total_duration == 0:
                continue
            
            # Calculate percentages
            fetch_pct = (fetch_duration / total_duration) * 100 if total_duration > 0 else 0
            clean_pct = (cleaning_duration / total_duration) * 100 if total_duration > 0 else 0
            store_pct = (storage_duration / total_duration) * 100 if total_duration > 0 else 0
            
            stage_rows.append([
                source_name,
                f"{fetch_duration:.1f}s ({fetch_pct:.0f}%)",
                f"{cleaning_duration:.1f}s ({clean_pct:.0f}%)",
                f"{storage_duration:.1f}s ({store_pct:.0f}%)",
                format_duration(total_duration)
            ])
        
        if not stage_rows:
            sections.append("_No stage timing data available._")
            return "\n\n".join(sections)
        
        # Create table
        headers = ['Source', 'Fetch', 'Cleaning', 'Storage', 'Total']
        table = format_markdown_table(headers, stage_rows)
        
        sections.append(table)
        
        # Add stage analysis insights
        insights = [
            "\n**Stage Insights:**",
            "- **Fetch:** Time spent retrieving data from R service",
            "- **Cleaning:** Time spent on validation and data quality checks",
            "- **Storage:** Time spent writing to bucket and database",
        ]
        
        sections.append("\n".join(insights))
        
        return "\n\n".join(sections)


__all__ = ['PerformanceSectionGenerator']
