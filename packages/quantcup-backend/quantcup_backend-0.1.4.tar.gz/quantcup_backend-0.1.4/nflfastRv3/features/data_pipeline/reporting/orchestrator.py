"""
Data Pipeline Report Generation Orchestrator

Context-aware report orchestration that delegates to specialized report generators.
Keeps CLI thin by centralizing all reporting business logic here.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Business Logic - orchestrates report generators)
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from logging import Logger


class ReportOrchestrator:
    """
    Context-aware report orchestration for data pipeline.
    
    Determines which report generator to use based on operation type.
    Centralizes reporting business logic, keeping implementation layer thin.
    
    Pattern: Strategy Pattern
    Complexity: 2 points (orchestration + delegation)
    Depth: 1 layer (delegates to report generators)
    """
    
    @staticmethod
    def generate_pipeline_report(
        result: Dict[str, Any],
        logger=None
    ) -> Optional[str]:
        """
        Generate detailed pipeline ingestion report.
        
        Extracts data from pipeline result and delegates to PipelineReportGenerator.
        
        Args:
            result: Pipeline result dictionary from DataPipeline.process()
                Expected structure:
                {
                    'status': 'success' | 'partial' | 'error',
                    'sources_processed': int,
                    'total_rows': int,
                    'duration': float,
                    'source_details': {...},
                    'storage_results': {...}
                }
            logger: Optional logger instance
            
        Returns:
            str: Path to generated report, or None if report generation failed
        """
        # Add early logging for debugging
        if logger:
            logger.info(f"[ReportOrchestrator] Starting pipeline report generation (status: {result.get('status')})")
            logger.debug(f"[ReportOrchestrator] Result keys: {list(result.keys())}")
        
        # Generate report for success or partial (some sources succeeded)
        status = result.get('status')
        if status not in ('success', 'partial'):
            if logger:
                logger.warning(f"[ReportOrchestrator] Cannot generate pipeline report - invalid status: {status}")
            return None
        
        try:
            # Import here to avoid circular dependencies
            if logger:
                logger.debug("[ReportOrchestrator] Importing pipeline report generator...")
            from nflfastRv3.features.data_pipeline.reporting.pipeline_report import create_pipeline_report_generator
            
            if logger:
                logger.debug("[ReportOrchestrator] Creating report generator instance...")
            report_generator = create_pipeline_report_generator(logger=logger)
            
            if logger:
                logger.info("[ReportOrchestrator] Generating pipeline report...")
            report_path = report_generator.generate_report(result)
            
            if logger:
                if report_path:
                    logger.info(f"[ReportOrchestrator] ✅ Pipeline report generated successfully: {report_path}")
                else:
                    logger.warning("[ReportOrchestrator] Report generator returned None")
            
            return report_path
            
        except ImportError as e:
            if logger:
                logger.error(f"[ReportOrchestrator] Pipeline report generator not available: {e}", exc_info=True)
            return None
        except Exception as e:
            if logger:
                logger.error(f"[ReportOrchestrator] ❌ Failed to generate pipeline report: {e}", exc_info=True)
            return None
    
    @staticmethod
    def generate_warehouse_report(
        results: Dict[str, Any],
        seasons: Optional[List[int]] = None,
        logger=None
    ) -> Optional[str]:
        """
        Generate detailed warehouse build report.
        
        Delegates to WarehouseReportGenerator for comprehensive build analysis.
        
        Args:
            results: Warehouse build results from WarehouseBuilder.build_all_tables()
                Expected structure:
                {
                    'status': 'success' | 'partial' | 'error',
                    'tables_built': int,
                    'total_tables': int,
                    'build_results': {...},
                    'performance': {...}
                }
            seasons: Optional list of seasons processed
            logger: Optional logger instance
            
        Returns:
            str: Path to generated report, or None if report generation failed
        """
        # Generate report for success or partial (some tables built)
        status = results.get('status') if results else None
        if not results or status not in ('success', 'partial'):
            if logger:
                logger.warning(f"Cannot generate warehouse report - status: {status}")
            return None
        
        try:
            # Import here to avoid circular dependencies
            # Will be implemented in Phase 3
            from .warehouse_report import create_warehouse_report_generator
            
            report_generator = create_warehouse_report_generator(logger=logger)
            report_path = report_generator.generate_report(results, seasons=seasons)
            
            return report_path
            
        except ImportError:
            if logger:
                logger.debug("Warehouse report generator not yet implemented (Phase 3)")
            return None
        except Exception as e:
            if logger:
                logger.warning(f"Failed to generate warehouse report: {e}")
            return None
    


def create_report_orchestrator(logger=None):
    """
    Factory function to create report orchestrator.
    
    Note: ReportOrchestrator uses static methods, so this returns the class itself.
    Provided for consistency with other create_* factory functions.
    
    Args:
        logger: Optional logger instance (unused - kept for API consistency)
        
    Returns:
        ReportOrchestrator: Report orchestrator class
    """
    return ReportOrchestrator


__all__ = ['ReportOrchestrator', 'create_report_orchestrator']
