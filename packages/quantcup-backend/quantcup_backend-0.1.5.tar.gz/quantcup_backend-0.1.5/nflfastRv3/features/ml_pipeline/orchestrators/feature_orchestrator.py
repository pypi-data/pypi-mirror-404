"""
Feature Engineering Implementation for nflfastRv3

Migrates proven FeatureEngineer business logic from nflfastRv2 into clean architecture.
Following REFACTORING_SPECS.md: Maximum 5 complexity points, 3 layers depth.

Pattern: Minimum Viable Decoupling (2 complexity points)
Layer: 2 (Implementation - calls infrastructure directly)

Integrates with sophisticated V2 feature sets:
- TeamEfficiencyFeatures: EPA calculations, red zone metrics, rankings
- RollingMetricsFeatures: Time-series analysis, momentum indicators  
- OpponentAdjustedFeatures: Strength-of-schedule adjustments
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import gc
from commonv2 import get_logger
from commonv2.utils.memory.manager import create_memory_manager
from ....shared.database_router import get_database_router
from ..feature_sets import (
    create_team_efficiency_features,
    create_rolling_metrics_features,
    create_opponent_adjusted_features,
    create_nextgen_features,
    create_contextual_features,
    create_injury_features,
    create_player_availability_features,
    create_odds_features,
    create_odds_game_features,
    create_weather_features
)


class FeatureEngineerImplementation:
    """
    Core feature engineering business logic.
    
    Pattern: Minimum Viable Decoupling (2 complexity points)
    Complexity: 2 points (DI + business logic)
    Depth: 1 layer (calls infrastructure directly)
    
    Migrated from nflfastRv2.FeatureEngineer with architectural simplification.
    """
    
    def __init__(self, db_service, logger):
        """
        Initialize with injected dependencies.
        
        Args:
            db_service: Database service (Layer 3)
            logger: Logger instance (Layer 3)
        """
        self.db_service = db_service
        self.logger = logger
    
    def build_features(self, feature_sets=None, seasons=None):
        """
        Execute feature engineering workflow.
        
        Simple feature building flow (migrated from V2):
        1. Validate inputs (inline)
        2. Build features in dependency order (Layer 3 calls)
        3. Return summary
        
        Args:
            feature_sets: Feature sets to build (list of names, or None for all)
            seasons: Seasons to build features for (list of ints, or None for all available seasons)
            
        Returns:
            dict: Feature building summary
        """
        from ..feature_sets import get_available_feature_sets, validate_feature_sets
        
        # Default to all available feature sets if not specified
        if feature_sets is None:
            feature_sets = get_available_feature_sets()
        
        # seasons=None means build for all available seasons in warehouse (let feature sets handle filtering)
        
        self.logger.info(f"Starting feature engineering: sets={feature_sets}, seasons={seasons or 'all available'}")
        
        try:
            # Validate feature sets using registry
            valid_sets, invalid_sets = validate_feature_sets(feature_sets)
            
            if invalid_sets:
                available = get_available_feature_sets()
                return {
                    'status': 'error',
                    'message': f"Invalid feature sets: {invalid_sets}. Available: {available}",
                    'features_built': 0
                }
            
            # Use validated sets
            feature_sets = valid_sets
            
            # Build features in dependency order with memory management
            # Maintain order: baseline features first, then contextual, then injury
            all_sets = get_available_feature_sets()
            build_order = [fs for fs in all_sets if fs in feature_sets]
            
            results = {}
            total_rows = 0
            
            # Initialize memory manager for tracking between feature sets
            memory_mgr = create_memory_manager(logger=self.logger)
            self.logger.info("🔍 Memory manager initialized for feature engineering")
            memory_mgr.log_status()
            
            for feature_set in build_order:
                if feature_set not in feature_sets:
                    continue
                
                self.logger.info(f"Building feature set: {feature_set}")
                memory_mgr.log_status()
                
                try:
                    build_result = self._build_feature_set(feature_set, seasons)
                    results[feature_set] = {
                        'status': 'success',
                        'rows_built': build_result['rows_built'],
                        'statistics': build_result.get('statistics', {})
                    }
                    total_rows += build_result['rows_built']
                    self.logger.info(f"✓ {feature_set}: {build_result['rows_built']:,} rows built")
                    
                    # Force garbage collection between feature sets to prevent memory accumulation
                    self.logger.debug(f"🧹 Running garbage collection after {feature_set}")
                    gc.collect()
                    memory_mgr.log_status()
                    
                except Exception as e:
                    self.logger.error(f"Failed to build {feature_set}: {e}")
                    results[feature_set] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    # Still run garbage collection even on failure
                    gc.collect()
                    continue
            
            successful = sum(1 for r in results.values() if r['status'] == 'success')
            total = len(results)
            
            self.logger.info(f"Feature engineering complete: {successful}/{total} feature sets built")
            
            # Generate feature report
            from ..reporting.orchestrator import ReportOrchestrator
            
            status = 'success' if successful == total else 'partial'
            report_result = {
                'status': status,
                'features_built': successful,
                'total_features': total,
                'total_rows': total_rows,
                'results': results
            }
            
            try:
                report_path = ReportOrchestrator.generate_feature_report(
                    results=report_result,
                    logger=self.logger
                )
                if report_path:
                    self.logger.info(f"📊 Feature report generated: {report_path}")
            except Exception as e:
                self.logger.warning(f"Failed to generate feature report: {e}")
            
            return report_result
            
        except Exception as e:
            self.logger.error(f"Feature engineering failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'features_built': 0,
                'total_rows': 0
            }
        
    def validate_feature_data(self, feature_set_name):
        """
        Validate that a feature set has been built and contains data.
        
        Args:
            feature_set_name: Name of the feature set to validate
            
        Returns:
            bool: True if feature set is valid
        """
        valid_sets = {
            'team_efficiency': 'features.team_efficiency_v1',
            'rolling_metrics': 'features.rolling_metrics_v1',
            'opponent_adjusted': 'features.team_opponent_adjusted_v1',
            'contextual': 'features.contextual_features_v1',
            'injury': 'features.injury_features_v1'
        }
        
        if feature_set_name not in valid_sets:
            self.logger.error(f"Unknown feature set: {feature_set_name}")
            return False
        
        table_name = valid_sets[feature_set_name]
        
        try:
            # Layer 3 call - direct database query
            engine = self.db_service.get_engine()
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            with engine.connect() as conn:
                result = conn.execute(query).fetchone()
                row_count = result[0] if result else 0
            
            if row_count == 0:
                self.logger.warning(f"Feature set {feature_set_name} has no data")
                return False
            
            self.logger.info(f"✓ Feature set {feature_set_name} validated: {row_count:,} rows")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate {feature_set_name}: {e}")
            return False
    
    def _build_feature_set(self, feature_set_name, seasons):
        """
        Build, analyze, and save a specific feature set.

        Following model_trainer.py pattern: orchestrator handles building, analysis, AND saving.
        This creates architectural consistency across the ML pipeline.

        Pattern matches model_trainer._save_model() approach:
        1. Build the thing (features/model)
        2. Analyze the thing (extract statistics for reporting)
        3. Save the thing (if requested)

        Args:
            feature_set_name: Name of feature set to build
            seasons: Seasons to build for

        Returns:
            dict: Results including rows_built and comprehensive statistics
        """
        # Step 1: Build features (feature set returns DataFrame - no saving)
        if feature_set_name == 'team_efficiency':
            service = create_team_efficiency_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'team_efficiency_v1'
        elif feature_set_name == 'rolling_metrics':
            service = create_rolling_metrics_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'rolling_metrics_v1'
        elif feature_set_name == 'opponent_adjusted':
            service = create_opponent_adjusted_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'team_opponent_adjusted_v1'
        elif feature_set_name == 'nextgen':
            service = create_nextgen_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'nextgen_features_v1'
        elif feature_set_name == 'contextual':
            service = create_contextual_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'contextual_features_v1'
        elif feature_set_name == 'injury':
            service = create_injury_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'injury_features_v1'
        elif feature_set_name == 'player_availability':
            service = create_player_availability_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'player_availability_v1'
        elif feature_set_name == 'odds':
            service = create_odds_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'odds_features_v1'
        elif feature_set_name == 'odds_game':
            service = create_odds_game_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'odds_features_game_v1'
        elif feature_set_name == 'weather':
            service = create_weather_features(self.db_service, self.logger)
            result = service.build_features(seasons=seasons)
            table_name = 'weather_features_v1'
        else:
            raise ValueError(f"Unknown feature set: {feature_set_name}")

        if result['status'] != 'success':
            raise RuntimeError(f"{feature_set_name} build failed: {result.get('message', 'Unknown error')}")

        # Step 2: Extract comprehensive statistics for reporting
        df = result.get('dataframe')
        if df is None or df.empty:
            raise RuntimeError(f"{feature_set_name} returned empty DataFrame")

        self.logger.info(f"📊 Analyzing {feature_set_name} features for reporting...")
        statistics = self._analyze_feature_dataframe(df, feature_set_name)
        self.logger.info(f"✓ Extracted {len(statistics.get('columns', {}))} column stats and {len(statistics.get('correlations', {}).get('strong_positive', {}))} correlations")

        # Step 3: Orchestrator handles saving (like model_trainer does)
        self.logger.info(f"💾 Orchestrator saving {feature_set_name} features...")
        save_result = self._save_features(df=df, table_name=table_name)

        if not save_result['success']:
            raise RuntimeError(f"Failed to save {feature_set_name}: {save_result.get('error')}")

        self.logger.info(f"✓ Orchestrator saved {len(df):,} rows to {table_name}")

        # Return both rows count and comprehensive statistics
        return {
            'rows_built': result['features_built'],
            'statistics': statistics
        }
    
    def _save_features(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Save features using bucket-first architecture with database routing.
        
        Matches model_trainer._save_model() pattern.
        
        Production: Bucket (primary) + Database (backup)
        Local: Database only (primary)
        
        Args:
            df: DataFrame to save
            table_name: Target table name
            
        Returns:
            Dictionary with save results
        """
        from commonv2.persistence.bucket_adapter import get_bucket_adapter
        from nflfastRv3.shared.database_router import DatabaseRouter
        from commonv2.core.config import DatabasePrefixes, FeatureConfig, SchemaNames
        
        if df.empty:
            raise ValueError(f"Cannot save empty DataFrame for {table_name}")
        
        try:
            # Get unique keys for this table
            unique_keys = self._get_feature_unique_keys(table_name)
            
            # Create config for feature routing
            config = FeatureConfig(
                table=table_name,
                schema=SchemaNames.FEATURES,
                unique_keys=unique_keys,
                databases=[DatabasePrefixes.LOCAL_DEV, DatabasePrefixes.API_PRODUCTION],
                bucket=True
            )
            
            # Step 1: Store in bucket FIRST (primary storage)
            bucket_adapter = get_bucket_adapter(logger=self.logger)
            bucket_success = bucket_adapter.store_data(df, table_name, 'features')
            
            if not bucket_success:
                raise RuntimeError(f"Bucket write failed for {table_name}")
            
            self.logger.info(f"💾 Bucket (primary): {len(df):,} rows → features/{table_name}")
            
            # Step 2: Route to databases (secondary storage)
            database_router = DatabaseRouter(logger=self.logger)
            database_success = database_router.route_to_databases(df, config)
            
            if not database_success:
                # Critical alert: Database routing failed
                self.logger.error(f"🚨 ALERT: Database routing failed for {table_name}")
                self.logger.error(f"   → Data safely stored in bucket: features/{table_name}")
                self.logger.error(f"   → Manual sync may be required from bucket to database")
                self.logger.error(f"   → Use: scripts/sync_bucket_to_database.py {table_name}")
                
                # Return partial success status
                return {
                    'success': True,  # Keep True since data is in bucket
                    'table_name': table_name,
                    'rows_saved': len(df),
                    'bucket_success': True,
                    'database_success': False,
                    'warning': 'Database sync failed - data in bucket only'
                }
            
            return {
                'success': True,
                'table_name': table_name,
                'rows_saved': len(df),
                'bucket_success': True,
                'database_success': True
            }
            
        except Exception as e:
            self.logger.error(f"❌ Write failed for {table_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_feature_unique_keys(self, table_name: str) -> List[str]:
        """
        Get unique keys for standard feature tables.
        
        Args:
            table_name: Name of the feature table
            
        Returns:
            List of column names that form the unique key
        """
        key_map = {
            # V1 tables (season-level - DEPRECATED due to temporal leakage)
            'team_efficiency_v1': ['team', 'season'],
            'team_opponent_adjusted_v1': ['team', 'season'],
            
            # V2 tables (game-level - CORRECT temporal separation)
            'team_efficiency_v2': ['game_id', 'team'],
            'team_opponent_adjusted_v2': ['game_id', 'team'],
            
            # Rolling metrics (already game-level)
            'rolling_metrics_v1': ['game_id', 'team'],
            'opponent_adjusted_v1': ['game_id', 'team'],
            
            # NextGen QB features (game-level)
            'nextgen_features_v1': ['game_id'],
            
            # Contextual features (game-level)
            'contextual_features_v1': ['game_id'],
            
            # Injury features (game-level)
            'injury_features_v1': ['game_id'],
            
            # Player availability features (game-level)
            'player_availability_v1': ['game_id'],
            
            # Odds features (play-level)
            'odds_features_v1': ['game_id'],  # Note: Actually play-level but keyed by game_id
            
            # Odds game features (game-level)
            'odds_features_game_v1': ['game_id'],
            
            # Weather features (game-level)
            'weather_features_v1': ['game_id'],
        }
        return key_map.get(table_name, ['game_id', 'team'])  # Default to game-level

    def _analyze_feature_dataframe(self, df: pd.DataFrame, feature_set_name: str) -> Dict[str, Any]:
        """
        Extract comprehensive statistics from feature DataFrame for reporting.

        Analyzes data quality, correlations, variance, and predictive power metrics
        that are essential for ML model development and feature engineering validation.

        Args:
            df: Feature DataFrame to analyze
            feature_set_name: Name of the feature set for context

        Returns:
            Dictionary containing all extracted statistics
        """
        import numpy as np

        if df.empty:
            return {'error': 'Empty DataFrame'}

        stats = {
            'feature_set': feature_set_name,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': {},
            'correlations': {},
            'variance_analysis': {},
            'data_quality': {},
            'temporal_stability': {},
            'predictive_power': {}
        }

        # 1. COLUMN INVENTORY - Data types, nulls, ranges
        for col in df.columns:
            col_stats = {
                'dtype': str(df[col].dtype),
                'null_count': df[col].isnull().sum(),
                'null_percentage': (df[col].isnull().sum() / len(df)) * 100,
                'unique_values': df[col].nunique(),
                'min': None,
                'max': None,
                'mean': None,
                'std': None
            }

            # Numeric columns get range and distribution stats
            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats.update({
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'variance': df[col].var()
                })
            # Categorical columns get value counts
            elif df[col].dtype == 'object' or isinstance(df[col].dtype, pd.CategoricalDtype):
                value_counts = df[col].value_counts().head(10).to_dict()
                col_stats['top_values'] = value_counts

            stats['columns'][col] = col_stats

        # 2. CORRELATION ANALYSIS - If target variable exists
        target_candidates = ['home_won', 'result', 'home_win', 'win']
        target_col = None
        for candidate in target_candidates:
            if candidate in df.columns:
                target_col = candidate
                break

        if target_col:
            # Calculate correlations with target
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            correlations = df[numeric_cols].corrwith(df[target_col]).sort_values(ascending=False)

            stats['correlations'] = {
                'target_column': target_col,
                'strong_positive': correlations[correlations > 0.15].head(10).to_dict(),
                'moderate_positive': correlations[(correlations > 0.08) & (correlations <= 0.15)].head(10).to_dict(),
                'weak_positive': correlations[(correlations > 0.05) & (correlations <= 0.08)].head(10).to_dict(),
                'weak_negative': correlations[(correlations > -0.08) & (correlations <= -0.05)].head(10).to_dict(),
                'moderate_negative': correlations[(correlations > -0.15) & (correlations <= -0.08)].head(10).to_dict(),
                'strong_negative': correlations[correlations <= -0.15].head(10).to_dict()
            }

        # 3. WIN/LOSS STRATIFICATION - If target exists
        if target_col:
            wins_df = df[df[target_col] == 1]
            losses_df = df[df[target_col] == 0]

            stratification = {}
            numeric_cols = df.select_dtypes(include=[np.number]).columns

            for col in numeric_cols:
                if col == target_col:
                    continue
                win_mean = wins_df[col].mean()
                loss_mean = losses_df[col].mean()
                diff = win_mean - loss_mean
                stratification[col] = {
                    'wins_mean': win_mean,
                    'losses_mean': loss_mean,
                    'difference': diff,
                    'abs_difference': abs(diff)
                }

            # Sort by absolute difference
            sorted_strat = dict(sorted(stratification.items(),
                                     key=lambda x: x[1]['abs_difference'],
                                     reverse=True))
            stats['predictive_power']['stratification'] = dict(list(sorted_strat.items())[:20])

        # 4. VARIANCE ANALYSIS
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            variances = df[numeric_cols].var().sort_values(ascending=False)
            stats['variance_analysis'] = {
                'highest_variance': variances.head(10).to_dict(),
                'lowest_variance': variances.tail(10).to_dict(),
                'zero_variance': variances[variances == 0].index.tolist()
            }

        # 5. TEMPORAL STABILITY - If season column exists
        if 'season' in df.columns and len(df['season'].unique()) > 1:
            season_stats = {}
            numeric_cols = df.select_dtypes(include=[np.number]).columns

            for col in numeric_cols:
                season_means = df.groupby('season')[col].mean()
                if len(season_means) > 1:
                    # Coefficient of variation as stability metric
                    mean_of_means = season_means.mean()
                    std_of_means = season_means.std()
                    cv = (std_of_means / abs(mean_of_means)) * 100 if mean_of_means != 0 else float('inf')

                    stability = "STABLE" if cv < 20 else "MODERATE" if cv < 50 else "UNSTABLE"
                    season_stats[col] = {
                        'cv_percentage': cv,
                        'stability': stability,
                        'season_means': season_means.to_dict()
                    }

            # Sort by stability (lowest CV first)
            sorted_stability = dict(sorted(season_stats.items(),
                                         key=lambda x: x[1]['cv_percentage']))
            stats['temporal_stability'] = dict(list(sorted_stability.items())[:15])

        # 6. DATA QUALITY SUMMARY
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        completeness = ((total_cells - null_cells) / total_cells) * 100

        stats['data_quality'] = {
            'total_cells': total_cells,
            'null_cells': null_cells,
            'completeness_percentage': completeness,
            'columns_with_nulls': (df.isnull().sum() > 0).sum(),
            'duplicate_rows': df.duplicated().sum()
        }

        # 7. FEATURE ENGINEERING VALIDATION
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0 and target_col:
            correlations = df[numeric_cols].corrwith(df[target_col])

            # Quality tiers
            strong_corr = sum(abs(correlations) > 0.15)
            moderate_corr = sum((abs(correlations) > 0.08) & (abs(correlations) <= 0.15))
            weak_corr = sum((abs(correlations) > 0.05) & (abs(correlations) <= 0.08))
            very_weak_corr = sum(abs(correlations) <= 0.05)

            stats['predictive_power']['quality_tiers'] = {
                'strong_predictive': strong_corr,
                'moderate_predictive': moderate_corr,
                'weak_predictive': weak_corr,
                'very_weak_predictive': very_weak_corr,
                'total_features_analyzed': len(numeric_cols),
                'useful_features_percentage': ((strong_corr + moderate_corr) / len(numeric_cols)) * 100 if len(numeric_cols) > 0 else 0
            }

        return stats


def create_feature_engineer(db_service=None, logger=None):
    """
    Create feature engineer with default dependencies.
    
    Args:
        db_service: Optional database service override
        logger: Optional logger override
        
    Returns:
        FeatureEngineerImplementation: Configured feature engineer
    """
    db_service = db_service or get_database_router()
    logger = logger or get_logger('nflfastRv3.feature_engineer')
    
    return FeatureEngineerImplementation(db_service, logger)


__all__ = ['FeatureEngineerImplementation', 'create_feature_engineer']
