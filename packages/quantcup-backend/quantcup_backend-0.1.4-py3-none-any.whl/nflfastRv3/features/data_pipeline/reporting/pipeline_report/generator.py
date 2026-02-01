"""
Pipeline Report Generator

Main orchestrator for pipeline ingestion report generation.
Composes section generators to produce comprehensive reports.

Pattern: Minimum Viable Decoupling (2 complexity points)
Architecture: Facade pattern with composition
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .sections import (
    SummarySectionGenerator,
    SourceDetailsSectionGenerator,
    QualitySectionGenerator,
    FailuresSectionGenerator,
    PipelineStorageHealthSectionGenerator,
    PerformanceSectionGenerator,
    DataLineageSectionGenerator
)
from ..common.config import REPORT_OUTPUT_DIR
from ..common.templates import create_report_footer


class PipelineReportGenerator:
    """
    Main orchestrator for pipeline ingestion report generation.
    
    Composition Pattern: Delegates section generation to specialized generators:
    - SummarySectionGenerator: Header, executive summary, pipeline context (ENHANCED Phase 1-4)
    - SourceDetailsSectionGenerator: Per-source breakdown and loading strategies (ENHANCED Phase 1-3)
    - QualitySectionGenerator: Data quality, loss tracking, schema validation (ENHANCED Phase 4)
    - PerformanceSectionGenerator: Performance metrics, bottlenecks, timing (NEW Phase 3)
    - DataLineageSectionGenerator: Data flow visualization, retention analysis (NEW Phase 1)
    - FailuresSectionGenerator: Error analysis, circuit breakers, recovery (ENHANCED Phase 2)
    - PipelineStorageHealthSectionGenerator: Storage health summary
    
    Backward Compatibility: Mirrors ML pipeline TrainingReportGenerator pattern
    """
    
    def __init__(self, logger=None):
        """
        Initialize pipeline report generator with composed section generators.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        
        # Compose section generators
        self.summary_gen = SummarySectionGenerator(logger=logger)
        self.source_details_gen = SourceDetailsSectionGenerator(logger=logger)
        self.quality_gen = QualitySectionGenerator(logger=logger)
        self.performance_gen = PerformanceSectionGenerator(logger=logger)  # NEW Phase 3
        self.lineage_gen = DataLineageSectionGenerator(logger=logger)  # NEW Phase 1
        self.failures_gen = FailuresSectionGenerator(logger=logger)
        self.storage_gen = PipelineStorageHealthSectionGenerator(logger=logger)
    
    def generate_report(
        self,
        result: Dict[str, Any],
        output_dir: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive markdown pipeline ingestion report.
        
        Orchestrates report generation by delegating to section generators.
        
        Args:
            result: Pipeline result dictionary from DataPipeline.process()
                Expected structure:
                {
                    'status': 'success' | 'warning' | 'error',
                    'tables': List[str],  # Table names processed
                    'total_rows': int,  # Total rows processed
                    'group_results': {
                        'group_name': {
                            'status': 'success' | 'failed',
                            'rows': int,
                            'error': str (if failed),
                            'source_details': {
                                'source_name': {
                                    'rows': int,
                                    'rows_fetched': int (optional),
                                    'rows_after_cleaning': int (optional),
                                    'status': str (optional),
                                    'error': str (optional)
                                }
                            }
                        }
                    },
                    'duration': float (optional),
                    'quality_metrics': dict (optional),
                    'schema_issues': List[dict] (optional),
                    'circuit_breaker_activations': List[dict] (optional),
                    'storage_failures': List[dict] (optional)
                }
            output_dir: Directory to save report (default: reports/data_pipeline)
            
        Returns:
            str: Path to generated report
        """
        if not output_dir:
            output_dir = REPORT_OUTPUT_DIR
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'pipeline_report_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build report sections (orchestrate)
        report_sections = []
        
        # 1. Header and summary sections
        report_sections.append(self.summary_gen.generate_header(result))
        report_sections.append(self.summary_gen.generate_executive_summary(result))
        report_sections.append(self.summary_gen.generate_data_pipeline_context())
        
        # 2. Source details sections
        report_sections.append(self.source_details_gen.generate_source_breakdown(result))
        report_sections.append(self.source_details_gen.generate_loading_strategy_details())
        
        # 3. Data quality sections
        report_sections.append(self.quality_gen.generate_quality_metrics(result))
        report_sections.append(self.quality_gen.generate_quality_recommendations(result))
        
        # 4. Performance metrics section (NEW - Phase 3 & 5)
        # Always show section - includes messaging when data unavailable
        report_sections.append(self.performance_gen.generate_performance_analysis(result))
        
        # 5. Data lineage section (NEW - Phase 1 & 5)
        # Always show section - includes messaging when data unavailable
        report_sections.append(self.lineage_gen.generate_data_lineage(result))
        
        # 6. Failure analysis sections (ENHANCED Phase 2)
        report_sections.append(self.failures_gen.generate_failures_analysis(result))
        
        # 7. Storage Health section
        if self.logger:
            self.logger.info("[PipelineReport] Generating storage health section...")
        storage_section = self.storage_gen.generate_storage_health_summary(result)
        if storage_section:
            report_sections.append(storage_section)
            if self.logger:
                self.logger.info(f"[PipelineReport] Storage section added to report ({len(storage_section)} chars)")
        else:
            if self.logger:
                self.logger.warning("[PipelineReport] Storage section is EMPTY - not added to report")
        
        # 8. Footer
        report_sections.append(create_report_footer())
        
        # Write report
        report_content = '\n\n'.join(filter(None, report_sections))  # Filter out None/empty sections
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Pipeline report saved: {report_path}")
        
        return str(report_path)


def create_pipeline_report_generator(logger=None):
    """
    Factory function to create pipeline report generator.
    
    Maintains backward compatibility with factory pattern.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        PipelineReportGenerator: Configured report generator
    """
    return PipelineReportGenerator(logger=logger)


__all__ = ['PipelineReportGenerator', 'create_pipeline_report_generator']
