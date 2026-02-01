"""
Warehouse Report Summary Section Generator

Generates header and executive summary for warehouse build reports.
Provides high-level metrics and status overview.

Pattern: Single Responsibility Principle
Complexity: 1 point (formatting and aggregation)
"""

from typing import Dict, Any, Optional


class SummarySectionGenerator:
    """
    Generates summary sections for warehouse build reports.
    
    Responsible for:
    - Report header with timestamp
    - Executive summary with high-level metrics
    - Warehouse architecture context
    - Overall build status assessment
    """
    
    def __init__(self, logger=None):
        """
        Initialize summary section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_header(self, results: Dict[str, Any], seasons: Optional[list] = None) -> str:
        """
        Generate report header with title and timestamp.
        
        Args:
            results: Warehouse build results dictionary
            seasons: Optional list of seasons processed
            
        Returns:
            str: Formatted header section
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Determine status emoji
        status = results.get('status', 'unknown')
        status_emoji = {
            'success': '✅',
            'partial': '⚠️',
            'failed': '❌'
        }.get(status, '❓')
        
        header = f"""# 📊 **Warehouse Build Report**

**Generated:** {timestamp}  
**Build Status:** {status_emoji} {status.upper()}"""
        
        if seasons:
            header += f"  \n**Seasons:** {', '.join(map(str, sorted(seasons)))}"
        
        return header
    
    def generate_executive_summary(self, results: Dict[str, Any]) -> str:
        """
        Generate executive summary with high-level metrics.
        
        PHASE 5 ENHANCED: Now includes Phase 1-4 highlights (memory, failures, schema changes).
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted executive summary section
        """
        total_tables = len(results.get('tables_built', []))
        total_rows = results.get('total_rows', 0)
        
        # Get dimension and fact counts
        dim_results = results.get('dimension_results', {})
        fact_results = results.get('fact_results', {})
        
        dim_count = len(dim_results.get('tables', []))
        fact_count = len(fact_results.get('tables', []))
        
        dim_rows = dim_results.get('total_rows', 0)
        fact_rows = fact_results.get('total_rows', 0)
        
        # Calculate success rates
        dim_success_rate = dim_results.get('success_rate', 0) * 100
        fact_success_rate = fact_results.get('success_rate', 0) * 100
        
        # Overall status assessment
        status = results.get('status', 'unknown')
        if status == 'success':
            assessment = "All warehouse tables built successfully"
        elif status == 'partial':
            assessment = "Some tables failed to build - review details below"
        else:
            assessment = "Warehouse build encountered critical failures"
        
        summary = f"""---

## 📋 Executive Summary

{assessment}

### Overview
- **Total Tables Built:** {total_tables}
- **Total Rows Loaded:** {total_rows:,}
- **Dimension Tables:** {dim_count} ({dim_rows:,} rows)
- **Fact Tables:** {fact_count} ({fact_rows:,} rows)

### Success Rates
- **Dimensions:** {dim_success_rate:.1f}%
- **Facts:** {fact_success_rate:.1f}%"""
        
        # PHASE 5: Add Phase 1-4 highlights
        
        # Phase 1: Memory usage
        total_memory_mb = results.get('total_memory_used_mb', 0)
        if total_memory_mb > 0:
            if total_memory_mb < 500:
                memory_rating = "✅ Excellent"
            elif total_memory_mb < 1000:
                memory_rating = "✅ Good"
            elif total_memory_mb < 1500:
                memory_rating = "⚠️ Moderate"
            else:
                memory_rating = "⚠️ High"
            
            summary += f"\n\n### Performance & Efficiency\n"
            summary += f"- **Total Memory Used:** {total_memory_mb:.2f} MB ({memory_rating})\n"
            
            # Column pruning stats
            column_pruning_stats = results.get('column_pruning_stats', {})
            pruning_tables_count = column_pruning_stats.get('total_tables_using_pruning', 0)
            if pruning_tables_count > 0:
                summary += f"- **Column Pruning:** Enabled for {pruning_tables_count} tables (~10x memory reduction)\n"
            
            # Build duration
            duration = results.get('duration', 0)
            if duration > 0:
                summary += f"- **Build Duration:** {duration:.2f}s\n"
                
                perf_metrics = results.get('performance_metrics', {})
                rate = perf_metrics.get('average_rate_rows_per_sec', 0)
                if rate > 0:
                    summary += f"- **Processing Rate:** {rate:,} rows/sec\n"
        
        # Phase 2: Build failures and empty tables
        build_failures = results.get('build_failures', [])
        empty_tables = results.get('empty_tables', [])
        
        if build_failures or empty_tables:
            summary += "\n\n### Issues Detected\n"
            if build_failures:
                critical_failures = [f for f in build_failures if not f.get('recoverable', True)]
                recoverable_failures = [f for f in build_failures if f.get('recoverable', True)]
                
                if critical_failures:
                    summary += f"- 🔴 **Critical Failures:** {len(critical_failures)} (requires attention)\n"
                if recoverable_failures:
                    summary += f"- ⚠️ **Recoverable Failures:** {len(recoverable_failures)}\n"
            
            if empty_tables:
                unexpected_empty = [t for t in empty_tables if not t.get('expected', False)]
                if unexpected_empty:
                    summary += f"- ⚠️ **Empty Tables:** {len(unexpected_empty)} (unexpected)\n"
        
        # Phase 4: Schema changes
        schema_changes = results.get('schema_changes', [])
        if schema_changes:
            critical_changes = [c for c in schema_changes if c.get('severity') == 'critical']
            warning_changes = [c for c in schema_changes if c.get('severity') == 'warning']
            
            summary += "\n\n### Schema Evolution\n"
            if critical_changes:
                summary += f"- 🔴 **Critical Schema Changes:** {len(critical_changes)} (breaking changes detected)\n"
            if warning_changes:
                summary += f"- ⚠️ **Schema Warnings:** {len(warning_changes)}\n"
            
            total_changes = len(schema_changes)
            summary += f"- **Total Schema Changes:** {total_changes}\n"
        
        return summary
    
    def generate_warehouse_context(self) -> str:
        """
        Generate warehouse architecture context section.
        
        Returns:
            str: Formatted warehouse context section
        """
        context = """---

## 🏗️ Warehouse Architecture

### Table Types

**Dimension Tables**
- Reference data (games, players, dates, drives)
- Slowly changing dimensions
- Relatively static (updated periodically)
- Foundation for fact table joins

**Fact Tables**
- Transactional play-by-play data
- Player-level statistics and performance metrics
- Large volume (millions of rows)
- Chunked processing for memory efficiency

### Build Strategy

1. **Dimensions First:** Reference tables built before facts
2. **Chunked Processing:** Large fact tables processed in chunks (5000+ rows/chunk)
3. **Column Pruning:** Only required columns loaded (10x memory reduction)
4. **Bucket-First:** Production uses bucket storage, dev uses database"""
        
        return context
    
    def generate_tables_overview(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed tables overview section.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted tables overview section
        """
        tables_built = results.get('tables_built', [])
        
        if not tables_built:
            return """---

## 📊 Tables Overview

No tables were successfully built."""
        
        # Get dimension and fact details
        dim_results = results.get('dimension_results', {})
        fact_results = results.get('fact_results', {})
        
        dim_details = dim_results.get('table_details', {})
        fact_details = fact_results.get('table_details', {})
        
        overview = """---

## 📊 Tables Overview

### Built Tables Summary"""
        
        # Dimension tables
        if dim_details:
            overview += "\n\n**Dimension Tables:**\n"
            for table_name in sorted(dim_details.keys()):
                details = dim_details[table_name]
                status = details.get('status', 'unknown')
                rows = details.get('rows', 0)
                status_emoji = '✅' if status == 'success' else '❌'
                overview += f"- {status_emoji} `{table_name}`: {rows:,} rows\n"
        
        # Fact tables
        if fact_details:
            overview += "\n**Fact Tables:**\n"
            for table_name in sorted(fact_details.keys()):
                details = fact_details[table_name]
                status = details.get('status', 'unknown')
                rows = details.get('rows', 0)
                processing_type = details.get('processing_type', 'standard')
                chunks = details.get('chunks_processed', 0)
                
                status_emoji = '✅' if status == 'success' else '❌'
                
                if processing_type == 'chunked' and chunks > 0:
                    overview += f"- {status_emoji} `{table_name}`: {rows:,} rows ({chunks} chunks)\n"
                else:
                    overview += f"- {status_emoji} `{table_name}`: {rows:,} rows\n"
        
        return overview


__all__ = ['SummarySectionGenerator']
