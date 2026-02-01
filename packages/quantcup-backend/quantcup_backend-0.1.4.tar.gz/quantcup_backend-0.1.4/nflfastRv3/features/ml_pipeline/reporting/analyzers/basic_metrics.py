"""
Basic metrics analysis for ML model performance.

Extracted from analyzers.py - handles confusion matrix and
prediction confidence analysis.
"""

import numpy as np
from sklearn.metrics import confusion_matrix


class BasicMetricsAnalyzer:
    """
    Handles basic metrics analysis (confusion matrix, prediction confidence).
    
    This class provides fundamental performance metrics for binary classification
    models used in NFL game outcome prediction.
    """
    
    def analyze_confusion_matrix(self, y_test, y_pred):
        """
        Generate confusion matrix analysis.
        
        Args:
            y_test: True labels
            y_pred: Predicted labels
            
        Returns:
            str: Formatted markdown confusion matrix analysis
        """
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        total = len(y_test)
        
        return f"""## Confusion Matrix Analysis

```
                Predicted
              Away Win  Home Win
Actual  Away    {tn:3d}      {fp:3d}
        Home    {fn:3d}      {tp:3d}
```

### Breakdown
- **True Negatives (Correct Away Wins):** {tn} games ({tn/total:.1%})
- **True Positives (Correct Home Wins):** {tp} games ({tp/total:.1%})
- **False Positives (Predicted Home, Actually Away):** {fp} games ({fp/total:.1%})
- **False Negatives (Predicted Away, Actually Home):** {fn} games ({fn/total:.1%})

### Error Analysis
**Total Errors:** {fp + fn} games ({(fp + fn)/total:.1%})

**Type I Errors (False Positives):** {fp} games  
*Predicted home team would win, but away team won*  
→ Model may have overestimated home field advantage or underestimated away team strength

**Type II Errors (False Negatives):** {fn} games  
*Predicted away team would win, but home team won*  
→ Model may have underestimated home team advantages or situational factors"""
    
    def analyze_prediction_confidence(self, y_test, y_pred, y_pred_proba):
        """
        Analyze prediction confidence distribution.
        
        Args:
            y_test: True labels
            y_pred: Predicted labels
            y_pred_proba: Prediction probabilities
            
        Returns:
            str: Formatted markdown confidence analysis
        """
        if y_pred_proba is None:
            return ""
        
        # Calculate prediction confidence
        confidence = np.max(y_pred_proba.reshape(-1, 2), axis=1)
        
        # Categorize by confidence
        high_conf = confidence >= 0.80
        med_conf = (confidence >= 0.60) & (confidence < 0.80)
        low_conf = confidence < 0.60
        
        # Accuracy by confidence level
        high_conf_acc = (y_test[high_conf] == y_pred[high_conf]).mean() if high_conf.any() else 0
        med_conf_acc = (y_test[med_conf] == y_pred[med_conf]).mean() if med_conf.any() else 0
        low_conf_acc = (y_test[low_conf] == y_pred[low_conf]).mean() if low_conf.any() else 0
        
        return f"""## Prediction Confidence Analysis

### Confidence Distribution
- **High Confidence (≥80%):** {high_conf.sum()} games ({high_conf.sum()/len(y_test):.1%})
  - Accuracy: {high_conf_acc:.1%}
- **Medium Confidence (60-80%):** {med_conf.sum()} games ({med_conf.sum()/len(y_test):.1%})
  - Accuracy: {med_conf_acc:.1%}
- **Low Confidence (<60%):** {low_conf.sum()} games ({low_conf.sum()/len(y_test):.1%})
  - Accuracy: {low_conf_acc:.1%}

### Interpretation
- **High confidence predictions** are highly reliable ({high_conf_acc:.1%} accuracy)
- **Low confidence predictions** indicate close matchups where either team could win
- Games with <60% confidence are inherently unpredictable (coin flips)"""


__all__ = ['BasicMetricsAnalyzer']
