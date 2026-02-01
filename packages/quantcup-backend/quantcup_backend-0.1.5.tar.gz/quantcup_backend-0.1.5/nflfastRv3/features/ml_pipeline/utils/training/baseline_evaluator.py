"""
Baseline Evaluator - Generic baseline comparison for regression and classification models.
"""

from typing import Dict, Any
import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error


class BaselineEvaluator:
    """Generic baseline comparison for regression and classification models."""
    
    @staticmethod
    def evaluate_classification_baselines(
        y_test: NDArray,
        y_pred: NDArray,
        y_pred_proba: NDArray,
        positive_class_rate: float = 0.565  # NFL home win rate
    ) -> Dict[str, Any]:
        """
        Calculate baseline comparisons for binary classification.
        
        Args:
            y_test: Actual outcomes
            y_pred: Model predictions
            y_pred_proba: Prediction probabilities
            positive_class_rate: Historical rate of positive class (e.g., 56.5% home wins)
            
        Returns:
            dict: Baseline metrics and comparisons
        """
        model_accuracy = accuracy_score(y_test, y_pred)
        
        # Baseline 1: Always predict positive class
        baseline_always_positive = np.ones_like(y_test)
        baseline_always_accuracy = accuracy_score(y_test, baseline_always_positive)
        
        # Baseline 2: Random guessing (50/50)
        np.random.seed(42)
        baseline_random = np.random.randint(0, 2, size=len(y_test))
        baseline_random_accuracy = accuracy_score(y_test, baseline_random)
        
        # Baseline 3: Historical rate
        baseline_historical = np.random.choice(
            [0, 1], size=len(y_test), 
            p=[1 - positive_class_rate, positive_class_rate]
        )
        baseline_historical_accuracy = accuracy_score(y_test, baseline_historical)
        
        return {
            'model_accuracy': model_accuracy,
            'baseline_always_positive_accuracy': baseline_always_accuracy,
            'baseline_random_accuracy': baseline_random_accuracy,
            'baseline_historical_accuracy': baseline_historical_accuracy,
            'improvement_over_always_positive': model_accuracy - baseline_always_accuracy,
            'improvement_over_random': model_accuracy - baseline_random_accuracy,
            'improvement_over_historical': model_accuracy - baseline_historical_accuracy,
            'beats_always_positive': model_accuracy > baseline_always_accuracy,
            'beats_random': model_accuracy > baseline_random_accuracy,
            'beats_historical': model_accuracy > baseline_historical_accuracy
        }
    
    @staticmethod
    def evaluate_regression_baselines(
        y_test: NDArray,
        y_pred: NDArray,
        historical_mean: float
    ) -> Dict[str, Any]:
        """
        Calculate baseline comparisons for regression models.
        
        Args:
            y_test: Actual values
            y_pred: Model predictions
            historical_mean: Historical average (e.g., 250 yards for QB)
            
        Returns:
            dict: Baseline metrics and comparisons
        """
        model_mae = mean_absolute_error(y_test, y_pred)
        model_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # Baseline 1: Always predict mean
        baseline_mean_pred = np.full_like(y_test, historical_mean, dtype=float)
        baseline_mean_mae = mean_absolute_error(y_test, baseline_mean_pred)
        
        # Baseline 2: Always predict test set mean
        baseline_test_mean_pred = np.full_like(y_test, y_test.mean(), dtype=float)
        baseline_test_mean_mae = mean_absolute_error(y_test, baseline_test_mean_pred)
        
        return {
            'model_mae': model_mae,
            'model_rmse': model_rmse,
            'baseline_historical_mean_mae': baseline_mean_mae,
            'baseline_test_mean_mae': baseline_test_mean_mae,
            'improvement_over_historical_mean': baseline_mean_mae - model_mae,
            'improvement_over_test_mean': baseline_test_mean_mae - model_mae,
            'beats_historical_mean': model_mae < baseline_mean_mae,
            'beats_test_mean': model_mae < baseline_test_mean_mae
        }