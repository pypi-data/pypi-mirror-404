"""
Common utilities for data pipeline reporting.

Provides shared functionality across all report generators.
"""

from .config import (
    REPORT_OUTPUT_DIR,
    STATUS_INDICATORS,
    DATA_LOSS_THRESHOLDS,
    STORAGE_EFFICIENCY_THRESHOLDS,
    SUCCESS_RATE_THRESHOLDS,
    get_status_indicator,
    get_data_loss_rating,
    get_storage_efficiency_rating,
)
from .formatters import (
    format_markdown_table,
    format_section_header,
    format_metric_row,
    format_code_block,
    format_list_items,
    format_bytes,
    format_duration,
    format_percentage,
)
from .metrics import (
    calculate_success_rate,
    calculate_data_loss_percentage,
    calculate_storage_efficiency,
    calculate_velocity,
    calculate_memory_usage_mb,
)
from .templates import (
    REPORT_HEADER_TEMPLATE,
    SECTION_DIVIDER,
    FOOTER_TEMPLATE,
    create_report_header,
    create_report_footer,
    SUMMARY_SECTION_TEMPLATE,
    METRICS_TABLE_TEMPLATE,
)

__all__ = [
    # Config
    'REPORT_OUTPUT_DIR',
    'STATUS_INDICATORS',
    'DATA_LOSS_THRESHOLDS',
    'STORAGE_EFFICIENCY_THRESHOLDS',
    'SUCCESS_RATE_THRESHOLDS',
    'get_status_indicator',
    'get_data_loss_rating',
    'get_storage_efficiency_rating',
    # Formatters
    'format_markdown_table',
    'format_section_header',
    'format_metric_row',
    'format_code_block',
    'format_list_items',
    'format_bytes',
    'format_duration',
    'format_percentage',
    # Metrics
    'calculate_success_rate',
    'calculate_data_loss_percentage',
    'calculate_storage_efficiency',
    'calculate_velocity',
    'calculate_memory_usage_mb',
    # Templates
    'REPORT_HEADER_TEMPLATE',
    'SECTION_DIVIDER',
    'FOOTER_TEMPLATE',
    'create_report_header',
    'create_report_footer',
    'SUMMARY_SECTION_TEMPLATE',
    'METRICS_TABLE_TEMPLATE',
]
