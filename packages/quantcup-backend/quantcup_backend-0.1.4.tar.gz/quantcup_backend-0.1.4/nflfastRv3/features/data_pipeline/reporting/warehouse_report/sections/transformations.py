"""
Transformation Details Section Generator for Warehouse Reports

PHASE 5: Enhanced report sections with transformation visualization.
Generates comprehensive transformation details showing what business logic
was applied to each warehouse table.

Pattern: Single Responsibility Principle
One class per report section for clear separation of concerns.
"""

from typing import Dict, Any, List


class TransformationDetailsSectionGenerator:
    """
    Generate transformation details sections for warehouse reports.
    
    PHASE 5 Implementation: Visualizes transformation execution and business logic.
    
    Responsibilities:
    - Show transformation overview across all tables
    - Detail business logic applied per table (weather categorization, EPA, etc.)
    - Track source data lineage
    - Multi-source consolidation analysis (injuries from multiple sources)
    
    Pattern: Simple formatter (1 complexity point)
    Complexity: Formats transformation metadata from warehouse build results
    """
    
    def __init__(self, logger=None):
        """
        Initialize transformation details section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_transformation_overview(self, results: Dict[str, Any]) -> str:
        """
        Generate high-level transformation overview.
        
        Shows count of tables by build type and transformation complexity.
        
        Args:
            results: Warehouse build results containing table_details
            
        Returns:
            Markdown section for transformation overview
        """
        section = "## 🔄 Transformation Details\n\n"
        section += "### Transformation Overview\n\n"
        
        # Analyze transformation types across all tables
        dim_details = results.get('dimension_results', {}).get('table_details', {})
        fact_details = results.get('fact_results', {}).get('table_details', {})
        
        # Count by build type
        single_source = []
        multi_source = []
        generated = []
        
        for table_name, details in dim_details.items():
            if details.get('status') == 'success':
                build_type = details.get('build_type', 'unknown')
                if build_type == 'single_source':
                    single_source.append(table_name)
                elif build_type == 'multi_source':
                    multi_source.append(table_name)
                elif build_type == 'generated':
                    generated.append(table_name)
        
        # Facts are typically single-source from play_by_play
        for table_name, details in fact_details.items():
            if details.get('status') == 'success':
                single_source.append(table_name)
        
        total_tables = len(single_source) + len(multi_source) + len(generated)
        
        section += f"**Total Tables Transformed:** {total_tables}\n\n"
        section += "**Transformation Types:**\n"
        section += f"- 📊 **Single-Source Tables:** {len(single_source)} (built from play_by_play)\n"
        section += f"- 🔀 **Multi-Source Tables:** {len(multi_source)} (consolidated from multiple sources)\n"
        section += f"- ⚙️ **Generated Tables:** {len(generated)} (computed/derived data)\n\n"
        
        if single_source:
            section += "**Single-Source Tables:** " + ", ".join(f"`{t}`" for t in single_source) + "\n\n"
        if multi_source:
            section += "**Multi-Source Tables:** " + ", ".join(f"`{t}`" for t in multi_source) + "\n\n"
        if generated:
            section += "**Generated Tables:** " + ", ".join(f"`{t}`" for t in generated) + "\n\n"
        
        return section
    
    def generate_per_table_transformation_details(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed transformation information per table.
        
        Shows specific business logic and transformations applied to each table.
        
        Args:
            results: Warehouse build results containing table_details
            
        Returns:
            Markdown section with per-table transformation details
        """
        section = "### Per-Table Transformation Details\n\n"
        
        dim_details = results.get('dimension_results', {}).get('table_details', {})
        fact_details = results.get('fact_results', {}).get('table_details', {})
        
        # Transformation business logic descriptions (from code analysis)
        transformation_logic = {
            'dim_game': {
                'source': 'play_by_play',
                'logic': [
                    'Weather categorization (clear, cloudy, rain, snow)',
                    'Venue standardization and stadium mapping',
                    'Game type classification (regular, playoff, super bowl)',
                    'Home/away team identification',
                    'Roof type and surface classification'
                ]
            },
            'dim_player': {
                'source': 'play_by_play',
                'logic': [
                    'Player demographics aggregation',
                    'Position standardization',
                    'Team affiliation tracking',
                    'Fantasy platform integration'
                ]
            },
            'dim_date': {
                'source': 'generated',
                'logic': [
                    'Date dimension generation from game dates',
                    'Week/season/year extraction',
                    'Calendar attributes (day of week, month, quarter)'
                ]
            },
            'dim_drive': {
                'source': 'play_by_play',
                'logic': [
                    'Drive-level aggregation from play-by-play',
                    'Drive outcome classification',
                    'Time of possession calculation',
                    'Play count per drive'
                ]
            },
            'injuries': {
                'source': 'multiple (injuries + depth_charts)',
                'logic': [
                    'Multi-source data consolidation',
                    'Injury status standardization',
                    'Team roster integration',
                    'Temporal tracking of injury reports'
                ]
            },
            'player_id_mapping': {
                'source': 'multiple (play_by_play + snap_counts)',
                'logic': [
                    'ID crosswalk generation',
                    'Player identification across data sources',
                    'Name matching and disambiguation'
                ]
            },
            'fact_play': {
                'source': 'play_by_play',
                'logic': [
                    'EPA (Expected Points Added) calculations',
                    'Win probability analysis',
                    'Play type classification',
                    'Down/distance situation encoding',
                    'Chunked processing for memory efficiency (5000+ rows/chunk)'
                ]
            },
            'fact_player_stats': {
                'source': 'play_by_play',
                'logic': [
                    'Player-level statistics aggregation',
                    'Fantasy points calculation',
                    'Performance metrics by position',
                    'Game-level stat rollups'
                ]
            },
            'fact_player_play': {
                'source': 'play_by_play',
                'logic': [
                    'Player-play attribution',
                    'Individual play contributions',
                    'Participation tracking',
                    'Chunked processing for large dataset'
                ]
            }
        }
        
        # Process dimensions
        if dim_details:
            section += "#### Dimension Table Transformations\n\n"
            for table_name in sorted(dim_details.keys()):
                details = dim_details[table_name]
                if details.get('status') == 'success' and table_name in transformation_logic:
                    transform_info = transformation_logic[table_name]
                    build_type = details.get('build_type', 'unknown')
                    source_table = details.get('source_table')
                    
                    section += f"**`{table_name}`** ({build_type})\n\n"
                    section += f"- **Source:** {source_table or transform_info['source']}\n"
                    section += f"- **Rows Built:** {details.get('rows', 0):,}\n"
                    section += "- **Business Logic:**\n"
                    for logic_item in transform_info['logic']:
                        section += f"  - {logic_item}\n"
                    section += "\n"
        
        # Process facts
        if fact_details:
            section += "#### Fact Table Transformations\n\n"
            for table_name in sorted(fact_details.keys()):
                details = fact_details[table_name]
                if details.get('status') == 'success' and table_name in transformation_logic:
                    transform_info = transformation_logic[table_name]
                    processing_type = details.get('processing_type', 'standard')
                    
                    section += f"**`{table_name}`** ({processing_type} processing)\n\n"
                    section += f"- **Source:** {transform_info['source']}\n"
                    section += f"- **Rows Built:** {details.get('rows', 0):,}\n"
                    if processing_type == 'chunked':
                        chunks = details.get('chunks_processed', 0)
                        section += f"- **Chunks Processed:** {chunks}\n"
                    section += "- **Business Logic:**\n"
                    for logic_item in transform_info['logic']:
                        section += f"  - {logic_item}\n"
                    section += "\n"
        
        return section
    
    def generate_multi_source_consolidation_analysis(self, results: Dict[str, Any]) -> str:
        """
        Generate analysis of multi-source table consolidation.
        
        Shows how data from multiple sources was combined into warehouse tables.
        
        Args:
            results: Warehouse build results containing table_details
            
        Returns:
            Markdown section with multi-source consolidation analysis
        """
        dim_details = results.get('dimension_results', {}).get('table_details', {})
        
        # Find multi-source tables
        multi_source_tables = []
        for table_name, details in dim_details.items():
            if details.get('status') == 'success' and details.get('build_type') == 'multi_source':
                multi_source_tables.append((table_name, details))
        
        if not multi_source_tables:
            return ""
        
        section = "### Multi-Source Consolidation\n\n"
        section += "The following tables consolidate data from multiple sources:\n\n"
        
        # Multi-source consolidation details
        consolidation_info = {
            'injuries': {
                'sources': ['injuries', 'depth_charts'],
                'consolidation_logic': [
                    'Merge injury reports from official NFL injury data',
                    'Integrate depth chart information for roster context',
                    'Resolve conflicts between injury status and depth position',
                    'Standardize injury designations across sources'
                ],
                'challenges': [
                    'Different update frequencies between sources',
                    'Injury status terminology variations',
                    'Player name matching across datasets'
                ]
            },
            'player_id_mapping': {
                'sources': ['play_by_play', 'snap_counts', 'roster data'],
                'consolidation_logic': [
                    'Generate unified player ID crosswalk',
                    'Match players across different ID systems (gsis_id, pfr_id, etc.)',
                    'Handle name variations and duplicates',
                    'Maintain historical ID mappings'
                ],
                'challenges': [
                    'ID format differences across sources',
                    'Players changing teams mid-season',
                    'Rookie player onboarding'
                ]
            }
        }
        
        for table_name, details in multi_source_tables:
            if table_name in consolidation_info:
                info = consolidation_info[table_name]
                rows = details.get('rows', 0)
                
                section += f"#### `{table_name}`\n\n"
                section += f"**Rows Built:** {rows:,}\n\n"
                section += f"**Source Tables:**\n"
                for source in info['sources']:
                    section += f"- `{source}`\n"
                section += "\n"
                
                section += "**Consolidation Logic:**\n"
                for logic_item in info['consolidation_logic']:
                    section += f"- {logic_item}\n"
                section += "\n"
                
                section += "**Challenges Addressed:**\n"
                for challenge in info['challenges']:
                    section += f"- {challenge}\n"
                section += "\n"
        
        return section
    
    def generate_transformation_details_section(self, results: Dict[str, Any]) -> str:
        """
        Generate complete transformation details section.
        
        PHASE 5: Main entry point that orchestrates all transformation subsections.
        
        Combines all transformation visualizations into one comprehensive section.
        
        Args:
            results: Warehouse build results containing table_details and transformation metadata
            
        Returns:
            Complete markdown transformation details section
        """
        if self.logger:
            self.logger.debug("[TransformationDetails] Generating transformation details section...")
        
        sections = []
        
        # Add all sub-sections
        sections.append(self.generate_transformation_overview(results))
        sections.append(self.generate_per_table_transformation_details(results))
        
        # Add multi-source analysis if applicable
        multi_source_section = self.generate_multi_source_consolidation_analysis(results)
        if multi_source_section:
            sections.append(multi_source_section)
        
        # Join non-empty sections
        full_section = '\n'.join(filter(None, sections))
        
        if self.logger:
            self.logger.debug(f"[TransformationDetails] Generated section: {len(full_section)} chars")
        
        return full_section


__all__ = ['TransformationDetailsSectionGenerator']
