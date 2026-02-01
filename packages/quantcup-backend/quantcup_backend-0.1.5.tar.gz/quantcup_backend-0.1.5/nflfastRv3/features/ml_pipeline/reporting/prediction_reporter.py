"""
Prediction Report Generator

Generic report orchestrator for prediction results that delegates complex analysis to specialized components.
Following the same pattern as feature_orchestrator.py and model_trainer.py.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Orchestrator → Analyzers/Interpreters)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from .analyzers import create_metrics_analyzer


class PredictionReportGenerator:
    """
    Generate comprehensive markdown reports for prediction results.

    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + orchestration)
    Depth: 1 layer (delegates to analyzers/interpreters)

    Matches pattern from:
    - TrainingReportGenerator (same module)
    """

    def __init__(self, logger=None):
        """
        Initialize with optional logger.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger

        # Delegate complex analysis to specialized components
        self.analyzer = create_metrics_analyzer()

    def generate_report(
        self,
        predictions: List[Dict[str, Any]],
        season: int,
        week: int,
        model_name: str = 'game_outcome',
        model_version: str = 'latest',
        output_dir: str = 'reports/predictions'
    ) -> str:
        """
        Generate comprehensive markdown prediction report.
        
        Note:
            TODO: If generating multiple artifact types (e.g., predictions CSV, confidence plots),
            consider using timestamped subfolders: 'reports/predictions/pred_{season}_{week}_{timestamp}'
            to group related artifacts. See scripts/analyze_pbp_odds_data_v4.py for reference.

        Orchestrates report generation by delegating to specialized components.

        Args:
            predictions: List of prediction dictionaries from predictor
            season: NFL season
            week: NFL week
            model_name: Name of the model used
            model_version: Version of the model used
            output_dir: Directory to save report

        Returns:
            str: Path to generated report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'prediction_report_{season}_{week}_{timestamp}.md'
        report_path = Path(output_dir) / report_filename

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Build report sections (orchestrate)
        report_sections = []

        # Simple formatting (keep in orchestrator)
        report_sections.append(self._generate_header(season, week, model_name, model_version))
        report_sections.append(self._generate_executive_summary(predictions))
        report_sections.append(self._generate_confidence_interpretation())
        report_sections.append(self._generate_model_info(model_name, model_version))
        report_sections.append(self._generate_predictions_table(predictions))
        
        # Simple sections (keep in orchestrator)
        report_sections.append(self._generate_confidence_analysis(predictions))
        report_sections.append(self._generate_artifacts_section(report_path))

        # Write report
        report_content = '\n\n'.join(report_sections)
        report_path.write_text(report_content, encoding='utf-8')

        if self.logger:
            self.logger.info(f"📊 Prediction report saved: {report_path}")

        return str(report_path)

    def _generate_header(self, season: int, week: int, model_name: str, model_version: str) -> str:
        """Generate report header (simple formatting - keep in orchestrator)."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f"""# NFL Game Outcome Predictions Report

**Generated:** {timestamp}

**Season:** {season} | **Week:** {week}
**Model:** {model_name} (version: {model_version})

---"""

    def _generate_executive_summary(self, predictions: List[Dict[str, Any]]) -> str:
        """Generate executive summary (simple formatting - keep in orchestrator)."""
        if not predictions:
            return """## Executive Summary

**No predictions generated** - Check model availability and data pipeline."""

        num_games = len(predictions)

        # Calculate confidence statistics
        confidences = [p.get('confidence', 0) for p in predictions]
        avg_confidence = np.mean(confidences) if confidences else 0
        high_conf = sum(1 for c in confidences if c >= 0.8)
        med_conf = sum(1 for c in confidences if 0.6 <= c < 0.8)
        low_conf = sum(1 for c in confidences if c < 0.6)

        # Home win bias analysis
        home_win_probs = [p.get('home_win_prob', 0.5) for p in predictions]
        avg_home_prob = np.mean(home_win_probs) if home_win_probs else 0.5
        home_bias = (avg_home_prob - 0.5) * 100

        return f"""## Executive Summary

**Predictions Generated:** {num_games} games

### Confidence Distribution
- **High Confidence (≥80%):** {high_conf} games ({high_conf/num_games:.1%})
- **Medium Confidence (60-80%):** {med_conf} games ({med_conf/num_games:.1%})
- **Low Confidence (<60%):** {low_conf} games ({low_conf/num_games:.1%})
- **Average Confidence:** {avg_confidence:.1%}

### Home Field Advantage
- **Average Home Win Probability:** {avg_home_prob:.1%}
- **Home Field Bias:** {home_bias:+.1f}% ({'slight over-prediction' if home_bias > 2 else 'slight under-prediction' if home_bias < -2 else 'well-calibrated'})

**Key Insight:** The model predicts outcomes for {num_games} games with an average confidence of {avg_confidence:.1%}. See confidence interpretation below for context."""

    def _generate_confidence_interpretation(self) -> str:
        """Explain what confidence levels mean in NFL context."""
        return """## Understanding Confidence in NFL Predictions

**What Confidence Means:**
- **80%+ confidence** → Model expects ~80%+ accuracy on similar matchups (elite conviction)
- **70-79% confidence** → Model expects ~70-79% accuracy (strong conviction)
- **60-69% confidence** → Model expects ~60-69% accuracy (moderate conviction)
- **<60% confidence** → Model sees matchup as close to 50/50 (low conviction)

**Betting Strategy by Confidence Level:**

| Confidence | Expected Accuracy | Betting Recommendation | Estimated ROI* |
|------------|------------------|------------------------|----------------|
| 80%+ | 80%+ | High conviction plays | 30%+ |
| 70-79% | 70-79% | Strong value bets | 15-30% |
| 60-69% | 60-69% | Standard plays | 5-15% |
| 50-59% | 50-59% | Small plays or avoid | 0-5% |

*Estimated ROI at standard -110 odds

**NFL Context:**
- **High-confidence games (80%+)** are rare in NFL due to competitive parity
- **Medium-confidence games (60-79%)** represent the bulk of profitable predictions
- **Low-confidence games (<60%)** are essentially coin flips - model sees no clear edge

**Key Strategy Insight:** Focus your betting volume on higher confidence predictions. If the average confidence is 66%, the model expects to achieve ~66% accuracy this week, which would be STRONG professional performance (see industry benchmarks in training reports)."""

    def _generate_model_info(self, model_name: str, model_version: str) -> str:
        """Generate model information section (simple formatting - keep in orchestrator)."""
        return f"""## Model Information

**Model Name:** {model_name}
**Version:** {model_version}

**Algorithm:** XGBoost Ensemble Classifier
**Features:** Rolling team metrics, EPA differentials, contextual factors
**Training Data:** Historical NFL games (2000-present)

**Usage Notes:**
- Predictions are probabilistic estimates, not guarantees
- Higher confidence scores indicate stronger predictions
- Consider additional factors (injuries, weather, motivation) for betting decisions"""

    def _generate_predictions_table(self, predictions: List[Dict[str, Any]]) -> str:
        """Generate detailed predictions table (simple formatting - keep in orchestrator)."""
        if not predictions:
            return """## Predictions

No predictions available."""

        # Sort by confidence descending
        sorted_predictions = sorted(predictions, key=lambda x: x.get('confidence', 0), reverse=True)

        table_rows = []
        for pred in sorted_predictions:
            home_team = pred.get('home_team', 'HOME')
            away_team = pred.get('away_team', 'AWAY')
            home_prob = pred.get('home_win_prob', 0.5)
            confidence = pred.get('confidence', 0)
            predicted_winner = pred.get('predicted_winner', home_team if home_prob >= 0.5 else away_team)

            # Format matchup with fixed width for alignment
            matchup = f"{away_team:>3} @ {home_team:<3}".ljust(11)

            # Format probabilities with consistent width
            home_pct = f"{home_prob:6.1%}".rjust(10)
            away_pct = f"{(1-home_prob):6.1%}".rjust(10)
            conf_pct = f"{confidence:6.1%}".rjust(10)

            # Confidence level - use text only for better alignment
            if confidence >= 0.8:
                conf_level = "HIGH  "
            elif confidence >= 0.6:
                conf_level = "MEDIUM"
            else:
                conf_level = "LOW   "

            table_rows.append(f"| {matchup} | {predicted_winner:>6} | {home_pct} | {away_pct} | {conf_pct} | {conf_level} |")

        table_header = """## Detailed Predictions

| Matchup     | Winner | Home Win % | Away Win % | Confidence | Level  |
|-------------|--------|------------|------------|------------|--------|"""

        return table_header + '\n' + '\n'.join(table_rows)

    def _generate_confidence_analysis(self, predictions: List[Dict[str, Any]]) -> str:
        """Generate confidence analysis section (simple formatting - keep in orchestrator)."""
        if not predictions:
            return """## Confidence Analysis

No predictions available for analysis."""

        confidences = [p.get('confidence', 0) for p in predictions]

        # Confidence distribution
        high_conf_games = [p for p in predictions if p.get('confidence', 0) >= 0.8]
        med_conf_games = [p for p in predictions if 0.6 <= p.get('confidence', 0) < 0.8]
        low_conf_games = [p for p in predictions if p.get('confidence', 0) < 0.6]

        sections = ["## Confidence Analysis"]

        # Overall statistics
        sections.append(f"""
### Overall Statistics
- **Total Predictions:** {len(predictions)}
- **Average Confidence:** {np.mean(confidences):.1%}
- **Median Confidence:** {np.median(confidences):.1%}
- **Highest Confidence:** {max(confidences):.1%}
- **Lowest Confidence:** {min(confidences):.1%}""")

        # Confidence breakdown
        sections.append(f"""
### Confidence Breakdown
- **High Confidence (≥80%):** {len(high_conf_games)} games
- **Medium Confidence (60-80%):** {len(med_conf_games)} games
- **Low Confidence (<60%):** {len(low_conf_games)} games""")

        # Top 5 most confident predictions
        if len(predictions) >= 5:
            sections.append("""
### Top 5 Most Confident Predictions""")

            top_5 = sorted(predictions, key=lambda x: x.get('confidence', 0), reverse=True)[:5]
            for i, pred in enumerate(top_5, 1):
                home_team = pred.get('home_team', 'HOME')
                away_team = pred.get('away_team', 'AWAY')
                winner = pred.get('predicted_winner', home_team)
                conf = pred.get('confidence', 0)
                matchup = f"{away_team} @ {home_team}"
                sections.append(f"{i}. **{winner}** ({matchup}) - {conf:.1%} confidence")

        return '\n'.join(sections)

    def _generate_artifacts_section(self, report_path: Path) -> str:
        """Generate artifacts section (simple formatting - keep in orchestrator)."""
        return f"""## Report Artifacts

**Report Location:** `{report_path}`

**Data Sources:**
- Model predictions stored in object storage
- Historical training data from warehouse
- Real-time schedule data from NFL sources

**Next Steps:**
1. Review predictions manually for additional context
2. Monitor actual game outcomes for model validation
3. Consider model retraining with new data as season progresses"""


def create_prediction_report_generator(logger=None):
    """
    Factory function to create prediction report generator.

    Matches pattern from:
    - create_report_generator()

    Args:
        logger: Optional logger instance

    Returns:
        PredictionReportGenerator: Configured report generator
    """
    return PredictionReportGenerator(logger=logger)


__all__ = ['PredictionReportGenerator', 'create_prediction_report_generator']