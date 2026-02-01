"""
Shared utilities for reporting components.

This module provides common formatters, metrics, templates and configuration
used across all report generators.
"""

from .formatters import (
    format_markdown_table,
    format_section_header,
    format_metric_row,
    format_code_block
)

from .templates import (
    REPORT_HEADER_TEMPLATE,
    SECTION_DIVIDER,
    FOOTER_TEMPLATE
)

from .config import (
    NFL_PERFORMANCE_THRESHOLDS,
    CONSISTENCY_THRESHOLDS,
    FEATURE_STABILITY_THRESHOLDS,
    ROI_BREAKEVEN_ACCURACY,
    ROI_PAYOUT_MULTIPLIER_110,
    STATISTICAL_SIGNIFICANCE_ALPHA,
    STATISTICAL_TEST_HYPOTHESES,
    NFL_BENCHMARKING_TEXT,
    get_performance_rating,
    get_consistency_rating,
    get_feature_stability_rating,
)

from .metrics import (
    calculate_roi,
    calculate_coefficient_of_variation,
)

from .correlation_utils import (
    safe_correlation,
    safe_corrwith,
    safe_corr_matrix,
)

__all__ = [
    # Formatters
    'format_markdown_table',
    'format_section_header',
    'format_metric_row',
    'format_code_block',
    # Templates
    'REPORT_HEADER_TEMPLATE',
    'SECTION_DIVIDER',
    'FOOTER_TEMPLATE',
    # Config
    'NFL_PERFORMANCE_THRESHOLDS',
    'CONSISTENCY_THRESHOLDS',
    'FEATURE_STABILITY_THRESHOLDS',
    'ROI_BREAKEVEN_ACCURACY',
    'ROI_PAYOUT_MULTIPLIER_110',
    'STATISTICAL_SIGNIFICANCE_ALPHA',
    'STATISTICAL_TEST_HYPOTHESES',
    'NFL_BENCHMARKING_TEXT',
    'get_performance_rating',
    'get_consistency_rating',
    'get_feature_stability_rating',
    # Metrics
    'calculate_roi',
    'calculate_coefficient_of_variation',
    # Correlation utilities
    'safe_correlation',
    'safe_corrwith',
    'safe_corr_matrix',
]
