"""
Tests for Sportsbook pipeline orchestration.

Test Coverage:
    - Pipeline initialization and configuration
    - Property methods (key, required_cols, table_name, etc.)
    - fetch() method with mocked browser and processor
    - post_process() CSV export functionality
    - run() method with various scenarios (success, empty data, dry-run)
    - State management and locking
    - Integration tests (marked with @pytest.mark.integration)
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import uuid
import json
import asyncio
from datetime import datetime

from odds_scraper.pipeline import SportsbookPipeline
from odds_scraper.config.settings import SportsbookSettings, BrowserConfig


class TestSportsbookPipelineProperties:
    """Test pipeline property methods."""
    
    def test_initialization(self):
        """Test pipeline initializes correctly with all required components."""
        pipeline = SportsbookPipeline()
        
        assert pipeline.settings is not None
        assert isinstance(pipeline.settings, SportsbookSettings)
        assert hasattr(pipeline, 'browser_engine')
        assert hasattr(pipeline, 'processor')
        assert Path('.pipelines').exists()
        assert Path('.pipelines/locks').exists()
    
    def test_key_property(self):
        """Test pipeline key is correct."""
        pipeline = SportsbookPipeline()
        assert pipeline.key == 'odds_scraper_nfl'
    
    def test_required_cols_property(self):
        """Test required columns are defined correctly."""
        pipeline = SportsbookPipeline()
        required = pipeline.required_cols
        
        assert isinstance(required, list)
        assert 'event_id' in required
        assert 'team' in required
        assert 'spread' in required
        assert 'spread_odds' in required
        assert 'moneyline' in required
        assert 'bookmaker' in required
        assert 'data_pull_id' in required
    
    def test_table_name_property(self):
        """Test table name is correct."""
        pipeline = SportsbookPipeline()
        assert pipeline.table_name == 'gamelines'
    
    def test_update_interval_property(self):
        """Test update interval comes from settings."""
        pipeline = SportsbookPipeline()
        # Default is 300 seconds (5 minutes)
        assert pipeline.update_interval > 0
        assert isinstance(pipeline.update_interval, int)
    
    def test_description_property(self):
        """Test description is human-readable."""
        pipeline = SportsbookPipeline()
        assert 'Sportsbook' in pipeline.description
        assert 'NFL' in pipeline.description


class TestSportsbookPipelineFetch:
    """Test the fetch() method."""
    
    @patch('odds_scraper.pipeline.asyncio.run')
    @patch.object(SportsbookPipeline, '_generate_pull_id')
    def test_fetch_success(self, mock_pull_id, mock_asyncio_run):
        """Test successful data fetch."""
        # Setup mocks
        mock_pull_id.return_value = 'test-pull-id-123'
        mock_raw_data = {
            'games': [
                {
                    'header': 'Team A @ Team B',
                    'date': '2025-01-01',
                    'time': '1:00PM',
                    'event_url': 'https://example.com/123',
                    'teams': [
                        {
                            'name': 'Team A',
                            'spread': '-3.5',
                            'spread_odds': '-110',
                            'moneyline': '-165'
                        },
                        {
                            'name': 'Team B',
                            'spread': '+3.5',
                            'spread_odds': '-110',
                            'moneyline': '+145'
                        }
                    ],
                    'total_over': '47.5',
                    'total_over_odds': '-110',
                    'total_under': '47.5',
                    'total_under_odds': '-110'
                }
            ]
        }
        mock_asyncio_run.return_value = mock_raw_data
        
        # Create pipeline and fetch
        pipeline = SportsbookPipeline()
        df = pipeline.fetch()
        
        # Verify results
        assert not df.empty
        assert len(df) == 2  # 2 teams
        assert 'bookmaker' in df.columns
        assert df['bookmaker'].iloc[0] == 'Sportsbook'
        assert df['data_pull_id'].iloc[0] == 'test-pull-id-123'
    
    @patch('odds_scraper.pipeline.asyncio.run')
    def test_fetch_empty_games(self, mock_asyncio_run):
        """Test fetch with no games returns empty DataFrame."""
        mock_asyncio_run.return_value = {'games': []}
        
        pipeline = SportsbookPipeline()
        df = pipeline.fetch()
        
        assert df.empty
    
    @patch('odds_scraper.pipeline.asyncio.run')
    def test_fetch_handles_exception(self, mock_asyncio_run):
        """Test fetch handles scraping exceptions gracefully."""
        mock_asyncio_run.side_effect = Exception("Browser error")
        
        pipeline = SportsbookPipeline()
        df = pipeline.fetch()
        
        # Should return empty DataFrame instead of raising
        assert df.empty


class TestSportsbookPipelinePersist:
    """Test persistence functionality."""
    
    @patch.object(SportsbookPipeline, 'bucket_adapter', new_callable=Mock)
    def test_persist_success(self, mock_bucket_adapter):
        """Test successful bucket storage."""
        mock_bucket_adapter.store_data.return_value = True
        
        pipeline = SportsbookPipeline()
        pipeline._bucket_adapter = mock_bucket_adapter
        
        # Include data_pull_start_time column that persist() expects
        df = pd.DataFrame({
            'event_id': [123, 123],
            'team': ['Team A', 'Team B'],
            'data_pull_start_time': [datetime.now(), datetime.now()]
        })
        success = pipeline.persist(df, dry_run=False)
        
        assert success is True
        mock_bucket_adapter.store_data.assert_called_once()
        
        # Verify correct schema was used
        call_kwargs = mock_bucket_adapter.store_data.call_args[1]
        assert call_kwargs['schema'] == 'odds_scraper'
        assert call_kwargs['table_name'] == 'gamelines'
    
    def test_persist_dry_run_mode(self):
        """Test dry run skips actual storage."""
        pipeline = SportsbookPipeline()
        df = pd.DataFrame({'a': [1, 2, 3]})
        
        success = pipeline.persist(df, dry_run=True)
        
        assert success is True
        # bucket_adapter should not be accessed in dry run
        assert pipeline._bucket_adapter is None
    
    @patch.object(SportsbookPipeline, 'bucket_adapter', new_callable=Mock)
    def test_persist_handles_exception(self, mock_bucket_adapter):
        """Test persist handles storage exceptions gracefully."""
        mock_bucket_adapter.store_data.side_effect = Exception("Storage error")
        
        pipeline = SportsbookPipeline()
        pipeline._bucket_adapter = mock_bucket_adapter
        
        # Include data_pull_start_time column that persist() expects
        df = pd.DataFrame({
            'event_id': [123],
            'team': ['Team A'],
            'data_pull_start_time': [datetime.now()]
        })
        success = pipeline.persist(df, dry_run=False)
        
        assert success is False


class TestSportsbookPipelinePostProcess:
    """Test post-processing functionality."""
    
    def test_post_process_without_csv(self):
        """Test post_process does nothing when write_csv=False."""
        pipeline = SportsbookPipeline()
        df = pd.DataFrame({'a': [1, 2, 3]})
        
        # Should not raise, does nothing
        pipeline.post_process(df, write_csv=False)
    
    def test_post_process_with_csv(self, tmp_path, monkeypatch):
        """Test CSV export functionality."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        pipeline = SportsbookPipeline()
        df = pd.DataFrame({
            'event_id': [123, 123],
            'team': ['Team A', 'Team B'],
            'spread': [-3.5, 3.5]
        })
        
        pipeline.post_process(df, write_csv=True)
        
        # Verify CSV was created
        csv_dir = tmp_path / 'data' / 'odds_scraper'
        assert csv_dir.exists()
        
        csv_files = list(csv_dir.glob('odds_*.csv'))
        assert len(csv_files) == 1
        
        # Verify content
        exported_df = pd.read_csv(csv_files[0])
        assert len(exported_df) == 2
        assert 'team' in exported_df.columns


class TestSportsbookPipelineRun:
    """Test the run() method end-to-end."""
    
    def setup_method(self):
        """Setup mocks for each test."""
        self.mock_df = pd.DataFrame({
            'event_id': [123, 123],
            'header': ['Game 1', 'Game 1'],
            'date': ['01/01/2025', '01/01/2025'],
            'time': ['1:00PM', '1:00PM'],
            'team': ['Team A', 'Team B'],
            'spread': [-3.5, 3.5],
            'spread_odds': [-110, -110],
            'moneyline': [-165, 145],
            'total_over': [47.5, 47.5],
            'total_over_odds': [-110, -110],
            'total_under': [47.5, 47.5],
            'total_under_odds': [-110, -110],
            'bookmaker': ['Sportsbook', 'Sportsbook'],
            'data_pull_id': ['test-123', 'test-123']
        })
    
    @patch.object(SportsbookPipeline, 'persist')
    @patch.object(SportsbookPipeline, 'fetch')
    @patch.object(SportsbookPipeline, '_check_interval')
    @patch.object(SportsbookPipeline, '_acquire_lock')
    @patch.object(SportsbookPipeline, '_release_lock')
    @patch.object(SportsbookPipeline, '_save_state')
    def test_run_success(self, mock_save_state, mock_release, mock_acquire,
                        mock_check, mock_fetch, mock_persist):
        """Test successful pipeline run."""
        # Setup mocks
        mock_check.return_value = True
        mock_acquire.return_value = True
        mock_fetch.return_value = self.mock_df
        mock_persist.return_value = True
        
        pipeline = SportsbookPipeline()
        rows = pipeline.run(force=False, dry_run=False)
        
        # Verify
        assert rows == 2
        mock_fetch.assert_called_once()
        mock_persist.assert_called_once()
        mock_save_state.assert_called_once_with(2)
        mock_release.assert_called_once()
    
    @patch.object(SportsbookPipeline, '_check_interval')
    def test_run_blocked_by_cooldown(self, mock_check):
        """Test run respects cooldown interval."""
        mock_check.return_value = False
        
        pipeline = SportsbookPipeline()
        rows = pipeline.run()
        
        # Should return 0 without fetching
        assert rows == 0
    
    @patch.object(SportsbookPipeline, '_check_interval')
    @patch.object(SportsbookPipeline, '_acquire_lock')
    def test_run_blocked_by_lock(self, mock_acquire, mock_check):
        """Test run respects PID lock."""
        mock_check.return_value = True
        mock_acquire.return_value = False
        
        pipeline = SportsbookPipeline()
        rows = pipeline.run()
        
        assert rows == 0
    
    @patch.object(SportsbookPipeline, 'persist')
    @patch.object(SportsbookPipeline, 'fetch')
    @patch.object(SportsbookPipeline, '_check_interval')
    @patch.object(SportsbookPipeline, '_acquire_lock')
    @patch.object(SportsbookPipeline, '_release_lock')
    @patch.object(SportsbookPipeline, '_save_state')
    def test_run_dry_run_mode(self, mock_save_state, mock_release, mock_acquire,
                              mock_check, mock_fetch, mock_persist):
        """Test dry run mode skips bucket storage."""
        mock_check.return_value = True
        mock_acquire.return_value = True
        mock_fetch.return_value = self.mock_df
        mock_persist.return_value = True
        
        pipeline = SportsbookPipeline()
        rows = pipeline.run(dry_run=True)
        
        assert rows == 2
        mock_fetch.assert_called_once()
        
        # Verify persist was called with dry_run=True
        mock_persist.assert_called_once()
        call_kwargs = mock_persist.call_args[1]
        assert call_kwargs['dry_run'] is True
        
        mock_save_state.assert_not_called()  # ✅ Should not save state in dry run
        mock_release.assert_called_once()
    
    @patch.object(SportsbookPipeline, 'fetch')
    @patch.object(SportsbookPipeline, '_check_interval')
    @patch.object(SportsbookPipeline, '_acquire_lock')
    @patch.object(SportsbookPipeline, '_release_lock')
    @patch.object(SportsbookPipeline, '_save_state')
    def test_run_empty_data(self, mock_save_state, mock_release, mock_acquire,
                            mock_check, mock_fetch):
        """Test run handles empty data gracefully."""
        mock_check.return_value = True
        mock_acquire.return_value = True
        mock_fetch.return_value = pd.DataFrame()  # Empty
        
        pipeline = SportsbookPipeline()
        rows = pipeline.run()
        
        assert rows == 0
        mock_save_state.assert_called_once_with(0)
        mock_release.assert_called_once()
    
    @patch.object(SportsbookPipeline, 'persist')
    @patch.object(SportsbookPipeline, 'fetch')
    @patch.object(SportsbookPipeline, 'post_process')
    @patch.object(SportsbookPipeline, '_check_interval')
    @patch.object(SportsbookPipeline, '_acquire_lock')
    @patch.object(SportsbookPipeline, '_release_lock')
    def test_run_with_csv_export(self, mock_release, mock_acquire, mock_check,
                                 mock_post_process, mock_fetch, mock_persist):
        """Test run calls post_process with write_csv flag."""
        mock_check.return_value = True
        mock_acquire.return_value = True
        mock_fetch.return_value = self.mock_df
        mock_persist.return_value = True
        
        pipeline = SportsbookPipeline()
        pipeline.run(write_csv=True)
        
        # Verify post_process was called with write_csv
        mock_post_process.assert_called_once()
        call_kwargs = mock_post_process.call_args[1]
        assert call_kwargs.get('write_csv') is True
    
    @patch.object(SportsbookPipeline, 'fetch')
    @patch.object(SportsbookPipeline, '_check_interval')
    @patch.object(SportsbookPipeline, '_acquire_lock')
    @patch.object(SportsbookPipeline, '_release_lock')
    def test_run_exception_handling(self, mock_release, mock_acquire,
                                    mock_check, mock_fetch):
        """Test run handles exceptions and releases lock."""
        mock_check.return_value = True
        mock_acquire.return_value = True
        mock_fetch.side_effect = Exception("Test error")
        
        pipeline = SportsbookPipeline()
        
        with pytest.raises(Exception, match="Test error"):
            pipeline.run()
        
        # Verify lock was released even on exception
        mock_release.assert_called_once()
    
    @patch.object(SportsbookPipeline, 'persist')
    @patch.object(SportsbookPipeline, 'fetch')
    @patch.object(SportsbookPipeline, '_check_interval')
    @patch.object(SportsbookPipeline, '_acquire_lock')
    @patch.object(SportsbookPipeline, '_release_lock')
    def test_run_persistence_failure(self, mock_release, mock_acquire,
                                     mock_check, mock_fetch, mock_persist):
        """Test run handles persistence failure gracefully."""
        mock_check.return_value = True
        mock_acquire.return_value = True
        mock_fetch.return_value = self.mock_df
        mock_persist.return_value = False  # Persistence failed
        
        pipeline = SportsbookPipeline()
        rows = pipeline.run()
        
        # Should return 0 when persistence fails
        assert rows == 0
        mock_release.assert_called_once()


@pytest.mark.integration
class TestSportsbookPipelineIntegration:
    """
    Integration tests requiring actual dependencies.
    
    Marked with @pytest.mark.integration to allow selective running.
    Run with: pytest odds_scraper/tests/test_pipeline.py -m integration -v
    """
    
    def test_pipeline_creates_state_directory(self):
        """Test pipeline creates .pipelines directory on init."""
        pipeline = SportsbookPipeline()
        
        assert Path('.pipelines').exists()
        assert Path('.pipelines/locks').exists()
    
    def test_generate_pull_id_uniqueness(self):
        """Test _generate_pull_id creates unique IDs."""
        pipeline = SportsbookPipeline()
        
        id1 = pipeline._generate_pull_id()
        id2 = pipeline._generate_pull_id()
        
        assert id1 != id2
        # Should be valid UUID
        uuid.UUID(id1)
        uuid.UUID(id2)
    
    def test_state_file_operations(self, tmp_path):
        """Test state file read/write operations."""
        pipeline = SportsbookPipeline()
        
        # Save state
        pipeline._save_state(rows_processed=100)
        
        # Verify state file exists
        state_path = pipeline._get_state_path()
        assert state_path.exists()
        
        # Verify content
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        assert state['last_rows'] == 100
        assert state['status'] == 'success'
        assert 'last_run' in state


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
