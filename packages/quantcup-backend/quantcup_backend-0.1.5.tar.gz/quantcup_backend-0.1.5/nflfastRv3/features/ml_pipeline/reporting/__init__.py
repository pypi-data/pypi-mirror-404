"""
Reporting components for ML pipeline.

Follows the same pattern as feature_sets/ and models/.
"""

from .analyzers import MetricsAnalyzer, create_metrics_analyzer
from .orchestrator import ReportOrchestrator, create_report_orchestrator
from .training_report import TrainingReportGenerator, create_report_generator
from .prediction_reporter import PredictionReportGenerator, create_prediction_report_generator
from .backtest_report import BacktestReportGenerator, create_backtest_reporter
from .optimize_report import OptimizationReportGenerator, create_optimize_reporter
from .feature_report import FeatureReportGenerator, create_feature_reporter
from .market_analysis import MarketComparisonAnalyzer, create_market_analyzer


__all__ = [
    'MetricsAnalyzer',
    'create_metrics_analyzer',
    'ReportOrchestrator',
    'create_report_orchestrator',
    'TrainingReportGenerator',
    'create_report_generator',
    'PredictionReportGenerator',
    'create_prediction_report_generator',
    'BacktestReportGenerator',
    'create_backtest_reporter',
    'OptimizationReportGenerator',
    'create_optimize_reporter',
    'FeatureReportGenerator',
    'create_feature_reporter',
    'MarketComparisonAnalyzer',
    'create_market_analyzer',
]