"""
Pipeline Ingestion Reporting Module

Generates comprehensive reports for data pipeline ingestion operations.
Tracks metrics like rows fetched, data loss, storage success rates, and failures.

Pattern: Facade pattern with section generators
Architecture: Mirrors ML pipeline reporting structure
"""

from .generator import PipelineReportGenerator, create_pipeline_report_generator

__all__ = ['PipelineReportGenerator', 'create_pipeline_report_generator']
