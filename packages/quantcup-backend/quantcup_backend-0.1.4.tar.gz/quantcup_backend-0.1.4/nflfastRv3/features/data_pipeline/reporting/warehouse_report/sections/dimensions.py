"""
Warehouse Report Dimensions Section Generator

Generates detailed breakdown of dimension table building.
Tracks row counts, columns, and data quality for reference tables.

Pattern: Single Responsibility Principle
Complexity: 1 point (formatting and aggregation)
"""

from typing import Dict, Any


class DimensionsSectionGenerator:
    """
    Generates dimension tables section for warehouse build reports.
    
    Responsible for:
    - Per-dimension detailed breakdown
    - Column counts and data quality indicators
    - Build status and error reporting
    - Dimension-specific insights
    """
    
    def __init__(self, logger=None):
        """
        Initialize dimensions section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_dimensions_breakdown(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed breakdown of dimension tables.
        
        PHASE 5 ENHANCED: Now includes memory, timing, and source attribution from Phase 1-3.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted dimensions breakdown section
        """
        dim_results = results.get('dimension_results', {})
        
        if not dim_results:
            return """---

## 📊 Dimension Tables Details

No dimension results available."""
        
        table_details = dim_results.get('table_details', {})
        
        if not table_details:
            return """---

## 📊 Dimension Tables Details

No dimension tables were built."""
        
        breakdown = """---

## 📊 Dimension Tables Details

### Per-Dimension Breakdown

"""
        
        # Sort tables by status (success first, then failed)
        success_tables = []
        failed_tables = []
        
        for table_name, details in sorted(table_details.items()):
            status = details.get('status', 'unknown')
            if status == 'success':
                success_tables.append((table_name, details))
            else:
                failed_tables.append((table_name, details))
        
        # Add successful tables with Phase 1-3 enhancements
        for table_name, details in success_tables:
            rows = details.get('rows', 0)
            columns = details.get('columns', 0)
            
            breakdown += f"#### ✅ `{table_name}`\n\n"
            breakdown += f"- **Rows:** {rows:,}\n"
            
            if columns > 0:
                breakdown += f"- **Columns:** {columns}\n"
            
            # PHASE 1: Add memory usage
            memory_mb = details.get('memory_mb', 0)
            if memory_mb:
                breakdown += f"- **Memory:** {memory_mb:.2f} MB\n"
            
            # PHASE 1: Add source table attribution
            source_table = details.get('source_table')
            build_type = details.get('build_type', 'unknown')
            if source_table:
                if isinstance(source_table, list):
                    breakdown += f"- **Source:** {', '.join(source_table)} (multi-source)\n"
                else:
                    breakdown += f"- **Source:** `{source_table}`\n"
                breakdown += f"- **Build Type:** {build_type}\n"
            
            # PHASE 1: Add column pruning info
            columns_pruned = details.get('columns_pruned', False)
            columns_loaded = details.get('columns_loaded', 'N/A')
            if columns_pruned:
                breakdown += f"- **Column Pruning:** ✅ Enabled ({columns_loaded} columns loaded)\n"
            
            # PHASE 3: Add build timing
            duration = details.get('duration', 0)
            if duration:
                rows_per_sec = details.get('rows_per_second', 0)
                breakdown += f"- **Build Time:** {duration:.2f}s ({rows_per_sec:,} rows/sec)\n"
            
            # Add specific insights based on table type
            insights = self._get_table_insights(table_name, rows)
            if insights:
                breakdown += f"- **Insights:** {insights}\n"
            
            breakdown += "\n"
        
        # Add failed tables
        for table_name, details in failed_tables:
            error = details.get('error', 'Unknown error')
            
            breakdown += f"#### ❌ `{table_name}`\n\n"
            breakdown += f"- **Status:** Failed\n"
            breakdown += f"- **Error:** {error}\n\n"
        
        return breakdown
    
    def generate_dimensions_summary_table(self, results: Dict[str, Any]) -> str:
        """
        Generate summary table of all dimensions.
        
        Args:
            results: Warehouse build results dictionary
            
        Returns:
            str: Formatted dimensions summary table
        """
        dim_results = results.get('dimension_results', {})
        table_details = dim_results.get('table_details', {})
        
        if not table_details:
            return ""
        
        summary = """### Dimensions Summary

| Table | Status | Rows | Columns | Notes |
|-------|--------|------|---------|-------|
"""
        
        for table_name in sorted(table_details.keys()):
            details = table_details[table_name]
            status = details.get('status', 'unknown')
            rows = details.get('rows', 0)
            columns = details.get('columns', 0)
            
            status_emoji = '✅' if status == 'success' else '❌'
            
            # Get quality indicator
            quality = self._assess_dimension_quality(table_name, rows)
            
            summary += f"| `{table_name}` | {status_emoji} | {rows:,} | {columns} | {quality} |\n"
        
        return summary
    
    def _get_table_insights(self, table_name: str, rows: int) -> str:
        """
        Get table-specific insights based on row count and table type.
        
        Args:
            table_name: Name of the dimension table
            rows: Number of rows in the table
            
        Returns:
            str: Insight message or empty string
        """
        # Expected ranges for dimension tables (approximate)
        expected_ranges = {
            'dim_game': (100, 5000),       # ~300 games per season
            'dim_player': (1000, 10000),   # Active and recent players
            'dim_date': (3000, 10000),     # Several years of dates
            'dim_drive': (5000, 50000),    # Multiple drives per game
            'injuries': (100, 5000),       # Current and recent injuries
            'player_id_mapping': (1000, 10000)  # Player ID crosswalk
        }
        
        if table_name not in expected_ranges:
            return ""
        
        min_expected, max_expected = expected_ranges[table_name]
        
        if rows < min_expected:
            return f"⚠️ Lower than expected (typical: {min_expected:,}+)"
        elif rows > max_expected:
            return f"✅ Comprehensive coverage ({max_expected:,}+ rows)"
        else:
            return "✅ Normal range"
    
    def _assess_dimension_quality(self, table_name: str, rows: int) -> str:
        """
        Assess data quality for dimension table based on row count.
        
        Args:
            table_name: Name of the dimension table
            rows: Number of rows in the table
            
        Returns:
            str: Quality indicator
        """
        # Expected minimum counts
        min_counts = {
            'dim_game': 100,
            'dim_player': 1000,
            'dim_date': 3000,
            'dim_drive': 5000,
            'injuries': 50,
            'player_id_mapping': 1000
        }
        
        min_expected = min_counts.get(table_name, 0)
        
        if rows == 0:
            return "⚠️ Empty"
        elif min_expected > 0 and rows < min_expected * 0.5:
            return "⚠️ Low coverage"
        else:
            return "✅ Good"


__all__ = ['DimensionsSectionGenerator']
