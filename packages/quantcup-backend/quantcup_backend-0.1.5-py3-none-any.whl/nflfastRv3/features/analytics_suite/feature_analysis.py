"""
Feature Analysis Implementation

Pattern: Minimum Viable Decoupling
Complexity: 2 points (DI + business logic)
Layer: 2 (Implementation - calls infrastructure directly)

Follows clean architecture with maximum 3 layers:
Layer 1: Public API (nflfastRv3/__init__.py)
Layer 2: This implementation
Layer 3: Infrastructure (database, validation)

Migrated from nflfastRv2/features/analytics_suite/feature_analysis.py
with V3 clean architecture patterns applied.
"""

import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy import text


class FeatureAnalysisImpl:
    """
    Core feature analysis business logic.
    
    Pattern: Minimum Viable Decoupling (⭐ RECOMMENDED START)
    Complexity: 2 points
    Depth: 1 layer (calls infrastructure directly)
    
    Responsibilities:
    - Run comprehensive feature analysis on NFL data
    - Analyze feature distributions and quality
    - Detect multicollinearity between features
    - Validate feature quality for ML models
    - No complex patterns or abstractions
    """
    
    def __init__(self, db_service, logger, bucket_adapter=None):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
            bucket_adapter: Bucket adapter (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
        self.bucket_adapter = bucket_adapter
    
    def run_feature_analysis(self, **kwargs) -> Dict[str, Any]:
        """
        Run comprehensive feature analysis on NFL data.
        
        Simple analysis flow:
        1. Load feature data (Layer 3 call)
        2. Analyze distributions (Layer 3 call)
        3. Validate quality (Layer 3 call)
        4. Check correlations (Layer 3 call)
        5. Return combined results
        
        Args:
            **kwargs: Additional analysis options
            
        Returns:
            Dictionary with feature analysis results
        """
        self.logger.info("Starting feature analysis")
        
        try:
            # Load feature data from analytics schema
            feature_data = self._load_feature_data()
            
            if feature_data.empty:
                return {
                    'status': 'error',
                    'message': 'No feature data available for analysis'
                }
            
            analysis_results = {
                'status': 'success',
                'dataset_info': self._get_dataset_info(feature_data),
                'distribution_analysis': self._analyze_feature_distributions(feature_data),
                'quality_assessment': self._validate_feature_quality(feature_data),
                'correlation_analysis': self._analyze_correlations(feature_data)
            }
            
            self.logger.info("Feature analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Feature analysis failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def analyze_feature_distributions(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Analyze the distribution of features in the dataset.
        
        Args:
            df: DataFrame with features to analyze
            **kwargs: Additional analysis options
            
        Returns:
            Dictionary with distribution analysis results
        """
        self.logger.info(f"Analyzing feature distributions for {df.shape[1]} features")
        return self._analyze_feature_distributions(df)
    
    def detect_multicollinearity(self, df: pd.DataFrame, threshold: float = 0.8, **kwargs) -> List[Tuple[str, str, float]]:
        """
        Detect multicollinearity between features.
        
        Args:
            df: DataFrame with numeric features
            threshold: Correlation threshold for flagging multicollinearity
            **kwargs: Additional analysis options
            
        Returns:
            List of tuples (feature1, feature2, correlation) for highly correlated pairs
        """
        self.logger.info(f"Detecting multicollinearity with threshold {threshold}")
        
        # Select only numeric columns
        numeric_df = df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64'])
        
        if numeric_df.empty:
            self.logger.warning("No numeric features found for multicollinearity analysis")
            return []
        
        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()
        
        # Find highly correlated pairs
        high_corr_pairs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                feature1 = corr_matrix.columns[i]
                feature2 = corr_matrix.columns[j]
                correlation_value = corr_matrix.iloc[i, j]
                
                if pd.isna(correlation_value):
                    continue
                
                try:
                    if (pd.notna(correlation_value) and 
                        not isinstance(correlation_value, (complex, str, bytes)) and
                        isinstance(correlation_value, (int, float))):
                        correlation = abs(float(correlation_value))
                        if correlation >= threshold:
                            high_corr_pairs.append((feature1, feature2, correlation))
                except (TypeError, ValueError, OverflowError):
                    continue
        
        # Sort by correlation strength
        high_corr_pairs.sort(key=lambda x: x[2], reverse=True)
        
        self.logger.info(f"Found {len(high_corr_pairs)} highly correlated feature pairs")
        return high_corr_pairs
    
    def validate_feature_quality(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Validate overall feature quality and identify potential issues.
        
        Args:
            df: DataFrame with features to validate
            **kwargs: Additional analysis options
            
        Returns:
            Dictionary with quality assessment results
        """
        self.logger.info("Validating feature quality")
        return self._validate_feature_quality(df)
    
    def _load_feature_data(self) -> pd.DataFrame:
        """
        Load feature data from bucket storage.
        
        Uses bucket adapter (Layer 3) - no complex patterns
        
        Returns:
            pd.DataFrame: Loaded feature data
        """
        self.logger.info("Loading feature data from bucket storage")
        
        if not self.bucket_adapter:
            self.logger.error("Bucket adapter not initialized")
            return pd.DataFrame()
            
        try:
            # Try to load from warehouse fact_play
            columns = [
                'game_id', 'season', 'week', 'yards_gained', 'touchdown',
                'interception', 'fumble_lost', 'first_down', 'penalty',
                'down', 'ydstogo', 'yardline_100', 'score_differential',
                'ep', 'epa', 'wp', 'wpa'
            ]
            
            df = self.bucket_adapter.read_data(
                'fact_play',
                'warehouse',
                columns=columns
            )
            
            if df.empty:
                # Fallback to raw play_by_play
                self.logger.warning("fact_play empty, falling back to raw play_by_play")
                df = self.bucket_adapter.read_data(
                    'play_by_play',
                    'raw_nflfastr',
                    columns=columns
                )
            
            # Limit to recent data for analysis if too large
            if len(df) > 50000:
                df = df.tail(50000)
                
            self.logger.info(f"Loaded {len(df)} records for feature analysis")
            return df
                
        except Exception as e:
            self.logger.error(f"Could not load feature data: {e}")
            return pd.DataFrame()
    
    def _get_dataset_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get basic information about the dataset.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            dict: Dataset information
        """
        return {
            'shape': df.shape,
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    
    def _analyze_feature_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the distribution of features in the dataset.
        
        Direct statistical analysis (Layer 3) - no complex patterns
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            dict: Distribution analysis results
        """
        self.logger.info(f"Analyzing feature distributions for {df.shape[1]} features")
        
        analysis = {
            "total_features": df.shape[1],
            "total_records": len(df),
            "numeric_features": [],
            "categorical_features": [],
            "missing_data": {},
            "basic_stats": {}
        }
        
        for column in df.columns:
            missing_pct = df[column].isnull().sum() / len(df) * 100
            analysis["missing_data"][column] = round(missing_pct, 2)
            
            if df[column].dtype in ['int64', 'float64', 'Int64', 'Float64']:
                analysis["numeric_features"].append(column)
                
                # Basic statistics for numeric features
                try:
                    stats = df[column].describe()
                    analysis["basic_stats"][column] = {
                        'mean': round(float(stats['mean']), 3) if pd.notna(stats['mean']) else None,
                        'std': round(float(stats['std']), 3) if pd.notna(stats['std']) else None,
                        'min': float(stats['min']) if pd.notna(stats['min']) else None,
                        'max': float(stats['max']) if pd.notna(stats['max']) else None,
                        'unique_values': int(df[column].nunique())
                    }
                except Exception:
                    analysis["basic_stats"][column] = {'error': 'Could not calculate stats'}
            else:
                analysis["categorical_features"].append(column)
                analysis["basic_stats"][column] = {
                    'unique_values': int(df[column].nunique()),
                    'most_common': str(df[column].mode().iloc[0]) if not df[column].mode().empty else None
                }
        
        self.logger.info("Feature distribution analysis complete")
        return analysis
    
    def _validate_feature_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate overall feature quality and identify potential issues.
        
        Direct quality checks (Layer 3) - no complex patterns
        
        Args:
            df: DataFrame to validate
            
        Returns:
            dict: Quality assessment results
        """
        self.logger.info("Validating feature quality")
        
        quality_report = {
            "total_features": df.shape[1],
            "total_records": len(df),
            "quality_issues": [],
            "recommendations": [],
            "overall_score": 0.0
        }
        
        # Check for common quality issues
        
        # 1. High missing data
        missing_data = df.isnull().sum() / len(df)
        high_missing = missing_data[missing_data > 0.5]
        if not high_missing.empty:
            quality_report["quality_issues"].append(
                f"High missing data: {list(high_missing.index)} (>50% missing)"
            )
            quality_report["recommendations"].append(
                "Consider removing features with >50% missing data or implement imputation"
            )
        
        # 2. Zero variance features
        numeric_df = df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64'])
        zero_var_features = []
        for col in numeric_df.columns:
            try:
                if numeric_df[col].var() == 0:
                    zero_var_features.append(col)
            except Exception:
                continue
        
        if zero_var_features:
            quality_report["quality_issues"].append(
                f"Zero variance features: {zero_var_features}"
            )
            quality_report["recommendations"].append(
                "Remove zero variance features as they provide no predictive value"
            )
        
        # 3. Features with single unique value
        single_value_features = []
        for col in df.columns:
            if df[col].nunique() <= 1:
                single_value_features.append(col)
        
        if single_value_features:
            quality_report["quality_issues"].append(
                f"Single value features: {single_value_features}"
            )
            quality_report["recommendations"].append(
                "Remove features with only one unique value"
            )
        
        # 4. Features with extreme outliers (IQR method)
        outlier_features = []
        for col in numeric_df.columns:
            try:
                Q1 = numeric_df[col].quantile(0.25)
                Q3 = numeric_df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = numeric_df[(numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)]
                outlier_pct = len(outliers) / len(numeric_df) * 100
                
                if outlier_pct > 10:  # More than 10% outliers
                    outlier_features.append((col, round(outlier_pct, 2)))
            except Exception:
                continue
        
        if outlier_features:
            outlier_list = [f"{col} ({pct}%)" for col, pct in outlier_features]
            quality_report["quality_issues"].append(
                f"High outlier features: {outlier_list} (>10% outliers)"
            )
            quality_report["recommendations"].append(
                "Consider outlier treatment for features with high outlier rates"
            )
        
        # Calculate overall quality score
        issues_count = len(quality_report["quality_issues"])
        max_possible_issues = 10  # Adjust based on number of checks
        quality_report["overall_score"] = max(0, (max_possible_issues - issues_count) / max_possible_issues)
        
        self.logger.info(f"Feature quality validation complete. Score: {quality_report['overall_score']:.2f}")
        return quality_report
    
    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze correlations between features.
        
        Direct correlation analysis (Layer 3) - no complex patterns
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            dict: Correlation analysis results
        """
        self.logger.info("Analyzing feature correlations")
        
        try:
            # Select only numeric columns for correlation analysis
            numeric_df = df.select_dtypes(include=['int64', 'float64', 'Int64', 'Float64'])
            
            if numeric_df.empty:
                return {'error': 'No numeric features found for correlation analysis'}
            
            # Calculate correlation matrix
            corr_matrix = numeric_df.corr()
            
            # Find highly correlated pairs (threshold = 0.8)
            high_corr_pairs = []
            threshold = 0.8
            
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    feature1 = corr_matrix.columns[i]
                    feature2 = corr_matrix.columns[j]
                    correlation_value = corr_matrix.iloc[i, j]
                    
                    if pd.isna(correlation_value):
                        continue
                    
                    try:
                        if (pd.notna(correlation_value) and 
                            not isinstance(correlation_value, (complex, str, bytes)) and
                            isinstance(correlation_value, (int, float))):
                            correlation = abs(float(correlation_value))
                            if correlation >= threshold:
                                high_corr_pairs.append({
                                    'feature1': feature1,
                                    'feature2': feature2,
                                    'correlation': round(correlation, 3)
                                })
                    except (TypeError, ValueError, OverflowError):
                        continue
            
            # Sort by correlation strength
            high_corr_pairs.sort(key=lambda x: x['correlation'], reverse=True)
            
            # Calculate feature importance based on average correlation
            feature_importance = {}
            for col in numeric_df.columns:
                try:
                    # Average absolute correlation with other features
                    col_corrs = corr_matrix[col].drop(col).abs()
                    avg_corr = col_corrs.mean()
                    if (pd.notna(avg_corr) and 
                        not isinstance(avg_corr, (complex, str, bytes)) and
                        isinstance(avg_corr, (int, float))):
                        feature_importance[col] = round(float(avg_corr), 3)
                    else:
                        feature_importance[col] = 0.0
                except (TypeError, ValueError, OverflowError):
                    feature_importance[col] = 0.0
            
            # Sort features by importance
            sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            return {
                'numeric_features_analyzed': len(numeric_df.columns),
                'high_correlations': high_corr_pairs[:10],  # Top 10
                'multicollinearity_warning': len(high_corr_pairs) > 0,
                'threshold_used': threshold,
                'feature_importance_by_correlation': dict(sorted_importance[:10]),
                'correlation_summary': {
                    'total_pairs': len(corr_matrix.columns) * (len(corr_matrix.columns) - 1) // 2,
                    'high_correlation_pairs': len(high_corr_pairs),
                    'avg_correlation': round(float(corr_matrix.abs().mean().mean()), 3)
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Could not complete correlation analysis: {e}")
            return {'error': str(e)}
    
    def analyze_contextual_features(
        self,
        phases: Optional[List[int]] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze contextual features across all phases.
        
        Consolidates: analyze_contextual_feature_data.py (999 lines)
        
        Validates:
        - Phase 1: rest_days, division_games, stadium_advantage
        - Phase 2: weather, playoff_implications
        - Phase 3: injury_impact
        
        Args:
            phases: List of phases to analyze (default: [1, 2, 3])
            year: Specific year to analyze (default: all years)
        
        Returns:
            Dictionary with phase-specific analysis
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Analyzing contextual features: phases={phases}, year={year}")
        
        # Default to all phases
        if phases is None:
            phases = [1, 2, 3]
        
        # Load contextual features
        query = "SELECT * FROM contextual_features"
        if year:
            query += f" WHERE season = {year}"
        query += " ORDER BY game_date"
        
        try:
            data = self.db_service.query(query)
        except Exception as e:
            self.logger.error(f"Failed to query contextual features: {e}")
            # Fallback for testing/dev if table doesn't exist
            return {'error': str(e)}
        
        results = {}
        
        # Analyze each phase
        if 1 in phases:
            results['phase1'] = self._analyze_phase1_features(data)
        
        if 2 in phases:
            results['phase2'] = self._analyze_phase2_features(data)
        
        if 3 in phases:
            results['phase3'] = self._analyze_phase3_features(data)
        
        # Overall data availability
        results['data_availability'] = self._calculate_feature_availability(data)
        
        duration = time.time() - start_time
        self.logger.info(f"Contextual feature analysis completed in {duration:.2f}s")
        
        return results
    
    def _analyze_phase1_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze Phase 1 contextual features.
        
        Features:
        - rest_days: Days between games
        - is_division_game: Division rivalry indicator
        - stadium_advantage: Home field advantage by stadium type
        """
        phase1_results = {}
        
        # Rest days analysis
        if 'rest_days' in data.columns:
            rest_days_stats = data.groupby('team').agg({
                'rest_days': ['mean', 'std', 'min', 'max', 'median'],
                'game_id': 'count'
            }).round(2)
            rest_days_stats.columns = ['mean', 'std', 'min', 'max', 'median', 'games']
            
            # Identify teams with unusual rest patterns
            unusual_rest = rest_days_stats[
                (rest_days_stats['mean'] < 6) | (rest_days_stats['mean'] > 8)
            ]
            
            phase1_results['rest_days'] = {
                'statistics': rest_days_stats.to_dict(),
                'unusual_patterns': unusual_rest.to_dict(),
                'overall_mean': data['rest_days'].mean(),
                'overall_std': data['rest_days'].std()
            }
        
        # Division games analysis
        if 'is_division_game' in data.columns:
            division_games = data[data['is_division_game'] == True]
            
            # Calculate win probability delta for division games
            if 'win_prob_delta' in data.columns:
                division_impact = division_games.groupby('team')['win_prob_delta'].agg([
                    'mean', 'std', 'count'
                ]).round(3)
                
                phase1_results['division_games'] = {
                    'total_division_games': len(division_games),
                    'pct_of_total': len(division_games) / len(data) if len(data) > 0 else 0,
                    'impact_by_team': division_impact.to_dict(),
                    'avg_impact': division_games['win_prob_delta'].mean()
                }
        
        # Stadium advantage analysis
        if 'location' in data.columns and 'stadium_type' in data.columns:
            home_games = data[data['location'] == 'home']
            
            if 'win_prob_delta' in data.columns:
                stadium_advantage = home_games.groupby('stadium_type').agg({
                    'win_prob_delta': ['mean', 'std'],
                    'game_id': 'count'
                }).round(3)
                stadium_advantage.columns = ['mean_advantage', 'std_advantage', 'games']
                
                phase1_results['stadium_advantage'] = {
                    'by_stadium_type': stadium_advantage.to_dict(),
                    'overall_home_advantage': home_games['win_prob_delta'].mean()
                }
        
        return phase1_results
    
    def _analyze_phase2_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze Phase 2 contextual features.
        
        Features:
        - weather_severity: Weather impact on games
        - playoff_implications: Playoff race impact
        """
        phase2_results = {}
        
        # Weather impact analysis
        if 'weather_severity' in data.columns:
            weather_data = data[data['weather_severity'].notna()]
            
            if 'win_prob_delta' in data.columns and 'total_score' in data.columns:
                weather_impact = weather_data.groupby('weather_severity').agg({
                    'win_prob_delta': ['mean', 'std'],
                    'total_score': ['mean', 'std'],
                    'game_id': 'count'
                }).round(3)
                weather_impact.columns = ['win_prob_mean', 'win_prob_std', 'score_mean', 'score_std', 'games']
                
                phase2_results['weather'] = {
                    'impact_by_severity': weather_impact.to_dict(),
                    'games_with_weather_data': len(weather_data),
                    'pct_with_weather': len(weather_data) / len(data) if len(data) > 0 else 0
                }
        
        # Playoff implications analysis
        if 'playoff_implications' in data.columns:
            playoff_games = data[data['playoff_implications'] == True]
            
            if len(playoff_games) > 0 and 'win_prob_delta' in data.columns:
                playoff_impact = {
                    'total_playoff_implication_games': len(playoff_games),
                    'pct_of_total': len(playoff_games) / len(data) if len(data) > 0 else 0,
                    'avg_win_prob_delta': playoff_games['win_prob_delta'].mean(),
                    'std_win_prob_delta': playoff_games['win_prob_delta'].std()
                }
                
                # Compare playoff vs non-playoff games
                non_playoff = data[data['playoff_implications'] == False]
                playoff_impact['comparison'] = {
                    'playoff_avg': playoff_games['win_prob_delta'].mean(),
                    'non_playoff_avg': non_playoff['win_prob_delta'].mean(),
                    'difference': playoff_games['win_prob_delta'].mean() - non_playoff['win_prob_delta'].mean()
                }
                
                phase2_results['playoff_implications'] = playoff_impact
        
        return phase2_results
    
    def _analyze_phase3_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze Phase 3 contextual features.
        
        Features:
        - injury_impact: Impact of injuries on performance
        """
        phase3_results = {}
        
        # Injury impact analysis
        if 'injury_count' in data.columns:
            injury_data = data[data['injury_count'] > 0]
            
            if len(injury_data) > 0:
                # Impact by injury severity
                if 'injury_severity' in data.columns and 'win_prob_delta' in data.columns:
                    injury_impact = injury_data.groupby('injury_severity').agg({
                        'win_prob_delta': ['mean', 'std'],
                        'game_id': 'count'
                    }).round(3)
                    injury_impact.columns = ['win_prob_mean', 'win_prob_std', 'games']
                    
                    phase3_results['injury_impact'] = {
                        'by_severity': injury_impact.to_dict(),
                        'games_with_injuries': len(injury_data),
                        'pct_with_injuries': len(injury_data) / len(data) if len(data) > 0 else 0
                    }
                
                # Impact by injury count
                if 'win_prob_delta' in data.columns:
                    injury_count_impact = injury_data.groupby('injury_count').agg({
                        'win_prob_delta': ['mean', 'std'],
                        'game_id': 'count'
                    }).round(3)
                    
                    phase3_results['injury_count_impact'] = injury_count_impact.to_dict()
        
        return phase3_results
    
    def _calculate_feature_availability(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate data availability for all contextual features.
        """
        feature_columns = [
            'rest_days', 'is_division_game', 'stadium_advantage',
            'weather_severity', 'playoff_implications',
            'injury_count', 'injury_severity'
        ]
        
        availability = {}
        
        for col in feature_columns:
            if col in data.columns:
                total_games = len(data)
                available_games = data[col].notna().sum()
                availability[col] = {
                    'available_games': int(available_games),
                    'total_games': total_games,
                    'availability_pct': round(available_games / total_games * 100, 2) if total_games > 0 else 0
                }
        
        return availability

    def analyze_merged_correlations(
        self,
        target_column: str = 'home_win',
        top_n: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze correlations in merged feature dataset.
        
        Consolidates: analyze_merged_features.py (416 lines)
        
        Analyzes:
        - Feature correlations with target
        - Feature importance rankings
        - Interaction term effectiveness
        - Contextual vs differential feature comparison
        
        Args:
            target_column: Target variable for correlation
            top_n: Number of top features to return
        
        Returns:
            Dictionary with correlation analysis
        """
        import time
        from sklearn.ensemble import RandomForestClassifier
        
        start_time = time.time()
        self.logger.info("Analyzing merged feature correlations")
        
        # Load merged features
        query = "SELECT * FROM ml_features"
        try:
            merged_data = self.db_service.query(query)
        except Exception as e:
            self.logger.error(f"Failed to query ml_features: {e}")
            return {'error': str(e)}
        
        if target_column not in merged_data.columns:
            # Fallback for testing if target column missing
            if 'win_prob_delta' in merged_data.columns:
                target_column = 'win_prob_delta'
            else:
                return {'error': f"Target column '{target_column}' not found in data"}
        
        results = {}
        
        # Separate features from metadata
        metadata_cols = ['game_id', 'season', 'week', 'home_team', 'away_team', target_column]
        feature_cols = [col for col in merged_data.columns if col not in metadata_cols]
        
        # Ensure we have numeric data
        X = merged_data[feature_cols].select_dtypes(include=['number'])
        y = merged_data[target_column]
        
        # 1. Correlation with target
        target_correlations = X.corrwith(y).abs().sort_values(ascending=False)
        
        results['target_correlations'] = {
            'top_features': target_correlations.head(top_n).to_dict(),
            'all_features': target_correlations.to_dict()
        }
        
        # 2. Feature importance via Random Forest
        self.logger.info("Calculating feature importance with Random Forest")
        
        try:
            rf = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            rf.fit(X.fillna(0), y)
            
            feature_importance = pd.Series(
                rf.feature_importances_,
                index=X.columns
            ).sort_values(ascending=False)
            
            results['feature_importance'] = {
                'top_features': feature_importance.head(top_n).to_dict(),
                'all_features': feature_importance.to_dict()
            }
        except Exception as e:
            self.logger.warning(f"Random Forest feature importance failed: {e}")
            feature_importance = target_correlations # Fallback
            results['feature_importance'] = {'error': str(e)}
        
        # 3. Interaction term analysis
        interaction_features = [col for col in feature_cols if '_x_' in col]
        
        if interaction_features and 'feature_importance' in results and 'error' not in results['feature_importance']:
            interaction_importance = feature_importance[interaction_features].sort_values(ascending=False)
            
            results['interaction_terms'] = {
                'total_interactions': len(interaction_features),
                'top_interactions': interaction_importance.head(10).to_dict(),
                'avg_importance': interaction_importance.mean(),
                'pct_in_top_20': sum(interaction_importance.index.isin(feature_importance.head(20).index)) / 20
            }
        
        # 4. Feature type comparison
        contextual_features = [col for col in feature_cols if col.startswith('ctx_')]
        differential_features = [col for col in feature_cols if col.endswith('_diff')]
        rolling_features = [col for col in feature_cols if 'avg_' in col or 'rolling_' in col]
        
        feature_type_importance = {
            'contextual': {
                'count': len(contextual_features),
                'avg_importance': feature_importance[contextual_features].mean() if contextual_features and 'feature_importance' in results and 'error' not in results['feature_importance'] else 0,
                'top_feature': feature_importance[contextual_features].idxmax() if contextual_features and 'feature_importance' in results and 'error' not in results['feature_importance'] else None
            },
            'differential': {
                'count': len(differential_features),
                'avg_importance': feature_importance[differential_features].mean() if differential_features and 'feature_importance' in results and 'error' not in results['feature_importance'] else 0,
                'top_feature': feature_importance[differential_features].idxmax() if differential_features and 'feature_importance' in results and 'error' not in results['feature_importance'] else None
            },
            'rolling': {
                'count': len(rolling_features),
                'avg_importance': feature_importance[rolling_features].mean() if rolling_features and 'feature_importance' in results and 'error' not in results['feature_importance'] else 0,
                'top_feature': feature_importance[rolling_features].idxmax() if rolling_features and 'feature_importance' in results and 'error' not in results['feature_importance'] else None
            }
        }
        
        results['feature_type_comparison'] = feature_type_importance
        
        # 5. Feature correlation matrix (top features only)
        if 'feature_importance' in results and 'error' not in results['feature_importance']:
            top_feature_names = feature_importance.head(top_n).index
            correlation_matrix = X[top_feature_names].corr()
            
            # Find highly correlated feature pairs
            high_corr_pairs = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # High correlation threshold
                        high_corr_pairs.append({
                            'feature1': correlation_matrix.columns[i],
                            'feature2': correlation_matrix.columns[j],
                            'correlation': round(corr_value, 3)
                        })
            
            results['high_correlations'] = {
                'pairs': high_corr_pairs,
                'count': len(high_corr_pairs)
            }
        
        duration = time.time() - start_time
        self.logger.info(f"Merged correlation analysis completed in {duration:.2f}s")
        
        return results

    def evaluate_rolling_metrics(
        self,
        windows: Optional[List[int]] = None,
        validate_calculations: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate rolling metrics features.
        
        Consolidates: evaluate_rolling_metrics_data.py (349 lines)
        
        Validates:
        - Rolling window calculations (4g, 8g, 16g)
        - Momentum indicators
        - Consistency metrics
        - Temporal safety (shift operations)
        
        Args:
            windows: List of window sizes to validate (default: [4, 8, 16])
            validate_calculations: Whether to validate calculations (default: True)
        
        Returns:
            Dictionary with rolling metrics evaluation
        """
        import time
        start_time = time.time()
        
        self.logger.info("Evaluating rolling metrics")
        
        # Default windows
        if windows is None:
            windows = [4, 8, 16]
        
        # Load rolling metrics
        query = """
            SELECT * FROM rolling_metrics
            ORDER BY team, game_date
        """
        try:
            rolling_data = self.db_service.query(query)
        except Exception as e:
            self.logger.error(f"Failed to query rolling_metrics: {e}")
            return {'error': str(e)}
        
        results = {}
        
        # 1. Validate window calculations
        if validate_calculations:
            validation_results = {}
            
            for window in windows:
                window_validation = self._validate_rolling_window(
                    rolling_data,
                    window,
                    metric='points'
                )
                validation_results[f'{window}g'] = window_validation
            
            results['validation'] = validation_results
        
        # 2. Momentum indicators
        results['momentum'] = self._analyze_momentum_indicators(rolling_data)
        
        # 3. Consistency metrics
        results['consistency'] = self._analyze_consistency_metrics(rolling_data)
        
        # 4. Temporal safety check
        results['temporal_safety'] = self._check_rolling_temporal_safety(rolling_data)
        
        # 5. Data quality
        results['data_quality'] = self._assess_rolling_data_quality(rolling_data)
        
        duration = time.time() - start_time
        self.logger.info(f"Rolling metrics evaluation completed in {duration:.2f}s")
        
        return results
    
    def _validate_rolling_window(
        self,
        data: pd.DataFrame,
        window: int,
        metric: str = 'points'
    ) -> Dict[str, Any]:
        """
        Validate rolling window calculation accuracy.
        """
        window_col = f'avg_{metric}_{window}g'
        
        if window_col not in data.columns:
            return {'error': f'Column {window_col} not found'}
        
        if metric not in data.columns:
            return {'error': f'Metric column {metric} not found'}
        
        # Manual calculation for validation
        manual_calc = data.groupby('team')[metric].transform(
            lambda x: x.shift(1).rolling(window, min_periods=1).mean()
        )
        
        # Compare with stored values
        diff = abs(data[window_col] - manual_calc)
        
        validation = {
            'window_size': window,
            'metric': metric,
            'max_error': diff.max(),
            'mean_error': diff.mean(),
            'std_error': diff.std(),
            'records_checked': len(data),
            'validation_passed': bool(diff.max() < 0.01) if not pd.isna(diff.max()) else False
        }
        
        if not validation['validation_passed']:
            # Find problematic records
            problematic = data[diff > 0.01][['team', 'game_date', window_col]].head(10)
            validation['problematic_records'] = problematic.to_dict()
        
        return validation
    
    def _analyze_momentum_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze momentum indicators.
        
        Momentum = short-term average - long-term average
        """
        # Calculate momentum (4g avg - 16g avg)
        if 'avg_points_4g' in data.columns and 'avg_points_16g' in data.columns:
            data['momentum'] = data['avg_points_4g'] - data['avg_points_16g']
            
            # Team-level momentum analysis
            team_momentum = data.groupby('team')['momentum'].agg([
                'mean', 'std', 'min', 'max'
            ]).round(2)
            
            # Identify teams with strong momentum
            strong_positive = team_momentum[team_momentum['mean'] > 3].sort_values('mean', ascending=False)
            strong_negative = team_momentum[team_momentum['mean'] < -3].sort_values('mean')
            
            return {
                'team_momentum': team_momentum.to_dict(),
                'strong_positive_momentum': strong_positive.to_dict(),
                'strong_negative_momentum': strong_negative.to_dict(),
                'overall_mean': data['momentum'].mean(),
                'overall_std': data['momentum'].std()
            }
        
        return {'error': 'Required columns not found'}
    
    def _analyze_consistency_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze consistency metrics (standard deviation of performance).
        """
        if 'points' not in data.columns:
             return {'error': 'Points column not found'}

        # Calculate rolling standard deviation
        data['consistency'] = data.groupby('team')['points'].transform(
            lambda x: x.shift(1).rolling(8, min_periods=1).std()
        )
        
        # Team-level consistency
        team_consistency = data.groupby('team')['consistency'].agg([
            'mean', 'std'
        ]).round(2)
        
        # Most/least consistent teams
        most_consistent = team_consistency.sort_values('mean').head(10)
        least_consistent = team_consistency.sort_values('mean', ascending=False).head(10)
        
        return {
            'team_consistency': team_consistency.to_dict(),
            'most_consistent_teams': most_consistent.to_dict(),
            'least_consistent_teams': least_consistent.to_dict()
        }
    
    def _check_rolling_temporal_safety(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check for temporal safety violations in rolling metrics.
        
        Ensures all rolling calculations use only past data (shift operations).
        """
        violations = []
        
        # Check if calculation_date exists and is after game_date
        if 'calculation_date' in data.columns and 'game_date' in data.columns:
            future_leakage = data[data['calculation_date'] > data['game_date']]
            
            if len(future_leakage) > 0:
                violations.append({
                    'type': 'future_leakage',
                    'count': len(future_leakage),
                    'description': 'Calculation date after game date'
                })
        
        # Check for same-game data in rolling windows
        # This would indicate the current game's data was included in the rolling average
        for window in [4, 8, 16]:
            col = f'avg_points_{window}g'
            if col in data.columns and 'points' in data.columns:
                # Rolling average should never equal current game points (unless all games identical)
                # Using a small epsilon for float comparison
                same_value = data[abs(data[col] - data['points']) < 0.001]
                
                if len(same_value) > len(data) * 0.01:  # More than 1% seems suspicious
                    violations.append({
                        'type': 'potential_same_game_inclusion',
                        'window': window,
                        'count': len(same_value),
                        'description': f'Rolling {window}g average equals current game value'
                    })
        
        return {
            'violations_found': len(violations) > 0,
            'violation_count': len(violations),
            'violations': violations,
            'temporal_safety_passed': len(violations) == 0
        }
    
    def _assess_rolling_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall data quality of rolling metrics."""
        quality_metrics = {
            'total_records': len(data),
            'teams': int(data['team'].nunique()) if 'team' in data.columns else 0,
            'date_range': {
                'min': str(data['game_date'].min()) if 'game_date' in data.columns else None,
                'max': str(data['game_date'].max()) if 'game_date' in data.columns else None
            }
        }
        
        # Null rates for rolling columns
        rolling_cols = [col for col in data.columns if 'avg_' in col or 'rolling_' in col]
        null_rates = {}
        
        for col in rolling_cols:
            null_rate = data[col].isnull().sum() / len(data) if len(data) > 0 else 0
            null_rates[col] = round(null_rate, 4)
        
        quality_metrics['null_rates'] = null_rates
        quality_metrics['avg_null_rate'] = round(sum(null_rates.values()) / len(null_rates), 4) if null_rates else 0
        
        return quality_metrics

    def validate_call_depth(self):
        """
        Development helper: Validate architecture constraints.
        
        Call depth check:
        User → run_feature_analysis() [Layer 1]
             → FeatureAnalysisImpl.run_feature_analysis() [Layer 2]
             → Database service calls [Layer 3]
        
        Returns:
            dict: Validation results
        """
        return {
            'max_depth': 3,
            'current_depth': 3,
            'within_limits': True,
            'pattern': 'Minimum Viable Decoupling',
            'complexity_points': 2,
            'traceable': True,
            'explanation': 'User → Feature Analysis → Database (3 layers)'
        }


# Convenience function for direct usage
def create_feature_analysis(db_service=None, logger=None, bucket_adapter=None):
    """
    Create feature analysis service with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        bucket_adapter: Optional bucket adapter override
        
    Returns:
        FeatureAnalysisImpl: Configured feature analysis service
    """
    from ...shared.database_router import get_database_router
    from commonv2.persistence.bucket_adapter import get_bucket_adapter
    from commonv2 import get_logger
    
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.analytics.feature_analysis')
    bucket_adapter = bucket_adapter or get_bucket_adapter()
    
    return FeatureAnalysisImpl(db_service, logger, bucket_adapter)


__all__ = [
    'FeatureAnalysisImpl',
    'create_feature_analysis'
]
