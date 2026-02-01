"""Unit tests for nflfastRv3 shared models."""

import pytest
from datetime import datetime
from typing import Dict, Any

from nflfastRv3.shared.models import (
    GameSchedule, FeatureVector, MLPrediction, 
    DataSourceConfig, ValidationResult, AnalyticsResult, PredictionOutcome
)


class TestGameSchedule:
    """Test GameSchedule model."""
    
    def test_game_schedule_creation(self):
        """Test creating a valid GameSchedule."""
        schedule = GameSchedule(
            game_id="2023_01_BUF_MIA",
            season=2023,
            week=1,
            game_date=datetime(2023, 9, 10, 13, 0),
            home_team="MIA",
            away_team="BUF"
        )
        
        assert schedule.game_id == "2023_01_BUF_MIA"
        assert schedule.season == 2023
        assert schedule.week == 1
        assert schedule.home_team == "MIA"
        assert schedule.away_team == "BUF"
    
    def test_game_schedule_validation(self):
        """Test GameSchedule validation."""
        # Valid team abbreviations
        valid_teams = ["BUF", "MIA", "NE", "NYJ", "PIT", "CLE", "BAL", "CIN"]
        
        for team in valid_teams:
            schedule = GameSchedule(
                game_id=f"2023_01_{team}_MIA",
                season=2023,
                week=1,
                game_date=datetime(2023, 9, 10, 13, 0),
                home_team="MIA",
                away_team=team
            )
            assert schedule.away_team == team
    
    def test_game_schedule_invalid_week(self):
        """Test GameSchedule validation with invalid week."""
        with pytest.raises(ValueError, match="Invalid week"):
            GameSchedule(
                game_id="2023_25_BUF_MIA",
                season=2023,
                week=25,  # Invalid week
                game_date=datetime(2023, 9, 10, 13, 0),
                home_team="MIA",
                away_team="BUF"
            )
    
    def test_game_schedule_invalid_season(self):
        """Test GameSchedule validation with invalid season."""
        with pytest.raises(ValueError, match="Invalid season"):
            GameSchedule(
                game_id="1990_01_BUF_MIA",
                season=1990,  # Invalid season
                week=1,
                game_date=datetime(1990, 9, 10, 13, 0),
                home_team="MIA",
                away_team="BUF"
            )
    
    def test_game_schedule_with_optional_fields(self):
        """Test GameSchedule with optional stadium and weather."""
        schedule = GameSchedule(
            game_id="2023_01_BUF_MIA",
            season=2023,
            week=1,
            game_date=datetime(2023, 9, 10, 13, 0),
            home_team="MIA",
            away_team="BUF",
            stadium="Hard Rock Stadium",
            weather={"temperature": 75, "conditions": "sunny"}
        )
        
        assert schedule.stadium == "Hard Rock Stadium"
        assert schedule.weather is not None
        assert schedule.weather["temperature"] == 75


class TestFeatureVector:
    """Test FeatureVector model."""
    
    def test_feature_vector_creation(self):
        """Test creating a valid FeatureVector."""
        features = {
            "team_efficiency_offense": 0.52,
            "team_efficiency_defense": 0.48,
            "recent_form_avg_score": 24.5,
            "head_to_head_wins": 2.0,
            "venue_home_advantage": 0.03
        }
        feature_names = [
            "team_efficiency_offense", "team_efficiency_defense", 
            "recent_form_avg_score", "head_to_head_wins", "venue_home_advantage"
        ]
        
        vector = FeatureVector(
            game_id="2023_01_BUF_MIA",
            features=features,
            feature_names=feature_names,
            created_at=datetime.now()
        )
        
        assert vector.game_id == "2023_01_BUF_MIA"
        assert len(vector.features) == 5
        assert vector.features["team_efficiency_offense"] == 0.52
        assert vector.feature_count == 5
    
    def test_feature_vector_validation_mismatch(self):
        """Test FeatureVector validation with mismatched features and names."""
        features = {"feature1": 0.5, "feature2": 0.8}
        feature_names = ["feature1"]  # Missing feature2
        
        with pytest.raises(ValueError, match="Features and feature_names must have same length"):
            FeatureVector(
                game_id="2023_01_BUF_MIA",
                features=features,
                feature_names=feature_names,
                created_at=datetime.now()
            )
    
    def test_feature_vector_validation_non_numeric(self):
        """Test FeatureVector validation with non-numeric features."""
        features = {"valid_feature": 0.5, "invalid_feature": "not_a_number"}
        feature_names = ["valid_feature", "invalid_feature"]
        
        with pytest.raises(ValueError, match="Feature invalid_feature must be numeric"):
            FeatureVector(
                game_id="2023_01_BUF_MIA",
                features=features,
                feature_names=feature_names,
                created_at=datetime.now()
            )
    
    def test_feature_vector_get_feature_array(self):
        """Test getting feature array in correct order."""
        features = {"feature_b": 0.8, "feature_a": 0.5, "feature_c": 0.3}
        feature_names = ["feature_a", "feature_c", "feature_b"]  # Different order
        
        vector = FeatureVector(
            game_id="2023_01_BUF_MIA",
            features=features,
            feature_names=feature_names,
            created_at=datetime.now()
        )
        
        array = vector.get_feature_array()
        assert array == [0.5, 0.3, 0.8]  # Should match feature_names order


class TestMLPrediction:
    """Test MLPrediction model."""
    
    def test_ml_prediction_creation(self):
        """Test creating a valid MLPrediction."""
        prediction = MLPrediction(
            game_id="2023_01_BUF_MIA",
            home_team="MIA",
            away_team="BUF",
            predicted_outcome=PredictionOutcome.AWAY_WIN,
            confidence=0.73,
            feature_importance={"team_efficiency": 0.45, "recent_form": 0.35},
            model_version="v1.0"
        )
        
        assert prediction.game_id == "2023_01_BUF_MIA"
        assert prediction.predicted_outcome == PredictionOutcome.AWAY_WIN
        assert prediction.confidence == 0.73
        assert prediction.feature_importance["team_efficiency"] == 0.45
    
    def test_ml_prediction_confidence_validation(self):
        """Test MLPrediction confidence validation."""
        # Test invalid confidence > 1
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            MLPrediction(
                game_id="2023_01_BUF_MIA",
                home_team="MIA",
                away_team="BUF",
                predicted_outcome=PredictionOutcome.HOME_WIN,
                confidence=1.5,  # Invalid
                feature_importance={"team_efficiency": 0.5},
                model_version="v1.0"
            )
        
        # Test invalid confidence < 0
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            MLPrediction(
                game_id="2023_01_BUF_MIA",
                home_team="MIA",
                away_team="BUF",
                predicted_outcome=PredictionOutcome.HOME_WIN,
                confidence=-0.1,  # Invalid
                feature_importance={"team_efficiency": 0.5},
                model_version="v1.0"
            )
    
    def test_ml_prediction_all_outcomes(self):
        """Test all prediction outcome types."""
        for outcome in [PredictionOutcome.HOME_WIN, PredictionOutcome.AWAY_WIN, PredictionOutcome.PUSH]:
            prediction = MLPrediction(
                game_id="2023_01_BUF_MIA",
                home_team="MIA",
                away_team="BUF",
                predicted_outcome=outcome,
                confidence=0.5,
                feature_importance={"team_efficiency": 0.5},
                model_version="v1.0"
            )
            assert prediction.predicted_outcome == outcome


class TestDataSourceConfig:
    """Test DataSourceConfig model."""
    
    def test_data_source_config_creation(self):
        """Test creating a valid DataSourceConfig."""
        config = DataSourceConfig(
            name="nflfastR_pbp",
            r_function="load_pbp",
            table_name="play_by_play",
            schema="nfl_data",
            seasons_required=True,
            incremental=True,
            unique_keys=["game_id", "play_id"]
        )
        
        assert config.name == "nflfastR_pbp"
        assert config.r_function == "load_pbp"
        assert config.table_name == "play_by_play"
        assert config.schema == "nfl_data"
        assert config.seasons_required is True
        assert config.incremental is True
        assert "game_id" in config.unique_keys
    
    def test_data_source_config_validation(self):
        """Test DataSourceConfig validation."""
        # Test missing name
        with pytest.raises(ValueError, match="name and r_function are required"):
            DataSourceConfig(
                name="",  # Empty name
                r_function="load_data",
                table_name="test_table",
                schema="test_schema",
                seasons_required=False,
                incremental=False,
                unique_keys=[]
            )
        
        # Test missing table_name
        with pytest.raises(ValueError, match="table_name and schema are required"):
            DataSourceConfig(
                name="test_source",
                r_function="load_data",
                table_name="",  # Empty table_name
                schema="test_schema",
                seasons_required=False,
                incremental=False,
                unique_keys=[]
            )


class TestValidationResult:
    """Test ValidationResult model."""
    
    def test_validation_result_success(self):
        """Test creating a successful ValidationResult."""
        result = ValidationResult(
            is_valid=True,
            warnings=["Minor data quality issue"],
            record_count=1000
        )
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.record_count == 1000
    
    def test_validation_result_failure(self):
        """Test creating a failed ValidationResult."""
        result = ValidationResult(
            is_valid=False,
            errors=["Missing required field", "Invalid data type"],
            record_count=5
        )
        
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 0
        assert result.record_count == 5
    
    def test_validation_result_add_error(self):
        """Test adding errors to ValidationResult."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        
        result.add_error("New error occurred")
        assert result.is_valid is False
        assert "New error occurred" in result.errors
    
    def test_validation_result_add_warning(self):
        """Test adding warnings to ValidationResult."""
        result = ValidationResult(is_valid=True)
        
        result.add_warning("Minor issue detected")
        assert result.is_valid is True  # Warnings don't affect validity
        assert "Minor issue detected" in result.warnings
    
    def test_validation_result_has_issues(self):
        """Test has_issues property."""
        # No issues
        result = ValidationResult(is_valid=True)
        assert not result.has_issues
        
        # With warning
        result.add_warning("Warning")
        assert result.has_issues
        
        # With error
        result.add_error("Error")
        assert result.has_issues


class TestAnalyticsResult:
    """Test AnalyticsResult model."""
    
    def test_analytics_result_creation(self):
        """Test creating a valid AnalyticsResult."""
        result = AnalyticsResult(
            analysis_type="team_efficiency_analysis",
            results={"BUF": 0.65, "MIA": 0.58},
            metadata={"execution_time": 1.23, "rows_processed": 500},
            generated_at=datetime(2023, 9, 10, 14, 30, 0)
        )
        
        assert result.analysis_type == "team_efficiency_analysis"
        assert result.results["BUF"] == 0.65
        assert result.metadata["execution_time"] == 1.23
        assert result.generated_at.year == 2023
    
    def test_analytics_result_get_result(self):
        """Test get_result method with defaults."""
        result = AnalyticsResult(
            analysis_type="test_analysis",
            results={"key1": "value1"}
        )
        
        assert result.get_result("key1") == "value1"
        assert result.get_result("missing_key") is None
        assert result.get_result("missing_key", "default") == "default"
    
    def test_analytics_result_add_metadata(self):
        """Test add_metadata method."""
        result = AnalyticsResult(
            analysis_type="test_analysis",
            results={}
        )
        
        result.add_metadata("execution_time", 2.5)
        result.add_metadata("cache_hit", True)
        
        assert result.metadata["execution_time"] == 2.5
        assert result.metadata["cache_hit"] is True


# Integration test for model interactions
class TestModelIntegration:
    """Test model interactions and workflows."""
    
    def test_game_schedule_to_feature_vector_workflow(self):
        """Test workflow from GameSchedule to FeatureVector."""
        # Create a game schedule
        schedule = GameSchedule(
            game_id="2023_01_BUF_MIA",
            season=2023,
            week=1,
            game_date=datetime(2023, 9, 10, 13, 0),
            home_team="MIA",
            away_team="BUF"
        )
        
        # Create feature vector for the game
        features = {"team_efficiency": 0.65}
        feature_names = ["team_efficiency"]
        
        feature_vector = FeatureVector(
            game_id=schedule.game_id,
            features=features,
            feature_names=feature_names,
            created_at=datetime.now()
        )
        
        # Verify consistency
        assert feature_vector.game_id == schedule.game_id
    
    def test_feature_vector_to_ml_prediction_workflow(self):
        """Test workflow from FeatureVector to MLPrediction."""
        # Create feature vector
        features = {"team_efficiency": 0.65, "recent_form": 0.72}
        feature_names = ["team_efficiency", "recent_form"]
        
        feature_vector = FeatureVector(
            game_id="2023_01_BUF_MIA",
            features=features,
            feature_names=feature_names,
            created_at=datetime.now()
        )
        
        # Create prediction based on features
        prediction = MLPrediction(
            game_id=feature_vector.game_id,
            home_team="MIA",
            away_team="BUF",
            predicted_outcome=PredictionOutcome.AWAY_WIN,
            confidence=0.68,
            feature_importance={"team_efficiency": 0.6, "recent_form": 0.4},
            model_version="v1.0"
        )
        
        # Verify consistency
        assert prediction.game_id == feature_vector.game_id
    
    def test_validation_workflow(self):
        """Test validation workflow across models."""
        # Create validation results for different stages
        data_validation = ValidationResult(is_valid=True, record_count=1000)
        data_validation.add_warning("Minor data quality issue")
        
        feature_validation = ValidationResult(is_valid=True, record_count=500)
        
        model_validation = ValidationResult(is_valid=True)
        
        # All validations should be valid
        assert data_validation.is_valid
        assert feature_validation.is_valid
        assert model_validation.is_valid
        
        # But one has warnings
        assert data_validation.has_issues
        assert not feature_validation.has_issues
        assert not model_validation.has_issues
