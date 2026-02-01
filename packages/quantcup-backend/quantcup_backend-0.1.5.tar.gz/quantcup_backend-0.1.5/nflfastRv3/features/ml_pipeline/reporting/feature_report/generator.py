"""
Feature Report - Main Generator

Orchestrates feature engineering report generation.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .sections import (
    HeaderSectionGenerator,
    SummarySectionGenerator,
    OverviewSectionGenerator,
    StatisticsSectionGenerator,
    QualitySectionGenerator,
    RecommendationsSectionGenerator,
)


class FeatureReportGenerator:
    """
    Feature engineering report orchestrator.
    
    Composes section generators to build comprehensive feature engineering reports.
    
    Pattern: Composition (delegates to section generators)
    Complexity: Low (orchestration only)
    """
    
    def __init__(self, logger=None):
        """
        Initialize report generator with section generators.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        
        # Initialize section generators
        self.header_gen = HeaderSectionGenerator(logger)
        self.summary_gen = SummarySectionGenerator(logger)
        self.overview_gen = OverviewSectionGenerator(logger)
        self.stats_gen = StatisticsSectionGenerator(logger)
        self.quality_gen = QualitySectionGenerator(logger)
        self.recommendations_gen = RecommendationsSectionGenerator(logger)
    
    def generate_report(
        self,
        results: Dict[str, Any],
        output_dir: str = 'reports/features'
    ) -> str:
        """
        Generate comprehensive feature engineering report.
        
        Note:
            TODO: If generating multiple artifact types (e.g., feature CSVs, correlation matrices),
            consider using timestamped subfolders: 'reports/features/features_{timestamp}' to group
            related artifacts. See scripts/analyze_pbp_odds_data_v4.py for reference.
        
        Args:
            results: Feature engineering results dict from FeatureEngineerImplementation
                Expected structure:
                {
                    'status': 'success' | 'partial' | 'error',
                    'features_built': int,
                    'total_features': int,
                    'total_rows': int,
                    'results': {
                        'feature_name': {
                            'status': 'success' | 'failed',
                            'rows_built': int,
                            'error': str (optional),
                            'statistics': {
                                'columns': {...},
                                'correlations': {...},
                                'variance_analysis': {...},
                                'temporal_stability': {...}
                            }
                        }
                    }
                }
            output_dir: Directory to save report
            
        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'feature_report_{timestamp}.md'
        report_path = Path(output_dir) / report_filename
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate report sections using composed generators
        report_sections = [
            self.header_gen.generate(),
            self.summary_gen.generate(results),
            self.overview_gen.generate_overview(),
            self.overview_gen.generate_details(results),
            self.stats_gen.generate_column_inventory(results),
            self.stats_gen.generate_correlation_analysis(results),
            self.stats_gen.generate_variance_analysis(results),
            self.stats_gen.generate_temporal_stability(results),
            self.quality_gen.generate(results),
            self.recommendations_gen.generate(results),
        ]
        
        # Assemble and write report
        report_content = '\n\n'.join(report_sections)
        report_path.write_text(report_content, encoding='utf-8')
        
        if self.logger:
            self.logger.info(f"📊 Feature report saved: {report_path}")
        
        return str(report_path)


__all__ = ['FeatureReportGenerator']
