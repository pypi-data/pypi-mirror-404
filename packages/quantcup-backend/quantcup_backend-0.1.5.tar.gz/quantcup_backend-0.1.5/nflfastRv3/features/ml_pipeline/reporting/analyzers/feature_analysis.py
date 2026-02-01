"""
Feature analysis for ML model performance.

Extracted from analyzers.py - handles feature importance, selection auditing,
and feature pipeline (gauntlet) analysis.
"""

import numpy as np
import pandas as pd
from collections import defaultdict

from nflfastRv3.features.ml_pipeline.reporting.common.formatters import format_markdown_table
from nflfastRv3.features.ml_pipeline.reporting.analyzers.utils import categorize_feature, get_registry_feature_reasons
from nflfastRv3.features.ml_pipeline.reporting.common.correlation_utils import (
    safe_correlation, safe_corrwith, safe_corr_matrix
)


class FeatureAnalyzer:
    """
    Handles feature importance and selection auditing.
    
    This class provides comprehensive feature analysis including:
    - Feature importance rankings
    - Feature selection audits
    - Gauntlet pipeline audits (variance, collinearity, relevance)
    - XGBoost-specific diagnostics
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
            category = categorize_feature(row['feature'])
            rows.append([
                row['feature'],
                f"{row['importance']:.4f}",
                f"{row['importance']/total_importance:.1%}",
                f"{row['cumulative']:.1%}",
                category
            ])
        
        # Generate table with dynamic widths
        table_content = format_markdown_table(headers, rows)
        
        # Category summary
        category_importance = importance_df.groupby(
            importance_df['feature'].apply(categorize_feature)
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
            from nflfastRv3.features.ml_pipeline.utils.feature_registry import FeatureRegistry
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
                corr_val = safe_correlation(X_train[feat], y_train)
                if pd.isna(corr_val):
                    target_corr = 0.0
                else:
                    target_corr = abs(corr_val)
            
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
            category = categorize_feature(stat['feature'])
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
        table_content = format_markdown_table(headers, table_rows)
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
        registry_reasons = get_registry_feature_reasons()
        
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
        # If categorize_feature() returns a new category, defaultdict auto-creates it
        for feat in sorted(disabled_in_registry):
            reason = registry_reasons.get(feat, 'No reason documented')
            category = categorize_feature(feat)
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
                
                # Calculate correlation matrix (using safe methods to avoid constant series warnings)
                numeric_cols = X_before_collinearity.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    corr_matrix = safe_corr_matrix(X_before_collinearity[numeric_cols])
                    target_corr = safe_corrwith(X_before_collinearity[numeric_cols], y)
                    
                    # Check if we got valid results
                    if corr_matrix.empty or target_corr.empty:
                        # Skip collinearity table if correlation failed
                        report.append("\n*Collinearity analysis skipped (insufficient non-constant features)*\n")
                    else:
                        # Apply abs() after safe calculation
                        corr_matrix = corr_matrix.abs()
                        target_corr = target_corr.abs()
                    
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
                    
                    report.append("\n" + format_markdown_table(headers, rows))
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
        # Note: selector has both 'correlation' (linear) and 'correlation_tree' (tree) drops
        dropped_tree = selector.dropped_features_.get('correlation_tree', [])
        
        if dropped_relevance:
            report.append(f"#### Stage 3a: Relevance Filter for Linear Models (Correlation < 0.005)")
            report.append(f"**Dropped {len(dropped_relevance)} features from linear models**\n")
            report.append("Features with correlation below linear model threshold:\n")
            
            # Recalculate correlations if data provided
            if X is not None and y is not None:
                numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    correlations = safe_corrwith(X[numeric_cols], y).abs()
                    
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
                    
                    report.append("\n" + format_markdown_table(headers, rows))
                    report.append("")
            else:
                # Fallback if no data provided
                report.append("```")
                for feat in sorted(dropped_relevance):
                    report.append(f"- {feat}")
                report.append("```\n")
        else:
            report.append(f"#### Stage 3a: Relevance Filter for Linear Models")
            report.append(f"✅ All features passed linear model correlation threshold (>= 0.005)\n")
        
        # Stage 3b: Tree model relevance filter (separate section)
        if dropped_tree:
            report.append(f"#### Stage 3b: Relevance Filter for Tree Models (Correlation < 0.001)")
            report.append(f"**Dropped {len(dropped_tree)} features from tree models**\n")
            report.append("Features below tree model threshold (Per Case Study #12 - trees use low-correlation features):\n")
            
            # Recalculate correlations if data provided
            if X is not None and y is not None:
                numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    correlations = safe_corrwith(X[numeric_cols], y).abs()
                    
                    # Prepare table data
                    headers = ['Feature', 'Correlation with Target']
                    rows = []
                    
                    for feat in sorted(dropped_tree):
                        if feat in correlations:
                            corr_val = correlations[feat]
                            rows.append([f"`{feat}`", f"{corr_val:.4f}"])
                    
                    report.append("\n" + format_markdown_table(headers, rows))
                    report.append("")
            else:
                # Fallback if no data provided
                report.append("```")
                for feat in sorted(dropped_tree):
                    report.append(f"- {feat}")
                report.append("```\n")
        else:
            report.append(f"#### Stage 3b: Relevance Filter for Tree Models")
            report.append(f"✅ All features passed tree model correlation threshold (>= 0.001)\n")
        
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
                        # Ensure tree_feats exist in X_selected
                        available_feats = [f for f in tree_feats if f in X_selected.columns]
                        if available_feats:
                            correlations = safe_corrwith(X_selected[available_feats], y_selected).abs()
                            # Check if we got valid results
                            if correlations.empty:
                                correlations = None
                    
                    report.append("\nFeatures with non-zero importance:")
                    
                    # Prepare table data
                    if correlations is not None:
                        headers = ['Feature', 'Importance', 'Correlation']
                        rows = []
                        for feat, imp in sorted(features_used, key=lambda x: x[1], reverse=True):
                            corr_val = correlations.get(feat, 0.0)
                            rows.append([f"`{feat}`", f"{imp:.4f}", f"{corr_val:.4f}"])
                        report.append("\n" + format_markdown_table(headers, rows))
                    else:
                        # Fallback when no transformed data available
                        headers = ['Feature', 'Importance']
                        rows = []
                        for feat, imp in sorted(features_used, key=lambda x: x[1], reverse=True):
                            rows.append([f"`{feat}`", f"{imp:.4f}"])
                        report.append("\n" + format_markdown_table(headers, rows))
                    
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
        #         category = categorize_feature(row['feature'])
        #         rows.append([row['feature'], f"{row['gain']:.4f}", category])
            
        #     sections.append(format_markdown_table(headers, rows))
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
        #         category = categorize_feature(row['feature'])
        #         rows.append([row['feature'], f"{row['splits']:.0f}", category])
            
        #     sections.append(format_markdown_table(headers, rows))
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
        #         category = categorize_feature(row['feature'])
        #         rows.append([row['feature'], f"{row['coverage']:.1f}", category])
            
        #     sections.append(format_markdown_table(headers, rows))
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
                    category = categorize_feature(feature)
                    rows.append([feature, f"{count:.0f}", category])
                
                sections.append(format_markdown_table(headers, rows))
            except Exception as tree_error:
                sections.append(f"\n*Tree statistics unavailable: {str(tree_error)}*\n")

            return '\n'.join(sections)

        except Exception as e:
            return f"## XGBoost Feature Importance Diagnostics\n\n*Error computing XGBoost diagnostics: {str(e)}*"


__all__ = ['FeatureAnalyzer']
