"""
Points Per Drive Analysis Models

Feature-specific models for points per drive efficiency analysis.
Extracted from analytics/domain/models.py following Solo Developer pattern.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


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


class TeamEfficiencyMetrics(BaseModel):
    """Represents calculated efficiency metrics for a team."""
    team: str
    team_name: str
    team_nick: str
    scoring_efficiency_ppd: float = Field(..., description="Points per drive (offense)")
    stopping_efficiency_ppd: float = Field(..., description="Opponent points per drive allowed (defense)")
    opponent_adjusted_scoring: float = Field(..., description="Opponent-adjusted scoring efficiency")
    opponent_adjusted_stopping: float = Field(..., description="Opponent-adjusted stopping efficiency")
    total_drives_offense: int = Field(..., ge=0)
    total_drives_defense: int = Field(..., ge=0)
    total_points_scored: int = Field(..., ge=0)
    total_points_allowed: int = Field(..., ge=0)
    team_logo_squared: Optional[str] = None
    team_logo_espn: Optional[str] = None
    team_color: Optional[str] = None


class LeagueEfficiencyAverages(BaseModel):
    """Represents league-wide average efficiency metrics."""
    avg_scoring_efficiency_ppd: float = Field(..., ge=0.0)
    avg_stopping_efficiency_ppd: float = Field(..., ge=0.0)
    avg_opponent_adjusted_scoring: float = Field(..., description="Opponent-adjusted scoring (can be negative)")
    avg_opponent_adjusted_stopping: float = Field(..., description="Opponent-adjusted stopping (can be negative)")
    total_drives: int = Field(..., ge=0)
    total_points: int = Field(..., ge=0)
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
    use_dynamic_ranges: bool = Field(default=False, description="Calculate ranges dynamically from data")
    padding_percent: float = Field(default=0.15, ge=0.0, le=0.5, description="Padding around data as percentage")
    min_range_size: float = Field(default=1.0, ge=0.1, description="Minimum range size to prevent overly zoomed charts")
    center_on_averages: bool = Field(default=True, description="Center ranges around league averages")
    
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
    """Available methods for calculating efficiency metrics."""
    EPA_BASED = "epa"
    YARDAGE_BASED = "yardage"
    DOWN_DISTANCE = "down_distance"


class AnalysisConfig(BaseModel):
    """Configuration for running efficiency analysis."""
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


class EfficiencyAnalysisResult(BaseModel):
    """Result of a complete efficiency analysis."""
    team_efficiency_metrics: List[TeamEfficiencyMetrics]
    league_averages: LeagueEfficiencyAverages
    chart_path: Optional[str] = None
    analysis_id: str
    season: int
    max_week: int
    created_at: datetime = Field(default_factory=datetime.now)
    execution_time_seconds: Optional[float] = None
    
    @validator('team_efficiency_metrics')
    def validate_teams_not_empty(cls, v):
        """Validate team efficiency metrics are not empty."""
        if not v:
            raise ValueError('Team efficiency metrics cannot be empty')
        return v
