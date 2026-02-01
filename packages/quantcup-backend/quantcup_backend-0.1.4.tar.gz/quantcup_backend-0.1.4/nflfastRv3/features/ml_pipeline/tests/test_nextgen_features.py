"""
Unit Tests for NextGen QB Features

Tests temporal safety, starter identification, and differential calculations.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock
from nflfastRv3.features.ml_pipeline.feature_sets.nextgen_features import (
    NextGenFeatures,
    create_nextgen_features
)


class TestNextGenFeatures:
    """Test suite for NextGen QB feature engineering."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger for testing."""
        logger = Mock()
        logger.info = Mock()
        logger.warning = Mock()
        logger.error = Mock()
        return logger
    
    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        return Mock()
    
    @pytest.fixture
    def mock_bucket_adapter(self):
        """Create mock bucket adapter."""
        adapter = Mock()
        adapter.read_data = Mock()
        return adapter
    
    @pytest.fixture
    def sample_nextgen_data(self):
        """Create sample NextGen QB data for testing."""
        return pd.DataFrame({
            'season': [2024] * 6,
            'week': [1, 1, 1, 2, 2, 2],
            'team_abbr': ['BUF', 'BUF', 'BUF', 'BUF', 'BUF', 'BUF'],
            'player_display_name': ['Josh Allen', 'Backup QB', 'Third String', 
                                   'Josh Allen', 'Backup QB', 'Third String'],
            'player_position': ['QB'] * 6,
            'attempts': [35, 5, 2, 40, 3, 1],
            'completions': [24, 3, 1, 28, 2, 0],
            'pass_yards': [275, 45, 10, 320, 25, 5],
            'pass_touchdowns': [2, 0, 0, 3, 0, 0],
            'interceptions': [1, 0, 0, 0, 1, 0],
            'passer_rating': [110.5, 85.0, 70.0, 125.3, 65.0, 50.0],
            'completion_percentage': [68.6, 60.0, 50.0, 70.0, 66.7, 0.0],
            'completion_percentage_above_expectation': [5.2, -2.0, -5.0, 7.5, 0.0, -10.0],
            'avg_time_to_throw': [2.65, 2.80, 3.00, 2.55, 2.90, 3.20],
            'aggressiveness': [12.5, 8.0, 5.0, 14.2, 7.5, 4.0],
            'avg_intended_air_yards': [8.5, 6.0, 4.5, 9.2, 5.5, 3.0],
            'avg_completed_air_yards': [7.2, 5.0, 3.5, 8.0, 4.8, 2.0],
            'avg_air_yards_differential': [-1.3, -1.0, -1.0, -1.2, -0.7, -1.0],
            'avg_air_yards_to_sticks': [0.5, -0.5, -1.0, 0.8, -0.3, -1.5],
            'max_completed_air_distance': [45.0, 30.0, 20.0, 50.0, 25.0, 15.0]
        })
    
    @pytest.fixture
    def sample_games_data(self):
        """Create sample game schedule data."""
        return pd.DataFrame({
            'game_id': ['2024_01_BUF_MIA', '2024_02_BUF_MIA'],
            'season': [2024, 2024],
            'week': [1, 2],
            'game_date': pd.to_datetime(['2024-09-08', '2024-09-15']),
            'home_team': ['BUF', 'BUF'],
            'away_team': ['MIA', 'MIA']
        })
    
    def test_starting_qb_identification(self, mock_db_service, mock_logger, sample_nextgen_data):
        """Test that QB with most attempts is identified as starter."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger)
        
        starters = nextgen._identify_starting_qbs(sample_nextgen_data)
        
        # Should only have 1 QB per team/week (the one with most attempts)
        assert len(starters) == 2  # 2 weeks
        
        # Week 1 starter should be Josh Allen (35 attempts)
        week_1_starter = starters[starters['week'] == 1].iloc[0]
        assert week_1_starter['player_display_name'] == 'Josh Allen'
        assert week_1_starter['attempts'] == 35
        
        # Week 2 starter should be Josh Allen (40 attempts)
        week_2_starter = starters[starters['week'] == 2].iloc[0]
        assert week_2_starter['player_display_name'] == 'Josh Allen'
        assert week_2_starter['attempts'] == 40
    
    def test_temporal_safety_week_1(self, mock_db_service, mock_logger):
        """Validate Week 1 uses season average, not current week."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger)
        
        # Create test data spanning multiple weeks
        test_df = pd.DataFrame({
            'season': [2024] * 5,
            'week': [1, 2, 3, 4, 5],
            'team_abbr': ['BUF'] * 5,
            'player_display_name': ['Josh Allen'] * 5,
            'passer_rating': [110.0, 95.0, 105.0, 100.0, 108.0],
            'completion_percentage': [68.0, 62.0, 66.0, 64.0, 67.0],
            'attempts': [35, 40, 38, 36, 39]
        })
        
        result = nextgen._create_team_level_features(test_df)
        
        # Week 1 should use season average (not 110.0)
        week_1_prior = result[result['week'] == 1]['prior_passer_rating'].iloc[0]
        season_avg = test_df['passer_rating'].mean()  # 103.6
        
        assert abs(week_1_prior - season_avg) < 0.1, \
            f"Week 1 prior should be season avg ({season_avg:.1f}), got {week_1_prior:.1f}"
        
        # Week 2 should use Week 1's actual value
        week_2_prior = result[result['week'] == 2]['prior_passer_rating'].iloc[0]
        assert week_2_prior == 110.0, \
            f"Week 2 prior should be Week 1 actual (110.0), got {week_2_prior:.1f}"
        
        # Week 3 should use Week 2's actual value
        week_3_prior = result[result['week'] == 3]['prior_passer_rating'].iloc[0]
        assert week_3_prior == 95.0, \
            f"Week 3 prior should be Week 2 actual (95.0), got {week_3_prior:.1f}"
    
    def test_differential_calculations(self, mock_db_service, mock_logger):
        """Test home vs away QB differentials."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger)
        
        # Create test game with QB matchup
        test_df = pd.DataFrame({
            'game_id': ['2024_01_BUF_MIA'],
            'season': [2024],
            'week': [1],
            'game_date': pd.to_datetime(['2024-09-08']),
            'home_team': ['BUF'],
            'away_team': ['MIA'],
            'prior_passer_rating_home': [110.0],
            'prior_passer_rating_away': [95.0],
            'prior_completion_percentage_home': [68.0],
            'prior_completion_percentage_away': [62.0],
            'prior_aggressiveness_home': [12.5],
            'prior_aggressiveness_away': [10.0]
        })
        
        result = nextgen._calculate_qb_differentials(test_df)
        
        # Check differentials
        assert result['qb_passer_rating_diff'].iloc[0] == 15.0, \
            "Passer rating diff should be 110 - 95 = 15.0"
        assert result['qb_completion_pct_diff'].iloc[0] == 6.0, \
            "Completion % diff should be 68 - 62 = 6.0"
        assert result['qb_aggressiveness_diff'].iloc[0] == 2.5, \
            "Aggressiveness diff should be 12.5 - 10.0 = 2.5"
    
    def test_td_int_ratio_calculation(self, mock_db_service, mock_logger):
        """Test TD/INT ratio differential calculation."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger)
        
        test_df = pd.DataFrame({
            'game_id': ['2024_01_BUF_MIA'],
            'season': [2024],
            'week': [1],
            'game_date': pd.to_datetime(['2024-09-08']),
            'home_team': ['BUF'],
            'away_team': ['MIA'],
            'prior_pass_touchdowns_home': [3.0],
            'prior_interceptions_home': [1.0],
            'prior_pass_touchdowns_away': [2.0],
            'prior_interceptions_away': [2.0]
        })
        
        result = nextgen._calculate_qb_differentials(test_df)
        
        # Home TD/INT ratio: 3/(1+1) = 1.5
        # Away TD/INT ratio: 2/(2+1) = 0.667
        # Diff: 1.5 - 0.667 = 0.833
        expected_diff = (3.0 / 2.0) - (2.0 / 3.0)
        
        assert 'qb_td_int_ratio_diff' in result.columns
        assert abs(result['qb_td_int_ratio_diff'].iloc[0] - expected_diff) < 0.01, \
            f"TD/INT ratio diff should be {expected_diff:.3f}"
    
    def test_missing_qb_data_handling(self, mock_db_service, mock_logger):
        """Test handling of missing QB data (fills with 0.0)."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger)
        
        # Create game with missing away QB data
        test_df = pd.DataFrame({
            'game_id': ['2024_01_BUF_MIA'],
            'season': [2024],
            'week': [1],
            'game_date': pd.to_datetime(['2024-09-08']),
            'home_team': ['BUF'],
            'away_team': ['MIA'],
            'prior_passer_rating_home': [110.0],
            # Missing: prior_passer_rating_away
        })
        
        result = nextgen._calculate_qb_differentials(test_df)
        
        # Should create differential with 0.0 for missing data
        assert 'qb_passer_rating_diff' in result.columns
        assert result['qb_passer_rating_diff'].iloc[0] == 0.0, \
            "Missing QB data should result in 0.0 differential"
    
    def test_cross_season_contamination_prevention(self, mock_db_service, mock_logger):
        """Test that features don't leak across seasons."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger)
        
        # Create data spanning two seasons
        test_df = pd.DataFrame({
            'season': [2023, 2023, 2024, 2024],
            'week': [17, 18, 1, 2],
            'team_abbr': ['BUF'] * 4,
            'player_display_name': ['Josh Allen'] * 4,
            'passer_rating': [105.0, 110.0, 115.0, 108.0],
            'attempts': [35, 38, 40, 36]
        })
        
        result = nextgen._create_team_level_features(test_df)
        
        # 2024 Week 1 should NOT use 2023 Week 18 data
        # It should use 2024 season average instead
        week_1_2024 = result[(result['season'] == 2024) & (result['week'] == 1)]
        week_1_prior = week_1_2024['prior_passer_rating'].iloc[0]
        
        # 2024 season average: (115.0 + 108.0) / 2 = 111.5
        season_2024_avg = result[result['season'] == 2024]['passer_rating'].mean()
        
        assert abs(week_1_prior - season_2024_avg) < 0.1, \
            f"2024 Week 1 should use 2024 season avg ({season_2024_avg:.1f}), not 2023 data"
        
        # 2024 Week 2 should use 2024 Week 1 actual
        week_2_2024 = result[(result['season'] == 2024) & (result['week'] == 2)]
        week_2_prior = week_2_2024['prior_passer_rating'].iloc[0]
        
        assert week_2_prior == 115.0, \
            f"2024 Week 2 should use 2024 Week 1 actual (115.0), got {week_2_prior:.1f}"
    
    def test_factory_function(self):
        """Test factory function creates NextGenFeatures instance."""
        nextgen = create_nextgen_features()
        
        assert isinstance(nextgen, NextGenFeatures)
        assert nextgen.db_service is not None
        assert nextgen.logger is not None
    
    def test_multiple_qbs_per_team_week(self, mock_db_service, mock_logger):
        """Test handling of multiple QBs in same game (injury, platoon)."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger)
        
        # Create scenario with QB change mid-game
        test_df = pd.DataFrame({
            'season': [2024, 2024, 2024],
            'week': [1, 1, 1],
            'team_abbr': ['BUF', 'BUF', 'BUF'],
            'player_display_name': ['Starter QB', 'Backup QB (injury)', 'Third String'],
            'attempts': [20, 15, 5],  # Starter injured, backup played more
            'passer_rating': [95.0, 110.0, 70.0]
        })
        
        starters = nextgen._identify_starting_qbs(test_df)
        
        # Should identify QB with MOST attempts as starter (even if injured)
        assert len(starters) == 1
        assert starters.iloc[0]['player_display_name'] == 'Starter QB'
        assert starters.iloc[0]['attempts'] == 20
    
    def test_empty_dataframe_handling(self, mock_db_service, mock_logger):
        """Test graceful handling of empty DataFrames."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger)
        
        empty_df = pd.DataFrame()
        
        # Should return empty DataFrame without errors
        result = nextgen._identify_starting_qbs(empty_df)
        assert result.empty
        
        result = nextgen._create_team_level_features(empty_df)
        assert result.empty
        
        result = nextgen._calculate_qb_differentials(empty_df)
        assert result.empty


class TestNextGenIntegration:
    """Integration tests for NextGen features with full pipeline."""
    
    @pytest.fixture
    def mock_bucket_with_data(self, sample_nextgen_data, sample_games_data):
        """Create mock bucket adapter that returns sample data."""
        adapter = Mock()
        
        def read_data_side_effect(table_name, schema, filters=None):
            if table_name == 'nextgen':
                return sample_nextgen_data.copy()
            elif table_name == 'dim_game':
                return sample_games_data.copy()
            return pd.DataFrame()
        
        adapter.read_data = Mock(side_effect=read_data_side_effect)
        return adapter
    
    @pytest.fixture
    def sample_nextgen_data(self):
        """Extended sample data for integration testing."""
        # Create data for BUF and MIA across 3 weeks
        data = []
        for week in [1, 2, 3]:
            # BUF QB
            data.append({
                'season': 2024, 'week': week, 'team_abbr': 'BUF',
                'player_display_name': 'Josh Allen', 'player_position': 'QB',
                'attempts': 35 + week, 'completions': 24 + week,
                'passer_rating': 110.0 + week * 2,
                'completion_percentage': 68.0 + week,
                'completion_percentage_above_expectation': 5.0 + week * 0.5,
                'avg_time_to_throw': 2.65 - week * 0.05,
                'aggressiveness': 12.0 + week,
                'avg_intended_air_yards': 8.5 + week * 0.3,
                'avg_completed_air_yards': 7.2 + week * 0.3,
                'avg_air_yards_differential': -1.3,
                'avg_air_yards_to_sticks': 0.5,
                'max_completed_air_distance': 45.0 + week * 2,
                'pass_yards': 275 + week * 10,
                'pass_touchdowns': 2 + (week % 2),
                'interceptions': 1 if week == 1 else 0
            })
            # MIA QB
            data.append({
                'season': 2024, 'week': week, 'team_abbr': 'MIA',
                'player_display_name': 'Tua Tagovailoa', 'player_position': 'QB',
                'attempts': 32 + week, 'completions': 22 + week,
                'passer_rating': 105.0 + week,
                'completion_percentage': 65.0 + week * 0.5,
                'completion_percentage_above_expectation': 4.0 + week * 0.3,
                'avg_time_to_throw': 2.50 - week * 0.03,
                'aggressiveness': 11.0 + week * 0.5,
                'avg_intended_air_yards': 7.8 + week * 0.2,
                'avg_completed_air_yards': 6.5 + week * 0.2,
                'avg_air_yards_differential': -1.3,
                'avg_air_yards_to_sticks': 0.3,
                'max_completed_air_distance': 42.0 + week,
                'pass_yards': 260 + week * 8,
                'pass_touchdowns': 2,
                'interceptions': 1 if week == 2 else 0
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def sample_games_data(self):
        """Sample game schedule for integration testing."""
        return pd.DataFrame({
            'game_id': ['2024_01_BUF_MIA', '2024_02_BUF_MIA', '2024_03_BUF_MIA'],
            'season': [2024, 2024, 2024],
            'week': [1, 2, 3],
            'game_date': pd.to_datetime(['2024-09-08', '2024-09-15', '2024-09-22']),
            'home_team': ['BUF', 'BUF', 'BUF'],
            'away_team': ['MIA', 'MIA', 'MIA']
        })
    
    def test_full_pipeline_integration(self, mock_db_service, mock_logger, mock_bucket_with_data):
        """Test complete NextGen feature pipeline."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger, mock_bucket_with_data)
        
        result = nextgen.build_features(seasons=[2024])
        
        # Should succeed
        assert result['status'] == 'success'
        assert 'dataframe' in result
        
        df = result['dataframe']
        
        # Should have game-level data
        assert len(df) == 3  # 3 games
        assert 'game_id' in df.columns
        
        # Should have QB differential features
        expected_features = [
            'qb_passer_rating_diff',
            'qb_completion_pct_diff',
            'qb_completion_above_exp_diff',
            'qb_aggressiveness_diff'
        ]
        
        for feat in expected_features:
            assert feat in df.columns, f"Missing feature: {feat}"
        
        # Validate differentials are calculated correctly
        # Week 1: Both QBs use season average, so diff should be close to 0
        week_1 = df[df['week'] == 1].iloc[0]
        # Week 1 diffs should be small (both using season averages)
        assert abs(week_1['qb_passer_rating_diff']) < 10.0
        
        # Week 2: Should use Week 1 actual values
        week_2 = df[df['week'] == 2].iloc[0]
        # BUF Week 1: 110.0, MIA Week 1: 105.0, Diff: 5.0
        assert abs(week_2['qb_passer_rating_diff'] - 5.0) < 0.1
    
    def test_feature_count(self, mock_db_service, mock_logger, mock_bucket_with_data):
        """Test that expected number of features are created."""
        nextgen = NextGenFeatures(mock_db_service, mock_logger, mock_bucket_with_data)
        
        result = nextgen.build_features(seasons=[2024])
        df = result['dataframe']
        
        # Count QB differential features
        qb_features = [col for col in df.columns if col.startswith('qb_') and col.endswith('_diff')]
        
        # Should have 12 QB differential features (per plan)
        assert len(qb_features) >= 11, \
            f"Expected at least 11 QB features, got {len(qb_features)}: {qb_features}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])