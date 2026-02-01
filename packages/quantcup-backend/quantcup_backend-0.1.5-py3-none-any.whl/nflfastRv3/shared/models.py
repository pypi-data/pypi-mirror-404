"""
Core data models and type definitions for nflfastRv3.

This module provides the fundamental data structures that support real implementations
across the entire pipeline while maintaining the clean architecture principles.
Follows the Minimum Viable Decoupling pattern with simple dataclasses.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum


class PredictionOutcome(Enum):
    """Enumeration for ML prediction outcomes."""
    HOME_WIN = "home_win"
    AWAY_WIN = "away_win"
    PUSH = "push"


@dataclass
class GameSchedule:
    """
    NFL game schedule information with all necessary metadata.
    
    Complexity: 1 point (simple data container)
    """
    game_id: str
    home_team: str
    away_team: str
    game_date: datetime
    week: int
    season: int
    season_type: str = 'REG'  # 'PRE' (preseason), 'REG' (regular), 'POST' (postseason)
    stadium: Optional[str] = None
    weather: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate game schedule data."""
        if self.week < 1 or self.week > 22:
            raise ValueError(f"Invalid week: {self.week}")
        if self.season < 1999:
            raise ValueError(f"Invalid season: {self.season}")
        if self.season_type not in ('PRE', 'REG', 'POST'):
            raise ValueError(f"Invalid season_type: {self.season_type}. Must be 'PRE', 'REG', or 'POST'")


@dataclass
class FeatureVector:
    """
    Complete feature vector for ML model input.
    
    Complexity: 1 point (simple data container with validation)
    """
    game_id: str
    features: Dict[str, float]
    feature_names: List[str]
    created_at: datetime
    
    def __post_init__(self):
        """Validate feature vector consistency."""
        if len(self.features) != len(self.feature_names):
            raise ValueError("Features and feature_names must have same length")
        
        # Ensure all features are numeric
        for name, value in self.features.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Feature {name} must be numeric, got {type(value)}")
    
    @property
    def feature_count(self) -> int:
        """Get the number of features in this vector."""
        return len(self.features)
    
    def get_feature_array(self) -> List[float]:
        """Get features as ordered array matching feature_names."""
        return [self.features[name] for name in self.feature_names]


@dataclass
class MLPrediction:
    """
    Machine learning prediction result with metadata.
    
    Complexity: 1 point (simple data container)
    """
    game_id: str
    home_team: str
    away_team: str
    predicted_outcome: PredictionOutcome
    confidence: float
    feature_importance: Dict[str, float]
    model_version: str
    prediction_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate prediction data."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")


@dataclass
class ValidationResult:
    """
    Result of data validation operations.
    
    Used throughout the pipeline to track data quality and validation status.
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    record_count: Optional[int] = None
    validation_date: datetime = field(default_factory=datetime.now)
    
    def add_error(self, error: str) -> None:
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)
    
    @property
    def has_issues(self) -> bool:
        """Check if there are any errors or warnings."""
        return len(self.errors) > 0 or len(self.warnings) > 0


@dataclass
class AnalyticsResult:
    """
    Result container for analytics operations.
    
    Provides a standardized way to return analysis results with metadata.
    """
    analysis_type: str
    results: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def get_result(self, key: str, default: Any = None) -> Any:
        """Safely get a result value."""
        return self.results.get(key, default)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the result."""
        self.metadata[key] = value


# Type aliases for cleaner code
GameData = Dict[str, Any]
FeatureData = Dict[str, Union[float, int]]
SeasonData = List[int]
