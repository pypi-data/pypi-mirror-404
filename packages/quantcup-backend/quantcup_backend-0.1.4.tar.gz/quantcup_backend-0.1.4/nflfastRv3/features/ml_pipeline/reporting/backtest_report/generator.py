"""
Backtest Report Generator

Main orchestrator that coordinates section generators to create complete reports.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..analyzers import create_metrics_analyzer
from .sections import (
    SummarySectionGenerator,
    ResultsSectionGenerator,
    TrendsSectionGenerator,
    StabilitySectionGenerator,
    StatisticsSectionGenerator,
    RecommendationsSectionGenerator,
)


class BacktestReportGenerator:
    """
    Backtest report orchestrator.
    
    Aggregates training results across multiple years to show
    model stability and performance trends over time.
    
    Pattern: Composition-based orchestration
    """
    
    def __init__(self, logger=None):
        """
        Initialize backtest report generator with section generators.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        
        # Initialize section generators
        self.summary_gen = SummarySectionGenerator(logger=logger)
        self.results_gen = ResultsSectionGenerator(logger=logger)
        self.trends_gen = TrendsSectionGenerator(logger=logger)
        self.stability_gen = StabilitySectionGenerator(logger=logger)
        self.statistics_gen = StatisticsSectionGenerator(logger=logger)
        self.recommendations_gen = RecommendationsSectionGenerator(logger=logger)
    
    def generate_report(
        self,
        backtest_results: List[Dict[str, Any]],
        model_name: str,
        train_years: int,
        start_year: int,
        end_year: int,
        test_week: Optional[int] = None,
        output_dir: str = 'reports/backtests'
    ) -> str:
        """
        Generate comprehensive backtest report.
        
        Note:
            TODO: If generating multiple artifact types (e.g., predictions CSV, performance plots),
            consider using timestamped subfolders: 'reports/backtests/backtest_{timestamp}' to group
            related artifacts. See scripts/analyze_pbp_odds_data_v4.py for reference.
        
        Args:
            backtest_results: List of training results from each iteration
            model_name: Model name
            train_years: Number of training years
            start_year: Backtest start year
            end_year: Backtest end year
            test_week: Optional specific test week
            output_dir: Directory to save report
            
        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        week_suffix = f"_week{test_week}" if test_week else ""
        report_filename = f'backtest_report_{model_name}_{start_year}_{end_year}{week_suffix}_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build report sections
        report_sections = []
        
        # Summary section (header, exec summary, benchmarking)
        report_sections.append(
            self.summary_gen.generate(
                model_name=model_name,
                train_years=train_years,
                start_year=start_year,
                end_year=end_year,
                test_week=test_week,
                backtest_results=backtest_results
            )
        )
        
        # Add feature selection audit (same features used across all test years)
        if backtest_results and 'X_train' in backtest_results[0] and 'X_test' in backtest_results[0]:
            analyzer = create_metrics_analyzer()
            first_result = backtest_results[0]
            audit_section = analyzer.analyze_feature_selection_audit(
                first_result['X_train'],
                first_result['X_test'],
                first_result.get('y_train')
            )
            # Add context note for backtest reports
            audit_with_note = audit_section.replace(
                "\n## Feature Selection Audit",
                "\n## Feature Selection Audit\n\n**Note:** The same feature set is used across all " +
                f"{len(backtest_results)} test years. This audit shows which features contributed to " +
                "the backtest results above."
            )
            report_sections.append(audit_with_note)
        
        # Results and trends sections
        report_sections.append(
            self.results_gen.generate(backtest_results=backtest_results)
        )
        report_sections.append(
            self.trends_gen.generate(backtest_results=backtest_results)
        )
        
        # Advanced analysis sections
        report_sections.append(
            self.statistics_gen.generate(backtest_results=backtest_results)
        )
        report_sections.append(
            self.stability_gen.generate(backtest_results=backtest_results)
        )
        
        # Recommendations
        report_sections.append(
            self.recommendations_gen.generate(
                backtest_results=backtest_results,
                train_years=train_years
            )
        )
        
        # Write report
        report_content = '\n\n'.join(s for s in report_sections if s)
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Backtest report saved: {report_path}")
        
        return str(report_path)


__all__ = ['BacktestReportGenerator']
