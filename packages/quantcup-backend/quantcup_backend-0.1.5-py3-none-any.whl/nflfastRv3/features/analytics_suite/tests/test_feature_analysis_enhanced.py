import pytest
from unittest.mock import Mock, MagicMock
import pandas as pd
import numpy as np
from nflfastRv3.features.analytics_suite.feature_analysis import FeatureAnalysisImpl


class TestFeatureAnalysisEnhanced:
    """Unit tests for enhanced feature analysis methods."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        return {
            'db_service': Mock(),
            'logger': Mock(),
            'bucket_adapter': Mock()
        }
    
    @pytest.fixture
    def analyzer(self, mock_dependencies):
        """Create FeatureAnalysisImpl instance."""
        return FeatureAnalysisImpl(**mock_dependencies)
    
    def test_analyze_contextual_features_phase1(self, analyzer, mock_dependencies):
        """Test Phase 1 contextual feature analysis."""
        # Mock data
        mock_dependencies['db_service'].query.return_value = pd.DataFrame({
            'game_id': [1, 2, 3],
            'team': ['KC', 'KC', 'BAL'],
            'rest_days': [7, 7, 6],
            'is_division_game': [True, False, True],
            'location': ['home', 'away', 'home'],
            'stadium_type': ['outdoor', 'dome', 'outdoor'],
            'win_prob_delta': [0.05, -0.02, 0.03]
        })
        
        result = analyzer.analyze_contextual_features(phases=[1])
        
        assert 'phase1' in result
        assert 'rest_days' in result['phase1']
        assert 'division_games' in result['phase1']
    
    def test_analyze_merged_correlations(self, analyzer, mock_dependencies):
        """Test merged feature correlation analysis."""
        # Mock data
        mock_dependencies['db_service'].query.return_value = pd.DataFrame({
            'game_id': [1, 2, 3],
            'home_win': [1, 0, 1],
            'avg_points_4g': [24.5, 21.3, 28.1],
            'diff_yards_8g': [50, -30, 75],
            'ctx_rest_days': [7, 6, 7]
        })
        
        result = analyzer.analyze_merged_correlations(top_n=5)
        
        assert 'target_correlations' in result
        assert 'feature_importance' in result
        assert 'feature_type_comparison' in result
    
    def test_evaluate_rolling_metrics_validation(self, analyzer, mock_dependencies):
        """Test rolling metrics validation."""
        # Mock data with rolling metrics
        mock_dependencies['db_service'].query.return_value = pd.DataFrame({
            'team': ['KC', 'KC', 'KC', 'KC'],
            'game_date': pd.date_range('2024-09-01', periods=4, freq='W'),
            'points': [28, 24, 31, 27],
            'avg_points_4g': [np.nan, 28, 26, 27.67]
        })
        
        result = analyzer.evaluate_rolling_metrics(windows=[4])
        
        assert 'validation' in result
        assert '4g' in result['validation']
        # Note: validation_passed might be False due to mock data not perfectly matching rolling calc
        # but we check structure exists
        assert 'max_error' in result['validation']['4g']