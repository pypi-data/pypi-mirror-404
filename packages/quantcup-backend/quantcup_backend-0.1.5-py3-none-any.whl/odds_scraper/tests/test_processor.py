"""Unit tests for OddsDataProcessor."""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from odds_scraper.core.processor import OddsDataProcessor


class TestOddsDataProcessor:
    """Test suite for OddsDataProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return OddsDataProcessor()
    
    @pytest.fixture
    def mock_game_data(self):
        """Mock game data from AgentQL response."""
        return {
            'header': 'Kansas City Chiefs @ Buffalo Bills',
            'date': 'FRI NOV 15',
            'time': '8:15PM',
            'event_url': 'https://sportsbook.odds_scraper.com/event/12345',
            'teams': [
                {
                    'name': 'Kansas City Chiefs',
                    'spread': '+3.5',
                    'spread_odds': '-110',
                    'moneyline': '+150'
                },
                {
                    'name': 'Buffalo Bills',
                    'spread': '-3.5',
                    'spread_odds': '-110',
                    'moneyline': '-180'
                }
            ],
            'total_over': '47.5',
            'total_over_odds': '-110',
            'total_under': '47.5',
            'total_under_odds': '-110'
        }
    
    @pytest.fixture
    def mock_raw_data(self, mock_game_data):
        """Mock raw data response."""
        return {
            'games': [mock_game_data]
        }
    
    def test_process_valid_data(self, processor, mock_raw_data):
        """Test processing valid game data."""
        data_pull_id = 'test-pull-123'
        df = processor.process(mock_raw_data, data_pull_id)
        
        # Check DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) == 2  # Two teams
        
        # Check columns
        expected_columns = [
            'event_id', 'header', 'date', 'time', 'team',
            'spread', 'spread_odds', 'moneyline',
            'total_over', 'total_over_odds', 'total_under', 'total_under_odds',
            'event_url', 'data_pull_id', 'data_pull_start_time', 'data_pull_end_time',
            'bookmaker', 'odds_format'
        ]
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Check metadata
        assert df['bookmaker'].iloc[0] == 'Sportsbook'
        assert df['odds_format'].iloc[0] == 'American'
        assert df['data_pull_id'].iloc[0] == data_pull_id
        
        # Check team data
        assert 'Kansas City Chiefs' in df['team'].values
        assert 'Buffalo Bills' in df['team'].values
        
        # Check numeric conversion (pandas may use int64 or float64 depending on values)
        assert df['spread'].dtype in [float, 'float64', int, 'int64']
        assert df['moneyline'].dtype in [float, 'float64', int, 'int64']
    
    def test_process_empty_games(self, processor):
        """Test processing when no games are returned."""
        raw_data = {'games': []}
        data_pull_id = 'test-pull-empty'
        df = processor.process(raw_data, data_pull_id)
        
        assert isinstance(df, pd.DataFrame)
        assert df.empty
    
    def test_process_missing_teams(self, processor):
        """Test processing game without teams."""
        raw_data = {
            'games': [{
                'header': 'Test Game',
                'date': 'TODAY',
                'time': '1:00PM',
                'teams': []
            }]
        }
        df = processor.process(raw_data, 'test-pull-no-teams')
        
        # Should return empty DataFrame or handle gracefully
        assert isinstance(df, pd.DataFrame)
    
    def test_parse_date_string_relative(self, processor):
        """Test parsing relative date strings."""
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        assert processor._parse_date_string('TODAY') == today
        assert processor._parse_date_string('TOMORROW') == tomorrow
        assert processor._parse_date_string('YESTERDAY') == yesterday
        assert processor._parse_date_string('today') == today
    
    def test_parse_date_string_formatted(self, processor):
        """Test parsing various date formats."""
        # ISO format
        result = processor._parse_date_string('2025-11-15')
        assert result == '2025-11-15'
        
        # Day name format (approximation test)
        result = processor._parse_date_string('FRI NOV 15')
        assert result is not None
        assert '-11-15' in result  # Check month and day
    
    def test_parse_date_string_with_ordinals(self, processor):
        """Test parsing dates with ordinal suffixes."""
        # These should be cleaned and parsed
        result = processor._parse_date_string('FRI NOV 15TH')
        assert result is not None
        
        result = processor._parse_date_string('MON DEC 2ND')
        assert result is not None
    
    def test_parse_date_string_invalid(self, processor):
        """Test parsing invalid date strings."""
        assert processor._parse_date_string('') is None
        assert processor._parse_date_string('INVALID') is None
        assert processor._parse_date_string(None) is None
    
    def test_extract_event_id_valid(self, processor):
        """Test extracting event ID from URL."""
        url = 'https://sportsbook.odds_scraper.com/event/12345'
        assert processor._extract_event_id(url) == 12345
        
        url = 'https://example.com/path/67890'
        assert processor._extract_event_id(url) == 67890
    
    def test_extract_event_id_invalid(self, processor):
        """Test extracting event ID from invalid URLs."""
        assert processor._extract_event_id('') is None
        assert processor._extract_event_id('https://example.com/path/abc') is None
        assert processor._extract_event_id(None) is None
    
    def test_convert_time_to_eastern(self, processor):
        """Test timezone conversion."""
        date_str = '2025-11-15'
        time_str = '8:15PM'
        
        result = processor._convert_time_to_eastern(date_str, time_str)
        assert result is not None
        assert len(result) == 2
        
        date_converted, time_converted = result
        assert isinstance(date_converted, str)
        assert isinstance(time_converted, str)
        assert '/' in date_converted  # MM/DD/YYYY format
        assert ':' in time_converted
        assert ('AM' in time_converted or 'PM' in time_converted)
    
    def test_convert_time_to_eastern_invalid(self, processor):
        """Test timezone conversion with invalid inputs."""
        assert processor._convert_time_to_eastern('', '8:15PM') is None
        assert processor._convert_time_to_eastern('2025-11-15', '') is None
        assert processor._convert_time_to_eastern(None, None) is None
    
    def test_convert_numeric_columns(self, processor):
        """Test numeric column conversion."""
        df = pd.DataFrame({
            'spread': ['3.5', '-7.0', 'invalid', ''],
            'spread_odds': ['-110', '100', '-150', None],
            'moneyline': ['+150', '-200', 'pk', '0']
        })
        
        processor._convert_numeric_columns(df)
        
        # Check conversion succeeded
        assert df['spread'].dtype in [float, 'float64']
        assert df['spread_odds'].dtype in [float, 'float64']
        assert df['moneyline'].dtype in [float, 'float64']
        
        # Check valid numeric conversions
        assert df['spread'].iloc[0] == 3.5
        assert df['spread'].iloc[1] == -7.0
        assert df['spread_odds'].iloc[0] == -110
        
        # Check invalid conversions become NaN
        assert pd.isna(df['spread'].iloc[2])
        assert df['moneyline'].iloc[3] == 0
    
    def test_process_game_complete(self, processor, mock_game_data):
        """Test processing a complete game."""
        data_pull_id = 'test-pull-game'
        start_time = datetime.now().isoformat()
        
        rows = processor._process_game(mock_game_data, data_pull_id, start_time)
        
        assert len(rows) == 2  # Two teams
        assert all(isinstance(row, dict) for row in rows)
        
        # Check first team
        team1 = rows[0]
        assert team1['team'] == 'Kansas City Chiefs'
        assert team1['spread'] == '+3.5'
        assert team1['spread_odds'] == '-110'
        assert team1['moneyline'] == '+150'
        assert team1['data_pull_id'] == data_pull_id
        assert team1['event_id'] == 12345
        
        # Check totals are in both team records
        assert team1['total_over'] == '47.5'
        assert team1['total_under'] == '47.5'
    
    def test_process_game_missing_team_name(self, processor):
        """Test processing game with missing team names."""
        game_data = {
            'header': 'Test Game',
            'date': 'TODAY',
            'time': '1:00PM',
            'event_url': 'https://example.com/123',
            'teams': [
                {'name': '', 'spread': '3.5'},  # Empty name
                {'spread': '3.5'}  # Missing name key
            ]
        }
        
        rows = processor._process_game(game_data, 'test-pull', datetime.now().isoformat())
        assert len(rows) == 0  # Should skip teams without names
    
    def test_numeric_conversion_warning_logs(self, processor, caplog):
        """Test that failed numeric conversions are logged."""
        df = pd.DataFrame({
            'spread': ['abc', 'def', 'ghi'],
            'spread_odds': ['-110', '-120', '-130'],
            'moneyline': ['100', '200', '300'],
            'total_over': ['47.5', '48.5', '49.5'],
            'total_over_odds': ['-110', '-110', '-110'],
            'total_under': ['47.5', '48.5', '49.5'],
            'total_under_odds': ['-110', '-110', '-110']
        })
        
        processor._convert_numeric_columns(df)
        
        # Check that warnings were logged for spread column
        # (All 3 non-numeric values should fail conversion)
        assert any('spread' in record.message and 'failed numeric conversion' in record.message 
                   for record in caplog.records)


class TestOddsDataProcessorIntegration:
    """Integration tests with more complex scenarios."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return OddsDataProcessor()
    
    def test_full_pipeline_multiple_games(self, processor):
        """Test processing multiple games end-to-end."""
        raw_data = {
            'games': [
                {
                    'header': 'Team A @ Team B',
                    'date': 'TODAY',
                    'time': '1:00PM',
                    'event_url': 'https://example.com/1',
                    'teams': [
                        {'name': 'Team A', 'spread': '3.5', 'spread_odds': '-110', 'moneyline': '+150'},
                        {'name': 'Team B', 'spread': '-3.5', 'spread_odds': '-110', 'moneyline': '-180'}
                    ],
                    'total_over': '47.5',
                    'total_over_odds': '-110',
                    'total_under': '47.5',
                    'total_under_odds': '-110'
                },
                {
                    'header': 'Team C @ Team D',
                    'date': 'TOMORROW',
                    'time': '4:25PM',
                    'event_url': 'https://example.com/2',
                    'teams': [
                        {'name': 'Team C', 'spread': '7.0', 'spread_odds': '-105', 'moneyline': '+250'},
                        {'name': 'Team D', 'spread': '-7.0', 'spread_odds': '-115', 'moneyline': '-300'}
                    ],
                    'total_over': '51.0',
                    'total_over_odds': '-115',
                    'total_under': '51.0',
                    'total_under_odds': '-105'
                }
            ]
        }
        
        df = processor.process(raw_data, 'test-multi-game')
        
        assert len(df) == 4  # 2 games × 2 teams
        assert df['event_id'].nunique() == 2  # Two unique events
        assert set(df['team'].values) == {'Team A', 'Team B', 'Team C', 'Team D'}
        
        # Verify timestamps
        assert 'data_pull_start_time' in df.columns
        assert 'data_pull_end_time' in df.columns
        assert df['data_pull_start_time'].iloc[0] <= df['data_pull_end_time'].iloc[0]
