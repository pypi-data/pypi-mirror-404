"""
Stability Metrics Calculator for Backtest Reports

Calculates feature importance stability metrics across test years.
"""

import pandas as pd
import numpy  as np
from collections import defaultdict
from typing import Dict, Any, List, Optional

from ..common import get_feature_stability_rating


class StabilityCalculator:
    """
    Calculates feature importance stability metrics.
    
    Responsibilities:
    - Extract feature importances from multiple test years
    - Calculate stability metrics (mean, std, CV)
    - Classify features by stability
    """
    
    def __init__(self, logger=None):
        """
        Initialize stability calculator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
    
    def calculate_feature_stability(
        self,
        backtest_results: List[Dict[str, Any]]
    ) -> Optional[pd.DataFrame]:
        """
        Calculate feature importance stability across test years.
        
        Args:
            backtest_results: List of training results from each test year
            
        Returns:
            DataFrame with stability metrics or None if no data available
        """
        # DIAGNOSTIC: Log input validation
        if self.logger:
            self.logger.debug(
                f"[DIAG] calculate_feature_stability called with "
                f"{len(backtest_results) if backtest_results else 0} results"
            )
        
        if not backtest_results or 'model' not in backtest_results[0]:
            if self.logger:
                self.logger.warning(
                    f"[DIAG] Early return: backtest_results empty={not backtest_results}, "
                    f"has_model={'model' in backtest_results[0] if backtest_results else 'N/A'}"
                )
            return None
        
        # Extract feature importances from each year
        feature_data = defaultdict(list)
        
        for idx, result in enumerate(backtest_results):
            model = result.get('model')
            
            # DIAGNOSTIC: Log model validation
            if self.logger:
                self.logger.debug(
                    f"[DIAG] Year {idx}: model exists={model is not None}, "
                    f"has_feature_importances={hasattr(model, 'feature_importances_') if model else False}"
                )
            
            if not model or not hasattr(model, 'feature_importances_'):
                if self.logger:
                    self.logger.warning(
                        f"[DIAG] Year {idx}: Skipping - model={type(model).__name__ if model else 'None'}"
                    )
                continue
            
            # Handle ensemble model (get XGBoost importances)
            if hasattr(model, 'xgboost_model') and hasattr(model, 'tree_features_'):
                feature_names = model.tree_features_
                importances = model.xgboost_model.feature_importances_
                if self.logger:
                    self.logger.debug(
                        f"[DIAG] Year {idx}: Using ensemble XGBoost - {len(feature_names)} features"
                    )
            else:
                # Standard model
                feature_names = result.get('X_test', pd.DataFrame()).columns
                importances = model.feature_importances_
                if self.logger:
                    self.logger.debug(
                        f"[DIAG] Year {idx}: Using standard model - {len(feature_names)} features"
                    )
            
            # DIAGNOSTIC: Validate feature count match
            if len(feature_names) != len(importances):
                if self.logger:
                    self.logger.error(
                        f"[DIAG] Year {idx}: MISMATCH - {len(feature_names)} feature names "
                        f"vs {len(importances)} importances"
                    )
                continue
            
            for feat, imp in zip(feature_names, importances):
                feature_data[feat].append(imp)
        
        if not feature_data:
            if self.logger:
                self.logger.warning(
                    f"[DIAG] No feature data collected after processing {len(backtest_results)} results"
                )
            return None
        
        # Calculate stability metrics
        stability_stats = []
        for feat, importances in feature_data.items():
            mean_imp = float(np.mean(importances))
            std_imp = float(np.std(importances))
            
            # DIAGNOSTIC: Check for edge cases
            if mean_imp <= 0:
                if self.logger:
                    self.logger.warning(f"[DIAG] Feature '{feat}': mean_imp={mean_imp} (non-positive)")
            
            cv = std_imp / mean_imp if mean_imp > 0.001 else 0  # Avoid div by zero
            
            # Get stability classification from config
            stability, note = get_feature_stability_rating(cv)
            
            stability_stats.append({
                'feature': feat,
                'mean_imp': mean_imp,
                'std_imp': std_imp,
                'cv': cv,
                'stability': stability,
                'note': note
            })
        
        # Sort by mean importance
        stability_df = pd.DataFrame(stability_stats).sort_values('mean_imp', ascending=False)
        
        return stability_df


__all__ = ['StabilityCalculator']
