"""
Warehouse Report Generator

Main orchestrator for warehouse build report generation.
Composes section generators to produce comprehensive reports.

Pattern: Minimum Viable Decoupling (2 complexity points)
Architecture: Facade pattern with composition
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .sections import (
    SummarySectionGenerator,
    DimensionsSectionGenerator,
    FactsSectionGenerator,
    PerformanceSectionGenerator,
    StorageHealthSectionGenerator,
    SchemaEvolutionSectionGenerator,
    TransformationDetailsSectionGenerator,  # PHASE 5
    DataLineageSectionGenerator  # PHASE 5
)
from ..common.config import REPORT_OUTPUT_DIR
from ..common.templates import create_report_footer


class WarehouseReportGenerator:
    """
    Main orchestrator for warehouse build report generation.
    
    Composition Pattern: Delegates section generation to specialized generators:
    - SummarySectionGenerator: Header, executive summary, warehouse context (PHASE 5 Enhanced)
    - DimensionsSectionGenerator: Dimension table breakdown and analysis (PHASE 5 Enhanced)
    - FactsSectionGenerator: Fact table breakdown, chunking analysis (PHASE 5 Enhanced)
    - PerformanceSectionGenerator: Memory optimization, build efficiency (PHASE 5 Enhanced)
    - StorageHealthSectionGenerator: Storage configuration and sync status
    - SchemaEvolutionSectionGenerator: PHASE 5 - Schema change detection and drift tracking
    - TransformationDetailsSectionGenerator: PHASE 5 NEW - Transformation business logic details
    - DataLineageSectionGenerator: PHASE 5 NEW - Data flow visualization
    
    Backward Compatibility: Mirrors pipeline report generator pattern
    """
    
    def __init__(self, logger=None):
        """
        Initialize warehouse report generator with composed section generators.
        
        PHASE 5: Added transformation and lineage section generators.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        
        # Compose section generators
        self.summary_gen = SummarySectionGenerator(logger=logger)
        self.dimensions_gen = DimensionsSectionGenerator(logger=logger)
        self.facts_gen = FactsSectionGenerator(logger=logger)
        self.performance_gen = PerformanceSectionGenerator(logger=logger)
        self.storage_gen = StorageHealthSectionGenerator(logger=logger)
        self.schema_gen = SchemaEvolutionSectionGenerator(logger=logger)
        
        # PHASE 5: New section generators
        self.transformation_gen = TransformationDetailsSectionGenerator(logger=logger)
        self.lineage_gen = DataLineageSectionGenerator(logger=logger)
    
    def generate_report(
        self,
        results: Dict[str, Any],
        seasons: Optional[List[int]] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive markdown warehouse build report.
        
        Orchestrates report generation by delegating to section generators.
        
        Args:
            results: Warehouse build results from WarehouseBuilder.build_all_tables()
                Expected structure:
                {
                    'status': 'success' | 'partial' | 'failed',
                    'tables_built': List[str],  # Table names built
                    'total_rows': int,  # Total rows across all tables
                    'dimension_results': {
                        'status': str,
                        'tables': List[str],
                        'total_rows': int,
                        'table_details': {
                            'table_name': {
                                'status': 'success' | 'failed',
                                'rows': int,
                                'columns': int,
                                'error': str (if failed)
                            }
                        },
                        'success_rate': float
                    },
                    'fact_results': {
                        'status': str,
                        'tables': List[str],
                        'total_rows': int,
                        'table_details': {
                            'table_name': {
                                'status': 'success' | 'failed',
                                'rows': int,
                                'processing_type': 'chunked' | 'standard',
                                'chunks_processed': int (if chunked),
                                'performance_metrics': dict (optional),
                                'columns': int (if standard),
                                'error': str (if failed)
                            }
                        },
                        'success_rate': float
                    },
                    'performance_metrics': {
                        'dimensions_built': int,
                        'facts_built': int,
                        'total_tables': int,
                        'build_success_rate': float
                    }
                }
            seasons: Optional list of seasons processed
            output_dir: Directory to save report (default: reports/data_pipeline)
            
        Returns:
            str: Path to generated report
        """
        if not output_dir:
            output_dir = REPORT_OUTPUT_DIR
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'warehouse_report_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build report sections (orchestrate)
        report_sections = []
        
        # 1. Header and summary sections
        report_sections.append(self.summary_gen.generate_header(results, seasons=seasons))
        report_sections.append(self.summary_gen.generate_executive_summary(results))
        report_sections.append(self.summary_gen.generate_warehouse_context())
        report_sections.append(self.summary_gen.generate_tables_overview(results))
        
        # 2. PHASE 5 NEW: Transformation Details section
        if self.logger:
            self.logger.info("[WarehouseReport] Generating transformation details section...")
        transformation_section = self.transformation_gen.generate_transformation_details_section(results)
        if transformation_section:
            report_sections.append(transformation_section)
            if self.logger:
                self.logger.info(f"[WarehouseReport] Transformation section added to report ({len(transformation_section)} chars)")
        
        # 3. Dimension tables sections (PHASE 5 Enhanced)
        report_sections.append(self.dimensions_gen.generate_dimensions_breakdown(results))
        report_sections.append(self.dimensions_gen.generate_dimensions_summary_table(results))
        
        # 4. Fact tables sections (PHASE 5 Enhanced)
        report_sections.append(self.facts_gen.generate_facts_breakdown(results))
        report_sections.append(self.facts_gen.generate_facts_summary_table(results))
        report_sections.append(self.facts_gen.generate_chunking_analysis(results))
        
        # 5. Performance sections (PHASE 5 Enhanced)
        report_sections.append(self.performance_gen.generate_performance_summary(results))
        report_sections.append(self.performance_gen.generate_build_efficiency_metrics(results))
        report_sections.append(self.performance_gen.generate_memory_optimization_analysis(results))
        report_sections.append(self.performance_gen.generate_optimization_recommendations(results))
        
        # 6. PHASE 5 NEW: Data Lineage section
        if self.logger:
            self.logger.info("[WarehouseReport] Generating data lineage section...")
        lineage_section = self.lineage_gen.generate_data_lineage_section(results)
        if lineage_section:
            report_sections.append(lineage_section)
            if self.logger:
                self.logger.info(f"[WarehouseReport] Data lineage section added to report ({len(lineage_section)} chars)")
        
        # 7. Storage Health section
        if self.logger:
            self.logger.info("[WarehouseReport] Generating storage health section...")
        storage_section = self.storage_gen.generate_storage_health_summary(results)
        if storage_section:
            report_sections.append(storage_section)
            if self.logger:
                self.logger.info(f"[WarehouseReport] Storage section added to report ({len(storage_section)} chars)")
        else:
            if self.logger:
                self.logger.warning("[WarehouseReport] Storage section is EMPTY - not added to report")
        
        # 8. PHASE 5: Schema Evolution section
        if self.logger:
            self.logger.info("[WarehouseReport] Generating schema evolution section...")
        schema_section = self.schema_gen.generate_schema_evolution_section(results)
        if schema_section:
            report_sections.append(schema_section)
            if self.logger:
                schema_changes_count = len(results.get('schema_changes', []))
                self.logger.info(
                    f"[WarehouseReport] Schema evolution section added to report "
                    f"({schema_changes_count} changes, {len(schema_section)} chars)"
                )
        else:
            if self.logger:
                self.logger.warning("[WarehouseReport] Schema evolution section is EMPTY - not added to report")
        
        # 9. Footer
        report_sections.append(create_report_footer())
        
        # Write report
        report_content = '\n\n'.join(filter(None, report_sections))  # Filter out None/empty sections
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Warehouse report saved: {report_path}")
        
        return str(report_path)


def create_warehouse_report_generator(logger=None):
    """
    Factory function to create warehouse report generator.
    
    Maintains backward compatibility with factory pattern.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        WarehouseReportGenerator: Configured report generator
    """
    return WarehouseReportGenerator(logger=logger)


__all__ = ['WarehouseReportGenerator', 'create_warehouse_report_generator']
