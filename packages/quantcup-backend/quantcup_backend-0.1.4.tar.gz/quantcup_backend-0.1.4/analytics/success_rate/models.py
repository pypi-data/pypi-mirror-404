"""
Success Rate Analysis Models

Feature-specific models for success rate analysis.
Extracted from analytics/domain/models.py following Solo Developer pattern.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PlayData(BaseModel):
    """Represents a single NFL play with success indicators."""
    team: str
    season: int
    week: int
    game_date: datetime
    play_type: str
    rush_attempt: bool
    pass_attempt: bool
    epa: float
    is_success: bool


class TeamInfo(BaseModel):
    """Represents team metadata and branding information."""
    team_abbr: str
    team_name: str
    team_nick: str
    team_id: str
    team_conf: str
    team_division: str
    team_color: str
    team_logo_squared: str
    team_logo_espn: Optional[str] = None
    
    @validator('team_abbr')
    def validate_team_abbr(cls, v):
        """Validate team abbreviation format."""
        if not v or len(v) < 2:
            raise ValueError('Team abbreviation must be at least 2 characters')
        return v.upper()


class TeamSuccessRate(BaseModel):
    """Represents calculated success rates for a team."""
    team: str
    team_name: str
    team_nick: str
    rush_success_rate: float = Field(..., ge=0.0, le=1.0)
    pass_success_rate: float = Field(..., ge=0.0, le=1.0)
    rush_attempts: int = Field(..., ge=0)
    pass_attempts: int = Field(..., ge=0)
    rush_successes: int = Field(..., ge=0)
    pass_successes: int = Field(..., ge=0)
    team_logo_squared: Optional[str] = None
    team_logo_espn: Optional[str] = None
    team_color: Optional[str] = None
    
    @validator('rush_successes')
    def validate_rush_successes(cls, v, values):
        """Validate rush successes don't exceed attempts."""
        if 'rush_attempts' in values and v > values['rush_attempts']:
            raise ValueError('Rush successes cannot exceed rush attempts')
        return v
    
    @validator('pass_successes')
    def validate_pass_successes(cls, v, values):
        """Validate pass successes don't exceed attempts."""
        if 'pass_attempts' in values and v > values['pass_attempts']:
            raise ValueError('Pass successes cannot exceed pass attempts')
        return v


class LeagueAverages(BaseModel):
    """Represents league-wide average success rates."""
    avg_rush_success_rate: float = Field(..., ge=0.0, le=1.0)
    avg_pass_success_rate: float = Field(..., ge=0.0, le=1.0)
    total_rush_attempts: int = Field(..., ge=0)
    total_pass_attempts: int = Field(..., ge=0)
    teams_included: int = Field(..., ge=1)


class ChartConfig(BaseModel):
    """Configuration for chart rendering."""
    title: str
    x_axis_label: str
    y_axis_label: str
    save_path: str
    width: int = Field(default=14, ge=1)
    height: int = Field(default=10, ge=1)
    dpi: int = Field(default=300, ge=72)
    x_min: Optional[float] = Field(default=0.30)
    x_max: Optional[float] = Field(default=0.52)
    y_min: Optional[float] = Field(default=0.30)
    y_max: Optional[float] = Field(default=0.57)
    logo_size: tuple = Field(default=(35, 35))
    
    @validator('x_max')
    def validate_x_range(cls, v, values):
        """Validate x_max is greater than x_min."""
        if v is not None and 'x_min' in values and values['x_min'] is not None and v <= values['x_min']:
            raise ValueError('x_max must be greater than x_min')
        return v
    
    @validator('y_max')
    def validate_y_range(cls, v, values):
        """Validate y_max is greater than y_min."""
        if v is not None and 'y_min' in values and values['y_min'] is not None and v <= values['y_min']:
            raise ValueError('y_max must be greater than y_min')
        return v


class CalculationMethod(str, Enum):
    """Available methods for calculating success rates."""
    EPA_BASED = "epa"
    YARDAGE_BASED = "yardage"
    DOWN_DISTANCE = "down_distance"


class AnalysisConfig(BaseModel):
    """Configuration for running success rate analysis."""
    season: int = Field(..., ge=1999, le=2030)
    max_week: int = Field(..., ge=1, le=22)
    calculation_method: CalculationMethod = CalculationMethod.EPA_BASED
    chart_config: Optional[ChartConfig] = None
    include_chart: bool = True
    
    @validator('season')
    def validate_season_range(cls, v):
        """Validate season is within reasonable range."""
        current_year = datetime.now().year
        if v > current_year + 1:
            raise ValueError(f'Season cannot be more than one year in the future: {current_year + 1}')
        return v


class SuccessRateAnalysisResult(BaseModel):
    """Result of a complete success rate analysis."""
    team_success_rates: List[TeamSuccessRate]
    league_averages: LeagueAverages
    chart_path: Optional[str] = None
    analysis_id: str
    season: int
    max_week: int
    created_at: datetime = Field(default_factory=datetime.now)
    execution_time_seconds: Optional[float] = None
    
    @validator('team_success_rates')
    def validate_teams_not_empty(cls, v):
        """Validate team success rates are not empty."""
        if not v:
            raise ValueError('Team success rates cannot be empty')
        return v
