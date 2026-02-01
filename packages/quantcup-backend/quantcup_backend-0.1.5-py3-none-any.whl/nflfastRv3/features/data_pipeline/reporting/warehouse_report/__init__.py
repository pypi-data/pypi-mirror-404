"""
Warehouse Build Report Generation Module

Comprehensive reporting for warehouse table building operations.
Tracks dimensions, facts, performance metrics, and memory optimization.

Pattern: Minimum Viable Decoupling (1 complexity point - exports only)
Architecture: Follows pipeline_report pattern for consistency
"""

from .generator import WarehouseReportGenerator, create_warehouse_report_generator

__all__ = ['WarehouseReportGenerator', 'create_warehouse_report_generator']
