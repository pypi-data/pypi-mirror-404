"""Statistical analysis components for ML reports.

Refactored with facade pattern for better organization.
Pattern: Facade Pattern (3 complexity points)
- Public API: MetricsAnalyzer (facade)
- Internal: _BasicMetricsAnalyzer, _FeatureAnalyzer, _EnsembleAnalyzer
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from sklearn.metrics import confusion_matrix

# try:
#     import shap
#     SHAP_AVAILABLE = True
# except ImportError:
#     SHAP_AVAILABLE = False

# try:
#     import xgboost as xgb
#     XGB_AVAILABLE = True
# except ImportError:
#     XGB_AVAILABLE = False


# ============================================================================
# SHARED UTILITIES (Module-level functions)
# ============================================================================

def _format_markdown_table(headers, rows):
    """
    Format a markdown table with dynamic column widths based on actual content.
    
    Args:
        headers: List of header strings
        rows: List of lists, where each inner list represents a row
        
    Returns:
        str: Formatted markdown table with proper alignment
    """
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


def _categorize_feature(feature_name):
    """Categorize feature by name pattern."""
    feature_lower = feature_name.lower()
    
    if 'interaction_' in feature_lower or feature_name in ['epa_advantage_4game', 'epa_advantage_8game', 'win_rate_advantage', 'momentum_advantage']:
        return 'Composite/Interaction'
    elif 'rolling_' in feature_lower:
        return 'Rolling Differentials'
    elif 'trending' in feature_lower:
        return 'Trending'
    elif 'rest' in feature_lower:
        return 'Contextual - Rest'
    elif any(w in feature_lower for w in ['weather', 'temp', 'precipitation', 'wind']):
        return 'Contextual - Weather'
    elif 'season' in feature_lower or 'games_remaining' in feature_lower:
        return 'Contextual - Season'
    elif any(w in feature_lower for w in ['stadium', 'dome', 'altitude', 'site']):
        return 'Contextual - Stadium'
    elif 'division' in feature_lower or 'conference' in feature_lower:
        return 'Contextual - Division'
    elif 'injury' in feature_lower or 'qb_available' in feature_lower or 'starter_injuries' in feature_lower:
        return 'Injury Features'
    elif 'qb_' in feature_lower:
        return 'NextGen QB'
    elif any(w in feature_lower for w in ['epa', 'efficiency', 'red_zone', 'third_down']):
        return 'Efficiency Metrics'
    elif 'recent_' in feature_lower:
        return 'Recent Form'
    else:
        return 'Other'


def _get_registry_feature_reasons():
    """Extract exclusion reasons from FeatureRegistry using enhanced metadata."""
    try:
        from ..utils.feature_registry import FeatureRegistry
        
        # Use new enhanced metadata methods
        reasons = {}
        disabled_features = FeatureRegistry.get_disabled_features()
        
        for feature_name, metadata in disabled_features.items():
            if isinstance(metadata, dict):
                # Enhanced format - extract reason and additional context
                reason = metadata.get('disabled_reason', 'No reason documented')
                
                # Add correlation info if available
                if metadata.get('tested_correlation') is not None:
                    reason += f" (correlation: {metadata['tested_correlation']:+.3f})"
                
                # Add test date if available
                if metadata.get('disabled_date'):
                    reason += f" [Tested: {metadata['disabled_date']}]"
                
                reasons[feature_name] = reason
            else:
                # Legacy format or simple boolean
                reasons[feature_name] = 'No reason documented'
        
        return reasons
    except Exception:
        return {}


# ============================================================================
# INTERNAL ANALYZER CLASSES (Private - not exported)
# ============================================================================

class _BasicMetricsAnalyzer:
    """
    Handles basic metrics analysis (confusion matrix, prediction confidence).
    
    Internal class - not part of public API.
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


class _FeatureAnalyzer:
    """
    Handles feature importance and selection auditing.
    
    Internal class - not part of public API.
    """
    
    def analyze_feature_importance(self, model, feature_names, X_train=None, y_train=None):
        """
        Generate feature importance analysis.

        Args:
            model: Trained model with feature_importances_ attribute or ensemble with xgboost_model
            feature_names: List or Index of feature names
            X_train: Training features (required for XGBoost diagnostics)
            y_train: Training labels (required for XGBoost diagnostics)

        Returns:
            str: Formatted markdown feature importance analysis
        """
        # Check for ensemble model with XGBoost
        if hasattr(model, 'xgboost_model'):
            if X_train is None or y_train is None:
                return "## Feature Importance\n\n*XGBoost diagnostics require training data (X_train, y_train).*"
            return self._analyze_xgboost_importance(model.xgboost_model, feature_names, X_train, y_train)

        # Fallback to standard sklearn feature importance
        if not hasattr(model, 'feature_importances_'):
            return "## Feature Importance\n\n*Feature importance not available for this model.*"
        
        # Validate lengths match
        if len(feature_names) != len(model.feature_importances_):
            return f"## Feature Importance\n\n*Feature importance mismatch: {len(feature_names)} names vs {len(model.feature_importances_)} values.*"

        # Get feature importance
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Top 30 features (expanded from 15 for better visibility)
        top_features = importance_df.head(30).copy()
        
        # Calculate cumulative importance
        total_importance = importance_df['importance'].sum()
        top_features['cumulative'] = top_features['importance'].cumsum() / total_importance
        
        # Prepare table data with formatted values
        headers = ['Feature', 'Importance', '% of Total', 'Cumulative', 'Category']
        rows = []
        for idx, row in top_features.iterrows():
            category = _categorize_feature(row['feature'])
            rows.append([
                row['feature'],
                f"{row['importance']:.4f}",
                f"{row['importance']/total_importance:.1%}",
                f"{row['cumulative']:.1%}",
                category
            ])
        
        # Generate table with dynamic widths
        table_content = _format_markdown_table(headers, rows)
        
        # Category summary
        category_importance = importance_df.groupby(
            importance_df['feature'].apply(_categorize_feature)
        )['importance'].sum().sort_values(ascending=False)
        
        category_section = "\n### Feature Importance by Category\n\n"
        for category, imp in category_importance.items():
            pct = imp / total_importance
            category_section += f"- **{category}:** {pct:.1%} ({imp:.4f})\n"
        
        return f"""## Feature Importance

### Top 30 Most Important Features

{table_content}

**Key Insight:** Top 5 features account for {importance_df.head(5)['importance'].sum()/total_importance:.1%} of total model importance.
{category_section}"""
    
    def analyze_feature_selection_audit(self, X_train, X_test, y_train=None, model_class=None):
        """
        Generate comprehensive feature selection audit.
        
        Shows:
        - Complete list of features used
        - Features available but excluded
        - Exclusion reasons from FeatureRegistry
        - Feature statistics and quality metrics
        
        Args:
            X_train: Training features DataFrame
            X_test: Test features DataFrame
            y_train: Training target (optional, for correlation calculation)
            model_class: Model class for accessing registry (optional)
            
        Returns:
            str: Formatted markdown feature audit
        """
        try:
            from ..utils.feature_registry import FeatureRegistry
        except ImportError:
            return "\n## Feature Selection Audit\n\n*FeatureRegistry not available - skipping audit*"
        
        # Get feature sets
        all_known = set(FeatureRegistry.get_all_features())
        active_in_registry = set(FeatureRegistry.get_active_features())
        actually_used = set(X_train.columns)
        
        # Calculate exclusions
        enabled_but_missing = active_in_registry - actually_used
        disabled_in_registry = all_known - active_in_registry
        
        # Feature statistics
        feature_stats = []
        for feat in actually_used:
            # Calculate target correlation if y_train provided
            target_corr = None
            if y_train is not None:
                try:
                    target_corr = abs(X_train[feat].corr(y_train))
                except:
                    target_corr = 0.0
            
            stats = {
                'feature': feat,
                'target_corr': target_corr if target_corr is not None else 0.0,
                'mean_train': X_train[feat].mean(),
                'std_train': X_train[feat].std(),
                'null_rate_train': X_train[feat].isnull().mean(),
                'mean_test': X_test[feat].mean(),
                'std_test': X_test[feat].std(),
                'null_rate_test': X_test[feat].isnull().mean(),
            }
            feature_stats.append(stats)
        
        # Sort by target correlation (descending - most important first)
        feature_stats.sort(key=lambda x: x['target_corr'], reverse=True)
        
        # Build report sections
        sections = ["\n## Feature Selection Audit"]
        
        # Summary statistics
        sections.append(f"""
### Summary Statistics
- **Total Features in Registry:** {len(all_known)}
- **Features Enabled in Registry:** {len(active_in_registry)}
- **Features Actually Used in Training:** {len(actually_used)}
- **Features Enabled but Missing:** {len(enabled_but_missing)}
- **Features Disabled in Registry:** {len(disabled_in_registry)}
""")
        
        # Features actually used (complete list with stats)
        sections.append("""
### Features Used in Training

Complete list of all features used to train this model:

""")
        
        # Prepare table data - Target Corr as second column
        headers = ['Feature', 'Target Corr', 'Mean (Train)', 'Std (Train)', 'Null %', 'Mean (Test)', 'Std (Test)', 'Null %', 'Category']
        table_rows = []
        for stat in feature_stats:
            category = _categorize_feature(stat['feature'])
            table_rows.append([
                stat['feature'],
                f"{stat['target_corr']:.4f}" if y_train is not None else 'N/A',
                f"{stat['mean_train']:.3f}",
                f"{stat['std_train']:.3f}",
                f"{stat['null_rate_train']:.1%}",
                f"{stat['mean_test']:.3f}",
                f"{stat['std_test']:.3f}",
                f"{stat['null_rate_test']:.1%}",
                category
            ])
        
        # Generate table with dynamic widths
        table_content = _format_markdown_table(headers, table_rows)
        sections.append(table_content)
        
        # Enabled but missing (data quality issue)
        if enabled_but_missing:
            sections.append(f"""
### ⚠️ Features Enabled but Not Available

These features are enabled in FeatureRegistry but were not found in the training data.
This indicates a data pipeline issue that should be investigated.

**Count:** {len(enabled_but_missing)}

**Features:**
{chr(10).join(f'- `{f}`' for f in sorted(enabled_but_missing))}
""")
        
        # Disabled features with reasons
        sections.append(f"""
### Features Disabled in Registry

These features are available but intentionally disabled. Reasons from FeatureRegistry:

**Count:** {len(disabled_in_registry)}
""")
        
        # Extract reasons from FeatureRegistry
        registry_reasons = _get_registry_feature_reasons()
        
        # Group by category using defaultdict for robustness
        # This auto-creates missing categories instead of crashing with KeyError
        categories = defaultdict(list)
        
        # Pre-populate known categories to maintain display order
        # (defaultdict will preserve insertion order in Python 3.7+)
        known_categories = [
            'Rolling Differentials',
            'Efficiency Metrics',  # Added - was missing
            'Recent Form',         # Added - was missing
            'Trending',
            'Contextual - Rest',
            'Contextual - Weather',
            'Contextual - Season',
            'Contextual - Stadium',
            'Contextual - Division',
            'Injury Features',
            'NextGen QB',
            'Composite/Interaction',
            'Other'
        ]
        for cat in known_categories:
            categories[cat] = []
        
        # Categorize disabled features
        # If _categorize_feature() returns a new category, defaultdict auto-creates it
        for feat in sorted(disabled_in_registry):
            reason = registry_reasons.get(feat, 'No reason documented')
            category = _categorize_feature(feat)
            categories[category].append(f"- `{feat}`: {reason}")
        
        for category, features in categories.items():
            if features:
                sections.append(f"""
#### {category}
{chr(10).join(features)}
""")
        
        return '\n'.join(sections)
    
    def analyze_gauntlet_audit(self, selector, original_features, X=None, y=None, X_selected=None, y_selected=None, model=None):
        """
        Generate complete feature pipeline audit from Registry → Final XGBoost Usage.
        
        Shows the entire journey:
        1. The Gauntlet (variance, collinearity, relevance) with WHY details
        2. Feature Splitting (linear vs tree groups)
        3. Poison Pill Detection (if any removed)
        4. XGBoost Final Usage (which features actually got used)
        
        Args:
            selector: FeatureSelector instance with dropped_features_ attribute
            original_features: List of original feature names before selection
            X: Optional DataFrame with original features (for correlation calculations in Stages 1-3)
            y: Optional Series with target variable (for correlation calculations in Stages 1-3)
            X_selected: Optional DataFrame with post-Gauntlet transformed features (for Step 6 correlation)
            y_selected: Optional Series with target variable (for Step 6 correlation)
            model: Optional trained model (for feature splitting and XGBoost usage info)
            
        Returns:
            str: Markdown formatted complete pipeline audit with WHY details
        """
        dropped_variance = selector.dropped_features_.get('variance', [])
        dropped_collinearity = selector.dropped_features_.get('collinearity', [])
        dropped_relevance = selector.dropped_features_.get('correlation', [])
        
        survived = selector.selected_features_ if selector.selected_features_ else []
        total_dropped = len(dropped_variance) + len(dropped_collinearity) + len(dropped_relevance)
        
        report = ["## Feature Selection Audit (The Gauntlet)\n"]
        report.append(f"**Original Features:** {len(original_features)}")
        report.append(f"**Final Features:** {len(survived)}")
        report.append(f"**Total Dropped:** {total_dropped}\n")
        
        # The Gauntlet stages
        report.append("### The Gauntlet - Stage Results\n")
        
        # Stage 1: Variance
        if dropped_variance:
            report.append(f"#### Stage 1: Variance Filter (Constant Features)")
            report.append(f"**Dropped {len(dropped_variance)} features** with zero variance\n")
            report.append("```")
            for feat in sorted(dropped_variance):
                report.append(f"- {feat}")
            report.append("```\n")
        else:
            report.append(f"#### Stage 1: Variance Filter")
            report.append(f"✅ No constant features detected\n")
        
        # Stage 2: Collinearity (with WHY details)
        if dropped_collinearity:
            report.append(f"#### Stage 2: Collinearity Filter (Correlation > 0.90)")
            report.append(f"**Dropped {len(dropped_collinearity)} redundant features**\n")
            report.append("Each feature was highly correlated with another feature that had stronger correlation with the target:\n")
            
            # Recalculate correlations if data provided
            if X is not None and y is not None:
                # Get all original features that participated in collinearity check
                all_features_before_collinearity = [f for f in original_features if f not in dropped_variance]
                X_before_collinearity = X[[f for f in all_features_before_collinearity if f in X.columns]]
                
                # Calculate correlation matrix
                numeric_cols = X_before_collinearity.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    corr_matrix = X_before_collinearity[numeric_cols].corr().abs()
                    target_corr = X_before_collinearity[numeric_cols].corrwith(y).abs()
                    
                    # Prepare table data
                    headers = ['Feature', 'Corr with Partner', 'Partner Feature', "Partner's Target Corr"]
                    rows = []
                    
                    for feat in sorted(dropped_collinearity):
                        if feat in corr_matrix.index:
                            # Find highest correlation partner
                            feat_corrs = corr_matrix.loc[feat]
                            feat_corrs = feat_corrs[feat_corrs.index != feat]  # Exclude self
                            if len(feat_corrs) > 0:
                                max_corr_idx = feat_corrs.idxmax()
                                max_corr_val = feat_corrs[max_corr_idx]
                                partner_target_corr = target_corr.get(max_corr_idx, 0.0)
                                rows.append([
                                    f"`{feat}`",
                                    f"{max_corr_val:.3f}",
                                    f"`{max_corr_idx}`",
                                    f"{partner_target_corr:.3f}"
                                ])
                    
                    report.append("\n" + _format_markdown_table(headers, rows))
                    report.append("")
            else:
                # Fallback if no data provided
                report.append("```")
                for feat in sorted(dropped_collinearity):
                    report.append(f"- {feat}")
                report.append("```\n")
        else:
            report.append(f"#### Stage 2: Collinearity Filter")
            report.append(f"✅ No highly correlated features detected\n")
        
        # Stage 3: Relevance (with WHY details)
        if dropped_relevance:
            report.append(f"#### Stage 3: Relevance Filter (Correlation < 0.005)")
            report.append(f"**Dropped {len(dropped_relevance)} irrelevant features**\n")
            report.append("Features with near-zero correlation to target variable:\n")
            
            # Recalculate correlations if data provided
            if X is not None and y is not None:
                numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    correlations = X[numeric_cols].corrwith(y).abs()
                    
                    # Prepare table data
                    headers = ['Feature', 'Correlation with Target']
                    rows = []
                    
                    for feat in sorted(dropped_relevance):
                        if feat in correlations:
                            corr_val = correlations[feat]
                            # Highlight known poison pills
                            toxic_watch = ['stadium_home_win_rate', 'stadium_scoring_rate', 'home_site_bias']
                            marker = " 🎯 POISON PILL" if any(t in feat for t in toxic_watch) else ""
                            rows.append([
                                f"`{feat}`{marker}",
                                f"{corr_val:.4f}"
                            ])
                    
                    report.append("\n" + _format_markdown_table(headers, rows))
                    report.append("")
            else:
                # Fallback if no data provided
                report.append("```")
                for feat in sorted(dropped_relevance):
                    report.append(f"- {feat}")
                report.append("```\n")
        else:
            report.append(f"#### Stage 3: Relevance Filter")
            report.append(f"✅ All features show meaningful correlation with target\n")
        
        # Survivors from The Gauntlet
        report.append(f"### ✅ Gauntlet Survivors ({len(survived)} features)\n")
        report.append("Features that passed all three Gauntlet filter stages:\n")
        
        # Step 4: Feature Splitting (if model provided)
        if model and hasattr(model, 'linear_features_') and hasattr(model, 'tree_features_'):
            linear_feats = model.linear_features_ or []
            tree_feats = model.tree_features_ or []
            
            report.append(f"\n#### Step 4: Feature Splitting\n")
            report.append(f"**Linear Features:** {len(linear_feats)} (for Elastic Net & Logistic Regression)")
            report.append("```")
            for feat in sorted(linear_feats):
                report.append(f"- {feat}")
            report.append("```\n")
            
            report.append(f"**Tree Features:** {len(tree_feats)} (for XGBoost)")
            report.append("```")
            for feat in sorted(tree_feats):
                report.append(f"- {feat}")
            report.append("```\n")
            
            # Step 5: Poison Pill Detection
            report.append(f"#### Step 5: Poison Pill Detection\n")
            
            # Check if poison pills were detected (stored in model if available)
            poison_pills_removed = []
            if hasattr(model, 'poison_pills_removed_'):
                poison_pills_removed = model.poison_pills_removed_
            
            if poison_pills_removed:
                report.append(f"**Removed {len(poison_pills_removed)} poison pills** (High importance, near-zero correlation)\n")
                report.append("```")
                for feat in sorted(poison_pills_removed):
                    report.append(f"- {feat}")
                report.append("```\n")
                
                final_tree_count = len(tree_feats) - len(poison_pills_removed)
                report.append(f"**Final tree features for XGBoost:** {final_tree_count}\n")
            else:
                report.append(f"✅ No poison pills detected - all {len(tree_feats)} tree features passed\n")
            
            # Step 6: XGBoost Final Usage
            if hasattr(model, 'xgboost_model') and model.xgboost_model and hasattr(model.xgboost_model, 'feature_importances_'):
                xgb_importance = model.xgboost_model.feature_importances_
                
                # Features with non-zero importance
                features_used = []
                features_unused = []
                for i, feat in enumerate(tree_feats):
                    if i < len(xgb_importance) and xgb_importance[i] > 0.0:
                        features_used.append((feat, xgb_importance[i]))
                    else:
                        features_unused.append(feat)
                
                report.append(f"#### Step 6: XGBoost Final Usage\n")
                report.append(f"**Features Actually Used:** {len(features_used)} of {len(tree_feats)} available\n")
                
                if features_used:
                    # Calculate correlations if transformed data provided
                    correlations = None
                    if X_selected is not None and y_selected is not None:
                        try:
                            # Ensure tree_feats exist in X_selected
                            available_feats = [f for f in tree_feats if f in X_selected.columns]
                            if available_feats:
                                correlations = X_selected[available_feats].corrwith(y_selected).abs()
                        except Exception:
                            correlations = None
                    
                    report.append("\nFeatures with non-zero importance:")
                    
                    # Prepare table data
                    if correlations is not None:
                        headers = ['Feature', 'Importance', 'Correlation']
                        rows = []
                        for feat, imp in sorted(features_used, key=lambda x: x[1], reverse=True):
                            corr_val = correlations.get(feat, 0.0)
                            rows.append([f"`{feat}`", f"{imp:.4f}", f"{corr_val:.4f}"])
                        report.append("\n" + _format_markdown_table(headers, rows))
                    else:
                        # Fallback when no transformed data available
                        headers = ['Feature', 'Importance']
                        rows = []
                        for feat, imp in sorted(features_used, key=lambda x: x[1], reverse=True):
                            rows.append([f"`{feat}`", f"{imp:.4f}"])
                        report.append("\n" + _format_markdown_table(headers, rows))
                    
                    report.append("")
                
                if features_unused:
                    report.append(f"\n**Features Not Used** ({len(features_unused)} features with zero importance):")
                    report.append("```")
                    for feat in sorted(features_unused):
                        report.append(f"- {feat}")
                    report.append("```")
                    report.append("\n*These features were available but XGBoost found them redundant or unhelpful during training.*\n")
        else:
            # Fallback if no model provided
            report.append("```")
            for feat in sorted(survived):
                report.append(feat)
            report.append("```\n")
        
        return '\n'.join(report)
    
    def _analyze_xgboost_importance(self, xgb_model, feature_names, X_train, y_train):
        """
        Generate comprehensive XGBoost feature importance analysis.

        Args:
            xgb_model: Trained XGBoost model
            feature_names: List of feature names
            X_train: Training features DataFrame
            y_train: Training labels

        Returns:
            str: Formatted markdown XGBoost diagnostics
        """
        # if not SHAP_AVAILABLE:
        #     return "## XGBoost Feature Importance Diagnostics\n\n*SHAP library not available. Install with: pip install shap*"
        
        # if not XGB_AVAILABLE:
        #     return "## XGBoost Feature Importance Diagnostics\n\n*XGBoost library not available.*"
        
        try:
            sections = ["## XGBoost Feature Importance Diagnostics"]

        #     # Gain-based importance
        #     sections.append("### Gain-Based Feature Importance")
        #     gain_importance = xgb_model.get_booster().get_score(importance_type='gain')
        #     gain_df = pd.DataFrame({
        #         'feature': list(gain_importance.keys()),
        #         'gain': list(gain_importance.values())
        #     }).sort_values('gain', ascending=False)

        #     sections.append("\nTop 20 features by information gain:\n")
            
        #     # Prepare table data
        #     headers = ['Feature', 'Gain', 'Category']
        #     rows = []
        #     for idx, row in gain_df.head(20).iterrows():
        #         category = _categorize_feature(row['feature'])
        #         rows.append([row['feature'], f"{row['gain']:.4f}", category])
            
        #     sections.append(_format_markdown_table(headers, rows))
        #     sections.append("")

        #     # Split count importance
        #     sections.append("### Split Count Importance")
        #     split_importance = xgb_model.get_booster().get_score(importance_type='weight')
        #     split_df = pd.DataFrame({
        #         'feature': list(split_importance.keys()),
        #         'splits': list(split_importance.values())
        #     }).sort_values('splits', ascending=False)

        #     sections.append("\nTop 20 features by split count:\n")
            
        #     # Prepare table data
        #     headers = ['Feature', 'Splits', 'Category']
        #     rows = []
        #     for idx, row in split_df.head(20).iterrows():
        #         category = _categorize_feature(row['feature'])
        #         rows.append([row['feature'], f"{row['splits']:.0f}", category])
            
        #     sections.append(_format_markdown_table(headers, rows))
        #     sections.append("")

        #     # Coverage importance
        #     sections.append("### Coverage Importance")
        #     cover_importance = xgb_model.get_booster().get_score(importance_type='cover')
        #     cover_df = pd.DataFrame({
        #         'feature': list(cover_importance.keys()),
        #         'coverage': list(cover_importance.values())
        #     }).sort_values('coverage', ascending=False)

        #     sections.append("\nTop 20 features by coverage (samples affected):\n")
            
        #     # Prepare table data
        #     headers = ['Feature', 'Coverage', 'Category']
        #     rows = []
        #     for idx, row in cover_df.head(20).iterrows():
        #         category = _categorize_feature(row['feature'])
        #         rows.append([row['feature'], f"{row['coverage']:.1f}", category])
            
        #     sections.append(_format_markdown_table(headers, rows))
        #     sections.append("")

        #     # Tree path statistics
        #     sections.append("### Tree Path Statistics")

            # Get tree info
            try:
                tree_df = xgb_model.get_booster().trees_to_dataframe()

                # Basic tree statistics
                num_trees = len(xgb_model.get_booster().get_dump())
                total_nodes = len(tree_df)
                leaf_nodes = tree_df[tree_df['Feature'] == 'Leaf'].shape[0]
                decision_nodes = total_nodes - leaf_nodes

                sections.append(f"""
- **Number of Trees:** {num_trees}
- **Total Nodes:** {total_nodes:,}
- **Decision Nodes:** {decision_nodes:,}
- **Leaf Nodes:** {leaf_nodes:,}
- **Average Nodes per Tree:** {total_nodes/num_trees:.1f}
""")

                # Feature usage across trees
                feature_usage = tree_df[tree_df['Feature'] != 'Leaf']['Feature'].value_counts()
                sections.append("### Feature Usage Across All Trees")
                sections.append("\nTop 20 most used features in tree splits:\n")
                
                # Prepare table data
                headers = ['Feature', 'Trees Used In', 'Category']
                rows = []
                for feature, count in feature_usage.head(20).items():
                    category = _categorize_feature(feature)
                    rows.append([feature, f"{count:.0f}", category])
                
                sections.append(_format_markdown_table(headers, rows))
            except Exception as tree_error:
                sections.append(f"\n*Tree statistics unavailable: {str(tree_error)}*\n")

            return '\n'.join(sections)

        except Exception as e:
            return f"## XGBoost Feature Importance Diagnostics\n\n*Error computing XGBoost diagnostics: {str(e)}*"


class _EnsembleAnalyzer:
    """
    Handles ensemble component diagnostics.
    
    Internal class - not part of public API.
    """
    
    def _format_enhanced_confusion_matrix(self, name, tn, fp, fn, tp, total):
        """
        Generate enhanced confusion matrix with comprehensive annotations and metrics.
        
        Aligned with NFL statistics:
        - Historical home win rate: ~55-57% (league-wide)
        - Model tolerance: ±10% from actual (well-calibrated)
        - Bias thresholds based on NFL betting standards
        
        Args:
            name: Model name
            tn, fp, fn, tp: Confusion matrix values
            total: Total number of games
            
        Returns:
            str: Formatted enhanced confusion matrix with breakdown
        """
        # Calculate all metrics
        actual_away_count = tn + fp
        actual_home_count = fn + tp
        predicted_away_count = tn + fn
        predicted_home_count = fp + tp
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        home_prediction_rate = predicted_home_count / total
        actual_home_rate = actual_home_count / total
        home_bias = home_prediction_rate - actual_home_rate
        
        # Build enhanced matrix with annotations
        sections = []
        sections.append("```")
        sections.append(f"              Predicted")
        sections.append(f"            Away  Home")
        sections.append(f"               ↓     ↓")
        sections.append(f"           {predicted_away_count:2d} pred {predicted_home_count:2d} pred")
        sections.append(f"           away   home")
        sections.append(f"")
        sections.append(f"Actual Away  {tn:3d}   {fp:3d}     ← {actual_away_count} actual away wins")
        sections.append(f"       Home  {fn:3d}   {tp:3d}     ← {actual_home_count} actual home wins")
        sections.append(f"               ↑     ↑")
        sections.append(f"              TN    FP")
        sections.append(f"              FN    TP")
        sections.append("```\n")
        
        # Numbers breakdown
        sections.append("**Numbers Breakdown:**")
        sections.append(f"- **TN = {tn}**: Correctly predicted away win {tn} time{'s' if tn != 1 else ''}")
        sections.append(f"- **FP = {fp}**: Wrongly predicted home {fp} time{'s' if fp != 1 else ''} (away actually won)")
        sections.append(f"- **FN = {fn}**: Wrongly predicted away {fn} time{'s' if fn != 1 else ''} (home actually won)")
        sections.append(f"- **TP = {tp}**: Correctly predicted home win {tp} time{'s' if tp != 1 else ''}\n")
        
        # Precision analysis with NFL context
        if precision >= 0.75:
            precision_quality = "Excellent"
            precision_note = "Very reliable when predicting home wins"
        elif precision >= 0.65:
            precision_quality = "Good"
            precision_note = "Reliable predictions"
        elif precision >= 0.55:
            precision_quality = "Moderate"
            precision_note = "Acceptable but room for improvement"
        else:
            precision_quality = "Poor"
            precision_note = "Too many false alarms - over-confident on home wins"
        
        sections.append(f"**Precision (Home): {precision:.2f}** ({precision_quality})")
        sections.append("```python")
        sections.append(f"precision = TP / (TP + FP) = {tp} / ({tp} + {fp}) = {tp}/{tp+fp} = {precision:.3f}")
        sections.append("```")
        sections.append(f"- *When {name.upper()} says \"home wins\", it's correct {precision:.1%} of the time*")
        sections.append(f"- {precision_note}\n")
        
        # Recall analysis with NFL context
        if recall >= 0.85:
            recall_quality = "Excellent"
            recall_note = "Catches almost all home wins - rarely misses"
        elif recall >= 0.75:
            recall_quality = "Good"
            recall_note = "Catches most home wins"
        elif recall >= 0.65:
            recall_quality = "Moderate"
            recall_note = "Misses some home wins - conservative on home predictions"
        else:
            recall_quality = "Poor"
            recall_note = "Misses too many home wins - under-predicting home advantage"
        
        sections.append(f"**Recall (Home): {recall:.2f}** ({recall_quality})")
        sections.append("```python")
        sections.append(f"recall = TP / (TP + FN) = {tp} / ({tp} + {fn}) = {tp}/{tp+fn} = {recall:.3f}")
        sections.append("```")
        sections.append(f"- *{name.upper()} catches {recall:.1%} of all home wins*")
        sections.append(f"- {recall_note}\n")
        
        # Home prediction rate with NFL bias analysis
        sections.append(f"**Home Prediction Rate: {home_prediction_rate:.1%}**")
        sections.append("```python")
        sections.append(f"home_predictions = (FP + TP) / total = ({fp} + {tp}) / {total} = {predicted_home_count}/{total} = {home_prediction_rate:.3f}")
        sections.append("```")
        sections.append(f"- *{name.upper()} picks home team in {predicted_home_count} out of {total} games*")
        sections.append(f"- **Reality**: {actual_home_count}/{total} ({actual_home_rate:.1%}) were actual home wins")
        
        # Bias interpretation (NFL-aligned thresholds)
        if abs(home_bias) < 0.05:
            bias_severity = "✅"
            bias_interpretation = "well-calibrated"
        elif abs(home_bias) < 0.15:
            bias_severity = "🟡"
            if home_bias > 0:
                bias_interpretation = "slight home bias"
            else:
                bias_interpretation = "slight away bias"
        elif abs(home_bias) < 0.25:
            bias_severity = "⚠️"
            if home_bias > 0:
                bias_interpretation = "moderate home bias"
            else:
                bias_interpretation = "moderate away bias"
        else:
            bias_severity = "🔴"
            if home_bias > 0:
                bias_interpretation = "severe home bias - major concern"
            else:
                bias_interpretation = "severe away bias - major concern"
        
        sections.append(f"- **Gap**: {home_bias:+.1%} {bias_severity} ({bias_interpretation})\n")
        
        # Contextual insights based on precision/recall combination
        if precision >= 0.70 and recall >= 0.75:
            insight = "**Analysis:** 🎯 Excellent balance - reliable and complete home win detection"
        elif precision >= 0.65 and recall < 0.65:
            insight = "**Analysis:** 🔒 Conservative predictor - only predicts home when very confident, but misses opportunities"
        elif precision < 0.60 and recall >= 0.75:
            insight = "**Analysis:** ⚡ Aggressive predictor - catches most home wins but too many false alarms"
        elif precision < 0.60 and recall < 0.65:
            insight = "**Analysis:** ⚠️ Weak home prediction - both unreliable and incomplete coverage"
        else:
            insight = "**Analysis:** 📊 Moderate performance - room for improvement in either reliability or coverage"
        
        sections.append(insight)
        
        return '\n'.join(sections)
    
    def analyze_ensemble_components(self, model, X_test, y_test, y_pred_proba):
        """
        Analyze ensemble component performance and interaction.
        
        Args:
            model: Ensemble model with component models
            X_test: Test features DataFrame
            y_test: Test labels Series
            y_pred_proba: Ensemble prediction probabilities
            
        Returns:
            str: Markdown formatted ensemble diagnostics
        """
        # Check if this is an ensemble by looking for individual model attributes
        if not (hasattr(model, 'xgboost_model') and hasattr(model, 'linear_model') and hasattr(model, 'secondary_linear_model')):
            return ""  # Not an ensemble
        
        # Build components dict from individual attributes
        components = {}
        if model.xgboost_model is not None:
            components['xgboost'] = model.xgboost_model
        if model.linear_model is not None:
            components['elasticnet'] = model.linear_model
        if model.secondary_linear_model is not None:
            # Determine type by checking model class
            model_type = type(model.secondary_linear_model).__name__
            if 'Logistic' in model_type or hasattr(model, 'classes_'):
                components['logistic'] = model.secondary_linear_model
            else:
                components['ridge'] = model.secondary_linear_model
        
        if not components:
            return ""  # No models fitted
        
        sections = ["## Ensemble Component Analysis\n"]
        
        # 1. Individual Component Performance
        sections.append("### Individual Model Performance\n")
        
        component_predictions = {}
        from sklearn.metrics import accuracy_score, roc_auc_score
        
        # Prepare table data
        headers = ['Component', 'Accuracy', 'AUC-ROC', 'Features', 'Predictions']
        rows = []
        
        for name, component_model in components.items():
            # Get component predictions using model-specific features
            if name == 'xgboost' and hasattr(model, 'tree_features_') and model.tree_features_:
                X_component = X_test[model.tree_features_]
                feat_count = len(model.tree_features_)
            elif name in ['elasticnet', 'logistic', 'ridge'] and hasattr(model, 'linear_features_') and model.linear_features_:
                X_component = X_test[model.linear_features_]
                feat_count = len(model.linear_features_)
            else:
                X_component = X_test
                feat_count = len(X_test.columns)
            
            # Generate predictions (handle both classifiers and regressors)
            y_pred_component = component_model.predict(X_component)
            
            # Get probabilities for classifiers
            if hasattr(component_model, 'predict_proba'):
                y_proba_component = component_model.predict_proba(X_component)[:, 1]
            else:
                # Regressor or ElasticNet used as classifier - clip predictions to [0,1]
                y_proba_component = np.clip(y_pred_component, 0, 1)
                y_pred_component = (y_proba_component >= 0.5).astype(int)
            
            # Calculate metrics
            acc = accuracy_score(y_test, y_pred_component)
            try:
                auc = roc_auc_score(y_test, y_proba_component)
            except:
                auc = 0.0
            
            component_predictions[name] = {
                'pred': y_pred_component,
                'proba': y_proba_component,
                'acc': acc,
                'auc': auc
            }
            
            # Add row to table
            home_wins = y_pred_component.sum()
            rows.append([
                f"**{name.upper()}**",
                f"{acc:.1%}",
                f"{auc:.3f}",
                str(feat_count),
                f"{home_wins}/{len(y_pred_component)} home wins"
            ])
        
        sections.append(_format_markdown_table(headers, rows))
        sections.append("")
        
        # 2. Per-Component Confusion Matrices (Enhanced)
        sections.append("### Component Confusion Matrices\n")
        sections.append("Detailed classification breakdown for each component:\n")
        
        for name, predictions in component_predictions.items():
            cm = confusion_matrix(y_test, predictions['pred'])
            tn, fp, fn, tp = cm.ravel()
            total = len(y_test)
            
            sections.append(f"\n#### {name.upper()}\n")
            
            # Use enhanced formatting with comprehensive breakdown
            enhanced_matrix = self._format_enhanced_confusion_matrix(name, tn, fp, fn, tp, total)
            sections.append(enhanced_matrix)
        
        sections.append("")
        
        # 2.5. Comparative Analysis Summary Table
        sections.append("### Comparative Analysis\n")
        sections.append("Side-by-side comparison of all ensemble components:\n")
        
        # Prepare comparative table data
        comp_headers = ['Metric', 'XGBOOST', 'ELASTICNET', 'LOGISTIC', 'Winner']
        comp_rows = []
        
        # Accuracy row
        acc_values = {name: pred['acc'] for name, pred in component_predictions.items()}
        best_acc_name = max(acc_values, key=lambda k: acc_values[k])
        acc_row = ['Accuracy']
        for name in ['xgboost', 'elasticnet', 'logistic']:
            if name in acc_values:
                val = acc_values[name]
                formatted = f"**{val:.1%}**" if name == best_acc_name else f"{val:.1%}"
                acc_row.append(formatted)
            else:
                acc_row.append('-')
        acc_row.append(best_acc_name.upper())
        comp_rows.append(acc_row)
        
        # Precision row
        precision_values = {}
        for name, predictions in component_predictions.items():
            cm = confusion_matrix(y_test, predictions['pred'])
            tn, fp, fn, tp = cm.ravel()
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0
            precision_values[name] = prec
        
        best_prec_name = max(precision_values, key=lambda k: precision_values[k])
        prec_row = ['Precision']
        for name in ['xgboost', 'elasticnet', 'logistic']:
            if name in precision_values:
                val = precision_values[name]
                formatted = f"**{val:.1%}**" if name == best_prec_name else f"{val:.1%}"
                prec_row.append(formatted)
            else:
                prec_row.append('-')
        prec_row.append(best_prec_name.upper())
        comp_rows.append(prec_row)
        
        # Recall row
        recall_values = {}
        for name, predictions in component_predictions.items():
            cm = confusion_matrix(y_test, predictions['pred'])
            tn, fp, fn, tp = cm.ravel()
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0
            recall_values[name] = rec
        
        best_rec_names = [n for n, v in recall_values.items() if abs(v - max(recall_values.values())) < 0.001]
        rec_row = ['Recall']
        for name in ['xgboost', 'elasticnet', 'logistic']:
            if name in recall_values:
                val = recall_values[name]
                formatted = f"**{val:.1%}**" if name in best_rec_names else f"{val:.1%}"
                rec_row.append(formatted)
            else:
                rec_row.append('-')
        rec_row.append('Tie' if len(best_rec_names) > 1 else best_rec_names[0].upper())
        comp_rows.append(rec_row)
        
        # Home Bias row
        bias_values = {}
        for name, predictions in component_predictions.items():
            cm = confusion_matrix(y_test, predictions['pred'])
            tn, fp, fn, tp = cm.ravel()
            total = len(y_test)
            actual_home_count = fn + tp
            predicted_home_count = fp + tp
            home_prediction_rate = predicted_home_count / total
            actual_home_rate = actual_home_count / total
            bias = home_prediction_rate - actual_home_rate
            bias_values[name] = bias
        
        # Best bias is closest to zero
        best_bias_name = min(bias_values, key=lambda x: abs(bias_values[x]))
        bias_row = ['Home Bias']
        for name in ['xgboost', 'elasticnet', 'logistic']:
            if name in bias_values:
                bias = bias_values[name]
                # Add severity indicator
                if abs(bias) < 0.10:
                    indicator = "✓"
                elif abs(bias) < 0.20:
                    indicator = "🟡"
                else:
                    indicator = "⚠️"
                
                formatted = f"**{bias:+.1%}** {indicator}" if name == best_bias_name else f"{bias:+.1%} {indicator}"
                bias_row.append(formatted)
            else:
                bias_row.append('-')
        bias_row.append(best_bias_name.upper())
        comp_rows.append(bias_row)
        
        # Best At row (based on strength analysis)
        strengths_row = ['Best At']
        for name in ['xgboost', 'elasticnet', 'logistic']:
            if name in component_predictions:
                prec = precision_values.get(name, 0)
                rec = recall_values.get(name, 0)
                bias = abs(bias_values.get(name, 0))
                
                # Determine strength
                if prec >= 0.70 and rec >= 0.75 and bias < 0.15:
                    strength = "**Balance**"
                elif rec >= 0.80:
                    strength = "Finding homes"
                elif prec >= 0.70:
                    strength = "Reliability"
                elif bias < 0.10:
                    strength = "Calibration"
                else:
                    strength = "-"
                
                strengths_row.append(strength)
            else:
                strengths_row.append('-')
        
        # Winner in Best At is the one with **Balance** or best overall
        if "**Balance**" in strengths_row:
            winner_idx = strengths_row.index("**Balance**")
            strengths_row.append(['XGBOOST', 'ELASTICNET', 'LOGISTIC'][winner_idx - 1])
        else:
            strengths_row.append(best_acc_name.upper())
        comp_rows.append(strengths_row)
        
        # Generate table
        sections.append("\n" + _format_markdown_table(comp_headers, comp_rows))
        sections.append("")
        
        # 3. Linear Model Coefficients
        sections.append("### Linear Model Feature Importance\n")
        sections.append("Top features driving linear model predictions:\n")
        
        # ElasticNet coefficients
        if 'elasticnet' in components and hasattr(model, 'linear_features_'):
            try:
                en_model = components['elasticnet']
                feature_names = model.linear_features_
                
                # Try multiple ways to extract coefficients
                coef_model = None
                
                # Method 1: Direct coefficient access
                if hasattr(en_model, 'coef_'):
                    coef_model = en_model
                # Method 2: Pipeline with named_steps
                elif hasattr(en_model, 'named_steps'):
                    if 'model' in en_model.named_steps:
                        coef_model = en_model.named_steps['model']
                    elif 'elasticnet' in en_model.named_steps:
                        coef_model = en_model.named_steps['elasticnet']
                # Method 3: Pipeline with steps list
                elif hasattr(en_model, 'steps'):
                    # Get the last step (usually the actual model)
                    coef_model = en_model.steps[-1][1]
                
                if coef_model and hasattr(coef_model, 'coef_'):
                    coefficients = coef_model.coef_
                    
                    # Handle both 1D and 2D coefficient arrays
                    if len(coefficients.shape) > 1:
                        coefficients = coefficients.ravel()
                    
                    # Create dataframe and sort by absolute value
                    if len(coefficients) == len(feature_names):
                        coef_df = pd.DataFrame({
                            'feature': feature_names,
                            'coefficient': coefficients
                        })
                        coef_df['abs_coef'] = coef_df['coefficient'].abs()
                        coef_df = coef_df.sort_values('abs_coef', ascending=False)
                        
                        sections.append("\n#### ElasticNet Top 10 Coefficients\n")
                        headers = ['Feature', 'Coefficient', 'Impact']
                        rows = []
                        for _, row in coef_df.head(10).iterrows():
                            if abs(row['coefficient']) > 0.015:
                                impact = "Strong ↑" if row['coefficient'] > 0 else "Strong ↓"
                            elif abs(row['coefficient']) > 0.008:
                                impact = "Medium ↑" if row['coefficient'] > 0 else "Medium ↓"
                            else:
                                impact = "Weak"
                            rows.append([row['feature'], f"{row['coefficient']:+.4f}", impact])
                        
                        sections.append(_format_markdown_table(headers, rows))
                        sections.append("")
            except Exception as e:
                sections.append(f"\n*ElasticNet coefficients unavailable: {str(e)}*\n")
        
        # Logistic Regression coefficients
        if 'logistic' in components and hasattr(model, 'linear_features_'):
            try:
                lr_model = components['logistic']
                feature_names = model.linear_features_
                
                # Try multiple ways to extract coefficients
                coef_model = None
                
                # Method 1: Direct coefficient access
                if hasattr(lr_model, 'coef_'):
                    coef_model = lr_model
                # Method 2: Pipeline with named_steps
                elif hasattr(lr_model, 'named_steps'):
                    if 'model' in lr_model.named_steps:
                        coef_model = lr_model.named_steps['model']
                    elif 'logistic' in lr_model.named_steps:
                        coef_model = lr_model.named_steps['logistic']
                # Method 3: Pipeline with steps list
                elif hasattr(lr_model, 'steps'):
                    # Get the last step (usually the actual model)
                    coef_model = lr_model.steps[-1][1]
                
                if coef_model and hasattr(coef_model, 'coef_'):
                    coefficients = coef_model.coef_
                    
                    # Handle both 1D and 2D coefficient arrays
                    if len(coefficients.shape) > 1:
                        coefficients = coefficients.ravel()
                    
                    # Create dataframe and sort by absolute value
                    if len(coefficients) == len(feature_names):
                        coef_df = pd.DataFrame({
                            'feature': feature_names,
                            'coefficient': coefficients
                        })
                        coef_df['abs_coef'] = coef_df['coefficient'].abs()
                        coef_df = coef_df.sort_values('abs_coef', ascending=False)
                        
                        sections.append("\n#### Logistic Regression Top 10 Coefficients\n")
                        headers = ['Feature', 'Coefficient', 'Odds Ratio']
                        rows = []
                        for _, row in coef_df.head(10).iterrows():
                            odds_ratio = np.exp(row['coefficient'])
                            rows.append([row['feature'], f"{row['coefficient']:+.4f}", f"{odds_ratio:.2f}x"])
                        
                        sections.append(_format_markdown_table(headers, rows))
                        sections.append("")
            except Exception as e:
                sections.append(f"\n*Logistic coefficients unavailable: {str(e)}*\n")
        
        # 4. Feature Allocation Transparency
        if hasattr(model, 'linear_features_') and hasattr(model, 'tree_features_'):
            sections.append("### Feature Allocation Breakdown\n")
            
            linear_feats = model.linear_features_ or []
            tree_feats = model.tree_features_ or []
            
            sections.append(f"#### Linear Model Features ({len(linear_feats)}):\n")
            sections.append("Used by ElasticNet and Logistic Regression:\n")
            sections.append("```")
            sections.append(", ".join(sorted(linear_feats)))
            sections.append("```\n")
            
            sections.append(f"#### Tree Model Features ({len(tree_feats)}):\n")
            sections.append("Used by XGBoost:\n")
            sections.append("```")
            sections.append(", ".join(sorted(tree_feats)))
            sections.append("```\n")
            
            sections.append("**Allocation Rationale:**")
            sections.append("- **Linear features:** Performance differentials (EPA, points, win rates) - continuous relationships")
            sections.append("- **Tree features:** Contextual features (stadium, weather, rest) - complex interactions")
            sections.append("")
        
        # 5. Error Pattern Analysis
        sections.append("### Component Error Pattern Analysis\n")
        sections.append("Understanding where each component makes mistakes:\n")
        
        for name, predictions in component_predictions.items():
            errors = y_test != predictions['pred']
            false_positives = (predictions['pred'] == 1) & (y_test == 0)
            false_negatives = (predictions['pred'] == 0) & (y_test == 1)
            
            total_errors = errors.sum()
            if total_errors > 0:
                fp_count = false_positives.sum()
                fn_count = false_negatives.sum()
                fp_rate = fp_count / total_errors
                
                sections.append(f"\n#### {name.upper()}\n")
                sections.append(f"- **Total Errors:** {total_errors} games ({total_errors/len(y_test):.1%})")
                sections.append(f"- **False Positives:** {fp_count} (predicted home, was away)")
                sections.append(f"- **False Negatives:** {fn_count} (predicted away, was home)")
                
                # Pattern classification
                if fp_rate > 0.65:
                    pattern = "⚠️ Primarily over-predicts home wins"
                elif fp_rate < 0.35:
                    pattern = "⚠️ Primarily under-predicts home wins"
                else:
                    pattern = "✅ Balanced error distribution"
                
                sections.append(f"- **Error Pattern:** {pattern}")
        
        sections.append("")
        
        # 6. Ensemble Weights
        if hasattr(model, 'weights') and model.weights:
            sections.append("### Ensemble Weights\n")
            sections.append("How much each model contributes to final prediction:\n")
            
            # Map component names to weight keys
            weight_map = {
                'xgboost': 'xgboost',
                'elasticnet': 'elastic_net',
                'logistic': 'logistic',
                'ridge': 'ridge'
            }
            
            for comp_name in components.keys():
                weight_key = weight_map.get(comp_name, comp_name)
                weight = model.weights.get(weight_key, 0.0)
                sections.append(f"- **{comp_name.upper()}:** {weight:.1%}")
            sections.append("")
        
        # 3. Component Agreement Analysis
        sections.append("### Component Agreement\n")
        
        # Count how often all models agree
        unanimous = 0
        split_vote = 0
        
        for i in range(len(y_test)):
            votes = [component_predictions[name]['pred'][i] for name in components.keys()]
            if all(v == votes[0] for v in votes):
                unanimous += 1
            else:
                split_vote += 1
        
        sections.append(f"- **Unanimous Agreement:** {unanimous}/{len(y_test)} games ({unanimous/len(y_test):.1%})")
        sections.append(f"- **Split Decisions:** {split_vote}/{len(y_test)} games ({split_vote/len(y_test):.1%})")
        sections.append("")
        
        # 4. Ensemble vs Best Component
        best_component = max(component_predictions.items(), key=lambda x: x[1]['acc'])
        
        # Calculate ensemble accuracy from probabilities
        y_pred_ensemble = (y_pred_proba[:, 1] >= 0.5).astype(int) if y_pred_proba.ndim > 1 else (y_pred_proba >= 0.5).astype(int)
        ensemble_acc = accuracy_score(y_test, y_pred_ensemble)
        
        sections.append(f"### Ensemble Value\n")
        sections.append(f"- **Best Individual:** {best_component[0].upper()} ({best_component[1]['acc']:.1%})")
        sections.append(f"- **Ensemble:** {ensemble_acc:.1%}")
        
        improvement = ensemble_acc - best_component[1]['acc']
        if improvement > 0.01:
            sections.append(f"- **Ensemble Gain:** +{improvement:.1%} ✅ (Ensemble is better)")
        elif improvement < -0.01:
            sections.append(f"- **Ensemble Loss:** {improvement:.1%} ⚠️ (Best component alone is better)")
        else:
            sections.append(f"- **Ensemble Effect:** {improvement:+.1%} (Marginal difference)")
        
        sections.append("")
        
        # 5. Where Components Disagree (most interesting cases)
        sections.append("### High-Disagreement Games\n")
        sections.append("Games where component models had very different confidence levels:\n")
        
        # Calculate variance in probabilities across components
        proba_matrix = np.array([component_predictions[name]['proba'] for name in components.keys()])
        proba_variance = np.var(proba_matrix, axis=0)
        
        # Get top 5 most disagreed-upon games
        num_disagreements = min(5, len(y_test))
        top_disagreements = np.argsort(proba_variance)[-num_disagreements:][::-1]
        
        # Prepare table data
        headers = ['Game #', 'XGB Prob', 'ElasticNet Prob', 'Logistic Prob', 'Variance', 'Actual']
        rows = []
        
        for idx in top_disagreements:
            xgb_prob = component_predictions.get('xgboost', {}).get('proba', np.zeros(len(y_test)))[idx]
            en_prob = component_predictions.get('elasticnet', {}).get('proba', np.zeros(len(y_test)))[idx]
            lr_prob = component_predictions.get('logistic', {}).get('proba', np.zeros(len(y_test)))[idx]
            variance = proba_variance[idx]
            actual = "Home Win" if y_test.iloc[idx] == 1 else "Away Win"
            
            rows.append([
                str(idx+1),
                f"{xgb_prob:.3f}",
                f"{en_prob:.3f}",
                f"{lr_prob:.3f}",
                f"{variance:.4f}",
                actual
            ])
        
        sections.append("\n" + _format_markdown_table(headers, rows))
        sections.append("")
        sections.append("**Interpretation:** High variance indicates components see different patterns. Low variance means all models agree on prediction confidence.")
        
        return '\n'.join(sections)


# ============================================================================
# PUBLIC API (Facade Pattern)
# ============================================================================

class MetricsAnalyzer:
    """
    Analyzes model performance metrics.
    
    Pattern: Facade Pattern - delegates to specialized internal analyzers
    Complexity: 3 points (facade + 3 internal classes)
    
    This facade provides backward-compatible access to all analysis methods
    while organizing them internally by responsibility:
    - Basic metrics (confusion matrix, confidence)
    - Feature analysis (importance, selection, gauntlet)
    - Ensemble diagnostics
    """
    
    def __init__(self):
        """Initialize with specialized analyzer instances."""
        self._metrics = _BasicMetricsAnalyzer()
        self._features = _FeatureAnalyzer()
        self._ensemble = _EnsembleAnalyzer()
    
    # ========================================================================
    # Basic Metrics Delegation
    # ========================================================================
    
    def analyze_confusion_matrix(self, y_test, y_pred):
        """
        Generate confusion matrix analysis.
        
        Args:
            y_test: True labels
            y_pred: Predicted labels
            
        Returns:
            str: Formatted markdown confusion matrix analysis
        """
        return self._metrics.analyze_confusion_matrix(y_test, y_pred)
    
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
        return self._metrics.analyze_prediction_confidence(y_test, y_pred, y_pred_proba)
    
    # ========================================================================
    # Feature Analysis Delegation
    # ========================================================================
    
    def analyze_feature_importance(self, model, feature_names, X_train=None, y_train=None):
        """
        Generate feature importance analysis.

        Args:
            model: Trained model with feature_importances_ attribute or ensemble with xgboost_model
            feature_names: List or Index of feature names
            X_train: Training features (required for XGBoost diagnostics)
            y_train: Training labels (required for XGBoost diagnostics)

        Returns:
            str: Formatted markdown feature importance analysis
        """
        return self._features.analyze_feature_importance(model, feature_names, X_train, y_train)
    
    def analyze_feature_selection_audit(self, X_train, X_test, y_train=None, model_class=None):
        """
        Generate comprehensive feature selection audit.
        
        Shows:
        - Complete list of features used
        - Features available but excluded
        - Exclusion reasons from FeatureRegistry
        - Feature statistics and quality metrics
        
        Args:
            X_train: Training features DataFrame
            X_test: Test features DataFrame
            y_train: Training target (optional, for correlation calculation)
            model_class: Model class for accessing registry (optional)
            
        Returns:
            str: Formatted markdown feature audit
        """
        return self._features.analyze_feature_selection_audit(X_train, X_test, y_train, model_class)
    
    def analyze_gauntlet_audit(self, selector, original_features, X=None, y=None, X_selected=None, y_selected=None, model=None):
        """
        Generate complete feature pipeline audit from Registry → Final XGBoost Usage.
        
        Shows the entire journey:
        1. The Gauntlet (variance, collinearity, relevance) with WHY details
        2. Feature Splitting (linear vs tree groups)
        3. Poison Pill Detection (if any removed)
        4. XGBoost Final Usage (which features actually got used)
        
        Args:
            selector: FeatureSelector instance with dropped_features_ attribute
            original_features: List of original feature names before selection
            X: Optional DataFrame with original features (for correlation calculations in Stages 1-3)
            y: Optional Series with target variable (for correlation calculations in Stages 1-3)
            X_selected: Optional DataFrame with post-Gauntlet transformed features (for Step 6 correlation)
            y_selected: Optional Series with target variable (for Step 6 correlation)
            model: Optional trained model (for feature splitting and XGBoost usage info)
            
        Returns:
            str: Markdown formatted complete pipeline audit with WHY details
        """
        return self._features.analyze_gauntlet_audit(selector, original_features, X, y, X_selected, y_selected, model)
    
    # ========================================================================
    # Ensemble Analysis Delegation
    # ========================================================================
    
    def analyze_ensemble_components(self, model, X_test, y_test, y_pred_proba):
        """
        Analyze ensemble component performance and interaction.
        
        Args:
            model: Ensemble model with component models
            X_test: Test features DataFrame
            y_test: Test labels Series
            y_pred_proba: Ensemble prediction probabilities
            
        Returns:
            str: Markdown formatted ensemble diagnostics
        """
        return self._ensemble.analyze_ensemble_components(model, X_test, y_test, y_pred_proba)
    
    # ========================================================================
    # Shared Utility Access (for backward compatibility)
    # ========================================================================
    
    def _categorize_feature(self, feature_name):
        """Categorize feature by name pattern."""
        return _categorize_feature(feature_name)
    
    def _get_registry_feature_reasons(self):
        """Extract exclusion reasons from FeatureRegistry."""
        return _get_registry_feature_reasons()


# ============================================================================
# Factory Function
# ============================================================================

def create_metrics_analyzer():
    """Factory function to create metrics analyzer."""
    return MetricsAnalyzer()


__all__ = ['MetricsAnalyzer', 'create_metrics_analyzer']