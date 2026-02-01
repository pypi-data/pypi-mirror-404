"""
Training Report Summary Section Generator

Generates header, executive summary, model configuration, and NFL benchmarking context sections.

**Refactoring Note**: Extracted from TrainingReportGenerator (lines 496-653)
to improve modularity and testability. Handles simple formatting sections
that don't require complex analysis.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List


class SummarySectionGenerator:
    """
    Generates training report summary sections.
    
    **Responsibilities**:
    - Report header with metadata
    - Executive summary with performance rating
    - NFL benchmarking context
    - Model configuration details
    
    **Pattern**: Single Responsibility Principle
    """
    
    def __init__(self, logger=None):
        """
        Initialize summary section generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def generate_header(
        self,
        train_seasons: List[int],
        test_seasons: List[int],
        test_week: Optional[int] = None
    ) -> str:
        """
        Generate report header section.
        
        Args:
            train_seasons: Training season years
            test_seasons: Test season years
            test_week: Optional specific test week
            
        Returns:
            str: Formatted header section
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        test_desc = f"Week {test_week}" if test_week else "Full Season"
        
        return f"""# NFL Game Outcome Model - Training Report

**Generated:** {timestamp}

**Training Seasons:** {', '.join(map(str, train_seasons))}  
**Test Seasons:** {', '.join(map(str, test_seasons))} ({test_desc})

---"""
    
    def generate_executive_summary(
        self,
        metrics: Dict[str, Any],
        train_size: int,
        test_size: int
    ) -> str:
        """
        Generate executive summary with performance rating.
        
        Args:
            metrics: Performance metrics dictionary
            train_size: Number of training samples
            test_size: Number of test samples
            
        Returns:
            str: Formatted executive summary section
        """
        accuracy = metrics.get('accuracy', 0)
        auc = metrics.get('auc', 0)
        
        # NFL-specific performance rating
        rating, perf_level = self._get_performance_rating(accuracy)
        
        return f"""## Executive Summary

**Model Performance:** {rating} - {perf_level}

- **Accuracy:** {accuracy:.1%} ({int(accuracy * test_size)}/{test_size} games predicted correctly)
- **AUC-ROC:** {auc:.3f} (discrimination ability)
- **Training Set:** {train_size:,} games
- **Test Set:** {test_size:,} games

**Key Takeaway:** The model achieved {accuracy:.1%} accuracy on {test_size} unseen games. See NFL benchmarking context below for performance interpretation."""
    
    def generate_nfl_benchmarking_context(self) -> str:
        """
        Generate NFL-specific benchmarking context section.
        
        Returns:
            str: Formatted benchmarking context section
        """
        # Prepare benchmarking table data
        headers = ['Accuracy', 'Status', 'Estimated ROI*', 'Performance Level']
        rows = [
            ['68%+', '🟢 Elite', '30%+', 'Top 1% of professional handicappers'],
            ['63-67%', '🟢 Exceptional', '15-29%', 'Elite professional performance'],
            ['60-62%', '🟡 Strong', '9-14%', 'Consistently profitable professional'],
            ['58-59%', '🟡 Good', '5-8%', 'Professional handicapper'],
            ['55-57%', '🟠 Fair', '2-4%', 'Beating the market'],
            ['52.4-54%', '🟠 Marginal', '0-1%', 'Near break-even'],
            ['<52.4%', '🔴 Unprofitable', 'Negative', 'Losing money after vig']
        ]
        
        benchmark_table = self._format_table(headers, rows)
        
        return f"""## 📊 NFL Prediction Benchmarking Context

**Why NFL Prediction Differs from Traditional ML:**

NFL game prediction is fundamentally different from typical machine learning classification tasks:
- Games are designed to be ~50/50 propositions by oddsmakers
- High inherent variance due to injuries, weather, officiating, and human factors
- Limited sample sizes (only 272 games per regular season)
- High competitive parity by design (draft system, salary cap, revenue sharing)
- Continuous roster turnover and coaching changes

**Industry Performance Benchmarks:**

{benchmark_table}

*Estimated ROI assuming standard -110 betting odds with flat bet sizing.

**Expected Variance:**
- Even elite handicappers experience ±3-5% accuracy variance year-to-year
- Standard deviation of 5-8% is NORMAL for sports betting, not a flaw
- NFL parity increases naturally (injuries, rule changes, coaching turnover)

**Key Takeaway:** In NFL prediction, 60% accuracy is STRONG performance, 65% is EXCEPTIONAL, and 70%+ sustained across full seasons is nearly impossible. Don't compare to 90%+ accuracies seen in other ML domains - NFL games are specifically designed to be coin flips."""
    
    def generate_model_config(
        self,
        model,
        num_features: int
    ) -> str:
        """
        Generate model configuration section.
        
        Args:
            model: Trained model instance
            num_features: Number of features used
            
        Returns:
            str: Formatted model configuration section
        """
        params = model.get_params()
        
        # Detect model type
        model_type = type(model).__name__
        model_module = type(model).__module__
        
        # Build algorithm description
        algorithm = self._get_algorithm_name(model_type, model_module)
        
        # Build hyperparameters section
        hyperparams_str = self._format_hyperparameters(params)
        
        return f"""## Model Configuration

**Algorithm:** {algorithm}

**Hyperparameters:**
{hyperparams_str}

**Features:** {num_features} differential features (home team - away team)"""
    
    # Helper methods
    
    def _get_performance_rating(self, accuracy: float) -> tuple[str, str]:
        """Get performance rating and level for given accuracy."""
        if accuracy >= 0.68:
            return "🟢 Elite", "Top 1% professional"
        elif accuracy >= 0.63:
            return "🟢 Exceptional", "Elite professional"
        elif accuracy >= 0.60:
            return "🟡 Strong", "Consistently profitable"
        elif accuracy >= 0.58:
            return "🟡 Good", "Professional"
        elif accuracy >= 0.55:
            return "🟠 Fair", "Above break-even"
        elif accuracy >= 0.524:
            return "🟠 Marginal", "Near break-even"
        else:
            return "🔴 Below Break-Even", "Needs improvement"
    
    def _get_algorithm_name(self, model_type: str, model_module: str) -> str:
        """Determine algorithm name from model type and module."""
        if 'xgboost' in model_module.lower():
            return "XGBoost Classifier (Gradient Boosting)"
        elif 'sklearn.ensemble' in model_module:
            if 'RandomForest' in model_type:
                return "Random Forest Classifier"
            elif 'GradientBoosting' in model_type:
                return "Gradient Boosting Classifier"
            else:
                return model_type
        elif 'lightgbm' in model_module.lower():
            return "LightGBM Classifier"
        elif 'catboost' in model_module.lower():
            return "CatBoost Classifier"
        else:
            return model_type
    
    def _format_hyperparameters(self, params: dict) -> str:
        """Format model hyperparameters for display."""
        hyperparams = []
        common_params = [
            'n_estimators', 'max_depth', 'learning_rate', 'subsample',
            'colsample_bytree', 'min_samples_split', 'min_samples_leaf',
            'max_features', 'random_state'
        ]
        
        for param in common_params:
            if param in params and params[param] is not None:
                param_name = param.replace('_', ' ').title()
                hyperparams.append(f"- {param_name}: {params[param]}")
        
        return '\n'.join(hyperparams) if hyperparams else "- Default parameters used"
    
    def _format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Format a markdown table with dynamic column widths."""
        if not rows:
            return ""
        
        # Calculate max width for each column
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Build header row
        header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
        
        # Build separator row
        separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
        
        # Build data rows
        data_rows = []
        for row in rows:
            formatted_row = "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
            data_rows.append(formatted_row)
        
        return header_row + "\n" + separator + "\n" + "\n".join(data_rows)


__all__ = ['SummarySectionGenerator']
