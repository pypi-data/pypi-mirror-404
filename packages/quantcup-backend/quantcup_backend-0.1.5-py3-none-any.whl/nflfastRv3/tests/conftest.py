"""Pytest configuration and fixtures for nflfastRv3 tests."""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime
from typing import Dict, Any

from nflfastRv3.shared.models import (
    GameSchedule, FeatureVector, MLPrediction, 
    ValidationResult, AnalyticsResult, PredictionOutcome
)
from nflfastRv3.features.data_pipeline.config.data_sources import DataSourceConfig

@pytest.fixture
def sample_game_schedule():
    """Fixture providing a sample GameSchedule for testing."""
    return GameSchedule(
        game_id="2023_01_BUF_MIA",
        home_team="MIA",
        away_team="BUF",
        game_date=datetime(2023, 9, 10, 13, 0),
        week=1,
        season=2023,
        stadium="Hard Rock Stadium",
        weather={"temperature": 75, "conditions": "sunny"}
    )


@pytest.fixture
def sample_feature_vector():
    """Fixture providing a sample FeatureVector for testing."""
    features = {
        'team_efficiency_offense': 0.65,
        'team_efficiency_defense': 0.48,
        'recent_form_wins': 3.0,
        'head_to_head_advantage': 0.2,
        'venue_home_advantage': 0.03
    }
    feature_names = list(features.keys())
    
    return FeatureVector(
        game_id="2023_01_BUF_MIA",
        features=features,
        feature_names=feature_names,
        created_at=datetime.now()
    )


@pytest.fixture
def sample_ml_prediction():
    """Fixture providing a sample MLPrediction for testing."""
    return MLPrediction(
        game_id="2023_01_BUF_MIA",
        home_team="MIA",
        away_team="BUF",
        predicted_outcome=PredictionOutcome.AWAY_WIN,
        confidence=0.73,
        feature_importance={
            'team_efficiency_offense': 0.4,
            'team_efficiency_defense': 0.3,
            'recent_form_wins': 0.2,
            'head_to_head_advantage': 0.1
        },
        model_version="test_v1.0"
    )


@pytest.fixture
def sample_data_source_config():
    """Fixture providing a sample DataSourceConfig for testing."""
    return DataSourceConfig(
        r_call="load_pbp(file_type = \"parquet\")",
        table="play_by_play",
        schema="nfl_data",
        unique_keys=["play_id", "game_id"],
        strategy="incremental"
    )


@pytest.fixture
def sample_validation_result():
    """Fixture providing a sample ValidationResult for testing."""
    result = ValidationResult(
        is_valid=True,
        record_count=1000
    )
    result.add_warning("Minor data quality issue")
    return result


@pytest.fixture
def sample_analytics_result():
    """Fixture providing a sample AnalyticsResult for testing."""
    return AnalyticsResult(
        analysis_type="team_efficiency_analysis",
        results={"BUF": 0.65, "MIA": 0.58, "NYJ": 0.52},
        metadata={"execution_time": 1.23, "rows_processed": 500},
        generated_at=datetime(2023, 9, 10, 14, 30, 0)
    )


@pytest.fixture
def mock_r_service():
    """Fixture providing a mocked R integration service."""
    mock_service = Mock()
    mock_service.r_available = True
    mock_service.nflfastr_available = True
    mock_service.is_healthy = True
    
    # Mock execute_r_call_string to return sample data (core R functionality)
    mock_service.execute_r_call_string.return_value = pd.DataFrame({
        'game_id': ['2023_01_BUF_MIA', '2023_01_NYJ_DAL'],
        'team': ['BUF', 'NYJ'],
        'opponent': ['MIA', 'DAL'],
        'offensive_epa': [0.15, 0.05],
        'defensive_epa': [-0.05, -0.15]
    })
    
    # NOTE: load_nfl_data removed as part of architectural fix
    # Data loading now handled by data pipeline -> database -> ML pipeline flow
    
    return mock_service


@pytest.fixture
def mock_database_service():
    """Fixture providing a mocked database service."""
    mock_db = Mock()
    mock_db.engine = Mock()
    mock_db.is_connected = True
    
    # Mock execute_query to return sample data
    mock_db.execute_query.return_value = pd.DataFrame({
        'team': ['BUF', 'MIA', 'NYJ'],
        'efficiency': [0.65, 0.58, 0.52],
        'games_played': [16, 16, 16]
    })
    
    return mock_db


@pytest.fixture
def mock_schedule_provider():
    """Fixture providing a mocked schedule data provider."""
    mock_provider = Mock()
    
    # Mock get_upcoming_games
    mock_provider.get_upcoming_games.return_value = [
        GameSchedule(
            game_id="2023_01_BUF_MIA",
            home_team="MIA",
            away_team="BUF",
            game_date=datetime(2023, 9, 10, 13, 0),
            week=1,
            season=2023
        ),
        GameSchedule(
            game_id="2023_01_NYJ_DAL",
            home_team="DAL",
            away_team="NYJ",
            game_date=datetime(2023, 9, 10, 16, 0),
            week=1,
            season=2023
        )
    ]
    
    # Mock get_team_schedule
    mock_provider.get_team_schedule.return_value = pd.DataFrame({
        'game_id': ['2023_01_BUF_MIA', '2023_02_BUF_NYJ'],
        'team': ['BUF', 'BUF'],
        'opponent': ['MIA', 'NYJ'],
        'week': [1, 2],
        'season': [2023, 2023]
    })
    
    return mock_provider


@pytest.fixture
def sample_nfl_data():
    """Fixture providing sample NFL data for testing."""
    return {
        'play_by_play': pd.DataFrame({
            'play_id': range(1, 101),
            'game_id': ['2023_01_BUF_MIA'] * 100,
            'week': [1] * 100,
            'season': [2023] * 100,
            'posteam': ['BUF'] * 50 + ['MIA'] * 50,
            'epa': [0.1, -0.2, 0.3] * 33 + [0.1],
            'down': [1, 2, 3, 4] * 25,
            'ydstogo': [10, 7, 3, 1] * 25
        }),
        'schedules': pd.DataFrame({
            'game_id': ['2023_01_BUF_MIA', '2023_01_NYJ_DAL'],
            'season': [2023, 2023],
            'week': [1, 1],
            'home_team': ['MIA', 'DAL'],
            'away_team': ['BUF', 'NYJ'],
            'gameday': ['2023-09-10', '2023-09-10']
        }),
        'rosters': pd.DataFrame({
            'player_id': ['player1', 'player2', 'player3'],
            'season': [2023, 2023, 2023],
            'team': ['BUF', 'BUF', 'MIA'],
            'position': ['QB', 'RB', 'WR'],
            'player_name': ['Josh Allen', 'James Cook', 'Tyreek Hill']
        })
    }


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")


# Pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.name.lower() or "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark performance tests
        if "performance" in item.name.lower() or "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        
        # Mark slow tests
        if "slow" in item.name.lower() or item.get_closest_marker("slow"):
            item.add_marker(pytest.mark.slow)


# Utility functions for tests
def create_mock_feature_vector(game_id: str = "2023_01_BUF_MIA", 
                              feature_count: int = 5) -> FeatureVector:
    """Create a mock FeatureVector for testing."""
    features = {f'feature_{i}': float(i) * 0.1 for i in range(feature_count)}
    feature_names = list(features.keys())
    
    return FeatureVector(
        game_id=game_id,
        features=features,
        feature_names=feature_names,
        created_at=datetime.now()
    )


def create_mock_prediction(game_id: str = "2023_01_BUF_MIA",
                          outcome: PredictionOutcome = PredictionOutcome.AWAY_WIN,
                          confidence: float = 0.7) -> MLPrediction:
    """Create a mock MLPrediction for testing."""
    return MLPrediction(
        game_id=game_id,
        home_team="MIA",
        away_team="BUF",
        predicted_outcome=outcome,
        confidence=confidence,
        feature_importance={'test_feature': 1.0},
        model_version="test_v1.0"
    )


