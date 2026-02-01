"""
Warehouse Report Facts Section Generator

Generates detailed breakdown of fact table building.
Tracks chunked processing, performance metrics, and large-scale data handling.

Pattern: Single Responsibility Principle
Complexity: 1 point (formatting and aggregation)
"""

from typing import Dict, Any


class FactsSectionGenerator:
    """
    Generates fact tables section for warehouse build reports.
    
    Responsible for:
    - Per-fact detailed breakdown
    - Chunked processing metrics
    - Performance tracking for large tables
    - Build status and error reporting
    """
    
    def __init__(self, logger=None):
        """
        Initialize facts section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_facts_breakdown(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed breakdown of fact tables.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted facts breakdown section
        """
        fact_results = results.get('fact_results', {})
        
        if not fact_results:
            return """---

## 📈 Fact Tables Details

No fact results available."""
        
        table_details = fact_results.get('table_details', {})
        
        if not table_details:
            return """---

## 📈 Fact Tables Details

No fact tables were built."""
        
        breakdown = """---

## 📈 Fact Tables Details

### Per-Fact Breakdown

"""
        
        # Sort tables by processing type (chunked first) and then by status
        chunked_success = []
        chunked_failed = []
        standard_success = []
        standard_failed = []
        
        for table_name, details in sorted(table_details.items()):
            status = details.get('status', 'unknown')
            processing_type = details.get('processing_type', 'standard')
            
            if processing_type == 'chunked':
                if status == 'success':
                    chunked_success.append((table_name, details))
                else:
                    chunked_failed.append((table_name, details))
            else:
                if status == 'success':
                    standard_success.append((table_name, details))
                else:
                    standard_failed.append((table_name, details))
        
        # Process chunked successful tables with Phase 1-3 enhancements
        for table_name, details in chunked_success:
            rows = details.get('rows', 0)
            chunks = details.get('chunks_processed', 0)
            performance = details.get('performance_metrics', {})
            
            breakdown += f"#### ✅ `{table_name}` (Chunked Processing)\n\n"
            breakdown += f"- **Rows:** {rows:,}\n"
            breakdown += f"- **Chunks Processed:** {chunks}\n"
            
            if chunks > 0:
                avg_rows_per_chunk = rows / chunks
                breakdown += f"- **Avg Rows/Chunk:** {avg_rows_per_chunk:,.0f}\n"
            
            # PHASE 1: Add chunk memory metrics
            chunk_size = details.get('chunk_size', 5000)
            memory_per_chunk = details.get('memory_per_chunk_mb')
            if memory_per_chunk and memory_per_chunk != 'N/A':
                breakdown += f"- **Chunk Size:** {chunk_size} rows\n"
                breakdown += f"- **Memory per Chunk:** {memory_per_chunk:.2f} MB\n"
            
            total_memory = details.get('total_memory_mb')
            if total_memory and total_memory != 'N/A':
                breakdown += f"- **Total Memory:** {total_memory:.2f} MB\n"
            
            # PHASE 1: Add column pruning info
            col_pruning = details.get('column_pruning_enabled', False)
            cols_loaded = details.get('columns_loaded', 'N/A')
            if col_pruning:
                breakdown += f"- **Column Pruning:** ✅ Enabled ({cols_loaded} columns)\n"
            
            # PHASE 3: Add build timing
            duration = details.get('duration', 0)
            if duration:
                breakdown += f"- **Build Time:** {duration:.2f}s\n"
            
            # PHASE 3: Add performance metrics if available
            if performance:
                rows_per_sec = performance.get('rows_per_second', 'N/A')
                if rows_per_sec != 'N/A':
                    breakdown += f"- **Processing Rate:** {rows_per_sec:,} rows/sec\n"
                
                avg_chunk_time = performance.get('avg_chunk_time', 'N/A')
                if avg_chunk_time != 'N/A':
                    breakdown += f"- **Avg Chunk Time:** {avg_chunk_time:.2f}s\n"
            
            # Add insights
            insights = self._get_fact_insights(table_name, rows, chunks)
            if insights:
                breakdown += f"- **Insights:** {insights}\n"
            
            breakdown += "\n"
        
        # Process standard successful tables
        for table_name, details in standard_success:
            rows = details.get('rows', 0)
            columns = details.get('columns', 0)
            
            breakdown += f"#### ✅ `{table_name}` (Standard Processing)\n\n"
            breakdown += f"- **Rows:** {rows:,}\n"
            
            if columns > 0:
                breakdown += f"- **Columns:** {columns}\n"
            
            insights = self._get_fact_insights(table_name, rows, 0)
            if insights:
                breakdown += f"- **Insights:** {insights}\n"
            
            breakdown += "\n"
        
        # Process failed tables
        for table_name, details in chunked_failed + standard_failed:
            error = details.get('error', 'Unknown error')
            processing_type = details.get('processing_type', 'standard')
            
            breakdown += f"#### ❌ `{table_name}` ({processing_type.title()})\n\n"
            breakdown += f"- **Status:** Failed\n"
            breakdown += f"- **Error:** {error}\n\n"
        
        return breakdown
    
    def generate_facts_summary_table(self, results: Dict[str, Any]) -> str:
        """
        Generate summary table of all fact tables.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted facts summary table
        """
        fact_results = results.get('fact_results', {})
        table_details = fact_results.get('table_details', {})
        
        if not table_details:
            return ""
        
        summary = """### Facts Summary

| Table | Status | Rows | Processing | Chunks | Notes |
|-------|--------|------|------------|--------|-------|
"""
        
        for table_name in sorted(table_details.keys()):
            details = table_details[table_name]
            status = details.get('status', 'unknown')
            rows = details.get('rows', 0)
            processing_type = details.get('processing_type', 'standard')
            chunks = details.get('chunks_processed', 0)
            
            status_emoji = '✅' if status == 'success' else '❌'
            processing_label = 'Chunked' if processing_type == 'chunked' else 'Standard'
            chunks_str = str(chunks) if chunks > 0 else 'N/A'
            
            # Get quality indicator
            quality = self._assess_fact_quality(table_name, rows)
            
            summary += f"| `{table_name}` | {status_emoji} | {rows:,} | {processing_label} | {chunks_str} | {quality} |\n"
        
        return summary
    
    def generate_chunking_analysis(self, results: Dict[str, Any]) -> str:
        """
        Generate analysis of chunked processing efficiency.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted chunking analysis section
        """
        fact_results = results.get('fact_results', {})
        table_details = fact_results.get('table_details', {})
        
        # Find tables that used chunking
        chunked_tables = [
            (name, details) for name, details in table_details.items()
            if details.get('processing_type') == 'chunked' and details.get('status') == 'success'
        ]
        
        if not chunked_tables:
            return ""
        
        analysis = """### Chunked Processing Analysis

**Memory Optimization Strategy:**  
Large fact tables are processed in chunks to prevent memory exhaustion. Each chunk is loaded, transformed, and saved before loading the next.

"""
        
        total_rows = 0
        total_chunks = 0
        
        for table_name, details in chunked_tables:
            rows = details.get('rows', 0)
            chunks = details.get('chunks_processed', 0)
            
            total_rows += rows
            total_chunks += chunks
        
        if total_chunks > 0:
            avg_chunk_size = total_rows / total_chunks
            
            analysis += f"**Overall Statistics:**\n"
            analysis += f"- **Tables Using Chunking:** {len(chunked_tables)}\n"
            analysis += f"- **Total Rows Processed:** {total_rows:,}\n"
            analysis += f"- **Total Chunks:** {total_chunks}\n"
            analysis += f"- **Average Chunk Size:** {avg_chunk_size:,.0f} rows\n\n"
            
            analysis += "**Per-Table Breakdown:**\n"
            for table_name, details in chunked_tables:
                rows = details.get('rows', 0)
                chunks = details.get('chunks_processed', 0)
                chunk_size = rows / chunks if chunks > 0 else 0
                
                analysis += f"- `{table_name}`: {chunks} chunks × {chunk_size:,.0f} rows/chunk = {rows:,} total rows\n"
        
        return analysis
    
    def _format_performance_metrics(self, performance: Dict[str, Any]) -> str:
        """
        Format performance metrics for display.
        
        Args:
            performance: Performance metrics dictionary
            
        Returns:
            str: Formatted performance metrics string
        """
        if not performance:
            return ""
        
        formatted = ""
        
        # Common performance metrics
        if 'duration_seconds' in performance:
            duration = performance['duration_seconds']
            formatted += f"- **Duration:** {duration:.2f}s\n"
        
        if 'rows_per_second' in performance:
            rate = performance['rows_per_second']
            formatted += f"- **Processing Rate:** {rate:,.0f} rows/sec\n"
        
        return formatted
    
    def _get_fact_insights(self, table_name: str, rows: int, chunks: int) -> str:
        """
        Get table-specific insights based on row count and chunking.
        
        Args:
            table_name: Name of the fact table
            rows: Number of rows in the table
            chunks: Number of chunks processed (0 for standard processing)
            
        Returns:
            str: Insight message or empty string
        """
        # Expected ranges for fact tables (approximate)
        expected_ranges = {
            'fact_play': (10000, 500000),           # Play-by-play data
            'fact_player_stats': (50000, 1000000),  # Player statistics
            'fact_player_play': (50000, 2000000)    # Player-play combos
        }
        
        if table_name not in expected_ranges:
            return ""
        
        min_expected, max_expected = expected_ranges[table_name]
        
        if rows < min_expected:
            return f"⚠️ Lower than expected (typical: {min_expected:,}+)"
        elif rows > max_expected:
            return f"✅ Comprehensive dataset ({max_expected:,}+ rows)"
        else:
            msg = "✅ Normal range"
            if chunks > 0:
                msg += f" | Chunked for memory efficiency"
            return msg
    
    def _assess_fact_quality(self, table_name: str, rows: int) -> str:
        """
        Assess data quality for fact table based on row count.
        
        Args:
            table_name: Name of the fact table
            rows: Number of rows in the table
            
        Returns:
            str: Quality indicator
        """
        # Expected minimum counts
        min_counts = {
            'fact_play': 10000,
            'fact_player_stats': 50000,
            'fact_player_play': 50000
        }
        
        min_expected = min_counts.get(table_name, 0)
        
        if rows == 0:
            return "⚠️ Empty"
        elif min_expected > 0 and rows < min_expected * 0.5:
            return "⚠️ Low volume"
        elif rows > 100000:
            return "✅ Large dataset"
        else:
            return "✅ Good"


__all__ = ['FactsSectionGenerator']
