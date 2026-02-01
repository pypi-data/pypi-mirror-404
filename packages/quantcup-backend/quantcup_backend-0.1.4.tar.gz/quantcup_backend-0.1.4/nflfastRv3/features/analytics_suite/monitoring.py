"""
Data Monitoring Implementation
Pattern: Minimum Viable Decoupling (MVD)

Consolidates 9 standalone monitoring scripts into a cohesive module with:
- Parallel execution for performance
- Standardized result format
- Comprehensive logging
- CLI integration
"""
from typing import TypedDict, List, Dict, Any, Optional, Literal, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np

from commonv2 import get_logger
from nflfastRv3.shared.database_router import get_database_router
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from nflfastRv3.shared.temporal_validator import TemporalValidator


class IntegrityCheckResult(TypedDict):
    """Standardized result format for all integrity checks."""
    check_name: str
    status: Literal['pass', 'fail', 'warn']
    issues: List[str]
    metrics: Dict[str, Any]
    timestamp: str
    duration_seconds: float

class DataMonitoringImpl:
    """
    Centralized data monitoring and integrity checking.
    
    Consolidates functionality from:
    - verify_dim_game_columns.py
    - verify_fact_play_columns.py
    - verify_feature_tables.py
    - verify_feature_registry.py
    - evaluate_playbyplay_data.py
    - compare_depth_chart_sources.py
    - compare_schedule_data.py
    - compare_team_data.py
    - debug_rest_days.py
    """
    
    def __init__(
        self,
        db_service: Optional[Any] = None,
        bucket_adapter: Optional[Any] = None,
        temporal_validator: Optional[TemporalValidator] = None
    ):
        """
        Initialize monitoring service with dependency injection.
        
        Args:
            db_service: Database service (default: auto-created)
            logger: Logger instance (default: auto-created)
            bucket_adapter: Bucket adapter (default: auto-created)
            temporal_validator: Temporal validator (default: auto-created)
        """
        self.logger = get_logger(__name__)
        self.db_service = db_service or get_database_router(self.logger)
        self.bucket_adapter = bucket_adapter or get_bucket_adapter(self.logger)
        self.temporal_validator = temporal_validator or TemporalValidator()
        
        self.logger.info("DataMonitoringImpl initialized")
    
    def run_monitoring_suite(
        self,
        check_type: str = 'all',
        parallel: bool = True,
        **kwargs
    ) -> Dict[str, IntegrityCheckResult]:
        """
        Orchestrator for all monitoring tasks.
        
        Args:
            check_type: Type of check to run ('all', 'warehouse', 'raw-data', 'sources', 'registry', 'debug')
            parallel: Whether to run checks in parallel (default: True)
            **kwargs: Additional arguments passed to specific checks
        
        Returns:
            Dictionary mapping check names to results
        
        Example:
            >>> monitor = DataMonitoringImpl()
            >>> results = monitor.run_monitoring_suite(check_type='warehouse')
            >>> print(results['warehouse_integrity']['status'])
            'pass'
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Starting monitoring suite: check_type={check_type}, parallel={parallel}")
        
        # Define check mapping
        checks = {
            'warehouse_integrity': lambda: self.verify_warehouse_integrity(**kwargs),
            'raw_data_quality': lambda: self.validate_raw_data(**kwargs),
            'source_comparison': lambda: self.compare_sources(**kwargs),
            'feature_registry': lambda: self.verify_feature_registry(**kwargs),
            'debug_logic': lambda: self.debug_specific_logic(**kwargs)
        }
        
        # Filter checks based on type
        if check_type != 'all':
            check_map = {
                'warehouse': ['warehouse_integrity'],
                'raw-data': ['raw_data_quality'],
                'sources': ['source_comparison'],
                'registry': ['feature_registry'],
                'debug': ['debug_logic']
            }
            selected_checks = {k: v for k, v in checks.items() if k in check_map.get(check_type, [])}
        else:
            selected_checks = checks
        
        # Execute checks
        if parallel and len(selected_checks) > 1:
            results = self._run_parallel_checks(selected_checks)
        else:
            results = self._run_sequential_checks(selected_checks)
        
        duration = time.time() - start_time
        self.logger.info(f"Monitoring suite completed in {duration:.2f}s")
        
        return results

    def verify_warehouse_integrity(
        self,
        tables: Optional[List[str]] = None,
        parallel: bool = True,
        **kwargs
    ) -> IntegrityCheckResult:
        """
        Verify warehouse table integrity.
        
        Consolidates:
        - verify_dim_game_columns.py: dim_game schema validation
        - verify_fact_play_columns.py: fact_play schema validation
        - verify_feature_tables.py: feature table validation
        
        Args:
            tables: List of tables to check (default: all warehouse tables)
            parallel: Whether to check tables in parallel
        
        Returns:
            IntegrityCheckResult with aggregated findings
        """
        import time
        start_time = time.time()
        
        self.logger.info("Starting warehouse integrity check")
        
        # Define table schemas
        table_schemas = {
            'dim_game': {
                'required_columns': [
                    'game_id', 'season', 'week', 'game_date', 'game_type',
                    'home_team', 'away_team', 'home_score', 'away_score',
                    'stadium', 'roof', 'surface'
                ],
                'key_columns': ['game_id'],
                'max_null_rate': 0.05
            },
            'fact_play': {
                'required_columns': [
                    'play_id', 'game_id', 'posteam', 'defteam', 'down', 'ydstogo',
                    'yardline_100', 'play_type', 'yards_gained', 'epa'
                ],
                'key_columns': ['play_id', 'game_id'],
                'max_null_rate': 0.10,
                'foreign_keys': {
                    'game_id': ('dim_game', 'game_id')
                }
            },
            'rolling_metrics': {
                'required_columns': [
                    'game_id', 'team', 'avg_points_4g', 'avg_points_8g', 'avg_points_16g',
                    'avg_yards_4g', 'avg_yards_8g', 'avg_yards_16g'
                ],
                'key_columns': ['game_id', 'team'],
                'max_null_rate': 0.05,
                'temporal_check': True
            },
            'contextual_features': {
                'required_columns': [
                    'game_id', 'team', 'rest_days', 'is_division_game',
                    'stadium_advantage', 'weather_severity'
                ],
                'key_columns': ['game_id', 'team'],
                'max_null_rate': 0.15,
                'temporal_check': True
            }
        }
        
        # Filter tables if specified
        if tables:
            table_schemas = {k: v for k, v in table_schemas.items() if k in tables}
        
        # Check tables
        if parallel:
            table_results = self._check_tables_parallel(table_schemas)
        else:
            table_results = self._check_tables_sequential(table_schemas)
        
        # Aggregate results
        all_issues = []
        all_metrics = {}
        overall_status = 'pass'
        
        for table_name, result in table_results.items():
            if result['status'] == 'fail':
                overall_status = 'fail'
            elif result['status'] == 'warn' and overall_status == 'pass':
                overall_status = 'warn'
            
            all_issues.extend([f"[{table_name}] {issue}" for issue in result['issues']])
            all_metrics[table_name] = result['metrics']
        
        duration = time.time() - start_time
        
        return IntegrityCheckResult(
            check_name='warehouse_integrity',
            status=overall_status,
            issues=all_issues,
            metrics=all_metrics,
            timestamp=pd.Timestamp.now().isoformat(),
            duration_seconds=duration
        )
    
    def _check_tables_parallel(self, table_schemas: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Check multiple tables in parallel using ThreadPoolExecutor.
        
        CRITICAL: Ensure db_service handles concurrent connections safely.
        If using SQLAlchemy, ensure QueuePool is configured correctly.
        """
        results = {}
        
        # Limit max_workers to avoid connection exhaustion
        with ThreadPoolExecutor(max_workers=min(len(table_schemas), 5)) as executor:
            future_to_table = {
                executor.submit(self._check_single_table, table_name, schema): table_name
                for table_name, schema in table_schemas.items()
            }
            
            for future in as_completed(future_to_table):
                table_name = future_to_table[future]
                try:
                    results[table_name] = future.result()
                except Exception as e:
                    self.logger.error(f"Error checking table {table_name}: {e}")
                    results[table_name] = {
                        'status': 'fail',
                        'issues': [f"Exception during check: {str(e)}"],
                        'metrics': {}
                    }
        
        return results
    
    def _check_tables_sequential(self, table_schemas: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Check tables sequentially."""
        results = {}
        for table_name, schema in table_schemas.items():
            try:
                results[table_name] = self._check_single_table(table_name, schema)
            except Exception as e:
                self.logger.error(f"Error checking table {table_name}: {e}")
                results[table_name] = {
                    'status': 'fail',
                    'issues': [f"Exception during check: {str(e)}"],
                    'metrics': {}
                }
        return results
    
    def _check_single_table(self, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a single table against its schema.
        
        Performs:
        1. Column presence validation
        2. Null rate checks
        3. Duplicate detection
        4. Foreign key validation (if specified)
        5. Temporal safety checks (if specified)
        """
        issues = []
        metrics = {}
        
        # Load table metadata
        try:
            # Get engine for default database
            engine = self.db_service.get_engine()
            
            # Get column info without loading full table
            column_query = f"SELECT * FROM {table_name} LIMIT 0"
            df_schema = pd.read_sql(column_query, engine)
            actual_columns = set(df_schema.columns)
            
            # Check required columns
            required_columns = set(schema['required_columns'])
            missing_columns = required_columns - actual_columns
            extra_columns = actual_columns - required_columns
            
            if missing_columns:
                issues.append(f"Missing required columns: {missing_columns}")
            
            metrics['total_columns'] = len(actual_columns)
            metrics['missing_columns'] = len(missing_columns)
            metrics['extra_columns'] = len(extra_columns)
            
            # Load sample for quality checks
            sample_query = f"SELECT * FROM {table_name} LIMIT 10000"
            df_sample = pd.read_sql(sample_query, engine)
            
            # Null rate check
            null_rates = df_sample.isnull().sum() / len(df_sample)
            high_null_cols = null_rates[null_rates > schema['max_null_rate']]
            
            if len(high_null_cols) > 0:
                issues.append(f"High null rates in columns: {high_null_cols.to_dict()}")
            
            metrics['avg_null_rate'] = null_rates.mean()
            metrics['max_null_rate'] = null_rates.max()
            
            # Duplicate check
            if 'key_columns' in schema:
                key_cols = schema['key_columns']
                duplicates = df_sample[df_sample.duplicated(subset=key_cols, keep=False)]
                
                if len(duplicates) > 0:
                    issues.append(f"Found {len(duplicates)} duplicate rows on key {key_cols}")
                
                metrics['duplicate_count'] = len(duplicates)
            
            # Foreign key check
            if 'foreign_keys' in schema:
                for fk_col, (ref_table, ref_col) in schema['foreign_keys'].items():
                    orphan_query = f"""
                        SELECT COUNT(*) as orphan_count
                        FROM {table_name} t
                        LEFT JOIN {ref_table} r ON t.{fk_col} = r.{ref_col}
                        WHERE r.{ref_col} IS NULL
                    """
                    orphan_result = pd.read_sql(orphan_query, engine)
                    orphan_count = orphan_result.iloc[0]['orphan_count']
                    
                    if orphan_count > 0:
                        issues.append(f"Found {orphan_count} orphaned records for FK {fk_col}")
                    
                    metrics[f'orphan_{fk_col}'] = orphan_count
            
            # Temporal safety check
            if schema.get('temporal_check', False):
                temporal_issues = self._check_temporal_safety(table_name, df_sample)
                issues.extend(temporal_issues)
            
            # Determine status
            if len(issues) == 0:
                status = 'pass'
            elif any('Missing required' in issue or 'orphaned' in issue for issue in issues):
                status = 'fail'
            else:
                # If we have issues but they aren't critical failures, it's a warning
                # However, if we have ANY issues, we should probably default to 'warn' unless critical
                status = 'warn'
            
            return {
                'status': status,
                'issues': issues,
                'metrics': metrics
            }
            
        except Exception as e:
            return {
                'status': 'fail',
                'issues': [f"Error checking table: {str(e)}"],
                'metrics': {}
            }
    
    def _check_temporal_safety(self, table_name: str, df: pd.DataFrame) -> List[str]:
        """Check for temporal safety violations (future leakage)."""
        issues = []
        
        # Check if calculation_date > game_date (future leakage)
        if 'calculation_date' in df.columns and 'game_date' in df.columns:
            future_leakage = df[df['calculation_date'] > df['game_date']]
            if len(future_leakage) > 0:
                issues.append(f"Temporal violation: {len(future_leakage)} rows with calculation_date > game_date")
        
        return issues

    def validate_raw_data(
        self,
        data_type: str = 'play_by_play',
        year: Optional[int] = None,
        **kwargs
    ) -> IntegrityCheckResult:
        """
        Validate raw data quality from bucket.
        
        Consolidates:
        - evaluate_playbyplay_data.py: Play-by-play data quality checks
        
        Args:
            data_type: Type of raw data to validate
            year: Specific year to validate (default: current year)
        
        Returns:
            IntegrityCheckResult with data quality findings
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Validating raw data: type={data_type}, year={year}")
        
        issues = []
        metrics = {}
        
        try:
            # Load raw data from bucket
            if year:
                data = self.bucket_adapter.read_data(data_type, filters=[('season', '==', year)])
            else:
                data = self.bucket_adapter.read_data(data_type)
            
            metrics['total_rows'] = len(data)
            metrics['total_columns'] = len(data.columns)
            
            # Define critical columns by data type
            critical_columns_map = {
                'play_by_play': [
                    'game_id', 'play_id', 'posteam', 'defteam', 'down', 'ydstogo',
                    'yardline_100', 'play_type', 'yards_gained', 'epa'
                ],
                'schedule': ['game_id', 'season', 'week', 'game_date', 'home_team', 'away_team'],
                'teams': ['team_id', 'team_abbr', 'team_name', 'conference', 'division']
            }
            
            critical_columns = critical_columns_map.get(data_type, [])
            
            # Check critical column availability
            missing_critical = [col for col in critical_columns if col not in data.columns]
            if missing_critical:
                issues.append(f"Missing critical columns: {missing_critical}")
            
            metrics['missing_critical_columns'] = len(missing_critical)
            
            # Null rate analysis
            null_rates = data.isnull().sum() / len(data)
            high_null_cols = null_rates[null_rates > 0.5]
            
            if len(high_null_cols) > 0:
                issues.append(f"High null rates (>50%) in columns: {high_null_cols.to_dict()}")
            
            metrics['avg_null_rate'] = null_rates.mean()
            metrics['high_null_column_count'] = len(high_null_cols)
            
            # Anomaly detection
            if data_type == 'play_by_play':
                # Check for impossible values
                if 'down' in data.columns:
                    invalid_downs = data[~data['down'].isin([1, 2, 3, 4, np.nan])]
                    if len(invalid_downs) > 0:
                        issues.append(f"Found {len(invalid_downs)} plays with invalid down values")
                
                if 'yardline_100' in data.columns:
                    invalid_yardline = data[(data['yardline_100'] < 0) | (data['yardline_100'] > 100)]
                    if len(invalid_yardline) > 0:
                        issues.append(f"Found {len(invalid_yardline)} plays with invalid yardline values")
                
                metrics['invalid_down_count'] = len(invalid_downs) if 'down' in data.columns else 0
                metrics['invalid_yardline_count'] = len(invalid_yardline) if 'yardline_100' in data.columns else 0
            
            # Aggregation feasibility check
            if 'game_id' in data.columns:
                games_with_data = data['game_id'].nunique()
                metrics['unique_games'] = games_with_data
                
                # Check if we have enough data for aggregation
                if games_with_data == 0:
                    issues.append(f"No games found in data")
            
            # Determine status
            if len(issues) == 0:
                status = 'pass'
            elif any('Missing critical' in issue for issue in issues):
                status = 'fail'
            else:
                # If we have issues but they aren't critical failures, it's a warning
                # However, if we have ANY issues, we should probably default to 'warn' unless critical
                status = 'warn'
            
        except Exception as e:
            self.logger.error(f"Error validating raw data: {e}")
            status = 'fail'
            issues = [f"Exception during validation: {str(e)}"]
            metrics = {}
        
        duration = time.time() - start_time
        
        return IntegrityCheckResult(
            check_name='raw_data_quality',
            status=status,
            issues=issues,
            metrics=metrics,
            timestamp=pd.Timestamp.now().isoformat(),
            duration_seconds=duration
        )

    def compare_sources(
        self,
        source_type: str = 'all',
        comparison_pairs: Optional[List[tuple]] = None,
        **kwargs
    ) -> IntegrityCheckResult:
        """
        Compare data across different sources.
        
        Consolidates:
        - compare_depth_chart_sources.py: Depth chart API vs Bucket
        - compare_schedule_data.py: Schedule data comparison
        - compare_team_data.py: Team metadata comparison
        
        Args:
            source_type: Type of data to compare ('depth-charts', 'schedule', 'teams', 'all')
            comparison_pairs: Custom comparison pairs [(source1, source2), ...]
        
        Returns:
            IntegrityCheckResult with comparison findings
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Comparing sources: type={source_type}")
        
        issues = []
        metrics = {}
        
        # Define comparison configurations
        comparisons = {
            'depth-charts': {
                'source1': ('database', "SELECT * FROM depth_charts WHERE source = 'api'"),
                'source2': ('bucket', 'depth_charts'),
                'join_keys': ['player_id', 'team', 'position'],
                'compare_columns': ['depth_position', 'status']
            },
            'schedule': {
                'source1': ('database', "SELECT * FROM dim_game"),
                'source2': ('bucket', 'schedule'),
                'join_keys': ['game_id'],
                'compare_columns': ['game_date', 'home_team', 'away_team', 'week']
            },
            'teams': {
                'source1': ('database', "SELECT * FROM dim_team"),
                'source2': ('bucket', 'teams'),
                'join_keys': ['team_id'],
                'compare_columns': ['team_abbr', 'team_name', 'conference', 'division']
            }
        }
        
        # Filter comparisons based on type
        if source_type != 'all':
            comparisons = {k: v for k, v in comparisons.items() if k == source_type}
        
        # Perform comparisons
        for comp_name, config in comparisons.items():
            try:
                comp_result = self._compare_two_sources(comp_name, config)
                issues.extend([f"[{comp_name}] {issue}" for issue in comp_result['issues']])
                metrics[comp_name] = comp_result['metrics']
            except Exception as e:
                self.logger.error(f"Error comparing {comp_name}: {e}")
                issues.append(f"[{comp_name}] Exception during comparison: {str(e)}")
        
        # Determine status
        if len(issues) == 0:
            status = 'pass'
        elif any('Schema mismatch' in issue or 'Data mismatch' in issue for issue in issues):
            status = 'warn'
        else:
            # If we have issues but they aren't critical failures, it's a warning
            status = 'warn'
        
        duration = time.time() - start_time
        
        return IntegrityCheckResult(
            check_name='source_comparison',
            status=status,
            issues=issues,
            metrics=metrics,
            timestamp=pd.Timestamp.now().isoformat(),
            duration_seconds=duration
        )
    
    def _compare_two_sources(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Compare data from two sources."""
        issues = []
        metrics = {}
        
        # Load data from both sources
        source1_type, source1_query = config['source1']
        source2_type, source2_data = config['source2']
        
        if source1_type == 'database':
            df1 = pd.read_sql(source1_query, self.db_service.get_engine())
        else:
            df1 = self.bucket_adapter.read_data(source1_query)
        
        if source2_type == 'database':
            df2 = pd.read_sql(source2_data, self.db_service.get_engine())
        else:
            df2 = self.bucket_adapter.read_data(source2_data)
        
        metrics['source1_rows'] = len(df1)
        metrics['source2_rows'] = len(df2)
        
        # Schema comparison
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)
        
        schema_diff = {
            'source1_only': list(cols1 - cols2),
            'source2_only': list(cols2 - cols1),
            'common': list(cols1 & cols2)
        }
        
        if schema_diff['source1_only'] or schema_diff['source2_only']:
            issues.append(f"Schema mismatch: {schema_diff}")
        
        metrics['schema_diff'] = schema_diff
        
        # Data comparison on common columns
        join_keys = config['join_keys']
        compare_cols = config['compare_columns']
        
        # Merge datasets
        merged = df1.merge(
            df2,
            on=join_keys,
            how='outer',
            suffixes=('_src1', '_src2'),
            indicator=True
        )
        
        # Check for records only in one source
        only_src1 = merged[merged['_merge'] == 'left_only']
        only_src2 = merged[merged['_merge'] == 'right_only']
        
        if len(only_src1) > 0:
            issues.append(f"Found {len(only_src1)} records only in source1")
        if len(only_src2) > 0:
            issues.append(f"Found {len(only_src2)} records only in source2")
        
        metrics['only_source1'] = len(only_src1)
        metrics['only_source2'] = len(only_src2)
        metrics['common_records'] = len(merged[merged['_merge'] == 'both'])
        
        # Compare values in common records
        both = merged[merged['_merge'] == 'both']
        mismatches = {}
        
        for col in compare_cols:
            if f'{col}_src1' in both.columns and f'{col}_src2' in both.columns:
                mismatch = both[both[f'{col}_src1'] != both[f'{col}_src2']]
                if len(mismatch) > 0:
                    mismatches[col] = len(mismatch)
                    issues.append(f"Data mismatch in column '{col}': {len(mismatch)} records differ")
        
        metrics['column_mismatches'] = mismatches
        
        return {
            'issues': issues,
            'metrics': metrics
        }

    def verify_feature_registry(self, **kwargs) -> IntegrityCheckResult:
        """
        Verify FeatureRegistry integrity.
        
        Consolidates:
        - verify_feature_registry.py: Registry integrity checks
        
        Returns:
            IntegrityCheckResult with registry validation findings
        """
        import time
        start_time = time.time()
        
        self.logger.info("Verifying feature registry")
        
        issues = []
        metrics = {}
        
        try:
            from nflfastRv3.features.ml_pipeline.utils.feature_registry import FeatureRegistry
            from nflfastRv3.features.ml_pipeline.utils.feature_patterns import FeaturePatterns
            from nflfastRv3.features.ml_pipeline.utils.feature_splitter import FeatureSplitter
            
            # Get active features
            active_features = FeatureRegistry.get_active_features()
            metrics['total_active_features'] = len(active_features)
            
            # Check model integration
            # Verify that all active features match at least one pattern used by the models
            # We use Game Outcome patterns as the baseline since it's the primary model
            
            game_outcome_patterns = (
                FeaturePatterns.GAME_OUTCOME_LINEAR +
                FeaturePatterns.GAME_OUTCOME_TREE
            )
            
            # Check which features match patterns
            matched_features = FeatureSplitter.filter_by_patterns(
                active_features,
                game_outcome_patterns
            )
            
            unmatched_features = set(active_features) - set(matched_features)
            
            if unmatched_features:
                issues.append(f"Active features not matching explicit Game Outcome patterns: {unmatched_features}")
            
            metrics['matched_features'] = len(matched_features)
            metrics['unmatched_features'] = len(unmatched_features)
            
            # Determine status
            if len(issues) == 0:
                status = 'pass'
            else:
                # Unmatched features are a warning, not a failure (fallback handles them)
                status = 'warn'
            
        except Exception as e:
            self.logger.error(f"Error verifying feature registry: {e}")
            status = 'fail'
            issues = [f"Exception during verification: {str(e)}"]
            metrics = {}
        
        duration = time.time() - start_time
        
        return IntegrityCheckResult(
            check_name='feature_registry',
            status=status,
            issues=issues,
            metrics=metrics,
            timestamp=pd.Timestamp.now().isoformat(),
            duration_seconds=duration
        )

    def debug_specific_logic(
        self,
        logic_type: str = 'rest_days',
        **kwargs
    ) -> IntegrityCheckResult:
        """
        Debug specific feature calculation logic.
        
        Consolidates:
        - debug_rest_days.py: Rest days feature debugging
        
        Args:
            logic_type: Type of logic to debug ('rest_days', etc.)
        
        Returns:
            IntegrityCheckResult with debugging findings
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Debugging specific logic: {logic_type}")
        
        if logic_type == 'rest_days':
            result = self._debug_rest_days()
        else:
            result = {
                'status': 'fail',
                'issues': [f"Unknown logic type: {logic_type}"],
                'metrics': {}
            }
        
        duration = time.time() - start_time
        result['timestamp'] = pd.Timestamp.now().isoformat()
        result['duration_seconds'] = duration
        
        return IntegrityCheckResult(**result)
    
    def _debug_rest_days(self) -> Dict[str, Any]:
        """Debug rest days feature calculation."""
        issues = []
        metrics = {}
        
        try:
            # Load rest days data
            query = """
                SELECT 
                    game_id,
                    team,
                    game_date,
                    prev_game_date,
                    rest_days,
                    season
                FROM contextual_features
                WHERE rest_days IS NOT NULL
                ORDER BY team, game_date
            """
            data = pd.read_sql(query, self.db_service.get_engine())
            
            metrics['total_records'] = len(data)
            
            # Check for cross-season contamination
            data['season_change'] = data.groupby('team')['season'].diff() != 0
            season_boundaries = data[data['season_change'] == True]
            
            # Rest days at season boundaries should be large (>180 days typically)
            contaminated = season_boundaries[season_boundaries['rest_days'] < 180]
            
            if len(contaminated) > 0:
                issues.append(f"Cross-season contamination detected: {len(contaminated)} records with rest_days < 180 at season boundary")
                metrics['contaminated_records'] = len(contaminated)
            else:
                metrics['contaminated_records'] = 0
            
            # Validate rest days calculation
            data['calculated_rest_days'] = (
                pd.to_datetime(data['game_date']) - pd.to_datetime(data['prev_game_date'])
            ).dt.days
            
            data['rest_days_diff'] = abs(data['rest_days'] - data['calculated_rest_days'])
            incorrect = data[data['rest_days_diff'] > 1]  # Allow 1 day tolerance
            
            if len(incorrect) > 0:
                issues.append(f"Incorrect rest days calculation: {len(incorrect)} records")
                metrics['incorrect_calculations'] = len(incorrect)
            else:
                metrics['incorrect_calculations'] = 0
            
            # Check for impossible values
            impossible = data[(data['rest_days'] < 3) | (data['rest_days'] > 365)]
            if len(impossible) > 0:
                issues.append(f"Impossible rest days values: {len(impossible)} records")
                metrics['impossible_values'] = len(impossible)
            else:
                metrics['impossible_values'] = 0
            
            # Determine status
            if len(issues) == 0:
                status = 'pass'
            elif metrics.get('contaminated_records', 0) > 0 or metrics.get('incorrect_calculations', 0) > 10:
                status = 'fail'
            else:
                status = 'warn'
            
        except Exception as e:
            self.logger.error(f"Error debugging rest days: {e}")
            status = 'fail'
            issues = [f"Exception during debugging: {str(e)}"]
            metrics = {}
        
        return {
            'check_name': 'debug_rest_days',
            'status': status,
            'issues': issues,
            'metrics': metrics
        }
    
    def _run_parallel_checks(self, checks: Dict[str, Any]) -> Dict[str, IntegrityCheckResult]:
        """Run checks in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(len(checks), 4)) as executor:
            future_to_check = {
                executor.submit(check_func): check_name
                for check_name, check_func in checks.items()
            }
            
            for future in as_completed(future_to_check):
                check_name = future_to_check[future]
                try:
                    results[check_name] = future.result()
                except Exception as e:
                    self.logger.error(f"Error in check {check_name}: {e}")
                    results[check_name] = IntegrityCheckResult(
                        check_name=check_name,
                        status='fail',
                        issues=[f"Exception: {str(e)}"],
                        metrics={},
                        timestamp=pd.Timestamp.now().isoformat(),
                        duration_seconds=0.0
                    )
        
        return results
    
    def _run_sequential_checks(self, checks: Dict[str, Any]) -> Dict[str, IntegrityCheckResult]:
        """Run checks sequentially."""
        results = {}
        for check_name, check_func in checks.items():
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.logger.error(f"Error in check {check_name}: {e}")
                results[check_name] = IntegrityCheckResult(
                    check_name=check_name,
                    status='fail',
                    issues=[f"Exception: {str(e)}"],
                    metrics={},
                    timestamp=pd.Timestamp.now().isoformat(),
                    duration_seconds=0.0
                )
        return results