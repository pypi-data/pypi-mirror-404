"""
Window Optimization Report Generator

Main orchestrator that composes section generators to build complete optimization reports.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from ..analyzers import create_metrics_analyzer
from .sections import (
    SummarySectionGenerator,
    WindowComparisonSectionGenerator,
    RecommendationsSectionGenerator,
)


class OptimizationReportGenerator:
    """
    Window optimization report orchestrator.
    
    Aggregates training results across different window sizes to identify
    the optimal amount of training data for a specific test period.
    
    Pattern: Composition-based section generation
    """
    
    def __init__(self, logger=None):
        """
        Initialize with optional logger.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        
        # Compose section generators
        self.summary = SummarySectionGenerator(logger)
        self.window_comparison = WindowComparisonSectionGenerator(logger)
        self.recommendations = RecommendationsSectionGenerator(logger)
    
    def generate_report(
        self,
        optimization_results: List[Dict[str, Any]],
        model_name: str,
        test_year: int,
        test_week: int,
        min_years: int,
        max_years: int,
        output_dir: str = 'reports/optimization'
    ) -> str:
        """
        Generate comprehensive window optimization report.
        
        Note:
            TODO: If generating multiple artifact types (e.g., optimization results CSV, comparison plots),
            consider using timestamped subfolders: 'reports/optimization/opt_{timestamp}' to group
            related artifacts. See scripts/analyze_pbp_odds_data_v4.py for reference.
        
        Args:
            optimization_results: List of training results from each window size
            model_name: Model name
            test_year: Test year
            test_week: Test week
            min_years: Minimum training years tested
            max_years: Maximum training years tested
            output_dir: Directory to save report
            
        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'optimization_report_{model_name}_{test_year}_week{test_week}_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build report sections
        report_sections = []
        
        # Header and summary
        report_sections.append(
            self.summary.generate_header(model_name, test_year, test_week, min_years, max_years)
        )
        report_sections.append(
            self.summary.generate_executive_summary(optimization_results)
        )
        report_sections.append(
            self.summary.generate_nfl_benchmarking_context()
        )
        
        # Add feature selection audit (same features used across all window sizes)
        if optimization_results and 'X_train' in optimization_results[0] and 'X_test' in optimization_results[0]:
            analyzer = create_metrics_analyzer()
            # Use the optimal result's data for the audit
            best_result = max(optimization_results, key=lambda x: x['metrics'].get('accuracy', 0))
            audit_section = analyzer.analyze_feature_selection_audit(
                best_result['X_train'],
                best_result['X_test'],
                best_result.get('y_train')
            )
            # Add context note for optimization reports
            audit_with_note = audit_section.replace(
                "\n## Feature Selection Audit",
                "\n## Feature Selection Audit\n\n**Note:** The same feature set is used across all " +
                f"{len(optimization_results)} window sizes tested. This audit shows which features " +
                "contributed to finding the optimal training window."
            )
            report_sections.append(audit_with_note)
        
        # Window comparison sections
        report_sections.append(
            self.window_comparison.generate_comparison_table(optimization_results)
        )
        report_sections.append(
            self.window_comparison.generate_optimal_window_analysis(optimization_results)
        )
        report_sections.append(
            self.window_comparison.generate_diminishing_returns_analysis(optimization_results)
        )
        
        # Recommendations
        report_sections.append(
            self.recommendations.generate(optimization_results, test_year, test_week)
        )
        
        # Write report
        report_content = '\n\n'.join(report_sections)
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Optimization report saved: {report_path}")
        
        return str(report_path)


__all__ = ['OptimizationReportGenerator']
