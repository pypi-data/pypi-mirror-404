"""
Reporting components for data pipeline.

Follows the same pattern as ML pipeline reporting.
Provides automatic report generation for pipeline operations.
"""

from .orchestrator import ReportOrchestrator, create_report_orchestrator

# Import report generators as they are implemented
# Phase 2: Pipeline Report
try:
    from .pipeline_report import PipelineReportGenerator, create_pipeline_report_generator
    _has_pipeline_report = True
except ImportError:
    _has_pipeline_report = False

# Phase 3: Warehouse Report
try:
    from .warehouse_report import WarehouseReportGenerator, create_warehouse_report_generator
    _has_warehouse_report = True
except ImportError:
    _has_warehouse_report = False

# Phase 4: Storage Report
try:
    from .storage_report import StorageReportGenerator, create_storage_report_generator
    _has_storage_report = True
except ImportError:
    _has_storage_report = False


# Build __all__ dynamically based on what's available
__all__ = [
    'ReportOrchestrator',
    'create_report_orchestrator',
]

if _has_pipeline_report:
    __all__.extend([
        'PipelineReportGenerator',
        'create_pipeline_report_generator',
    ])

if _has_warehouse_report:
    __all__.extend([
        'WarehouseReportGenerator',
        'create_warehouse_report_generator',
    ])

if _has_storage_report:
    __all__.extend([
        'StorageReportGenerator',
        'create_storage_report_generator',
    ])
