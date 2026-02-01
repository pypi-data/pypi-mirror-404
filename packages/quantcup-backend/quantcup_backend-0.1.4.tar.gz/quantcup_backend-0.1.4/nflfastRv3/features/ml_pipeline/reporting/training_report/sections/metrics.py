"""
Training Report Metrics Section Generator

Generates performance metrics, confusion matrix analysis, test games table, and prediction confidence sections.

**Refactoring Note**: Extracted from TrainingReportGenerator (lines 655-832)
to improve modularity and testability. Handles metrics display and test results.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List


class MetricsSectionGenerator:
    """
    Generates training report metrics sections.
    
    **Responsibilities**:
    - Performance metrics display
    - Test games detailed table
    - Confusion matrix analysis (delegates to analyzer)
    - Prediction confidence analysis (delegates to analyzer)
    
    **Pattern**: Single Responsibility Principle
    """
    
    def __init__(self, analyzer=None, logger=None):
        """
        Initialize metrics section generator.
        
        Args:
            analyzer: MetricsAnalyzer instance for complex analysis
            logger: Optional logger instance
        """
        self.analyzer = analyzer
        self.logger = logger
    
    def generate_performance_metrics(
        self,
        metrics: Dict[str, Any],
        y_test: pd.Series,
        y_pred: np.ndarray
    ) -> str:
        """
        Generate detailed performance metrics section.
        
        Args:
            metrics: Performance metrics dictionary
            y_test: True labels
            y_pred: Predicted labels
            
        Returns:
            str: Formatted performance metrics section
        """
        accuracy = metrics.get('accuracy', 0)
        auc = metrics.get('auc', 0)
        actual_home_rate = metrics.get('actual_home_win_rate', 0)
        pred_home_rate = metrics.get('predicted_home_win_rate', 0)
        
        # Calculate additional metrics
        home_advantage_bias = pred_home_rate - actual_home_rate
        bias_interpretation = self._interpret_bias(home_advantage_bias)
        
        return f"""## Performance Metrics

### Overall Performance
- **Accuracy:** {accuracy:.1%}
- **AUC-ROC:** {auc:.3f}
- **Error Rate:** {(1-accuracy):.1%}

### Home Field Advantage Analysis
- **Actual Home Win Rate:** {actual_home_rate:.1%}
- **Predicted Home Win Rate:** {pred_home_rate:.1%}
- **Bias:** {home_advantage_bias:+.1%} {bias_interpretation}

### Classification Report
```
{metrics.get('classification_report', 'N/A')}
```"""
    
    def generate_test_games_table(
        self,
        test_metadata: pd.DataFrame,
        y_test: pd.Series,
        y_pred: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> str:
        """
        Generate detailed test games table showing individual predictions.
        
        Args:
            test_metadata: Test game metadata
            y_test: True labels
            y_pred: Predicted labels
            y_pred_proba: Prediction probabilities
            
        Returns:
            str: Formatted test games table section
        """
        if len(test_metadata) == 0:
            return """## Test Games Detailed Results

No test games available."""
        
        # Build game-by-game results with confidence for sorting
        game_data = []
        
        for idx in range(len(y_test)):
            # Extract metadata
            if 'home_team' in test_metadata.columns and 'away_team' in test_metadata.columns:
                home_team = test_metadata.iloc[idx].get('home_team', 'HOME')
                away_team = test_metadata.iloc[idx].get('away_team', 'AWAY')
            else:
                home_team = 'HOME'
                away_team = 'AWAY'
            
            # Get actual outcome (1 = home win, 0 = away win)
            actual_home_win = bool(y_test.iloc[idx])
            actual_winner = home_team if actual_home_win else away_team
            
            # Get prediction
            pred_home_win = bool(y_pred[idx])
            predicted_winner = home_team if pred_home_win else away_team
            
            # Get probabilities
            home_prob = y_pred_proba[idx][1] if len(y_pred_proba[idx]) > 1 else y_pred_proba[idx][0]
            confidence = max(home_prob, 1 - home_prob)
            
            # Check if correct
            is_correct = (pred_home_win == actual_home_win)
            result_icon = "✅" if is_correct else "❌"
            
            # Format matchup
            matchup = f"{away_team} @ {home_team}"
            
            # Confidence level
            conf_level = self._get_confidence_level(confidence)
            
            game_data.append({
                'confidence_raw': confidence,
                'row': [
                    matchup,
                    predicted_winner,
                    f"{home_prob:.1%}",
                    f"{(1-home_prob):.1%}",
                    f"{confidence:.1%}",
                    conf_level,
                    actual_winner,
                    result_icon
                ]
            })
        
        # Sort by confidence descending (highest confidence first)
        game_data.sort(key=lambda x: x['confidence_raw'], reverse=True)
        
        # Extract sorted rows
        table_rows = [game['row'] for game in game_data]
        
        # Use dynamic table formatting
        headers = ['Matchup', 'Predicted', 'Home Win %', 'Away Win %', 'Confidence', 'Level', 'Actual', 'Result']
        table_content = self._format_table(headers, table_rows)
        
        return f"""## Test Games Detailed Results

Individual predictions for each test game (sorted by confidence):

{table_content}"""
    
    def generate_confusion_matrix_section(
        self,
        y_test: pd.Series,
        y_pred: np.ndarray
    ) -> str:
        """
        Generate confusion matrix section (delegates to analyzer).
        
        Args:
            y_test: True labels
            y_pred: Predicted labels
            
        Returns:
            str: Formatted confusion matrix section
        """
        if self.analyzer is None:
            return ""
        
        return self.analyzer.analyze_confusion_matrix(y_test, y_pred)
    
    def generate_prediction_confidence_section(
        self,
        y_test: pd.Series,
        y_pred: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> str:
        """
        Generate prediction confidence section (delegates to analyzer).
        
        Args:
            y_test: True labels
            y_pred: Predicted labels
            y_pred_proba: Prediction probabilities
            
        Returns:
            str: Formatted prediction confidence section
        """
        if self.analyzer is None:
            return ""
        
        return self.analyzer.analyze_prediction_confidence(y_test, y_pred, y_pred_proba)
    
    # Helper methods
    
    def _interpret_bias(self, bias: float) -> str:
        """Interpret home advantage bias."""
        if bias > 0.02:
            return "(slight over-prediction of home wins)"
        elif bias < -0.02:
            return "(slight under-prediction of home wins)"
        else:
            return "(well-calibrated)"
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level indicator."""
        if confidence >= 0.8:
            return "🟢 High"
        elif confidence >= 0.6:
            return "🟡 Medium"
        else:
            return "🔴 Low"
    
    def _format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Format a markdown table with dynamic column widths, accounting for emojis."""
        if not rows:
            return ""
        
        # Calculate max width for each column (accounting for emoji display width)
        col_widths = [self._display_width(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], self._display_width(str(cell)))
        
        # Build header row
        header_row = "| " + " | ".join(self._pad_to_width(h, col_widths[i]) for i, h in enumerate(headers)) + " |"
        
        # Build separator row
        separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
        
        # Build data rows
        data_rows = []
        for row in rows:
            formatted_row = "| " + " | ".join(self._pad_to_width(str(cell), col_widths[i]) for i, cell in enumerate(row)) + " |"
            data_rows.append(formatted_row)
        
        return header_row + "\n" + separator + "\n" + "\n".join(data_rows)
    
    def _display_width(self, text: str) -> int:
        """Calculate display width accounting for emojis taking up ~2 character widths."""
        # Common emoji patterns (circle emojis used in tables)
        emoji_pattern = re.compile(r'[\U0001F534-\U0001F7FF]|[\u2705\u274C]|[\U0001F7E0-\U0001F7E2]')
        
        # Count emojis
        emoji_count = len(emoji_pattern.findall(text))
        
        # Regular character count
        char_count = len(text)
        
        # Each emoji takes ~2 display widths but counts as 1-2 chars
        # So add 1 extra width per emoji
        return char_count + emoji_count
    
    def _pad_to_width(self, text: str, target_width: int) -> str:
        """Pad text to target display width, accounting for emoji widths."""
        current_width = self._display_width(text)
        padding_needed = target_width - current_width
        
        if padding_needed > 0:
            return text + (' ' * padding_needed)
        return text


__all__ = ['MetricsSectionGenerator']
