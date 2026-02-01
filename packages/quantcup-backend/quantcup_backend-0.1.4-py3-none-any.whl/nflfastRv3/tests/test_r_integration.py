"""Unit tests for nflfastRv3 R integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from nflfastRv3.shared.r_integration import RIntegrationService, get_r_service
from nflfastRv3.shared.models import ValidationResult
from nflfastRv3.features.data_pipeline.config.data_sources import DataSourceConfig


class TestRIntegrationService:
    """Test RIntegrationService class."""
    
    def test_singleton_pattern(self):
        """Test that RIntegrationService follows singleton pattern."""
        service1 = RIntegrationService.get_instance()
        service2 = RIntegrationService.get_instance()
        assert service1 is service2
    
    def test_get_r_service_convenience_function(self):
        """Test get_r_service convenience function."""
        service = get_r_service()
        assert isinstance(service, RIntegrationService)
    
    @patch('nflfastRv3.shared.r_integration.HAS_RPY2', True)
    @patch('nflfastRv3.shared.r_integration.pandas2ri')
    @patch('nflfastRv3.shared.r_integration.robjects')
    def test_initialization_with_rpy2(self, mock_robjects, mock_pandas2ri):
        """Test initialization when rpy2 is available."""
        mock_r_session = Mock()
        mock_r_session.return_value = ['R version 4.3.0']
        mock_robjects.r = mock_r_session
        
        with patch('nflfastRv3.shared.r_integration.importr') as mock_importr:
            mock_importr.return_value = Mock()  # Mock nflfastR package
            
            service = RIntegrationService()
            assert service.r_available is True
            assert service.nflfastr_available is True
    
    @patch('nflfastRv3.shared.r_integration.HAS_RPY2', False)
    def test_initialization_without_rpy2(self):
        """Test initialization when rpy2 is not available."""
        service = RIntegrationService()
        assert service.r_available is True  # Still allows basic functionality
        assert service.nflfastr_available is False
    
    @patch('nflfastRv3.shared.r_integration.HAS_RPY2', True)
    @patch('nflfastRv3.shared.r_integration.pandas2ri')
    @patch('nflfastRv3.shared.r_integration.robjects')
    def test_execute_r_call_string_with_rpy2(self, mock_robjects, mock_pandas2ri):
        """Test execute_r_call_string with rpy2."""
        # Mock successful R function execution
        mock_r_session = Mock()
        mock_r_session.return_value = ['R version 4.3.0']
        mock_robjects.r = mock_r_session
        
        # Mock direct R call execution
        mock_df = pd.DataFrame({'game_id': ['2023_01_BUF_MIA'], 'week': [1]})
        mock_r_session.side_effect = [['R version 4.3.0'], mock_df]
        
        # Mock pandas conversion
        mock_pandas2ri.rpy2py.return_value = mock_df
        
        with patch('nflfastRv3.shared.r_integration.importr') as mock_importr:
            mock_importr.return_value = Mock()
            
            service = RIntegrationService()
            result = service.execute_r_call_string('load_pbp(seasons = c(2023))')
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
    
    @patch('nflfastRv3.shared.r_integration.HAS_RPY2', False)
    def test_execute_r_call_string_fallback(self):
        """Test execute_r_call_string with fallback method."""
        service = RIntegrationService()
        
        # Fallback should return empty DataFrame
        result = service.execute_r_call_string('load_pbp(seasons = c(2023))')
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    def test_execute_r_call_string_without_r_available(self):
        """Test execute_r_call_string when R is not available."""
        with patch.object(RIntegrationService, '_initialize_r_environment'):
            service = RIntegrationService()
            service.r_available = False
            
            with pytest.raises(RuntimeError, match="R environment not available"):
                service.execute_r_call_string('load_pbp(seasons = c(2023))')
    
    # NOTE: load_nfl_data function removed as part of architectural fix
    # ML pipeline now uses database layer instead of direct R calls
    
    def test_validate_loaded_data_success(self):
        """Test successful data validation."""
        config = DataSourceConfig(
            r_call="load_pbp(seasons = c(2023))",
            table="pbp",
            schema="nfl_data",
            unique_keys=["play_id", "game_id"],
            strategy="incremental"
        )
        
        df = pd.DataFrame({
            'play_id': [1, 2, 3],
            'game_id': ['2023_01_BUF_MIA'] * 3,
            'week': [1, 1, 1]
        })
        
        service = RIntegrationService()
        validation = service._validate_loaded_data(df, config)
        
        assert validation.is_valid is True
        assert validation.record_count == 3
        assert len(validation.errors) == 0
    
    def test_validate_loaded_data_empty(self):
        """Test validation of empty data."""
        config = DataSourceConfig(
            r_call="load_pbp(seasons = c(2023))",
            table="pbp",
            schema="nfl_data",
            unique_keys=["play_id"],
            strategy="incremental"
        )
        
        df = pd.DataFrame()
        
        service = RIntegrationService()
        validation = service._validate_loaded_data(df, config)
        
        assert validation.is_valid is False
        assert "No data loaded" in validation.errors
    
    def test_validate_loaded_data_missing_keys(self):
        """Test validation with missing required keys."""
        config = DataSourceConfig(
            r_call="load_pbp(seasons = c(2023))",
            table="pbp",
            schema="nfl_data",
            unique_keys=["play_id", "missing_column"],
            strategy="incremental"
        )
        
        df = pd.DataFrame({
            'play_id': [1, 2, 3],
            'game_id': ['2023_01_BUF_MIA'] * 3
        })
        
        service = RIntegrationService()
        validation = service._validate_loaded_data(df, config)
        
        assert validation.is_valid is False
        assert "Missing required columns" in validation.errors[0]
        assert "missing_column" in validation.errors[0]
    
    def test_validate_loaded_data_duplicates(self):
        """Test validation with duplicate records."""
        config = DataSourceConfig(
            r_call="load_pbp(seasons = c(2023))",
            table="pbp",
            schema="nfl_data",
            unique_keys=["play_id"],
            strategy="incremental"
        )
        
        df = pd.DataFrame({
            'play_id': [1, 1, 2],  # Duplicate play_id
            'game_id': ['2023_01_BUF_MIA'] * 3
        })
        
        service = RIntegrationService()
        validation = service._validate_loaded_data(df, config)
        
        assert validation.is_valid is True  # Still valid but has warnings
        assert "duplicate records" in validation.warnings[0]
    
    def test_validate_loaded_data_null_columns(self):
        """Test validation with null columns."""
        config = DataSourceConfig(
            r_call="load_pbp(seasons = c(2023))",
            table="pbp",
            schema="nfl_data",
            unique_keys=["play_id"],
            strategy="incremental"
        )
        
        df = pd.DataFrame({
            'play_id': [1, 2, 3],
            'null_column': [None, None, None]
        })
        
        service = RIntegrationService()
        validation = service._validate_loaded_data(df, config)
        
        assert validation.is_valid is True  # Still valid but has warnings
        assert "all null values" in validation.warnings[0]
    
    @patch('nflfastRv3.shared.r_integration.HAS_RPY2', True)
    @patch('nflfastRv3.shared.r_integration.importr')
    def test_get_available_functions_success(self, mock_importr):
        """Test getting available nflfastR functions."""
        mock_nflfastr = Mock()
        mock_nflfastr.__dict__ = {
            'load_pbp': Mock(),
            'load_schedules': Mock(),
            '_private_function': Mock(),
            'another_function': Mock()
        }
        mock_importr.return_value = mock_nflfastr
        
        service = RIntegrationService()
        service.nflfastr_available = True
        service.nflreadr_available = False
        
        functions = service.get_available_functions()
        
        # Functions should be prefixed with package name
        assert 'nflfastR::load_pbp' in functions
        assert 'nflfastR::load_schedules' in functions
        assert 'nflfastR::another_function' in functions
        assert 'nflfastR::_private_function' not in functions  # Should exclude private functions
    
    @patch('nflfastRv3.shared.r_integration.HAS_RPY2', False)
    def test_get_available_functions_no_rpy2(self):
        """Test getting available functions when rpy2 is not available."""
        service = RIntegrationService()
        functions = service.get_available_functions()
        assert functions == []
    
    def test_is_healthy_true(self):
        """Test health check when service is healthy."""
        service = RIntegrationService()
        service.r_available = True
        service.nflfastr_available = True
        
        assert service.is_healthy is True
    
    def test_is_healthy_false_no_r(self):
        """Test health check when R is not available."""
        service = RIntegrationService()
        service.r_available = False
        service.nflfastr_available = True
        
        assert service.is_healthy is False
    
    @patch('nflfastRv3.shared.r_integration.HAS_RPY2', False)
    def test_is_healthy_no_rpy2_but_r_available(self):
        """Test health check when rpy2 is not available but R is."""
        service = RIntegrationService()
        service.r_available = True
        service.nflfastr_available = False
        
        assert service.is_healthy is True  # Should still be healthy with fallback


class TestRIntegrationConvenienceFunctions:
    """Test convenience functions for R integration."""
    
    def test_execute_real_r_call_convenience(self):
        """Test execute_real_r_call convenience function."""
        mock_df = pd.DataFrame({'test': [1, 2, 3]})
        
        with patch('nflfastRv3.shared.r_integration.get_r_service') as mock_get_service:
            mock_service = Mock()
            mock_service.execute_r_call_string.return_value = mock_df
            mock_get_service.return_value = mock_service
            
            from nflfastRv3.shared.r_integration import execute_real_r_call
            result = execute_real_r_call('load_pbp(seasons = c(2023))')
            
            assert isinstance(result, pd.DataFrame)
            mock_service.execute_r_call_string.assert_called_once_with('load_pbp(seasons = c(2023))', None)
    
    def test_execute_r_call_string_with_config(self):
        """Test execute_r_call_string with data source configuration."""
        config = DataSourceConfig(
            r_call="load_pbp(seasons = c(2023))",
            table="pbp",
            schema="nfl_data",
            unique_keys=["play_id"],
            strategy="incremental"
        )
        
        mock_df = pd.DataFrame({'test': [1, 2, 3]})
        
        with patch('nflfastRv3.shared.r_integration.get_r_service') as mock_get_service:
            mock_service = Mock()
            mock_service.execute_r_call_string.return_value = mock_df
            mock_get_service.return_value = mock_service
            
            service = get_r_service()
            result = service.execute_r_call_string(config.r_call, config.table)
            
            assert isinstance(result, pd.DataFrame)
            mock_service.execute_r_call_string.assert_called_once_with(config.r_call, config.table)
    
    def test_multiple_data_sources_execution(self):
        """Test executing multiple data source configurations."""
        mock_dfs = {
            'play_by_play': pd.DataFrame({'play_id': [1, 2, 3]}),
            'schedules': pd.DataFrame({'game_id': ['2023_01_BUF_MIA']}),
            'rosters': pd.DataFrame({'player_id': ['player1', 'player2']})
        }
        
        with patch('nflfastRv3.shared.r_integration.get_r_service') as mock_get_service:
            mock_service = Mock()
            mock_service.execute_r_call_string.side_effect = lambda r_call, name: mock_dfs.get(name, pd.DataFrame())
            mock_service.logger = Mock()
            mock_get_service.return_value = mock_service
            
            # Test multiple data source executions
            from nflfastRv3.features.data_pipeline.config.data_sources import NFL_DATA_SOURCES
            service = get_r_service()
            results = {}
            for name, config in NFL_DATA_SOURCES.items():
                if name in ['play_by_play', 'schedules', 'rosters']:  # Test subset
                    try:
                        df = service.execute_r_call_string(config.r_call, name)
                        if not df.empty:
                            results[name] = df
                    except Exception:
                        pass  # Skip failed loads in test
            
            assert 'play_by_play' in results
            assert 'schedules' in results
            assert 'rosters' in results
            assert len(results['play_by_play']) == 3
            assert len(results['schedules']) == 1
            assert len(results['rosters']) == 2


class TestRIntegrationErrorHandling:
    """Test error handling in R integration."""
    
    @patch('nflfastRv3.shared.r_integration.HAS_RPY2', True)
    @patch('nflfastRv3.shared.r_integration.robjects')
    @patch('nflfastRv3.shared.r_integration.RRuntimeError', Exception)
    def test_rpy2_runtime_error(self, mock_robjects):
        """Test handling of R runtime errors."""
        # Import RRuntimeError from the correct location
        from nflfastRv3.shared.r_integration import RRuntimeError
        
        mock_r_session = Mock()
        mock_robjects.r = mock_r_session
        mock_r_session.side_effect = [['R version 4.3.0'], RRuntimeError("R runtime error")]
        
        with patch('nflfastRv3.shared.r_integration.pandas2ri'), \
             patch('nflfastRv3.shared.r_integration.importr'):
            
            service = RIntegrationService()
            service.r_available = True
            
            with pytest.raises(RuntimeError, match="R call.*execution failed"):
                service.execute_r_call_string('load_pbp(seasons = c(2023))')
    
    def test_execute_r_call_string_error_handling(self):
        """Test error handling in execute_r_call_string (core R functionality)."""
        with patch.object(RIntegrationService, '_execute_smart_r_call', side_effect=Exception("R error")):
            service = RIntegrationService()
            service.r_available = True
            
            with pytest.raises(RuntimeError, match="R call.*execution failed"):
                service.execute_r_call_string('load_pbp(seasons = c(2023))')


class TestRIntegrationPerformance:
    """Performance tests for R integration."""
    
    def test_singleton_performance(self):
        """Test performance of singleton pattern."""
        import time
        
        start = time.time()
        for _ in range(1000):
            service = RIntegrationService.get_instance()
        end = time.time()
        
        assert (end - start) < 0.1  # Should be very fast
    
    def test_validation_performance(self):
        """Test performance of data validation."""
        config = DataSourceConfig(
            r_call="load_pbp(seasons = c(2023))",
            table="large_dataset",
            schema="nfl_data",
            unique_keys=["play_id"],
            strategy="incremental"
        )
        
        # Create large DataFrame
        large_df = pd.DataFrame({
            'play_id': range(10000),
            'game_id': ['2023_01_BUF_MIA'] * 10000,
            'week': [1] * 10000
        })
        
        service = RIntegrationService()
        
        import time
        start = time.time()
        validation = service._validate_loaded_data(large_df, config)
        end = time.time()
        
        assert (end - start) < 1.0  # Should complete in under 1 second
        assert validation.is_valid is True
        assert validation.record_count == 10000
