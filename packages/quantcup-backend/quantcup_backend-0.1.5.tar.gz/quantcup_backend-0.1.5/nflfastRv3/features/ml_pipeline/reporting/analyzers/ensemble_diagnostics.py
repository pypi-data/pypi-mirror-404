"""
Ensemble component diagnostics for ML model performance.

Extracted from analyzers.py - handles ensemble model analysis including
component performance, agreement, and error patterns.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, roc_auc_score

from nflfastRv3.features.ml_pipeline.reporting.common.formatters import format_markdown_table
from nflfastRv3.features.ml_pipeline.reporting.analyzers.utils import categorize_feature


class EnsembleAnalyzer:
    """
    Handles ensemble component diagnostics.
    
    This class provides comprehensive ensemble analysis including:
    - Individual component performance
    - Component confusion matrices
    - Comparative analysis
    - Feature allocation breakdown
    - Error pattern analysis
    - Component agreement metrics
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
        
        sections.append(format_markdown_table(headers, rows))
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
        sections.append("\n" + format_markdown_table(comp_headers, comp_rows))
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
                        
                        sections.append(format_markdown_table(headers, rows))
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
                        
                        sections.append(format_markdown_table(headers, rows))
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
        
        sections.append("\n" + format_markdown_table(headers, rows))
        sections.append("")
        sections.append("**Interpretation:** High variance indicates components see different patterns. Low variance means all models agree on prediction confidence.")
        
        return '\n'.join(sections)


__all__ = ['EnsembleAnalyzer']
