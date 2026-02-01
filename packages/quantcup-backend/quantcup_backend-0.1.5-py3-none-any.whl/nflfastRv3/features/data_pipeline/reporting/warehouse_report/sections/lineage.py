"""
Data Lineage Section Generator for Warehouse Reports

PHASE 5: Enhanced report sections with data flow visualization.
Generates comprehensive data lineage showing flow from source through
transformations to warehouse tables.

Pattern: Single Responsibility Principle
One class per report section for clear separation of concerns.
"""

from typing import Dict, Any


class DataLineageSectionGenerator:
    """
    Generate data lineage sections for warehouse reports.
    
    PHASE 5 Implementation: Visualizes data flow from sources to warehouse.
    
    Responsibilities:
    - Show complete data flow: Source Tables → Transformations → Warehouse
    - Track transformation stages per table
    - Visualize memory optimization points
    - Show storage routing (database vs bucket)
    
    Pattern: Simple formatter (1 complexity point)
    Complexity: Formats lineage metadata from warehouse build results
    """
    
    def __init__(self, logger=None):
        """
        Initialize data lineage section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_warehouse_data_flow(self, results: Dict[str, Any]) -> str:
        """
        Generate high-level warehouse data flow diagram.
        
        Shows the complete path from source data through transformations to warehouse.
        
        Args:
            results: Warehouse build results containing build_metadata and table_details
            
        Returns:
            Markdown section with data flow visualization
        """
        section = "## 📊 Data Lineage\n\n"
        section += "### Warehouse Data Flow\n\n"
        section += "```\n"
        section += "┌─────────────────────────────────────────────────────────────┐\n"
        section += "│                      DATA FLOW OVERVIEW                      │\n"
        section += "└─────────────────────────────────────────────────────────────┘\n"
        section += "\n"
        
        # Determine storage mode
        build_metadata = results.get('build_metadata', {})
        bucket_mode = build_metadata.get('bucket_mode', False)
        
        if bucket_mode:
            bucket_name = build_metadata.get('bucket_name', 'unknown')
            section += "Storage Mode: BUCKET-FIRST ✅\n"
            section += f"Bucket: {bucket_name}\n"
            section += "\n"
            section += "┌──────────────────┐\n"
            section += "│  Bucket Storage  │\n"
            section += "│  (play_by_play)  │\n"
            section += "└────────┬─────────┘\n"
            section += "         │ Column Pruning (10x memory reduction)\n"
            section += "         ▼\n"
            section += "┌────────────────────┐\n"
            section += "│ DataFrameEngine   │\n"
            section += "│ (In-Memory View)  │\n"
            section += "└────────┬───────────┘\n"
            section += "         │\n"
            section += "         ▼\n"
            section += "┌─────────────────────┐\n"
            section += "│  Transformation     │\n"
            section += "│  Modules            │\n"
            section += "│  (Build Logic)      │\n"
            section += "└────────┬────────────┘\n"
            section += "         │\n"
            section += "         ├─► Dimensions (Single-Pass)\n"
            section += "         ├─► Facts (Chunked: 5000 rows/chunk)\n"
            section += "         └─► Multi-Source (Bucket Adapter)\n"
            section += "         │\n"
            section += "         ▼\n"
            section += "┌─────────────────────┐\n"
            section += "│  Warehouse Schema   │\n"
            section += "│  (Bucket Storage)   │\n"
            section += "└─────────────────────┘\n"
        else:
            section += "Storage Mode: DATABASE 🗄️\n"
            section += "\n"
            section += "┌────────────────┐\n"
            section += "│   Database     │\n"
            section += "│ (raw_nflfastr) │\n"
            section += "└────────┬───────┘\n"
            section += "         │ SQL Queries\n"
            section += "         ▼\n"
            section += "┌─────────────────────┐\n"
            section += "│  Transformation     │\n"
            section += "│  Modules            │\n"
            section += "│  (Build Logic)      │\n"
            section += "└────────┬────────────┘\n"
            section += "         │\n"
            section += "         ├─► Dimensions (Direct Query)\n"
            section += "         ├─► Facts (Chunked Processing)\n"
            section += "         └─► Multi-Source (Direct Query)\n"
            section += "         │\n"
            section += "         ▼\n"
            section += "┌─────────────────────┐\n"
            section += "│  Warehouse Schema   │\n"
            section += "│  (Database Tables)  │\n"
            section += "└─────────────────────┘\n"
        
        section += "```\n\n"
        
        # Add key statistics
        total_rows = results.get('total_rows', 0)
        total_memory = results.get('total_memory_used_mb', 0)
        
        section += f"**Pipeline Statistics:**\n"
        section += f"- **Total Rows Processed:** {total_rows:,}\n"
        section += f"- **Memory Used:** {total_memory:.2f} MB\n"
        
        column_pruning_stats = results.get('column_pruning_stats', {})
        pruning_tables = column_pruning_stats.get('enabled_tables', [])
        if pruning_tables:
            section += f"- **Column Pruning:** Enabled for {len(pruning_tables)} tables\n"
        
        chunked_tables = build_metadata.get('chunked_tables', [])
        if chunked_tables:
            section += f"- **Chunked Processing:** {len(chunked_tables)} large fact tables\n"
        
        section += "\n"
        
        return section
    
    def generate_per_table_lineage(self, results: Dict[str, Any]) -> str:
        """
        Generate per-table data lineage details.
        
        Shows source → transformation → destination path for each table.
        
        Args:
            results: Warehouse build results containing table_details
            
        Returns:
            Markdown section with per-table lineage
        """
        section = "### Per-Table Data Lineage\n\n"
        
        dim_details = results.get('dimension_results', {}).get('table_details', {})
        fact_details = results.get('fact_results', {}).get('table_details', {})
        
        # Table lineage information
        lineage_info = {
            'dim_game': {
                'source': 'play_by_play',
                'transformations': ['Game-level aggregation', 'Weather categorization', 'Venue standardization'],
                'optimization': 'Column pruning'
            },
            'dim_player': {
                'source': 'play_by_play',
                'transformations': ['Player deduplication', 'Demographics extraction', 'Position standardization'],
                'optimization': 'Column pruning'
            },
            'dim_date': {
                'source': 'Generated from game_date',
                'transformations': ['Date dimension generation', 'Calendar attributes'],
                'optimization': 'None (lightweight)'
            },
            'dim_drive': {
                'source': 'play_by_play',
                'transformations': ['Drive-level grouping', 'Outcome classification', 'Time calculation'],
                'optimization': 'Column pruning'
            },
            'injuries': {
                'source': 'injuries + depth_charts (multi-source)',
                'transformations': ['Data consolidation', 'Status standardization', 'Bucket-based loading'],
                'optimization': 'Multi-source loading via BucketAdapter'
            },
            'player_id_mapping': {
                'source': 'play_by_play + snap_counts (multi-source)',
                'transformations': ['ID crosswalk generation', 'Name matching'],
                'optimization': 'Multi-source loading via BucketAdapter'
            },
            'fact_play': {
                'source': 'play_by_play',
                'transformations': ['EPA calculations', 'Win probability', 'Play classification'],
                'optimization': 'Chunked processing (5000 rows/chunk) + Column pruning'
            },
            'fact_player_stats': {
                'source': 'play_by_play',
                'transformations': ['Player aggregation', 'Fantasy points', 'Performance metrics'],
                'optimization': 'Standard processing + Column pruning'
            },
            'fact_player_play': {
                'source': 'play_by_play',
                'transformations': ['Player-play attribution', 'Participation tracking'],
                'optimization': 'Chunked processing (5000 rows/chunk) + Column pruning'
            }
        }
        
        # Process all tables
        all_tables = []
        
        # Add dimensions
        for table_name, details in sorted(dim_details.items()):
            if details.get('status') == 'success':
                all_tables.append(('dimension', table_name, details))
        
        # Add facts
        for table_name, details in sorted(fact_details.items()):
            if details.get('status') == 'success':
                all_tables.append(('fact', table_name, details))
        
        # Generate lineage for each table
        for table_type, table_name, details in all_tables:
            if table_name in lineage_info:
                info = lineage_info[table_name]
                rows = details.get('rows', 0)
                memory_mb = details.get('memory_mb', 0)
                
                section += f"#### `{table_name}` ({table_type})\n\n"
                section += "```\n"
                section += f"{info['source']}\n"
                section += "    │\n"
                section += "    ▼\n"
                for i, transform in enumerate(info['transformations']):
                    is_last = i == len(info['transformations']) - 1
                    section += f"[ {transform} ]\n"
                    if not is_last:
                        section += "    │\n"
                        section += "    ▼\n"
                section += "    │\n"
                section += "    ▼\n"
                section += f"warehouse.{table_name} ({rows:,} rows"
                if memory_mb:
                    section += f", {memory_mb:.1f} MB"
                section += ")\n"
                section += "```\n"
                section += f"**Optimization:** {info['optimization']}\n\n"
        
        return section
    
    def generate_transformation_pipeline_diagram(self, results: Dict[str, Any]) -> str:
        """
        Generate transformation pipeline diagram showing processing stages.
        
        Visualizes the transformation pipeline with memory optimization points.
        
        Args:
            results: Warehouse build results
            
        Returns:
            Markdown section with pipeline diagram
        """
        section = "### Transformation Pipeline\n\n"
        
        build_metadata = results.get('build_metadata', {})
        chunked_tables = build_metadata.get('chunked_tables', [])
        standard_tables = build_metadata.get('standard_tables', [])
        
        section += "**Processing Strategies:**\n\n"
        section += "```\n"
        section += "┌──────────────────────────────────────────────┐\n"
        section += "│      TRANSFORMATION PIPELINE STAGES          │\n"
        section += "└──────────────────────────────────────────────┘\n"
        section += "\n"
        section += "STAGE 1: Data Loading\n"
        section += "├─► Column Pruning Applied (250+ cols → ~50 cols)\n"
        section += "├─► Memory Reduction: ~10x\n"
        section += "└─► Load Strategy: Bucket-First OR Database\n"
        section += "\n"
        section += "STAGE 2: Dimension Transformation\n"
        section += "├─► Single-Pass Processing\n"
        section += "├─► Business Logic Application\n"
        section += "└─► Storage: Streaming to Warehouse\n"
        section += "\n"
        section += "STAGE 3: Fact Transformation\n"
        section += "├─► Chunked Tables (Memory-Safe):\n"
        
        if chunked_tables:
            for table in chunked_tables:
                section += f"│   └─► {table} (5000 rows/chunk)\n"
        else:
            section += "│   └─► None\n"
        
        section += "├─► Standard Tables (In-Memory):\n"
        if standard_tables:
            for table in standard_tables:
                section += f"│   └─► {table}\n"
        else:
            section += "│   └─► None\n"
        
        section += "└─► Storage: Streaming to Warehouse\n"
        section += "```\n\n"
        
        # Add memory optimization summary
        total_memory = results.get('total_memory_used_mb', 0)
        column_pruning_stats = results.get('column_pruning_stats', {})
        pruning_tables_count = column_pruning_stats.get('total_tables_using_pruning', 0)
        
        section += "**Memory Optimization:**\n"
        section += f"- **Total Memory Used:** {total_memory:.2f} MB\n"
        section += f"- **Tables with Column Pruning:** {pruning_tables_count}\n"
        section += f"- **Tables with Chunking:** {len(chunked_tables)}\n"
        section += f"- **Memory Efficiency:** Column pruning reduces memory by ~10x for large datasets\n"
        
        return section
    
    def generate_data_lineage_section(self, results: Dict[str, Any]) -> str:
        """
        Generate complete data lineage section.
        
        PHASE 5: Main entry point that orchestrates all lineage subsections.
        
        Combines all data lineage visualizations into one comprehensive section.
        
        Args:
            results: Warehouse build results containing lineage metadata
            
        Returns:
            Complete markdown data lineage section
        """
        if self.logger:
            self.logger.debug("[DataLineage] Generating data lineage section...")
        
        sections = []
        
        # Add all sub-sections
        sections.append(self.generate_warehouse_data_flow(results))
        sections.append(self.generate_per_table_lineage(results))
        sections.append(self.generate_transformation_pipeline_diagram(results))
        
        # Join non-empty sections
        full_section = '\n'.join(filter(None, sections))
        
        if self.logger:
            self.logger.debug(f"[DataLineage] Generated section: {len(full_section)} chars")
        
        return full_section


__all__ = ['DataLineageSectionGenerator']
