"""
Warehouse Report Performance Section Generator

Generates performance analysis for warehouse builds.
Tracks memory optimization, column pruning, and build efficiency.

Pattern: Single Responsibility Principle
Complexity: 1 point (formatting and aggregation)
"""

from typing import Dict, Any


class PerformanceSectionGenerator:
    """
    Generates performance section for warehouse build reports.
    
    Responsible for:
    - Memory optimization analysis
    - Column pruning effectiveness
    - Build duration and throughput metrics
    - Performance recommendations
    """
    
    def __init__(self, logger=None):
        """
        Initialize performance section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_performance_summary(self, results: Dict[str, Any]) -> str:
        """
        Generate performance summary section.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted performance summary section
        """
        performance_metrics = results.get('performance_metrics', {})
        
        if not performance_metrics:
            return """---

## ⚡ Performance Metrics

No performance metrics available."""
        
        summary = """---

## ⚡ Performance Metrics

### Build Performance Summary

"""
        
        # Extract metrics
        dimensions_built = performance_metrics.get('dimensions_built', 0)
        facts_built = performance_metrics.get('facts_built', 0)
        total_tables = performance_metrics.get('total_tables', 0)
        success_rate = performance_metrics.get('build_success_rate', 0) * 100
        
        summary += f"- **Tables Built:** {total_tables} ({dimensions_built} dimensions + {facts_built} facts)\n"
        summary += f"- **Success Rate:** {success_rate:.1f}%\n"
        
        # Calculate throughput if duration available
        total_rows = results.get('total_rows', 0)
        
        if total_rows > 0:
            summary += f"- **Total Rows Processed:** {total_rows:,}\n"
        
        return summary
    
    def generate_memory_optimization_analysis(self, results: Dict[str, Any]) -> str:
        """
        Generate memory optimization analysis section.
        
        PHASE 5 ENHANCED: Now shows detailed table-by-table memory breakdown.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted memory optimization analysis
        """
        analysis = """---

## 💾 Memory Optimization

### Column Pruning Strategy

**Bucket-First Architecture Benefits:**
- **Column Pruning:** Only required columns loaded from bucket storage
- **Memory Reduction:** ~10x reduction vs loading full PBP dataset
- **Chunked Processing:** Large fact tables processed in memory-safe chunks
- **Streaming Storage:** Results streamed to bucket without full buffering

"""
        
        # PHASE 5: Add table memory breakdown
        analysis += self.generate_table_memory_breakdown(results)
        
        # PHASE 5: Add column pruning analysis
        analysis += self.generate_column_pruning_analysis(results)
        
        # PHASE 5: Add chunking efficiency metrics
        analysis += self.generate_chunking_efficiency_metrics(results)
        
        return analysis
    
    def generate_table_memory_breakdown(self, results: Dict[str, Any]) -> str:
        """
        PHASE 5: Generate table-by-table memory breakdown with trends.
        
        Shows memory usage per table using Phase 1 memory_mb metrics.
        
        Args:
            results: Warehouse build results
            
        Returns:
            Formatted memory breakdown table
        """
        section = "### Table Memory Breakdown\n\n"
        
        # Get dimension and fact results
        dim_details = results.get('dimension_results', {}).get('table_details', {})
        fact_details = results.get('fact_results', {}).get('table_details', {})
        
        # Collect all table memory data
        table_memory = []
        
        # Process dimensions
        for table_name, details in dim_details.items():
            if details.get('status') == 'success':
                memory_mb = details.get('memory_mb', 0)
                rows = details.get('rows', 0)
                table_memory.append((table_name, 'dimension', memory_mb, rows))
        
        # Process facts
        for table_name, details in fact_details.items():
            if details.get('status') == 'success':
                # For chunked tables, use total_memory_mb if available
                if details.get('processing_type') == 'chunked':
                    memory_mb = details.get('total_memory_mb', 0)
                    if isinstance(memory_mb, str):  # Handle 'N/A'
                        memory_mb = 0
                else:
                    memory_mb = details.get('memory_mb', 0)
                rows = details.get('rows', 0)
                table_memory.append((table_name, 'fact', memory_mb, rows))
        
        if not table_memory:
            section += "*No memory data available*\n\n"
            return section
        
        # Sort by memory usage (descending)
        table_memory.sort(key=lambda x: x[2], reverse=True)
        
        # Create table
        section += "| Table | Type | Memory (MB) | Rows | MB per 1K Rows |\n"
        section += "|-------|------|-------------|------|----------------|\n"
        
        total_memory = 0
        for table_name, table_type, memory_mb, rows in table_memory:
            total_memory += memory_mb
            mb_per_1k = (memory_mb / rows * 1000) if rows > 0 else 0
            section += f"| `{table_name}` | {table_type} | {memory_mb:.2f} | {rows:,} | {mb_per_1k:.3f} |\n"
        
        section += f"| **TOTAL** | - | **{total_memory:.2f}** | - | - |\n"
        section += "\n"
        
        # Add efficiency rating
        if total_memory < 500:
            rating = "✅ Excellent"
        elif total_memory < 1000:
            rating = "✅ Good"
        elif total_memory < 1500:
            rating = "⚠️ Moderate"
        else:
            rating = "⚠️ High"
        
        section += f"**Memory Efficiency Rating:** {rating}\n\n"
        
        return section
    
    def generate_column_pruning_analysis(self, results: Dict[str, Any]) -> str:
        """
        PHASE 5: Generate column pruning effectiveness analysis.
        
        Shows before/after memory comparisons using Phase 1 columns_pruned metrics.
        
        Args:
            results: Warehouse build results
            
        Returns:
            Formatted column pruning analysis
        """
        section = "### Column Pruning Effectiveness\n\n"
        
        column_pruning_stats = results.get('column_pruning_stats', {})
        enabled_tables = column_pruning_stats.get('enabled_tables', [])
        
        if not enabled_tables:
            section += "*Column pruning not enabled for this build*\n\n"
            return section
        
        section += f"**Tables Using Column Pruning:** {len(enabled_tables)}\n\n"
        
        # List tables with pruning
        dim_details = results.get('dimension_results', {}).get('table_details', {})
        fact_details = results.get('fact_results', {}).get('table_details', {})
        
        pruned_tables_info = []
        
        # Check dimensions
        for table_name, details in dim_details.items():
            if details.get('columns_pruned', False) and details.get('status') == 'success':
                columns_loaded = details.get('columns_loaded', 'N/A')
                memory_mb = details.get('memory_mb', 0)
                pruned_tables_info.append((table_name, columns_loaded, memory_mb))
        
        # Check facts
        for table_name, details in fact_details.items():
            if details.get('column_pruning_enabled', False) and details.get('status') == 'success':
                columns_loaded = details.get('columns_loaded', 'N/A')
                memory_mb = details.get('total_memory_mb', 0) if details.get('processing_type') == 'chunked' else details.get('memory_mb', 0)
                if isinstance(memory_mb, str):
                    memory_mb = 0
                pruned_tables_info.append((table_name, columns_loaded, memory_mb))
        
        if pruned_tables_info:
            section += "| Table | Columns Loaded | Memory (MB) | Savings Estimate |\n"
            section += "|-------|----------------|-------------|------------------|\n"
            
            for table_name, columns_loaded, memory_mb in pruned_tables_info:
                # Estimate savings (10x reduction means 90% saved)
                estimated_full_memory = memory_mb * 10
                savings_mb = estimated_full_memory - memory_mb
                section += f"| `{table_name}` | {columns_loaded} | {memory_mb:.2f} | ~{savings_mb:.2f} MB saved |\n"
            
            section += "\n"
            section += "**Impact:**\n"
            section += "- Column pruning reduces play_by_play memory from ~4GB to ~400MB\n"
            section += "- Enables processing of large datasets within memory limits\n"
            section += "- Loading only needed columns (50-80 vs 250+)\n\n"
        
        return section
    
    def generate_chunking_efficiency_metrics(self, results: Dict[str, Any]) -> str:
        """
        PHASE 5: Generate chunking efficiency metrics.
        
        Shows chunk memory efficiency using Phase 1 memory_per_chunk_mb metrics.
        
        Args:
            results: Warehouse build results
            
        Returns:
            Formatted chunking efficiency section
        """
        section = "### Chunked Processing Efficiency\n\n"
        
        fact_details = results.get('fact_results', {}).get('table_details', {})
        
        # Find chunked tables
        chunked_tables = []
        for table_name, details in fact_details.items():
            if details.get('processing_type') == 'chunked' and details.get('status') == 'success':
                chunked_tables.append((table_name, details))
        
        if not chunked_tables:
            section += "*No chunked processing used in this build*\n\n"
            return section
        
        section += f"**Tables Using Chunked Processing:** {len(chunked_tables)}\n\n"
        
        section += "| Table | Chunks | Chunk Size | Avg Memory/Chunk | Total Rows |\n"
        section += "|-------|--------|------------|------------------|------------|\n"
        
        for table_name, details in chunked_tables:
            chunks = details.get('chunks_processed', 0)
            chunk_size = details.get('chunk_size', 5000)
            memory_per_chunk = details.get('memory_per_chunk_mb', 'N/A')
            total_rows = details.get('rows', 0)
            
            # Format memory per chunk
            if isinstance(memory_per_chunk, (int, float)):
                memory_str = f"{memory_per_chunk:.2f} MB"
            else:
                memory_str = str(memory_per_chunk)
            
            section += f"| `{table_name}` | {chunks} | {chunk_size} | {memory_str} | {total_rows:,} |\n"
        
        section += "\n"
        section += "**Benefits:**\n"
        section += "- Memory-safe processing of large datasets (>50K rows)\n"
        section += "- Prevents memory exhaustion by processing in manageable chunks\n"
        section += "- Streaming storage: Each chunk saved before loading next\n"
        section += "- Consistent memory usage regardless of total dataset size\n\n"
        
        return section
    
    def generate_optimization_recommendations(self, results: Dict[str, Any]) -> str:
        """
        Generate optimization recommendations based on build results.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted optimization recommendations
        """
        recommendations = []
        
        # Analyze build results for optimization opportunities
        fact_results = results.get('fact_results', {})
        fact_tables = fact_results.get('table_details', {})
        
        total_rows = results.get('total_rows', 0)
        
        # Check for large non-chunked tables
        large_standard_tables = [
            (name, details) for name, details in fact_tables.items()
            if details.get('processing_type') == 'standard' and details.get('rows', 0) > 50000
        ]
        
        if large_standard_tables:
            recommendations.append({
                'priority': 'Medium',
                'area': 'Processing Strategy',
                'suggestion': f"Consider chunked processing for {len(large_standard_tables)} fact table(s) with >50K rows",
                'benefit': 'Improved memory efficiency and streaming storage capabilities'
            })
        
        # Check for failed tables
        status = results.get('status', 'unknown')
        if status == 'partial':
            failed_dims = sum(
                1 for details in results.get('dimension_results', {}).get('table_details', {}).values()
                if details.get('status') != 'success'
            )
            failed_facts = sum(
                1 for details in fact_tables.values()
                if details.get('status') != 'success'
            )
            
            if failed_dims > 0 or failed_facts > 0:
                recommendations.append({
                    'priority': 'High',
                    'area': 'Reliability',
                    'suggestion': f"Investigate {failed_dims + failed_facts} failed table(s) to improve success rate",
                    'benefit': 'Complete warehouse coverage and data consistency'
                })
        
        # Performance insights based on row counts
        if total_rows > 2000000:
            recommendations.append({
                'priority': 'Low',
                'area': 'Performance',
                'suggestion': 'Monitor bucket storage I/O patterns for large datasets',
                'benefit': 'Identify potential bottlenecks in data loading/saving'
            })
        
        # Format recommendations
        if not recommendations:
            return """---

## 🎯 Optimization Recommendations

✅ **No optimization recommendations** - warehouse build is performing efficiently."""
        
        section = """---

## 🎯 Optimization Recommendations

"""
        
        # Sort by priority
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        for rec in recommendations:
            priority_emoji = {
                'High': '🔴',
                'Medium': '🟡',
                'Low': '🟢'
            }.get(rec['priority'], '⚪')
            
            section += f"### {priority_emoji} {rec['priority']} Priority: {rec['area']}\n\n"
            section += f"**Recommendation:** {rec['suggestion']}\n\n"
            section += f"**Expected Benefit:** {rec['benefit']}\n\n"
        
        return section
    
    def generate_build_efficiency_metrics(self, results: Dict[str, Any]) -> str:
        """
        Generate build efficiency metrics.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted build efficiency metrics
        """
        dim_results = results.get('dimension_results', {})
        fact_results = results.get('fact_results', {})
        
        dim_success = dim_results.get('success_rate', 0) * 100
        fact_success = fact_results.get('success_rate', 0) * 100
        
        section = """### Build Efficiency

| Metric | Value | Rating |
|--------|-------|--------|
"""
        
        # Dimension success rate
        dim_rating = self._get_success_rate_rating(dim_success)
        section += f"| Dimension Success Rate | {dim_success:.1f}% | {dim_rating} |\n"
        
        # Fact success rate
        fact_rating = self._get_success_rate_rating(fact_success)
        section += f"| Fact Success Rate | {fact_success:.1f}% | {fact_rating} |\n"
        
        # Overall efficiency
        total_tables = len(results.get('tables_built', []))
        performance = results.get('performance_metrics', {})
        expected_tables = performance.get('total_tables', total_tables)
        
        if expected_tables > 0:
            overall_efficiency = (total_tables / expected_tables) * 100
            efficiency_rating = self._get_success_rate_rating(overall_efficiency)
            section += f"| Overall Build Efficiency | {overall_efficiency:.1f}% | {efficiency_rating} |\n"
        
        return section
    
    def _get_success_rate_rating(self, rate: float) -> str:
        """
        Get rating for success rate.
        
        Args:
            rate: Success rate percentage
            
        Returns:
            str: Rating emoji and label
        """
        if rate >= 95:
            return "✅ Excellent"
        elif rate >= 80:
            return "🟢 Good"
        elif rate >= 60:
            return "🟡 Fair"
        else:
            return "🔴 Needs attention"


__all__ = ['PerformanceSectionGenerator']
