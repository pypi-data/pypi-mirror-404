import pytest
from unittest.mock import Mock, patch
import pandas as pd
from nflfastRv3.features.analytics_suite.monitoring import DataMonitoringImpl, IntegrityCheckResult


class TestDataMonitoringImpl:
    """Unit tests for DataMonitoringImpl."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        return {
            'db_service': Mock(),
            'logger': Mock(),
            'bucket_adapter': Mock(),
            'temporal_validator': Mock()
        }
    
    @pytest.fixture
    def monitor(self, mock_dependencies):
        """Create DataMonitoringImpl instance with mocks."""
        return DataMonitoringImpl(**mock_dependencies)
    
    def test_verify_warehouse_integrity_pass(self, monitor, mock_dependencies):
        """Test warehouse integrity check with passing data."""
        # Mock database response
        # We need to mock pd.read_sql since we switched to using it directly
        with patch('pandas.read_sql') as mock_read_sql:
            mock_read_sql.return_value = pd.DataFrame({
                'game_id': [1, 2, 3],
                'season': [2024, 2024, 2024],
                'week': [1, 1, 2],
                'game_date': ['2024-09-08', '2024-09-08', '2024-09-15'],
                'home_team': ['KC', 'BAL', 'SF'],
                'away_team': ['BAL', 'KC', 'MIN'],
                'game_type': ['REG', 'REG', 'REG'],
                'home_score': [20, 27, 30],
                'away_score': [17, 20, 10],
                'stadium': ['Arrowhead', 'M&T Bank', 'Levi'],
                'roof': ['outdoors', 'outdoors', 'outdoors'],
                'surface': ['grass', 'grass', 'grass']
            })
            
            result = monitor.verify_warehouse_integrity(tables=['dim_game'], parallel=False)
            
            assert result['status'] == 'pass'
            assert len(result['issues']) == 0
            assert 'dim_game' in result['metrics']
    
    def test_verify_warehouse_integrity_missing_columns(self, monitor, mock_dependencies):
        """Test warehouse integrity check with missing columns."""
        # Mock database response with missing columns
        with patch('pandas.read_sql') as mock_read_sql:
            mock_read_sql.return_value = pd.DataFrame({
                'game_id': [1, 2, 3],
                'season': [2024, 2024, 2024]
                # Missing required columns
            })
            
            result = monitor.verify_warehouse_integrity(tables=['dim_game'], parallel=False)
            
            assert result['status'] == 'fail'
            assert any('Missing required columns' in issue for issue in result['issues'])
    
    def test_validate_raw_data_pass(self, monitor, mock_dependencies):
        """Test raw data validation with good data."""
        # Mock bucket response
        mock_dependencies['bucket_adapter'].read_data.return_value = pd.DataFrame({
            'game_id': [1, 2, 3],
            'play_id': [1, 2, 3],
            'posteam': ['KC', 'BAL', 'SF'],
            'defteam': ['BAL', 'KC', 'MIN'],
            'down': [1, 2, 3],
            'ydstogo': [10, 7, 5],
            'yardline_100': [75, 50, 25],
            'play_type': ['pass', 'run', 'pass'],
            'yards_gained': [15, 3, 8],
            'epa': [0.5, -0.2, 0.3]
        })
        
        result = monitor.validate_raw_data(data_type='play_by_play', year=2024)
        
        assert result['status'] == 'pass'
        assert result['metrics']['total_rows'] == 3
    
    def test_compare_sources_schema_mismatch(self, monitor, mock_dependencies):
        """Test source comparison with schema mismatch."""
        # Mock different schemas
        mock_dependencies['db_service'].query.return_value = pd.DataFrame({
            'team_id': [1, 2],
            'team_abbr': ['KC', 'BAL'],
            'team_name': ['Chiefs', 'Ravens']
        })
        
        mock_dependencies['bucket_adapter'].read_data.return_value = pd.DataFrame({
            'team_id': [1, 2],
            'team_abbr': ['KC', 'BAL'],
            'full_name': ['Kansas City Chiefs', 'Baltimore Ravens']  # Different column name
        })
        
        result = monitor.compare_sources(source_type='teams')
        
        assert result['status'] == 'warn'
        assert any('Schema mismatch' in issue for issue in result['issues'])
    
    def test_verify_feature_registry_pass(self, monitor):
        """Test feature registry verification."""
        # Mock FeatureRegistry and FeaturePatterns
        with patch('nflfastRv3.features.ml_pipeline.utils.feature_registry.FeatureRegistry') as MockRegistry, \
             patch('nflfastRv3.features.ml_pipeline.utils.feature_patterns.FeaturePatterns') as MockPatterns, \
             patch('nflfastRv3.features.ml_pipeline.utils.feature_splitter.FeatureSplitter') as MockSplitter:
            
            # Setup active features
            active_features = ['rolling_4g_epa', 'interaction_home_rest']
            MockRegistry.get_active_features.return_value = active_features
            
            # Setup patterns
            MockPatterns.GAME_OUTCOME_LINEAR = [r'^rolling_']
            MockPatterns.GAME_OUTCOME_TREE = [r'^interaction_']
            
            # Setup splitter to return all features as matched
            MockSplitter.filter_by_patterns.return_value = active_features
            
            result = monitor.verify_feature_registry()
            
            assert result['status'] == 'pass'
            assert result['metrics']['total_active_features'] == 2
            assert result['metrics']['matched_features'] == 2
            assert result['metrics']['unmatched_features'] == 0
    
    def test_debug_rest_days_contamination(self, monitor, mock_dependencies):
        """Test rest days debugging with cross-season contamination."""
        # Mock data with contamination
        mock_dependencies['db_service'].query.return_value = pd.DataFrame({
            'game_id': [1, 2, 3],
            'team': ['KC', 'KC', 'KC'],
            'game_date': ['2023-12-31', '2024-01-07', '2024-01-14'],
            'prev_game_date': ['2023-12-24', '2023-12-31', '2024-01-07'],
            'rest_days': [7, 7, 7],  # Should be ~180+ at season boundary
            'season': [2023, 2024, 2024]
        })
        
        result = monitor.debug_specific_logic(logic_type='rest_days')
        
        assert result['status'] in ['fail', 'warn']
        assert any('contamination' in issue.lower() for issue in result['issues'])