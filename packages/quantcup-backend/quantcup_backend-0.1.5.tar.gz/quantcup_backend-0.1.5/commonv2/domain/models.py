"""
Domain models for CommonV2.

Clean, typed domain objects that represent core business entities.
Uses Pydantic for validation and type safety.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import pandas as pd


@dataclass
class Team:
    """Core team entity with standardized data."""
    abbreviation: str
    full_name: str
    nickname: Optional[str] = None
    conference: Optional[str] = None
    division: Optional[str] = None
    team_id: Optional[str] = None
    
    # Visual branding
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    logo_espn: Optional[str] = None
    logo_wikipedia: Optional[str] = None
    
    def __post_init__(self):
        """Validate team data after creation."""
        if not self.abbreviation or len(self.abbreviation) < 2:
            raise ValueError(f"Invalid team abbreviation: {self.abbreviation}")
        if not self.full_name:
            raise ValueError("Team full_name is required")


@dataclass
class Game:
    """Core game entity with standardized data."""
    home_team: str
    away_team: str
    game_date: datetime
    week: Optional[int] = None
    season: Optional[int] = None
    game_id: Optional[str] = None
    
    # Game details
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    game_type: Optional[str] = None  # REG, POST, PRE
    
    def __post_init__(self):
        """Validate game data after creation."""
        if not self.home_team or not self.away_team:
            raise ValueError("Both home_team and away_team are required")
        if self.home_team == self.away_team:
            raise ValueError("Home and away teams cannot be the same")


@dataclass
class Season:
    """Season entity for validation and operations."""
    year: int
    
    def __post_init__(self):
        """Validate season year."""
        if not (1920 <= self.year <= 2050):
            raise ValueError(f"Season year out of reasonable range: {self.year}")
    
    @property
    def is_current(self) -> bool:
        """Check if this is the current NFL season."""
        from datetime import datetime
        current_date = datetime.now()
        current_season_year = current_date.year if current_date.month >= 9 else current_date.year - 1
        return self.year == current_season_year


# Type aliases for common data structures
TeamDataFrame = pd.DataFrame  # DataFrame with team data
GameDataFrame = pd.DataFrame  # DataFrame with game data
