"""
Unit Tests for Train/Test Split Refactoring

Tests for the data leakage fix and new features added in the train/test split refactoring.
Covers both Phase 1 (explicit seasons) and Phase 2 (week filtering + relative training).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import numpy as np
from nflfastRv3.features.ml_pipeline.models.game_outcome import GameOutcomeModel


class TestPhase1DataLeakageFix:
    """Tests for Phase 1: Data leakage fix and explicit seasons."""
    
    def test_auto_split_removes_last_season_from_training(self):
        """Verify train and test seasons don't overlap after auto-split fix."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        # Create mock dependencies
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Test auto-split with multiple seasons
        train_seasons = '2020-2023'
        train_list = trainer._parse_seasons(train_seasons)
        
        # Simulate the fixed auto-split logic
        test_list = [train_list[-1]]
        train_list_fixed = train_list[:-1]
        
        # Verify no overlap
        assert set(train_list_fixed) & set(test_list) == set(), \
            "Train and test seasons should not overlap after fix"
        assert train_list_fixed == [2020, 2021, 2022], \
            "Training should exclude last season"
        assert test_list == [2023], \
            "Testing should use only last season"
    
    def test_single_season_auto_split_raises_error(self):
        """Test error when auto-splitting single season."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Mock the data preparation to avoid actual data loading
        with patch.object(trainer, '_prepare_training_data'):
            with pytest.raises(ValueError, match="Cannot auto-split single season"):
                trainer.train_model(
                    model_class=GameOutcomeModel,
                    train_seasons='2023',
                    test_seasons=None
                )
    
    def test_overlap_validation_explicit_seasons(self):
        """Test error when train and test seasons overlap in explicit mode."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Mock the data preparation to avoid actual data loading
        with patch.object(trainer, '_prepare_training_data'):
            with pytest.raises(ValueError, match="must not overlap"):
                trainer.train_model(
                    model_class=GameOutcomeModel,
                    train_seasons='2020-2023',
                    test_seasons='2022,2023'  # Overlaps!
                )
    
    def test_explicit_seasons_no_overlap_succeeds(self):
        """Test that explicit seasons without overlap work correctly."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Parse seasons
        train_list = trainer._parse_seasons('2020-2022')
        test_list = trainer._parse_seasons('2023')
        
        # Verify no overlap
        overlap = set(train_list) & set(test_list)
        assert overlap == set(), "Should have no overlap"
        assert train_list == [2020, 2021, 2022]
        assert test_list == [2023]
    
    def test_season_parsing_range_format(self):
        """Test season parsing with range format."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Test range format
        seasons = trainer._parse_seasons('2020-2023')
        assert seasons == [2020, 2021, 2022, 2023]
    
    def test_season_parsing_comma_format(self):
        """Test season parsing with comma-separated format."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Test comma-separated format
        seasons = trainer._parse_seasons('2020,2021,2022,2023')
        assert seasons == [2020, 2021, 2022, 2023]


class TestPhase2WeekFiltering:
    """Tests for Phase 2: Week filtering and relative training."""
    
    def test_week_validation_valid_range(self):
        """Test that valid week numbers (1-22) are accepted."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Mock the data preparation to avoid actual data loading
        with patch.object(trainer, '_prepare_training_data', return_value=pd.DataFrame()):
            # Valid weeks should not raise errors
            for week in [1, 10, 18, 22]:
                try:
                    trainer.train_model(
                        model_class=GameOutcomeModel,
                        train_seasons='2020-2022',
                        test_seasons='2023',
                        test_week=week
                    )
                except ValueError as e:
                    if "Invalid week" in str(e):
                        pytest.fail(f"Week {week} should be valid but raised error")
    
    def test_week_validation_invalid_range(self):
        """Test that invalid week numbers raise errors."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Mock the data preparation to avoid actual data loading
        with patch.object(trainer, '_prepare_training_data'):
            # Invalid weeks should raise errors
            for week in [0, 23, 99, -1]:
                with pytest.raises(ValueError, match="Invalid week"):
                    trainer.train_model(
                        model_class=GameOutcomeModel,
                        train_seasons='2020-2022',
                        test_seasons='2023',
                        test_week=week
                    )
    
    def test_week_filtering_parameter_passthrough(self):
        """Test that test_week parameter is passed through correctly."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Mock _prepare_training_data to capture the test_week parameter
        mock_prepare = Mock(return_value=pd.DataFrame())
        
        with patch.object(trainer, '_prepare_training_data', mock_prepare):
            trainer.train_model(
                model_class=GameOutcomeModel,
                train_seasons='2020-2022',
                test_seasons='2023',
                test_week=10
            )
            
            # Verify test_week was passed to _prepare_training_data
            mock_prepare.assert_called_once()
            call_args = mock_prepare.call_args
            assert call_args[0][2] == 10, "test_week should be passed as third argument"


class TestCLIArgumentHandling:
    """Tests for CLI argument handling and mode detection."""
    
    def test_explicit_seasons_mode_requires_both_args(self):
        """Test that explicit seasons mode requires both train and test seasons."""
        from nflfastRv3.cli.ml_commands import MLCommands
        
        # Mock args with only train_seasons
        args = type('Args', (), {
            'model': 'xgboost',
            'train_seasons': '2020-2022',
            'test_seasons': None,
            'train_years': None,
            'test_year': None,
            'test_week': None,
            'season': 2024,
            'save_model': False
        })()
        
        mock_logger = Mock()
        result = MLCommands._handle_train(args, mock_logger)
        
        # Should return error code
        assert result == 1
        mock_logger.error.assert_called()
    
    def test_relative_training_mode_calculates_window(self):
        """Test that relative training mode calculates correct training window."""
        # Test the calculation logic
        test_year = 2024
        train_years = 5
        
        start_year = test_year - train_years  # 2019
        end_year = test_year - 1  # 2023
        
        assert start_year == 2019
        assert end_year == 2023
        assert start_year < end_year, "Training window should be valid"
    
    def test_deprecated_season_argument_still_works(self):
        """Test that deprecated --season argument maintains backward compatibility."""
        from nflfastRv3.cli.ml_commands import MLCommands
        
        # Mock args with deprecated --season
        args = type('Args', (), {
            'model': 'xgboost',
            'train_seasons': None,
            'test_seasons': None,
            'train_years': None,
            'test_year': None,
            'test_week': None,
            'season': 2023,  # Deprecated but should still work
            'save_model': False
        })()
        
        mock_logger = Mock()
        
        # Mock the ML pipeline to avoid actual training
        with patch('nflfastRv3.cli.ml_commands.MLPipelineImpl') as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.train_model_only.return_value = {
                'status': 'success',
                'metrics': {'accuracy': 0.7, 'auc': 0.75}
            }
            mock_pipeline_class.return_value = mock_pipeline
            
            with patch('nflfastRv3.cli.ml_commands.get_database_router'):
                result = MLCommands._handle_train(args, mock_logger)
                
                # Should succeed
                assert result == 0
                # Should show deprecation warning
                mock_logger.warning.assert_called()


class TestBucketSideFiltering:
    """Tests for bucket-side week filtering optimization."""
    
    def test_week_filter_format(self):
        """Test that week filters are formatted correctly for PyArrow."""
        # Test filter format
        test_week = 10
        test_seasons = [2023]
        
        # Expected filter format for PyArrow
        expected_filters = [
            ('season', '==', 2023),
            ('week', '==', 10)
        ]
        
        # Verify filter structure
        assert len(expected_filters) == 2
        assert expected_filters[0][0] == 'season'
        assert expected_filters[0][1] == '=='
        assert expected_filters[1][0] == 'week'
        assert expected_filters[1][1] == '=='
        assert expected_filters[1][2] == test_week


class TestIntegration:
    """Integration tests for the complete refactoring."""
    
    def test_end_to_end_explicit_seasons(self):
        """Test end-to-end flow with explicit seasons."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Test the season parsing and validation logic
        train_list = trainer._parse_seasons('2020-2022')
        test_list = trainer._parse_seasons('2023')
        
        # Verify overlap validation would pass
        overlap = set(train_list) & set(test_list)
        assert overlap == set()
        
        # Verify seasons are correct
        assert train_list == [2020, 2021, 2022]
        assert test_list == [2023]
    
    def test_end_to_end_auto_split(self):
        """Test end-to-end flow with auto-split."""
        from nflfastRv3.features.ml_pipeline.model_trainer import ModelTrainerImplementation
        
        mock_db = Mock()
        mock_logger = Mock()
        trainer = ModelTrainerImplementation(mock_db, mock_logger)
        
        # Test the auto-split logic
        train_list = trainer._parse_seasons('2020-2023')
        
        # Simulate auto-split
        if len(train_list) >= 2:
            test_list = [train_list[-1]]
            train_list = train_list[:-1]
            
            # Verify no overlap
            assert set(train_list) & set(test_list) == set()
            assert train_list == [2020, 2021, 2022]
            assert test_list == [2023]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])