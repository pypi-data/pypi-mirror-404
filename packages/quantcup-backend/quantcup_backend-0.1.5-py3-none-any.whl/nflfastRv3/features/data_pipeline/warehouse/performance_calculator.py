"""
Performance Calculator Component

Extracted from warehouse.py (lines 438-533).
Calculates comprehensive performance metrics for warehouse builds.

Pattern: Single Responsibility (2 complexity points)
- Base calculations: 1 point
- Performance analysis:  1 point
"""

from typing import Dict, Any, List, Tuple


class PerformanceCalculator:
    """
    Calculates comprehensive performance metrics for warehouse builds.
    
    Pattern: Single Responsibility (2 complexity points)
    Complexity: 2 points (base + performance analysis)
    
    Responsibilities:
    - Performance metrics calculation
    - Processing rate analysis
    - Bottleneck identification
    - Per-source and warehouse-level metrics
    """
    
    def __init__(self, logger):
        """
        Initialize performance calculator.
        
        Args:
            logger: Logger instance for diagnostic messages
        """
        self.logger = logger
    
    def calculate_warehouse_metrics(self, results: Dict, total_rows: int, pipeline_duration: float) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics for warehouse build.
        
        Extracted from warehouse.py lines 438-533.
        
        Analyzes build timing at all levels to identify bottlenecks and optimization opportunities.
        
        Args:
            results: Build results dictionary with timing data
            total_rows: Total rows processed
            pipeline_duration: Total pipeline duration
            
        Returns:
            Dict with performance analysis:
            - total_duration_seconds: Overall warehouse build time
            - average_rate_rows_per_sec: Overall processing rate
            - slowest_table: Table taking longest to build
            - fastest_table: Table with highest processing rate
            - memory_efficiency_mb_per_row: Memory usage per row
            - tables: Per-table breakdown with rates and percentages
        """
        # Calculate warehouse-level metrics
        total_duration = results.get('duration', pipeline_duration)
        total_memory_mb = results.get('total_memory_used_mb', 0)
        
        # Aggregate table metrics
        table_metrics = {}
        all_durations = []
        
        # Process dimension tables
        for table_name, details in results.get('dimension_results', {}).get('table_details', {}).items():
            if details.get('status') == 'success' and 'duration' in details:
                duration = details['duration']
                rows = details['rows']
                all_durations.append((table_name, duration))
                
                table_metrics[table_name] = {
                    'duration': duration,
                    'rows': rows,
                    'rate': int(rows / duration) if duration > 0 else 0,
                    'percent_of_total_time': round((duration / total_duration * 100), 1) if total_duration > 0 else 0,
                    'type': 'dimension',
                    'memory_mb': details.get('memory_mb', 0)
                }
        
        # Process fact tables
        for table_name, details in results.get('fact_results', {}).get('table_details', {}).items():
            if details.get('status') == 'success' and 'duration' in details:
                duration = details['duration']
                rows = details['rows']
                all_durations.append((table_name, duration))
                
                # Calculate rate based on processing type
                rate = int(rows / duration) if duration > 0 else 0
                
                table_metrics[table_name] = {
                    'duration': duration,
                    'rows': rows,
                    'rate': rate,
                    'percent_of_total_time': round((duration / total_duration * 100), 1) if total_duration > 0 else 0,
                    'type': 'fact',
                    'processing_type': details.get('processing_type', 'standard')
                }
                
                # Add chunking metrics if available
                if details.get('processing_type') == 'chunked':
                    perf_metrics = details.get('performance_metrics', {})
                    table_metrics[table_name]['chunks_processed'] = details.get('chunks_processed', 0)
                    table_metrics[table_name]['avg_chunk_time'] = perf_metrics.get('avg_chunk_time', 'N/A')
                    
                    # Classify chunk performance
                    avg_chunk_time = perf_metrics.get('avg_chunk_time', 0)
                    if isinstance(avg_chunk_time, (int, float)):
                        if avg_chunk_time < 1.0:
                            chunk_perf = 'optimal'
                        elif avg_chunk_time < 3.0:
                            chunk_perf = 'good'
                        elif avg_chunk_time < 5.0:
                            chunk_perf = 'moderate'
                        else:
                            chunk_perf = 'slow'
                        table_metrics[table_name]['chunk_performance'] = chunk_perf
        
        # Identify bottlenecks
        slowest_table = max(all_durations, key=lambda x: x[1])[0] if all_durations else None
        fastest_table = max(table_metrics.items(), key=lambda x: x[1]['rate'])[0] if table_metrics else None
        
        # Calculate memory efficiency
        memory_efficiency = round(total_memory_mb / total_rows, 6) if total_rows > 0 else 0
        
        return {
            'total_duration_seconds': total_duration,
            'average_rate_rows_per_sec': int(total_rows / total_duration) if total_duration > 0 else 0,
            'slowest_table': slowest_table,
            'fastest_table': fastest_table,
            'memory_efficiency_mb_per_row': memory_efficiency,
            'tables': table_metrics
        }
    


__all__ = ['PerformanceCalculator']
